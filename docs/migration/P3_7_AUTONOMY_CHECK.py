"""Operator-only closure experiment; no new runtime/executor capability is registered."""
from pathlib import Path
import json,sys,tempfile,subprocess,os,uuid
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from factory.generation import read_json,json_bytes,byte_hash
from factory.product_integrity import validate_product_integrity,NEXT_ENV
from factory.web_tools import execute,command
from factory.executor import ToolExecutor

RUNTIME=r'''const fs=require('fs'),cp=require('child_process');
(async()=>{const cfg=JSON.parse(fs.readFileSync('/work/src/content/site.json'));const forbidden=['/work/.nexonova','/home/germanleiks/NexoNova/nexonova-factory','/home/germanleiks/NexoNova/nexonova-prototype','/home/germanleiks/NexoNova/.nexonova-staging'];
 const absence=Object.fromEntries(forbidden.map(p=>[p,!fs.existsSync(p)]));if(Object.values(absence).some(x=>!x))throw Error('Private path exposed');
 const python=Object.fromEntries(['python','python3'].map(x=>[x,cp.spawnSync(x,['--version']).error?.code==='ENOENT']));if(Object.values(python).some(x=>!x))throw Error('Python unexpectedly present');
 const server=cp.spawn(process.execPath,['node_modules/next/dist/bin/next','start','--hostname','127.0.0.1','--port','3187'],{stdio:'ignore'});
 try{let response;for(let i=0;i<100;i++){try{response=await fetch('http://127.0.0.1:3187/');break}catch{await new Promise(r=>setTimeout(r,100));}}
 if(!response?.ok)throw Error('Server did not start');const html=await response.text();if(!html.includes(cfg.brand.name)||!html.includes(cfg.hero.title))throw Error('Wrong product');
 const links=[...new Set([...html.matchAll(/(?:src|href)="([^"#]+)"/g)].map(x=>x[1]).filter(x=>x.startsWith('/')))];let checked=[];
 for(const path of links){const r=await fetch(new URL(path,'http://127.0.0.1:3187'));if(!r.ok)throw Error('Broken asset');checked.push({path,status:r.status});}
 console.log(JSON.stringify({status:'complete',brand:cfg.brand.name,privatePathsAbsent:absence,pythonAbsent:python,metadataAbsent:!fs.existsSync('/work/.nexonova'),httpStatus:response.status,localResources:checked}));
 }finally{server.kill('SIGTERM');await new Promise(r=>server.once('exit',r));}
})().catch(e=>{console.error(e.message);process.exitCode=1});'''

def main():
 docs=ROOT/'docs/migration';image=read_json(ROOT/'config/web-tools.json')['image'];reports=[]
 for name,manifest_file in [('nexonova-website','P3_5_GENERATION_MANIFEST.json'),('synthetic-website','P3_6_GENERATION_MANIFEST.json')]:
  product=ROOT.parent/name;manifest=read_json(docs/manifest_file);before=validate_product_integrity(product,manifest,[ROOT,ROOT.parent/'nexonova-prototype']);snapshot={x['path']:(product/x['path']).read_bytes() for x in manifest['files']}
  result={'project':name,'initialIntegrity':before,'image':image,'actions':[]};reports.append(result)
  with tempfile.TemporaryDirectory(prefix='p37-autonomy-',dir='/var/tmp') as tmp:
   base=Path(tmp);work=base/'product';work.mkdir();client=base/'client';client.mkdir()
   for rel,data in snapshot.items():
    if rel.startswith('.nexonova/'):continue
    if rel=='next-env.d.ts':data=b'/// <reference types="next" />\n/// <reference types="next/image-types/global" />\n'
    p=work/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
   for action in ('version','install','typecheck','test-content','build'):
    step,interrupted=execute(action,work,image,client);result['actions'].append(step);(docs/'P3_7_AUTONOMY.json').write_bytes(json_bytes(reports));print(name,action,step['status'],flush=True)
    if interrupted or step['status']!='complete':raise RuntimeError('Action failed; see report')
   # An explicit one-shot operator experiment, not a customer-supplied tool command.
   cname='nexonova-p37-'+uuid.uuid4().hex;args=command('version',work,cname,image);i=args.index('--entrypoint');args=args[:i]+['--entrypoint','node',image,'-e',RUNTIME]
   env={'PATH':'/usr/bin:/bin','HOME':str(client),'DOCKER_CONFIG':str(client)}
   try:
    p=subprocess.run(args,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
    runtime={'command':args,'exit_code':p.returncode,'output':p.stdout}
   finally:
    subprocess.run(['docker','--host','unix:///var/run/docker.sock','rm','-f',cname],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10)
    cleaned=ToolExecutor._confirm_removed('docker',cname,env)
   runtime['cleanup']=cleaned;result['runtime']=runtime
   if p.returncode or not cleaned:raise RuntimeError('Runtime experiment failed')
   for rel,data in snapshot.items():
    if rel.startswith('.nexonova/'):continue
    actual=(work/rel).read_bytes()
    if rel=='next-env.d.ts':assert actual==NEXT_ENV
    else:assert actual==data,'Source modified by validation'
   assert not (work/'.nexonova').exists()
   result['copySourceUnchangedExceptKnownNextDeclaration']=True
  result['temporaryCopyRemoved']=not base.exists();result['originalSourceUnchanged']=all((product/k).read_bytes()==v for k,v in snapshot.items());result['status']='complete';(docs/'P3_7_AUTONOMY.json').write_bytes(json_bytes(reports))
 return 0
if __name__=='__main__':raise SystemExit(main())
