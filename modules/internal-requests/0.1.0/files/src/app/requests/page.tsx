import {headers} from 'next/headers';
import {redirect} from 'next/navigation';
import Link from 'next/link';
import {identity} from '../../server/auth.js';
import {listRequests} from '../../modules/internal-requests/service.js';
import {RequestError} from '../../modules/internal-requests/validation.js';
import {Editor} from './editor.js';
import styles from './requests.module.css';
export const dynamic='force-dynamic';
export default async function Requests({searchParams}:{searchParams:Promise<Record<string,string|string[]|undefined>>}) {
  let actor;try {actor=await identity(await headers());}catch{return <main>Servicio no disponible</main>;}
  if(!actor)redirect('/login');
  let result;
  try {
    const params=new URLSearchParams();for(const [key,value] of Object.entries(await searchParams)){if(Array.isArray(value))value.forEach(v=>params.append(key,v));else if(value!==undefined)params.append(key,value);}
    result=await listRequests(actor,params);
  }catch(e){return <main>{e instanceof RequestError?'Entrada rechazada':'Servicio no disponible'}</main>;}
  return <main className={styles.main}><h1>Solicitudes internas</h1><h2>Nueva solicitud</h2><Editor/><h2>Listado</h2>
    <ul className={styles.list}>{result.items.map(item=><li key={item.id}><Link href={`/requests/${item.id}`}>{item.title}</Link> · {item.status}</li>)}</ul>
    {!result.items.length&&<p>No hay solicitudes visibles.</p>}
    {result.nextCursor&&<Link href={`/requests?cursor=${result.nextCursor}&limit=${Math.min(100,result.items.length)}`}>Siguiente página</Link>}
    <p><Link href="/requests">Recargar desde inicio</Link></p>
  </main>;
}
