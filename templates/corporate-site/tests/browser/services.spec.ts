import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { normalizeDomain, createLocalChat, behavior, prepareInquiry } from '../../src/services/interactions';
const content = JSON.parse(readFileSync(new URL('../../src/content/site.json', import.meta.url), 'utf8'));
for (const [raw, expected] of [
 ['  HTTPS://WWW.EJEMPLO.CL/  ', 'www.ejemplo.cl'], ['Ejemplo.CL.', 'ejemplo.cl'],
 ['sub.mi-empresa.cl', 'sub.mi-empresa.cl'], ['xn--maana-pta.cl', 'xn--maana-pta.cl'],
 ['localhost', null], ['127.0.0.1', null], ['https://user:pass@ejemplo.cl', null],
 ['ejemplo.cl/ruta', null], ['-mal.cl', null], ['mal..cl', null], ['mañana.cl', null],
 ['a'.repeat(64)+'.cl', null], ['ejemplo.cl?x=1', null], ['', null],
] as const) test(`domain ${raw}`, () => { expect(normalizeDomain(raw)).toBe(expected); });
test('chat answers only deterministic configured content and bounded fallback', async () => {
 const chat=createLocalChat(content);
 expect(await chat.reply('servicios')).toBe(await chat.reply('servicios'));
 for(const service of content.services) expect(await chat.reply('servicios')).toContain(service.description);
 expect(await chat.reply('inventar ventas millonarias')).toBe(behavior.chatFallback);
 expect(await chat.reply('contacto')).toContain('No se enviará');
 expect(await chat.reply('planes')).toBe(await chat.reply('planes'));
});
test('preparation has explicit non-send notice and no totals', () => {
 const text=prepareInquiry({name:' Ana ',contact:'correo de prueba',interest:'Web',message:'Hola'},
 {planId:content.plans[0]?.id ?? '',services:[content.services[0].title],domain:'ejemplo.cl'},content);
 expect(text).toContain('Nombre: Ana');expect(text).toContain('ejemplo.cl — Disponibilidad no consultada');
 expect(text).toContain(behavior.preparedNotice);expect(text).not.toContain('Total');
 expect(()=>prepareInquiry({name:' ',contact:'x',interest:'x',message:'x'},{planId:'',services:[],domain:''},content)).toThrow();
});
