import { defineConfig } from 'prisma/config';
// Offline generation needs no DB URL; migrate is gated by the operator harness.
export default defineConfig({schema:'validation/prisma/schema.prisma',migrations:{path:'validation/prisma/migrations'},datasource:{url:process.env.MIGRATION_DATABASE_URL}});
