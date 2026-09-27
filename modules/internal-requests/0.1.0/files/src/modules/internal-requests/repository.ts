import {randomUUID} from 'node:crypto';
import {requestsDb} from './db.js';
import {scope,type Actor} from './authorization.js';
import {dto} from './dto.js';
import {RequestError,missing,type Create,type Command,type Page} from './validation.js';
export async function insert(actor: Actor, input: Create) {
  scope(actor);
  const now=new Date();
  return dto(await requestsDb().internalRequest.create({data:{id:randomUUID(),title:input.title,description:input.description,status:'open',ownerId:actor.id,createdAt:now,updatedAt:now,archivedAt:null,version:1}}));
}
export async function detail(actor: Actor,id: string) {
  const row=await requestsDb().internalRequest.findFirst({where:{id,...scope(actor)}});
  return row ? dto(row) : missing();
}
export async function list(actor: Actor,page: Page) {
  const cursor=page.cursor;
  const rows=await requestsDb().internalRequest.findMany({where:{...scope(actor),...(cursor?{OR:[{createdAt:{gt:cursor.createdAt}},{createdAt:cursor.createdAt,id:{gt:cursor.id}}]}:{})},orderBy:[{createdAt:'asc'},{id:'asc'}],take:page.limit+1});
  const items=rows.slice(0,page.limit).map(dto);const last=items.at(-1);
  return {items,nextCursor:rows.length>page.limit&&last?Buffer.from(JSON.stringify({createdAt:last.createdAt,id:last.id})).toString('base64url'):null};
}
export async function mutate(actor: Actor,id: string,command: Command) {
  const visible={id,...scope(actor)};
  return requestsDb().$transaction(async tx=>{
    const now=new Date();
    const state=command.action==='close'?{status:'open' as const}:command.action==='reopen'?{status:'closed' as const}:{};
    const change=command.action==='edit'?{title:command.title,description:command.description}:command.action==='close'?{status:'closed' as const}:command.action==='reopen'?{status:'open' as const}:{archivedAt:now};
    const result=await tx.internalRequest.updateMany({where:{...visible,...state,version:{equals:command.expectedVersion,lt:2147483647}},data:{...change,version:{increment:1},updatedAt:now}});
    if (result.count!==1) {
      const exists=await tx.internalRequest.findFirst({where:visible,select:{id:true}});
      if (!exists) return missing();
      throw new RequestError(409,'OPERATION_CONFLICT');
    }
    if(command.action==='archive') return null;
    const row=await tx.internalRequest.findFirst({where:visible});
    if(!row) throw new Error('Transaction invariant');
    return dto(row);
  },{isolationLevel:'ReadCommitted',maxWait:3000,timeout:5000});
}
