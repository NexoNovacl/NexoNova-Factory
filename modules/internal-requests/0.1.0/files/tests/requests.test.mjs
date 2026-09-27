import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createInput,commandInput,pageInput,resourceId} from '../build-checks/src/modules/internal-requests/validation.js';
import {scope} from '../build-checks/src/modules/internal-requests/authorization.js';
test('strict input and Unicode scalar limits',()=>{
  assert.equal(createInput({title:'🔐'.repeat(120),description:''}).title.length,240);
  for(const title of ['', ' ', 'a'.repeat(121),'\u0000','\ud800'])assert.throws(()=>createInput({title,description:''}));
  for(const key of ['ownerId','userId','role','version','status','archivedAt','constructor','__proto__'])assert.throws(()=>createInput(JSON.parse(`{"title":"ok","description":"","${key}":"spoof"}`)));
  assert.throws(()=>createInput({title:'ok',description:'a'.repeat(2001)}));
});
test('commands and versions are closed',()=>{
  for(const action of ['edit','close','reopen','archive'])assert.equal(commandInput({action,expectedVersion:1,...(action==='edit'?{title:'ok',description:''}:{})}).action,action);
  for(const expectedVersion of [0,-1,1.2,'1',2147483648,null])assert.throws(()=>commandInput({action:'close',expectedVersion}));
  assert.throws(()=>commandInput({action:'delete',expectedVersion:1}));
});
test('pagination and identifiers reject coercion',()=>{
  assert.equal(pageInput(new URLSearchParams()).limit,20);
  for(const query of ['limit=0','limit=101','limit=01','limit=2&limit=3','offset=0','cursor=','cursor=!!!'])assert.throws(()=>pageInput(new URLSearchParams(query)));
  assert.throws(()=>resourceId('1 OR 1=1'));
});
test('unknown and absent actors deny by default',()=>{
  for(const actor of [null,{id:'u',role:'ADMIN'},{id:'u',role:'unknown'},{id:'',role:'admin'}])assert.throws(()=>scope(actor));
  assert.deepEqual(scope({id:'u',role:'member'}),{archivedAt:null,ownerId:'u'});
  assert.deepEqual(scope({id:'a',role:'admin'}),{archivedAt:null});
});
