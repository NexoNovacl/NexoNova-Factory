"""D02 real HTTP acceptance, including comparison to unmodified Next launcher."""
from validate_business_requests import *
from business_requests_probe import RequestsProbe

def d02(m,a,b):
 r=m.r;app=m.app
 control=RequestsProbe(r,m.db,namespace='synthetic-requests',launcher='scripts/start.mjs',suffix='-control');control.env['BETTER_AUTH_SECRET']=app.env['BETTER_AUTH_SECRET'];control.start()
 observations=[]
 def fields(result):return {k.lower():v for k,v in result[3].items()}
 def tokens(result):return [x.strip().lower() for x in fields(result).get('vary','').split(',') if x.strip()]
 for actor in ['a','admin']:
  for path in ['/requests','/requests/'+a['id'],'/requests/'+str(__import__('uuid').uuid4()),'/requests?limit=invalid']:
   for isrsc in [False,True]:
    headers={'RSC':'1'} if isrsc else {}
    actual=app.request(path,cookie=m.cookies[actor],headers=headers);baseline=control.request(path,cookie=m.cookies[actor],headers=headers)
    actualtokens=tokens(actual);basetokens=tokens(baseline)
    m.check('C28-D02-page-status',actual[0]==baseline[0])
    m.check('C28-D02-vary-union',set(actualtokens)==set(basetokens)|{'cookie'} and len(actualtokens)==len(set(actualtokens)))
    m.check('C28-D02-no-store',fields(actual).get('cache-control')=='no-store')
    observations.append({'actor':actor,'kind':'rsc' if isrsc else 'html','status':actual[0],'varyBefore':basetokens,'varyAfter':actualtokens,'cacheControl':fields(actual).get('cache-control')})
 # Unrelated routes retain baseline status/body semantics and headers; tokens not globally changed.
 for path in ['/login','/api/auth-check','/api/admin-check','/api/auth/get-session']:
  actual=app.request(path,cookie=m.cookies['a']);baseline=control.request(path,cookie=m.cookies['a']);m.check('C28-D02-nonmodule-status',actual[0]==baseline[0]);m.check('C28-D02-nonmodule-headers',tokens(actual)==tokens(baseline) and fields(actual).get('cache-control')==fields(baseline).get('cache-control'))
 before=m.snap()
 for actor in ['a','admin']:
  for path,status in [('',200),('/'+a['id'],200),('/bad',404),('?limit=0',400)]:
   result=app.request('/api/requests'+path,cookie=m.cookies[actor]);m.check('C28-D02-api-status',result[0]==status);t=tokens(result);m.check('C28-D02-api-headers','cookie' in t and len(t)==len(set(t)) and fields(result).get('cache-control')=='no-store')
  for origin in [None,'null','https://evil.invalid']:
   for path,method,body in [('', 'POST',{'title':'No','description':''}),('/'+a['id'],'PATCH',{'action':'close','expectedVersion':a['version']})]:m.api('C28',actor,path,method,body,403,{'Origin':origin,'Forwarded':'host=evil.invalid;proto=https','X-Forwarded-Host':'evil.invalid','X-Forwarded-Proto':'https'})
  for path in ['', '/'+a['id']]:
   for method in ['PUT','DELETE','OPTIONS']:m.api('C28',actor,path,method,{},405)
  m.api('C28',actor,status=403,headers={'Sec-Fetch-Site':'cross-site'})
 m.check('C28-D02-no-mutating-errors',m.snap()==before)
 m.api('C28','anonymous',status=401)
 # Successful writes exercise boundary too, without leaving fixtures in module lists.
 item=m.create(case='C28');item=m.patch(item,'edit',case='C28',title='D02 successful edit',description='')['item'];m.patch(item,'archive',case='C28',status=204)
 m.report['D02']={'status':'PASS_HTTP','scope':'HTML/RSC, member/admin, success/errors, exact Next Vary union, unrelated route comparison; browser navigation follows in C34','observations':observations}
 r.remove('container',control.name);control.relay.close_run();r.relays.remove(control.relay)
 # This case still requires browser check from approved C28 before final PASS.
 write(OUT/(r.id+'.progress.json'),m.report)
