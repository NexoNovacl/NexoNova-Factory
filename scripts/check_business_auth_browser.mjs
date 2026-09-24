import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = resolve(fileURLToPath(new URL('..', import.meta.url)));
// Reuse the already installed validation tooling read-only, never product runtime.
const require = createRequire(resolve(root, '../nexonova-website/package.json'));
const { chromium } = require('@playwright/test');
let raw=''; for await (const chunk of process.stdin) {raw+=chunk;if(raw.length>8192)throw new Error('INPUT_LIMIT');}
const input=JSON.parse(raw);raw='';
const allowed=new URL(input.origin).origin;
const browser=await chromium.launch({headless:true});
const results=[]; const failures=[];
try {
 for(const viewport of [{width:1440,height:1000},{width:390,height:844}]) {
  const context=await browser.newContext({viewport, ignoreHTTPSErrors: input.selfSignedFixture === true});
  const page=await context.newPage();let external=0;let errors=0;
  page.on('pageerror',()=>errors++);
  await page.route('**/*',async route=>{if(new URL(route.request().url()).origin!==allowed){external++;await route.abort();}else await route.continue();});
  await page.goto(input.origin+'/login');
  await page.getByLabel('Email',{exact:true}).fill('admin@example.invalid');
  await page.getByLabel('Contraseña',{exact:true}).fill(input.password);
  await page.getByLabel('Contraseña',{exact:true}).press('Tab');
  if(!await page.getByRole('button',{name:'Entrar',exact:true}).evaluate(e=>e===document.activeElement))throw new Error('KEYBOARD_LOGIN_FOCUS');
  await page.keyboard.press('Enter');
  await page.getByRole('heading',{name:'Sesión válida',exact:true}).waitFor();
  await page.goto(input.origin+'/admin-check');
  await page.getByRole('heading',{name:'Prueba administrativa',exact:true}).waitFor();
  const cookies=await context.cookies();
  if(!cookies.some(c=>c.httpOnly&&c.sameSite==='Lax'&&c.name.includes('session_token')))throw new Error('COOKIE_POLICY');
  await page.getByRole('button',{name:'Cerrar sesión'}).focus();await page.keyboard.press('Enter');
  await page.getByRole('heading',{name:'Iniciar sesión',exact:true}).waitFor();
  await page.goto(input.origin+'/auth-check');
  await page.getByRole('heading',{name:'Iniciar sesión',exact:true}).waitFor();
  await page.getByLabel('Email',{exact:true}).fill('member@example.invalid');
  await page.getByLabel('Contraseña',{exact:true}).fill(input.memberPassword);
  await page.getByRole('button',{name:'Entrar',exact:true}).click();
  await page.getByRole('heading',{name:'Sesión válida',exact:true}).waitFor();
  await page.goto(input.origin+'/admin-check');
  await page.getByRole('heading',{name:'Acceso denegado',exact:true}).waitFor();
  if(external||errors)throw new Error('BROWSER_ERRORS_OR_EXTERNAL_REQUESTS');
  results.push({viewport,keyboardLoginLogout:true,anonymousRedirect:true,externalRequests:external,javaScriptErrors:errors});
  await context.close();
 }
} catch { failures.push('BROWSER_CHECK_FAILED; details withheld');process.exitCode=1; }
finally {await browser.close();}
console.log(JSON.stringify({results,failures}));
