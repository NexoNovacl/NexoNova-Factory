#!/usr/bin/env python3
"""Fail-closed consumer: verifies individual cases, step references, hashes and sources."""
import json,hashlib,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sethash(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def evaluate(receipt,root=ROOT):
 requirements=json.loads((ROOT/'docs/migration/P4_5_A_VALIDATION.json').read_text())['futureGateRequirements']
 cases=receipt.get('cases',{});failures={}
 source=receipt.get('sourceHashes',{})
 source_ok=bool(source) and receipt.get('sourceSetSha256')==sethash(source) and all((root/p).is_file() and sha(root/p)==h for p,h in source.items())
 for i in range(1,41):
  c=f'C{i:02}';item=cases.get(c,{});errors=[]
  if item.get('status')!='PASS':errors.append(item.get('status','MISSING'))
  if not source_ok:errors.append('SOURCE_PROVENANCE')
  evidence=item.get('evidence',[])
  if not evidence:errors.append('MISSING_EVIDENCE')
  if item.get('proofSetSha256')!=sethash(evidence):errors.append('PROOF_SET_CHANGED')
  for ref in evidence:
   path=root/ref.get('path','')
   if not path.is_file() or sha(path)!=ref.get('sha256'):errors.append('EVIDENCE_HASH');continue
   try:
    data=json.loads(path.read_text());indexes=ref['stepIndexes']
    if not indexes:errors.append('MISSING_STEPS')
    for index in indexes:
     if type(index) is not int or index<0:raise ValueError('Invalid step index')
     step=data['steps'][index]
     if step.get('passed') is not True:errors.append('STEP_NOT_PASS')
   except (ValueError,KeyError,IndexError,TypeError):errors.append('INVALID_REFERENCE')
  if errors:failures[c]=errors
 return {'gates':{gate:{'status':'BLOCKED' if any(c in failures for c in required) else 'PASS','missingOrInvalidCases':[c for c in required if c in failures]} for gate,required in requirements.items()},'invalidCases':failures,'readiness':'BLOCKED','generation':'NOT_IMPLEMENTED','autonomy':'NOT_IMPLEMENTED'}
def selftest():
 import tempfile
 results=[]
 with tempfile.TemporaryDirectory(prefix='p45-evidence-') as temp:
  root=Path(temp);(root/'source').write_text('source');(root/'evidence.json').write_text(json.dumps({'steps':[{'passed':True}]}))
  fixture={'sourceHashes':{'source':sha(root/'source')},'cases':{f'C{i:02}':{'status':'PASS','evidence':[{'path':'evidence.json','sha256':sha(root/'evidence.json'),'stepIndexes':[0]}]} for i in range(1,41)}}
  fixture['sourceSetSha256']=sethash(fixture['sourceHashes'])
  for c in fixture['cases'].values():c['proofSetSha256']=sethash(c['evidence'])
  assert all(x['status']=='PASS' for x in evaluate(fixture,root)['gates'].values());results.append('positive-consumer-fixture-only')
  for status in ['FAIL','BLOCKED','NOT_EXECUTED']:
   bad=copy.deepcopy(fixture);bad['cases']['C01']['status']=status;assert evaluate(bad,root)['gates']['database-migrations']['status']=='BLOCKED';results.append(status)
  for operation in ['case','evidence','hash','steps','source']:
   bad=copy.deepcopy(fixture)
   if operation=='case':del bad['cases']['C01']
   elif operation=='evidence':bad['cases']['C01']['evidence']=[]
   elif operation=='hash':bad['cases']['C01']['evidence'][0]['sha256']='changed'
   elif operation=='steps':bad['cases']['C01']['evidence'][0]['stepIndexes']=[]
   else:bad['sourceHashes']['source']='changed'
   assert evaluate(bad,root)['gates']['database-migrations']['status']=='BLOCKED';results.append('missing-or-altered-'+operation)
  (root/'evidence.json').write_text(json.dumps({'steps':[{'passed':False}]}));bad=copy.deepcopy(fixture)
  for c in bad['cases'].values():
   c['evidence'][0]['sha256']=sha(root/'evidence.json');c['proofSetSha256']=sethash(c['evidence'])
  assert all(x['status']=='BLOCKED' for x in evaluate(bad,root)['gates'].values());results.append('failed-referenced-step')
 report={'phase':'P4.5-B','case':'C39','status':'PASS','scope':'Evidence-consumer tests only; synthetic fixtures do not demonstrate business integration','validatorSha256':sha(Path(__file__)),'steps':[{'name':'C39-'+x,'passed':True,'exitCode':0} for x in results]}
 path=ROOT/'docs/migration/p4-5-b-runs/evidence-consumer-d02.json';path.write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(results))
if __name__=='__main__':
 import sys
 if len(sys.argv)==1:selftest()
 else:print(json.dumps(evaluate(json.loads(Path(sys.argv[1]).read_text())),indent=2))
