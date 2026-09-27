#!/usr/bin/env python3
from validate_business_requests import *
def main():
 auth.base.NODE=auth.IMAGE;auth.base.LABEL='nexonova.p45b.run'
 report={'phase':'P4.5-B','case':'C38','status':'RUNNING','scenarios':[],'validatorSha256':sha(__file__)}
 with tempfile.TemporaryDirectory(prefix='nexonova-p45b-cleanup-',dir='/var/tmp') as tmp:
  sentinel=Run(Path(tmp)/'sentinel') if False else None
  sentinelpath=Path(tmp)/'sentinel';sentinelpath.mkdir();sentinel=Run(sentinelpath);sentinel.id=sentinel.id.replace('p43-','p45b-sentinel-')
  name=sentinel.id+'-container';sentinel.register('container',name)
  sentinel.record('sentinel-start',sentinel.docker(['run','-d','--pull=never','--name',name,'--label',auth.base.LABEL+'='+sentinel.id,'--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--memory=64m',auth.IMAGE,'node','-e','setInterval(()=>{},1000)']))
  try:
   for mode in ['success','failure','timeout']:
    path=Path(tmp)/mode;path.mkdir();r=Run(path);r.id=r.id.replace('p43-','p45b-');r.work.mkdir()
    row={'mode':mode,'runId':r.id}
    try:
     for kind in ['network','volume']:
      resource=r.id+'-'+kind;r.register(kind,resource);r.record(mode+'-'+kind,r.docker([kind,'create',*(['--internal'] if kind=='network' else []),'--label',auth.base.LABEL+'='+r.id,resource]))
     r.check('foreign-removal-denied',not r.remove('container',name) and sentinel.exists('container',name))
     if mode=='timeout':
      try:r.node('timeout',['node','-e','setInterval(()=>{},1000)'],timeout=.3)
      except subprocess.TimeoutExpired:row['inducedTimeoutObserved']=True
      else:raise AssertionError('Timeout not observed')
     elif mode=='failure':
      try:r.node('failure',['node','-e','process.exit(7)'])
      except auth.base.InfrastructureError:row['inducedFailureObserved']=True
      else:raise AssertionError('Failure not observed')
     else:r.node('success',['node','-e',"console.log('ok')"])
    finally:
     row['cleanup']=r.finish();row['steps']=r.steps;row['cleanupPassed']=all(x['removedOrAbsent'] for x in row['cleanup']);row['sentinelIntact']=sentinel.exists('container',name);row['environmentFilesAbsent']=not list(path.glob('env-*'));report['scenarios'].append(row)
   report['status']='PASS' if all(x['cleanupPassed'] and x['sentinelIntact'] and x['environmentFilesAbsent'] for x in report['scenarios']) else 'FAIL'
  finally:report['sentinelCleanup']=sentinel.finish()
 report['temporaryDirectoryRemoved']=not Path(tmp).exists();write(OUT/'cleanup-scenarios-d02.json',report);print(report['status'])
if __name__=='__main__':main()
