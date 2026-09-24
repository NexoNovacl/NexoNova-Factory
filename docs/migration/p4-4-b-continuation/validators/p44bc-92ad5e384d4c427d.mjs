// Real browser complement to P4.4-B; secrets enter stdin and never enter evidence.
import {createRequire} from 'node:module';
import {resolve} from 'node:path';
const require=createRequire(resolve(import.meta.dirname,'../../nexonova-website/package.json'));
const {chromium}=require('@playwright/test');
let raw='';for await(const chunk of process.stdin){raw+=chunk;if(raw.length>16384)throw Error('INPUT_LIMIT');}
const input=JSON.parse(raw);raw='';
const browser=await chromium.launch({headless:true});
const result={mode:input.mode,checks:[],externalRequests:0,javaScriptErrors:0};
function check(name,ok){if(!ok)throw Error(name);result.checks.push(name);}
try{
 const context=await browser.newContext({ignoreHTTPSErrors:input.secure===true});
 const page=await context.newPage();
 page.on('pageerror',()=>result.javaScriptErrors++);
 await page.route('**/*',async route=>{if(new URL(route.request().url()).origin!==input.origin){result.externalRequests++;await route.abort();}else await route.continue();});
 if(input.mode==='negative-login'){
  const messages=[];
  for(const email of ['admin@example.invalid','absent@example.invalid']){
   await page.goto(input.origin+'/login');
   await page.getByLabel('Email',{exact:true}).fill(email);
   await page.getByLabel('Contraseña',{exact:true}).fill(input.wrongPassword);
   const response=page.waitForResponse(r=>r.url().endsWith('/api/auth/sign-in/email')&&r.request().method()==='POST');
   await page.getByRole('button',{name:'Entrar',exact:true}).click();
   check('login-401-'+messages.length,(await response).status()===401);
   await page.getByRole('status').filter({hasText:'No fue posible iniciar sesión.'}).waitFor();
   messages.push(await page.getByRole('status').textContent());
   check('no-session-'+messages.length,!(await context.cookies()).some(c=>c.name.includes('session_token')));
  }
  check('same-generic-message',messages[0]===messages[1]);
 }else{
  if(input.cookie){
   const cookies=input.cookie.split('; ').map(part=>{const index=part.indexOf('=');return {name:part.slice(0,index),value:part.slice(index+1),url:input.origin,httpOnly:true,secure:input.secure===true,sameSite:'Lax'};});
   await context.addCookies(cookies);
  }
  if(input.mode==='secure-login'){
   await page.goto(input.origin+'/login');
   await page.getByLabel('Email',{exact:true}).fill('admin@example.invalid');
   await page.getByLabel('Contraseña',{exact:true}).fill(input.password);
   await page.getByRole('button',{name:'Entrar',exact:true}).click();
   await page.getByRole('heading',{name:'Sesión válida',exact:true}).waitFor();
   const cookies=(await context.cookies()).filter(c=>c.name.includes('session_token'));
   check('secure-httponly-lax-host-only-path-session',cookies.length===1&&cookies.every(c=>c.secure&&c.httpOnly&&c.sameSite==='Lax'&&c.path==='/'&&c.domain==='127.0.0.1'&&c.expires===-1));
  }else{
   await page.goto(input.origin+'/auth-check');
   await page.getByRole('heading',{name:input.allowed?'Sesión válida':'Iniciar sesión',exact:true}).waitFor();
   const api=await context.request.get(input.origin+'/api/auth-check');
   check('server-api-status',api.status()===(input.allowed?200:401));
   const session=await context.request.get(input.origin+'/api/auth/get-session');
   check('get-session-status',session.status()===200);
   check('session-presence',((await session.json())!==null)===Boolean(input.allowed));
   check('protected-page',input.allowed||new URL(page.url()).pathname==='/login');
  }
 }
 check('no-external-requests',result.externalRequests===0);check('no-javascript-errors',result.javaScriptErrors===0);
 await context.close();result.status='PASS';
}catch{result.status='FAIL';process.exitCode=1;}
finally{await browser.close();}
console.log(JSON.stringify(result));
