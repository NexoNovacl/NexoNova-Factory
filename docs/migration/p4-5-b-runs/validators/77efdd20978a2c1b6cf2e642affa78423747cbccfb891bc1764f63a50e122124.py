#!/usr/bin/env python3
"""Real PostgreSQL/HTTP probes of the P4.5-B isolated composition."""
from validate_business_requests import *
import time,uuid,threading,concurrent.futures,base64,urllib.request,urllib.error
class Matrix:
 def __init__(self,r,db,app,report):self.r=r;self.db=db;self.app=app;self.report=report;self.cookies={};self.ids={}
 def check(self,name,condition):self.r.check(name,condition)
 def snap(self):return self.r.sql(self.db,'SELECT row_to_json(t) FROM app."InternalRequest" t ORDER BY id; SELECT id,role FROM app."User" ORDER BY id;').stdout
 def row(self,id):return json.loads(self.r.sql(self.db,'SELECT row_to_json(t) FROM app."InternalRequest" t WHERE id=\''+id+"'").stdout)
 def api(self,case,actor,path='',method='GET',body=None,status=200,headers=None):
  started=time.monotonic();result=self.app.request('/api/requests'+path,method,body,self.cookies.get(actor,''),headers);elapsed=round((time.monotonic()-started)*1000,2)
  try:data=json.loads(result[1]) if result[1] else None
  except ValueError:data=None
  self.report.setdefault('http',[]).append({'case':case,'actor':actor,'method':method,'pathKind':'collection' if not path or path.startswith('?') else 'detail','status':result[0],'expected':status,'elapsedMs':elapsed,'error':data.get('error') if isinstance(data,dict) else None})
  self.check(case+'-'+method+'-'+str(len(self.report['http'])),result[0]==status)
  self.check(case+'-cache-'+str(len(self.report['http'])),{k.lower():v for k,v in result[3].items()}.get('cache-control')=='no-store' and 'cookie' in {k.lower():v for k,v in result[3].items()}.get('vary','').lower())
  return data
 def create(self,actor='a',title='Synthetic request',case='C05'):
  item=self.api(case,actor,method='POST',body={'title':title,'description':'Synthetic description'},status=201)['item'];self.check(case+'-persisted',self.row(item['id'])['title']==title);return item
 def patch(self,item,action,actor='a',status=200,case='C10',version=None,**fields):return self.api(case,actor,'/'+item['id'],'PATCH',{'action':action,'expectedVersion':item['version'] if version is None else version,**fields},status)
 def done(self,*cases):
  for c in cases:self.report['cases'][c]={'status':'PASS','steps':[s['name'] for s in self.r.steps if s['name'].startswith(c+'-')]}
  write(OUT/(self.r.id+'.progress.json'),self.report)
 def race(self,case,item,commands,actors):
  barrier=threading.Barrier(2)
  def worker(i):
   barrier.wait(timeout=10);start=time.monotonic_ns();res=self.app.request('/api/requests/'+item['id'],'PATCH',{'expectedVersion':item['version'],**commands[i]},self.cookies[actors[i]]);return {'worker':i,'thread':threading.get_native_id(),'startNs':start,'status':res[0]}
  with concurrent.futures.ThreadPoolExecutor(2) as pool:out=list(pool.map(worker,range(2)))
  self.report.setdefault('races',[]).append({'case':case,'workers':out,'commands':[c['action'] for c in commands]})
  self.check(case+'-one-commit-'+str(len(self.report['races'])),sum(x['status'] in [200,204] for x in out)==1 and all(x['status'] in [200,204,404,409] for x in out))
  row=self.row(item['id']);self.check(case+'-single-increment-'+str(len(self.report['races'])),row['version']==item['version']+1)
  return out,row

def setup(r,db):
 r.node('auth-only',['node','node_modules/prisma/build/index.js','migrate','deploy'],db['network'],{'MIGRATION_DATABASE_URL':r.url(db,'migrator')})
 r.record('auth-grants',r.sql(db,(r.work/'validation/runtime-grants.sql').read_text()))
 db['passwords']['bootstrap']=secrets.token_hex(24);r.values.append(db['passwords']['bootstrap'])
 r.record('bootstrap-role',r.sql(db,"CREATE ROLE bpbootstrap LOGIN PASSWORD '"+db['passwords']['bootstrap']+"'; GRANT CONNECT ON DATABASE "+db['database']+" TO bpbootstrap;"+(r.work/'validation/bootstrap-grants.sql').read_text()))
 password='Fixture-'+secrets.token_hex(24);r.values.append(password);env={'BOOTSTRAP_DATABASE_URL':r.url(db,'bootstrap')}
 r.node_input('bootstrap-admin',['npm','run','bootstrap-admin'],db['network'],env,json.dumps({'database':db['database'],'email':'admin@example.invalid','name':'Synthetic Admin','password':password}))
 for who in ['a','b']:r.node_input('fixture-'+who,['node','build-checks/validation/requests-users.js'],db['network'],env,json.dumps({'database':db['database'],'email':'member-'+who+'@example.invalid','password':password}))
 return password

def run_matrix(m,password):
 r=m.r;db=m.db;app=m.app
 for who,email in [('a','member-a@example.invalid'),('b','member-b@example.invalid'),('admin','admin@example.invalid')]:
  status,cookie,_=app.login(email,password);m.check('C02-existing-session-'+who,status==200 and bool(cookie));m.cookies[who]=cookie
  m.ids[who]=r.sql(db,"SELECT id FROM app.\"User\" WHERE email='"+email+"'").stdout.strip()
 authsnapshot='SELECT row_to_json(t) FROM app."User" t ORDER BY id; SELECT row_to_json(t) FROM app."Session" t ORDER BY id; SELECT row_to_json(t) FROM app."Account" t ORDER BY id;'
 before=r.sql(db,authsnapshot).stdout
 migration='SELECT migration_name,checksum,finished_at FROM app._prisma_migrations ORDER BY migration_name';old=r.sql(db,migration).stdout
 env={'MIGRATION_DATABASE_URL':r.url(db,'migrator')}
 r.node('C02-upgrade-session',['node','node_modules/prisma/build/index.js','migrate','deploy','--config','prisma.requests.config.ts'],db['network'],env)
 m.check('C02-auth-data-byte-identical',before==r.sql(db,authsnapshot).stdout)
 m.check('C02-auth-history-preserved',r.sql(db,migration).stdout.startswith(old))
 history=r.sql(db,migration).stdout
 r.node('C02-reapply-session',['node','node_modules/prisma/build/index.js','migrate','deploy','--config','prisma.requests.config.ts'],db['network'],env)
 m.check('C02-reapply-stable',history==r.sql(db,migration).stdout and before==r.sql(db,authsnapshot).stdout)
 r.record('module-grants',r.sql(db,(r.work/'validation/requests-runtime-grants.sql').read_text()))
 r.record('bootstrap-retired',r.sql(db,'ALTER ROLE bpbootstrap NOLOGIN; REVOKE ALL ON app."User",app."Account" FROM bpbootstrap; REVOKE USAGE ON SCHEMA app FROM bpbootstrap;'))
 m.done('C02')
 # Independent catalog inventory, constraints and effective column grants.
 catalog=r.sql(db,"SELECT column_name,data_type,is_nullable,column_default FROM information_schema.columns WHERE table_schema='app' AND table_name='InternalRequest' ORDER BY ordinal_position; SELECT enumlabel FROM pg_enum WHERE enumtypid='app.\"InternalRequestStatus\"'::regtype ORDER BY enumsortorder; SELECT conname,convalidated,condeferrable FROM pg_constraint WHERE conrelid='app.\"InternalRequest\"'::regclass ORDER BY conname;").stdout
 m.report['catalog']=catalog;m.check('C01-catalog',len(catalog.splitlines())==16 and 'archivedAt|timestamp without time zone|YES|' in catalog and 'open\nclosed\n' in catalog and 'InternalRequest_ownerId_fkey|t|f' in catalog)
 m.report['grants']=r.sql(db,"SELECT grantee,privilege_type,column_name FROM information_schema.column_privileges WHERE table_schema='app' AND table_name='InternalRequest' AND grantee IN ('bpruntime','bpbootstrap') ORDER BY grantee,privilege_type,column_name").stdout
 a=m.create();b=m.create('b');admin=m.create('admin')
 for who,item in [('a',a),('b',b),('admin',admin)]:m.check('C05-defaults-'+who,item['ownerId']==m.ids[who] and item['status']=='open' and item['version']==1 and item['archivedAt'] is None and set(item)=={'id','title','description','status','ownerId','createdAt','updatedAt','archivedAt','version'})
 if '--resume-pages' in sys.argv:
  m.patch(b,'archive','b',204,'resume');
  for path in ['/requests','/requests/'+a['id']]:
   res=app.request(path,cookie=m.cookies['a']);rawresponse=urllib.request.build_opener(urllib.request.ProxyHandler({})).open(urllib.request.Request(app.origin+path,headers={'Cookie':m.cookies['a']}));m.report.setdefault('rawVary',[]).append(rawresponse.headers.get_all('Vary'));rawresponse.close();hdr={k.lower():v for k,v in res[3].items()};m.report.setdefault('pageHeaders',[]).append({'status':res[0],'cache':hdr.get('cache-control'),'vary':hdr.get('vary')});m.check('C28-page-private',res[0]==200 and 'no-store' in hdr.get('cache-control','') and 'cookie' in hdr.get('vary','').lower())
  return session_tail(m,a,b,password)
 before=m.snap();rolequery(r,db,'runtime','C06-orphan',"INSERT INTO app.\"InternalRequest\" (id,title,description,\"ownerId\",\"createdAt\",\"updatedAt\") VALUES ('orphan','Orphan','','absent',NOW(),NOW())",'23503');m.check('C06-no-effects',before==m.snap());m.done('C05','C06')
 before=m.snap()
 for actor in ['a','admin']:
  for key in ['ownerId','userId','role','status','archivedAt','id','createdAt','version','identity','constructor','__proto__']:
   m.api('C07',actor,method='POST',body={'title':'Spoof','description':'',key:{'nested':'spoof'}},status=400)
   m.api('C07',actor,'/'+a['id'],'PATCH',{'action':'edit','expectedVersion':1,'title':'Spoof','description':'',key:'spoof'},400)
 m.check('C07-no-effects',before==m.snap());m.done('C07')
 for who,item in [('a',a),('b',b)]:m.check('C08-own-list-'+who,[x['id'] for x in m.api('C08',who)['items']]==[item['id']])
 m.check('C09-admin-list',set(x['id'] for x in m.api('C09','admin')['items'])=={a['id'],b['id'],admin['id']})
 for item in [a,b]:m.check('C09-admin-detail',m.api('C09','admin','/'+item['id'])['item']['ownerId']==item['ownerId'])
 m.done('C08')
 original=a.copy();a=m.patch(a,'edit',title='Edited',description='New')['item'];a=m.patch(a,'close')['item'];a=m.patch(a,'edit',title='Edited closed',description='Closed edit')['item'];m.check('C10-edit-closed',a['version']==4 and a['status']=='closed' and all(a[k]==original[k] for k in ['id','ownerId','createdAt']))
 before=m.snap();m.patch(a,'close',status=409,case='C11');m.check('C11-no-effects',before==m.snap());a=m.patch(a,'reopen',case='C11')['item'];before=m.snap();m.patch(a,'reopen',status=409,case='C11');m.check('C11-no-effects-open',before==m.snap())
 m.done('C10','C11')
 for actor,state in [('a','open'),('admin','closed')]:
  item=m.create(actor,case='C12')
  if state=='closed':item=m.patch(item,'close',actor,case='C12')['item']
  m.patch(item,'archive',actor,204,'C12');row=m.row(item['id']);m.check('C12-retained-'+state,row['status']==state and row['archivedAt']==row['updatedAt'] and row['archivedAt'] is not None and row['version']==item['version']+1)
  before=m.snap()
  for who in ['a','b','admin']:
   m.api('C14',who,'/'+item['id'],status=404)
   for action in ['edit','close','reopen','archive']:m.patch(item,action,who,404,'C14',**({'title':'No','description':''} if action=='edit' else {}))
   m.check('C14-absent-list',item['id'] not in [x['id'] for x in m.api('C14',who)['items']])
  m.check('C14-unchanged',before==m.snap())
 m.done('C12')
 before=m.snap()
 for action in ['edit','close','reopen','archive']:
  extra={'title':'No','description':''} if action=='edit' else {}
  for version in [None,0,-1,1.2,'1',2147483648]:
   data={'action':action,**extra}
   if version is not None:data['expectedVersion']=version
   m.api('C13','a','/'+a['id'],'PATCH',data,400)
  m.patch(a,action,status=409,case='C13',version=1,**extra)
 m.check('C13-invalid-unchanged',before==m.snap())
 maxitem=m.create(case='C13');r.record('C13-max-fixture',r.sql(db,'UPDATE app."InternalRequest" SET version=2147483647 WHERE id=\''+maxitem['id']+"'"));maxitem['version']=2147483647;before=m.snap()
 for action in ['edit','close','reopen','archive']:m.patch(maxitem,action,status=409,case='C13',**({'title':'No','description':''} if action=='edit' else {}))
 m.check('C13-max-unchanged',before==m.snap());m.done('C13')
 m.check('C15-detail',m.api('C15','a','/'+a['id'])['item']==a);a=m.patch(a,'edit',case='C15',title='Own direct',description='')['item'];m.done('C15')
 absent=str(uuid.uuid4());before=m.snap()
 foreign=m.api('C17','a','/'+b['id'],status=404);m.check('C17-uniform',foreign==m.api('C17','a','/'+absent,status=404)=={'error':'RESOURCE_NOT_FOUND'})
 for version in [1,2]:m.api('C18','a','/'+b['id'],'PATCH',{'action':'edit','expectedVersion':version,'title':'Attack','description':''},404,{'X-Role':'admin','X-Owner-Id':m.ids['b']})
 for action in ['close','reopen','archive']:
  for target in [b['id'],absent]:
   for version in [1,2]:m.api('C19','a','/'+target,'PATCH',{'action':action,'expectedVersion':version},404)
 m.check('C18-C19-no-effects',before==m.snap());m.done('C17','C18','C19')
 for action in ['edit','close','reopen','archive']:
  result=m.patch(b,action,'admin',204 if action=='archive' else 200,'C16',**({'title':'Admin edit','description':'Allowed'} if action=='edit' else {}))
  if result:b=result['item']
  m.check('C16-owner-preserved',m.row(b['id'])['ownerId']==m.ids['b'])
 m.done('C16')
 before=m.snap()
 for id in [absent,b['id'],'bad','ABC','%27OR%201=1','%2F','%00',a['id'].upper()]:
  for action in [None,'edit','close','reopen','archive']:
   data=None if action is None else {'action':action,'expectedVersion':1,**({'title':'No','description':''} if action=='edit' else {})}
   result=m.api('C22','a','/'+id,'GET' if action is None else 'PATCH',data,404);m.check('C22-body-uniform',result=={'error':'RESOURCE_NOT_FOUND'})
 m.check('C22-no-effects',before==m.snap());m.done('C22')
 invalid=r.sql(db,"\\set VERBOSITY verbose\nUPDATE app.\"User\" SET role='unknown' WHERE id='"+m.ids['a']+"'");m.check('C21-db-enum',invalid.returncode!=0 and '22P02' in invalid.stdout);m.done('C21')
 for i in range(6):
  item=m.create(case='C23');out,row=m.race('C23',item,[{'action':'edit','title':'Winner X','description':'X'},{'action':'edit','title':'Winner Y','description':'Y'}],['a','a' if i<3 else 'admin']);m.check('C23-status-'+str(i),sorted(x['status'] for x in out)==[200,409]);m.check('C23-no-mixed-'+str(i),(row['title'],row['description']) in [('Winner X','X'),('Winner Y','Y')])
 m.done('C23')
 for first,second in [('edit','close'),('close','archive'),('reopen','archive'),('edit','edit')]:
  item=m.create(case='C24')
  if first=='reopen':item=m.patch(item,'close',case='C24')['item']
  commands=[{'action':x,**({'title':'Race','description':str(i)} if x=='edit' else {})} for i,x in enumerate([first,second])]
  out,row=m.race('C24',item,commands,['a','b' if second=='edit' else 'admin'])
  if second=='edit':m.check('C24-nonowner',out[1]['status']==404 and row['description']=='0')
  if row['archivedAt'] is not None:m.api('C24','admin','/'+item['id'],status=404)
 m.done('C24')
 # >100 tied timestamps, both owners. UUIDs generated only by technical fixture.
 for who in ['a','b']:
  values=','.join("('"+str(uuid.uuid4())+"','Page fixture','','open','"+m.ids[who]+"','2025-01-01','2025-01-01',1)" for _ in range(107))
  r.record('C25-dataset-'+who,r.sql(db,'INSERT INTO app."InternalRequest" (id,title,description,status,"ownerId","createdAt","updatedAt",version) VALUES '+values))
 for who in ['a','admin']:
  where='"archivedAt" IS NULL'+(' AND "ownerId"=\''+m.ids[who]+"'" if who=='a' else '')
  expected=r.sql(db,'SELECT id FROM app."InternalRequest" WHERE '+where+' ORDER BY "createdAt",id').stdout.splitlines()
  for limit in [None,1,100]:
   path='?limit='+str(limit) if limit else '';seen=[]
   while True:
    data=m.api('C25',who,path);seen.extend(x['id'] for x in data['items']);m.check('C25-bounded',len(data['items'])<=(limit or 20))
    if data['nextCursor'] is None:break
    path='?limit='+str(limit or 20)+'&cursor='+data['nextCursor']
   m.check('C25-complete-'+who+'-'+str(limit),seen==expected and len(seen)==len(set(seen)))
 m.done('C25')
 for query in ['limit=0','limit=101','limit=01','limit=1.1','limit=-1','limit=1&limit=2','ownerId=x','cursor=','cursor=%%%','cursor='+('a'*257),'page=1']:
  m.api('C26','a','?'+query,status=400)
 cursor=base64.urlsafe_b64encode(json.dumps({'createdAt':'2024-01-01T00:00:00.000Z','id':b['id']}).encode()).decode().rstrip('=')
 m.check('C26-forged-scope',all(x['ownerId']==m.ids['a'] for x in m.api('C26','a','?cursor='+cursor)['items']))
 data=m.api('C26','a','?limit=1');target=m.api('C26','a','?cursor='+data['nextCursor'])['items'][0];m.patch(target,'archive',case='C26',status=204);m.check('C26-live-page',target['id'] not in [x['id'] for x in m.api('C26','a','?cursor='+data['nextCursor'])['items']]);m.done('C26')
 for title,description,expected in [('x','',201),('🔐'*120,'x'*2000,201),('🔐'*121,'',400),('x','x'*2001,400),(' ','',400),(None,'',400),('\ud800','',400),('x\x00','',400),('x','x'*17000,413),("<script>window.p45xss=1</script>' OR 1=1 --",'',201)]:m.api('C27','a',method='POST',body={'title':title,'description':description},status=expected)
 m.api('C27','a',method='POST',body={'title':'x','description':''},status=415,headers={'Content-Type':'text/plain'})
 before=m.snap()
 for origin in [None,'null','https://evil.invalid']:
  for path,method,body in [('', 'POST',{'title':'No','description':''}),('/'+a['id'],'PATCH',{'action':'close','expectedVersion':a['version']})]:m.api('C28','a',path,method,body,403,{'Origin':origin,'X-Forwarded-Host':'evil.invalid','X-Forwarded-Proto':'https'})
 m.api('C28','a',headers={'Sec-Fetch-Site':'cross-site'},status=403)
 for path in ['', '/'+a['id']]:
  for method in ['PUT','DELETE']:m.api('C28','a',path,method,{},405)
 m.api('C28','a','/'+a['id']);m.check('C28-no-effects',before==m.snap())
 for path in ['/requests','/requests/'+a['id']]:
  res=app.request(path,cookie=m.cookies['a']);m.check('C28-page-private',res[0]==200 and 'no-store' in {k.lower():v for k,v in res[3].items()}.get('cache-control','') and 'cookie' in {k.lower():v for k,v in res[3].items()}.get('vary','').lower())
 m.done('C28')
 return session_tail(m,a,b,password)

def session_tail(m,a,b,password):
 r=m.r;db=m.db;app=m.app
 # Sessions: no cookie, forged, expired and revoked; preserve live sessions separately.
 for kind in ['anonymous','forged','expired','revoked']:
  if kind=='anonymous':cookie=''
  elif kind=='forged':cookie='synthetic-requests.session_token=forged'
  else:
   app.restart();status,cookie,_=app.login('member-a@example.invalid',password);m.check('C20-session-'+kind,status==200)
   selector='SELECT id FROM app."Session" WHERE "userId"=\''+m.ids['a']+'\' ORDER BY "createdAt" DESC LIMIT 1'
   r.record('C20-'+kind,r.sql(db,('UPDATE app."Session" SET "expiresAt"=NOW()-INTERVAL \'1 second\' WHERE id=(' if kind=='expired' else 'DELETE FROM app."Session" WHERE id=(')+selector+')'))
  m.cookies[kind]=cookie;before=m.snap()
  for path,method,body in [('', 'GET',None),('', 'POST',{'title':'No','description':''}),('/'+a['id'],'GET',None),*[( '/'+a['id'],'PATCH',{'action':x,'expectedVersion':a['version'],**({'title':'No','description':''} if x=='edit' else {})}) for x in ['edit','close','reopen','archive']]]:m.api('C20',kind,path,method,body,401)
  for path in ['/requests','/requests/'+a['id']]:res=app.request(path,cookie=cookie);m.check('C20-page-'+kind,'login' in res[1].lower() or 'iniciar' in res[1].lower())
  m.check('C20-no-effects-'+kind,before==m.snap())
 m.done('C20')
 # Keep fixtures for follow-up browser, auth, restart and resource probes in this run.
 return a,b

def main():
 auth.base.NODE=auth.IMAGE;auth.base.LABEL='nexonova.p45b.run'
 work=Path(json.loads((OUT/'p45b-ba2c6a6f1698418a.json').read_text())['preparedWorkspace'])
 with tempfile.TemporaryDirectory(prefix='nexonova-p45b-integration-',dir='/var/tmp') as tmp:
  r=Run(tmp);r.id=r.id.replace('p43-','p45b-');r.work=work
  report={'phase':'P4.5-B','stage':'integration','runId':r.id,'status':'RUNNING','cases':{f'C{i:02}':{'status':'NOT_EXECUTED'} for i in range(1,41)},'sourceHashes':{str(p.relative_to(ROOT)):sha(p) for p in [*OVERLAY.rglob('*'),Path(__file__),ROOT/'scripts/validate_business_requests.py',ROOT/'scripts/validate_business_requests_extra.py',ROOT/'scripts/check_business_requests.mjs',ROOT/'scripts/validate_business_auth.py',ROOT/'factory/business_infrastructure.py'] if p.is_file()}}
  shutil.copyfile(__file__,OUT/'validators'/(r.id+'.py'))
  try:
   for p in OVERLAY.rglob('*'):
    if p.is_file():assert sha(p)==sha(work/p.relative_to(OVERLAY)),'Workspace source mismatch'
   db=r.create_db('primary');password=setup(r,db);app=auth.HttpProbe(r,db,namespace='synthetic-requests');app.start();m=Matrix(r,db,app,report)
   a,b=run_matrix(m,password)
   from validate_business_requests_extra import extra
   extra(m,password,a,b)
   report['status']='PASS'
  except Exception as e:report['status']='FAIL';report['error']=str(e) if isinstance(e,(auth.base.InfrastructureError,AssertionError)) else type(e).__name__
  finally:
   for relay in getattr(r,'relays',[]):relay.close_run()
   report['steps']=r.steps;report['cleanup']=r.finish();report['cleanupPassed']=all(x['removedOrAbsent'] for x in report['cleanup'])
   if not report['cleanupPassed']:report['status']='FAIL'
   report['secretScanPassed']=not any(v and v in json.dumps(report) for v in r.values)
   if not report['secretScanPassed']:raise RuntimeError('Secret scan failed; receipt withheld')
   write(OUT/(r.id+'.json'),report);(OUT/(r.id+'.running.json')).unlink(missing_ok=True)
  print(report['status'],r.id,flush=True);return report['status']=='PASS'
if __name__=='__main__':sys.exit(0 if main() else 1)
