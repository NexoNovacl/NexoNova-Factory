// Test-only fixture: never imported by app, no HTTP entry point.
import { hashPassword } from 'better-auth/crypto';
import { PrismaPg } from '@prisma/adapter-pg';
import { PrismaClient } from '../src/generated/auth/client.js';
import { randomUUID } from 'node:crypto';
import { validPassword } from '../src/server/policy.js';
let db: PrismaClient | undefined;
try {
  process.stdin.setEncoding("utf8");
 let input=''; for await(const chunk of process.stdin) {input+=chunk;if(input.length>4096)throw new Error();}
 const data=JSON.parse(input); if(!validPassword(data.password)||data.email!=='member@example.invalid')throw new Error();
 const url=new URL(process.env.BOOTSTRAP_DATABASE_URL||'');if(url.username!=='bpbootstrap'||url.pathname.slice(1)!==data.database)throw new Error();
 db=new PrismaClient({adapter:new PrismaPg({connectionString:url.toString()},{schema:'app'})});
 const hash=await hashPassword(data.password),id=randomUUID();
 await db.$transaction(async tx=>{await tx.user.create({data:{id,name:'Synthetic Member',email:data.email,role:'member'}});await tx.account.create({data:{id:randomUUID(),userId:id,accountId:id,providerId:'credential',password:hash}});});
 console.log('SYNTHETIC_MEMBER_CREATED');
} catch {console.error('FIXTURE_REJECTED');process.exitCode=1;} finally {await db?.$disconnect();}
