"use client";
import { useState } from 'react';
export default function Logout() {
  const [error,setError] = useState('');
  async function logout() {
    try { const result = await fetch('/api/auth/sign-out', {method:'POST', headers:{'Content-Type':'application/json'},body:'{}'}); if (!result.ok) throw new Error(); window.location.assign('/login'); }
    catch { setError('No fue posible cerrar la sesión.'); }
  }
  return <><button onClick={logout}>Cerrar sesión</button><p role="status">{error}</p></>;
}
