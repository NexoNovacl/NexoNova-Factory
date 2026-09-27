// Real browser: credentials enter stdin only; never serialize cookies, HTML or password.
import {createRequire} from 'node:module';
import {resolve} from 'node:path';
const require=createRequire(resolve(import.meta.dirname,'../../nexonova-website/package.json'));
const {chromium}=require('@playwright/test');
let raw='';for await(const chunk of process.stdin)raw+=chunk;
const input=JSON.parse(raw);raw='';
const result={checks:[],externalRequests:0,javaScriptErrors:0,status:'FAIL'};
const browser=await chromium.launch({headless:true});
function check(name,value){if(!value)throw Error(name);result.checks.push(name);}
async function context(cookie,viewport={width:1280,height:800}){
 const c=await browser.newContext({viewport,ignoreHTTPSErrors:true});
 await c.route('**/*',route=>{if(new URL(route.request().url()).origin!==input.origin){result.externalRequests++;return route.abort();}return route.continue();});
 c.on('page',p=>p.on('pageerror',()=>result.javaScriptErrors++));
 if(cookie)await c.addCookies(cookie.split('; ').map(part=>{const i=part.indexOf('=');return {name:part.slice(0,i),value:part.slice(i+1),url:input.origin,httpOnly:true,secure:input.secure??false,sameSite:'Lax'};}));
 return c;
}
try{
 if(input.mode==='negative'){
  for(const [name,cookie] of Object.entries(input.cookies)){
   const c=await context(cookie);const p=await c.newPage();
   for(const path of ['/requests','/requests/'+input.id]){await p.goto(input.origin+path);await p.getByRole('heading',{name:'Iniciar sesión',exact:true}).waitFor();check('C20-'+name+'-page',new URL(p.url()).pathname==='/login');}
   check('C20-'+name+'-api',(await c.request.get(input.origin+'/api/requests')).status()===401);await c.close();
  }
 }else{
  const c=await context(input.cookies.a),page=await c.newPage();
  await page.goto(input.origin+'/requests');await page.getByRole('heading',{name:'Solicitudes internas'}).waitFor();
  await page.getByLabel('Título',{exact:true}).focus();await page.keyboard.type('Browser keyboard request');await page.keyboard.press('Tab');await page.keyboard.type('Browser description');await page.keyboard.press('Tab');await page.keyboard.press('Enter');
  await page.getByRole('heading',{name:'Detalle de solicitud'}).waitFor();const path=new URL(page.url()).pathname;check('C34-keyboard-create',/^\/requests\/[0-9a-f-]+$/.test(path));
  const tab=await c.newPage();await tab.goto(input.origin+path);await tab.getByLabel('Título',{exact:true}).fill('Stale draft preserved');
  await page.getByLabel('Título',{exact:true}).fill('<script>window.p45xss=1</script>');await page.getByRole('button',{name:'Guardar',exact:true}).click();await page.getByRole('status').filter({hasText:'Cambios guardados.'}).waitFor();
  await tab.getByRole('button',{name:'Guardar',exact:true}).click();await tab.getByRole('status').filter({hasText:'Conflicto'}).waitFor();check('C34-conflict-draft',await tab.getByLabel('Título',{exact:true}).inputValue()==='Stale draft preserved');
  for(const button of ['Cerrar','Reabrir']){await page.getByRole('button',{name:button,exact:true}).click();await page.getByTestId('status').filter({hasText:button==='Cerrar'?'closed':'open'}).waitFor();}
  await page.reload();check('C27-xss-text',await page.getByLabel('Título',{exact:true}).inputValue()==='<script>window.p45xss=1</script>'&&await page.evaluate(()=>window.p45xss===undefined));
  await page.goto(input.origin+'/requests');check('C27-xss-list',await page.getByRole('link',{name:'<script>window.p45xss=1</script>',exact:true}).count()===1&&await page.evaluate(()=>window.p45xss===undefined));
  const b=await context(input.cookies.b),bp=await b.newPage();await bp.goto(input.origin+path);check('C34-horizontal-page',!(await bp.getByRole('button',{name:'Guardar',exact:true}).count()));check('C34-horizontal-api',(await b.request.get(input.origin+'/api'+path)).status()===404);
  const admin=await context(input.cookies.admin,{width:390,height:844}),ap=await admin.newPage();await ap.goto(input.origin+path);await ap.getByRole('heading',{name:'Detalle de solicitud'}).waitFor();check('C09-admin-browser',await ap.getByLabel('Título',{exact:true}).inputValue()==='<script>window.p45xss=1</script>');
  await ap.getByLabel('Título',{exact:true}).fill('Admin browser edit');await ap.getByRole('button',{name:'Guardar',exact:true}).click();await ap.getByRole('status').filter({hasText:'Cambios guardados.'}).waitFor();
  check('C34-mobile-bounded',await ap.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  await ap.getByRole('button',{name:'Archivar',exact:true}).click();await ap.getByRole('group',{name:'Confirmar archivado'}).waitFor();await ap.getByRole('button',{name:'Confirmar archivado',exact:true}).click();await ap.getByRole('heading',{name:'Solicitudes internas'}).waitFor();
  for(const [name,ctx] of [['owner',c],['nonowner',b],['admin',admin]]){check('C14-archived-'+name,(await ctx.request.get(input.origin+'/api'+path)).status()===404);const p=await ctx.newPage();await p.goto(input.origin+path);check('C14-archived-page-'+name,!(await p.getByRole('button',{name:'Guardar',exact:true}).count()));}
  // Real browser requests with hostile Origin and API bypass.
  const cross=await c.request.post(input.origin+'/api/requests',{headers:{Origin:'https://evil.invalid'},data:{title:'No',description:''}});check('C28-browser-origin',cross.status()===403);
  await c.close();await b.close();await admin.close();
 }
 check('C36-no-external',result.externalRequests===0);check('C34-no-js-errors',result.javaScriptErrors===0);result.status='PASS';
}catch(e){result.failedCheck=e instanceof Error?e.message.split('\n')[0].slice(0,160):'browser error';process.exitCode=1;}
finally{await browser.close();}
console.log(JSON.stringify(result));
