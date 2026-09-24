import { test } from 'node:test';
import assert from 'node:assert/strict';
import { randomBytes } from 'node:crypto';
import { authEnvironment, boundedExpiry, validPassword, SESSION_SECONDS } from '../build-checks/src/server/policy.js';
function env() { return {AUTH_PRODUCT_ID:'synthetic-auth',BETTER_AUTH_SECRET:randomBytes(32).toString('hex'),BETTER_AUTH_URL:'http://127.0.0.1:3100',AUTH_PROFILE:'local-test',DATABASE_URL:`postgresql://bpruntime:${randomBytes(24).toString('hex')}@db/test?schema=app`}; }
test('local profile is explicit; production requires HTTPS',()=>{
 const e=env();assert.equal(authEnvironment(e).secure,false);
 assert.throws(()=>authEnvironment({...e,AUTH_PROFILE:'production'}));
 assert.equal(authEnvironment({...e,AUTH_PROFILE:'production',BETTER_AUTH_URL:'https://auth.example.invalid'}).secure,true);
 for(const bad of ['http://localhost:3100','http://example.invalid','https://127.0.0.1','http://127.0.0.1/path','http://127.0.0.1/?x=1'])assert.throws(()=>authEnvironment({...e,BETTER_AUTH_URL:bad}));
});
test('required environment and role fail closed',()=>{
 const e=env();for(const key of Object.keys(e)) {const copy={...e};delete copy[key];assert.throws(()=>authEnvironment(copy));}
 assert.throws(()=>authEnvironment({...e,BETTER_AUTH_SECRET:'short'}));
 assert.throws(()=>authEnvironment({...e,DATABASE_URL:e.DATABASE_URL.replace('bpruntime','bpmigrator')}));
});
test('session clamp never extends shorter expiry and caps 24h',()=>{
 const now=Date.now(),created=new Date(now);
 assert.equal(boundedExpiry(created,new Date(now+86400000),now).getTime()-now,SESSION_SECONDS*1000);
 assert.equal(boundedExpiry(created,new Date(now+1000),now).getTime()-now,1000);
 assert.throws(()=>boundedExpiry(new Date(NaN),created,now));
});
test('password bounds match JavaScript UTF-16 semantics without trimming',()=>{
 assert.equal(validPassword('a'.repeat(14)),false);assert.equal(validPassword('a'.repeat(15)),true);
 assert.equal(validPassword('á'.repeat(128)),true);assert.equal(validPassword('á'.repeat(129)),false);
 assert.equal(validPassword('🔐'.repeat(64)),true);assert.equal(validPassword('🔐'.repeat(65)),false);
 assert.equal(validPassword(null),false);
});
