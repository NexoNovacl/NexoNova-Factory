from pathlib import Path
from unittest.mock import patch
import pytest
from factory.web_tools import command,validate_policy,validate_product
from factory.generation import inspect_files,file_records,digest
from factory.storage import StorageError
IMAGE='node@sha256:'+'a'*64

def test_fixed_commands_and_docker_restrictions(tmp_path):
    args=command('build',tmp_path,'owned',IMAGE)
    assert '--network=none' in args and '--pull=never' in args and '--read-only' in args
    assert '--cap-drop=ALL' in args and '--security-opt=no-new-privileges' in args
    assert '--privileged' not in args and '-p' not in args
    assert 'unix:///var/run/docker.sock' in args
    assert args[-3:]==[IMAGE,'node_modules/next/dist/bin/next','build']
    assert '--cpus=2' in args
    assert command('install',tmp_path,'owned',IMAGE).count('--network=bridge')==1
    assert '--ignore-scripts' in command('install',tmp_path,'owned',IMAGE)
    with pytest.raises(StorageError):command('arbitrary-shell',tmp_path,'owned',IMAGE)

def test_unknown_image_policy_and_unapproved_content_never_start_process(tmp_path):
    policy={'format':'nexonova.web-policy.v1','image':IMAGE,'approved_content_hashes':[],'authorization_basis':'test host authority'}
    src=tmp_path/'src';src.mkdir();(src/'README.md').write_text('synthetic')
    with patch('factory.web_tools.execute',side_effect=AssertionError('must not run')):
        with pytest.raises(StorageError,match='authorization'):validate_product(src,policy,tmp_path)
    policy['image']='node:latest'
    with pytest.raises(StorageError):validate_policy(policy)

def test_non_registry_dependency_is_refused_even_if_content_bound(tmp_path):
    import json
    src=tmp_path/'src';src.mkdir();(src/'package-lock.json').write_text(json.dumps({'packages':{'x':{'resolved':'file:../private','integrity':'sha512-test'}}}))
    policy={'format':'nexonova.web-policy.v1','image':IMAGE,'approved_content_hashes':[digest(file_records(inspect_files(src)))],'authorization_basis':'test host authority'}
    with patch('factory.web_tools.execute',side_effect=AssertionError('must not run')):
        with pytest.raises(StorageError,match='Dependency'):validate_product(src,policy,tmp_path)


def test_tool_mutation_of_source_cannot_be_certified(tmp_path):
    import json
    from factory.constants import ROOT
    from factory.generation import Generator,load_bundle,read_json
    b=load_bundle(ROOT/'config/pilots/nexonova',ROOT/'templates/corporate-site',ROOT/'templates/corporate-site.manifest.json')
    output=tmp_path/'out';output.mkdir();g=Generator(output,tmp_path/'stage',[ROOT.parent/'nexonova-prototype'],[digest(b['order'])])
    run=g.stage(b,ROOT.parent/'nexonova-prototype');manifest=read_json(run/'generation.json')
    policy={'format':'nexonova.web-policy.v1','image':IMAGE,'approved_content_hashes':[manifest['stableHash']],'authorization_basis':'test host authority'}
    def mutate(action,work,image,client):
        (work/'README.md').write_text('changed by process')
        return {'action':action,'status':'complete','cleanup':True},False
    with patch('factory.web_tools.execute',side_effect=mutate) as execute:
        result=validate_product(run/'product',policy,run,manifest=manifest)
    assert execute.call_count==1
    assert result['status']=='unapproved-source-change'
    assert result['sourceUnchanged'] and result['temporaryCopyRemoved']
