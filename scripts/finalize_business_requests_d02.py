#!/usr/bin/env python3
"""Final preservation and cleanup of controlled D02 continuation; never rewrites old receipts."""
from validate_business_requests import *
from factory.product_integrity import validate_product_integrity

def main():
 work=Path('/var/tmp/nexonova-p45b-d02-work')
 entry=json.loads((ROOT/'docs/migration/P4_5_B_ENTRY.json').read_text())
 report={'phase':'P4.5-B','stage':'final-preservation-cleanup','steps':[],'status':'RUNNING','sourceHashes':{str(Path(__file__).relative_to(ROOT)):sha(__file__)}}
 def check(name,ok):
  report['steps'].append({'name':name,'passed':bool(ok),'exitCode':0 if ok else 1})
  if not ok:raise AssertionError(name)
 check('C37-entry-hashes',all((ROOT/p).is_file() and sha(ROOT/p)==h for p,h in entry['hashes'].items()));report['entryFileCount']=len(entry['hashes'])
 for product,manifest in [('nexonova-website','P3_5_GENERATION_MANIFEST.json'),('synthetic-website','P3_6_GENERATION_MANIFEST.json')]:
  result=validate_product_integrity(ROOT.parent/product,json.loads((ROOT/'docs/migration'/manifest).read_text()),[ROOT.parent/'nexonova-prototype']);report.setdefault('products',{})[product]=result;check('C37-'+product,result['status']=='complete')
 source=json.loads((ROOT/'config/pilots/nexonova/source-manifest.json').read_text());prototype=ROOT.parent/'nexonova-prototype';expected={e['path']:e['sha256'].removeprefix('sha256:') for e in source['entries']};actual={p.relative_to(prototype).as_posix():sha(p) for p in prototype.rglob('*') if p.is_file() and '.git' not in p.relative_to(prototype).parts};check('C37-prototype-exact-set',actual==expected);report['prototypeFileCount']=len(actual)
 tests=json.loads((OUT/'preservation-tests-d02.json').read_text());check('C37-final-88-tests',tests['status']=='PASS');report['preservationTestsSha256']=sha(OUT/'preservation-tests-d02.json')
 # Original checkpoint and all its referenced evidence remain immutable.
 old=json.loads((OUT/'d02-entry/P4_5_B_FINAL_RECEIPT.json').read_text());check('C37-prior-evidence-intact',all(sha(ROOT/ref['path'])==ref['sha256'] for case in old['cases'].values() for ref in case['evidence']))
 d02=json.loads((OUT/'D02-page-vary.json').read_text());check('C28-no-next-patches',all(sha(work/x['path'])==x['sha256'] for x in d02['frameworkSources']))
 # Recompose source to verify deterministic schema and unchanged auth model/migration now too.
 with tempfile.TemporaryDirectory(prefix='nexonova-p45b-verify-',dir='/var/tmp') as tmp:
  composed=Path(tmp)/'work';schema=compose(composed);check('C32-composition-current',schema==sha(work/'prisma/business/schema.prisma'))
  core=ROOT/'templates/business-platform-auth';check('C32-auth-original-identical',all(sha(p)==sha(composed/p.relative_to(core)) for p in core.rglob('*') if p.is_file()))
  report['schemaSha256']=schema
 auth.base.NODE=auth.IMAGE;auth.base.LABEL='nexonova.p45b.run'
 with tempfile.TemporaryDirectory(prefix='nexonova-p45b-final-',dir='/var/tmp') as tmp:
  r=Run(tmp);r.id=r.id.replace('p43-','p45b-');r.work=work
  versions=r.node('C33-final-versions',['node','-e',"console.log(JSON.stringify({node:process.version,next:require('next/package.json').version,react:require('react/package.json').version,prisma:require('prisma/package.json').version,pg:require('pg/package.json').version,typescript:require('typescript/package.json').version,betterAuth:JSON.parse(require('fs').readFileSync('node_modules/better-auth/package.json')).version}))"])
  report['versions']=json.loads(versions.stdout);check('C33-version-matrix',report['versions']=={'node':'v22.23.2','next':'15.5.25','react':'19.2.8','prisma':'7.5.0','pg':'8.16.3','typescript':'5.9.3','betterAuth':'1.7.5'})
  report['openssl']=r.node('C33-openssl-version',['openssl','version']).stdout.strip();check('C33-openssl-present',report['openssl'].startswith('OpenSSL 3.0.20'))
  report['imageReferences']={'node':auth.IMAGE,'postgres':auth.base.PG};report['imageIds']={}
  for key,ref in report['imageReferences'].items():
   data=json.loads(r.docker(['image','inspect',ref]).stdout)[0];report['imageIds'][key]=data['Id'];check('C33-image-'+key,data['Architecture']=='amd64')
  report['runnerCleanup']=r.finish();check('C38-final-helper-cleanup',all(x['removedOrAbsent'] for x in report['runnerCleanup']))
  report['steps']+=r.steps
  report['inventory']={}
  for kind in ['container','network','volume']:
   p=r.docker([kind,'ls',*(['-a'] if kind=='container' else []),'--filter','label='+auth.base.LABEL,'--format','{{.Names}}' if kind=='container' else '{{.Name}}']);report['inventory'][kind]=p.stdout.splitlines();check('C38-no-owned-'+kind,p.returncode==0 and not p.stdout.strip())
  report['unrelatedContainersUntouched']=r.docker(['container','ls','-a','--format','{{.Names}}']).stdout.splitlines()
  # Only remove the exact workspace created for this authorized continuation.
  if work.parent!=Path('/var/tmp') or work.name!='nexonova-p45b-d02-work':raise AssertionError('Unexpected path')
  shutil.rmtree(work);check('C38-workspace-removed',not work.exists())
  report['remainingOwnedPaths']=[str(p) for p in Path('/var/tmp').glob('nexonova-p45b-*') if p!=Path(tmp)];check('C38-no-owned-paths',not report['remainingOwnedPaths'])
 scenarios=json.loads((OUT/'cleanup-scenarios-d02.json').read_text());check('C38-success-failure-timeout-sentinel',scenarios['status']=='PASS' and scenarios['temporaryDirectoryRemoved'] and all(x['removedOrAbsent'] for x in scenarios['sentinelCleanup']));report['cleanupScenariosSha256']=sha(OUT/'cleanup-scenarios-d02.json');check('C38-final-directory-removed',not Path(tmp).exists())
 ps=subprocess.run(['ps','-eo','pid=,comm=,args='],text=True,stdout=subprocess.PIPE,check=True).stdout.splitlines();owned=[];browser=[]
 for line in ps:
  parts=line.strip().split(None,2)
  if len(parts)<3:continue
  pid,comm,args=parts
  if comm=='node' and any(x in args for x in ['check_business_requests.mjs','check_business_requests_headers.mjs','check_business_auth_continuation.mjs']):owned.append(int(pid))
  if comm.startswith(('chrome-headless','chromium')) and 'playwright_chromiumdev_profile-' in args:browser.append(int(pid))
 report['remainingValidatorNodePids']=owned;report['remainingPlaywrightBrowserPids']=browser;check('C38-no-validator-processes',not owned and not browser)
 report['status']='PASS';write(OUT/'final-preservation-cleanup-d02.json',report)
 # Remove only obsolete progress markers of our finished fixture runs.
 for p in OUT.glob('*.running.json'):p.unlink()
 print('PASS final preservation and cleanup')
if __name__=='__main__':main()
