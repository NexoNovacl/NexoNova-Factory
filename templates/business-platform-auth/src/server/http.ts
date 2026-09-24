import { getAuth, identity } from './auth.js';
import { authEnvironment, validPassword } from './policy.js';
export function response(value: unknown, status = 200) {
  return Response.json(value, { status, headers: { 'Cache-Control': 'no-store', 'Vary': 'Cookie', 'X-Content-Type-Options': 'nosniff' } });
}
// Conservative per-process login budget; no identity derived from spoofable proxy headers.
let windowStart = 0, attempts = 0;
function allowLogin() {
  const now = Date.now();
  if (now - windowStart >= 60000) { windowStart = now; attempts = 0; }
  return ++attempts <= 5;
}
async function body(request: Request): Promise<Record<string, unknown>> {
  if (!request.headers.get('content-type')?.startsWith('application/json')) throw new Error();
  const reader = request.body?.getReader(); if (!reader) throw new Error();
  const chunks: Uint8Array[] = []; let length = 0;
  try {
    for (;;) { const {done, value} = await reader.read(); if (done) break; length += value.byteLength; if (length > 4096) throw new Error(); chunks.push(value); }
  } finally { await reader.cancel(); reader.releaseLock(); }
  const value = JSON.parse(Buffer.concat(chunks).toString('utf8'));
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error();
  return value;
}
export async function authRequest(request: Request) {
  try {
    const config = authEnvironment(); const url = new URL(request.url);
    const operation = url.pathname;
    if (url.search || !['/api/auth/sign-in/email','/api/auth/sign-out','/api/auth/get-session'].includes(operation)) return response({ error: 'NOT_FOUND' }, 404);
    const expected = operation.endsWith('get-session') ? 'GET' : 'POST';
    if (request.method !== expected) return response({ error: 'METHOD_NOT_ALLOWED' }, 405);
    if (request.headers.get('sec-fetch-site') === 'cross-site' || (expected === 'POST' && request.headers.get('origin') !== config.origin)) return response({ error: 'ORIGIN_REJECTED' }, 403);
    let data: Record<string, unknown> = {};
    if (expected === 'POST') {
      try { data = await body(request); } catch { return response({ error: 'INPUT_REJECTED' }, 400); }
      if (operation.endsWith('sign-in/email')) {
        if (!allowLogin()) { const out = response({ error: 'RATE_LIMITED' },429); out.headers.set('Retry-After','60'); return out; }
        if (Object.keys(data).some(k => !['email','password','rememberMe','callbackURL'].includes(k)) || typeof data.email !== 'string' || data.email.length > 254 || !validPassword(data.password) || (data.rememberMe !== undefined && typeof data.rememberMe !== 'boolean') || (data.callbackURL !== undefined && data.callbackURL !== '/auth-check')) return response({ error: 'INPUT_REJECTED' },400);
        data = { email: data.email.trim().toLowerCase(), password: data.password, rememberMe: false, callbackURL: '/auth-check' };
      } else if (Object.keys(data).length) return response({ error: 'INPUT_REJECTED' },400);
    }
    const headers = new Headers(request.headers);
    for (const key of [...headers.keys()]) if (key.startsWith('x-forwarded-') || key === 'forwarded' || key === 'x-real-ip') headers.delete(key);
    headers.delete('content-length'); headers.set('host',new URL(config.origin).host);
    const forwarded = new Request(config.origin + operation, { method: expected, headers, ...(expected === 'POST' ? {body: JSON.stringify(data)} : {}) });
    const result = await getAuth().handler(forwarded);
    if (result.status >= 500) return response({ error: 'AUTH_UNAVAILABLE' },503);
    if (!result.ok) return response({ error: result.status === 429 ? 'RATE_LIMITED' : 'AUTH_REJECTED' },result.status);
    const json = await result.json();
    const out = response(operation.endsWith('get-session') ? (json ? {user: {id: json.user.id, role: json.user.role}, expiresAt: json.session.expiresAt} : null) : { success: true });
    for (const cookie of result.headers.getSetCookie()) out.headers.append('set-cookie',cookie);
    return out;
  } catch { return response({ error: 'AUTH_UNAVAILABLE' },503); }
}
export async function probe(request: Request, admin = false) {
  try {
    const user = await identity(request.headers);
    if (!user) return response({ error: 'UNAUTHORIZED' },401);
    if (admin && user.role !== 'admin') return response({ error: 'FORBIDDEN' },403);
    return response({ user });
  } catch { return response({ error: 'AUTH_UNAVAILABLE' },503); }
}
