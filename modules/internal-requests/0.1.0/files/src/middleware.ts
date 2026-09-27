// Response-cache defense only. Authentication and authorization stay in server services.
import {NextResponse} from 'next/server';
export function middleware() {
  const response=NextResponse.next();response.headers.set('Cache-Control','no-store');response.headers.set('Vary','Cookie');return response;
}
export const config={matcher:['/requests/:path*','/api/requests/:path*']};
