/** Future browser harness. Import/--describe never loads a browser or contacts HTTP.
 * An external session supplies the live guard; this module cannot mint authority.
 * No credentials, cookies, HTML or uncontrolled errors are included in returned evidence.
 */
import { pathToFileURL } from 'node:url';

export const executionAuthority = 'none';
const requiredTokens = ['rsc', 'next-router-state-tree', 'next-router-prefetch'];
function requireThat(value, message) { if (!value) throw new Error(message); }

export function checkHeaders(headers, { page = false, nextTokens = requiredTokens } = {}) {
  const normalized = Object.fromEntries(Object.entries(headers).map(([k,v]) => [k.toLowerCase(),v]));
  requireThat(typeof normalized['cache-control'] === 'string' &&
    normalized['cache-control'].trim().toLowerCase() === 'no-store', 'no-store missing');
  const vary = (normalized.vary ?? '').split(',').map(x=>x.trim().toLowerCase()).filter(Boolean);
  requireThat(vary.includes('cookie') && new Set(vary).size === vary.length, 'Vary Cookie missing/duplicated');
  if (page) for (const token of nextTokens) requireThat(vary.includes(token.toLowerCase()), 'Next Vary token lost');
  return { noStore: true, cookieVary: true, preservedTokens: page ? [...nextTokens] : [] };
}

export function validateConfig(config) {
  requireThat(config && config.executionAuthority === 'none', 'config is not executive authority');
  const origin = new URL(config.origin);
  requireThat(origin.protocol === 'https:' && ['127.0.0.1', 'localhost', '[::1]'].includes(origin.hostname) &&
    origin.pathname === '/' && !origin.search && !origin.hash && !origin.username && !origin.password, 'local HTTPS origin required');
  requireThat(config.productId && config.binding && ['workOrderHash','generationManifestHash','adaptationHash']
    .every(k=>/^sha256:[a-f0-9]{64}$/.test(config.binding[k])), 'three executive hash bindings required');
  requireThat(config.nextVaryTokens?.length && config.nextVaryTokens.every(x=>typeof x==='string'), 'exact Next token baseline required');
}

async function revalidate(guard, config) {
  requireThat(typeof guard === 'function', 'live external guard required');
  const value = await guard('http-browser');
  requireThat(value?.action === 'http-browser' && value?.reservationActive === true &&
    ['workOrderHash','generationManifestHash','adaptationHash'].every(k=>value[k]===config.binding[k]) && value.origin===config.origin &&
    JSON.stringify(value.nextVaryTokens)===JSON.stringify(config.nextVaryTokens), 'external reservation/binding invalid');
}

export async function runBrowserValidation({ config, loadBrowser, guard, credentials }) {
  validateConfig(config);
  requireThat(typeof loadBrowser === 'function', 'pinned installed browser loader required');
  await revalidate(guard,config);
  // Loader is supplied by the future authorized harness, never npm install/download here.
  const browser = await loadBrowser();
  const results = [];
  const contexts = [];
  try {
    for (const role of ['member','admin']) {
      requireThat(credentials?.[role]?.email && credentials?.[role]?.password, 'private fixture credentials missing');
      await revalidate(guard,config);
      const context = await browser.newContext({ ignoreHTTPSErrors: true, baseURL: config.origin });
      contexts.push(context);
      const page = await context.newPage();
      await revalidate(guard,config);
      const login = await context.request.post('/api/auth/sign-in/email', { data: credentials[role] });
      requireThat(login.status() === 200, 'fixture login failed');
      await revalidate(guard,config);
      const response = await page.goto('/requests');
      requireThat(response?.status() === 200, 'authenticated page failed');
      const pageHeaders = checkHeaders(await response.allHeaders(), {page:true,nextTokens:config.nextVaryTokens});
      await revalidate(guard,config);
      await page.getByLabel('Título',{exact:true}).fill('P46 synthetic '+role);
      await page.getByLabel('Descripción',{exact:true}).fill('Disposable fixture for authorized validation');
      await page.getByRole('button',{name:'Crear',exact:true}).click();
      await page.getByRole('heading',{name:'Detalle de solicitud',exact:true}).waitFor();
      await revalidate(guard,config);
      await page.getByRole('link',{name:'Volver al listado',exact:true}).click();
      await page.getByRole('heading',{name:'Solicitudes internas',exact:true}).waitFor();
      await revalidate(guard,config);
      await page.getByRole('link',{name:'P46 synthetic '+role,exact:true}).click();
      await page.getByRole('heading',{name:'Detalle de solicitud',exact:true}).waitFor();
      await revalidate(guard,config);
      await page.getByRole('button',{name:'Cerrar',exact:true}).click();
      await page.getByRole('button',{name:'Reabrir',exact:true}).waitFor();
      await revalidate(guard,config);
      await page.getByRole('button',{name:'Reabrir',exact:true}).click();
      await page.getByRole('button',{name:'Cerrar',exact:true}).waitFor();
      await revalidate(guard,config);
      await page.getByRole('button',{name:'Archivar',exact:true}).click();
      await page.getByRole('button',{name:'Confirmar archivado',exact:true}).click();
      await page.getByRole('heading',{name:'Solicitudes internas',exact:true}).waitFor();

      await revalidate(guard,config);
      const listed = await context.request.get('/api/requests');
      requireThat(listed.status() === 200, 'authenticated list failed');
      const apiHeaders = checkHeaders(await listed.allHeaders());
      const cookies = await context.cookies(config.origin);
      requireThat(cookies.length > 0 && cookies.filter(c=>/session/i.test(c.name)).some(c=>c.secure && c.httpOnly), 'secure session cookie absent');
      await revalidate(guard,config);
      const reserved = await context.request.get('/sign-in', {maxRedirects:0});
      requireThat(reserved.status() === 404, 'historical reservation materialized/redirected');
      await revalidate(guard,config);
      const absent = await context.request.get('/api/requests/00000000-0000-4000-8000-000000000000');
      requireThat(absent.status() === 404, 'resource uniform 404 failed');
      checkHeaders(await absent.allHeaders());
      await revalidate(guard,config);
      const rsc = await context.request.get('/requests',{headers:{RSC:'1','Next-Router-Prefetch':'1'}});
      requireThat(rsc.status() === 200, 'RSC request failed');
      checkHeaders(await rsc.allHeaders(),{page:true,nextTokens:config.nextVaryTokens});
      await revalidate(guard,config);
      const logout = await context.request.post('/api/auth/sign-out',{data:{}});
      requireThat(logout.status() === 200, 'logout failed');
      await revalidate(guard,config);
      const revoked = await context.request.get('/api/requests');
      requireThat(revoked.status() === 401, 'revoked session accepted');
      checkHeaders(await revoked.allHeaders());
      results.push({role, authenticatedPage:true, authenticatedApi:true, pageHeaders, apiHeaders,
        uiCreateCloseReopenArchive:true, clientNavigation:true, secureCookie:true, historicalSignIn404:true, resource404:true, rsc:true, logout:true});
    }
    await revalidate(guard,config);
    const anonymous = await browser.newContext({ignoreHTTPSErrors:true,baseURL:config.origin});
    contexts.push(anonymous);
    const denied = await anonymous.request.get('/api/requests');
    requireThat(denied.status() === 401, 'anonymous API accepted');
    checkHeaders(await denied.allHeaders());
    return {productId:config.productId, binding:config.binding, checks:results,
      anonymousDenied:true, scope:'individual browser assertions; not complete G15-G19', executionAuthority:'none'};
  } finally {
    // Always close resources created by this call, including after revocation/error.
    const closing = await Promise.allSettled(contexts.map(c=>c.close()));
    await browser.close();
    requireThat(closing.every(x=>x.status==='fulfilled'), 'browser cleanup incomplete');
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (process.argv.length === 3 && process.argv[2] === '--describe') {
    console.log(JSON.stringify({executionAuthority:'none', runtimeStatus:'NOT_EXECUTED',
      requires:'External guarded API call; no executable WorkOrder CLI'}));
  } else {
    console.error('BLOCKED: EXECUTION_B requires a separate hash-bound external authorization and reservation.');
    process.exitCode = 2;
  }
}
