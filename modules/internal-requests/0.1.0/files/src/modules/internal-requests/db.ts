import {PrismaPg} from '@prisma/adapter-pg';
import {PrismaClient} from '../../generated/requests/client.js';
import {authEnvironment} from '../../server/policy.js';
let client: PrismaClient | undefined;
export function requestsDb() {
  return client ??= new PrismaClient({adapter:new PrismaPg({connectionString:authEnvironment().database,max:5,connectionTimeoutMillis:3000,statement_timeout:5000},{schema:'app'})});
}
