#!/usr/bin/env python3
"""Remove only the two recovered, verified disposable preparation directories."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report={'scope':'Recovered P4.4-B image/build/npm staging only','status':'PASS','directories':[],'preserved':['installed pinned Docker images','shared Playwright browser installation','all historical repository receipts','unrelated containers and files'],'validatorSha256':sha(Path(__file__))}
 paths=[Path('/var/tmp/nexonova-p44b-image'),Path('/var/tmp/p44b-auth-compat-qgpgn1sx')]
 p=subprocess.run(['docker','ps','-aq'],text=True,capture_output=True,check=True)
 mounts=[]
 if p.stdout.strip():
  objects=json.loads(subprocess.run(['docker','inspect',*p.stdout.split()],text=True,capture_output=True,check=True).stdout)
  mounts=[m.get('Source','') for o in objects for m in o.get('Mounts',[])]
 for directory in paths:
  entry={'path':str(directory),'existed':directory.exists()}
  if directory.exists():
   assert not directory.is_symlink() and directory.stat().st_uid==os.getuid()
   assert not any(m==str(directory) or m.startswith(str(directory)+'/') for m in mounts)
   for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:cwd=os.readlink(p/'cwd')
    except OSError:continue
    assert cwd!=str(directory) and not cwd.startswith(str(directory)+'/')
   if directory.name=='nexonova-p44b-image':
    assert sha(directory/'context/Dockerfile')==sha(ROOT/'infrastructure/images/node-openssl/Dockerfile')
    markers=['context/Dockerfile','context/SHA256SUMS','reproducibility.json','build-1.json','build-2.json']
   else:
    package=json.loads((directory/'package.json').read_text())
    assert package['name']=='business-platform-auth-core' and package['dependencies']['better-auth']=='1.7.5'
    assert (directory/'compile.log').is_file() and (directory/'.npm-cache').is_dir()
    markers=['package.json','package-lock.json','compile.log','generate.log','engine.log']
   entry['verifiedMarkers']={m:sha(directory/m) for m in markers}
   shutil.rmtree(directory)
  entry['removedOrAbsent']=not directory.exists();assert entry['removedOrAbsent'];report['directories'].append(entry)
 (ROOT/'docs/migration/P4_4_B_TEMP_CLEANUP.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report))
if __name__=='__main__':main()
