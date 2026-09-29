"""Strict, deliberately bounded contract validation. No effects or third-party code."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'business-auth-internal-requests-0.1.0-d02'
LAUNCHER = ['node', 'scripts/start-requests.mjs']

class ContractError(ValueError):
    """Closed rejection; never implies permission to proceed."""


def require(condition, message):
    if not condition:
        raise ContractError(message)


def loads(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def invalid(_):
        raise ContractError('non-finite JSON number')
    try:
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8', errors='strict')
        require(isinstance(raw, str) and not raw.startswith('\ufeff'), 'UTF-8 without BOM required')
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    except (ValueError, UnicodeError, TypeError, RecursionError) as exc:
        raise ContractError('invalid strict JSON') from exc


def canonical(value):
    def visit(v):
        require(type(v) in (dict, list, str, int, bool, type(None)), 'non-canonical type')
        if type(v) is dict:
            require(all(type(k) is str for k in v), 'non-string key')
            for x in v.values():
                visit(x)
        if type(v) is list:
            for x in v:
                visit(x)
    visit(value)
    try:
        return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                           separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')
    except UnicodeError as exc:
        raise ContractError('invalid Unicode scalar') from exc


def digest(raw):
    require(type(raw) is bytes, 'hash requires original bytes')
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def object_hash(value):
    return digest(canonical(value))


def relative_path(path):
    require(type(path) is str and path and path.isascii(), 'relative ASCII path required')
    require(not any(c in path for c in '\\%?#\x00') and
            not any(ord(c) < 33 or ord(c) == 127 for c in path), 'unsafe path characters')
    require(all(p not in ('', '.', '..') for p in path.split('/')), 'unsafe path segment')
    require(':' not in path, 'absolute/drive path forbidden')
    return path


def path_set(paths):
    folded = set()
    for p in paths:
        relative_path(p)
        f = p.casefold()
        require(f not in folded, 'duplicate/casefold collision')
        folded.add(f)
    for p in folded:
        require(not any('/'.join(p.split('/')[:i]) in folded
                        for i in range(1, len(p.split('/')))), 'file/directory collision')


def read_relative(root, path):
    """Read-only; reject symlinks throughout the path, including the supplied root."""
    relative_path(path)
    root = Path(root).absolute()
    for part in (root, *root.parents):
        require(not part.is_symlink(), 'symlink root')
    target = root
    for part in path.split('/'):
        target = target / part
        require(not target.is_symlink(), 'symlink input')
    require(target.is_file() and target.stat().st_nlink == 1, 'missing/special/hardlinked input')
    return target.read_bytes()


KEYWORDS = {'$schema', '$defs', '$ref', 'type', 'properties', 'required',
            'additionalProperties', 'items', 'minItems', 'maxItems', 'uniqueItems',
            'minLength', 'maxLength', 'pattern', 'minimum', 'maximum', 'const', 'enum',
            'description', 'title'}


def validate(schema, value):
    """Subset only: reject unsupported schema assertions instead of ignoring them."""
    def audit(s):
        require(type(s) is dict and not (set(s) - KEYWORDS), 'unsupported schema keyword')
        if '$schema' in s:
            require(s['$schema'] == 'https://json-schema.org/draft/2020-12/schema', 'schema dialect')
        for key in ('properties', '$defs'):
            for child in s.get(key, {}).values():
                audit(child)
        if 'items' in s:
            audit(s['items'])
        if '$ref' in s:
            require(s['$ref'].startswith('#/$defs/') and s['$ref'].count('/') == 2,
                    'only local definition refs supported')
        require(s.get('additionalProperties', False) is False, 'open schema forbidden')
        require(s.get('type') in (None, 'object', 'array', 'string', 'integer', 'boolean', 'null'),
                'unsupported schema type')
    audit(schema)
    def walk(s, v, depth=0):
        require(depth < 80, 'schema reference/depth limit')
        if '$ref' in s:
            key = s['$ref'].split('/')[-1]
            require(key in schema.get('$defs', {}), 'unresolved schema ref')
            walk(schema['$defs'][key], v, depth+1)
        types = {'object': dict, 'array': list, 'string': str, 'integer': int,
                 'boolean': bool, 'null': type(None)}
        if 'type' in s:
            require(type(v) is types[s['type']], 'wrong type')
        if 'const' in s:
            require(canonical(v) == canonical(s['const']), 'const mismatch')
        if 'enum' in s:
            require(any(canonical(v) == canonical(x) for x in s['enum']), 'enum mismatch')
        if type(v) is dict:
            require(not (set(s.get('required', [])) - set(v)), 'missing property')
            if s.get('additionalProperties') is False:
                require(not (set(v) - set(s.get('properties', {}))), 'unknown property')
            for k, child in s.get('properties', {}).items():
                if k in v:
                    walk(child, v[k], depth+1)
        elif type(v) is list:
            require(s.get('minItems', 0) <= len(v) <= s.get('maxItems', len(v)), 'array bounds')
            if s.get('uniqueItems'):
                require(len({canonical(x) for x in v}) == len(v), 'duplicate array item')
            if 'items' in s:
                for x in v:
                    walk(s['items'], x, depth+1)
        elif type(v) is str:
            require(s.get('minLength', 0) <= len(v) <= s.get('maxLength', len(v)), 'string bounds')
            if 'pattern' in s:
                require(re.search(s['pattern'], v) is not None, 'pattern mismatch')
        elif type(v) is int:
            require(s.get('minimum', v) <= v <= s.get('maximum', v), 'integer bounds')
    walk(schema, value)
    return value


def contract(name, value):
    require(re.fullmatch('[a-z-]+\\.v1', name) is not None, 'unknown contract name')
    schema = loads(read_relative(ROOT, 'schemas/' + name + '.json'))
    return validate(schema, value)
