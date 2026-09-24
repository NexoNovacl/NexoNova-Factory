import {spawnSync} from 'node:child_process';
try {
 const value=process.env.MIGRATION_DATABASE_URL;if(!value)throw Error();
 const url=new URL(value);if(url.protocol!=='postgresql:'||decodeURIComponent(url.username)!=='bpmigrator')throw Error();
 const result=spawnSync(process.execPath,['node_modules/prisma/build/index.js','migrate','deploy'],{stdio:'inherit'});
 process.exitCode=result.status??1;
} catch {console.error('MIGRATION_ENV_REJECTED; values withheld');process.exitCode=2;}
