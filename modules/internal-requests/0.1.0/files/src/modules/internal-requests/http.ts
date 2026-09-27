import {identity} from '../../server/auth.js';
import {authEnvironment} from '../../server/policy.js';
import {RequestError} from './validation.js';
import {createRequest,listRequests,getRequest,changeRequest} from './service.js';
function response(status: number,body: unknown,extra: Record<string,string>={}) {
  return new Response(body===null?null:JSON.stringify(body),{status,headers:{'Cache-Control':'no-store','Vary':'Cookie',...(body===null?{}:{'Content-Type':'application/json'}),...extra}});
}
async function input(request: Request) {
  if(!/^application\/json(?:\s*;\s*charset=utf-8)?$/i.test(request.headers.get('content-type')??'')) throw new RequestError(415,'UNSUPPORTED_MEDIA_TYPE');
  const reader=request.body?.getReader();let length=0;const chunks: Uint8Array[]=[];
  if(reader) try {while(true){const part=await reader.read();if(part.done)break;length+=part.value.length;if(length>16384){await reader.cancel();throw new RequestError(413,'BODY_TOO_LARGE');}chunks.push(part.value);}}finally{reader.releaseLock();}
  try {return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(Buffer.concat(chunks)));}catch{throw new RequestError(400,'INPUT_REJECTED');}
}
export async function handle(request: Request,id?: string) {
  const allowed=id===undefined?['GET','POST']:['GET','PATCH'];
  if(!allowed.includes(request.method)) return response(405,{error:'METHOD_NOT_ALLOWED'},{Allow:allowed.join(', ')});
  try {
    const actor=await identity(request.headers);
    if(!actor) throw new RequestError(401,'UNAUTHORIZED');
    if(request.headers.get('sec-fetch-site')==='cross-site') throw new RequestError(403,'ORIGIN_REJECTED');
    if(request.method!=='GET' && request.headers.get('origin')!==authEnvironment().origin) throw new RequestError(403,'ORIGIN_REJECTED');
    const params=new URL(request.url).searchParams;
    if(request.method==='GET' && id===undefined) return response(200,await listRequests(actor,params));
    if([...params].length) throw new RequestError(400,'INPUT_REJECTED');
    if(request.method==='GET') return response(200,{item:await getRequest(actor,id!)});
    const body=await input(request);
    if(request.method==='POST') {const item=await createRequest(actor,body);return response(201,{item},{Location:`/api/requests/${item.id}`});}
    const item=await changeRequest(actor,id!,body);
    return item===null?response(204,null):response(200,{item});
  } catch(e) {
    return e instanceof RequestError?response(e.status,{error:e.code}):response(503,{error:'SERVICE_UNAVAILABLE'});
  }
}
