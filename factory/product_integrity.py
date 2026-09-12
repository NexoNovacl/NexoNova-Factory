"""Validate a materialized source baseline without treating build caches as source."""
import os,re,json
from pathlib import Path
from .generation import read_json,byte_hash,digest,safe_root
from .storage import safe_path,StorageError
from .executor import redact

DERIVED={"node_modules",".next","test-results","playwright-report",".npm-cache"}
NEXT_ENV=("/// <reference types=\"next\" />\n/// <reference types=\"next/image-types/global\" />\n"
          "/// <reference path=\"./.next/types/routes.d.ts\" />\n\n// NOTE: This file should not be edited\n"
          "// see https://nextjs.org/docs/app/api-reference/config/typescript for more information.\n").encode()

def validate_product_integrity(root,manifest,private_roots):
    root=safe_root(root);expected={e['path']:e['sha256'] for e in manifest['files']}
    actual={};derived=[];framework_changes=[]
    for current,dirs,files in os.walk(root,followlinks=False):
        for name in list(dirs):
            path=Path(current)/name
            if path.is_symlink():raise StorageError('Linked product directory')
            if Path(current)==root and name in DERIVED:dirs.remove(name);derived.append(name)
        for name in files:
            path=Path(current)/name;rel=path.relative_to(root).as_posix();safe_path(root,rel)
            if Path(current)==root and name.endswith('.tsbuildinfo'):derived.append(rel);continue
            if rel not in expected:raise StorageError('Unexpected non-derived product file')
            if path.stat().st_size>20_000_000:raise StorageError('Product source budget exceeded')
            data=path.read_bytes();actual[rel]=byte_hash(data)
            if actual[rel]!=expected[rel]:
                if rel=='next-env.d.ts' and data==NEXT_ENV:framework_changes.append(rel)
                else:raise StorageError('Product source differs from generated baseline')
            text=data.decode('utf8')
            if redact(text)!=text:raise StorageError('Potential secret in product source')
            if any(str(p) in text for p in private_roots):raise StorageError('Private source path leaked')
    if set(actual)!=set(expected):raise StorageError('Missing generated product file')
    metadata=read_json(root/'.nexonova/project.json')
    if metadata['projectId']!=manifest['projectId'] or digest(metadata['baseline']['files'])!=metadata['baseline']['hash']:
        raise StorageError('Product metadata mismatch')
    package=read_json(root/'package.json')
    for dependencies in ('dependencies','devDependencies'):
        if any(str(v).startswith(('file:','link:')) for v in package.get(dependencies,{}).values()):raise StorageError('Local package dependency forbidden')
    # Static relative imports/assets; dynamic DOM anchors are exercised by Playwright.
    for path in (root/'src').rglob('*'):
        if not path.is_file():continue
        text=path.read_text()
        for value in re.findall(r'(?:from\s+|import\s*)[\"\'](\.[^\"\']+)[\"\']',text):
            target=path.parent/value
            if not target.resolve().is_relative_to(root.resolve()):raise StorageError('Import escapes product')
            choices=[target,*(Path(str(target)+suffix) for suffix in ('.ts','.tsx','.json','.css')),target/'index.ts',target/'index.tsx']
            if not any(p.is_file() for p in choices):raise StorageError('Broken relative import')
        for value in re.findall(r'(?:src|href)=[\"\'](/[^\"\']+)[\"\']',text):
            if not (root/'public'/value.lstrip('/')).is_file():raise StorageError('Missing local asset or route')
    return {'status':'complete','sourceFiles':len(actual),'frameworkManagedChanges':framework_changes,
            'derivedDirectoriesOrFiles':sorted(derived),'privatePathsDetected':False,'secretHeuristicMatches':False,
            'baselineDefinition':'Exact bytes at generation, before tools. Next 15 regenerates next-env.d.ts; exact known generated form is separately reported, not treated as identical baseline.'}
