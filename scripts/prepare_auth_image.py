"""Reproduce the approved OpenSSL image offline after public-package preparation.
No application credentials, Docker login, remote daemon or registry publication.
"""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile,urllib.request
ROOT=Path(__file__).resolve().parents[1]

def main():
 source=ROOT/'infrastructure/images/node-openssl'
 lock=json.loads((source/'image-lock.json').read_text())
 if hashlib.sha256((source/'Dockerfile').read_bytes()).hexdigest()!=lock['recipeSha256']:
  raise ValueError('Recipe differs from approved image lock')
 with tempfile.TemporaryDirectory(prefix='p44b-image-rebuild-',dir='/var/tmp') as tmp:
  base=Path(tmp);context=base/'context';context.mkdir();client=base/'client';client.mkdir()
  for name in ['Dockerfile','SHA256SUMS']:shutil.copyfile(source/name,context/name)
  for package in lock['packages']:
   if not package['url'].startswith('https://snapshot.debian.org/archive/'):raise ValueError('Unapproved package source')
   data=urllib.request.urlopen(package['url'],timeout=90).read(20_000_001)
   if hashlib.sha256(data).hexdigest()!=package['sha256']:raise ValueError('Package integrity mismatch')
   (context/package['file']).write_bytes(data)
  env={'PATH':'/usr/bin:/bin','HOME':str(client),'DOCKER_CONFIG':str(client)}
  command=['docker','--host','unix:///var/run/docker.sock'];results=[]
  for iteration in [1,2]:
   args=[*command,'buildx','build','--no-cache','--pull=false','--network=none','--provenance=false','--platform='+lock['platform'],'--build-arg','SOURCE_DATE_EPOCH='+str(lock['sourceDateEpoch']),'--output',f'type=docker,name=nexonova-p44b-node-openssl:0.1.0,rewrite-timestamp=true,dest={base}/image-{iteration}.tar','--metadata-file',str(base/f'build-{iteration}.json'),str(context)]
   p=subprocess.run(args,env=env,capture_output=True,text=True,timeout=300)
   if p.returncode:raise RuntimeError('Offline image build failed; no image accepted')
   info=json.loads((base/f'build-{iteration}.json').read_text());results.append(info)
   if info['containerimage.digest']!=lock['manifestDigest'] or info['containerimage.config.digest']!=lock['configDigest']:raise ValueError('Image differs from approved manifest/config digest')
  p=subprocess.run([*command,'load','-i',str(base/'image-1.tar')],env=env,capture_output=True,text=True,timeout=90)
  if p.returncode:raise RuntimeError('Local image load failed')
  report={'status':'PASS','scope':'image-reproduction-only','manifestDigest':lock['manifestDigest'],'configDigest':lock['configDigest'],'builds':results,'publicPackagesChecked':len(lock['packages'])}
 (ROOT/'docs/migration/P4_4_B_IMAGE_REBUILD.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Two offline builds match approved image digests')
if __name__=='__main__':main()
