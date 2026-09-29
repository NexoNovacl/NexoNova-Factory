#!/usr/bin/env python3
"""Future runtime harness. Default CLI is descriptive and cannot execute a WorkOrder.

Execution is an explicit API requiring an ExecutionSession and a hash-bound recipe.
This implementation phase tests recipe construction and fake transports only.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import argparse
import contextlib
import json
import os
import selectors
import signal
import subprocess
import time

from factory.business_execution_contracts import canonical, digest, loads, require, ContractError
from factory.business_materialization import ExecutionSession, OwnedTree, secure_read, snapshot

NODE_IMAGE = 'nexonova-p44b-node-openssl@sha256:0d0e3b31790d5b477357d4596d0c4b97f7fe2c7a43d7501821b7de1d90f52c16'
POSTGRES_IMAGE = 'postgres@sha256:efedf3595f1d6f415c08568ba171029bf54052e754cc9f030e3f2412b21f3d67'
ACTIONS = ('stage','database','build','integration','preservation-cleanup')
LABEL = 'nexonova.p46.run'


def validate_recipe(recipe, wo, control):
    keys = {'format','executionAuthority','runId','productId','namespace','nodeImage','postgresImage',
            'port','httpPort','controlRoot','sourceDirectory','envFiles','tlsDirectory','cacheDirectory','expectedNextEnvHash'}
    require(type(recipe) is dict and set(recipe) == keys, 'runtime recipe incomplete/unknown fields')
    require(recipe['format'] == 'nexonova.business-runtime-recipe.v1' and recipe['executionAuthority'] == 'none', 'recipe is not authority')
    import re
    require(recipe['runId'] == wo['runId'] and recipe['productId'] == wo['productId'], 'recipe identity mismatch')
    require(recipe['controlRoot']==str(control),'hash-bound control root mismatch')
    expected_namespace = 'p46-'+wo['runId']+'-'+wo['productId']
    require(recipe['namespace'] == expected_namespace and re.fullmatch('[a-z0-9-]{1,110}',expected_namespace), 'namespace mismatch')
    require(recipe['nodeImage'] == NODE_IMAGE and recipe['postgresImage'] == POSTGRES_IMAGE, 'image digest changed')
    require(type(recipe['port']) is int and 1024 <= recipe['port'] <= 65535, 'explicit loopback port required')
    require(type(recipe['httpPort']) is int and 1024 <= recipe['httpPort'] <= 65535 and recipe['httpPort']!=recipe['port'], 'distinct explicit HTTP/TLS ports required')
    require(recipe['sourceDirectory'] == wo['destinations']['validation'], 'validation directory mismatch')
    require(set(recipe['envFiles']) == {'runtime','migrator','bootstrap','postgres'}, 'separate credentials required')
    paths = list(recipe['envFiles'].values())+[recipe['tlsDirectory'],recipe['cacheDirectory']]
    require(len(set(paths)) == len(paths), 'private inputs overlap')
    for p in paths:
        path = Path(p)
        require(path.is_absolute() and str(path) == p and '..' not in path.parts and path.is_relative_to(control), 'private path outside control root')
        require(',' not in p and '\n' not in p and '\x00' not in p, 'unsafe mount path')
    require(re.fullmatch('sha256:[a-f0-9]{64}',recipe['expectedNextEnvHash']), 'exact Next derived bytes hash required')
    # Network is offline for installation in this version. No imaginary egress allowlist.
    require(wo['resources']['maxContainers'] >= 3 and wo['resources']['maxMemoryMiB'] >= 4096,
            'runtime resource budget insufficient')
    return recipe


def recipes(recipe, wo):
    """Build argv arrays only; no commands are executed by this function."""
    namespace = recipe['namespace']
    labels = ['--label',LABEL+'='+wo['runId'],'--label','nexonova.p46.product='+wo['productId']]
    net, volume, db, app = (namespace+x for x in ('-net','-data','-db','-app'))
    source = recipe['sourceDirectory']
    common = ['--pull=never','--init','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges',
              '--pids-limit=256','--cpus=2','--memory=2g','--tmpfs','/tmp:rw,nosuid,nodev,size=256m']
    def node(name, command, *, role='runtime',network='none',readonly=False):
        mount = 'type=bind,src='+source+',dst=/work'+(',readonly' if readonly else '')
        return ['docker','run','--rm','--name',namespace+'-'+name,*labels,*common,'--network',network,
                '--user',str(os.getuid())+':'+str(os.getgid()),'--mount',mount,'--workdir','/work',
                '--mount','type=bind,src='+recipe['cacheDirectory']+',dst=/npm-cache',
                '--env-file',recipe['envFiles'][role],'--env','npm_config_cache=/npm-cache','--env','HOME=/tmp','--env','NEXT_TELEMETRY_DISABLED=1',
                '--env','BETTER_AUTH_TELEMETRY=0',NODE_IMAGE,*command]
    def step(name, action, argv, timeout=600, resource=None):
        if resource is None and argv[:2]==['docker','run'] and '--name' in argv:
            resource={'kind':'container','name':argv[argv.index('--name')+1],'runId':wo['runId'],'productId':wo['productId']}
        return {'name':name,'action':action,'argv':argv,'timeout':min(timeout,wo['resources']['maxDurationSeconds']),
                'resource':resource,'runtimeStatus':'NOT_EXECUTED'}
    def resource(kind,name):
        return {'kind':kind,'name':name,'runId':wo['runId'],'productId':wo['productId']}
    result = [
        step('network','docker',['docker','network','create','--internal',*labels,net],60,resource('network',net)),
        step('volume','docker',['docker','volume','create',*labels,volume],60,resource('volume',volume)),
        step('postgres','docker',['docker','run','-d','--name',db,*labels,'--pull=never','--network',net,
             '--memory=1g','--cpus=1','--pids-limit=256','--cap-drop=ALL','--security-opt=no-new-privileges',
             '--env-file',recipe['envFiles']['postgres'],'--mount','type=volume,src='+volume+',dst=/var/lib/postgresql/data',
             '--user','postgres',POSTGRES_IMAGE],120,resource('container',db)),
        step('install','install',node('install',['npm','ci','--offline','--ignore-scripts','--no-audit','--no-fund'])),
        step('engine','install',node('engine',['node','node_modules/@prisma/engines/dist/scripts/postinstall.js'])),
        step('auth-generate','build',node('authgen',['node','node_modules/prisma/build/index.js','generate'])),
        step('requests-generate','build',node('reqgen',['node','node_modules/prisma/build/index.js','generate','--config','prisma.requests.config.ts'])),
        step('migrate','migrate',node('migrate',['node','node_modules/prisma/build/index.js','migrate','deploy','--config','prisma.requests.config.ts'],role='migrator',network=net)),
        step('reapply','migrate',node('reapply',['node','node_modules/prisma/build/index.js','migrate','deploy','--config','prisma.requests.config.ts'],role='migrator',network=net)),
        step('compile-checks','build',node('checks',['node','node_modules/typescript/bin/tsc','-p','tsconfig.generation-checks.json'])),
        step('unit','build',node('unit',['npm','test'])),
        step('typecheck','build',node('typecheck',['npm','run','typecheck'])),
        step('build','build',node('build',['npm','run','build'])),
        step('app','docker',['docker','run','-d','--name',app,*labels,*[x for x in common if x!='--memory=2g'],'--network',net,
             '--memory=1g','--publish','127.0.0.1:'+str(recipe['httpPort'])+':3000','--user',str(os.getuid())+':'+str(os.getgid()),
             '--mount','type=bind,src='+source+',dst=/work,readonly',
             '--mount','type=bind,src='+recipe['tlsDirectory']+',dst=/tls,readonly',
             '--workdir','/work','--env-file',recipe['envFiles']['runtime'],'--env','HOME=/tmp','--env','NEXT_TELEMETRY_DISABLED=1',
             '--env','BETTER_AUTH_TELEMETRY=0','--env','PORT=3000',NODE_IMAGE,'node','scripts/start-requests.mjs'],120,resource('container',app)),
    ]
    def sql_step(name, action, source):
        return {**step(name,action,['docker','exec','-i',db,'sh','-c','exec psql -d "$POSTGRES_DB" "$@"','psql','-X','-q','-v','ON_ERROR_STOP=1','-U','postgres','-At'],60),
                'stdinSource':source}
    # Provisioning consumes a separate explicitly authorized technical action.
    result.insert(3,sql_step('roles','bootstrap-fixtures','roles'))
    index=next(i for i,x in enumerate(result) if x['name']=='reapply')+1
    result.insert(index,sql_step('grants','bootstrap-fixtures','grants'))
    result.insert(index+1,sql_step('tables','migrate','tables'))
    result.insert(index+2,sql_step('fk','migrate','fk'))
    index=next(i for i,x in enumerate(result) if x['name']=='compile-checks')+1
    for offset,(name,script,source) in enumerate([('bootstrap-admin','scripts/bootstrap-admin.js','admin'),
                                               ('member-a','validation/requests-users.js','member-a'),
                                               ('member-b','validation/requests-users.js','member-b')]):
        command=node(name,['node','build-checks/'+script],role='bootstrap',network=net)
        command.insert(command.index('--rm')+1,'-i')
        result.insert(index+offset,{**step(name,'bootstrap-fixtures',command),'stdinSource':source})
    result.insert(index+3,sql_step('revoke-bootstrap','bootstrap-fixtures','revoke-bootstrap'))
    return result


def parse_private_env(raw):
    require(type(raw) is bytes and len(raw)<=65536,'private env budget')
    result={}
    for line in raw.decode('utf-8').splitlines():
        if not line or line.startswith('#'):continue
        key,separator,value=line.partition('=')
        require(separator and key not in result and key.replace('_','').isalnum(),'ambiguous env input')
        require(value and not any(c in value for c in ('\x00','\r','\n')),'invalid env value')
        result[key]=value
    return result


def database_sql(source, recipe, payload, env):
    # Passwords remain in stdin only; never argv/journal/receipt.
    from urllib.parse import urlsplit,unquote
    import re
    if source in ('admin','member-a','member-b'):
        key={'admin':'P46_BOOTSTRAP_ADMIN_JSON','member-a':'P46_BOOTSTRAP_MEMBER_A_JSON','member-b':'P46_BOOTSTRAP_MEMBER_B_JSON'}[source]
        raw=env['bootstrap'].get(key,'').encode()
        value=loads(raw)
        require(value.get('database')==env['postgres'].get('POSTGRES_DB') and type(value.get('password')) is str,'private fixture payload mismatch')
        if source=='admin':require(value.get('email')=='admin@example.invalid','synthetic admin identity required')
        if source!='admin':require(value.get('email')==source+'@example.invalid','synthetic fixture identity mismatch')
        return raw
    if source=='revoke-bootstrap':return b'DROP OWNED BY bpbootstrap; DROP ROLE bpbootstrap;'
    if source=='tables':return b"SELECT tablename FROM pg_tables WHERE schemaname='app' ORDER BY tablename;"
    if source=='fk':return b"SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='app.\"InternalRequest\"'::regclass AND contype='f';"
    if source=='grants':
        return b'\n'.join(payload[p] for p in ('validation/runtime-grants.sql','validation/bootstrap-grants.sql','validation/requests-runtime-grants.sql'))
    require(source=='roles','unknown SQL source')
    database=env['postgres'].get('POSTGRES_DB')
    require(type(database) is str and re.fullmatch('[a-z][a-z0-9_]{0,47}',database),'explicit synthetic DB name required')
    require(env['postgres'].get('POSTGRES_USER','postgres')=='postgres','technical PostgreSQL user mismatch')
    statements=[]
    for role,key,name in [('runtime','DATABASE_URL','bpruntime'),('migrator','MIGRATION_DATABASE_URL','bpmigrator'),('bootstrap','BOOTSTRAP_DATABASE_URL','bpbootstrap')]:
        url=urlsplit(env[role].get(key,''))
        password=unquote(url.password or '')
        require(url.scheme in ('postgres','postgresql') and url.username==name and url.hostname==recipe['namespace']+'-db' and
                url.port==5432 and url.path=='/'+database and not url.query and not url.fragment,'DB credential isolation mismatch')
        require(re.fullmatch('[a-f0-9]{48,128}',password),'independent ephemeral hex credential required')
        statements.append("CREATE ROLE "+name+" LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD '"+password+"';")
    require(len({urlsplit(env[r][k]).password for r,k in [('runtime','DATABASE_URL'),('migrator','MIGRATION_DATABASE_URL'),('bootstrap','BOOTSTRAP_DATABASE_URL')]})==3,'DB credentials reused')
    statements += ['REVOKE ALL ON DATABASE "'+database+'" FROM PUBLIC;',
                   'ALTER DATABASE "'+database+'" OWNER TO bpmigrator;',
                   'GRANT CONNECT ON DATABASE "'+database+'" TO bpruntime, bpbootstrap;',
                   'CREATE SCHEMA app AUTHORIZATION bpmigrator;','REVOKE ALL ON SCHEMA public FROM PUBLIC;']
    return ('\n'.join(statements)+'\n').encode()


class ProcessTransport:
    """Bounded output and wall-clock timeout; never shell=True; not used in unit tests."""
    def run(self, argv, timeout, input_bytes=None):
        require(type(argv) is list and argv and all(type(x) is str and '\x00' not in x for x in argv), 'argv required')
        require(input_bytes is None or type(input_bytes) is bytes and len(input_bytes) <= 4096, 'stdin budget')
        process = subprocess.Popen(argv,stdin=subprocess.PIPE if input_bytes is not None else subprocess.DEVNULL,
                                   stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
        output = bytearray()
        deadline = time.monotonic()+timeout
        try:
            if input_bytes is not None:
                process.stdin.write(input_bytes)
                process.stdin.close()
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout,selectors.EVENT_READ)
                while selector.get_map():
                    if time.monotonic() > deadline:
                        raise ContractError('command timeout')
                    for key,_ in selector.select(timeout=min(.1,max(0,deadline-time.monotonic()))):
                        chunk = os.read(key.fileobj.fileno(),65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                        else:
                            output.extend(chunk)
                            require(len(output) <= 2*1024*1024,'command output budget')
            code = process.wait(timeout=max(.1,deadline-time.monotonic()))
            return {'exitCode':code,'output':bytes(output)}
        finally:
            if process.poll() is None:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                process.wait()
            process.stdout.close()
            if process.stdin and not process.stdin.closed:
                process.stdin.close()


def verify_resource(record, inspected):
    require(type(inspected) is list and len(inspected) == 1,'resource inspection ambiguous')
    obj = inspected[0]
    labels = obj.get('Config',{}).get('Labels') if record['kind']=='container' else obj.get('Labels')
    require(type(labels) is dict and labels.get(LABEL) == record['runId'] and
            labels.get('nexonova.p46.product') == record['productId'],'foreign resource; no cleanup')
    actual_name = obj.get('Name','').lstrip('/')
    require(actual_name == record['name'],'resource name mismatch')
    identifier = obj.get('Id',actual_name)
    if record.get('id'):
        require(record['id'] == identifier,'resource identity changed')
    return identifier


class RuntimeHarness:
    def __init__(self, session, recipe_bytes, *, transport=None):
        require(type(session) is ExecutionSession,'validated execution boundary required')
        self.session = session
        self.recipe_bytes = recipe_bytes
        self.recipe = validate_recipe(loads(recipe_bytes),session.wo,session.control_root)
        require(digest(recipe_bytes) in {x['sha256'] for x in session.wo['inputHashes']},'recipe not bound by WorkOrder')
        self.transport = transport if transport is not None else ProcessTransport()
        self.steps = recipes(self.recipe,session.wo)

    def run(self):
        try:
            return self._run()
        except BaseException:
            try:
                self.cleanup_resources()
            except BaseException as cleanup_error:
                raise ContractError('runtime failed and owned cleanup is BLOCKED; inspect the journal before recovery') from cleanup_error
            raise

    def _run(self):
        steps = self.steps
        actions = list(dict.fromkeys(s['action'] for s in steps))
        outputs = []
        # One atomic reservation for the entire action, not one consumption per command.
        with self.session.workflow(actions) as (journal,guard):
            private_hashes={p:digest(secure_read(p)) for p in self.recipe['envFiles'].values()}
            for step in steps:
                guard()
                OwnedTree(self.recipe['sourceDirectory'],journal,self.session.binding).verify()
                for env_file in self.recipe['envFiles'].values():
                    raw = secure_read(env_file)
                    require(digest(raw)==private_hashes[env_file],'private environment changed during workflow')
                    require(raw and os.stat(env_file,follow_symlinks=False).st_mode & 0o077 == 0,'private env file required')
                event = {'kind':'runtime-intent','step':step['name'],'action':step['action'],
                         'binding':self.session.binding,'resource':step['resource']}
                journal.append(event,guard)
                guard()
                if step['name']=='roles':
                    deadline=time.monotonic()+30
                    while True:
                        guard()
                        ready=self.transport.run(['docker','exec',self.recipe['namespace']+'-db','pg_isready','-U','postgres'],2)
                        if ready['exitCode']==0:break
                        require(time.monotonic()<deadline,'database readiness timeout')
                        time.sleep(.1)
                stdin_bytes=None
                if step.get('stdinSource'):
                    env={k:parse_private_env(secure_read(p)) for k,p in self.recipe['envFiles'].items()}
                    stdin_bytes=database_sql(step['stdinSource'],self.recipe,self.session.bundle['payload'],env)
                guard()
                result = self.transport.run(step['argv'],step['timeout'],input_bytes=stdin_bytes)
                if step['name']=='tables':
                    require(result['exitCode']==0 and result['output'].decode().splitlines()==['Account','InternalRequest','Session','User','Verification','_prisma_migrations'],'schema inventory mismatch')
                if step['name']=='fk':
                    require(result['exitCode']==0 and b'FOREIGN KEY ("ownerId") REFERENCES app."User"(id) ON UPDATE RESTRICT ON DELETE RESTRICT' in result['output'],'real FK missing')
                require(type(result) is dict and type(result.get('exitCode')) is int and type(result.get('output')) is bytes,'invalid transport result')
                if step['resource'] and '--rm' not in step['argv']:
                    guard()
                    inspection = self.transport.run(['docker',step['resource']['kind'],'inspect',step['resource']['name']],30)
                    require(inspection['exitCode']==0,'resource inspection failed')
                    rid=verify_resource(step['resource'],loads(inspection['output']))
                    journal.append({'kind':'runtime-resource','binding':self.session.binding,
                                    'resource':{**step['resource'],'id':rid}},guard)
                # Persist neither env values nor uncontrolled subprocess output.
                summary={'step':step['name'],'exitCode':result['exitCode'],'outputHash':digest(result['output']),
                         'status':'PASS' if result['exitCode']==0 else 'FAIL','runtimeGate':'NOT_EVALUATED'}
                journal.append({'kind':'runtime-step','binding':self.session.binding,**summary},guard)
                self._capture_derived(journal,guard)
                outputs.append(summary)
                require(result['exitCode']==0,'runtime step failed; no dependent steps')
        return outputs

    def _capture_derived(self,journal,guard):
        root=Path(self.recipe['sourceDirectory'])
        actual=snapshot(root,build_links=True)
        original=self.session.bundle['payload']
        derived=('.next/','node_modules/','build-checks/','src/generated/')
        for rel,entry in actual['entries'].items():
            if entry['kind']!='file':
                require(any(p.startswith(rel+'/') for p in original) or rel.startswith(derived) or
                        rel in ('.next','node_modules','build-checks','src/generated'),'unexpected runtime directory/link')
                continue
            if rel in original:
                expected=digest(original[rel])
                if rel=='next-env.d.ts':
                    require(entry['sha256'] in (expected,self.recipe['expectedNextEnvHash']),'unapproved Next change')
                else:require(entry['sha256']==expected,'protected output source changed')
            else:
                require(rel.startswith(derived) or rel=='tsconfig.tsbuildinfo','unexpected runtime file; quarantine')
        require(set(original) <= set(actual['entries']),'runtime removed source')
        journal.append({'kind':'tree-state','path':str(root),'binding':self.session.binding,
                        'snapshot':actual,'runtimeDerived':True},guard)

    def cleanup_resources(self, *, retain_candidate=False):
        with self.session.operation('cleanup') as (journal,guard):
            resources=[]
            for row in journal.read():
                event=row['event']
                if event.get('binding')!=self.session.binding:continue
                if event['kind']=='runtime-resource':resources.append(event['resource'])
                elif event['kind']=='runtime-intent' and event.get('resource'):
                    if event['resource'] not in resources:resources.append(event['resource'])
            unique={r['name']:r for r in resources}
            for resource in reversed(list(unique.values())):
                guard()
                inspected=self.transport.run(['docker',resource['kind'],'inspect',resource['name']],30)
                if inspected['exitCode']!=0:
                    guard()
                    listing=self.transport.run(['docker',resource['kind'],'ls',*(['--all'] if resource['kind']=='container' else []),
                        '--filter','name='+resource['name'],'--format','{{.Names}}' if resource['kind']=='container' else '{{.Name}}'],30)
                    require(listing['exitCode']==0 and resource['name'] not in listing['output'].decode().splitlines(),
                            'absence/inspect error not reconciled')
                    journal.append({'kind':'resource-already-absent','resource':resource,'binding':self.session.binding},guard)
                    continue
                identifier=verify_resource(resource,loads(inspected['output']))
                journal.append({'kind':'resource-remove-intent','resource':{**resource,'id':identifier},
                                'binding':self.session.binding},guard)
                guard()
                args=['docker',resource['kind'],'rm']+(['--force'] if resource['kind']=='container' else [])+[resource['name']]
                result=self.transport.run(args,60)
                require(result['exitCode']==0,'owned resource cleanup failed')
                # Query inventory: empty exact ID/name result must demonstrate absence.
                guard()
                listing=self.transport.run(['docker',resource['kind'],'ls',*(['--all'] if resource['kind']=='container' else []),'--filter','name='+resource['name'],
                                            '--format','{{.Names}}' if resource['kind']=='container' else '{{.Name}}'],30)
                require(listing['exitCode']==0 and resource['name'] not in listing['output'].decode().splitlines(),
                        'cleanup absence unproven')
                journal.append({'kind':'resource-removed','resource':resource,'binding':self.session.binding},guard)
            for role in ('validation','staging'):
                path=self.session.wo['destinations'][role]
                if os.path.lexists(path):
                    tree=OwnedTree(path,journal,self.session.binding)
                    if role=='staging' and retain_candidate:
                        tree.verify()
                        journal.append({'kind':'retained-source-candidate','path':path,'binding':self.session.binding},guard)
                    else:tree.cleanup(guard)
        return {'status':'OWNED_RESOURCES_REMOVED','runtimeGate':'NOT_EVALUATED','executionAuthority':'none'}



def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--describe',action='store_true',required=True)
    parser.parse_args(argv)
    print(json.dumps({'executionAuthority':'none','runtimeStatus':'NOT_EXECUTED',
        'requires':'External EXECUTION_B_APPROVED, concrete hash-bound recipe and ExecutionSession API',
        'phases':list(ACTIONS),'automaticGatePromotion':False}))
    return 0




class LocalTLSRelay:
    """Local validation TLS only; constructed/listened only under live external authority.

    No trust-store modification. The caller supplies the future pinned browser driver
    while the context is active; implementation tests never instantiate this listener.
    """
    def __init__(self, session, recipe):
        self.session,self.recipe=session,recipe

    @contextlib.contextmanager
    def running(self):
        import socket
        import socketserver
        import ssl
        import threading
        with self.session.operation('http-browser') as (journal,guard):
            guard()
            recipe=self.recipe
            tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            cert=Path(recipe['tlsDirectory'])/'cert.pem'
            key=Path(recipe['tlsDirectory'])/'key.pem'
            secure_read(cert);secure_read(key)
            require(os.stat(key).st_mode & 0o077==0,'TLS key must be private')
            tls.load_cert_chain(cert,key)
            active=set();lock=threading.Lock()
            class Handler(socketserver.BaseRequestHandler):
                def handle(self):
                    guard()
                    with socket.create_connection(('127.0.0.1',recipe['httpPort']),timeout=5) as upstream:
                        with lock:active.update((self.request,upstream))
                        try:
                            with selectors.DefaultSelector() as selector:
                                selector.register(self.request,selectors.EVENT_READ,upstream)
                                selector.register(upstream,selectors.EVENT_READ,self.request)
                                while True:
                                    guard()
                                    events=selector.select(.2)
                                    for registered,_ in events:
                                        data=registered.fileobj.recv(65536)
                                        if not data:return
                                        registered.data.sendall(data)
                        finally:
                            with lock:active.discard(self.request);active.discard(upstream)
            class Server(socketserver.ThreadingTCPServer):
                allow_reuse_address=False
                daemon_threads=False
                block_on_close=True
                def get_request(self):
                    connection,address=super().get_request()
                    connection.settimeout(5)
                    try:return tls.wrap_socket(connection,server_side=True),address
                    except BaseException:
                        connection.close();raise
            journal.append({'kind':'tls-listen-intent','port':recipe['port'],'binding':self.session.binding},guard)
            guard()
            server=Server(('127.0.0.1',recipe['port']),Handler)
            worker=threading.Thread(target=server.serve_forever,name='p46-owned-tls')
            worker.start()
            try:
                yield {'origin':'https://127.0.0.1:'+str(recipe['port']), 'guard':guard,
                       'binding':self.session.binding,'executionAuthority':'none'}
            finally:
                server.shutdown()
                with lock:
                    for connection in list(active):
                        try:connection.shutdown(socket.SHUT_RDWR)
                        except OSError:pass
                        connection.close()
                server.server_close()
                worker.join(timeout=10)
                require(not worker.is_alive(),'TLS relay cleanup incomplete')

if __name__=='__main__':
    raise SystemExit(main())
