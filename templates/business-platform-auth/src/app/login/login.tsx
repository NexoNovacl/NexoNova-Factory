"use client";
import { useState, type FormEvent } from 'react';
import styles from '../page.module.css';
export default function Login() {
  const [message,setMessage] = useState(''); const [busy,setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget); setBusy(true);setMessage('');
    try { const result = await fetch('/api/auth/sign-in/email', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ email:data.get('email'),password:data.get('password'),rememberMe:false }) });
      if (result.ok) window.location.assign('/auth-check'); else setMessage(result.status === 429 ? 'Demasiados intentos. Espera un minuto.' : 'No fue posible iniciar sesión.');
    } catch { setMessage('Servicio no disponible.'); } finally { setBusy(false); }
  }
  return <form onSubmit={submit} className={styles.card}><label>Email<input name="email" type="email" autoComplete="username" required maxLength={254} /></label><label>Contraseña<input name="password" type="password" autoComplete="current-password" required minLength={15} maxLength={128}/></label><button disabled={busy} type="submit">Entrar</button><p role="status">{message}</p><noscript>Esta prueba requiere JavaScript para iniciar sesión.</noscript></form>;
}
