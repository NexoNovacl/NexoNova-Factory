#!/usr/bin/env python3
"""Sanitized inventory of owned P4.4 temporary resources; no process argv or env output."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 out={'scope':'Host P4.4-B inventory; unrelated resources untouched','temporaryDirectories':[],'matchingProcesses':[],'docker':{}}
 for folder in sorted(Path('/var/tmp').iterdir()):
  if not folder.is_dir() or not any(s in folder.name for s in ['p44','p4-4','p43','p44b-base']):continue
  count=0;size=0;symlinks=0
  for current,dirs,files in os.walk(folder,followlinks=False):
   symlinks+=sum((Path(current)/name).is_symlink() for name in dirs+files)
   for name in files:
    p=Path(current)/name
    if p.is_symlink():continue
    count+=1;size+=p.stat().st_size
  out['temporaryDirectories'].append({'path':str(folder),'uid':folder.stat().st_uid,'files':count,'bytes':size,'symlinks':symlinks,'topLevel':sorted(p.name for p in folder.iterdir())})
 for p in Path('/proc').iterdir():
  if not p.name.isdigit() or int(p.name)==os.getpid():continue
  try:
   args=(p/'cmdline').read_bytes().split(b'\0');cwd=os.readlink(p/'cwd')
   # Do not match shell command text; only executable/script paths or cwd.
   matched=any(b'validate_business_auth' in a and b' ' not in a for a in args[:4]) or any(s in cwd for s in ['p44b','p44bc'])
   if matched:out['matchingProcesses'].append({'pid':int(p.name),'name':(p/'comm').read_text().strip(),'cwdClass':'owned-test-directory' if 'p44' in cwd else 'factory','argvWithheld':True})
  except (OSError,PermissionError):pass
 for kind,cmd in [('containers',['ps','-a','--format','{{.Names}}\t{{.Status}}']),('networks',['network','ls','--format','{{.Name}}']),('volumes',['volume','ls','--format','{{.Name}}'])]:
  p=subprocess.run(['docker',*cmd],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);out['docker'][kind]={'exitCode':p.returncode,'items':p.stdout.splitlines()}
 out['validatorSha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 suffix='FINAL' if '--final' in sys.argv else 'INITIAL'
 (ROOT/('docs/migration/P4_4_B_HOST_'+suffix+'.json')).write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(out))
if __name__=='__main__':main()
