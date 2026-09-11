import type { SiteContent } from "../content/types";
export const behavior = {
  domainNotice: "Demostración: no consulta disponibilidad ni registra dominios.",
  domainStatus: "Disponibilidad no consultada",
  preparedNotice: "La consulta se ha preparado; no se ha enviado.",
  chatLimit: 40,
  chatFallback: "Solo puedo orientar sobre los servicios, planes de ejemplo y contacto de esta demostración. No consulto datos externos ni confirmo condiciones comerciales.",
};
export function normalizeDomain(raw: string): string | null {
  const value = raw.trim().toLowerCase().replace(/^https?:\/\//, "").replace(/\/$/, "").replace(/\.$/, "");
  if (value.length > 253 || !/^[a-z0-9.-]+$/.test(value)) return null;
  const labels = value.split(".");
  if (labels.length < 2 || !labels.every(label => /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(label))) return null;
  if (!/^(?:[a-z]{2,63}|xn--[a-z0-9-]{2,59})$/.test(labels.at(-1)!)) return null;
  return value;
}
export type Interest = { planId: string; services: string[]; domain: string };
export type ContactFields = { name: string; contact: string; interest: string; message: string };
export function interestLines(value: Interest, content: SiteContent): string[] {
  const plan = content.plans.find(p => p.id === value.planId);
  return [plan ? `Plan de ejemplo: ${plan.name} (provisional)` : "",
    ...value.services.filter(title => content.services.some(s => s.title === title)).map(title => `Servicio: ${title}`),
    value.domain ? `Dominio: ${value.domain} — ${behavior.domainStatus}` : ""].filter(Boolean);
}
export function prepareInquiry(fields: ContactFields, interest: Interest, content: SiteContent): string {
  if (Object.values(fields).some(v => !v.trim())) throw new Error("Completa los campos requeridos.");
  return [`Consulta para ${content.brand.name}`, `Nombre: ${fields.name.trim()}`, `Medio de contacto: ${fields.contact.trim()}`,
    `Interés: ${fields.interest.trim()}`, ...interestLines(interest, content), `Mensaje: ${fields.message.trim()}`, behavior.preparedNotice].join("\n");
}
export interface ChatService { reply(message: string): Promise<string> }
export function createLocalChat(content: SiteContent): ChatService {
  return { async reply(message) {
    const query = message.trim().toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    if (/\b(servicios?|web)\b/.test(query)) return content.services.map(s => `${s.title}: ${s.description}`).join("\n");
    if (/\b(planes?|precios?)\b/.test(query)) return content.plans.length ?
      content.plans.map(p => `${p.name}: ${p.price} — ejemplo provisional. ${p.description}`).join("\n") : "Esta configuración no incluye planes de ejemplo.";
    if (/\b(contacto|consulta)\b/.test(query)) return "En Contacto puedes preparar y copiar una consulta local. No se enviará ningún mensaje.";
    const faq = content.faq.find(f => f.question.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "") === query);
    return faq?.answer ?? behavior.chatFallback;
  }};
}
