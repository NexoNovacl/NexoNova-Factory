"""Bounded Node validation of hash-approved products in disposable local Docker copies.

Preparation is the sole network-enabled action; dependency lifecycle scripts are disabled.
No generic command arguments, remote Docker, credentials, ports or Python adapter changes.
"""
from pathlib import Path
import json,os,re,selectors,signal,subprocess,tempfile,time,uuid
from .generation import inspect_files,file_records,digest,json_bytes,read_json,safe_root,byte_hash
from .storage import StorageError,safe_path
from .executor import redact,ToolExecutor

COMMANDS={
 "version": ["node","--version"],
 "install": ["npm","ci","--ignore-scripts","--no-audit","--no-fund","--registry=https://registry.npmjs.org"],
 "typecheck": ["node","node_modules/typescript/bin/tsc","--noEmit","--incremental","false"],
 "test-content": ["node","--test","tests/content.test.mjs"],
 "build": ["node","node_modules/next/dist/bin/next","build"],
 "probe": ["node","-e", "const fs=require('fs'); let rootWritable=false;try{fs.writeFileSync('/p35-probe','x');rootWritable=true}catch{};console.log(JSON.stringify({uid:process.getuid(),network:require('os').networkInterfaces(),rootWritable,privateEnv:process.env.P35_PRIVATE_SENTINEL??null,cap:fs.readFileSync('/proc/self/status','utf8').split('\\n').filter(x=>x.startsWith('CapEff:')),memory:fs.readFileSync('/sys/fs/cgroup/memory.max','utf8').trim(),pids:fs.readFileSync('/sys/fs/cgroup/pids.max','utf8').trim(),cpu:fs.readFileSync('/sys/fs/cgroup/cpu.max','utf8').trim()}))"],
}

def validate_policy(policy):
 if set(policy)!={'format','image','approved_content_hashes','authorization_basis'} or policy['format']!='nexonova.web-policy.v1':raise StorageError('Invalid web policy')
 if not re.fullmatch(r'node@sha256:[a-f0-9]{64}',policy['image']):raise StorageError('Pinned official Node image required')
 if not policy['authorization_basis']:raise StorageError('Operator scope required')

def command(action,work,name,image):
 if action not in COMMANDS:raise StorageError('Web action is not allowlisted')
 safe_root(work)
 if ',' in str(work):raise StorageError('Ambiguous Docker mount')
 return ['docker','--host','unix:///var/run/docker.sock','run','--rm','--pull=never','--name',name,
  '--network='+('bridge' if action=='install' else 'none'),'--read-only','--cap-drop=ALL',
  '--security-opt=no-new-privileges','--pids-limit=256','--memory=2g','--cpus=2',
  '--ulimit','fsize=268435456:268435456','--user',f'{os.getuid()}:{os.getgid()}',
  '--workdir','/work','--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=128m',
  '--mount',f'type=bind,source={work},target=/work',
  '--env','HOME=/tmp','--env','NEXT_TELEMETRY_DISABLED=1','--env','CI=1',
  '--env','npm_config_userconfig=/dev/null','--env','npm_config_globalconfig=/tmp/no-global-npmrc',
  '--env','npm_config_cache=/work/.npm-cache','--env','npm_config_ignore_scripts=true',
  '--entrypoint',COMMANDS[action][0],image,*COMMANDS[action][1:]]

def execute(action,work,image,client,*,timeout=300,max_output=1_048_576):
 name='nexonova-web-'+uuid.uuid4().hex;args=command(action,work,name,image)
 env={'PATH':'/usr/bin:/bin','HOME':str(client),'DOCKER_CONFIG':str(client)}
 result={'action':action,'container':name,'command':args,'status':'error','exit_code':None,'output':'','cleanup':False}
 data=bytearray();interrupted=False;process=None
 try:
  process=subprocess.Popen(args,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
  deadline=time.monotonic()+timeout
  with selectors.DefaultSelector() as selector:
   selector.register(process.stdout,selectors.EVENT_READ)
   while selector.get_map():
    if time.monotonic()>=deadline:result['status']='timeout';break
    for key,_ in selector.select(.1):
     chunk=os.read(key.fd,8192)
     if not chunk:selector.unregister(key.fileobj)
     else:data.extend(chunk)
    if len(data)>max_output:result['status']='output-limit';break
   else:
    process.wait(timeout=max(.01,deadline-time.monotonic()));result['status']='complete' if process.returncode==0 else 'error'
 except KeyboardInterrupt:result['status']='interrupted';interrupted=True
 except subprocess.TimeoutExpired:result['status']='timeout'
 except OSError:result['status']='unavailable'
 finally:
  if process:
   if process.poll() is None:os.killpg(process.pid,signal.SIGKILL)
   process.wait();result['exit_code']=process.returncode;process.stdout.close()
  try:
   subprocess.run(['docker','--host','unix:///var/run/docker.sock','rm','-f',name],env=env,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10)
   result['cleanup']=ToolExecutor._confirm_removed('docker',name,env)
  except (OSError,subprocess.TimeoutExpired):pass
  result['output']=redact(bytes(data[:max_output]).decode('utf8',errors='replace'))
  if not result['cleanup'] and result['status']=='complete':result['status']='cleanup-unconfirmed'
 return result,interrupted

def validate_product(source,policy,report_root,manifest=None):
 validate_policy(policy)
 if manifest is not None:
  from .product_integrity import validate_product_integrity
  validate_product_integrity(source,manifest,[])
  source_snapshot={e['path']:(source/e['path']).read_bytes() for e in manifest['files']}
  original=dict(source_snapshot)
  # Next's generated declaration is not a client customization; clone the pinned
  # bootstrap form for clean typecheck, without rewriting the materialized source.
  for entry in manifest['files']:
   if entry['path']=='next-env.d.ts' and entry['sha256']!=byte_hash(original['next-env.d.ts']):
    bootstrap=b'/// <reference types="next" />\n/// <reference types="next/image-types/global" />\n'
    if byte_hash(bootstrap)!=entry['sha256']:raise StorageError('Unknown Next declaration baseline')
    original['next-env.d.ts']=bootstrap
 else:
  original=inspect_files(source);source_snapshot=original
 stable=digest(file_records(original))
 if stable not in policy['approved_content_hashes']:raise StorageError('Web execution lacks exact content authorization')
 # Even pinned templates must not introduce remote/git/file dependency resolution.
 lock=json.loads(original['package-lock.json'])
 for package in lock['packages'].values():
  if 'resolved' in package and (not package['resolved'].startswith('https://registry.npmjs.org/') or not package.get('integrity','').startswith('sha512-')):
   raise StorageError('Dependency source/integrity not approved')
 root=safe_root(report_root)
 if not root.is_dir():raise StorageError('Explicit existing validation root required')
 report={'format':'nexonova.web-validation.v1','inputHash':stable,'image':policy['image'],'results':[],'status':'running'}
 with tempfile.TemporaryDirectory(prefix='web-copy-',dir=root) as directory:
  job=Path(directory);work=job/'product';work.mkdir();client=job/'docker-client';client.mkdir()
  for rel,data in original.items():
   p=safe_path(work,rel);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  for action in ('version','probe','install','typecheck','test-content','build'):
   result,interrupted=execute(action,work,policy['image'],client)
   if manifest is not None:
    try:
     from .product_integrity import validate_product_integrity
     result['workIntegrity']=validate_product_integrity(work,manifest,[])['status']
    except (OSError,ValueError):
     result['workIntegrity']='changed';result['status']='unapproved-source-change'
   report['results'].append(result)
   report['status']='running' if result['status']=='complete' else result['status']
   (root/'web-result.json').write_bytes(json_bytes(report))
   if interrupted:
    report['status']='interrupted';(root/'web-result.json').write_bytes(json_bytes(report));raise KeyboardInterrupt
   if result['status']!='complete':break
  else:report['status']='complete'
  report['sourceUnchanged']=({p:(source/p).read_bytes() for p in source_snapshot}==source_snapshot) if manifest is not None else inspect_files(source)==original
  if not report['sourceUnchanged']:report['status']='source-changed'
 report['temporaryCopyRemoved']=not job.exists()
 (root/'web-result.json').write_bytes(json_bytes(report))
 return report
