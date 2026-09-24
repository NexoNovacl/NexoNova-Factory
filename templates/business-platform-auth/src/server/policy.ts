export const SESSION_SECONDS = 8 * 60 * 60;
export function validPassword(value: unknown): value is string {
  return typeof value === "string" && value.length >= 15 && value.length <= 128;
}
export function boundedExpiry(created: Date, requested: Date, now = Date.now()): Date {
  const start = created.getTime(), end = requested.getTime();
  if (!Number.isFinite(start) || !Number.isFinite(end) || start > now + 1000) throw new Error("SESSION_DATE_REJECTED");
  return new Date(Math.min(end, start + SESSION_SECONDS * 1000, now + SESSION_SECONDS * 1000));
}
export function authEnvironment(env: NodeJS.ProcessEnv = process.env) {
  const fail = (): never => { throw new Error("AUTH_ENV_REJECTED"); };
  const productId = env.AUTH_PRODUCT_ID;
  if (!productId || !/^[a-z][a-z0-9-]{2,48}$/.test(productId)) return fail();
  const secret = env.BETTER_AUTH_SECRET;
  if (!secret || Buffer.byteLength(secret) < 32) return fail();
  let origin: URL, database: URL;
  try { origin = new URL(env.BETTER_AUTH_URL || ""); database = new URL(env.DATABASE_URL || ""); } catch { return fail(); }
  if (origin.username || origin.password || origin.pathname !== "/" || origin.search || origin.hash) return fail();
  if (!['postgres:', 'postgresql:'].includes(database.protocol) || database.username !== 'bpruntime' || !database.password) return fail();
  const profile = env.AUTH_PROFILE;
  if (profile !== 'production' && profile !== 'local-test') return fail();
  if (profile === 'production' && origin.protocol !== 'https:') return fail();
  if (profile === 'local-test' && (origin.protocol !== 'http:' || origin.hostname !== '127.0.0.1')) return fail();
  return { productId, secret, origin: origin.origin, database: database.toString(), secure: profile === 'production' };
}
