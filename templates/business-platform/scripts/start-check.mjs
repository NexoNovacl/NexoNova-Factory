import {spawn} from 'node:child_process';
const child=spawn(process.execPath,['node_modules/next/dist/bin/next','start','--hostname','127.0.0.1','--port','3191'],{stdio:'ignore'});
try{let response;for(let i=0;i<80;i++){try{response=await fetch('http://127.0.0.1:3191');break}catch{await new Promise(r=>setTimeout(r,100));}}
if(!response?.ok||!(await response.text()).includes('Base técnica experimental'))throw Error('Core startup failed');console.log('CORE_HTTP_PASS');
}finally{if(child.exitCode===null&&child.signalCode===null){const ended=new Promise(r=>child.once('exit',r));child.kill('SIGTERM');await ended;}}
