"""P4.3 operator-only local infrastructure validation, separate from corporate profiles."""
from pathlib import Path
import json,os,re,secrets,shutil,subprocess,tempfile,time,uuid
from .constants import ROOT
from .generation import read_json,json_bytes,byte_hash
from .executor import redact

NODE='node@sha256:83f487e0a63425e5b4d146fb5e5be574bcbe1b7b843d3ebafdd95eaf7767a7e5'
PG='postgres@sha256:efedf3595f1d6f415c08568ba171029bf54052e754cc9f030e3f2412b21f3d67'
LABEL='nexonova.p43.run'
FUTURE=['authentication','resource-authorization','module-crud','generation','autonomy']
class InfrastructureError(ValueError):pass
EXPECTED_VERSIONS={'node':'v22.23.2','next':'15.5.25','react':'19.2.8','typescript':'5.9.3','prisma':'7.5.0','client':'7.5.0','adapter':'7.5.0','pg':'8.16.3'}

def validate_versions(actual):
 if actual!=EXPECTED_VERSIONS:raise InfrastructureError('Version matrix mismatch; values withheld')


def gate_summary(steps,cleanup):
 ok=lambda names:all(s['passed'] for s in steps) and all(any(s['name']==n and s['passed'] for s in steps) for n in names)
 return {'compatibility':{'status':'PASS' if ok(['versions','postgres-version','generate','typecheck','build']) else 'FAIL','scope':'P4.3-only; Better Auth NOT_IMPLEMENTED'},
 'database-migrations':{'status':'PASS' if ok(['empty-db','migrate-first','migrate-again','migration-stable','runtime-ddl','write','read-after-app-restart']) else 'FAIL'},
 'build-tests':{'status':'PASS' if ok(['typecheck','unit','build','start-app','restart-app','compose-up','compose-http','compose-persistence','compose-app-prisma-read','compose-restarted-app-prisma-read']) else 'FAIL','scope':'technical-core-only'},
 'cleanup':{'status':'PASS' if cleanup else 'FAIL'},**{name:{'status':'NOT_IMPLEMENTED'} for name in FUTURE}}

class Run:
 def __init__(self,base):
  self.base=Path(base);self.id='p43-'+uuid.uuid4().hex[:16];self.client=self.base/'client';self.client.mkdir();self.work=self.base/'work'
  self.env={'PATH':'/usr/bin:/bin','HOME':str(self.client),'DOCKER_CONFIG':str(self.client)}
  self.values=[];self.resources=[];self.steps=[];self.db=[];self.active=[]
 def clean_text(self,text):
  for value in sorted(self.values,key=len,reverse=True):text=text.replace(value,'[REDACTED]')
  text=re.sub(r'postgres(?:ql)?://[^\s\"\']+','[DATABASE_URL_REDACTED]',text)
  return redact(text.replace(str(self.base),'[RUN_TEMP]'))
 def docker(self,args,*,stdin=None,timeout=180):
  return subprocess.run(['docker','--host','unix:///var/run/docker.sock',*args],env=self.env,input=stdin,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
 def record(self,name,p,expect=0):
  good=(p.returncode==expect) if isinstance(expect,int) else p.returncode!=0
  self.steps.append({'name':name,'exitCode':p.returncode,'expected':expect,'passed':good,'output':self.clean_text(p.stdout)})
  if not good:raise InfrastructureError('Step failed: '+name)
  print(name,'PASS',flush=True)
  return p
 def envfile(self,values):
  path=self.base/('env-'+uuid.uuid4().hex);fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'w') as f:f.write(''.join(k+'='+v+'\n' for k,v in values.items()))
  return path
 def register(self,kind,name):self.resources.append((kind,name))
 def owned(self,kind,name):
  if (kind,name) not in self.resources:return False
  p=self.docker([kind,'inspect',name]);
  if p.returncode:return False
  data=json.loads(p.stdout)[0];labels=data.get('Config',{}).get('Labels',{}) if kind=='container' else data.get('Labels',{})
  return labels.get(LABEL)==self.id
 def exists(self,kind,name):
  # Docker container names have slash/regex subtleties; compare exact listed names.
  column='{{.Names}}' if kind=='container' else '{{.Name}}'
  p=self.docker([kind,'ls',*(['-a'] if kind=='container' else []),'--format',column])
  if p.returncode:raise InfrastructureError('Cannot verify resource absence')
  return name in p.stdout.splitlines()
 def remove(self,kind,name):
  if not self.owned(kind,name):return False
  args=['rm','-f',name] if kind=='container' else [kind,'rm',name]
  for _ in range(20):
   self.docker(args)
   if not self.exists(kind,name):return True
   time.sleep(.1)
  return False
 def node(self,name,args,network='none',variables=None,expect=0,timeout=300):
  cname=self.id+'-'+name;self.register('container',cname);envpath=self.envfile(variables or {})
  cmd=['run','--rm','--pull=never','--name',cname,'--label',LABEL+'='+self.id,'--network',network,'--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--memory=2g','--cpus=2','--pids-limit=256','--user',f'{os.getuid()}:{os.getgid()}','--tmpfs','/tmp:rw,nosuid,nodev,size=256m','--mount',f'type=bind,source={self.work},target=/work','--workdir','/work','--env-file',str(envpath),'--env','HOME=/tmp','--env','NEXT_TELEMETRY_DISABLED=1','--env','npm_config_userconfig=/dev/null','--env','npm_config_globalconfig=/tmp/absent','--env','npm_config_cache=/work/.npm-cache','--entrypoint',args[0],NODE,*args[1:]]
  try:p=self.docker(cmd,timeout=timeout)
  finally:
   envpath.unlink(missing_ok=True)
   if self.owned('container',cname):self.remove('container',cname)
  return self.record(name,p,expect)
 def create_db(self,suffix):
  net=self.id+'-'+suffix+'-net';vol=self.id+'-'+suffix+'-data';name=self.id+'-'+suffix+'-db';database='db_'+suffix
  for kind,n,args in [('network',net,['network','create','--internal','--label',LABEL+'='+self.id,net]),('volume',vol,['volume','create','--label',LABEL+'='+self.id,vol])]:
   self.register(kind,n);p=self.docker(args)
   if p.returncode:raise InfrastructureError('Resource creation failed')
  # One narrowly privileged initialization of the newly created volume, not app/DB.
  init=name+'-volume-init';self.register('container',init)
  p=self.docker(['run','--rm','--pull=never','--name',init,'--label',LABEL+'='+self.id,'--network=none','--read-only','--cap-drop=ALL','--cap-add=CHOWN','--security-opt=no-new-privileges','--memory=128m','--pids-limit=32','--mount',f'type=volume,source={vol},target=/data','--entrypoint','chown',PG,'999:999','/data'])
  self.record(suffix+'-volume-init',p)
  passwords={role:secrets.token_hex(24) for role in ['admin','runtime','migrator']};self.values.extend(passwords.values())
  env=self.envfile({'POSTGRES_PASSWORD':passwords['admin'],'POSTGRES_USER':'postgres','POSTGRES_DB':database,'PGDATA':'/var/lib/postgresql/data/pgdata','POSTGRES_INITDB_ARGS':'--auth-host=scram-sha-256 --auth-local=trust'})
  self.register('container',name)
  p=self.docker(['run','-d','--pull=never','--name',name,'--label',LABEL+'='+self.id,'--network',net,'--network-alias','db','--user','999:999','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--memory=512m','--cpus=1','--pids-limit=128','--tmpfs','/tmp:rw,nosuid,nodev,size=64m','--tmpfs','/var/run/postgresql:rw,nosuid,nodev,uid=999,gid=999,size=16m','--mount',f'type=volume,source={vol},target=/var/lib/postgresql/data','--env-file',str(env),PG,'-c','log_statement=none','-c','log_min_error_statement=panic'])
  env.unlink();self.record(suffix+'-db-start',p)
  for _ in range(80):
   p=self.docker(['exec',name,'pg_isready','-h','127.0.0.1','-U','postgres','-d',database],timeout=5)
   if p.returncode==0:break
   time.sleep(.25)
  else:raise InfrastructureError('DB readiness timeout')
  db={'container':name,'network':net,'volume':vol,'database':database,'passwords':passwords}
  self.db.append(db)
  # Local trust only inside isolated DB container, no socket mount on host or app.
  sql=f'''CREATE ROLE bpmigrator LOGIN PASSWORD '{passwords['migrator']}';
CREATE ROLE bpruntime LOGIN PASSWORD '{passwords['runtime']}';
REVOKE ALL ON DATABASE {database} FROM PUBLIC;
GRANT CONNECT ON DATABASE {database} TO bpmigrator,bpruntime;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA app AUTHORIZATION bpmigrator;
'''
  self.record(suffix+'-roles',self.sql(db,sql))
  return db
 def sql(self,db,sql):return self.docker(['exec','-i',db['container'],'psql','-X','-v','ON_ERROR_STOP=1','-U','postgres','-d',db['database'],'-At'],stdin=sql)
 def url(self,db,role,host='db'):
  value=f"postgresql://bp{role}:{db['passwords'][role]}@{host}:5432/{db['database']}?schema=app";self.values.append(value);return value
 def finish(self):
  results=[]
  for kind,name in reversed(self.resources):
   row={'kind':kind,'name':name,'removedOrAbsent':False}
   try:row['removedOrAbsent']=self.remove(kind,name) if self.owned(kind,name) else not self.exists(kind,name)
   except (InfrastructureError,OSError,subprocess.TimeoutExpired) as error:row['error']=self.clean_text(type(error).__name__+': cleanup unverified')
   results.append(row)
  return results

def validate_core():
 report={'format':'nexonova.business-infrastructure-receipt.v1','scope':'P4.3-technical-core-only','status':'BLOCKED','readiness':'BLOCKED','steps':[]}
 target=ROOT/'docs/migration/P4_3_INFRASTRUCTURE.json'
 with tempfile.TemporaryDirectory(prefix='nexonova-p43-',dir='/var/tmp') as tmp:
  run=Run(tmp);report['runId']=run.id
  shutil.copytree(ROOT/'templates/business-platform',run.work)
  original={p.relative_to(run.work).as_posix():byte_hash(p.read_bytes()) for p in run.work.rglob('*') if p.is_file()}
  report['coreFiles']=[{'path':p,'sha256':h} for p,h in sorted(original.items())]
  report['validatorSha256']=byte_hash(Path(__file__).read_bytes())
  report['images']={'node':NODE,'postgres':PG}
  try:
   run.node('install',['npm','ci','--ignore-scripts','--no-audit','--no-fund'],network='bridge')
   run.node('prepare-prisma-engine',['node','node_modules/@prisma/engines/dist/scripts/postinstall.js'],network='bridge')
   run.node('generate',['node','node_modules/prisma/build/index.js','generate'])
   versions=run.node('versions',['node','-e',"console.log(JSON.stringify({node:process.version,next:require('next/package.json').version,react:require('react/package.json').version,typescript:require('typescript/package.json').version,prisma:require('prisma/package.json').version,client:require('@prisma/client/package.json').version,adapter:JSON.parse(require('fs').readFileSync('node_modules/@prisma/adapter-pg/package.json','utf8')).version,pg:require('pg/package.json').version}))"])
   try:validate_versions(json.loads(versions.stdout))
   except InfrastructureError:
    run.steps[-1]['passed']=False
    raise
   report['versions']=EXPECTED_VERSIONS
   run.node('typecheck',['npm','run','typecheck']);run.node('unit',['npm','test']);run.node('compile-checks',['npm','run','compile:checks']);run.node('build',['npm','run','build'])
   first=run.create_db('a');second=run.create_db('b')
   pgversion=run.record('postgres-version',run.sql(first,'SHOW server_version;'))
   if not pgversion.stdout.startswith('16.15'):
    run.steps[-1]['passed']=False
    raise InfrastructureError('PostgreSQL version mismatch')
   report['postgresVersion']=pgversion.stdout.strip()
   empty=run.sql(first,"SELECT count(*) FROM information_schema.tables WHERE table_schema='app';");run.record('empty-db',empty)
   if empty.stdout.strip()!='0':raise InfrastructureError('DB was not empty')
   runtime={'DATABASE_URL':run.url(first,'runtime')};migrator={'MIGRATION_DATABASE_URL':run.url(first,'migrator')}
   run.node('migrate-first',['node','scripts/migrate-check.mjs'],first['network'],migrator)
   before=run.sql(first,'SELECT migration_name,checksum,finished_at FROM app._prisma_migrations ORDER BY migration_name;').stdout
   run.node('migrate-again',['node','scripts/migrate-check.mjs'],first['network'],migrator)
   after=run.sql(first,'SELECT migration_name,checksum,finished_at FROM app._prisma_migrations ORDER BY migration_name;').stdout
   run.record('migration-stable',subprocess.CompletedProcess([],0 if before==after and len(after.splitlines())==1 else 1,'one stable completed migration' if before==after else 'changed'))
   run.record('runtime-grants',run.sql(first,(run.work/'validation/runtime-grants.sql').read_text()))
   run.node('runtime-ddl',['node','-e',"const {Client}=require('pg');(async()=>{const c=new Client({connectionString:process.env.DATABASE_URL});await c.connect();try{await c.query('CREATE TABLE app.forbidden(id int)');process.exitCode=1}catch(e){if(e.code!=='42501')process.exitCode=1;else console.log('DDL_DENIED_42501')}finally{await c.end()}})()"],first['network'],runtime)
   run.node('env-missing',['node','build-checks/scripts/db-check.js','read'],expect='nonzero')
   run.node('runtime-swapped',['node','build-checks/scripts/db-check.js','read'],first['network'],{'DATABASE_URL':migrator['MIGRATION_DATABASE_URL']},expect='nonzero')
   run.node('migration-swapped',['node','scripts/migrate-check.mjs'],first['network'],{'MIGRATION_DATABASE_URL':runtime['DATABASE_URL']},expect='nonzero')
   run.node('runtime-migrate-direct',['node','node_modules/prisma/build/index.js','migrate','deploy'],second['network'],{'MIGRATION_DATABASE_URL':run.url(second,'runtime')},expect='nonzero')
   run.node('db-unavailable',['node','build-checks/scripts/db-check.js','read'],'none',runtime,expect='nonzero')
   run.node('write',['node','build-checks/scripts/db-check.js','write'],first['network'],runtime)
   run.node('start-app',['node','scripts/start-check.mjs'],first['network'],runtime)
   run.node('restart-app',['node','scripts/start-check.mjs'],first['network'],runtime)
   run.node('read-after-app-restart',['node','build-checks/scripts/db-check.js','read'],first['network'],runtime)
   # Compose uses this run's already initialized volume/network; no migrations on up.
   initial_logs=run.docker(['logs',first['container']])
   if initial_logs.returncode or any(v in initial_logs.stdout for v in run.values):raise InfrastructureError('Initial DB logs unavailable or secret match; content withheld')
   run.record('db-stop-for-compose',run.docker(['stop','--time','15',first['container']]))
   if not run.remove('container',first['container']):raise InfrastructureError('Pre-Compose DB stop failed')
   override=run.work/'compose.validation.json'
   override.write_text(json.dumps({'volumes':{'database':{'external':True,'name':first['volume']}},'networks':{'private':{'external':True,'internal':False,'name':first['network']}}}))
   compose_env=run.envfile({'COMPOSE_PROJECT_NAME':run.id+'-compose','VALIDATION_RUN_ID':run.id,'APP_UID':str(os.getuid()),'APP_GID':str(os.getgid()),'POSTGRES_DB':first['database'],'POSTGRES_ADMIN_PASSWORD':first['passwords']['admin'],'DATABASE_URL':runtime['DATABASE_URL']})
   compose=['compose','--env-file',str(compose_env),'--project-directory',str(run.work),'-f',str(run.work/'compose.yaml'),'-f',str(override)]
   for service in ['db','app']:run.register('container',run.id+'-compose-'+service)
   try:
    run.record('compose-config',run.docker([*compose,'config','--quiet']))
    run.record('compose-up',run.docker([*compose,'up','-d','--wait','app']))
    first['container']=run.id+'-compose-db'
    run.node('compose-http',['node','-e',"(async()=>{const r=await fetch('http://app:3000');if(!r.ok||!(await r.text()).includes('Base técnica experimental'))process.exitCode=1;else console.log('COMPOSE_HTTP_PASS')})()"],first['network'])
    run.record('compose-app-prisma-read',run.docker([*compose,'exec','-T','app','node','build-checks/scripts/db-check.js','read']))
    run.record('compose-restart-app',run.docker([*compose,'restart','app']))
    run.record('compose-restarted-app-prisma-read',run.docker([*compose,'exec','-T','app','node','build-checks/scripts/db-check.js','read']))
    run.node('compose-persistence',['node','build-checks/scripts/db-check.js','read'],first['network'],runtime)
    # Inspect controls without publishing environment values.
    for service in ['app','db']:
     item=json.loads(run.docker(['inspect',run.id+'-compose-'+service]).stdout)[0];host=item['HostConfig']
     if not host['ReadonlyRootfs'] or host['Privileged'] or host['PortBindings'] or host['CapDrop']!=['ALL']:raise InfrastructureError('Compose restriction mismatch')
     if host['Memory']<=0 or host['PidsLimit']<=0 or host['NanoCpus']<=0:raise InfrastructureError('Missing Compose resource limits')
     if not any('no-new-privileges' in x for x in host['SecurityOpt']):raise InfrastructureError('Compose privilege control missing')
    network=json.loads(run.docker(['network','inspect',first['network']]).stdout)[0]
    if not network['Internal']:raise InfrastructureError('Business network is not internal')
    app=json.loads(run.docker(['inspect',run.id+'-compose-app']).stdout)[0]
    mounts=app['Mounts']
    if any(m['Type']=='volume' or m['Destination']=='/var/run/docker.sock' or m.get('RW') for m in mounts if m['Type']!='tmpfs'):raise InfrastructureError('Unexpected app writable/volume mount')
    run.record('readonly-app-source',run.docker(['exec',run.id+'-compose-app','node','-e',"try{require('fs').writeFileSync('/app/forbidden','x');process.exitCode=1}catch(e){if(e.code!=='EROFS'&&e.code!=='EACCES')process.exitCode=1;else console.log('WRITE_DENIED')} "]))
    report['composeRestrictionsVerified']=True
   finally:
    compose_env.unlink(missing_ok=True)

   ip=json.loads(run.docker(['inspect',first['container']]).stdout)[0]['NetworkSettings']['Networks'][first['network']]['IPAddress']
   run.node('cross-network',['node','build-checks/scripts/db-check.js','read'],second['network'],{'DATABASE_URL':run.url(first,'runtime',ip)},expect='nonzero')
   run.node('no-other-volume',['node','-e',"const fs=require('fs');if(fs.existsSync('/var/lib/postgresql/data')||fs.existsSync('/var/run/docker.sock'))process.exitCode=1;else console.log('No DB volume or Docker socket mounted')"],second['network'])
   run.node('second-db-migrate',['node','scripts/migrate-check.mjs'],second['network'],{'MIGRATION_DATABASE_URL':run.url(second,'migrator')})
   run.record('second-runtime-grants',run.sql(second,(run.work/'validation/runtime-grants.sql').read_text()))
   isolated=run.sql(second,'SELECT count(*) FROM app."TechnicalSmoke";')
   if isolated.returncode or isolated.stdout.strip()!='0':raise InfrastructureError('Second volume contains unexpected data')
   run.record('separate-volume-empty',isolated)
   run.node('second-db-no-first-data',['node','build-checks/scripts/db-check.js','read'],second['network'],{'DATABASE_URL':run.url(second,'runtime')},expect='nonzero')
   # Invalid migration on the second disposable database; never edit accepted history.
   bad=run.work/'validation/prisma/migrations/00000000000001_invalid';bad.mkdir();(bad/'migration.sql').write_text('THIS IS NOT SQL;\n')
   run.node('invalid-migration',['node','scripts/migrate-check.mjs'],second['network'],{'MIGRATION_DATABASE_URL':run.url(second,'migrator')},expect='nonzero')
   failed=run.sql(second,"SELECT count(*) FROM app._prisma_migrations WHERE migration_name='00000000000001_invalid' AND finished_at IS NULL AND logs LIKE '%42601%';")
   if failed.returncode or failed.stdout.strip()!='1':raise InfrastructureError('Invalid migration did not record SQL syntax failure')
   run.record('failed-migration-history',failed)
   shutil.rmtree(bad)
   # Real configuration rejection, before any incompatible stack can run.
   wrong=dict(EXPECTED_VERSIONS);wrong['prisma']='6.0.0'
   try:validate_versions(wrong)
   except InfrastructureError:run.steps.append({'name':'incompatible-version-rejected','exitCode':None,'expected':'rejected','passed':True,'output':'Unsupported matrix blocked before execution'})
   else:raise InfrastructureError('Incompatible version accepted')
   # An independently owned sentinel must survive this run's cleanup API.
   foreign=run.id+'-foreign-volume'
   run.record('foreign-create',run.docker(['volume','create','--label',LABEL+'=sentinel-owner',foreign]))
   try:
    if run.remove('volume',foreign):raise InfrastructureError('Foreign resource removal allowed')
    run.record('foreign-preserved',run.docker(['volume','inspect',foreign]))
   finally:
    # The test explicitly created this sentinel; delete via its independent owner check.
    inspect=run.docker(['volume','inspect',foreign])
    if inspect.returncode==0 and json.loads(inspect.stdout)[0]['Labels'].get(LABEL)=='sentinel-owner':
     run.record('foreign-sentinel-cleanup',run.docker(['volume','rm',foreign]))
     if run.exists('volume',foreign):raise InfrastructureError('Sentinel cleanup incomplete')
   # Real negative cleanup attempt: Docker must reject an occupied network.
   run.record('cleanup-incomplete-detected',run.docker(['network','rm',first['network']]),expect='nonzero')
   run.record('occupied-network-still-exists',run.docker(['network','inspect',first['network']]))
   for db in run.db:
    logs=run.docker(['logs',db['container']])
    if logs.returncode:raise InfrastructureError('DB logs unavailable for verification')
    if any(v in logs.stdout for v in run.values):raise InfrastructureError('Raw DB log secret match; content withheld')
   report['rawDatabaseLogsSecretMatches']=False
   report['status']='PASS'
  except (InfrastructureError,OSError,ValueError,subprocess.TimeoutExpired,KeyboardInterrupt) as e:
   report['status']='FAIL';report['error']=run.clean_text(type(e).__name__+': '+str(e));report['interrupted']=isinstance(e,KeyboardInterrupt)
  finally:
   report['steps']=run.steps;report['resources']=[{'kind':k,'name':n} for k,n in run.resources]
   report['cleanup']=run.finish();clean=all(x['removedOrAbsent'] for x in report['cleanup']);report['gates']=gate_summary(run.steps,clean)
   if not clean:report['status']='FAIL'
   report['originalCoreUnchanged']=all(byte_hash((ROOT/'templates/business-platform'/p).read_bytes())==h for p,h in original.items())
   raw=json.dumps(report);report['ephemeralSecretMatches']=any(value in raw for value in run.values)
   if report['ephemeralSecretMatches']:raise InfrastructureError('Evidence secret check failed; report withheld')
   target.write_bytes(json_bytes(report))
 report['temporaryDirectoryRemoved']=not Path(tmp).exists();target.write_bytes(json_bytes(report))
 archive=target.parent/'p4-3-runs';archive.mkdir(exist_ok=True);(archive/(report['runId']+'.json')).write_bytes(json_bytes(report));return report
