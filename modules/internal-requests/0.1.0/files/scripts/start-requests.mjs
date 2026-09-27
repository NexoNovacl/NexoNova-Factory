// P4.5-B launcher. The approved auth launcher and auth policy remain byte-identical.
import http from 'node:http';
import next from 'next';
import {authEnvironment} from '../build-checks/src/server/policy.js';
import {requestsResponseBoundary} from './requests-response-boundary.mjs';
try {authEnvironment();}catch{console.error('AUTH_ENV_REJECTED');process.exit(2);}
const port=Number(process.env.PORT??3000);
if(!Number.isInteger(port)||port<1||port>65535)process.exit(2);
const app=next({dev:false,hostname:'0.0.0.0',port});
await app.prepare();
const handle=app.getRequestHandler();
const server=http.createServer((request,response)=>{
  requestsResponseBoundary(request,response);
  Promise.resolve(handle(request,response)).catch(()=>{
    // Never serialize framework/DB exceptions. An already-started stream cannot be retried.
    if(response.headersSent){response.destroy();return;}
    response.statusCode=503;response.end('Service unavailable');
  });
});
server.listen(port,'0.0.0.0');
let stopping=false;
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>{
  if(stopping)return;stopping=true;
  const deadline=setTimeout(()=>{server.closeAllConnections();process.exit(1);},10000);deadline.unref();
  server.close(async()=>{await app.close();clearTimeout(deadline);process.exit(0);});
});
