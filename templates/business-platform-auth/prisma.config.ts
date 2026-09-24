import { defineConfig } from "prisma/config";
export default defineConfig({ schema: "prisma/auth/schema.prisma", migrations: { path: "prisma/auth/migrations" }, datasource: { url: process.env.MIGRATION_DATABASE_URL } });
