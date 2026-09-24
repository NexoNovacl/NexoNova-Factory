import { spawn } from 'node:child_process';
import { authEnvironment } from '../build-checks/src/server/policy.js';
try { authEnvironment(); } catch { console.error('AUTH_ENV_REJECTED'); process.exit(2); }
const app = spawn(process.execPath, ['node_modules/next/dist/bin/next', 'start', '--hostname', '0.0.0.0'], { stdio: 'inherit' });
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => app.kill(signal));
app.on('exit', (code, signal) => process.exit(code ?? (signal === 'SIGINT' ? 130 : 143)));
