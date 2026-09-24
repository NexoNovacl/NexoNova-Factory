import { hashPassword } from "better-auth/crypto";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "../src/generated/auth/client.js";
import { randomUUID } from "node:crypto";
import { validPassword } from "../src/server/policy.js";
let db: PrismaClient | undefined;
try {
  process.stdin.setEncoding("utf8");
  let text = '';
  for await (const chunk of process.stdin) { text += chunk; if (Buffer.byteLength(text) > 4096) throw new Error(); }
  const data = JSON.parse(text);
  if (Object.keys(data).sort().join(',') !== 'database,email,name,password' || typeof data.email !== 'string' || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email) || data.email.length > 254 || typeof data.name !== 'string' || !data.name.trim() || data.name.length > 100 || !validPassword(data.password)) throw new Error();
  const url = new URL(process.env.BOOTSTRAP_DATABASE_URL || '');
  if (url.username !== 'bpbootstrap' || !url.password || decodeURIComponent(url.pathname.slice(1)) !== data.database) throw new Error();
  db = new PrismaClient({ adapter: new PrismaPg({ connectionString: url.toString() }, { schema: 'app' }) });
  const email = data.email.trim().toLowerCase();
  const hash = await hashPassword(data.password);
  const result = await db.$transaction(async tx => {
    await tx.$executeRaw`SELECT pg_advisory_xact_lock(442004)`;
    const users = await tx.user.findMany({ include: { accounts: true } });
    if (users.length) {
      const user = users.find(u => u.email === email);
      if (user?.role === 'admin' && user.accounts.some(a => a.providerId === 'credential' && a.accountId === user.id && a.password)) return 'ALREADY_INITIALIZED';
      throw new Error();
    }
    if (await tx.account.count()) throw new Error();
    const id = randomUUID();
    await tx.user.create({ data: { id, email, name: data.name.trim(), role: 'admin', emailVerified: false } });
    await tx.account.create({ data: { id: randomUUID(), userId: id, accountId: id, providerId: 'credential', password: hash } });
    return 'CREATED';
  });
  console.log(result);
} catch { console.error('BOOTSTRAP_REJECTED'); process.exitCode = 1; }
finally { await db?.$disconnect(); }
