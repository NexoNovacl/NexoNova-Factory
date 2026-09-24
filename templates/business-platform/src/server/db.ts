import { PrismaClient } from '../generated/prisma/client.js';
import { PrismaPg } from '@prisma/adapter-pg';
export function runtimeClient(){
 const value=process.env.DATABASE_URL;
 if(!value) throw new Error('DATABASE_URL required; value withheld');
 const url=new URL(value);
 if(url.protocol!=='postgresql:'||decodeURIComponent(url.username)!=='bpruntime')throw new Error('Runtime role configuration rejected');
 return new PrismaClient({adapter:new PrismaPg({connectionString:value,connectionTimeoutMillis:2000},{schema:'app'})});
}
