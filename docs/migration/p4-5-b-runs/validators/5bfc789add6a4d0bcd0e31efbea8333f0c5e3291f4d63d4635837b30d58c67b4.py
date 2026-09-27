#!/usr/bin/env python3
"""Incremental build of isolated approved composition; no product generation."""
from validate_business_requests import *
def main():
 auth.base.NODE=auth.IMAGE;auth.base.LABEL='nexonova.p45b.run'
 prior=json.loads((OUT/'p45b-ba2c6a6f1698418a.json').read_text());work=Path(prior['preparedWorkspace'])
 with tempfile.TemporaryDirectory(prefix='nexonova-p45b-build-',dir='/var/tmp') as tmp:
  r=Run(tmp);r.id=r.id.replace('p43-','p45b-');r.work=work
  report={'stage':'build','runId':r.id,'status':'RUNNING','sourceHashes':{str(p.relative_to(ROOT)):sha(p) for p in [*OVERLAY.rglob('*'),Path(__file__)] if p.is_file()},'workspace':str(work)}
  try:
   for p in OVERLAY.rglob('*'):
    if p.is_file():dest=work/p.relative_to(OVERLAY);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
   config=json.loads((work/'tsconfig.checks.json').read_text());config['include']+=['src/modules/internal-requests/**/*.ts','validation/requests-users.ts'];(work/'tsconfig.checks.json').write_text(json.dumps(config,indent=2)+'\n')
   if '--repair-install' in sys.argv:
    r.node('repair-prepared-symlinks',['npm','ci','--ignore-scripts','--no-audit','--no-fund'],network='bridge')
    r.node('repair-engine',['node','node_modules/@prisma/engines/dist/scripts/postinstall.js'],network='bridge')
   for name,cmd in [('C33-compile',['npm','run','compile:checks']),('C33-unit',['npm','test']),('C33-typecheck',['npm','run','typecheck']),('C33-build',['npm','run','build'])]:r.node(name,cmd,timeout=600)
   report['status']='PASS'
  except Exception as e:report['status']='FAIL';report['error']=str(e)
  finally:
   report['steps']=r.steps;report['cleanup']=r.finish();report['cleanupPassed']=all(x['removedOrAbsent'] for x in report['cleanup']);write(OUT/(r.id+'.json'),report);(OUT/(r.id+'.running.json')).unlink(missing_ok=True)
  print(report['status'],r.id,flush=True);return report['status']=='PASS'
if __name__=='__main__':sys.exit(0 if main() else 1)
