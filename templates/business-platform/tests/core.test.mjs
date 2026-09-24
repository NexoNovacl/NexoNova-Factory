import {test} from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
test('technical schema has no auth or business model',()=>{const s=readFileSync('validation/prisma/schema.prisma','utf8');assert.deepEqual([...s.matchAll(/^model (\w+)/gm)].map(x=>x[1]),['TechnicalSmoke']);});
test('initial migration is fixed and contains no role credentials',()=>{const s=readFileSync('validation/prisma/migrations/00000000000000_technical_smoke/migration.sql','utf8');assert.match(s,/CREATE TABLE/);assert.doesNotMatch(s,/PASSWORD|CURRENT_TIMESTAMP|InternalRequest/);});
