"""Deterministic, approved-template-only generation. No project code executes here.

Operator policy is trusted host configuration, never authority supplied by a brief.
Linux no-replace rename and a single-writer staging lock protect publication.
"""
from __future__ import annotations
import ctypes
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from contextlib import contextmanager
from .constants import ROOT
from .executor import redact
from .product_contracts import (obj, enum, TEXT, SLUG, HASH, STRINGS, digest,
    relative_path, validate_spec, validate_manifest, verify_source)
from .schemas import SchemaError, validate_strict
from .storage import safe_path, StorageError

GENERATION_ORDER_SCHEMA = obj({
    "format": enum("nexonova.product-work-order.v2"), "operation": enum("generate-project"),
    "project_id": SLUG, "product_type": enum("corporate-site"), "template_version": TEXT,
    "inputs": obj({name: HASH for name in ("spec", "source_manifest", "public_config", "selection", "template")}),
    "constraints": obj({"destination": enum("new-only"), "external_services": enum("denied"),
        "deployment": enum("denied"), "scope": enum("P3.5-internal-pilot", "P3.6-internal-pilot")}),
})
PUBLIC_SCHEMA = obj({
    "format": enum("corporate-site.visual.v1"),
    "brand": obj({"name": TEXT, "navy": TEXT, "blue": TEXT, "cyan": TEXT}),
    "hero": obj({"title": TEXT, "accent": TEXT, "description": TEXT}),
    "about": obj({"title": TEXT, "description": TEXT}),
    "services": {"type":"array","items":obj({"title":TEXT,"description":TEXT})},
    "plans": {"type":"array","items":obj({"id":SLUG,"name":TEXT,"price":TEXT,"description":TEXT})},
    "faq": {"type":"array","items":obj({"question":TEXT,"answer":TEXT})},
})
SELECTION_SCHEMA = obj({
    "format": enum("nexonova.generation-selection.v1"), "source_tree_hash": HASH,
    "assets": {"type":"array","items":TEXT,"maxItems":0},
    "source_mode": enum("reference-only-no-copy"), "font": enum("Inter-system-fallback-no-file"),
    "content": enum("approved-internal-pilot-provisional"), "omitted_paths": STRINGS,
    "resolved_for_scope": STRINGS,
})
TEMPLATE_SCHEMA = obj({
    "format":enum("nexonova.template.v1"),"template_id":enum("corporate-site"),"version":TEXT,
    "files":{"type":"array","items":obj({"path":TEXT,"sha256":HASH,"bytes":{"type":"integer","minimum":0}})},
})
INPUT_FILES = {"spec":"corporate-site.json","source_manifest":"source-manifest.json",
               "public_config":"visual-content.json","selection":"generation-selection.json"}

def json_bytes(value):
    return (json.dumps(value,ensure_ascii=True,sort_keys=True,indent=2,allow_nan=False)+"\n").encode()

def byte_hash(data): return "sha256:"+hashlib.sha256(data).hexdigest()

def read_json(path):
    # Reading contracts is not permission to follow links or ingest secret files.
    safe_path(path.parent,path.name)
    if path.stat().st_size>2_000_000: raise StorageError("Contract too large")
    return json.loads(path.read_text())

def safe_root(path):
    raw=Path(path).absolute()
    if any(part in (".","..") for part in str(path).split("/")):
        raise StorageError("Ambiguous root")
    if any(p.is_symlink() for p in (raw,*raw.parents)): raise StorageError("Linked root")
    return raw

def inspect_files(root):
    """Exact source inventory; no cache exclusions, links, binary or sensitive files."""
    safe_root(root)
    if not root.is_dir(): raise StorageError("Missing source directory")
    result={};size=0
    for p in sorted(root.rglob("*")):
        rel=p.relative_to(root).as_posix();relative_path(rel);safe_path(root,rel)
        if p.is_dir(): continue
        if p.name.startswith('.env') or p.name in {'.npmrc','.pypirc'} or p.suffix in {'.pem','.key','.p12','.pfx'}:
            raise StorageError("Sensitive filename refused")
        if size+p.stat().st_size>20_000_000 or len(result)>=2000: raise StorageError("Generation budget exceeded")
        data=p.read_bytes();size+=len(data)
        try: text=data.decode('utf8')
        except UnicodeDecodeError: raise StorageError("Unapproved binary source") from None
        if redact(text)!=text: raise StorageError("Potential secret in input; content withheld")
        result[rel]=data
    folded=[s.casefold() for s in result]
    if len(folded)!=len(set(folded)): raise StorageError("Case-insensitive filename collision")
    return result

def file_records(files):
    return [{"path":p,"sha256":byte_hash(data),"bytes":len(data)} for p,data in sorted(files.items())]

def load_bundle(pilot, template_dir, template_manifest):
    values={key:read_json(pilot/name) for key,name in INPUT_FILES.items()}
    values['template']=read_json(template_manifest)
    values['order']=read_json(pilot/'generation-work-order.json')
    values['template_files']=inspect_files(template_dir)
    return values

def validate_inputs(bundle, allowed_orders):
    order=bundle['order'];validate_strict(GENERATION_ORDER_SCHEMA,order)
    # The host grant is outside the untrusted input bundle.
    if digest(order) not in allowed_orders: raise StorageError("Generation WorkOrder lacks exact operator authorization")
    for key,value in order['inputs'].items():
        if digest(bundle[key])!=value: raise StorageError("Approved input hash changed: "+key)
    spec=bundle['spec'];manifest=bundle['source_manifest'];public=bundle['public_config'];selection=bundle['selection'];template=bundle['template']
    validate_spec(spec);validate_manifest(manifest);validate_strict(PUBLIC_SCHEMA,public)
    validate_strict(SELECTION_SCHEMA,selection);validate_strict(TEMPLATE_SCHEMA,template)
    if selection['assets']: raise StorageError("Asset copying not implemented in this approved template")
    if order['project_id']!=spec['project_id'] or spec['source_id']!=manifest['source_id']:
        raise StorageError("Inconsistent project/source")
    if order['template_version']!=template['version']: raise StorageError("Template version mismatch")
    if not all(s['enabled'] for s in spec['sections']): raise StorageError("Section disabling unsupported by this template")
    expected_sections={'header','hero','domains','about','plans','services','faq','contact','footer','chat','inquiry'}
    if {s['id'] for s in spec['sections']}!=expected_sections: raise StorageError("Template section contract mismatch")
    if selection['source_tree_hash']!=manifest['tree_hash']: raise StorageError("Selection/source mismatch")
    expected_omissions=sorted([e['path'] for e in manifest['entries']]+manifest['missing'])
    if sorted(selection['omitted_paths'])!=expected_omissions: raise StorageError("Every omitted source must be explicit")
    pending=set(spec['pending_decisions']+manifest['pending_decisions'])
    if set(selection['resolved_for_scope'])!=pending or len(selection['resolved_for_scope'])!=len(pending):
        raise StorageError("Unresolved material decisions for generation scope")
    if spec['brand']['font_family']!='Inter': raise StorageError("Font materialization unsupported")
    expected_brand={"name":spec['brand']['name'],**spec['brand']['colors']}
    if public['brand']!=expected_brand: raise StorageError("Public brand differs from specification")
    if len({s['title'] for s in public['services']})!=len(public['services']): raise StorageError('Duplicate public service')
    if [s['title'] for s in public['services']]!=spec['services']: raise StorageError("Public services differ from specification")
    if len(public['plans'])!=len(spec['plans']): raise StorageError("Public plans differ from specification")
    for plan,approved in zip(public['plans'],spec['plans']):
        price='$'+format(approved['price_clp'],',').replace(',','.')
        if (plan['id'],plan['name'],plan['price'])!=(approved['id'],approved['name'],price):
            raise StorageError("Provisional plan data mismatch")
    if not public['faq'] or len({q['question'] for q in public['faq']})!=len(public['faq']): raise StorageError("Invalid FAQ")
    for record in template['files']: relative_path(record['path'])
    if file_records(bundle['template_files'])!=template['files']: raise StorageError("Template files changed or inventory inconsistent")
    reserved={'.nexonova/project.json'}
    if reserved & set(bundle['template_files']): raise StorageError("Generated metadata collision")
    if json.loads(bundle['template_files']['package.json'])['version']!=template['version']:
        raise StorageError("Template package version mismatch")
    return order

class Generator:
    def __init__(self, output_root, staging_root, protected, allowed_orders):
        self.output_root=safe_root(output_root);self.staging_root=safe_root(staging_root)
        self.protected=[safe_root(p) for p in [ROOT,*protected]]
        self.allowed_orders=allowed_orders
        if not self.output_root.is_dir(): raise StorageError("Approved output root must exist")
        if self.staging_root==self.output_root: raise StorageError("Staging and output roots must differ")
        self.check_destination(self.staging_root)

    def check_destination(self,path):
        path=safe_root(path)
        for protected in self.protected:
            if path==protected or path.is_relative_to(protected) or protected.is_relative_to(path):
                raise StorageError("Protected source overlaps destination")
        return path

    def destination(self,project_id):
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,62}',project_id): raise StorageError("Invalid destination ID")
        path=self.check_destination(safe_path(self.output_root,project_id))
        if path==self.staging_root or path.is_relative_to(self.staging_root): raise StorageError("Output/staging collision")
        if any(p.name.casefold()==project_id.casefold() for p in self.output_root.iterdir()):
            raise StorageError("Destination already exists; replacement is not authorized")
        return path

    @contextmanager
    def locked(self):
        self.check_destination(self.staging_root)
        if not self.staging_root.exists(): self.staging_root.mkdir(mode=0o700)
        marker=self.staging_root/'.owner.json'
        owner={"format":"nexonova.staging-root.v1","output_root":str(self.output_root)}
        if marker.exists():
            if read_json(marker)!=owner: raise StorageError("Staging root ownership mismatch")
        elif any(self.staging_root.iterdir()): raise StorageError("Unrecognized nonempty staging root")
        else:
            with marker.open('xb') as f:f.write(json_bytes(owner))
        fd=os.open(safe_path(self.staging_root,'.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX);yield
        finally:os.close(fd)

    def stage(self,bundle,source_root):
        order=validate_inputs(bundle,self.allowed_orders)
        verify_source(source_root,bundle['source_manifest'])
        with self.locked():
            self.destination(order['project_id'])
            run=Path(tempfile.mkdtemp(prefix='generation-',dir=self.staging_root))
            product=run/'product';product.mkdir()
            files=dict(bundle['template_files'])
            files['src/content/site.json']=json_bytes(bundle['public_config'])
            for name in ('package.json','package-lock.json'):
                data=json.loads(files[name]);data['name']=order['project_id']
                if name=='package-lock.json':data['packages']['']['name']=order['project_id']
                files[name]=json_bytes(data)
            baseline=file_records(files)
            metadata={"format":"nexonova.project.v1","projectId":order['project_id'],"productType":order['product_type'],
                "template":{"id":bundle['template']['template_id'],"version":bundle['template']['version'],"hash":digest(bundle['template'])},
                "specification":{"version":bundle['spec']['format'],"hash":digest(bundle['spec'])},
                "configurationHash":digest(bundle['public_config']),"sourceHash":bundle['source_manifest']['tree_hash'],
                "baseline":{"format":"nexonova.baseline.v1","files":baseline,"hash":digest(baseline)},
                "maintenance":"Baseline for comparison only; automatic updates not implemented"}
            files['.nexonova/project.json']=json_bytes(metadata)
            for rel,data in sorted(files.items()):
                path=safe_path(product,rel);path.parent.mkdir(parents=True,exist_ok=True)
                with path.open('xb') as stream:stream.write(data)
            actual=inspect_files(product)
            if actual!=files: raise StorageError("Written content differs from generation plan")
            records=file_records(actual)
            diff={"format":"nexonova.creation-diff.v1","destination":order['project_id'],"destinationExists":False,
                "files":[{"path":e['path'],"change":"A","before":None,"after":e['sha256']} for e in records]}
            report={"format":"nexonova.generation.v1","projectId":order['project_id'],"order_hash":digest(order),
                "template":metadata['template'],"configurationHash":metadata['configurationHash'],
                "files":[{**e,"origin":('public-config' if e['path']=='src/content/site.json' else 'generator-metadata' if e['path']=='.nexonova/project.json' else 'template-with-project-name' if e['path'] in ('package.json','package-lock.json') else 'template')} for e in records],
                "assets":[],"omitted":bundle['selection']['omitted_paths'],"decisions":bundle['selection'],
                "stableHash":digest(records),"diffHash":digest(diff),
                "determinism":"All product bytes deterministic. Only enclosing staging directory has a random ID; no timestamps or IDs in product."}
            (run/'generation.json').write_bytes(json_bytes(report));(run/'diff.json').write_bytes(json_bytes(diff))
            (run/'state.json').write_bytes(json_bytes({"state":"staged","stableHash":report['stableHash']}))
            return run

    def review(self,run):
        run=self.run_path(run)
        report=read_json(run/'generation.json');diff=read_json(run/'diff.json')
        if report['order_hash'] not in self.allowed_orders: raise StorageError("Staging authorization revoked")
        if digest(diff)!=report['diffHash']: raise StorageError("Diff changed")
        records=file_records(inspect_files(run/'product'))
        if digest(records)!=report['stableHash']: raise StorageError("Staging changed after generation")
        if diff!={"format":"nexonova.creation-diff.v1","destination":report['projectId'],"destinationExists":False,
                  "files":[{"path":e['path'],"change":"A","before":None,"after":e['sha256']} for e in records]}:
            raise StorageError("Diff does not match actual files")
        self.destination(report['projectId'])
        return report,diff

    def run_path(self,run):
        relative_path(run.name)
        if not re.fullmatch(r'generation-[a-z0-9_]+',run.name) or run.parent!=self.staging_root:
            raise StorageError("Unrecognized staging path")
        safe_path(self.staging_root,run.name)
        return run

    def materialize(self,run,expected_diff_hash):
        with self.locked():
            report,diff=self.review(run)
            if digest(diff)!=expected_diff_hash: raise StorageError("Reviewed diff hash changed")
            validation=read_json(run/'web-result.json')
            required={'version','probe','install','typecheck','test-content','build'}
            if (validation.get('format')!='nexonova.web-validation.v1' or validation.get('status')!='complete'
                    or validation.get('inputHash')!=report['stableHash'] or not validation.get('sourceUnchanged')
                    or not validation.get('temporaryCopyRemoved') or {r.get('action') for r in validation.get('results',[])}!=required
                    or len(validation['results'])!=len(required)
                    or any(r.get('status')!='complete' or not r.get('cleanup') for r in validation['results'])):
                raise StorageError('Matching successful web validation required before materialization')
            target=self.destination(report['projectId'])
            # Atomic Linux rename refuses even an empty pre-existing destination.
            rename=ctypes.CDLL(None,use_errno=True).renameat2
            rename.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint]
            srcfd=os.open(run,os.O_DIRECTORY|os.O_NOFOLLOW);dstfd=os.open(self.output_root,os.O_DIRECTORY|os.O_NOFOLLOW)
            try:
                if rename(srcfd,b'product',dstfd,target.name.encode(),1)!=0:
                    code=ctypes.get_errno();raise StorageError("Atomic no-replace publication failed: "+errno.errorcode.get(code,'UNKNOWN'))
            finally:os.close(srcfd);os.close(dstfd)
            (run/'state.json').write_bytes(json_bytes({"state":"materialized","projectId":report['projectId'],"stableHash":report['stableHash']}))
            return target

    def discard(self,run):
        import shutil
        with self.locked():
            self.review(run) # Only recognized, intact, unmaterialized staging is discarded.
            shutil.rmtree(run)


def configured_generator(policy_path=ROOT/'config/generation.json'):
    policy=read_json(policy_path)
    if set(policy)!={'format','output_root','staging_root','protected_roots','authorized_orders','authorization_basis'} or policy['format']!='nexonova.generation-policy.v1':
        raise StorageError("Invalid host generation policy")
    # Paths are explicit operator configuration; resolve once, then check link ancestry.
    def configured_path(value):
        raw=ROOT/value
        if any(p.is_symlink() for p in (raw,*raw.parents)): raise StorageError("Linked configured path")
        return raw.resolve()
    return Generator(configured_path(policy['output_root']),configured_path(policy['staging_root']),
        [configured_path(p) for p in policy['protected_roots']],policy['authorized_orders'])
