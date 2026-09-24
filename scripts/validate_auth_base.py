"""Re-execute the approved P4.3 fixture in a disposable copy with the P4.4 image.
Only process-local image/root/label overrides; historical files/receipts are untouched.
"""
from pathlib import Path
import json,hashlib,shutil,sys,tempfile,subprocess
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from factory import business_infrastructure as base

def main():
 lock=json.loads((ROOT/'infrastructure/images/node-openssl/image-lock.json').read_text())
 image=lock['executionReference'];old=(base.ROOT,base.NODE,base.LABEL)
 with tempfile.TemporaryDirectory(prefix='p44b-base-',dir='/var/tmp') as temp:
  root=Path(temp);target=root/'templates/business-platform';target.parent.mkdir();shutil.copytree(ROOT/'templates/business-platform',target)
  (root/'docs/migration').mkdir(parents=True)
  compose=target/'compose.yaml';compose.write_text(compose.read_text().replace(base.NODE,image).replace(base.LABEL,'nexonova.p44b.base'))
  try:
   base.ROOT=root;base.NODE=image;base.LABEL='nexonova.p44b.base'
   report=base.validate_core()
  finally:base.ROOT,base.NODE,base.LABEL=old
  report['scope']='P4.4-B OpenSSL base matrix, without Better Auth'
  report['imageLock']=lock
  report['wrapperSha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
  report['historicalReceiptsModified']=False
  engine=next((s for s in report['steps'] if s['name']=='prepare-prisma-engine'),{})
  report['opensslDetectionWarning']=any(t in engine.get('output','').lower() for t in ['failed to detect','openssl-1.1.x'])
  if report['opensslDetectionWarning']:report['status']='FAIL'
  (ROOT/'docs/migration/P4_4_B_BASE_MATRIX.json').write_text(json.dumps(report,indent=2)+'\n')
  print('BASE_MATRIX='+report['status']);return 0 if report['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
