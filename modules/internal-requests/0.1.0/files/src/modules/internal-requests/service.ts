import {scope,type Actor} from './authorization.js';
import {createInput,commandInput,pageInput,resourceId} from './validation.js';
import * as repository from './repository.js';
export function createRequest(actor: Actor,input: unknown) {scope(actor);return repository.insert(actor,createInput(input));}
export function listRequests(actor: Actor,params: URLSearchParams) {scope(actor);return repository.list(actor,pageInput(params));}
export function getRequest(actor: Actor,id: string) {scope(actor);return repository.detail(actor,resourceId(id));}
export function changeRequest(actor: Actor,id: string,input: unknown) {scope(actor);const command=commandInput(input);return repository.mutate(actor,resourceId(id),command);}
