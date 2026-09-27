export class RequestError extends Error {
  constructor(public status: number, public code: string) { super(code); }
}
export const reject = (): never => { throw new RequestError(400, 'INPUT_REJECTED'); };
export const missing = (): never => { throw new RequestError(404, 'RESOURCE_NOT_FOUND'); };
export function exact(value: unknown, keys: string[]): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return reject();
  const object = value as Record<string, unknown>;
  if (Object.keys(object).length !== keys.length || keys.some(k => !Object.hasOwn(object, k))) return reject();
  return object;
}
function text(value: unknown, min: number, max: number): string {
  if (typeof value !== 'string') return reject();
  const points = [...value];
  if (points.length < min || points.length > max || points.some(c => { const n=c.codePointAt(0)!; return n === 0 || (n >= 0xd800 && n <= 0xdfff); })) return reject();
  if (min && !value.trim()) return reject();
  return value;
}
export type Create = {title: string; description: string};
export type Command = ({action: 'edit'; expectedVersion: number} & Create) | {action: 'close'|'reopen'|'archive'; expectedVersion: number};
export function createInput(value: unknown): Create {
  const o=exact(value,['title','description']);
  return {title:text(o.title,1,120), description:text(o.description,0,2000)};
}
export function commandInput(value: unknown): Command {
  if (!value || typeof value !== 'object') return reject();
  const action=(value as Record<string,unknown>).action;
  if (!['edit','close','reopen','archive'].includes(action as string)) return reject();
  const o=exact(value,action==='edit'?['action','expectedVersion','title','description']:['action','expectedVersion']);
  if (typeof o.expectedVersion !== 'number' || !Number.isInteger(o.expectedVersion) || o.expectedVersion < 1 || o.expectedVersion > 2147483647) return reject();
  if (action==='edit') return {action, expectedVersion:o.expectedVersion, ...createInput({title:o.title,description:o.description})};
  return {action:action as 'close'|'reopen'|'archive',expectedVersion:o.expectedVersion};
}
export const validId = (id: string) => /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(id);
export function resourceId(id: string) { if (!validId(id)) return missing(); return id; }
export type Page = {limit: number; cursor?: {createdAt: Date; id: string}};
export function pageInput(params: URLSearchParams): Page {
  const keys=[...params.keys()];
  if (keys.some(k=> !['limit','cursor'].includes(k)) || new Set(keys).size!==keys.length) return reject();
  const raw=params.get('limit') ?? '20';
  if (!/^[1-9][0-9]{0,2}$/.test(raw) || Number(raw)>100) return reject();
  const result: Page={limit:Number(raw)};
  if (params.has('cursor')) {
    const cursor=params.get('cursor')!;
    if (!/^[A-Za-z0-9_-]{1,256}$/.test(cursor)) return reject();
    try {
      const bytes=Buffer.from(cursor,'base64url');
      if (bytes.toString('base64url')!==cursor) return reject();
      const o=exact(JSON.parse(bytes.toString('utf8')),['createdAt','id']);
      if (typeof o.createdAt!=='string' || typeof o.id!=='string' || !validId(o.id)) return reject();
      const date=new Date(o.createdAt);
      if (!Number.isFinite(date.getTime()) || date.toISOString()!==o.createdAt) return reject();
      result.cursor={createdAt:date,id:o.id};
    } catch { return reject(); }
  }
  return result;
}
