#!/usr/bin/env python3
"""Isolated P4.5-B validation composition, never a Factory product generator."""
from pathlib import Path
import sys,json,hashlib,shutil,tempfile,subprocess,secrets,os
sys.path.insert(0,str(Path(__file__).resolve().parent))
import validate_business_auth as auth
ROOT=auth.ROOT; OVERLAY=ROOT/'modules/internal-requests/0.1.0/files'; OUT=ROOT/'docs/migration/p4-5-b-runs'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):
 p.parent.mkdir(exist_ok=True,parents=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2)+'\n');tmp.replace(p)
def compose(target):
 shutil.copytree(ROOT/'templates/business-platform-auth',target)
 for source in OVERLAY.rglob('*'):
  if source.is_file():
   dest=target/source.relative_to(OVERLAY)
   if dest.exists():raise ValueError('Overlay cannot replace core files')
   dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
 schema=(target/'prisma/auth/schema.prisma').read_text()
 output=target/'prisma/business';output.mkdir()
 (output/'schema.prisma').write_text(schema.replace('../../src/generated/auth','../../src/generated/requests')+'\n'+(target/'prisma/modules/internal-requests.prisma').read_text())
 shutil.copytree(target/'prisma/auth/migrations',output/'migrations')
 shutil.copytree(target/'prisma/requests-migrations',output/'migrations',dirs_exist_ok=True)
 return sha(output/'schema.prisma')
class Run(auth.AuthRun):
 def _checkpoint(self):write(OUT/(self.id+'.running.json'),{'runId':self.id,'status':'RUNNING','steps':self.steps,'resources':self.resources})
def sqlcheck(r,db,name,sql,predicate):
 p=r.sql(db,sql);r.check(name,p.returncode==0 and predicate(p.stdout.strip()));return p.stdout.strip()
def rolequery(r,db,role,name,sql,code=None):
 js="const {Client}=require('pg');(async()=>{const c=new Client({connectionString:process.env.DATABASE_URL});await c.connect();try{await c.query("+json.dumps(sql)+");console.log('OK');"+("process.exitCode=1;" if code else "")+"}catch(e){"+("if(e.code!=="+json.dumps(code)+")process.exitCode=1;else console.log('EXPECTED_SQLSTATE_'+e.code);" if code else "process.exitCode=1;console.log('SQL_FAILED');")+"}finally{await c.end()}})().catch(()=>{console.log('CONNECTION_FAILED');process.exitCode=1})"
 r.node(name,['node','-e',js],db['network'],{'DATABASE_URL':r.url(db,role)})
def schema_stage():
 auth.base.NODE=auth.IMAGE;auth.base.LABEL='nexonova.p45b.run'
 report={'phase':'P4.5-B','stage':'schema','status':'RUNNING','readiness':'BLOCKED','cases':{f'C{i:02}':'NOT_EXECUTED' for i in range(1,41)}}
 with tempfile.TemporaryDirectory(prefix='nexonova-p45b-schema-',dir='/var/tmp') as tmp:
  r=Run(tmp);r.id=r.id.replace('p43-','p45b-');report['runId']=r.id
  report['sourceHashes']={str(p.relative_to(ROOT)):sha(p) for p in [*OVERLAY.rglob('*'),Path(__file__),ROOT/'scripts/validate_business_auth.py',ROOT/'factory/business_infrastructure.py'] if p.is_file()}
  report['entrySha256']=sha(ROOT/'docs/migration/P4_5_B_ENTRY.json');report['schemaSha256']=compose(r.work)
  archive=OUT/'validators';archive.mkdir(parents=True,exist_ok=True);shutil.copyfile(__file__,archive/(r.id+'.py'))
  try:
   second=Path(tmp)/'second';report['compositionDeterministic']=compose(second)==report['schemaSha256'];shutil.rmtree(second);r.check('C32-composition-identical',report['compositionDeterministic'])
   for p in (ROOT/'templates/business-platform-auth').rglob('*'):
    if p.is_file():assert sha(p)==sha(r.work/p.relative_to(ROOT/'templates/business-platform-auth'))
   r.check('C32-core-byte-identical',True)
   r.node('setup-install',['npm','ci','--ignore-scripts','--no-audit','--no-fund'],network='bridge')
   r.node('setup-engine',['node','node_modules/@prisma/engines/dist/scripts/postinstall.js'],network='bridge')
   for name,args in [('auth-generate',['generate']),('module-validate',['validate','--config','prisma.requests.config.ts']),('module-generate',['generate','--config','prisma.requests.config.ts'])]:r.node(name,['node','node_modules/prisma/build/index.js',*args])
   db=r.create_db('requests')
   env={'MIGRATION_DATABASE_URL':r.url(db,'migrator')}
   r.node('C01-deploy',['node','node_modules/prisma/build/index.js','migrate','deploy','--config','prisma.requests.config.ts'],db['network'],env)
   report['tables']=sqlcheck(r,db,'C01-tables',"SELECT tablename FROM pg_tables WHERE schemaname='app' ORDER BY tablename",lambda v:v.splitlines()==['Account','InternalRequest','Session','User','Verification','_prisma_migrations'])
   report['columns']=sqlcheck(r,db,'C01-columns',"SELECT column_name FROM information_schema.columns WHERE table_schema='app' AND table_name='InternalRequest' ORDER BY ordinal_position",lambda v:v.splitlines()==['id','title','description','status','ownerId','createdAt','updatedAt','archivedAt','version'])
   report['constraints']=sqlcheck(r,db,'C01-real-fk',"SELECT conname||':'||pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='app.\"InternalRequest\"'::regclass ORDER BY conname",lambda v:'FOREIGN KEY ("ownerId") REFERENCES app."User"(id) ON UPDATE RESTRICT ON DELETE RESTRICT' in v and v.count('CHECK')==3)
   report['indexes']=sqlcheck(r,db,'C01-indexes',"SELECT indexname FROM pg_indexes WHERE schemaname='app' AND tablename='InternalRequest' ORDER BY indexname",lambda v:len(v.splitlines())==4)
   before=r.sql(db,'SELECT migration_name,checksum,finished_at FROM app._prisma_migrations ORDER BY migration_name').stdout
   r.node('C02-reapply',['node','node_modules/prisma/build/index.js','migrate','deploy','--config','prisma.requests.config.ts'],db['network'],env)
   r.check('C02-history-stable',before==r.sql(db,'SELECT migration_name,checksum,finished_at FROM app._prisma_migrations ORDER BY migration_name').stdout)
   r.record('fixture-user',r.sql(db,"INSERT INTO app.\"User\" (id,name,email,role,\"updatedAt\") VALUES ('fixture-owner','Fixture','fixture@example.invalid','member',NOW());"))
   r.record('runtime-grants',r.sql(db,(r.work/'validation/runtime-grants.sql').read_text()+(r.work/'validation/requests-runtime-grants.sql').read_text()))
   insert='INSERT INTO app."InternalRequest" (id,title,description,"ownerId","createdAt","updatedAt") VALUES (\'fixture-request\',\'Fixture\',\'\',\'fixture-owner\',NOW(),NOW())'
   rolequery(r,db,'runtime','C03-insert',insert);rolequery(r,db,'runtime','C03-select','SELECT * FROM app."InternalRequest"');rolequery(r,db,'runtime','C03-update','UPDATE app."InternalRequest" SET title=\'Changed\',version=version+1')
   for i,sql in enumerate(['CREATE TABLE app.forbidden(id int)','DELETE FROM app."InternalRequest"','TRUNCATE app."InternalRequest"','UPDATE app."InternalRequest" SET "ownerId"=\'fixture-owner\'','UPDATE app."InternalRequest" SET id=id','UPDATE app."InternalRequest" SET "createdAt"=NOW()','SELECT * FROM app._prisma_migrations']):rolequery(r,db,'runtime','C03-denied-'+str(i),sql,'42501')
   rolequery(r,db,'runtime','C04-orphan-denied',insert.replace('fixture-request','orphan').replace('fixture-owner','absent'),'23503')
   for name,sql in [('delete','DELETE FROM app."User" WHERE id=\'fixture-owner\''),('update','UPDATE app."User" SET id=\'other\' WHERE id=\'fixture-owner\'')]:
    p=r.sql(db,'\\set VERBOSITY verbose\n'+sql);r.check('C04-user-'+name+'-restricted',p.returncode!=0 and '23503' in p.stdout)
   r.record('archive-fixture',r.sql(db,'UPDATE app."InternalRequest" SET "archivedAt"=NOW()'))
   p=r.sql(db,'\\set VERBOSITY verbose\nDELETE FROM app."User" WHERE id=\'fixture-owner\'');r.check('C04-archived-user-restricted',p.returncode!=0 and '23503' in p.stdout)
   db['passwords']['bootstrap']=secrets.token_hex(24);r.values.append(db['passwords']['bootstrap'])
   r.record('bootstrap-role',r.sql(db,"CREATE ROLE bpbootstrap LOGIN PASSWORD '"+db['passwords']['bootstrap']+"'; GRANT CONNECT ON DATABASE "+db['database']+" TO bpbootstrap;"+(r.work/'validation/bootstrap-grants.sql').read_text()))
   for i,sql in enumerate(['SELECT * FROM app."InternalRequest"',insert.replace('fixture-request','bootstrap-test')]):rolequery(r,db,'bootstrap','C04-bootstrap-denied-'+str(i),sql,'42501')
   sqlcheck(r,db,'C04-no-orphans', 'SELECT count(*) FROM app."InternalRequest"',lambda v:v=='1')
   diff=r.node('C32-diff',['node','node_modules/prisma/build/index.js','migrate','diff','--from-config-datasource','--to-schema','prisma/business/schema.prisma','--script','--config','prisma.requests.config.ts'],db['network'],env)
   report['knownDiff']=diff.stdout
   statements=[s.strip() for s in diff.stdout.splitlines() if s.strip() and not s.startswith('--') and not s.startswith('Loaded Prisma')]
   r.check('C32-only-reviewed-fk-difference',statements==['ALTER TABLE "app"."InternalRequest" DROP CONSTRAINT "InternalRequest_ownerId_fkey";'])
   # Auth-only upgrade path with real existing User data; auth migration bytes remain unchanged.
   other=r.create_db('upgrade');otherenv={'MIGRATION_DATABASE_URL':r.url(other,'migrator')}
   r.node('C02-auth-only',['node','node_modules/prisma/build/index.js','migrate','deploy'],other['network'],otherenv)
   r.record('C02-existing-user',r.sql(other,"INSERT INTO app.\"User\" (id,name,email,\"updatedAt\") VALUES ('existing','Existing','existing@example.invalid',NOW())"))
   old=r.sql(other,'SELECT row_to_json(u) FROM app."User" u; SELECT checksum,finished_at FROM app._prisma_migrations').stdout
   r.node('C02-upgrade',['node','node_modules/prisma/build/index.js','migrate','deploy','--config','prisma.requests.config.ts'],other['network'],otherenv)
   after=r.sql(other,'SELECT row_to_json(u) FROM app."User" u; SELECT checksum,finished_at FROM app._prisma_migrations WHERE migration_name=\'00000000000000_auth_initial\'').stdout
   r.check('C02-existing-auth-unchanged',old==after)
   report['cases'].update({c:'PASS' for c in ['C01','C03','C04','C32']});report['cases']['C02']='NOT_EXECUTED';report['C02remaining']='Upgrade with real session/credentials remains for integrated auth stage.'
   prepared=Path('/var/tmp')/('nexonova-p45b-prepared-'+r.id);shutil.copytree(r.work,prepared);report['preparedWorkspace']=str(prepared);report['preparedScope']='Source/npm/generated clients only; no environment files or DB data. Retained for next stage and final cleanup.'
   report['status']='PASS'
  except Exception as e:report['status']='FAIL';report['error']=type(e).__name__+(': '+str(e) if isinstance(e,auth.base.InfrastructureError) else ': details withheld')
  finally:
   report['steps']=r.steps;report['cleanup']=r.finish();report['cleanupPassed']=all(x['removedOrAbsent'] for x in report['cleanup'])
   if not report['cleanupPassed']:report['status']='FAIL'
   report['secretScanPassed']=not any(v and v in json.dumps(report) for v in r.values)
   if not report['secretScanPassed']:raise RuntimeError('Secret found; receipt withheld')
   write(OUT/(r.id+'.json'),report);(OUT/(r.id+'.running.json')).unlink(missing_ok=True)
 report['temporaryDirectoryRemoved']=not Path(tmp).exists();write(OUT/(r.id+'.json'),report);print(report['status'],r.id,flush=True)
 return report
if __name__=='__main__':sys.exit(0 if schema_stage()['status']=='PASS' else 1)
