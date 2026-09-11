"use client";
import { useState } from "react";
import { useInquiry } from "./InquiryState";
import { normalizeDomain, interestLines } from "../services/interactions";
import s from "./Site.module.css";
export function Inquiry() {
  const { ready, interest, content, setPlan, toggleService, setDomain } = useInquiry(); const [error, setError] = useState("");
  return <section id="consulta" className={s.section} aria-labelledby="inquiry-title"><div className={s.container}>
    <article className={s.plan}><p className={s.eyebrow}>Intereses para conversar</p><h2 id="inquiry-title">Tu consulta</h2>
      <p>Elige o modifica tus intereses. No se realiza contratación ni se envía información.</p>
      <div role="status">{interestLines(interest,content).length ? <ul>{interestLines(interest,content).map(line => <li key={line}>{line}</li>)}</ul> : <p>Aún no has seleccionado intereses.</p>}</div>
      <div className={s.actions}>
        {interest.planId && <button className={s.button} onClick={() => setPlan("")}>Eliminar plan</button>}
        {interest.services.map(title => <button className={s.button} key={title} onClick={() => toggleService(title)}>Eliminar servicio {title}</button>)}
        {interest.domain && <button className={s.button} onClick={() => setDomain("")}>Eliminar dominio</button>}
      </div>
      <form key={interest.domain} onSubmit={e => {e.preventDefault(); const data = new FormData(e.currentTarget); const value=normalizeDomain(String(data.get("domain"))); if(value){setDomain(value);setError("");}else setError("Introduce un dominio válido.");}}>
        <label htmlFor="inquiry-domain">Añadir o modificar dominio</label>
        <input className={s.field} id="inquiry-domain" name="domain" defaultValue={interest.domain} maxLength={300} />
        <button className={s.button} type="submit" disabled={!ready}>Guardar dominio</button><p role="status">{error}</p>
      </form>
      <div className={s.actions}><a href="#servicios">Cambiar servicios</a>{content.plans.length > 0 && <a href="#planes">Cambiar plan</a>}<a className={s.button} href="#contacto">Preparar consulta</a></div>
    </article>
  </div></section>;
}
