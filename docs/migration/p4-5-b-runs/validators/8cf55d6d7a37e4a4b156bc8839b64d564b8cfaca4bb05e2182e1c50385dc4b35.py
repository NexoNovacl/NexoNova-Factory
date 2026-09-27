#!/usr/bin/env python3
"""Close only the stopped P4.5-B attempt; preserve partial evidence and human-review blocker."""
from validate_business_requests import *
from factory.product_integrity import validate_product_integrity

def main():
 work=Path(json.loads((OUT/'p45b-ba2c6a6f1698418a.json').read_text())['preparedWorkspace'])
 diagnostic={'phase':'P4.5-B','decision':'D02','status':'BLOCKED_PENDING_HUMAN_REVIEW','caseStatus':{'C28':'FAIL'},'expected':'no-store and Vary Cookie on success/errors/pages','actual':{'pageStatus':200,'cacheControl':'no-store','vary':'rsc, next-router-state-tree, next-router-prefetch, next-router-segment-prefetch, Accept-Encoding'},'evidence':['p45b-f71fae0235be4d6d.json','p45b-0a12a2069e164369.json'],'diagnosis':'Next 15.5.25 app-page template calls res.setHeader(Vary, routeModule.getVaryHeader(...)), replacing middleware Vary Cookie. Raw get_all(Vary) confirms one header without Cookie; not dictionary flattening. API handlers retain Cookie.','controlPreserved':'No-store remains on pages; server identity and resource predicates remain. No claim that missing Vary enables a demonstrated leak.','humanReviewRequiredBy':'User execution rule 9: stop before required approved-core changes or weakening approved controls.','notApplied':['No Next patch/upgrade','No core/start/auth modification','No relaxation of C28','No replacement of FK or grants'],'options':[{'id':'A','proposal':'Review a module-specific response boundary that appends Cookie after Next rendering while preserving framework Vary tokens and unchanged auth. Requires design/implementation approval and real regression tests; not implemented.','recommended':True},{'id':'B','proposal':'Explicitly revise page cache acceptance to verified no-store without requiring Vary Cookie on RSC pages, retaining API Vary Cookie. This changes the approved C28 requirement; not applied.'}],'nextVersion':'15.5.25'}
 for name in ['build/templates/app-page.js','server/route-modules/app-page/module.js']:
  p=work/'node_modules/next/dist'/name
  diagnostic.setdefault('frameworkSources',[]).append({'path':'node_modules/next/dist/'+name,'sha256':sha(p),'matchingLines':[{'line':i,'text':line.strip()} for i,line in enumerate(p.read_text().splitlines(),1) if 'getVaryHeader' in line or "setHeader('Vary'" in line or 'return baseVaryHeader;' in line]})
 write(OUT/'D02-page-vary.json',diagnostic)
 entry=json.loads((ROOT/'docs/migration/P4_5_B_ENTRY.json').read_text())
 preservation={'phase':'P4.5-B','scope':'Final entry/historical/product preservation at mandatory D02 stop','steps':[]}
 differences=[p for p,h in entry['hashes'].items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
 preservation['entryDifferences']=differences;preservation['entryFilesCompared']=len(entry['hashes']);preservation['steps'].append({'name':'C37-entry-hashes','passed':not differences,'exitCode':0 if not differences else 1})
 for product,manifest in [('nexonova-website','P3_5_GENERATION_MANIFEST.json'),('synthetic-website','P3_6_GENERATION_MANIFEST.json')]:
  baseline=json.loads((ROOT/'docs/migration'/manifest).read_text());result=validate_product_integrity(ROOT.parent/product,baseline,[ROOT.parent/'nexonova-prototype']);preservation.setdefault('products',{})[product]=result;preservation['steps'].append({'name':'C37-'+product,'passed':result['status']=='complete','exitCode':0})
 source=json.loads((ROOT/'config/pilots/nexonova/source-manifest.json').read_text());prototype=ROOT.parent/'nexonova-prototype';expected={e['path']:e['sha256'].removeprefix('sha256:') for e in source['entries']}
 actual={p.relative_to(prototype).as_posix():sha(p) for p in prototype.rglob('*') if p.is_file() and '.git' not in p.relative_to(prototype).parts}
 preservation['prototypeFiles']=len(actual);preservation['steps'].append({'name':'C37-prototype-exact-set-hashes','passed':actual==expected,'exitCode':0 if actual==expected else 1})
 tests=json.loads((OUT/'preservation-tests.json').read_text());preservation['steps'].append({'name':'C37-88-tests','passed':tests['status']=='PASS','exitCode':tests['exitCode']});preservation['testsReceiptSha256']=sha(OUT/'preservation-tests.json')
 preservation['status']='PASS' if all(x['passed'] for x in preservation['steps']) else 'FAIL';write(OUT/'preservation-final.json',preservation)
 # Inventory and remove only the retained workspace named in this execution's successful schema receipt.
 auth.base.LABEL='nexonova.p45b.run';auth.base.NODE=auth.IMAGE
 with tempfile.TemporaryDirectory(prefix='nexonova-p45b-final-',dir='/var/tmp') as tmp:
  r=Run(tmp);r.id=r.id.replace('p43-','p45b-');cleanup={'phase':'P4.5-B','steps':[],'inventory':{},'preparedWorkspace':str(work)}
  for kind in ['container','network','volume']:
   args=[kind,'ls',*(['-a'] if kind=='container' else []),'--filter','label='+auth.base.LABEL,'--format','{{.Names}}' if kind=='container' else '{{.Name}}'];p=r.docker(args);cleanup['inventory'][kind]=p.stdout.splitlines();cleanup['steps'].append({'name':'C38-final-'+kind,'passed':p.returncode==0 and not p.stdout.strip(),'exitCode':p.returncode})
  # Read-only inventory of unrelated containers; no stop/remove operations against them.
  cleanup['otherContainers']=r.docker(['container','ls','-a','--format','{{.Names}}']).stdout.splitlines()
  if work.parent!=Path('/var/tmp') or work.name!='nexonova-p45b-prepared-p45b-ba2c6a6f1698418a':raise ValueError('Unexpected workspace')
  shutil.rmtree(work);cleanup['steps'].append({'name':'C38-prepared-workspace-removed','passed':not work.exists(),'exitCode':0})
  cleanup['temporaryPaths']=sorted(str(p) for p in Path('/var/tmp').glob('nexonova-p45b-*') if p!=Path(tmp))
  cleanup['steps'].append({'name':'C38-no-owned-temporary-paths','passed':not cleanup['temporaryPaths'],'exitCode':0 if not cleanup['temporaryPaths'] else 1})
  scenarios=json.loads((OUT/'cleanup-scenarios.json').read_text());cleanup['steps'].append({'name':'C38-success-failure-timeout-sentinel','passed':scenarios['status']=='PASS' and scenarios['temporaryDirectoryRemoved'] and all(x['removedOrAbsent'] for x in scenarios['sentinelCleanup']),'exitCode':0})
  cleanup['scenarioReceiptSha256']=sha(OUT/'cleanup-scenarios.json');cleanup['status']='PASS' if all(x['passed'] for x in cleanup['steps']) else 'FAIL'
 cleanup['finalTemporaryDirectoryRemoved']=not Path(tmp).exists();write(OUT/'cleanup-final.json',cleanup)
 # These are our stale progress markers, never historical evidence. No owned Docker resources remain.
 if cleanup['status']=='PASS':
  for p in OUT.glob('*.running.json'):p.unlink()
 print(json.dumps({'preservation':preservation['status'],'cleanup':cleanup['status'],'blocker':'D02'},indent=2))
if __name__=='__main__':main()
