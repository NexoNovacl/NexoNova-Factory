'use client';
import {useState,type FormEvent} from 'react';
import {useRouter} from 'next/navigation';
import type {RequestDto} from '../../modules/internal-requests/dto.js';
import styles from './requests.module.css';
export function Editor({initial}:{initial?:RequestDto}) {
  const router=useRouter();const [item,setItem]=useState(initial);
  const [title,setTitle]=useState(initial?.title??'');const [description,setDescription]=useState(initial?.description??'');
  const [message,setMessage]=useState('');const [busy,setBusy]=useState(false);const [confirm,setConfirm]=useState(false);
  async function save(action: 'edit'|'close'|'reopen'|'archive') {
    if(busy)return;setBusy(true);setMessage('');
    try {
      const fields={title,description};
      const body=item?{action,expectedVersion:item.version,...(action==='edit'?fields:{})}:fields;
      const res=await fetch(item?`/api/requests/${item.id}`:'/api/requests',{method:item?'PATCH':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),cache:'no-store'});
      if(res.status===204){router.push('/requests');router.refresh();return;}
      if(!res.ok){setMessage(res.status===409?'Conflicto de versión o estado. Tu borrador se conserva. Recarga antes de volver a guardar.':res.status===404?'Solicitud no disponible.':res.status===503?'Servicio no disponible. El resultado puede ser incierto; recarga antes de reintentar.':'Operación rechazada.');return;}
      const data=await res.json();setItem(data.item);
      if(!item){router.push(`/requests/${data.item.id}`);router.refresh();}
      else {setMessage('Cambios guardados.');router.refresh();}
    } catch {setMessage('Conexión interrumpida. El resultado puede ser incierto; recarga antes de reintentar.');}
    finally {setBusy(false);setConfirm(false);}
  }
  function submit(e:FormEvent){e.preventDefault();void save('edit');}
  return <section>
    {item&&<p>Estado: <span data-testid="status">{item.status}</span> · Versión: <span data-testid="version">{item.version}</span></p>}
    <form className={styles.form} onSubmit={submit}>
      <label>Título<input name="title" value={title} required onChange={e=>setTitle(e.target.value)}/></label>
      <label>Descripción<textarea name="description" value={description} onChange={e=>setDescription(e.target.value)}/></label>
      <button disabled={busy} type="submit">{item?'Guardar':'Crear'}</button>
    </form>
    {item&&<div className={styles.actions}>
      <button disabled={busy} onClick={()=>void save(item.status==='open'?'close':'reopen')}>{item.status==='open'?'Cerrar':'Reabrir'}</button>
      <button disabled={busy} onClick={()=>setConfirm(true)}>Archivar</button>
      <button disabled={busy} onClick={()=>window.location.reload()}>Recargar</button>
    </div>}
    {confirm&&<section role="group" aria-label="Confirmar archivado"><p>El archivado es permanente y la solicitud dejará de estar visible.</p><button disabled={busy} onClick={()=>void save('archive')}>Confirmar archivado</button><button onClick={()=>setConfirm(false)}>Cancelar</button></section>}
    <p role="status" className={styles.message}>{message}</p>
  </section>;
}
