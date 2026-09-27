import {handle} from "../../../../modules/internal-requests/http.js";
export const dynamic="force-dynamic";
export const runtime="nodejs";
export async function GET(request: Request, context: {params: Promise<{id:string}>}) {return handle(request,(await context.params).id);}
export async function POST(request: Request, context: {params: Promise<{id:string}>}) {return handle(request,(await context.params).id);}
export async function PATCH(request: Request, context: {params: Promise<{id:string}>}) {return handle(request,(await context.params).id);}
export async function PUT(request: Request, context: {params: Promise<{id:string}>}) {return handle(request,(await context.params).id);}
export async function DELETE(request: Request, context: {params: Promise<{id:string}>}) {return handle(request,(await context.params).id);}
export async function HEAD(request: Request, context: {params: Promise<{id:string}>}) {return handle(request,(await context.params).id);}
export async function OPTIONS(request: Request, context: {params: Promise<{id:string}>}) {return handle(request,(await context.params).id);}
