"""Explicit missing actor/negative variants, with real HTTP/DB unless labeled pure."""
from validate_business_requests import *
import uuid,base64

def gaps(m,a,b):
 r=m.r;db=m.db
 # Admin invalid transitions and full version-negative matrix, without changing existing fixtures.
 item=m.create('admin',case='C11');before=m.snap();m.patch(item,'reopen','admin',409,'C11');m.check('C11-admin-open-unchanged',m.snap()==before)
 item=m.patch(item,'close','admin',case='C11')['item'];before=m.snap();m.patch(item,'close','admin',409,'C11');m.check('C11-admin-closed-unchanged',m.snap()==before);item=m.patch(item,'reopen','admin',case='C11')['item'];m.check('C11-admin-reopened',item['status']=='open')
 for action in ['edit','close','reopen','archive']:
  extra={'title':'No','description':''} if action=='edit' else {}
  before=m.snap()
  for value in [None,0,-1,1.2,'1',2147483648]:
   data={'action':action,**extra}
   if value is not None:data['expectedVersion']=value
   m.api('C13','admin','/'+item['id'],'PATCH',data,400)
  m.patch(item,action,'admin',409,'C13',version=1,**extra);m.check('C13-admin-negative-unchanged',before==m.snap())
 r.record('C13-admin-max-fixture',r.sql(db,'UPDATE app."InternalRequest" SET version=2147483647 WHERE id=\''+item['id']+"'"));item['version']=2147483647;before=m.snap()
 for action in ['edit','close','reopen','archive']:m.patch(item,action,'admin',409,'C13',**({'title':'No','description':''} if action=='edit' else {}))
 m.check('C13-admin-max-unchanged',before==m.snap());m.done('C11','C13')
 other=m.create('b',case='C19');other=m.patch(other,'close','b',case='C19')['item'];before=m.snap()
 for action in ['close','reopen','archive']:
  for version in [1,other['version']]:m.patch(other,action,'a',404,'C19',version=version)
 m.check('C19-closed-foreign-unchanged',before==m.snap());m.done('C19')
 # Exact static error headers/body; no existence/owner metadata, versions do not change 404.
 absent=str(uuid.uuid4())
 def signature(result):
  headers={k.lower():v for k,v in result[3].items()};return result[0],result[1],{k:headers.get(k) for k in ['cache-control','vary','content-type','content-length']},bool(result[2])
 for actor,ids in [('a',[absent,other['id'],b['id'],'invalid','%2F','%00']),('admin',[absent,b['id'],'invalid','%2F','%00'])]:
  for action in [None,'edit','close','reopen','archive']:
   results=[]
   for id in ids:
    body=None if action is None else {'action':action,'expectedVersion':1,**({'title':'No','description':''} if action=='edit' else {})}
    res=m.app.request('/api/requests/'+id,'GET' if action is None else 'PATCH',body,m.cookies[actor]);results.append(signature(res))
   m.check('C22-identical-errors-'+actor+'-'+str(action),all(x==results[0] for x in results) and results[0][0]==404 and results[0][1]=='{"error":"RESOURCE_NOT_FOUND"}' and results[0][3] is False)
 m.done('C22')
 forged=base64.urlsafe_b64encode(json.dumps({'createdAt':'2020-01-01T00:00:00.000Z','id':other['id']}).encode()).decode().rstrip('=')
 rows=m.api('C17','a','?cursor='+forged,headers={'X-Role':'admin','X-User-Id':m.ids['b'],'X-Owner-Id':m.ids['b']})['items'];m.check('C17-header-cursor-own-scope',all(row['ownerId']==m.ids['a'] for row in rows));m.done('C17')
 result=m.api('C15','a','/'+a['id']);m.check('C15-exact-dto',set(result)=={'item'} and set(result['item'])=={'id','title','description','status','ownerId','createdAt','updatedAt','archivedAt','version'})
 html=m.app.request('/requests/'+a['id'],cookie=m.cookies['a']);m.check('C15-html-own-title',html[0]==200 and a['title'] in html[1] and 'session_token' not in html[1] and 'providerId' not in html[1]);m.done('C15')
 # Unit test at the actual service entry boundary: no mock DB or forged integrated auth claim.
 js="import * as s from './build-checks/src/modules/internal-requests/service.js';const actor={id:'fixture',role:'unknown'};for(const f of [()=>s.createRequest(actor,{}),()=>s.listRequests(actor,new URLSearchParams()),()=>s.getRequest(actor,'id'),()=>s.changeRequest(actor,'id',{})]){let denied=false;try{f()}catch(e){denied=e.status===401&&e.code==='UNAUTHORIZED'}if(!denied)process.exit(1)}console.log('PURE_SERVICE_DENY_DEFAULT')"
 r.node('C21-pure-service-entry-deny',['node','--input-type=module','-e',js]);m.done('C21')
