import { betterAuth } from "better-auth";
import { prismaAdapter } from "better-auth/adapters/prisma";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "../generated/auth/client.js";
import { authEnvironment, boundedExpiry, SESSION_SECONDS } from "./policy.js";
function createAuth() {
  const config = authEnvironment();
  const db = new PrismaClient({ adapter: new PrismaPg({ connectionString: config.database }, { schema: "app" }) });
  return betterAuth({
    database: prismaAdapter(db, { provider: "postgresql" }),
    secret: config.secret, baseURL: config.origin, trustedOrigins: [config.origin],
    telemetry: { enabled: false }, logger: { disabled: true },
    emailAndPassword: { enabled: true, disableSignUp: true, autoSignIn: false, minPasswordLength: 15, maxPasswordLength: 128 },
    user: { additionalFields: { role: { type: ["admin", "member"], required: true, defaultValue: "member", input: false } } },
    session: { expiresIn: SESSION_SECONDS, disableSessionRefresh: true, cookieCache: { enabled: false } },
    databaseHooks: { session: { create: { before: async (session) => ({ data: { ...session, expiresAt: boundedExpiry(session.createdAt, session.expiresAt) } }) } } },
    advanced: { cookiePrefix: config.productId, useSecureCookies: config.secure,
      defaultCookieAttributes: { httpOnly: true, secure: config.secure, sameSite: "lax", path: "/" },
      ipAddress: { disableIpTracking: true } },
    rateLimit: { enabled: true, storage: "memory", window: 60, max: 100,
      customRules: { "/sign-in/email": { window: 60, max: 5 } } },
  });
}
let auth: ReturnType<typeof createAuth> | undefined;
export function getAuth() { return auth ??= createAuth(); }
export async function identity(headers: Headers) {
  const data = await getAuth().api.getSession({ headers });
  if (!data) return null;
  const now = Date.now();
  if (data.session.expiresAt.getTime() <= now || now - data.session.createdAt.getTime() >= SESSION_SECONDS * 1000) return null;
  if (data.user.role !== 'admin' && data.user.role !== 'member') return null;
  return { id: data.user.id, name: data.user.name, role: data.user.role };
}
