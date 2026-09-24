"""P4.3 orchestration policy tests; real Docker evidence is a separate receipt."""
import json
from copy import deepcopy
import pytest
from factory.business_infrastructure import Run,gate_summary,validate_versions,EXPECTED_VERSIONS,InfrastructureError,FUTURE,NODE,PG
from factory.constants import ROOT

@pytest.mark.parametrize('field,value', [('node','v20.0.0'),('prisma','6.0.0'),('client','7.4.0'),('adapter','7.4.0'),('next','latest'),('extra','unapproved')])
def test_incompatible_matrix_is_rejected(field,value):
 actual=deepcopy(EXPECTED_VERSIONS);actual[field]=value
 with pytest.raises(InfrastructureError):validate_versions(actual)

def test_exact_matrix_and_digests():
 validate_versions(deepcopy(EXPECTED_VERSIONS))
 for image in [NODE,PG]:assert '@sha256:' in image and len(image.split('sha256:')[1])==64
 package=json.loads((ROOT/'templates/business-platform/package.json').read_text())
 lock=json.loads((ROOT/'templates/business-platform/package-lock.json').read_text())
 for name,version in package['dependencies'].items():
  assert lock['packages']['node_modules/'+name]['version']==version
 assert 'better-auth' not in package['dependencies']

def test_unexecuted_gates_never_pass():
 gates=gate_summary([],False)
 assert all(gates[n]['status']=='NOT_IMPLEMENTED' for n in FUTURE)
 assert all(gates[n]['status']=='FAIL' for n in ['compatibility','database-migrations','build-tests','cleanup'])

def test_failed_negative_or_cleanup_prevents_success():
 names=['versions','postgres-version','generate','typecheck','build','empty-db','migrate-first','migrate-again','migration-stable','runtime-ddl','write','read-after-app-restart','unit','start-app','restart-app','compose-up','compose-http','compose-persistence','compose-app-prisma-read','compose-restarted-app-prisma-read']
 steps=[{'name':n,'passed':True} for n in names]
 assert gate_summary(steps,True)['database-migrations']['status']=='PASS'
 steps.append({'name':'cross-network','passed':False})
 gates=gate_summary(steps,False)
 assert gates['database-migrations']['status']=='FAIL' and gates['cleanup']['status']=='FAIL'
 assert gates['compatibility']['status']=='FAIL'

def test_foreign_resource_is_rejected_before_docker(tmp_path):
 run=Run(tmp_path)
 def forbidden(*args,**kwargs):raise AssertionError('must not touch Docker')
 run.docker=forbidden
 assert run.remove('volume','foreign') is False

def test_sensitive_evidence_is_redacted_without_logging_original(tmp_path):
 run=Run(tmp_path);secret='synthetic phrase with spaces';run.values.append(secret)
 out=run.clean_text('password="'+secret+'" postgresql://synthetic:other@db/example '+str(tmp_path))
 assert secret not in out and 'synthetic:other' not in out and str(tmp_path) not in out

def test_cleanup_failure_is_reported_not_hidden(tmp_path):
 run=Run(tmp_path);run.register('container','owned-test')
 def unavailable(*args,**kwargs):raise InfrastructureError('daemon unavailable')
 run.docker=unavailable
 rows=run.finish()
 assert rows==[{'kind':'container','name':'owned-test','removedOrAbsent':False,'error':'InfrastructureError: cleanup unverified'}]
 assert gate_summary([],all(row['removedOrAbsent'] for row in rows))['cleanup']['status']=='FAIL'

def test_exact_presence_includes_stopped_containers(tmp_path):
 import subprocess
 run=Run(tmp_path);calls=[]
 def listed(args,**kwargs):
  calls.append(args);return subprocess.CompletedProcess(args,0,'owned-test\nowned-test-extra\n')
 run.docker=listed
 assert run.exists('container','owned-test')
 assert not run.exists('container','owned')
 assert all('-a' in args for args in calls)
