import { headers } from 'next/headers';
import { redirect } from 'next/navigation';
import { identity } from '../../server/auth';
import Logout from '../logout';
export const dynamic = 'force-dynamic';
export default async function Page() {
  let user; try { user = await identity(await headers()); } catch { return <main><h1>Servicio no disponible</h1></main>; }
  if (!user) redirect('/login');
  if (user.role !== 'admin') return <main><h1>Acceso denegado</h1></main>;
  return <main><h1>Prueba administrativa</h1><p>Rol admin validado en servidor. Sin recursos empresariales.</p><Logout /></main>;
}
