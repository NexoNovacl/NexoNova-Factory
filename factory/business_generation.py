"""Pure in-memory generation plan. There is intentionally no materializer here."""
from __future__ import annotations
from .business_execution_contracts import (ROOT, LAUNCHER, canonical, contract, digest,
    loads, object_hash, path_set, read_relative, require)
from .business_execution_inventory import adapt, DESCRIPTOR

CODE_PATHS = ('factory/business_execution_contracts.py', 'factory/business_execution_inventory.py',
              'factory/business_generation.py', 'factory/business_execution_authority.py',
              'factory/business_generation_evidence.py')
SCHEMA_NAMES = ('business-execution-inventory', 'business-route-adaptation', 'public-business-generation',
                'business-composition', 'business-generation-plan', 'business-generation-manifest',
                'business-generation-metadata', 'business-generation-validation',
                'business-execution-work-order', 'business-execution-authorization')


def tree_hash(root, paths):
    return object_hash([{'path':p, 'sha256':digest(read_relative(root,p))} for p in sorted(paths)])


def plan(spec, root=ROOT):
    contract('public-business-generation.v1', spec)
    descriptor, sources, inventory, adaptation = adapt(root)
    payload, records = {}, {}
    def add(path, raw, owner, source, transform):
        require(path not in payload, 'output collision')
        payload[path] = raw
        records[path] = {'path':path, 'sha256':digest(raw), 'bytes':len(raw), 'owner':owner,
                         'provenance':{'source':source,'transform':transform}}
    for row in descriptor['files']:
        add(row['destination'], sources[row['source']], row['owner'], row['source'], 'copy-bytes.v1')
    original = payload['prisma/auth/schema.prisma'].decode('utf-8')
    require(original.count('../../src/generated/auth') == 1, 'Prisma generation marker changed')
    combined = (original.replace('../../src/generated/auth','../../src/generated/requests') + '\n' +
                payload['prisma/modules/internal-requests.prisma'].decode('utf-8')).encode('utf-8')
    add('prisma/business/schema.prisma', combined, 'composition', DESCRIPTOR, 'business-schema.v1')
    for path, raw in sorted(list(payload.items())):
        for prefix in ('prisma/auth/migrations/', 'prisma/requests-migrations/'):
            if path.startswith(prefix):
                add('prisma/business/migrations/'+path[len(prefix):], raw,
                    'composition', path, 'business-migrations.v1')
    checks = loads(payload['tsconfig.checks.json'])
    extra = ['src/modules/internal-requests/**/*.ts','validation/requests-users.ts']
    require(not set(extra).intersection(checks['include']), 'unexpected checks configuration')
    checks['include'] += extra
    add('tsconfig.generation-checks.json', canonical(checks), 'composition',
        'tsconfig.checks.json', 'checks-config.v1')
    add('product-public.json', canonical({'productId':spec['productId'],'public':spec['public']}),
        'composition', 'public-spec', 'public-data.v1')
    guide = ('# '+spec['public']['name']+'\n\nGenerated candidate; runtime validation NOT_EXECUTED.\n'
             'Required start: node scripts/start-requests.mjs\n'
             'Do not use the auth-only npm start.\n'
             'Prisma: generate both clients; migrate deploy --config prisma.requests.config.ts separately.\n'
             'Checks: tsc -p tsconfig.generation-checks.json; npm test; npm run typecheck; npm run build.\n'
             'See factory-generation/metadata.json and inherited limitations; no deployment authority.\n')
    add('GENERATION.md', guide.encode('utf-8'), 'composition', 'public-spec', 'generation-guide.v1')
    add('factory-generation/inventory.json', canonical(inventory), 'composition', DESCRIPTOR, 'copy-bytes.v1')
    add('factory-generation/adaptation.json', canonical(adaptation), 'composition', DESCRIPTOR, 'copy-bytes.v1')
    path_set(payload)
    limitations = [inventory['sources']['approvedReceipt']]
    files = [records[p] for p in sorted(records)]
    code_hash = tree_hash(root, CODE_PATHS)
    schema_hash = tree_hash(root, ['schemas/'+x+'.v1.json' for x in SCHEMA_NAMES])
    result = {'format':'nexonova.business-generation-plan.v1','productId':spec['productId'],
              'profile':spec['profile'],'specHash':object_hash(spec), 'compositionHash':object_hash(descriptor),
              'inventoryHash':object_hash(inventory),'adaptationHash':object_hash(adaptation),
              'codeHash':code_hash,'schemaHash':schema_hash,'files':files,
              'limitations':limitations,'executionAuthority':'none'}
    contract('business-generation-plan.v1', result)
    manifest = {'format':'nexonova.business-generation-manifest.v1','productId':spec['productId'],
                'profile':spec['profile'],'planHash':object_hash(result),'specHash':object_hash(spec),
                'inventoryHash':object_hash(inventory),'adaptationHash':object_hash(adaptation),
                'generatorHash':code_hash,'files':files,'launcher':LAUNCHER.copy(),
                'migrations':[{'path':p,'sha256':digest(raw)} for p,raw in sorted(payload.items())
                              if p.startswith('prisma/business/migrations/')],
                'transforms':descriptor['transforms'],'limitations':limitations,
                'excludes':['factory-generation/manifest.json','factory-generation/metadata.json']}
    contract('business-generation-manifest.v1', manifest)
    metadata = {'format':'nexonova.business-generation-metadata.v1','productId':spec['productId'],
                'public':spec['public'],'profile':spec['profile'],'capability':'business-platform',
                'generationManifestHash':object_hash(manifest),'inventoryHash':object_hash(inventory),
                'adaptationHash':object_hash(adaptation),'versions':{'next':'15.5.25','prisma':'7.5.0','betterAuth':'1.7.5'},
                'launcher':LAUNCHER.copy(),'prismaConfig':'prisma.requests.config.ts','limitations':limitations,
                'validationState':'NOT_EXECUTED','executionAuthority':'none'}
    contract('business-generation-metadata.v1', metadata)
    payload['factory-generation/manifest.json'] = canonical(manifest)
    payload['factory-generation/metadata.json'] = canonical(metadata)
    return {'plan':result,'inventory':inventory,'adaptation':adaptation,
            'manifest':manifest,'metadata':metadata,'payload':payload}


def validate_bundle(bundle):
    """Independent consistency checks; does not attest runtime success or permit effects."""
    for key, name in [('plan','business-generation-plan'),('inventory','business-execution-inventory'),
                      ('adaptation','business-route-adaptation'),('manifest','business-generation-manifest'),
                      ('metadata','business-generation-metadata')]:
        contract(name+'.v1', bundle[key])
    p,m,meta = bundle['plan'],bundle['manifest'],bundle['metadata']
    payload = bundle['payload']
    path_set(payload)
    require(m['planHash'] == object_hash(p), 'plan hash mismatch')
    require(meta['generationManifestHash'] == object_hash(m), 'manifest hash mismatch')
    for obj in (p,m,meta):
        require(obj['inventoryHash'] == object_hash(bundle['inventory']), 'inventory binding mismatch')
        require(obj['adaptationHash'] == object_hash(bundle['adaptation']), 'adaptation binding mismatch')
        require(obj['productId'] == p['productId'], 'product binding mismatch')
    require(bundle['adaptation']['inventoryCanonicalSha256'] == object_hash(bundle['inventory']), 'adapter binding')
    require(p['files'] == m['files'], 'file lists differ')
    require(m['files'] == sorted(m['files'],key=lambda r:r['path']), 'file ordering')
    path_set([r['path'] for r in m['files']])
    expected = {r['path'] for r in m['files']} | set(m['excludes'])
    require(set(payload) == expected, 'payload missing/extra')
    for row in m['files']:
        require(digest(payload[row['path']]) == row['sha256'] and len(payload[row['path']]) == row['bytes'], 'payload altered')
    for key in ('manifest','metadata','inventory','adaptation'):
        require(payload['factory-generation/'+key+'.json'] == canonical(bundle[key]), 'contract bytes differ')
    # Schema/hash consistency alone cannot bless a self-consistently forged profile.
    from .business_execution_inventory import load_descriptor
    approved = load_descriptor()
    require(bundle['inventory'] == approved['inventory'] and
            bundle['adaptation'] == approved['adaptation'], 'unapproved inventory/adaptation')
    spec = {'format':'nexonova.public-business-generation.v1','productId':p['productId'],
            'public':meta['public'],'profile':p['profile'],
            'modules':[{'id':'internal-requests','version':'0.1.0'}],'executionAuthority':'none'}
    require(p['specHash'] == m['specHash'] == object_hash(spec), 'public spec mismatch')
    require(m['generatorHash'] == p['codeHash'] == tree_hash(ROOT,CODE_PATHS), 'generator provenance mismatch')
    require(p['schemaHash'] == tree_hash(ROOT,['schemas/'+n+'.v1.json' for n in SCHEMA_NAMES]), 'schema provenance mismatch')
    require(p['compositionHash'] == object_hash(approved), 'composition provenance mismatch')
    for row in approved['files']:
        require(digest(payload[row['destination']]) == row['sha256'], 'protected source bytes changed')
    require(m['transforms'] == approved['transforms'], 'unknown transform')
    require(m['limitations'] == p['limitations'] == meta['limitations'] ==
            [approved['inventory']['sources']['approvedReceipt']], 'limitations lost')
    migrations = [{'path':q,'sha256':digest(raw)} for q,raw in sorted(payload.items())
                  if q.startswith('prisma/business/migrations/')]
    require(m['migrations'] == migrations, 'migration inventory mismatch')
    # Recompute derived bytes to reject a rehashed arbitrary payload or removed file.
    expected = plan(spec)
    require(bundle == expected, 'planned derivation changed')
    return {'status':'PASS','scope':'pure bundle consistency','executionAuthority':'none'}
