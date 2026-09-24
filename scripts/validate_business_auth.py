#!/usr/bin/env python3
"""Operator-only P4.4-B integration validation; no product generation."""
from pathlib import Path
import sys,json,os,shutil,subprocess,tempfile,secrets,time,socket,urllib.request,urllib.error,socketserver,threading,select,concurrent.futures,ssl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory import business_infrastructure as base
ROOT=Path(__file__).resolve().parents[1]
IMAGE=json.loads((ROOT/'infrastructure/images/node-openssl/image-lock.json').read_text())['executionReference']

class AuthRun(base.Run):
 def __init__(self,temporary):
  self.checkpoint_lock=threading.RLock()
  super().__init__(temporary)
 def checkpoint(self):
  with self.checkpoint_lock:self._checkpoint()
 def _checkpoint(self):
  folder=ROOT/'docs/migration/p4-4-b-runs';folder.mkdir(exist_ok=True)
  target=folder/(self.id+'.running.json');temporary=target.with_suffix('.tmp')
  temporary.write_text(json.dumps({'runId':self.id,'status':'RUNNING','steps':self.steps,'resources':[{'kind':k,'name':n} for k,n in self.resources]},indent=2)+'\n');temporary.replace(target)
 def clean_text(self,text):
  self.values=[value for value in self.values if value]
  return super().clean_text(text).replace(str(ROOT),'[FACTORY]').replace(str(Path.home()),'[OPERATOR_HOME]')
 def register(self,kind,name):
  super().register(kind,name);self.checkpoint()
 def record(self,name,p,expect=0):
  try:return super().record(name,p,expect)
  finally:self.checkpoint()
 def node_input(self,name,args,network='none',variables=None,stdin=None,expect=0,timeout=180):
  cname=self.id+'-'+name;self.register('container',cname);ep=self.envfile(variables or {})
  cmd=['run','--rm','-i','--pull=never','--name',cname,'--label',base.LABEL+'='+self.id,'--network',network,'--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--memory=2g','--cpus=2','--pids-limit=256','--user',f'{os.getuid()}:{os.getgid()}','--tmpfs','/tmp:rw,nosuid,nodev,size=256m','--mount',f'type=bind,src={self.work},dst=/work','--workdir','/work','--env-file',str(ep),'--env','HOME=/tmp','--env','NEXT_TELEMETRY_DISABLED=1','--env','BETTER_AUTH_TELEMETRY=0',IMAGE,*args]
  try:p=self.docker(cmd,stdin=stdin,timeout=timeout)
  finally:
   ep.unlink(missing_ok=True)
   if self.owned('container',cname):self.remove('container',cname)
  return p if expect is None else self.record(name,p,expect)
 def check(self,name,condition):
  return self.record(name,subprocess.CompletedProcess([],0 if condition else 1,'verified' if condition else 'condition not satisfied'))

class LocalRelay(socketserver.ThreadingTCPServer):
 allow_reuse_address=False
 daemon_threads=True
 def __init__(self):
  self.target=None;self.active=set();self.guard=threading.Lock()
  super().__init__(('127.0.0.1',0),RelayHandler)
 def close_run(self):
  self.shutdown();self.server_close()
  with self.guard:
   for connection in list(self.active):
    try:connection.shutdown(socket.SHUT_RDWR)
    except OSError:pass
    connection.close()
class RelayHandler(socketserver.BaseRequestHandler):
 def handle(self):
  if self.server.target is None:return
  try:
   with socket.create_connection(self.server.target,timeout=10) as upstream:
    pair=[self.request,upstream]
    with self.server.guard:self.server.active.update(pair)
    try:
     while True:
      ready,_,_=select.select(pair,[],[],30)
      if not ready:return
      for source in ready:
       data=source.recv(65536)
       if not data:return
       (upstream if source is self.request else self.request).sendall(data)
    finally:
     with self.server.guard:self.server.active.difference_update(pair)
  except OSError:return

class HttpProbe:
 def __init__(self,run,db,profile='local-test',namespace='synthetic-auth'):
  self.run=run;self.db=db;self.profile=profile
  self.relay=LocalRelay();self.port=self.relay.server_address[1]
  if not hasattr(run,'relays'):run.relays=[]
  run.relays.append(self.relay)
  if profile=='production':
   tls=run.base/'tls';tls.mkdir(mode=0o700)
   name=run.id+'-tls-fixture';run.register('container',name)
   result=run.docker(['run','--rm','--pull=never','--name',name,'--label',base.LABEL+'='+run.id,'--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--memory=128m','--cpus=1','--pids-limit=32','--user',f'{os.getuid()}:{os.getgid()}','--mount',f'type=bind,src={tls},dst=/tls',IMAGE,'openssl','req','-x509','-newkey','ec','-pkeyopt','ec_paramgen_curve:P-256','-nodes','-keyout','/tls/key.pem','-out','/tls/cert.pem','-days','1','-subj','/CN=127.0.0.1','-addext','subjectAltName=IP:127.0.0.1'])
   run.record('tls-fixture',result)
   context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(tls/'cert.pem',tls/'key.pem')
   self.relay.socket=context.wrap_socket(self.relay.socket,server_side=True)
  self.thread=threading.Thread(target=self.relay.serve_forever,daemon=True);self.thread.start()
  self.origin=('https' if profile=='production' else 'http')+'://127.0.0.1:'+str(self.port);self.name=run.id+'-'+profile+'-app'
  secret=secrets.token_hex(32);run.values.append(secret)
  self.env={'DATABASE_URL':run.url(db,'runtime'),'BETTER_AUTH_SECRET':secret,'BETTER_AUTH_URL':self.origin,'AUTH_PRODUCT_ID':namespace,'AUTH_PROFILE':profile,'NODE_ENV':'production','BETTER_AUTH_TELEMETRY':'0','NEXT_TELEMETRY_DISABLED':'1'}
 def start(self):
  r=self.run;r.register('container',self.name);ep=r.envfile(self.env)
  try:
   r.record('start-auth-app',r.docker(['run','-d','--init','--pull=never','--name',self.name,'--label',base.LABEL+'='+r.id,'--network',self.db['network'],'--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--memory=1g','--cpus=2','--pids-limit=256','--user',f'{os.getuid()}:{os.getgid()}','--tmpfs','/tmp:rw,nosuid,nodev,size=128m','--mount',f'type=bind,src={r.work},dst=/work,readonly','--workdir','/work','--env-file',str(ep),IMAGE,'node','scripts/start.mjs']))
  finally:ep.unlink(missing_ok=True)
  inspected=json.loads(r.docker(['inspect',self.name]).stdout)[0]
  address=inspected['NetworkSettings']['Networks'][self.db['network']]['IPAddress']
  self.relay.target=(address,3000)
  self.ready()
 def ready(self):
  for _ in range(100):
   try:
    if self.request('/login')[0]==200:return
   except (OSError,TimeoutError):pass
   time.sleep(.2)
  raise base.InfrastructureError('App readiness failed')
 def restart(self):
  self.run.record('restart-auth-app',self.run.docker(['restart',self.name]));self.ready()
 def request(self,path,method='GET',data=None,cookie='',headers=None):
  hdr={'Origin':self.origin,'Content-Type':'application/json',**(headers or {})}
  hdr={key:value for key,value in hdr.items() if value is not None}
  if cookie:hdr['Cookie']=cookie
  req=urllib.request.Request(self.origin+path,data=None if data is None else json.dumps(data).encode(),method=method,headers=hdr)
  try:response=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=str(self.run.base/'tls/cert.pem'))) if self.profile=='production' else urllib.request.HTTPSHandler()).open(req,timeout=10)
  except urllib.error.HTTPError as error:response=error
  payload=response.read().decode();cookies=response.headers.get_all('Set-Cookie') or []
  for value in cookies:
   token=value.split(';',1)[0].split('=',1)[-1]
   if len(token)>=16:self.run.values.append(token)
  return response.status,payload,cookies,dict(response.headers)
 def login(self,email,password,remember='omitted'):
  body={'email':email,'password':password}
  if remember!='omitted':body['rememberMe']=remember
  status,payload,cookies,headers=self.request('/api/auth/sign-in/email','POST',body)
  cookie='; '.join(c.split(';',1)[0] for c in cookies)
  return status,cookie,cookies

def auth_matrix(run,db,password,bootstrap,report):
 member_password='á🔐'+secrets.token_hex(24);run.values.append(member_password)
 run.node_input('member-fixture',['node','build-checks/validation/create-member.js'],db['network'],bootstrap,json.dumps({'database':db['database'],'email':'member@example.invalid','password':member_password}))
 app=HttpProbe(run,db);app.start()
 run.check('anonymous-api',app.request('/api/auth-check')[0]==401)
 run.check('forged-session',app.request('/api/auth-check',cookie='synthetic-auth.session_token=forged')[0]==401)
 for remember in [True,False,'omitted']:
  status,cookie,cookies=app.login('admin@example.invalid',password,remember)
  run.check('login-'+str(remember),status==200 and bool(cookie))
  session_response=app.request('/api/auth/get-session',cookie=cookie)
  run.check('session-'+str(remember),session_response[0]==200 and json.loads(session_response[1]) is not None)
  protected=app.request('/api/auth-check',cookie=cookie)
  run.check('protected-'+str(remember),protected[0]==200)
  run.check('private-api-no-store-'+str(remember),any(k.lower()=='cache-control' and 'no-store' in v and 'public' not in v for k,v in protected[3].items()))
  maximum=run.sql(db,'SELECT max(EXTRACT(EPOCH FROM ("expiresAt"-"createdAt"))) FROM app."Session";').stdout.strip()
  run.check('absolute-eight-hours-'+str(remember),0<float(maximum)<=28800)
  report.setdefault('sessionLifetimeSeconds',{})[str(remember)]=float(maximum)
  run.check('cookie-policy-'+str(remember),any('HttpOnly' in c and 'SameSite=Lax' in c and 'Path=/' in c and 'Domain=' not in c for c in cookies))
 admin_cookie=cookie
 before=run.sql(db,'SELECT "createdAt","updatedAt","expiresAt" FROM app."Session" ORDER BY id;').stdout
 app.request('/api/auth/get-session',cookie=admin_cookie)
 run.check('no-session-refresh',before==run.sql(db,'SELECT "createdAt","updatedAt","expiresAt" FROM app."Session" ORDER BY id;').stdout)
 run.check('admin-probe',app.request('/api/admin-check',cookie=admin_cookie)[0]==200)
 sensitive=run.sql(db,'SELECT token FROM app."Session" UNION ALL SELECT password FROM app."Account" WHERE password IS NOT NULL;')
 run.values.extend(sensitive.stdout.splitlines())
 html=app.request('/auth-check',cookie=admin_cookie)
 run.check('ssr-no-secrets',html[0]==200 and not any(value and value in html[1] for value in run.values))
 run.check('private-page-no-store',any(k.lower()=='cache-control' and 'no-store' in v and 'public' not in v for k,v in html[3].items()))

 app.restart()
 run.check('session-after-restart',app.request('/api/auth-check',cookie=admin_cookie)[0]==200)
 status,member_cookie,_=app.login('member@example.invalid',member_password)
 run.check('member-login',status==200)
 run.check('member-authenticated',app.request('/api/auth-check',cookie=member_cookie)[0]==200)
 run.check('member-admin-denied',app.request('/api/admin-check',cookie=member_cookie)[0]==403)
 run.check('spoofed-role-header',app.request('/api/admin-check',cookie=member_cookie,headers={'role':'admin','userId':'admin'})[0]==403)
 for path in ['/api/auth/sign-up/email','/api/auth/update-user','/api/auth/set-role']:
  run.check('closed-'+path.rsplit('/',1)[-1],app.request(path,'POST',{'role':'admin'},cookie=member_cookie)[0]==404)
 run.check('role-body-rejected',app.request('/api/auth/sign-in/email','POST',{'email':'member@example.invalid','password':member_password,'role':'admin','userId':'other'})[0]==400)
 run.check('origin-rejected',app.request('/api/auth/sign-out','POST',{},member_cookie,{'Origin':'https://untrusted.invalid'})[0]==403)
 run.check('missing-origin-rejected',app.request('/api/auth/sign-out','POST',{},member_cookie,{'Origin':None})[0]==403)
 run.check('cross-site-get-rejected',app.request('/api/auth/get-session',cookie=member_cookie,headers={'Sec-Fetch-Site':'cross-site'})[0]==403)
 run.check('spoofed-role-query',app.request('/api/admin-check?role=admin&userId=admin',cookie=member_cookie)[0]==403)
 run.check('spoofed-role-cookie',app.request('/api/admin-check',cookie=member_cookie+'; role=admin; userId=admin')[0]==403)
 run.check('null-origin-rejected',app.request('/api/auth/sign-out','POST',{},member_cookie,{'Origin':'null'})[0]==403)
 run.check('redirect-rejected',app.request('/api/auth/sign-in/email','POST',{'email':'member@example.invalid','password':member_password,'callbackURL':'https://untrusted.invalid'})[0]==400)
 run.check('logout',app.request('/api/auth/sign-out','POST',{},member_cookie)[0]==200)
 run.check('logout-database-row-removed',run.sql(db,'SELECT count(*) FROM app."Session" s JOIN app."User" u ON s."userId"=u.id WHERE u.email=$$member@example.invalid$$;').stdout.strip()=='0')
 run.check('revoked-replay',app.request('/api/auth-check',cookie=member_cookie)[0]==401)
 run.record('expire-fixture',run.sql(db,'UPDATE app."Session" SET "expiresAt"=NOW()-interval $$1 second$$;'))
 run.check('expired-get-session',app.request('/api/auth/get-session',cookie=admin_cookie)[1]=='null')
 run.check('expired-protected',app.request('/api/auth-check',cookie=admin_cookie)[0]==401)
 app.restart()
 wrong=secrets.token_hex(24);run.values.append(wrong)
 invalid=app.request('/api/auth/sign-in/email','POST',{'email':'admin@example.invalid','password':wrong})
 unknown=app.request('/api/auth/sign-in/email','POST',{'email':'absent@example.invalid','password':wrong})
 run.check('generic-login-rejection',invalid[:2]==unknown[:2] and invalid[0]==401)
 for _ in range(3):app.request('/api/auth/sign-in/email','POST',{'email':'absent@example.invalid','password':wrong})
 run.check('rate-limit',app.request('/api/auth/sign-in/email','POST',{'email':'absent@example.invalid','password':wrong})[0]==429)
 app.restart()
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  rate_results=list(pool.map(lambda _:app.request('/api/auth/sign-in/email','POST',{'email':'absent@example.invalid','password':wrong})[0],range(6)))
 run.check('concurrent-rate-limit',sorted(rate_results)==[401,401,401,401,401,429])
 logs=run.docker(['logs',app.name])
 run.check('app-logs-no-known-secrets',logs.returncode==0 and not any(v and v in logs.stdout for v in run.values))
 # Real privilege failures; each statement must fail specifically with PostgreSQL 42501.
 statements=['CREATE TABLE app.forbidden(id int)', 'INSERT INTO app."User" (id) VALUES ($$forbidden$$)', 'UPDATE app."User" SET role=$$admin$$ WHERE false', 'INSERT INTO app."Account" (id) VALUES ($$forbidden$$)', 'UPDATE app."Account" SET password=NULL WHERE false', 'SELECT * FROM app."Verification"', 'SELECT * FROM app._prisma_migrations']
 for index,statement in enumerate(statements):
  js="const {Client}=require('pg'); (async()=>{const c=new Client({connectionString:process.env.DATABASE_URL});await c.connect();try{await c.query("+json.dumps(statement)+");process.exitCode=1}catch(e){if(e.code!=='42501')process.exitCode=1;else console.log('PRIVILEGE_DENIED_42501')}finally{await c.end()}})().catch(()=>{console.error('PROBE_FAILED');process.exitCode=1})"
  run.node('privilege-'+str(index),['node','-e',js],db['network'],{'DATABASE_URL':run.url(db,'runtime')})
 run.node_input('bootstrap-runtime-denied',['npm','run','bootstrap-admin'],db['network'],{'BOOTSTRAP_DATABASE_URL':run.url(db,'runtime')},json.dumps({'database':db['database'],'email':'other@example.invalid','name':'Other','password':password}),expect='nonzero')
 run.node_input('bootstrap-migrator-denied',['npm','run','bootstrap-admin'],db['network'],{'BOOTSTRAP_DATABASE_URL':run.url(db,'migrator')},json.dumps({'database':db['database'],'email':'other@example.invalid','name':'Other','password':password}),expect='nonzero')
 run.node_input('bootstrap-other-denied',['npm','run','bootstrap-admin'],db['network'],bootstrap,json.dumps({'database':db['database'],'email':'other@example.invalid','name':'Other','password':password}),expect='nonzero')
 run.node_input('bootstrap-short-denied',['npm','run','bootstrap-admin'],db['network'],bootstrap,json.dumps({'database':db['database'],'email':'other@example.invalid','name':'Other','password':'short'}),expect='nonzero')
 for name,variables in [('missing',{}),('production-http',{**app.env,'AUTH_PROFILE':'production'}),('short-secret',{**app.env,'BETTER_AUTH_SECRET':'short'}),('swapped-runtime',{**app.env,'DATABASE_URL':run.url(db,'migrator')})]:
  run.node('config-'+name,['node','scripts/start.mjs'],variables=variables,expect='nonzero')
 app.restart()
 browser=subprocess.run(['node',str(ROOT/'scripts/check_business_auth_browser.mjs')],input=json.dumps({'origin':app.origin,'password':password,'memberPassword':member_password}),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=150,cwd=ROOT,env={'PATH':os.environ['PATH'],'HOME':str(Path.home()),'PLAYWRIGHT_BROWSERS_PATH':'/var/tmp/nexonova-p33-browsers'})
 run.record('browser',browser)
 report['browser']=json.loads(browser.stdout)
 # Database availability and permission failures must fail closed with no successful probe.
 app.restart();status,live_cookie,_=app.login('admin@example.invalid',password);run.check('failure-fixture-login',status==200)
 run.record('revoke-user-select',run.sql(db,'REVOKE SELECT ON app."User" FROM bpruntime;'))
 run.check('insufficient-permissions',app.request('/api/auth-check',cookie=live_cookie)[0]==503)
 run.record('restore-user-select',run.sql(db,'GRANT SELECT ON app."User" TO bpruntime;'))
 run.record('stop-database',run.docker(['stop',db['container']]))
 run.check('database-down',app.request('/api/auth-check',cookie=live_cookie)[0]==503)
 run.node_input('bootstrap-database-down',['npm','run','bootstrap-admin'],db['network'],bootstrap,json.dumps({'database':db['database'],'email':'admin@example.invalid','name':'Synthetic Admin','password':password}),expect='nonzero')
 run.record('restart-database',run.docker(['start',db['container']]))
 for _ in range(100):
  if run.docker(['exec',db['container'],'pg_isready','-U','postgres','-d',db['database']]).returncode==0:break
  time.sleep(.2)
 run.check('database-restarted-session-valid',app.request('/api/auth-check',cookie=live_cookie)[0]==200)
 run.record('revoke-session-offline',run.sql(db,'DELETE FROM app."Session" WHERE "userId" IN (SELECT id FROM app."User" WHERE email=$$admin@example.invalid$$);'))
 run.check('revoked-get-session',app.request('/api/auth/get-session',cookie=live_cookie)[1]=='null')
 run.check('revoked-protected',app.request('/api/auth-check',cookie=live_cookie)[0]==401)
 # Collect sensitive synthetic values only in memory for exact secondary evidence scanning.
 sensitive=run.sql(db,'SELECT token FROM app."Session" UNION ALL SELECT password FROM app."Account" WHERE password IS NOT NULL;')
 if sensitive.returncode:raise base.InfrastructureError('Secret evidence scan unavailable')
 run.values.extend(sensitive.stdout.splitlines())
 for name in [app.name,db['container']]:
  logs=run.docker(['logs',name]);run.check('final-log-scan-'+('app' if name==app.name else 'db'),logs.returncode==0 and not any(v and v in logs.stdout for v in run.values))
 run.record('retire-bootstrap',run.sql(db,'ALTER ROLE bpbootstrap NOLOGIN; REVOKE ALL ON app."User",app."Account" FROM bpbootstrap; REVOKE USAGE ON SCHEMA app FROM bpbootstrap;'))
 # Separate ephemeral HTTPS fixture, not deployment: real Secure cookie transport.
 secure=HttpProbe(run,db,profile='production',namespace='synthetic-secure');secure.start()
 status,secure_cookie,attributes=secure.login('admin@example.invalid',password)
 run.check('secure-login',status==200 and any('; Secure' in c and '; HttpOnly' in c for c in attributes))
 run.check('secure-session',secure.request('/api/auth-check',cookie=secure_cookie)[0]==200)
 # Use a currently valid source session; a revoked cookie would not prove isolation.
 run.check('cookie-source-still-valid',secure.request('/api/auth-check',cookie=secure_cookie)[0]==200)
 run.check('cookie-namespace-isolation',app.request('/api/auth-check',cookie=secure_cookie)[0]==401)
 renamed=secure_cookie.replace('__Secure-synthetic-secure.','synthetic-auth.').replace('synthetic-secure.','synthetic-auth.')
 run.check('cookie-signing-secret-isolation',renamed!=secure_cookie and app.request('/api/auth-check',cookie=renamed)[0]==401)
 browser_tls=subprocess.run(['node',str(ROOT/'scripts/check_business_auth_browser.mjs')],input=json.dumps({'origin':secure.origin,'password':password,'memberPassword':member_password,'selfSignedFixture':True}),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=150,cwd=ROOT,env={'PATH':os.environ['PATH'],'HOME':str(Path.home()),'PLAYWRIGHT_BROWSERS_PATH':'/var/tmp/nexonova-p33-browsers'})
 run.record('browser-https',browser_tls);report['browserHttps']=json.loads(browser_tls.stdout)
 # Cleanup negative scenarios are confined to this run and an explicitly owned sentinel.
 run.node('ordinary-process-failure',['node','-e','process.exit(7)'],expect=7)
 run.check('ordinary-process-cleaned',not run.exists('container',run.id+'-ordinary-process-failure'))
 timed_out=False
 try:run.node('timeout-process',['node','-e',"console.log('TIMEOUT_STARTED');setTimeout(()=>{},60000)"],timeout=2)
 except subprocess.TimeoutExpired as error:
  captured=error.stdout or b''
  timed_out='TIMEOUT_STARTED' in (captured.decode() if isinstance(captured,bytes) else captured)
 run.check('timeout-process-cleaned',timed_out and not run.exists('container',run.id+'-timeout-process'))
 run.record('occupied-network-rejected',run.docker(['network','rm',db['network']]),expect='nonzero')
 sentinel=run.id+'-foreign-sentinel'
 run.record('sentinel-created',run.docker(['volume','create','--label',base.LABEL+'='+run.id+'-other-owner',sentinel]))
 try:run.check('foreign-resource-preserved',not run.remove('volume',sentinel) and run.exists('volume',sentinel))
 finally:
  info=json.loads(run.docker(['volume','inspect',sentinel]).stdout)[0]
  if info.get('Labels',{}).get(base.LABEL)==run.id+'-other-owner':run.record('sentinel-creator-cleanup',run.docker(['volume','rm',sentinel]))
 run.check('sentinel-absent',not run.exists('volume',sentinel))
 report['authSmoke']='PASS';report['appPortWasLoopbackOnly']=True

def bootstrap_race(run,report):
 db=run.create_db('race');runtime={'MIGRATION_DATABASE_URL':run.url(db,'migrator')}
 run.node('race-migrate',['npm','run','migrate'],db['network'],runtime)
 db['passwords']['bootstrap']=secrets.token_hex(24);run.values.append(db['passwords']['bootstrap'])
 run.record('race-bootstrap-role',run.sql(db,"CREATE ROLE bpbootstrap LOGIN PASSWORD '"+db['passwords']['bootstrap']+"'; GRANT CONNECT ON DATABASE "+db['database']+" TO bpbootstrap;"+(run.work/'validation/bootstrap-grants.sql').read_text()))
 env={'BOOTSTRAP_DATABASE_URL':run.url(db,'bootstrap')};password=secrets.token_hex(24);run.values.append(password)
 def attempt(i):
  return run.node_input('concurrent-bootstrap-'+str(i),['npm','run','bootstrap-admin'],db['network'],env,json.dumps({'database':db['database'],'email':f'candidate{i}@example.invalid','name':'Synthetic Candidate','password':password}),expect=None)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(attempt,[1,2]))
 run.check('bootstrap-concurrent-outcomes',sorted(p.returncode for p in results)==[0,1])
 counts=run.sql(db,'SELECT (SELECT count(*) FROM app."User"),(SELECT count(*) FROM app."Account"),(SELECT count(*) FROM app."Session");')
 run.check('bootstrap-concurrent-atomic',counts.returncode==0 and counts.stdout.strip()=='1|1|0')
 run.record('race-retire-bootstrap',run.sql(db,'ALTER ROLE bpbootstrap NOLOGIN;'))
 report['bootstrapConcurrent']={'attempts':2,'createdAdmins':1,'createdAccounts':1,'sessions':0}
 # Deliberately partial identity in this disposable race DB; never repair/promote it.
 run.record('partial-identity-fixture',run.sql(db,"INSERT INTO app.\"User\" (id,name,email,role,\"updatedAt\") VALUES ('partial','Partial fixture','partial@example.invalid','admin',NOW()); ALTER ROLE bpbootstrap LOGIN;"))
 run.node_input('bootstrap-partial-denied',['npm','run','bootstrap-admin'],db['network'],env,json.dumps({'database':db['database'],'email':'partial@example.invalid','name':'Partial fixture','password':password}),expect='nonzero')
 run.check('partial-not-repaired',run.sql(db,'SELECT count(*) FROM app."Account" WHERE "userId"=$$partial$$;').stdout.strip()=='0')
 run.record('partial-retire-bootstrap',run.sql(db,'ALTER ROLE bpbootstrap NOLOGIN;'))

def _validate():
 report={'phase':'P4.4-B','status':'BLOCKED','readiness':'BLOCKED','steps':[]}
 target=ROOT/'docs/migration/P4_4_B_AUTH_PROGRESS.json'
 with tempfile.TemporaryDirectory(prefix='nexonova-p44b-auth-',dir='/var/tmp') as tmp:
  run=AuthRun(tmp);run.id=run.id.replace('p43-','p44b-');report['runId']=run.id
  shutil.copytree(ROOT/'templates/business-platform-auth',run.work)
  cache=Path('/var/tmp/p44b-auth-compat-qgpgn1sx/.npm-cache')
  if cache.exists():shutil.copytree(cache,run.work/'.npm-cache')
  try:
   run.node('install',['npm','ci','--ignore-scripts','--no-audit','--no-fund'],network='bridge')
   run.node('engine',['node','node_modules/@prisma/engines/dist/scripts/postinstall.js'],network='bridge')
   versions=run.node('versions',['node','-e',"const fs=require('fs');const pkgs={next:'next',react:'react',typescript:'typescript',prisma:'prisma',client:'@prisma/client',adapter:'@prisma/adapter-pg',pg:'pg',betterAuth:'better-auth'};console.log(JSON.stringify({node:process.version,...Object.fromEntries(Object.entries(pkgs).map(([key,pkg])=>[key,JSON.parse(fs.readFileSync('node_modules/'+pkg+'/package.json')).version]))}))"])
   actual=json.loads(versions.stdout);run.check('exact-versions',actual=={**base.EXPECTED_VERSIONS,'betterAuth':'1.7.5'});report['versions']=actual
   run.node('openssl',['openssl','version'])
   run.node('generate',['node','node_modules/prisma/build/index.js','generate'])
   run.node('compile',['npm','run','compile:checks'])
   run.node('typecheck',['npm','run','typecheck'])
   run.node('unit',['npm','test'])
   run.node('build',['npm','run','build'])
   run.node('migration-sql',['node','-e',"const {spawnSync}=require('node:child_process'); const fs=require('node:fs'); const p=spawnSync(process.execPath,['node_modules/prisma/build/index.js','migrate','diff','--from-empty','--to-schema','prisma/auth/schema.prisma','--script'],{encoding:'utf8'}); if(p.status!==0){console.error('MIGRATION_DIFF_FAILED');process.exit(1)}; fs.mkdirSync('prisma/auth/migrations/00000000000000_auth_initial',{recursive:true}); fs.writeFileSync('prisma/auth/migrations/00000000000000_auth_initial/migration.sql',p.stdout); console.log('MIGRATION_CANDIDATE_WRITTEN');"])
   migration=run.work/'prisma/auth/migrations/00000000000000_auth_initial/migration.sql'
   sql=migration.read_text()
   # app is pre-provisioned with owner bpmigrator. No database CREATE privilege.
   sql=sql.replace('-- CreateSchema\nCREATE SCHEMA IF NOT EXISTS "app";\n', '')
   if 'CREATE SCHEMA' in sql:raise base.InfrastructureError('Unexpected schema creation')
   reviewed=(ROOT/'templates/business-platform-auth/prisma/auth/migrations/00000000000000_auth_initial/migration.sql').read_text()
   run.check('reviewed-migration-identical',sql==reviewed)
   migration.write_text(reviewed)
   (migration.parent.parent/'migration_lock.toml').write_text('provider = "postgresql"\n')
   # Candidate SQL is reviewed before promotion to template; no automatic overwrite.
   report['migrationSql']=sql
   db=run.create_db('auth')
   pg_version=run.record('postgres-version',run.sql(db,'SHOW server_version;'));run.check('postgres-16-15',pg_version.stdout.startswith('16.15'));report['postgresVersion']=pg_version.stdout.strip()
   env={'MIGRATION_DATABASE_URL':run.url(db,'migrator')}
   run.node('migrate',['npm','run','migrate'],db['network'],env)
   before=run.sql(db,'SELECT checksum,finished_at FROM app._prisma_migrations;').stdout
   run.node('migrate-repeat',['npm','run','migrate'],db['network'],env)
   run.check('migration-stable',before==run.sql(db,'SELECT checksum,finished_at FROM app._prisma_migrations;').stdout)
   run.record('runtime-grants',run.sql(db,(run.work/'validation/runtime-grants.sql').read_text()))
   run.node('migrator-url-swapped',['npm','run','migrate'],db['network'],{'MIGRATION_DATABASE_URL':run.url(db,'runtime')},expect='nonzero')
   direct=run.node('runtime-direct-migrate-denied',['node','node_modules/prisma/build/index.js','migrate','deploy'],db['network'],{'MIGRATION_DATABASE_URL':run.url(db,'runtime')},expect='nonzero')
   run.check('runtime-direct-migrate-permission-error','permission denied' in direct.stdout.lower())

   db['passwords']['bootstrap']=secrets.token_hex(24);run.values.append(db['passwords']['bootstrap'])
   run.record('bootstrap-role',run.sql(db,"CREATE ROLE bpbootstrap LOGIN PASSWORD '"+db['passwords']['bootstrap']+"'; GRANT CONNECT ON DATABASE "+db['database']+" TO bpbootstrap;"+(run.work/'validation/bootstrap-grants.sql').read_text()))
   password=secrets.token_hex(24);run.values.append(password)
   payload=json.dumps({'database':db['database'],'name':'Synthetic Admin','email':'admin@example.invalid','password':password})
   bootstrap={'BOOTSTRAP_DATABASE_URL':run.url(db,'bootstrap')}
   run.record('bootstrap-account-insert-revoke',run.sql(db,'REVOKE INSERT ON app."Account" FROM bpbootstrap;'))
   run.node_input('bootstrap-insufficient-permission',['npm','run','bootstrap-admin'],db['network'],bootstrap,payload,expect='nonzero')
   run.check('bootstrap-rollback-no-orphan',run.sql(db,'SELECT (SELECT count(*) FROM app."User"),(SELECT count(*) FROM app."Account");').stdout.strip()=='0|0')
   run.record('bootstrap-account-insert-restore',run.sql(db,'GRANT INSERT ON app."Account" TO bpbootstrap;'))
   run.node_input('bootstrap',['npm','run','bootstrap-admin'],db['network'],bootstrap,payload)
   run.node_input('bootstrap-repeat',['npm','run','bootstrap-admin'],db['network'],bootstrap,payload)
   run.check('single-admin',run.sql(db,'SELECT count(*) FROM app."User" WHERE role=$$admin$$;').stdout.strip()=='1')
   bootstrap_race(run,report)
   auth_matrix(run,db,password,bootstrap,report)
   for database in run.db:
    found=run.sql(database,'SELECT token FROM app."Session" UNION ALL SELECT password FROM app."Account" WHERE password IS NOT NULL;')
    if found.returncode:raise base.InfrastructureError('Final sensitive-value collection failed')
    run.values.extend(found.stdout.splitlines())
   for kind,name in run.resources:
    if kind=='container' and (name.endswith('-app') or name.endswith('-db')) and run.owned(kind,name):
     logs=run.docker(['logs',name]);run.check('final-raw-log-scan-'+name,logs.returncode==0 and not any(value and value in logs.stdout for value in run.values))
   report['containerPolicies']=[]
   for kind,name in run.resources:
    if kind=='container' and (name.endswith('-app') or name.endswith('-db')) and run.owned(kind,name):
     item=json.loads(run.docker(['inspect',name]).stdout)[0];host=item['HostConfig']
     run.check('container-restrictions-'+name,not host['Privileged'] and host['ReadonlyRootfs'] and 'ALL' in host['CapDrop'] and any('no-new-privileges' in option for option in host['SecurityOpt']) and not host.get('PortBindings'))
     for network in item['NetworkSettings']['Networks']:
      run.check('internal-network-'+name,json.loads(run.docker(['network','inspect',network]).stdout)[0]['Internal'] is True)
     report['containerPolicies'].append({'name':name,'user':item['Config']['User'],'readonlyRootfs':host['ReadonlyRootfs'],'capDrop':host['CapDrop'],'securityOpt':host['SecurityOpt'],'memoryBytes':host['Memory'],'nanoCpus':host['NanoCpus'],'pidsLimit':host['PidsLimit'],'publishedPorts':host.get('PortBindings') or {}})
   report['status']='PASS';report['scope']='P4.4-B auth integration only; human review pending'
  except Exception as error:
   report['status']='FAIL';report['error']=type(error).__name__+(': '+str(error) if isinstance(error,base.InfrastructureError) else ': validation stopped; sensitive details withheld')
  finally:
   report['steps']=run.steps
   report['diagnostics']=[]
   for kind,name in run.resources:
    if kind=='container' and name.endswith('-app') and run.owned(kind,name):
     log=run.docker(['logs','--tail','35',name]);report['diagnostics'].append({'component':'auth-app','output':run.clean_text(log.stdout)})
   for relay in getattr(run,'relays',[]):relay.close_run()
   report['hostRelaysClosed']=all(relay.socket.fileno()==-1 for relay in getattr(run,'relays',[]))
   report['cleanup']=run.finish()
   report['cleanupPassed']=all(x['removedOrAbsent'] for x in report['cleanup'])
   if not report['cleanupPassed']:report['status']='FAIL'
   report['gates']={k:'NOT_IMPLEMENTED' for k in ['resource-authorization','module-crud','generation','autonomy']}
   archive=ROOT/'docs/migration/p4-4-b-runs';archive.mkdir(exist_ok=True)
   (archive/(run.id+'.json')).write_text(json.dumps(report,indent=2)+'\n')
   target.write_text(json.dumps(report,indent=2)+'\n')
   (archive/(run.id+'.running.json')).unlink(missing_ok=True)
 report['temporaryDirectoryRemoved']=not Path(tmp).exists()
 passed=report['status']=='PASS' and report['temporaryDirectoryRemoved'] and report['hostRelaysClosed'] and report['cleanupPassed']
 if not passed:report['status']='FAIL'
 for gate in ['compatibility','database-migrations','authentication','auth-role-probes','build-tests']:
  report['gates'][gate]='PASS' if passed else 'FAIL'
 report['gates']['cleanup']='PASS' if report['cleanupPassed'] and report['hostRelaysClosed'] and report['temporaryDirectoryRemoved'] else 'FAIL'
 target.write_text(json.dumps(report,indent=2)+'\n')
 (ROOT/'docs/migration/p4-4-b-runs'/(report['runId']+'.json')).write_text(json.dumps(report,indent=2)+'\n')
 print(report['status'],flush=True)
 return report
def validate():
 original=(base.NODE,base.LABEL)
 base.NODE=IMAGE;base.LABEL='nexonova.p44b.auth'
 try:return _validate()
 finally:base.NODE,base.LABEL=original

if __name__=='__main__':
 result=validate();sys.exit(0 if result['status']=='PASS' else 1)
