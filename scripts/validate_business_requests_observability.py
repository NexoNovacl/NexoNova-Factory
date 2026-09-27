#!/usr/bin/env python3
"""Targeted supplemental evidence: actual ORM SQL, final browser headers, defaults/grants."""
from validate_business_requests_integration import *
from datetime import datetime,timezone
import signal

def main():
 auth.base.NODE=auth.IMAGE;auth.base.LABEL='nexonova.p45b.run'
 with tempfile.TemporaryDirectory(prefix='nexonova-p45b-observe-',dir='/var/tmp') as tmp:
  r=Run(tmp);r.id=r.id.replace('p43-','p45b-');r.work=Path('/var/tmp/nexonova-p45b-d02-work')
  sources=[*OVERLAY.rglob('*'),Path(__file__),ROOT/'scripts/check_business_requests_headers.mjs',ROOT/'scripts/business_requests_probe.py',ROOT/'scripts/validate_business_requests_integration.py']
  report={'phase':'P4.5-B','stage':'observability','runId':r.id,'status':'RUNNING','sourceHashes':{str(p.relative_to(ROOT)):sha(p) for p in sources if p.is_file()},'cases':{}}
  for p in sources:
   if p.is_file() and p.parent==ROOT/'scripts':shutil.copyfile(p,OUT/'validators'/(sha(p)+p.suffix))
  try:
   db=r.create_db('observe');password=setup(r,db);r.node('C01-observe-deploy',['node','node_modules/prisma/build/index.js','migrate','deploy','--config','prisma.requests.config.ts'],db['network'],{'MIGRATION_DATABASE_URL':r.url(db,'migrator')});r.record('runtime-grants',r.sql(db,(r.work/'validation/requests-runtime-grants.sql').read_text()))
   r.record('C40-enable-fixture-query-log',r.sql(db,"ALTER ROLE bpruntime SET log_statement='all'; ALTER ROLE bpruntime SET log_parameter_max_length=0; ALTER ROLE bpruntime SET log_parameter_max_length_on_error=0;"))
   app=RequestsProbe(r,db,namespace='synthetic-observe');app.start();m=Matrix(r,db,app,report)
   for who,email in [('a','member-a@example.invalid'),('admin','admin@example.invalid')]:
    status,cookie,_=app.login(email,password);m.check('login-'+who,status==200);m.cookies[who]=cookie;m.ids[who]=r.sql(db,"SELECT id FROM app.\"User\" WHERE email='"+email+"'").stdout.strip()
   start=datetime.now(timezone.utc);item=m.create(title='Headers navigation fixture');end=datetime.now(timezone.utc);created=datetime.fromisoformat(item['createdAt'].replace('Z','+00:00'));m.check('C05-server-times',start<=created<=end and item['updatedAt']==item['createdAt']);m.check('C05-uuid',uuid.UUID(item['id']).version==4 and item['id']==str(uuid.UUID(item['id'])))
   m.api('C40','a','?limit=7');item=m.patch(item,'edit',case='C40',title='Headers navigation fixture',description='Observed SQL')['item']
   raw=r.docker(['logs',db['container']]).stdout
   known=r.values+r.sql(db,'SELECT token FROM app."Session" UNION ALL SELECT password FROM app."Account" WHERE password IS NOT NULL').stdout.splitlines()
   m.check('C36-db-log-known-secret-scan',not any(value and len(value)>10 and value in raw for value in known))
   r.values.extend(known)
   # Persist only parameterized statement lines on the business table, never DETAIL bind values/auth SQL.
   lines=[line.split('execute ',1)[1] for line in raw.splitlines() if 'execute ' in line and '"InternalRequest"' in line and '$' in line and not 'DETAIL:' in line]
   report['businessSql']=lines
   m.check('C40-actual-list-sql',any('SELECT' in line and '"ownerId" = $' in line and '"archivedAt" IS NULL' in line and 'LIMIT $' in line and 'ORDER BY' in line for line in lines))
   m.check('C40-actual-cas-sql',any('UPDATE' in line and '"ownerId" = $' in line and '"archivedAt" IS NULL' in line and '"version" = $' in line and '"version" < $' in line for line in lines))
   r.record('C40-restore-fixture-query-log',r.sql(db,'ALTER ROLE bpruntime RESET log_statement; ALTER ROLE bpruntime RESET log_parameter_max_length; ALTER ROLE bpruntime RESET log_parameter_max_length_on_error;'));app.restart()
   columns=r.sql(db,"SELECT column_name,data_type,is_nullable,column_default FROM information_schema.columns WHERE table_schema='app' AND table_name='InternalRequest' ORDER BY ordinal_position").stdout.strip().splitlines()
   expected=['id|text|NO|','title|text|NO|','description|text|NO|','status|USER-DEFINED|NO|\'open\'::app."InternalRequestStatus"','ownerId|text|NO|','createdAt|timestamp without time zone|NO|','updatedAt|timestamp without time zone|NO|','archivedAt|timestamp without time zone|YES|','version|integer|NO|1'];m.check('C01-exact-column-types-defaults',columns==expected)
   rows=r.sql(db,"SELECT grantee,privilege_type,column_name FROM information_schema.column_privileges WHERE table_schema='app' AND table_name='InternalRequest' AND grantee IN ('bpruntime','bpbootstrap')").stdout.splitlines();fields=['id','title','description','status','ownerId','createdAt','updatedAt','archivedAt','version'];expectedgrants={'bpruntime|'+op+'|'+f for op in ['SELECT','INSERT'] for f in fields}|{'bpruntime|UPDATE|'+f for f in ['title','description','status','updatedAt','archivedAt','version']};m.check('C03-exact-effective-column-grants',set(rows)==expectedgrants)
   p=subprocess.Popen(['node',str(ROOT/'scripts/check_business_requests_headers.mjs')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True,env={**os.environ,'PLAYWRIGHT_BROWSERS_PATH':'/var/tmp/nexonova-p33-browsers'})
   try:output=p.communicate(json.dumps({'origin':app.origin,'cookies':m.cookies,'title':item['title']}),timeout=120)[0]
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.communicate();raise
   result=json.loads(output.strip().splitlines()[-1]);report['browser']=result;m.check('C28-browser-header-navigation',p.returncode==0 and result['status']=='PASS')
   # Internal Docker network + an attempted connection to a reserved documentation address.
   r.node('C36-egress-denied',['node','-e',"const net=require('node:net');const s=net.createConnection({host:'192.0.2.1',port:443});s.setTimeout(1000);s.on('connect',()=>{s.destroy();process.exitCode=1});s.on('error',()=>console.log('EGRESS_DENIED'));s.on('timeout',()=>{s.destroy();console.log('EGRESS_DENIED_TIMEOUT')})"],db['network'])
   report['status']='PASS'
  except Exception as e:report['status']='FAIL';report['error']=str(e) if isinstance(e,auth.base.InfrastructureError) else type(e).__name__
  finally:
   for relay in getattr(r,'relays',[]):relay.close_run()
   report['steps']=r.steps;report['cleanup']=r.finish();report['cleanupPassed']=all(x['removedOrAbsent'] for x in report['cleanup']);report['secretScanPassed']=not any(v and v in json.dumps(report) for v in r.values)
   if not report['secretScanPassed']:raise RuntimeError('Secret scan failed; receipt withheld')
   write(OUT/(r.id+'.json'),report);(OUT/(r.id+'.running.json')).unlink(missing_ok=True)
  print(report['status'],r.id);return report['status']=='PASS'
if __name__=='__main__':sys.exit(0 if main() else 1)
