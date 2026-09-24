const { spawnSync } = await import('node:child_process');
try {
  const url = new URL(process.env.MIGRATION_DATABASE_URL || '');
  if (url.username !== 'bpmigrator' || !url.password) throw new Error();
} catch { console.error('MIGRATION_ENV_REJECTED'); process.exit(2); }
const result = spawnSync(process.execPath, ['node_modules/prisma/build/index.js', 'migrate', 'deploy'], { stdio: 'inherit' });
process.exit(result.status ?? 1);
