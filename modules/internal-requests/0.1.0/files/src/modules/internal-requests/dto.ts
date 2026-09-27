export type RequestRow = {id:string;title:string;description:string;status:string;ownerId:string;createdAt:Date;updatedAt:Date;archivedAt:Date|null;version:number};
export function dto(row: RequestRow) {
  return {id:row.id,title:row.title,description:row.description,status:row.status,ownerId:row.ownerId,createdAt:row.createdAt.toISOString(),updatedAt:row.updatedAt.toISOString(),archivedAt:row.archivedAt?.toISOString()??null,version:row.version};
}
export type RequestDto = ReturnType<typeof dto>;
