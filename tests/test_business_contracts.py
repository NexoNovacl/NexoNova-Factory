"""Contract mutations and synthetic composition fixtures; no app/DB/tool execution."""
from copy import deepcopy
import json,subprocess,os
import pytest
from factory.constants import ROOT
from factory.business_contracts import (load_bundle,build_plan,validate_graph,check,PLAN,APPROVED_MODULE,SCHEMAS,BusinessContractError,digest)
from factory.generation import read_json,json_bytes

PILOT=ROOT/'config/business/internal-requests-pilot'
def bundle():return load_bundle(PILOT)
def grants():return read_json(ROOT/'config/business/authorization.json')['authorizedOrders']
def rebind(b):
 b['order']['inputs']={k:digest(b[k]) for k in ['spec','catalog','environment']}
 return [digest(b['order'])]

def test_valid_deterministic_plan_never_claims_execution(tmp_path):
 b=bundle();a=build_plan(b,grants());c=build_plan(json.loads(json.dumps(b)),grants())
 assert a==c and digest(a)==digest(c)
 for path in [tmp_path/'a.json',tmp_path/'b.json']:path.write_bytes(json_bytes(a))
 assert (tmp_path/'a.json').read_bytes()==(tmp_path/'b.json').read_bytes()
 assert a['readiness']=='BLOCKED' and not a['outputsWritten']
 assert all(g['status']=='NOT_IMPLEMENTED' for g in a['gates'])
 assert a==read_json(ROOT/'docs/migration/P4_2_PLAN.json')

@pytest.mark.parametrize('path,value',[
 (['spec','unknown'],'synthetic-secret-value'),(['spec','coreVersion'],'0.2.0'),
 (['spec','modules'],[{'id':'customers','version':'0.1.0'}]),
 (['spec','modules'],[{'id':'internal-requests','version':'0.1.0'}]*2),
 (['spec','modules'],[]),(['spec','modules'],[{'id':'internal-requests','version':'1.0.0'}]),
 (['spec','policy','roles'],['admin','owner']),(['spec','policy','owner'],'body'),
 (['spec','policy','states'],['open','closed','pending']),(['spec','policy','physicalDelete'],'allowed'),
 (['spec','policy','reassignment'],'allowed'),(['spec','policy','member'],'all-in-product'),
 (['spec','policy','clientOwnerId'],'allowed'),(['spec','policy','foreignResource'],'403-with-details'),
 (['spec','policy','roleEditing'],'allowed'),(['spec','auth','sessionMaxSeconds'],86400),
 (['spec','auth','rememberMe'],True),(['spec','auth','rememberMe'],0),
 (['spec','auth','publicSignup'],'open'),(['spec','public','name'],'secret synthetic-value'),
 (['spec','public','NEXT_PUBLIC_SECRET'],'synthetic-value'),
 (['spec','persistence','runtimeDDL'],'allowed'),(['spec','restrictions','organization'],'multi'),
 (['spec','targets','exactCompatibility'],'PASS'),(['order','scope'],'P3.5-internal-pilot'),
 (['order','actions'],['migrate']),(['order','execution'],'allowed'),
 (['order','secret'],'synthetic-value'),(['order','productId'],'other-product'),
 ])
def test_unsupported_mutations_rejected_even_with_rebound_grant(path,value):
 b=bundle();obj=b
 for key in path[:-1]:obj=obj[key]
 obj[path[-1]]=value
 with pytest.raises(BusinessContractError) as caught:build_plan(b,rebind(b))
 assert 'synthetic-value' not in str(caught.value) and 'synthetic-secret-value' not in str(caught.value)

@pytest.mark.parametrize('mutation',['value','public-secret','next-public','duplicate','runtime-migrator','not-required'])
def test_environment_requirements_never_values(mutation):
 b=bundle();rows=b['environment']['requirements']
 if mutation=='value':rows[0]['value']='postgresql://synthetic:synthetic@invalid/db'
 elif mutation=='public-secret':rows[0]['classification']='public-configurable'
 elif mutation=='next-public':rows[0]['name']='NEXT_PUBLIC_DATABASE_URL'
 elif mutation=='duplicate':rows.append(deepcopy(rows[0]))
 elif mutation=='runtime-migrator':rows[1]['consumers']=['app']
 else:rows[0]['required']=False
 with pytest.raises(BusinessContractError):build_plan(b,rebind(b))

def test_hash_binding_and_separate_host_authority():
 b=bundle();b['spec']['public']['title']='Otro título'
 with pytest.raises(BusinessContractError):build_plan(b,grants())
 rebind(b)
 with pytest.raises(BusinessContractError):build_plan(b,grants())
 with pytest.raises(BusinessContractError):build_plan(bundle(),[])

def pair():
 a=deepcopy(APPROVED_MODULE);b=deepcopy(a);b['id']='fixture-only';b['routes']=[{'path':'/fixture','methods':['GET']}];b['files']=[{'path':'src/fixture-only','owner':'fixture-only','kind':'directory'}];b['models']=['FixtureOnly'];return a,b

@pytest.mark.parametrize('kind',['duplicate','cycle','conflict','route','dynamic-route','owner','overlap','version','missing-dependency','model','traversal','core-route'])
def test_invalid_composition_fixtures_not_production_catalog(kind):
 a,b=pair()
 if kind=='duplicate':b=deepcopy(a)
 elif kind=='cycle':a['dependencies']=['fixture-only'];b['dependencies']=['internal-requests']
 elif kind=='conflict':a['conflicts']=['fixture-only']
 elif kind=='route':b['routes']=deepcopy(a['routes'])
 elif kind=='dynamic-route':b['routes']=[{'path':'/requests/[other]','methods':['GET']}]
 elif kind=='owner':b['files'][0]['owner']='internal-requests'
 elif kind=='overlap':b['files'][0]['path']='src/modules/internal-requests/extra.ts'
 elif kind=='version':b['core']='9.0.0'
 elif kind=='missing-dependency':b['dependencies']=['absent']
 elif kind=='model':b['models']=a['models']
 elif kind=='traversal':b['files'][0]['path']='../escape'
 else:b['routes']=[{'path':'/api/auth/[...all]','methods':['GET']}]
 with pytest.raises(BusinessContractError):validate_graph([a,b])

def test_synthetic_valid_graph_is_stable_but_not_authorized_catalog():
 a,b=pair();b['dependencies']=['internal-requests'];assert validate_graph([b,a])==validate_graph([a,b])
 data=bundle();data['catalog']=[a,b]
 with pytest.raises(BusinessContractError):build_plan(data,rebind(data))

@pytest.mark.parametrize('field,value',[('status','pending'),('title',121),('version',0)])
def test_model_contract_cannot_change(field,value):
 b=bundle();f=next(x for x in b['catalog'][0]['fields'] if x['name']==field);f['constraints'][{'status':'values','title':'maxLength','version':'minimum'}[field]]=value
 with pytest.raises(BusinessContractError):build_plan(b,rebind(b))

def test_future_receipts_or_metadata_cannot_be_injected():
 plan=build_plan(bundle(),grants())
 for key,value in [('metadata',{'secret':'synthetic-value'}),('outputsWritten',['app.ts']),('readiness','PASS'),('gates',[])]:
  altered=deepcopy(plan);altered[key]=value
  with pytest.raises(BusinessContractError):check(PLAN,altered)

def test_schema_exports_match_implementation():
 for name,schema in SCHEMAS.items():assert read_json(ROOT/'schemas'/(name+'.json'))==schema

def test_cli_read_only_contract_success_and_sanitized_failure(tmp_path):
 cmd=[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/validate_business_contracts.py')]
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
 r=subprocess.run(cmd,capture_output=True,text=True,env=env);assert r.returncode==0 and 'execution=BLOCKED' in r.stdout
 for name in ['spec.json','catalog.json','environment.json','work-order.json']:(tmp_path/name).write_bytes((PILOT/name).read_bytes())
 p=tmp_path/'spec.json';d=json.loads(p.read_text());d['auth']='synthetic-private-marker';p.write_text(json.dumps(d))
 before={x.name:x.read_bytes() for x in tmp_path.iterdir()}
 r=subprocess.run(cmd+['--pilot',str(tmp_path)],capture_output=True,text=True,env=env)
 assert r.returncode==2 and 'synthetic-private-marker' not in r.stdout+r.stderr
 assert before=={x.name:x.read_bytes() for x in tmp_path.iterdir()}


def test_authorization_requires_a_typed_hash_list():
    for authority in [digest(bundle()['order']),[digest(bundle()['order'])]*2,['not-a-hash']]:
        with pytest.raises(BusinessContractError):build_plan(bundle(),authority)
