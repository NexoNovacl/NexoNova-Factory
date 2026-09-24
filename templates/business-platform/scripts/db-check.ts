import { runtimeClient } from '../src/server/db.js';
const mode=process.argv[2];
(async()=>{const db=runtimeClient();
 try{
  const roles=await db.$queryRaw<Array<{current_user:string}>>`SELECT current_user`;
  if(roles[0].current_user!=='bpruntime')throw new Error('Wrong role');
  if(mode==='write')await db.technicalSmoke.create({data:{id:'p43-smoke',marker:'synthetic-persistence'}});
  else if(mode==='read') {const row=await db.technicalSmoke.findUnique({where:{id:'p43-smoke'}});if(row?.marker!=='synthetic-persistence')throw new Error('Persistence missing');}
  else throw new Error('Unsupported smoke operation');
  console.log(JSON.stringify({status:'PASS',operation:mode,role:'bpruntime'}));
 }finally{await db.$disconnect();}
})().catch(()=>{console.error('DB_CHECK_FAILED; details withheld');process.exitCode=1;});
