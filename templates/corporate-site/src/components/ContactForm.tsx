"use client";
import { useState, useRef } from "react";
import { useInquiry } from "./InquiryState";
import { behavior, prepareInquiry, interestLines, type ContactFields } from "../services/interactions";
import s from "./Site.module.css";
export function ContactForm() {
  const { interest, content } = useInquiry();
  const [fields,setFields] = useState<ContactFields>({name:"",contact:"",interest:"",message:""});
  const [prepared,setPrepared] = useState<{text:string; signature:string}|null>(null); const [copyState,setCopyState] = useState("");
  const previewRef=useRef<HTMLTextAreaElement>(null); const signature=JSON.stringify({fields,interest});
  const current=prepared?.signature === signature ? prepared.text : "";
  const update=(key:keyof ContactFields,value:string)=>{setFields(v=>({...v,[key]:value}));setCopyState("");};
  return <section id="contacto" className={s.contact} aria-labelledby="contact-title"><div className={s.container}>
    <h2 id="contact-title">Tu próximo paso online empieza con una conversación.</h2>
    <p>No se ha enviado ninguna consulta. La información permanece solo en esta página hasta recargarla.</p>
    <form className={s.contactForm} onSubmit={e=>{e.preventDefault();setPrepared({text:prepareInquiry(fields,interest,content),signature});setCopyState("");}}>
      <label htmlFor="contact-name">Nombre</label><input className={s.field} id="contact-name" required maxLength={120} value={fields.name} onChange={e=>update("name",e.target.value)} pattern=".*\S.*" />
      <label htmlFor="contact-medium">Medio de contacto</label><input className={s.field} id="contact-medium" required maxLength={200} value={fields.contact} onChange={e=>update("contact",e.target.value)} pattern=".*\S.*" placeholder="Correo o teléfono que quieras incluir" />
      <label htmlFor="contact-interest">Servicio o interés</label><input className={s.field} id="contact-interest" required maxLength={300} value={fields.interest} onChange={e=>update("interest",e.target.value)} pattern=".*\S.*" />
      <div aria-label="Intereses incorporados">{interestLines(interest,content).map(line=><p key={line}>{line}</p>)}</div>
      <label htmlFor="contact-message">Mensaje</label><textarea className={s.field} id="contact-message" required maxLength={3000} value={fields.message} onChange={e=>update("message",e.target.value)} />
      <button className={s.button} type="submit" disabled={Object.values(fields).some(v=>!v.trim())}>Preparar vista previa</button>
    </form>
    {current ? <div className={s.preview}>
      <p role="status">{behavior.preparedNotice}</p><label htmlFor="prepared-message">Vista previa del mensaje</label>
      <textarea ref={previewRef} className={s.field} id="prepared-message" readOnly value={current} rows={12} />
      <button className={s.button} onClick={async()=>{try {await navigator.clipboard.writeText(current);setCopyState("Copiado al portapapeles; no enviado.");}catch {setCopyState("No se pudo copiar. Selecciona el texto y cópialo manualmente.");previewRef.current?.focus();previewRef.current?.select();}}}>Copiar consulta</button>
      <p role="status">{copyState}</p>
    </div> : prepared && <p role="status">La selección o el mensaje cambió. Prepara una nueva vista previa.</p>}
  </div></section>;
}
