"""Read-only P4.2 contract CLI; stdout is a declaration, never generated product files."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from factory.business_contracts import load_bundle,build_plan,digest,BusinessContractError
from factory.generation import read_json

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pilot',type=Path,default=ROOT/'config/business/internal-requests-pilot');p.add_argument('--plan',action='store_true');a=p.parse_args()
 try:
  policy=read_json(ROOT/'config/business/authorization.json')
  if set(policy)!={'format','authorizedOrders','basis'} or policy['format']!='nexonova.business-contract-authorization.v1' or not policy['basis']:raise BusinessContractError('Invalid host authorization')
  plan=build_plan(load_bundle(a.pilot),policy['authorizedOrders'])
  print(json.dumps(plan,sort_keys=True,indent=2) if a.plan else 'contracts=valid; planHash='+digest(plan)+'; execution=BLOCKED; futureGates=NOT_IMPLEMENTED')
  return 0 # Contract validation success only; never execution readiness.
 except (ValueError,TypeError,KeyError,OSError):
  print('contracts=invalid; execution=BLOCKED; input values withheld',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
