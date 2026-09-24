"""Explicit local P4.3 experiment, never a business generation WorkOrder execution."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from factory.business_infrastructure import validate_core
if __name__=='__main__':
 result=validate_core();print('P4.3='+result['status']+'; global readiness=BLOCKED');raise SystemExit(130 if result.get('interrupted') else (0 if result['status']=='PASS' else 1))
