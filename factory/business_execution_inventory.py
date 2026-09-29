"""Closed approved profile adapter. Read-only source inspection, no runtime execution."""
from __future__ import annotations
from copy import deepcopy
import re
from .business_execution_contracts import (ROOT, ContractError, contract, digest, loads,
    object_hash, path_set, read_relative, require)

DESCRIPTOR = 'config/business/compositions/business-auth-internal-requests-0.1.0-d02.json'
DESCRIPTOR_HASH = 'sha256:8d280c90dd2019d77165e77d25bb3f678c4d2d37c44dc6aa06a8bd5f8fc1048d'
SOURCE_ROOTS = ('templates/business-platform-auth', 'modules/internal-requests/0.1.0/files')


def pattern_tokens(pattern):
    require(type(pattern) is str and pattern.startswith('/'), 'invalid route')
    if pattern == '/':
        return []
    result = []
    for i, part in enumerate(pattern[1:].split('/')):
        if re.fullmatch('[a-z0-9-]+', part):
            result.append(part)
        elif re.fullmatch(r'\[[a-z][a-z0-9]*\]', part):
            result.append(':param')
        elif re.fullmatch(r'\[\.\.\.[a-z][a-z0-9]*\]', part):
            require(i == len(pattern[1:].split('/'))-1, 'non-terminal catchall')
            result.append(':catchall')
        else:
            raise ContractError('unsupported routing convention')
    return result


def intersects(left, right):
    """Intersection of literals/single parameters/terminal one-or-more catchalls."""
    a, b = pattern_tokens(left), pattern_tokens(right)
    i = 0
    while i < len(a) and i < len(b):
        x, y = a[i], b[i]
        if ':catchall' in (x, y):
            return True  # Both have a non-empty remaining suffix.
        if x != ':param' and y != ':param' and x != y:
            return False
        i += 1
    return len(a) == len(b)


def check_route_collisions(routes):
    seen = []
    for route in routes:
        p = route['pattern']
        pattern_tokens(p)
        require(not intersects(p, '/sign-in') and not intersects(p, '/sign-in/[...reserved]'),
                'reserved non-materializable sign-in subtree')
        # _next is outside permitted literal grammar as well as reserved.
        require(not p.startswith('/_next'), 'framework namespace')
        if intersects(p, '/api/auth') or intersects(p, '/api/auth/[...all]'):
            require(p == '/api/auth/[...all]' and route['owner'] == 'auth-core',
                    'reserved auth namespace')
        require(not any(intersects(p, other) for other in seen), 'route collision')
        seen.append(p)
    path_set([r['outputPath'] for r in routes])


def load_descriptor(root=ROOT):
    raw = read_relative(root, DESCRIPTOR)
    require(digest(raw) == DESCRIPTOR_HASH, 'closed descriptor changed')
    return contract('business-composition.v1', loads(raw))


def source_snapshot(root, descriptor):
    """The anchored map must equal the entire actual source tree; extras are not ignored."""
    expected = {x['source']: x['sha256'] for x in descriptor['files']}
    require(len(expected) == len(descriptor['files']), 'duplicate source')
    actual = set()
    for prefix in SOURCE_ROOTS:
        base = root / prefix
        require(base.is_dir() and not base.is_symlink(), 'missing/symlink source root')
        for p in base.rglob('*'):
            require(not p.is_symlink(), 'symlink source tree')
            if not p.is_dir():
                actual.add(p.relative_to(root).as_posix())
    require(actual == set(expected), 'source inventory extra/missing')
    result = {}
    for path, wanted in sorted(expected.items()):
        raw = read_relative(root, path)
        require(digest(raw) == wanted, 'source hash mismatch: ' + path)
        result[path] = raw
    for ref in descriptor['approvedReferences']:
        require(digest(read_relative(root, ref['path'])) == ref['sha256'], 'approval/reference mismatch')
    path_set([x['destination'] for x in descriptor['files']])
    return result


def validate_inventory(inventory, expected, source_bytes, root=ROOT):
    contract('business-execution-inventory.v1', inventory)
    require(inventory == expected, 'closed inventory differs from approved profile')
    check_route_collisions(inventory['routes'])
    require(inventory['routes'] == sorted(inventory['routes'], key=lambda x:x['pattern']), 'route order')
    refs = list(inventory['sources'].values()) + [inventory['launch']['source'], inventory['launch']['boundarySource']]
    refs += [r['source'] for r in inventory['routes']]
    for ref in refs:
        raw = source_bytes.get(ref['path'])
        if raw is None:
            raw = read_relative(root, ref['path'])
        require(digest(raw) == ref['sha256'], 'inventory source mismatch')
    discovered = set()
    for source in source_bytes:
        if '/src/app/' not in source:
            continue
        suffix = source.split('/src/app/', 1)[1]
        name = suffix.split('/')[-1]
        if name in ('page.tsx', 'route.ts'):
            discovered.add(source)
    require(discovered == {r['source']['path'] for r in inventory['routes']}, 'route discovery mismatch')
    for r in inventory['routes']:
        raw = source_bytes[r['source']['path']].decode('utf-8')
        exports = sorted(set(re.findall(r'export\s+(?:async\s+)?(?:const|function)\s+(GET|POST|PATCH|PUT|DELETE|HEAD|OPTIONS)\b', raw)))
        require(exports == r['exportedMethods'], 'method exports mismatch')


def adapt(root=ROOT):
    d = load_descriptor(root)
    sources = source_snapshot(root, d)
    inventory, adaptation = deepcopy(d['inventory']), deepcopy(d['adaptation'])
    validate_inventory(inventory, d['inventory'], sources, root)
    legacy = loads(read_relative(root, inventory['sources']['legacyPlan']['path']))
    # Historical validators/digest are pure. No WorkOrder execution or runner import.
    from .business_contracts import PLAN, check
    from .product_contracts import digest as legacy_digest
    check(PLAN, legacy)
    for key, filename in [('spec','spec'),('catalog','catalog'),('environment','environment'),('order','work-order')]:
        value = loads(read_relative(root, 'config/business/internal-requests-pilot/' + filename + '.json'))
        require(legacy_digest(value) == legacy['inputs'][key], 'historical input digest mismatch')
    require(legacy['coreRoutes'] == ['/sign-in', '/api/auth/[...all]'], 'legacy routes changed')
    require(legacy['outputsWritten'] == [] and legacy['readiness'] == 'BLOCKED', 'legacy state changed')
    contract('business-route-adaptation.v1', adaptation)
    require(adaptation['inventoryCanonicalSha256'] == object_hash(inventory), 'adaptation inventory hash mismatch')
    require(adaptation['legacyPlan'] == inventory['sources']['legacyPlan'], 'legacy reference mismatch')
    require(adaptation['decision'] == inventory['sources']['g01Decision'], 'decision mismatch')
    return d, sources, inventory, adaptation
