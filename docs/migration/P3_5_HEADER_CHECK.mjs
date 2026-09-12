import {createRequire} from 'node:module';
import fs from 'node:fs';
const [product,url,label,out]=process.argv.slice(2);
const {chromium}=createRequire(product+'/package.json')('@playwright/test');
const browser=await chromium.launch({headless:true});const results=[];
try {for(const width of [1440,390,320]) {
 const context=await browser.newContext({viewport:{width,height:960}});const page=await context.newPage();const errors=[],external=[];
 page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',r=>{if(new URL(r.request().url()).origin!==url){external.push(r.request().url());return r.abort();}return r.continue();});
 const measure=()=>page.evaluate(()=>{const h=document.querySelector('header'),r=h.getBoundingClientRect(),s=getComputedStyle(h);return {scrollY,top:r.top,left:r.left,width:r.width,height:r.height,position:s.position,offset:s.top,zIndex:s.zIndex,overflow:document.documentElement.scrollWidth>innerWidth,headerAtTop:!!document.elementFromPoint(innerWidth/2,10)?.closest('header')};});
 await page.goto(url);await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(150);const clean=await measure();
 await page.screenshot({path:`${out}/${label}-clean-${width}.png`,fullPage:false});await page.screenshot({path:`${out}/${label}-landing-${width}.png`,fullPage:true});
 // Reproduce the historical visual test before its full-page capture.
 await page.locator('#preguntas summary').first().focus();await page.keyboard.press('Enter');
 if(width<1050){await page.getByText('Menú',{exact:true}).click();await page.getByText('Menú',{exact:true}).click();}
 await page.emulateMedia({reducedMotion:'reduce'});await page.waitForTimeout(150);
 const historical=await measure();await page.screenshot({path:`${out}/${label}-historical-${width}.png`,fullPage:true});
 await page.screenshot({path:`${out}/${label}-scrolled-viewport-${width}.png`,fullPage:false});
 await page.evaluate(()=>window.scrollTo({top:600,behavior:'instant'}));const scrolled=await measure();
 await page.reload();await page.evaluate(()=>{history.scrollRestoration='manual';window.scrollTo({top:0,behavior:'instant'});});await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(100);const reset=await measure();
 if([clean,scrolled,reset].some(m=>m.top!==0||m.left!==0||m.width!==width||m.overflow||!m.headerAtTop)||errors.length||external.length)throw Error('Header check failed '+JSON.stringify({label,width,clean,scrolled,reset,errors,external}));
 results.push({label,width,clean,historical,scrolled,reset,errors,external});await context.close();
}}finally{await browser.close();fs.writeFileSync(`${out}/${label}.json`,JSON.stringify(results,null,2));}
