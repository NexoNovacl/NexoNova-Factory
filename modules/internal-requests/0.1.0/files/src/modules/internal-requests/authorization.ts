import {RequestError} from './validation.js';
export type Actor = {id: string; role: string};
export function scope(actor: Actor) {
  if (!actor || !actor.id || !['member','admin'].includes(actor.role)) throw new RequestError(401,'UNAUTHORIZED');
  return actor.role==='admin' ? {archivedAt:null} : {archivedAt:null,ownerId:actor.id};
}
