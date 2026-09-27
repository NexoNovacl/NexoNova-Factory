"""Continuation checks invoked in the live integration fixture; no historical receipt writes."""
from validate_business_requests import *
from business_requests_probe import RequestsProbe
import time,concurrent.futures

def browser(m,mode,**data):
 p=subprocess.run(['node',str(ROOT/'scripts/check_business_requests.mjs')],input=json.dumps({'mode':mode,'origin':m.app.origin,'cookies':m.cookies,**data}),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180,env={**os.environ,'PLAYWRIGHT_BROWSERS_PATH':'/var/tmp/nexonova-p33-browsers'})
 # Browser errors never include submitted values in the persisted result.
 try:result=json.loads(p.stdout.strip().splitlines()[-1])
 except:result={'status':'FAIL','reason':'Browser output unavailable'}
 if result.get('failedCheck'):result['failedCheck']=m.r.clean_text(result['failedCheck'])
 m.report.setdefault('browser',[]).append(result);m.check('C34-browser-'+mode,p.returncode==0 and result['status']=='PASS')

def extra(m,password,a,b):
 r=m.r;db=m.db;app=m.app
 from validate_business_requests_gaps import gaps
 gaps(m,a,b)
 browser(m,'negative',id=a['id'],cookies={k:m.cookies[k] for k in ['anonymous','forged','expired','revoked']})
 browser(m,'flow')
 m.done('C09','C14','C27','C28','C34','C20')
 # Repeat relevant authentication guarantees against this composition, not historical aggregate PASS.
 app.restart()
 wrong='Wrong-'+secrets.token_hex(24);r.values.append(wrong)
 negatives=[app.request('/api/auth/sign-in/email','POST',{'email':email,'password':wrong}) for email in ['member-a@example.invalid','absent@example.invalid']]
 m.check('C35-generic-login',negatives[0][0]==negatives[1][0]==401 and negatives[0][1]==negatives[1][1])
 m.check('C35-signup-closed',app.request('/api/auth/sign-up/email','POST',{})[0]==404)
 m.check('C35-member-probe',app.request('/api/admin-check',cookie=m.cookies['a'])[0]==403)
 m.check('C35-admin-probe',app.request('/api/admin-check',cookie=m.cookies['admin'])[0]==200)
 status,cookie,cookies=app.login('member-a@example.invalid',password,True);m.check('C35-session-cookie',status==200 and cookies and all('httponly' in c.lower() and 'samesite=lax' in c.lower() and 'max-age' not in c.lower() and 'expires=' not in c.lower() and 'secure' not in c.lower() for c in cookies))
 selector='SELECT id FROM app."Session" WHERE "userId"=\''+m.ids['a']+'\' ORDER BY "createdAt" DESC LIMIT 1'
 sid=r.sql(db,selector).stdout.strip()
 duration=r.sql(db,'SELECT EXTRACT(EPOCH FROM ("expiresAt"-"createdAt")) <=28800 FROM app."Session" WHERE id=\''+sid+"'").stdout.strip();m.check('C35-max-eight-hours',duration=='t')
 r.record('C35-inside-boundary',r.sql(db,'UPDATE app."Session" SET "createdAt"=NOW()-INTERVAL \'7 hours 59 minutes\',"expiresAt"=NOW()+INTERVAL \'1 minute\' WHERE id=\''+sid+"'"))
 sessionbefore=r.sql(db,'SELECT row_to_json(t) FROM app."Session" t WHERE id=\''+sid+"'").stdout
 m.check('C35-before-eight-hours',app.request('/api/requests',cookie=cookie)[0]==200)
 m.check('C35-no-refresh',sessionbefore==r.sql(db,'SELECT row_to_json(t) FROM app."Session" t WHERE id=\''+sid+"'").stdout)
 r.record('C35-absolute-boundary',r.sql(db,'UPDATE app."Session" SET "createdAt"=NOW()-INTERVAL \'8 hours\',"expiresAt"=NOW()+INTERVAL \'1 minute\' WHERE id=\''+sid+"'"))
 m.check('C35-absolute-expired',app.request('/api/requests',cookie=cookie)[0]==401)
 status,cookie,_=app.login('member-a@example.invalid',password);m.check('C35-new-login',status==200)
 m.check('C35-logout',app.request('/api/auth/sign-out','POST',{},cookie)[0]==200);m.check('C35-replay-denied',app.request('/api/requests',cookie=cookie)[0]==401)
 # App + database restarts preserve visible and archived business rows and existing active sessions.
 before=m.snap();app.restart();m.check('C29-app-data',before==m.snap());m.api('C29','a','/'+a['id']);m.api('C29','a','/'+b['id'],status=404)
 r.record('C29-db-restart',r.docker(['restart',db['container']]));time.sleep(2);app.ready();m.check('C29-db-data',before==m.snap());m.api('C29','a','/'+a['id']);m.api('C29','admin','/'+b['id'],status=404);m.done('C29')
 # Revoke privileges one operation at a time, restore exact approved grants.
 before=m.snap()
 for privilege,sql,method,path,body in [
  ('SELECT','REVOKE SELECT ON app."InternalRequest" FROM bpruntime','GET','',None),
  ('INSERT','REVOKE INSERT (id,title,description,status,"ownerId","createdAt","updatedAt","archivedAt",version) ON app."InternalRequest" FROM bpruntime','POST','',{'title':'No','description':''}),
  ('UPDATE','REVOKE UPDATE (title,description,status,"updatedAt","archivedAt",version) ON app."InternalRequest" FROM bpruntime','PATCH','/'+a['id'],{'action':'edit','expectedVersion':a['version'],'title':'No','description':''})]:
  r.record('C30-revoke-'+privilege,r.sql(db,sql));m.api('C30','a',path,method,body,503);r.record('C30-restore-'+privilege,r.sql(db,(r.work/'validation/requests-runtime-grants.sql').read_text()));m.check('C30-no-effects-'+privilege,before==m.snap())
 r.record('C30-db-stop',r.docker(['stop',db['container']]))
 for path,method,body in [('', 'GET',None),('', 'POST',{'title':'No','description':''}),('/'+a['id'],'PATCH',{'action':'close','expectedVersion':a['version']})]:m.api('C30','a',path,method,body,503)
 r.record('C30-db-start',r.docker(['start',db['container']]));time.sleep(2);app.ready();m.check('C30-recovered',before==m.snap());m.api('C30','a','/'+a['id']);m.done('C30')
 # Second isolated product, production TLS profile; no shared DB/secret/cookie prefix.
 from validate_business_requests_integration import setup
 other=r.create_db('secondary');secondpass=setup(r,other)
 r.node('C31-secondary-migration',['node','node_modules/prisma/build/index.js','migrate','deploy','--config','prisma.requests.config.ts'],other['network'],{'MIGRATION_DATABASE_URL':r.url(other,'migrator')})
 r.record('C31-secondary-grants',r.sql(other,(r.work/'validation/requests-runtime-grants.sql').read_text()))
 secure=RequestsProbe(r,other,profile='production',namespace='synthetic-requests-two');secure.start()
 status,cookie,cookies=secure.login('member-a@example.invalid',secondpass);m.check('C31-valid-second',status==200)
 m.check('C35-secure-cookie',cookies and all('secure' in c.lower() and 'httponly' in c.lower() and 'samesite=lax' in c.lower() for c in cookies))
 m.check('C31-cross-cookie',secure.request('/api/requests',cookie=m.cookies['a'])[0]==401 and app.request('/api/requests',cookie=cookie)[0]==401)
 m.check('C31-cross-id',secure.request('/api/requests/'+a['id'],cookie=cookie)[0]==404)
 page=m.api('C31','a','?limit=1');res=secure.request('/api/requests?cursor='+page['nextCursor'],cookie=cookie);m.check('C31-cross-cursor',res[0]==200 and json.loads(res[1])=={'items':[],'nextCursor':None})
 res=secure.request('/api/requests','POST',{'title':'Second product','description':''},cookie);m.check('C31-second-create',res[0]==201)
 id2=json.loads(res[1])['item']['id'];m.check('C31-no-contamination',r.sql(db,'SELECT count(*) FROM app."InternalRequest" WHERE id=\''+id2+"'").stdout.strip()=='0' and r.sql(other,'SELECT count(*) FROM app."InternalRequest"').stdout.strip()=='1')
 m.report['networks']=[]
 for d in [db,other]:
  info=json.loads(r.docker(['network','inspect',d['network']]).stdout)[0];m.report['networks'].append({'name':d['network'],'internal':info['Internal']});m.check('C31-internal-network',info['Internal'])
 # Existing browser validator used read-only; fresh real secure login, no historical receipt write.
 p=subprocess.run(['node',str(ROOT/'scripts/check_business_auth_continuation.mjs')],input=json.dumps({'mode':'secure-login','origin':secure.origin,'secure':True,'password':secondpass}),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120,env={**os.environ,'PLAYWRIGHT_BROWSERS_PATH':'/var/tmp/nexonova-p33-browsers'})
 result=json.loads(p.stdout.strip().splitlines()[-1]);m.report['secureBrowser']=result;m.check('C35-secure-browser',p.returncode==0 and result['status']=='PASS');m.done('C31','C35')
 # Real EXPLAIN and connection measurements (pilot measurements, not SLA).
 plans=r.sql(db,'EXPLAIN (FORMAT JSON) SELECT id FROM app."InternalRequest" WHERE "ownerId"=\''+m.ids['a']+'\' AND "archivedAt" IS NULL ORDER BY "createdAt",id LIMIT 21; EXPLAIN (FORMAT JSON) UPDATE app."InternalRequest" SET version=version+1 WHERE id=\''+a['id']+'\' AND "ownerId"=\''+m.ids['a']+'\' AND "archivedAt" IS NULL AND version='+str(a['version'])+' AND version<2147483647;').stdout
 m.report['plans']=plans;m.check('C40-plan-limit-scope','Limit' in plans and 'ownerId' in plans and 'archivedAt' in plans and 'version' in plans)
 counts=[]
 for cycle in range(3):
  with concurrent.futures.ThreadPoolExecutor(6) as pool:statuses=list(pool.map(lambda _:app.request('/api/requests?limit=20',cookie=m.cookies['a'])[0],range(30)))
  m.check('C40-bounded-reads-'+str(cycle),all(s==200 for s in statuses));count=int(r.sql(db,"SELECT count(*) FROM pg_stat_activity WHERE usename='bpruntime'").stdout.strip());counts.append(count)
 m.report['runtimeConnectionCounts']=counts;m.check('C40-pools-bounded',max(counts)<=15 and counts[-1]<=counts[0]+2)
 m.report['resourceStats']=r.docker(['stats','--no-stream','--format','{{.Name}} {{.MemUsage}} {{.PIDs}}',app.name,db['container']]).stdout
 logs=r.docker(['logs',app.name]).stdout+r.docker(['logs',secure.name]).stdout
 secrets_to_scan=[v for v in r.values if len(v)>10]
 # Add tokens and password hashes from DB only in memory; never record raw query output.
 for d in [db,other]:
  secrets_to_scan+=r.sql(d,'SELECT token FROM app."Session" UNION ALL SELECT password FROM app."Account" WHERE password IS NOT NULL').stdout.splitlines()
 content=[logs,*[app.request(path,cookie=m.cookies['a'])[1] for path in ['/requests','/requests/'+a['id']]]]
 for p in (r.work/'.next/static').rglob('*.js'):content.append(p.read_text())
 m.check('C36-known-secret-scan',not any(secret and secret in text for secret in secrets_to_scan for text in content))
 m.check('C33-no-client-db',not any('PrismaClient' in text or 'BOOTSTRAP_DATABASE_URL' in text or 'DATABASE_URL' in text for text in content[3:]))
 m.report['scan']={'scope':['app logs','SSR','client JS','final report serialized separately'],'knownValues':len(secrets_to_scan),'matches':0,'limitation':'Exact known synthetic values; not a formal exhaustive secret detector.'}
 r.values.extend(secrets_to_scan);m.done('C33','C36','C40')
