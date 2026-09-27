"""P4.5-owned launcher and lossless HTTP headers; P4.4 helpers unchanged."""
from validate_business_requests import auth,json,os
import urllib.request,urllib.error,ssl
class RequestsProbe(auth.HttpProbe):
 def __init__(self,*args,launcher='scripts/start-requests.mjs',suffix='',**kwargs):
  super().__init__(*args,**kwargs);self.launcher=launcher;self.name+=suffix
 def start(self):
  r=self.run;r.register('container',self.name);ep=r.envfile(self.env)
  try:r.record('start-requests-app',r.docker(['run','-d','--init','--pull=never','--name',self.name,'--label',auth.base.LABEL+'='+r.id,'--network',self.db['network'],'--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--memory=1g','--cpus=2','--pids-limit=256','--user',f'{os.getuid()}:{os.getgid()}','--tmpfs','/tmp:rw,nosuid,nodev,size=128m','--mount',f'type=bind,src={r.work},dst=/work,readonly','--workdir','/work','--env-file',str(ep),auth.IMAGE,'node',self.launcher]))
  finally:ep.unlink(missing_ok=True)
  inspected=json.loads(r.docker(['inspect',self.name]).stdout)[0];self.relay.target=(inspected['NetworkSettings']['Networks'][self.db['network']]['IPAddress'],3000);self.ready()
 def request(self,path,method='GET',data=None,cookie='',headers=None):
  hdr={'Origin':self.origin,'Content-Type':'application/json',**(headers or {})};hdr={k:v for k,v in hdr.items() if v is not None}
  if cookie:hdr['Cookie']=cookie
  req=urllib.request.Request(self.origin+path,data=None if data is None else json.dumps(data).encode(),method=method,headers=hdr)
  opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=str(self.run.base/'tls/cert.pem'))) if self.profile=='production' else urllib.request.HTTPSHandler())
  try:response=opener.open(req,timeout=30)
  except urllib.error.HTTPError as e:response=e
  payload=response.read().decode();cookies=response.headers.get_all('Set-Cookie') or []
  for value in cookies:
   token=value.split(';',1)[0].split('=',1)[-1]
   if len(token)>=16:self.run.values.append(token)
  # HTTP field names are case insensitive; combine repeatable fields without losing Vary.
  normalized={key:', '.join(response.headers.get_all(key)) for key in response.headers.keys() if key.lower()!='set-cookie'}
  return response.status,payload,cookies,normalized
