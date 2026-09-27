import {createRequire} from 'node:module';import {resolve} from 'node:path';
const require=createRequire(resolve(import.meta.dirname,'../../nexonova-website/package.json'));const {chromium}=require('@playwright/test');
let raw='';for await(const chunk of process.stdin)raw+=chunk;const input=JSON.parse(raw);raw='';
const browser=await chromium.launch({headless:true});const result={status:'FAIL',checks:[],responses:[],externalRequests:0};
function check(name,ok){if(!ok)throw Error(name);result.checks.push(name);}
try{
 for(const [actor,cookie] of Object.entries(input.cookies)){
  const context=await browser.newContext();await context.addCookies(cookie.split('; ').map(p=>{const i=p.indexOf('=');return {name:p.slice(0,i),value:p.slice(i+1),url:input.origin,httpOnly:true,sameSite:'Lax'};}));
  await context.route('**/*',route=>{if(new URL(route.request().url()).origin!==input.origin){result.externalRequests++;return route.abort();}return route.continue();});
  const page=await context.newPage();const pending=[];
  page.on('response',response=>{if(/^\/(api\/)?requests(\/|$)/.test(new URL(response.url()).pathname))pending.push((async()=>{const h=await response.allHeaders(),tokens=(h.vary??'').split(',').map(x=>x.trim().toLowerCase());result.responses.push({actor,status:response.status(),cacheControl:h['cache-control'],vary:tokens});check('C28-browser-final-headers',h['cache-control']==='no-store'&&tokens.includes('cookie')&&tokens.length===new Set(tokens).size);})());});
  await page.goto(input.origin+'/requests');await page.getByRole('link',{name:input.title,exact:true}).click();await page.getByRole('heading',{name:'Detalle de solicitud'}).waitFor();
  await page.getByRole('link',{name:'Volver al listado',exact:true}).click();await page.getByRole('heading',{name:'Solicitudes internas'}).waitFor();await page.goto(input.origin+'/requests/absent');await Promise.all(pending);await context.close();
 }
 const anonymous=await browser.newContext();const redirect=await anonymous.request.get(input.origin+'/requests',{maxRedirects:0});const h=redirect.headers();check('C28-anonymous-redirect',redirect.status()===307&&h.location==='/login'&&h['cache-control']==='no-store'&&(h.vary??'').toLowerCase().includes('cookie'));await anonymous.close();
 check('C28-browser-responses-observed',result.responses.length>=6);check('C36-no-external-headers-probe',result.externalRequests===0);result.status='PASS';
}catch(e){result.failedCheck=e.message.split('\n')[0].slice(0,120);process.exitCode=1;}finally{await browser.close();}
console.log(JSON.stringify(result));
