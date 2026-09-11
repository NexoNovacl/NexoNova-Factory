"use client";
import { useState } from "react";
import { behavior, normalizeDomain } from "../services/interactions";
import { useInquiry } from "./InquiryState";
import s from "./Site.module.css";
export function DomainSearch() {
  const [input, setInput] = useState(""); const [checked, setChecked] = useState(""); const [error, setError] = useState("");
  const { interest, setDomain, ready } = useInquiry();
  return <section id="dominios" className={s.domain} aria-labelledby="domain-title">
    <p className={s.eyebrow}>Demostración local</p><h2 id="domain-title">Consulta tu dominio</h2>
    <p>Una idea para tu próxima dirección online.</p>
    <form onSubmit={e => { e.preventDefault(); const value = normalizeDomain(input); setChecked(value ?? ""); setError(value ? "" : "Introduce un dominio válido, sin rutas ni datos de acceso (ejemplo.cl)."); if(value) setInput(value); }}>
      <label htmlFor="domain">Nombre de dominio</label>
      <div className={s.search}><span aria-hidden="true">www.</span><input id="domain" value={input} onChange={e => {setInput(e.target.value);setChecked("");setError("");}} maxLength={300} autoCapitalize="none" autoComplete="off" spellCheck={false} aria-describedby="domain-note domain-result" placeholder="tudominio.cl" /><button type="submit" disabled={!ready}>Consultar</button></div>
    </form>
    <p id="domain-note" className={s.note}>{behavior.domainNotice}</p>
    <div id="domain-result" role="status">{error || (checked && `${checked} — ${behavior.domainStatus}`)}</div>
    {checked && <button className={s.lightButton} onClick={() => setDomain(checked)} disabled={interest.domain === checked}>{interest.domain === checked ? "Dominio incorporado" : "Añadir dominio a Tu consulta"}</button>}
    <p><a href="#consulta">Revisar Tu consulta →</a></p>
  </section>;
}
