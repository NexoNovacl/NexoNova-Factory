# Business Platform technical core 0.1.0

P4.3 experimental core: Next App Router, React, TypeScript, CSS Modules and Prisma 7/PostgreSQL 16. No authentication, application users, business module or generated product exists yet. Better Auth is deliberately absent.

Exact dependencies live in package.json/package-lock.json; Docker images are digest pinned in compose.yaml. Use Node 22.23.2 for the validated matrix. Separate preparation from offline execution:

```sh
npm ci --ignore-scripts --no-audit --no-fund
node node_modules/@prisma/engines/dist/scripts/postinstall.js
npm run generate
npm run typecheck
npm test
npm run compile:checks
npm run build
```

Only dependency/engine preparation downloads packages. Never use credentials or real data for this fixture. `npm run migrate` separately requires MIGRATION_DATABASE_URL with the provisioned bpmigrator login; runtime requires DATABASE_URL with bpruntime. The database must first have schema app owned by bpmigrator and least-privilege grants for bpruntime. The controlled infrastructure experiment provisions these; Compose up deliberately does not.

`validation/prisma` is a synthetic TechnicalSmoke schema and fixed migration history for infrastructure tests, not the final business schema. `validation/runtime-grants.sql` grants only usage/CRUD on that table, not DDL or migration history. Do not automatically include the fixture in future generated products. No reset/db push/automatic startup migration is provided.

Compose requires externally supplied COMPOSE_PROJECT_NAME, APP_UID, APP_GID, POSTGRES_DB, POSTGRES_ADMIN_PASSWORD and DATABASE_URL. Never commit their values. Use a unique namespace and disposable volume. First prepare volume ownership with `docker compose --profile prepare run --rm volume-init`, then `docker compose up -d db`; provision technical connection roles securely, migrate separately, then `docker compose up -d app`. Dependencies/client/build must already exist in this project. The app mount is readonly; DB has no published port; neither service gets external network connectivity. No public app port is published. This is a local prepared-project Compose base, not a production distribution image.

The app receives no migration/admin credential. SIGKILL/host/daemon failure can require manual inspection and cleanup of the exact run resources. Do not use global prune. Sessions, resource authorization, internal-requests and product generation remain future gates, not validated capabilities.
