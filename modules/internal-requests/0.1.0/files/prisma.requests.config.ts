import { defineConfig } from "prisma/config";
export default defineConfig({ schema: "prisma/business/schema.prisma", migrations: { path: "prisma/business/migrations" }, datasource: { url: process.env.MIGRATION_DATABASE_URL } });
