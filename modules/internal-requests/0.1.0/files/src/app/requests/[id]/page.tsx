import {headers} from 'next/headers';
import {redirect,notFound} from 'next/navigation';
import Link from 'next/link';
import {identity} from '../../../server/auth.js';
import {getRequest} from '../../../modules/internal-requests/service.js';
import {RequestError} from '../../../modules/internal-requests/validation.js';
import {Editor} from '../editor.js';
import styles from '../requests.module.css';
export const dynamic='force-dynamic';
export default async function Detail({params}:{params:Promise<{id:string}>}) {
  let actor;try{actor=await identity(await headers());}catch{return <main>Servicio no disponible</main>;}
  if(!actor)redirect('/login');
  let item;try{item=await getRequest(actor,(await params).id);}catch(e){if(e instanceof RequestError&&e.status===404)notFound();return <main>Servicio no disponible</main>;}
  return <main className={styles.main}><Link href="/requests">Volver al listado</Link><h1>Detalle de solicitud</h1><Editor initial={item}/></main>;
}
