#!/usr/bin/env python3
"""Read-only historical preservation plus scoped regression; writes a new receipt."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from factory.product_integrity import validate_product_integrity

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report={'scope':'P4.4-B continuation preservation','status':'PASS','validatorSha256':sha(Path(__file__))}
 a=json.loads((ROOT/'docs/migration/P4_4_A_VALIDATION.json').read_text())
 hashes=a['protectedHashesAfter']
 report['protected']={'checked':len(hashes),'changed':[p for p,h in hashes.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]}
 recovery=json.loads((ROOT/'docs/migration/P4_4_B_RECOVERY_AUDIT.json').read_text())
 report['recoveredImplementation']={'checked':len(recovery['currentImplementationHashes']),'changed':[p for p,h in recovery['currentImplementationHashes'].items() if sha(ROOT/p)!=h]}
 historical={p:sha(ROOT/p) for p in subprocess.check_output(['git','ls-files','docs/migration','docs/business-platform','infrastructure/images'],cwd=ROOT,text=True).splitlines() if (ROOT/p).is_file()}
 report['historicalGitChanges']=subprocess.check_output(['git','diff','--name-only','HEAD','--','docs/migration','docs/business-platform','infrastructure/images'],cwd=ROOT,text=True).splitlines()
 report['historicalHashes']=historical
 baseline=json.loads((ROOT/'docs/migration/P3_BASELINE.json').read_text());report['products']={}
 for file in ['P3_5_GENERATION_MANIFEST.json','P3_6_GENERATION_MANIFEST.json']:
  p=ROOT/'docs/migration'/file;manifest=json.loads(p.read_text());name=manifest['projectId']
  assert manifest['stableHash']==baseline['products'][name]
  result=validate_product_integrity(ROOT.parent/name,manifest,[ROOT,ROOT.parent/'nexonova-prototype',ROOT.parent/'.nexonova-staging'])
  report['products'][name]={'manifest':str(p.relative_to(ROOT)),'manifestSha256':sha(p),'result':result}
 source=ROOT/'config/pilots/nexonova/source-manifest.json';entries=json.loads(source.read_text())['entries']
 checked=[];changed=[]
 for e in entries:
  if not e.get('sha256'):continue
  p=ROOT.parent/'nexonova-prototype'/e['path'];checked.append(e['path'])
  if not p.is_file() or sha(p)!=e['sha256'].removeprefix('sha256:'):changed.append(e['path'])
 report['prototype']={'manifest':str(source.relative_to(ROOT)),'manifestSha256':sha(source),'checked':len(checked),'changed':changed}
 report['commands']=[]
 for cmd in [[str(ROOT/'.venv/bin/python'),'-B','-m','pytest','tests/test_p3_baseline.py','tests/test_business_contracts.py','tests/test_business_infrastructure.py','-q','-p','no:cacheprovider'],['python3','-B','scripts/validate_business_contracts.py'],['python3','-B','scripts/validate_repository.py']]:
  p=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);report['commands'].append({'command':[v.replace(str(ROOT)+'/','') for v in cmd],'exitCode':p.returncode,'output':p.stdout})
 if changed or report['protected']['changed'] or report['recoveredImplementation']['changed'] or report['historicalGitChanges'] or any(c['exitCode'] for c in report['commands']):report['status']='FAIL'
 (ROOT/'docs/migration/P4_4_B_CONTINUATION_PRESERVATION.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['historicalHashes','commands']}))
 return 0 if report['status']=='PASS' else 1
if __name__=='__main__':sys.exit(main())
