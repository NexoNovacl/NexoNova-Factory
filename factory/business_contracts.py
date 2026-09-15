"""P4.2 declarations only: no rendering, execution, database or account creation."""
from copy import deepcopy
import re,json
from .product_contracts import obj,enum,SLUG,HASH,digest,relative_path
from .schemas import validate_strict,SchemaError
from .generation import read_json

VERSION='0.1.0'
def arr(item):return {'type':'array','items':item}
def fixed(value):return {'enum':[value]}
LABEL={'type':'string','minLength':1,'maxLength':80,'pattern':r'[A-Za-zÀ-ÿ0-9 .-]+'}
POLICY={'roles':['admin','member'],'member':'own-only','admin':'all-in-product','owner':'session-derived','clientOwnerId':'forbidden','reassignment':'forbidden','roleEditing':'forbidden','states':['open','closed'],'archive':'archivedAt','physicalDelete':'forbidden','foreignResource':'uniform-404','concurrency':'expected-version-or-409','enforcement':'NOT_IMPLEMENTED'}
AUTH={'provider':'better-auth','method':'email-password','publicSignup':'closed','bootstrap':'offline-only','defaultPassword':'forbidden','sessionMaxSeconds':28800,'rememberMe':False,'logout':'revoke','oauth':False,'emailProvider':False,'mfa':False,'recoveryEmail':False,'enforcement':'NOT_IMPLEMENTED'}
PERSISTENCE={'engine':'postgresql','major':16,'orm':'prisma','ormMajor':7,'migrationTool':'prisma-migrate','runtimeDDL':'forbidden','credentials':'runtime-migrator-separated','isolation':'database-network-volume-secret-session-per-product','implementation':'NOT_IMPLEMENTED'}
TARGETS={'next':'app-router','language':'typescript','ui':'react-css-modules','api':'route-handlers-domain-services','auth':'better-auth','database':'postgresql-16','orm':'prisma-7','exactCompatibility':'PENDING_P4.3'}
RESTRICTIONS={'data':'synthetic-only','organization':'one-per-product','generation':'forbidden','infrastructure':'forbidden','migrations':'forbidden','bootstrap':'forbidden','deployment':'forbidden','externalProviders':'forbidden'}
FIELDS=[{'name':n,'type':t,'nullable':nullable,'source':source,'constraints':constraints} for n,t,nullable,source,constraints in [
 ('id','identifier',False,'server',{'format':'opaque'}),('title','string',False,'input',{'minLength':1,'maxLength':120}),('description','string',False,'input',{'minLength':0,'maxLength':2000}),('status','enum',False,'validated-command',{'values':['open','closed']}),('ownerId','user-reference',False,'session',{'reassignment':False}),('createdAt','datetime',False,'server',{'clock':'runtime'}),('updatedAt','datetime',False,'server',{'clock':'runtime'}),('archivedAt','datetime',True,'validated-command',{'physicalDelete':False}),('version','integer',False,'server',{'minimum':1,'write':'compare-and-increment'})]]
GATES=['compatibility','database-migrations','authentication','resource-authorization','module-crud','generation','build-tests','autonomy','cleanup']
ROUTES=[{'path':'/requests','methods':['GET']},{'path':'/requests/[id]','methods':['GET']},{'path':'/api/requests','methods':['GET','POST']},{'path':'/api/requests/[id]','methods':['GET','PATCH']}]
APPROVED_MODULE={'format':'nexonova.business-module.v1','id':'internal-requests','version':VERSION,'core':VERSION,'dependencies':[],'conflicts':[],'routes':ROUTES,'files':[{'path':'src/modules/internal-requests','owner':'internal-requests','kind':'directory'},{'path':'prisma/modules/internal-requests.prisma','owner':'internal-requests','kind':'file'}],'models':['InternalRequest'],'fields':FIELDS,'permissions':POLICY,'migrations':{'status':'NOT_IMPLEMENTED','intent':'initial-internal-request-model','files':[]},'requiredGates':GATES,'implementation':'NOT_IMPLEMENTED'}
SPEC=obj({'format':enum('nexonova.business-platform.v0.1.0'),'productId':SLUG,'capability':enum('business-platform'),'coreVersion':enum(VERSION),'modules':arr(obj({'id':SLUG,'version':enum(VERSION)})),'public':obj({'name':LABEL,'title':LABEL,'primaryColor':{'type':'string','pattern':r'#[a-fA-F0-9]{6}'}}),'auth':fixed(AUTH),'policy':fixed(POLICY),'persistence':fixed(PERSISTENCE),'targets':fixed(TARGETS),'restrictions':fixed(RESTRICTIONS)})
MODULE=obj({'format':enum('nexonova.business-module.v1'),'id':SLUG,'version':enum(VERSION),'core':enum(VERSION),'dependencies':arr(SLUG),'conflicts':arr(SLUG),'routes':arr(obj({'path':{'type':'string','maxLength':160},'methods':arr(enum('GET','POST','PATCH'))})),'files':arr(obj({'path':{'type':'string','maxLength':200},'owner':SLUG,'kind':enum('file','directory')})),'models':arr({'type':'string','pattern':r'[A-Za-z][A-Za-z0-9]*'}),'fields':fixed(FIELDS),'permissions':fixed(POLICY),'migrations':fixed(APPROVED_MODULE['migrations']),'requiredGates':fixed(GATES),'implementation':enum('NOT_IMPLEMENTED')})
ENV_ROWS=[{'name':n,'classification':c,'consumers':who,'required':True,'valuePolicy':'operator-supplied-not-stored'} for n,c,who in [
 ('DATABASE_URL','secret',['app']),('MIGRATION_DATABASE_URL','secret',['migration-tool']),('BETTER_AUTH_SECRET','secret',['app']),('BETTER_AUTH_URL','public-configurable',['app']),('NODE_ENV','private-runtime',['app','migration-tool'])]]
ENV=obj({'format':enum('nexonova.business-environment.v1'),'requirements':arr(obj({'name':{'type':'string','pattern':r'[A-Z][A-Z0-9_]*'},'classification':enum('secret','private-runtime','public-configurable'),'consumers':arr(enum('app','migration-tool')),'required':fixed(True),'valuePolicy':enum('operator-supplied-not-stored')}))})
ACTIONS=['validate-contracts','plan-contracts']
ORDER=obj({'format':enum('nexonova.business-work-order.v1'),'productId':SLUG,'scope':enum('P4.2-contracts-only'),'actions':fixed(ACTIONS),'inputs':obj({n:HASH for n in ['spec','catalog','environment']}),'execution':enum('forbidden')})
PLAN=obj({'format':enum('nexonova.business-plan.v1'),'productId':SLUG,'coreVersion':enum(VERSION),'inputs':obj({n:HASH for n in ['spec','catalog','environment','order']}),'specification':SPEC,'modules':arr(MODULE),'environment':ENV,'coreRoutes':fixed(['/sign-in','/api/auth/[...all]']),'gates':fixed([{'id':g,'status':'NOT_IMPLEMENTED','required':True} for g in GATES]),'readiness':enum('BLOCKED'),'reason':enum('P4.3-and-later-not-implemented'),'outputsWritten':fixed([]),'deferredContracts':fixed(['generation-manifest','product-metadata-v2','execution-validation-receipt'])})
SCHEMAS={'business-platform.v0.1.0':SPEC,'business-module.v1':MODULE,'business-environment.v1':ENV,'business-work-order.v1':ORDER,'business-plan.v1':PLAN}

class BusinessContractError(ValueError):pass

def check(schema,value):
    try:
        validate_strict(schema,value)
        def exact_enums(rule,data):
            if 'enum' in rule and json.dumps(data,sort_keys=True,allow_nan=False) not in [json.dumps(v,sort_keys=True,allow_nan=False) for v in rule['enum']]:
                raise ValueError('Enum type mismatch')
            if rule.get('type')=='object':
                for key,child in rule.get('properties',{}).items():
                    if key in data:exact_enums(child,data[key])
            if rule.get('type')=='array':
                for item in data:exact_enums(rule.get('items',{}),item)
        exact_enums(schema,value)
    except (ValueError,TypeError,KeyError):
        # Shared P3 validator can echo enum values/keys: never expose them here.
        raise BusinessContractError('Invalid business contract; values withheld') from None

def unique(values):
    if len(values)!=len(set(values)):raise BusinessContractError('Duplicate declaration')

def public_safe(public):
    for value in public.values():
        if re.search(r'(?i)(secret|password|token|credential|sk-|postgres|://|/home/)',value):
            raise BusinessContractError('Sensitive public content rejected; value withheld')

def validate_graph(modules,core=VERSION):
    """Composition algorithm can be tested with invalid synthetic descriptors, not plugins."""
    for module in modules:check(MODULE,module)
    ids=[m['id'] for m in modules];unique(ids);by_id={m['id']:m for m in modules}
    routes=[];owned=[];models=[]
    for m in modules:
        check(MODULE,m)
        if m['core']!=core:raise BusinessContractError('Incompatible core')
        unique(m['dependencies']);unique(m['conflicts'])
        if set(m['conflicts']) & set(ids):raise BusinessContractError('Module conflict')
        if set(m['dependencies'])-set(ids):raise BusinessContractError('Missing dependency')
        for route in m['routes']:
            path=route['path']
            if not path.startswith('/') or path.startswith('//'):raise BusinessContractError('Invalid route')
            try:relative_path(path[1:])
            except ValueError:raise BusinessContractError('Invalid route') from None
            # Parameter spelling does not create a distinct route.
            key=re.sub(r'\[[^/]+\]','[]',path).casefold();routes.append(key)
            if key in {'/sign-in','/api/auth/[...]','/api/auth/[]'} or key.startswith('/api/auth/'):
                raise BusinessContractError('Core route collision')
            unique(route['methods'])
            if not route['methods']:raise BusinessContractError('Empty route methods')
        for f in m['files']:
            try:relative_path(f['path'])
            except ValueError:raise BusinessContractError('Invalid ownership path') from None
            if f['owner']!=m['id']:raise BusinessContractError('Incompatible file owner')
            path=f['path'].casefold()
            if any(path==old or path.startswith(old+'/') or old.startswith(path+'/') for old in owned):
                raise BusinessContractError('Overlapping file ownership')
            owned.append(path)
        models.extend(x.casefold() for x in m['models'])
    unique(routes);unique(models)
    visited=set();active=set();ordered=[]
    def visit(mid):
        if mid in active:raise BusinessContractError('Dependency cycle')
        if mid in visited:return
        active.add(mid)
        for dep in sorted(by_id[mid]['dependencies']):visit(dep)
        active.remove(mid);visited.add(mid);ordered.append(mid)
    for mid in sorted(ids):visit(mid)
    return ordered

def validate_environment(environment):
    check(ENV,environment);rows=environment['requirements'];unique([r['name'] for r in rows])
    if sorted(rows,key=lambda r:r['name'])!=sorted(ENV_ROWS,key=lambda r:r['name']):
        raise BusinessContractError('Unsupported environment requirement; no values accepted')

def _build_plan(bundle,authorized_order_hashes):
    if not isinstance(authorized_order_hashes,list):raise BusinessContractError('Invalid host authorization list')
    for grant in authorized_order_hashes:check(HASH,grant)
    unique(authorized_order_hashes)
    if set(bundle)!={'spec','catalog','environment','order'}:raise BusinessContractError('Unexpected input bundle')
    spec,catalog,environment,order=[bundle[k] for k in ['spec','catalog','environment','order']]
    check(SPEC,spec);public_safe(spec['public']);validate_environment(environment);check(ORDER,order)
    if not isinstance(catalog,list) or not catalog:raise BusinessContractError('Invalid closed catalog')
    validate_graph(catalog)
    if catalog!=[APPROVED_MODULE]:raise BusinessContractError('Catalog not supported by this MVP')
    ids=[m['id'] for m in spec['modules']];unique(ids)
    if spec['modules']!=[{'id':'internal-requests','version':VERSION}]:raise BusinessContractError('Unsupported module combination')
    if spec['productId']!=order['productId']:raise BusinessContractError('Product identity mismatch')
    for key in ['spec','catalog','environment']:
        if digest(bundle[key])!=order['inputs'][key]:raise BusinessContractError('Authorized input hash changed')
    if digest(order) not in authorized_order_hashes:raise BusinessContractError('Exact operator authorization required')
    plan={'format':'nexonova.business-plan.v1','productId':spec['productId'],'coreVersion':VERSION,'inputs':{k:digest(bundle[k]) for k in ['spec','catalog','environment','order']},'specification':deepcopy(spec),'modules':deepcopy(catalog),'environment':deepcopy(environment),'coreRoutes':['/sign-in','/api/auth/[...all]'],'gates':[{'id':g,'status':'NOT_IMPLEMENTED','required':True} for g in GATES],'readiness':'BLOCKED','reason':'P4.3-and-later-not-implemented','outputsWritten':[],'deferredContracts':['generation-manifest','product-metadata-v2','execution-validation-receipt']}
    check(PLAN,plan)
    return plan

def load_bundle(directory):
    return {k:read_json(directory/name) for k,name in {'spec':'spec.json','catalog':'catalog.json','environment':'environment.json','order':'work-order.json'}.items()}


def build_plan(bundle,authorized_order_hashes):
    try:return _build_plan(bundle,authorized_order_hashes)
    except BusinessContractError:raise
    except (ValueError,TypeError,KeyError,AttributeError):
        raise BusinessContractError('Malformed business contract; values withheld') from None
