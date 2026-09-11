import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
const content=JSON.parse(readFileSync(new URL('../../src/content/site.json',import.meta.url),'utf8'));
for(const width of [1440,390]) {
 test(`integrated local inquiry and chat ${width}px`,async({page,context})=>{
  await page.setViewportSize({width,height:960});
  const network:string[]=[],errors:string[]=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',route=>{
   const req=route.request();const url=new URL(req.url());
   if(url.origin!=='http://127.0.0.1:3183'||req.method()!=='GET'||url.pathname.startsWith('/api/')) {network.push(req.method()+' '+url.pathname);return route.abort();}
   return route.continue();
  });
  await page.goto('/');
  await page.locator('#domain').fill('mal..cl');await page.getByRole('button',{name:'Consultar',exact:true}).click();
  await expect(page.locator('#domain-result')).toContainText('Introduce un dominio válido');
  await page.locator('#domain').fill(' HTTPS://WWW.EJEMPLO.CL/ ');await page.getByRole('button',{name:'Consultar',exact:true}).click();
  await expect(page.locator('#domain')).toHaveValue('www.ejemplo.cl');
  await expect(page.locator('#domain-result')).toContainText('Disponibilidad no consultada');
  await expect(page.locator('#domain-note')).toHaveText('Demostración: no consulta disponibilidad ni registra dominios.');
  await page.getByRole('button',{name:'Añadir dominio a Tu consulta'}).click();
  const inquiry=page.locator('#consulta');await expect(inquiry).toContainText('www.ejemplo.cl');
  await inquiry.getByRole('button',{name:'Eliminar dominio'}).click();await expect(inquiry).not.toContainText('Dominio: www.ejemplo.cl');
  await page.locator('#inquiry-domain').fill('NUEVO.CL');await inquiry.getByRole('button',{name:'Guardar dominio'}).click();
  await expect(inquiry).toContainText('Dominio: nuevo.cl');
  await page.getByRole('button',{name:'Seleccionar servicio '+content.services[0].title,exact:true}).click();
  await expect(inquiry).toContainText('Servicio: '+content.services[0].title);
  await inquiry.getByRole('button',{name:'Eliminar servicio '+content.services[0].title,exact:true}).click();
  await page.getByRole('button',{name:'Seleccionar servicio '+content.services[0].title,exact:true}).click();
  if(content.services.length>1) await page.getByRole('button',{name:'Seleccionar servicio '+content.services[1].title,exact:true}).click();
  if(content.plans.length){
   await page.getByRole('button',{name:'Seleccionar plan '+content.plans[0].name,exact:true}).click();
   await expect(inquiry).toContainText('Plan de ejemplo: '+content.plans[0].name);
   await inquiry.getByRole('button',{name:'Eliminar plan',exact:true}).click();
   await expect(inquiry).not.toContainText('Plan de ejemplo:');
   await page.getByRole('button',{name:'Seleccionar plan '+content.plans.at(-1).name,exact:true}).click();
  }
  await inquiry.getByRole('link',{name:'Preparar consulta',exact:true}).click();
  await expect(page.locator('#contacto')).toContainText('Dominio: nuevo.cl');
  await page.locator('#contact-name').fill('Ana Piloto');await page.locator('#contact-medium').fill('ana@example.invalid');
  await page.locator('#contact-interest').fill('Sitio informativo');await page.locator('#contact-message').fill('Consulta sintética de prueba.');
  await page.getByRole('button',{name:'Preparar vista previa'}).click();
  await expect(page.getByText('La consulta se ha preparado; no se ha enviado.',{exact:true})).toBeVisible();
  const preview=page.locator('#prepared-message');await expect(preview).toContainText('Servicio: '+content.services[0].title);
  await expect(preview).toContainText('Dominio: nuevo.cl');
  await context.grantPermissions(['clipboard-read','clipboard-write']);
  await page.getByRole('button',{name:'Copiar consulta',exact:true}).click();
  expect(await page.evaluate(()=>navigator.clipboard.readText())).toBe(await preview.inputValue());
  await page.locator('#contact-message').fill('Mensaje actualizado');await expect(preview).toHaveCount(0);
  await page.getByRole('button',{name:'Preparar vista previa'}).click();
  await inquiry.getByRole('button',{name:'Eliminar dominio'}).click();await expect(preview).toHaveCount(0);
  await page.getByRole('button',{name:'Preparar vista previa'}).click();await expect(preview).not.toContainText('nuevo.cl');
  const launcher=page.getByRole('button',{name:'Asistente de demostración',exact:true});await launcher.click();
  const dialog=page.getByRole('dialog');await expect(dialog).toBeVisible();await expect(page.locator('#chat-message')).toBeFocused();
  await page.locator('#chat-message').fill('servicios');await page.keyboard.press('Enter');
  await expect(page.getByRole('log')).toContainText(content.services[0].description);
  await page.locator('#chat-message').fill('pregunta no contemplada');await page.keyboard.press('Enter');
  await expect(page.getByRole('log')).toContainText('Solo puedo orientar');
  await expect(page.getByRole('log').getByText(/Solo puedo orientar/)).toBeInViewport();
  for(let i=0;i<10;i++){await page.keyboard.press('Shift+Tab');expect(await page.evaluate(()=>!!document.activeElement?.closest('dialog'))).toBe(true);}
  for(let i=0;i<10;i++){await page.keyboard.press('Tab');expect(await page.evaluate(()=>!!document.activeElement?.closest('dialog'))).toBe(true);}
  await page.screenshot({path:`test-results/chat-${width}.png`,fullPage:false});
  await page.keyboard.press('Escape');await expect(dialog).not.toBeVisible();await expect(launcher).toBeFocused();
  await launcher.click();await expect(page.getByRole('log')).toContainText('pregunta no contemplada');
  await dialog.getByRole('button',{name:'Servicios',exact:true}).click();await expect(dialog).not.toBeVisible();await expect(page.locator('#servicios')).toBeFocused();
  await launcher.click();await dialog.getByRole('button',{name:'Contacto',exact:true}).click();await expect(page.locator('#contacto')).toBeFocused();
  if(content.plans.length){await launcher.click();await dialog.getByRole('button',{name:'Planes de ejemplo',exact:true}).click();await expect(page.locator('#planes')).toBeFocused();}
  await launcher.click();await page.getByRole('button',{name:'Cerrar asistente'}).click();await expect(launcher).toBeFocused();
  expect(await page.evaluate(()=>[localStorage.length,sessionStorage.length])).toEqual([0,0]);
  expect(network).toEqual([]);expect(errors).toEqual([]);
  await page.screenshot({path:`test-results/flow-${width}.png`,fullPage:true});
  await page.reload();await expect(inquiry).toContainText('Aún no has seleccionado intereses.');
  await expect(page.locator('#contact-name')).toHaveValue('');
  await launcher.click();await expect(page.getByRole('log')).toHaveText('');
 });
}
test('clipboard denial keeps a selectable preview and honest failure',async({page})=>{
 await page.goto('/');
 await page.locator('#contact-name').fill('Prueba');await page.locator('#contact-medium').fill('medio');
 await page.locator('#contact-interest').fill('interés');await page.locator('#contact-message').fill('mensaje');
 await page.getByRole('button',{name:'Preparar vista previa'}).click();
 await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(new Error('denied'))},configurable:true}));
 await page.getByRole('button',{name:'Copiar consulta'}).click();
 await expect(page.getByText('No se pudo copiar. Selecciona el texto y cópialo manualmente.')).toBeVisible();
 await expect(page.locator('#prepared-message')).toBeFocused();
});

test('native submissions remain blocked when JavaScript is disabled',async({browser})=>{
 const context=await browser.newContext({javaScriptEnabled:false});
 const page=await context.newPage();const response=await page.goto('http://127.0.0.1:3183/');
 expect(response?.headers()['content-security-policy']).toContain("form-action 'none'");
 await page.locator('#domain').fill('ejemplo.cl');
 const requests:string[]=[];page.on('request',r=>requests.push(r.url()));
 await expect(page.getByRole('button',{name:'Consultar',exact:true})).toBeDisabled();
 await page.locator('#domain').press('Enter');
 await expect(page).toHaveURL('http://127.0.0.1:3183/');expect(requests).toEqual([]);
 await context.close();
});
