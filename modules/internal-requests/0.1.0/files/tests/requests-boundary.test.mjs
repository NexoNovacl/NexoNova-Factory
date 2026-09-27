import {test} from 'node:test';import assert from 'node:assert/strict';
import {isRequestsPath,mergeVary} from '../scripts/requests-response-boundary.mjs';
test('module boundary namespaces only',()=>{for(const path of ['/requests','/requests/id','/api/requests?x=1','/%72equests/id'])assert.equal(isRequestsPath(path),true);for(const path of ['/login','/api/auth/get-session','/requests-other','/auth-check'])assert.equal(isRequestsPath(path),false);});
test('Vary union preserves framework tokens without duplicates',()=>{assert.equal(mergeVary(['rsc, Cookie','RSC, Accept-Encoding']),'rsc, Cookie, Accept-Encoding');assert.equal(mergeVary(undefined),'Cookie');assert.throws(()=>mergeVary('*'));});
