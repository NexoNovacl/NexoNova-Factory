#!/usr/bin/env python3
"""P4.4-B missing subcases only. Never invokes or overwrites the historical runner."""
import concurrent.futures, hashlib, json, os, secrets, shutil, statistics, subprocess, sys, tempfile, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import validate_business_auth as prior
ROOT=prior.ROOT
OUT=ROOT/'docs/migration/p4-4-b-continuation'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,data):
 temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');temp.replace(path)
class Run(prior.AuthRun):
 def _checkpoint(self):
  OUT.mkdir(exist_ok=True)
  dump(OUT/(self.id+'.running.json'),{'runId':self.id,'status':'RUNNING','sourceHashes':getattr(self,'source_hashes',{}),'steps':self.steps,'resources':[{'kind':k,'name':n} for k,n in self.resources]})
 def check(self,name,condition):return super().check(name,condition)

def browser(r,app,mode,**values):
 p=subprocess.run(['node',str(ROOT/'scripts/check_business_auth_continuation.mjs')],input=json.dumps({'mode':mode,'origin':app.origin,'secure':app.profile=='production',**values}),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120,env={**os.environ,'PLAYWRIGHT_BROWSERS_PATH':'/var/tmp/nexonova-p33-browsers'})
 r.record('browser-'+mode+'-'+values.get('case',''),p)
 data=json.loads(p.stdout);r.check('browser-result-'+mode+'-'+values.get('case',''),data['status']=='PASS')
 return data

def setup_db(r,suffix):
 db=r.create_db(suffix)
 r.node(suffix+'-migrate',['npm','run','migrate'],db['network'],{'MIGRATION_DATABASE_URL':r.url(db,'migrator')})
 r.record(suffix+'-runtime-grants',r.sql(db,(r.work/'validation/runtime-grants.sql').read_text()))
 db['passwords']['bootstrap']=secrets.token_hex(24);r.values.append(db['passwords']['bootstrap'])
 r.record(suffix+'-bootstrap-grants',r.sql(db,"CREATE ROLE bpbootstrap LOGIN PASSWORD '"+db['passwords']['bootstrap']+"'; GRANT CONNECT ON DATABASE "+db['database']+" TO bpbootstrap;"+(r.work/'validation/bootstrap-grants.sql').read_text()))
 return db

def bootstrap(r,db,password,name,email='admin@example.invalid',expect=0):
 return r.node_input(name,['node','build-checks/scripts/bootstrap-admin.js'],db['network'],{'BOOTSTRAP_DATABASE_URL':r.url(db,'bootstrap')},json.dumps({'database':db['database'],'email':email,'name':'Synthetic Admin','password':password}),expect=expect)

def snapshot(r,db):
 # Raw state remains in memory; hashes/tokens never written to receipts.
 p=r.sql(db,'SELECT row_to_json(u) FROM app."User" u ORDER BY id; SELECT row_to_json(a) FROM app."Account" a ORDER BY id; SELECT row_to_json(s) FROM app."Session" s ORDER BY id; SELECT row_to_json(v) FROM app."Verification" v ORDER BY id;')
 if p.returncode:raise prior.base.InfrastructureError('State snapshot unavailable')
 return p.stdout

def session_checks(r,app,cookie,allowed,name):
 r.check(name+'-probe',app.request('/api/auth-check',cookie=cookie)[0]==(200 if allowed else 401))
 response=app.request('/api/auth/get-session',cookie=cookie)
 r.check(name+'-better-auth',response[0]==200 and (json.loads(response[1]) is not None)==allowed)

def main():
 OUT.mkdir(exist_ok=True)
 resume='--remaining-b10' in sys.argv
 prior.base.NODE=prior.IMAGE;prior.base.LABEL='nexonova.p44b.continuation'
 paths=list((ROOT/'templates/business-platform-auth').rglob('*'))+[ROOT/'scripts/validate_business_auth_continuation.py',ROOT/'scripts/check_business_auth_continuation.mjs',ROOT/'scripts/validate_business_auth.py',ROOT/'factory/business_infrastructure.py',ROOT/'infrastructure/images/node-openssl/image-lock.json']
 hashes={str(p.relative_to(ROOT)):digest(p) for p in paths if p.is_file()}
 report={'phase':'P4.4-B','status':'RUNNING','readiness':'BLOCKED','sourceHashes':hashes,'images':{'node':prior.IMAGE,'postgres':prior.base.PG},'recoveryCheckpoint':{'path':'docs/migration/P4_4_B_RECOVERY_AUDIT.json','sha256':digest(ROOT/'docs/migration/P4_4_B_RECOVERY_AUDIT.json')},'setupReason':'Rebuild disposable app and databases to execute missing subcases; recovered 160-check runner is not invoked.','browser':[]}
 with tempfile.TemporaryDirectory(prefix='nexonova-p44b-continuation-',dir='/var/tmp') as tmp:
  r=Run(tmp);r.id=r.id.replace('p43-','p44bc-');r.source_hashes=hashes;report['runId']=r.id;report['resumeFrom']='p44bc-965191032d2d4a9a: B10 onward' if resume else None;r.checkpoint()
  validators=OUT/'validators';validators.mkdir(exist_ok=True)
  shutil.copy2(__file__,validators/(r.id+'.py'))
  shutil.copy2(ROOT/'scripts/check_business_auth_continuation.mjs',validators/(r.id+'.mjs'))
  shutil.copytree(ROOT/'templates/business-platform-auth',r.work)
  cache=Path('/var/tmp/p44b-auth-compat-qgpgn1sx/.npm-cache')
  if cache.exists():shutil.copytree(cache,r.work/'.npm-cache')
  try:
   r.node('setup-install',['npm','ci','--ignore-scripts','--no-audit','--no-fund'],network='bridge')
   r.node('setup-engine',['node','node_modules/@prisma/engines/dist/scripts/postinstall.js'],network='bridge')
   r.node('setup-generate',['node','node_modules/prisma/build/index.js','generate'])
   r.node('setup-compile',['npm','run','compile:checks'])
   r.node('setup-build',['npm','run','build'])
   a=setup_db(r,'continuationa')
   tables=r.sql(a,"SELECT tablename FROM pg_tables WHERE schemaname='app' ORDER BY tablename;")
   report['schemaTables']=tables.stdout.splitlines()
   r.check('B02-exact-live-table-inventory',tables.returncode==0 and report['schemaTables']==['Account','Session','User','Verification','_prisma_migrations'])
   password=secrets.token_hex(24);r.values.append(password)
   if resume:
    bootstrap(r,a,password,'resume-bootstrap')
    app=prior.HttpProbe(r,a);app.start()
    status,fresh,_=app.login('admin@example.invalid',password);r.check('resume-valid-session',status==200)
   else:
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
     results=list(pool.map(lambda n:bootstrap(r,a,password,'same-email-'+str(n),expect=None),[1,2]))
    r.check('B04-same-email-concurrent-outcomes',all(p.returncode==0 for p in results) and sorted(p.stdout.strip() for p in results)==['ALREADY_INITIALIZED','CREATED'])
    counts=r.sql(a,'SELECT (SELECT count(*) FROM app."User" WHERE role=\'admin\'),(SELECT count(*) FROM app."Account" WHERE "providerId"=\'credential\'),(SELECT count(*) FROM app."Session");')
    r.check('B04-same-email-one-admin-account-no-session',counts.returncode==0 and counts.stdout.strip()=='1|1|0')
    before=snapshot(r,a);alternate=secrets.token_hex(24);r.values.append(alternate)
    bootstrap(r,a,alternate,'repeat-new-password');r.check('B04-repeat-all-state-unchanged',snapshot(r,a)==before)
    bootstrap(r,a,password,'different-email',email='other@example.invalid',expect='nonzero');r.check('B04-other-all-state-unchanged',snapshot(r,a)==before)
    bootstrap(r,a,'short','short-password',expect='nonzero');r.check('B04-invalid-all-state-unchanged',snapshot(r,a)==before)
    member_password='á🔐'+secrets.token_hex(24);r.values.append(member_password)
    r.node_input('member-fixture',['node','build-checks/validation/create-member.js'],a['network'],{'BOOTSTRAP_DATABASE_URL':r.url(a,'bootstrap')},json.dumps({'database':a['database'],'email':'member@example.invalid','password':member_password}))
    before=snapshot(r,a);bootstrap(r,a,password,'member-existing',email='member@example.invalid',expect='nonzero');r.check('B04-member-no-promotion-state-unchanged',snapshot(r,a)==before)
    r.record('partial-fixture',r.sql(a,"INSERT INTO app.\"User\"(id,name,email,role,\"updatedAt\") VALUES ('partial','Partial','partial@example.invalid','admin',NOW());"))
    before=snapshot(r,a);bootstrap(r,a,password,'partial-existing',email='partial@example.invalid',expect='nonzero');r.check('B04-partial-full-state-unchanged',snapshot(r,a)==before)
    app=prior.HttpProbe(r,a);app.start()
    report['browser'].append(browser(r,app,'negative-login',wrongPassword=alternate))
    app.restart()
    timings={'wrong':[],'unknown':[]}
    for i in range(3):
     app.restart()
     for kind in (['wrong','unknown'] if i%2==0 else ['unknown','wrong']):
      start=time.perf_counter();res=app.request('/api/auth/sign-in/email','POST',{'email':'admin@example.invalid' if kind=='wrong' else 'absent@example.invalid','password':alternate});timings[kind].append(round((time.perf_counter()-start)*1000,2));r.check('B05-timing-generic-'+kind+'-'+str(i),res[0]==401 and json.loads(res[1])=={'error':'AUTH_REJECTED'})
    report['timingReview']={'milliseconds':timings,'medianMilliseconds':{k:statistics.median(v) for k,v in timings.items()},'scope':'Three alternating pairs; cold-start/order noise and small sample. No formal indistinguishability claim.'}
    app.restart();status,cookie,_=app.login('admin@example.invalid',password);r.check('B04-original-password-retained',status==200)
    for name,value,allowed in [('valid',cookie,True),('absent','',False),('forged','synthetic-auth.session_token=forged',False)]:report['browser'].append(browser(r,app,'session',case=name,cookie=value,allowed=allowed))
    # Coherent timestamps preserve the configured 28800s lifetime. Test both sides without changing app clocks/constants.
    r.record('B07-before-boundary-fixture',r.sql(a,'UPDATE app."Session" SET "createdAt"=NOW()-interval \'7 hours 59 minutes\', "updatedAt"=NOW()-interval \'7 hours 59 minutes\', "expiresAt"=NOW()+interval \'1 minute\';'))
    before=snapshot(r,a);session_checks(r,app,cookie,True,'B07-before-eight-hours');r.check('B07-no-refresh-near-boundary',snapshot(r,a)==before)
    r.record('B07-boundary-fixture',r.sql(a,'UPDATE app."Session" SET "createdAt"=NOW()-interval \'8 hours\', "updatedAt"=NOW()-interval \'8 hours\', "expiresAt"=NOW();'))
    session_checks(r,app,cookie,False,'B07-at-or-after-eight-hours')
    report['browser'].append(browser(r,app,'session',case='expired',cookie=cookie,allowed=False))
    app.restart();session_checks(r,app,cookie,False,'B12-expired-after-restart')
    # A supplied forged or previously valid token must not become the next session token.
    status,fresh,_=app.login('admin@example.invalid',password);r.check('B08-new-session-different',status==200 and fresh!=cookie)
    forged='synthetic-auth.session_token=chosen-attacker-value'
    response=app.request('/api/auth/sign-in/email','POST',{'email':'admin@example.invalid','password':password},cookie=forged)
    fixed='; '.join(c.split(';',1)[0] for c in response[2]);r.check('B08-fixation-rejected',response[0]==200 and fixed and fixed not in [forged,fresh,cookie])
    session_checks(r,app,forged,False,'B08-forged-still-invalid')
    r.check('B08-logout-new',app.request('/api/auth/sign-out','POST',{},fixed)[0]==200)
    app.restart();session_checks(r,app,fixed,False,'B12-revoked-after-restart');session_checks(r,app,fresh,True,'B12-live-control-after-restart')
   before=snapshot(r,a)
   for i,path in enumerate(['/api/auth/sign-up%2Femail','/api/auth/%73ign-up/email','/api/auth/%75pdate-user','/api/auth/sign-up%252Femail','/api/auth/sign-up/email/','/api/auth//sign-up/email']):
    res=app.request(path,'POST',{'email':'encoded@example.invalid','password':password,'role':'admin'})
    chain=[res[0]]
    if res[0] in [307,308]:
     location=next((v for k,v in res[3].items() if k.lower()=='location'),'')
     r.check('B10-normalization-local-'+str(i),location=='/api/auth/sign-up/email')
     res=app.request(location,'POST',{'email':'encoded@example.invalid','password':password,'role':'admin'});chain.append(res[0])
    report.setdefault('encodedPathResponses',[]).append({'path':path,'statuses':chain})
    r.check('B10-encoded-closed-'+str(i),res[0] in [400,403,404,405])
   r.check('B10-encoded-no-state-change',snapshot(r,a)==before)
   unknown=r.sql(a,"UPDATE app.\"User\" SET role='unknown' WHERE email='member@example.invalid';")
   r.check('B10-unknown-role-database-rejected',unknown.returncode!=0 and 'invalid input value for enum' in unknown.stdout and snapshot(r,a)==before)
   res=app.request('/api/auth/sign-in/email','POST',{'email':'admin@example.invalid','password':password,'role':'unknown'});r.check('B10-unknown-role-input-rejected',res[0]==400 and snapshot(r,a)==before)
   malicious={'X-Forwarded-Host':'untrusted.invalid','X-Forwarded-Proto':'https','X-Forwarded-For':'198.51.100.1','Forwarded':'for=198.51.100.1;host=untrusted.invalid;proto=https','X-Real-IP':'198.51.100.1'}
   r.check('B14-forwarded-origin-cannot-bypass',app.request('/api/auth/sign-out','POST',{},fresh,{**malicious,'Origin':'https://untrusted.invalid'})[0]==403)
   app.restart()
   res=app.request('/api/auth/sign-in/email','POST',{'email':'admin@example.invalid','password':password},headers=malicious)
   r.check('B14-forwarded-host-cookie-policy',res[0]==200 and all('untrusted.invalid' not in c and 'Domain=' not in c and '; Secure' not in c for c in res[2]))
   before=snapshot(r,a)
   for i,long_password in enumerate(['á'*129,'🔐'*65]):
    r.values.append(long_password);res=app.request('/api/auth/sign-in/email','POST',{'email':'admin@example.invalid','password':long_password});r.check('B16-overlong-integrated-'+str(i),res[0]==400 and snapshot(r,a)==before)
    bootstrap(r,a,long_password,'overlong-bootstrap-'+str(i),expect='nonzero');r.check('B16-overlong-bootstrap-state-'+str(i),snapshot(r,a)==before)
   app.restart();start=time.monotonic()
   for i in range(5):r.check('B15-budget-'+str(i),app.request('/api/auth/sign-in/email','POST',{'email':'absent@example.invalid','password':alternate},headers={**malicious,'X-Forwarded-For':'198.51.100.'+str(i+1)})[0]==401)
   res=app.request('/api/auth/sign-in/email','POST',{'email':'absent@example.invalid','password':alternate});r.check('B15-429-retry-after',res[0]==429 and any(k.lower()=='retry-after' and v=='60' for k,v in res[3].items()))
   print('B15 waiting for real fixed 60-second window',flush=True)
   while time.monotonic()-start<61:time.sleep(min(10,61-(time.monotonic()-start)))
   r.check('B15-recovery-without-restart',app.login('admin@example.invalid',password)[0]==200)
   b=setup_db(r,'continuationb');bootstrap(r,b,password,'second-product-bootstrap')
   other=prior.HttpProbe(r,b,profile='production',namespace='synthetic-other');other.start()
   status,source_cookie,_=app.login('admin@example.invalid',password);r.check('B14-source-control-valid',status==200)
   session_checks(r,app,source_cookie,True,'B14-product-a-valid')
   session_checks(r,other,source_cookie,False,'B14-product-b-cookie-a-rejected')
   renamed=source_cookie.replace('synthetic-auth.','__Secure-synthetic-other.')
   session_checks(r,other,renamed,False,'B14-product-b-renamed-cookie-rejected')
   r.check('B14-independent-database-empty-session',r.sql(b,'SELECT count(*) FROM app."Session";').stdout.strip()=='0')
   report['browser'].append(browser(r,other,'secure-login',password=password))
   r.check('B14-distinct-networks-volumes',a['network']!=b['network'] and a['volume']!=b['volume'])
   for db in [a,b]:r.record('retire-bootstrap-'+db['database'],r.sql(db,'ALTER ROLE bpbootstrap NOLOGIN; REVOKE ALL ON app."User",app."Account" FROM bpbootstrap; REVOKE USAGE ON SCHEMA app FROM bpbootstrap;'))
   report['status']='PASS'
  except Exception as error:
   report['status']='FAIL';report['error']=type(error).__name__+(': '+str(error) if isinstance(error,prior.base.InfrastructureError) else ': details withheld')
  finally:
   # Collect only in memory, before cleanup, then scan raw logs and the complete serialized receipt.
   for db in r.db:
    p=r.sql(db,'SELECT token FROM app."Session" UNION ALL SELECT password FROM app."Account" WHERE password IS NOT NULL;')
    if p.returncode==0:r.values.extend(v for v in p.stdout.splitlines() if v)
   report['rawLogScan']=[]
   for kind,name in r.resources:
    if kind=='container' and (name.endswith('-app') or name.endswith('-db')) and r.owned(kind,name):
     p=r.docker(['logs',name]);ok=p.returncode==0 and not any(v and v in p.stdout for v in r.values)
     report['rawLogScan'].append({'name':name,'passed':ok})
     if not ok:report['status']='FAIL'
   for relay in getattr(r,'relays',[]):relay.close_run()
   report['hostRelaysClosed']=all(relay.socket.fileno()==-1 for relay in getattr(r,'relays',[]))
   report['cleanup']=r.finish();report['steps']=r.steps
   report['cleanupPassed']=all(x['removedOrAbsent'] for x in report['cleanup']) and report['hostRelaysClosed']
   if not report['cleanupPassed']:report['status']='FAIL'
   report['sourceUnchanged']=all(digest(ROOT/p)==h for p,h in hashes.items())
   if not report['sourceUnchanged']:report['status']='FAIL'
   serial=json.dumps(report,ensure_ascii=False)
   matches=any(v and v in serial for v in r.values)
   report['receiptSecretScan']={'passed':not matches,'method':'Exact synthetic secrets/DB URLs/session tokens/password hashes in memory, against full serialized receipt before persistence; no secret values retained.'}
   if matches:raise RuntimeError('Receipt withheld: secret detected')
   dump(OUT/(r.id+'.json'),report)
   (OUT/(r.id+'.running.json')).unlink(missing_ok=True)
 report['temporaryDirectoryRemoved']=not Path(tmp).exists()
 dump(OUT/(r.id+'.json'),report)
 print(report['status'],r.id,flush=True)
 return 0 if report['status']=='PASS' else 1
if __name__=='__main__':sys.exit(main())
