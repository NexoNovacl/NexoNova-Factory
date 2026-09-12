import {createRequire} from 'node:module';import fs from 'node:fs';
const [product,out]=process.argv.slice(2),content=JSON.parse(fs.readFileSync(product+'/src/content/site.json','utf8'));
const {chromium}=createRequire(product+'/package.json')('@playwright/test');const browser=await chromium.launch();const results=[];
const assert=(ok,msg)=>{if(!ok)throw Error(msg)};
try{for(const width of [1440,390,320]){
 const context=await browser.newContext({viewport:{width,height:960},reducedMotion:'reduce',permissions:['clipboard-read','clipboard-write']});const page=await context.newPage();const errors=[],external=[];
 page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',r=>{if(new URL(r.request().url()).origin!=='http://127.0.0.1:3185'){external.push(r.request().url());return r.abort();}return r.continue();});
 await page.goto('http://127.0.0.1:3185');await page.evaluate(()=>document.fonts.ready);
 const geometry=()=>page.evaluate(()=>{const r=document.querySelector('header').getBoundingClientRect();return {y:scrollY,top:r.top,left:r.left,width:r.width,height:r.height};});
 let a=await geometry();await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));let b=await geometry();assert(JSON.stringify(a)===JSON.stringify(b)&&b.y===0&&b.top===0,'Unstable initial viewport');
 await page.screenshot({path:`${out}/clean-${width}.png`,fullPage:false});await page.screenshot({path:`${out}/landing-${width}.png`,fullPage:true});
 const tokens=await page.getByRole('banner').evaluate(e=>{const s=getComputedStyle(e);return ['--brand-navy','--brand-blue','--brand-cyan'].map(k=>s.getPropertyValue(k).trim());});assert(JSON.stringify(tokens)===JSON.stringify([content.brand.navy,content.brand.blue,content.brand.cyan]),'Brand tokens');
 assert((await page.locator('#planes').count())===(content.plans.length?1:0),'Plans visibility');
 const chat=page.getByRole('button',{name:'Asistente de demostración',exact:true});await chat.click();
 await page.locator('#chat-message').fill('servicios');await page.keyboard.press('Enter');await page.getByRole('log').getByText(content.services[0].description,{exact:false}).waitFor();
 await page.locator('#chat-message').fill('planes');await page.keyboard.press('Enter');
 const expected=content.plans.length?content.plans[0].price:'Esta configuración no incluye planes de ejemplo.';await page.getByRole('log').getByText(expected,{exact:false}).waitFor();
 await page.keyboard.press('Escape');await page.getByRole('button',{name:'Seleccionar servicio '+content.services[0].title,exact:true}).click();
 await page.locator('#contact-name').fill('Persona Sintética');await page.locator('#contact-medium').fill('persona@example.invalid');await page.locator('#contact-interest').fill(content.services[0].title);await page.locator('#contact-message').fill('Solicitud ficticia para revisión local.');await page.getByRole('button',{name:'Preparar vista previa'}).click();
 const message=await page.locator('#prepared-message').inputValue();assert(message.includes('Consulta para '+content.brand.name)&&message.includes(content.services[0].title),'Wrong inquiry branding');
 await page.getByRole('button',{name:'Copiar consulta',exact:true}).click();assert(await page.evaluate(()=>navigator.clipboard.readText())===message,'Copy mismatch');
 assert(!errors.length&&!external.length,'Browser errors/network');results.push({width,geometry:b,tokens,plans:content.plans.length,chatExpected:expected,preparedMessage:message,errors,external});await context.close();
}}finally{await browser.close();fs.writeFileSync(out+'/browser.json',JSON.stringify(results,null,2));}
