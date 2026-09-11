"use client";
import { useMemo, useRef, useState, useEffect } from "react";
import { behavior, createLocalChat, type ChatService } from "../services/interactions";
import { useInquiry } from "./InquiryState";
import s from "./Site.module.css";
export function DemoChat({ service }: { service?: ChatService }) {
  const {content}=useInquiry(); const chat=useMemo(()=>service ?? createLocalChat(content),[service,content]);
  const dialog=useRef<HTMLDialogElement>(null);const trigger=useRef<HTMLButtonElement>(null);const input=useRef<HTMLInputElement>(null);
  const [messages,setMessages]=useState<{role:string;text:string}[]>([]);const [text,setText]=useState("");const [busy,setBusy]=useState(false);
  const log=useRef<HTMLDivElement>(null);
  useEffect(()=>{if(log.current)log.current.scrollTop=log.current.scrollHeight;},[messages]);
  const navigate=(id:string)=>{dialog.current?.close(); requestAnimationFrame(()=>{const target=document.getElementById(id);target?.scrollIntoView();target?.setAttribute("tabindex","-1");target?.focus({preventScroll:true});});};
  return <>
    <button ref={trigger} className={s.chatLauncher} aria-haspopup="dialog" onClick={()=>{dialog.current?.showModal();input.current?.focus();}}>Asistente de demostración</button>
    <dialog ref={dialog} className={s.chatDialog} aria-labelledby="chat-title" onClose={()=>trigger.current?.focus()} onKeyDown={e=>{
      if(e.key!=="Tab") return;
      const items=Array.from(e.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), a[href], textarea:not(:disabled), [tabindex="0"]')).filter(el=>el.getClientRects().length>0);
      const first=items[0],last=items.at(-1);
      if(!first){e.preventDefault();return;}
      if(e.shiftKey && document.activeElement===first){e.preventDefault();last?.focus();}
      else if(!e.shiftKey && document.activeElement===last){e.preventDefault();first.focus();}
    }}>
      <header className={s.chatHeader}><h2 id="chat-title">Asistente de demostración</h2><button onClick={()=>dialog.current?.close()} aria-label="Cerrar asistente">×</button></header>
      <p>Respuestas locales de ejemplo. Sin IA externa. No incluyas información sensible.</p>
      <nav className={s.actions} aria-label="Accesos del asistente"><button onClick={()=>navigate("servicios")}>Servicios</button>{content.plans.length > 0 && <button onClick={()=>navigate("planes")}>Planes de ejemplo</button>}<button onClick={()=>navigate("contacto")}>Contacto</button></nav>
      <div ref={log} className={s.messages} role="log" aria-label="Conversación" aria-live="polite">{messages.map((m,i)=><p key={i} className={m.role==="Tú" ? s.userMessage : s.botMessage}><strong>{m.role}: </strong>{m.text}</p>)}</div>
      <form onSubmit={async e=>{e.preventDefault();if(!text.trim()||busy)return;const question=text.trim();setText("");setBusy(true);setMessages(v=>[...v,{role:"Tú",text:question}].slice(-behavior.chatLimit));try{const answer=await chat.reply(question);setMessages(v=>[...v,{role:"Asistente",text:answer}].slice(-behavior.chatLimit));}catch{setMessages(v=>[...v,{role:"Asistente",text:behavior.chatFallback}].slice(-behavior.chatLimit));}finally{setBusy(false);}}}>
        <label htmlFor="chat-message">Mensaje al asistente</label><input ref={input} className={s.field} id="chat-message" maxLength={500} value={text} onChange={e=>setText(e.target.value)} />
        <button className={s.button} disabled={!text.trim()||busy}>Consultar asistente</button>
      </form>
    </dialog>
  </>;
}
