// Own HTTP response boundary: no framework patches and no global prototype mutation.
export function isRequestsPath(url) {
  try { const path=decodeURIComponent(new URL(url,'http://localhost').pathname);return /^\/(?:api\/)?requests(?:\/|$)/.test(path); } catch { return false; }
}
export function mergeVary(value) {
  const tokens=(Array.isArray(value)?value.join(','):String(value??'')).split(',').map(x=>x.trim()).filter(Boolean);
  // '*' already varies on every request field; combining it with field names is invalid.
  if(tokens.includes('*')) throw new Error('UNSUPPORTED_VARY_WILDCARD');
  const seen=new Set();return [...tokens,'Cookie'].filter(token=>{const key=token.toLowerCase();if(seen.has(key))return false;seen.add(key);return true;}).join(', ');
}
export function requestsResponseBoundary(request,response) {
  if(!isRequestsPath(request.url??'/'))return;
  const writeHead=response.writeHead;
  response.writeHead=function(statusCode,statusMessage,headers) {
    const supplied=typeof statusMessage==='string'?headers:statusMessage;
    if(Array.isArray(supplied)){for(let i=0;i<supplied.length;i+=2)this.setHeader(supplied[i],supplied[i+1]);}
    else if(supplied){for(const [key,value] of Object.entries(supplied))this.setHeader(key,value);}
    this.setHeader('Vary',mergeVary(this.getHeader('Vary')));
    this.setHeader('Cache-Control','no-store');
    return typeof statusMessage==='string'?writeHead.call(this,statusCode,statusMessage):writeHead.call(this,statusCode);
  };
}
