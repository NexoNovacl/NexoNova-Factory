"""Real filesystem generation, deterministic bytes and no-replace publication."""
from copy import deepcopy
from pathlib import Path
import json,os
import pytest
from factory.constants import ROOT
from factory.generation import (Generator,load_bundle,digest,inspect_files,validate_inputs,StorageError,SchemaError,byte_hash,json_bytes)

def bundle(): return load_bundle(ROOT/'config/pilots/nexonova',ROOT/'templates/corporate-site',ROOT/'templates/corporate-site.manifest.json')
def generator(tmp_path,b):
    output=tmp_path/'products';output.mkdir()
    source=ROOT.parent/'nexonova-prototype'
    return Generator(output,tmp_path/'staging',[source],[digest(b['order'])]),source

def test_same_inputs_produce_identical_bytes_and_only_additions(tmp_path):
    b=bundle();g,source=generator(tmp_path,b)
    a=g.stage(b,source);c=g.stage(b,source)
    assert a!=c and inspect_files(a/'product')==inspect_files(c/'product')
    report,diff=g.review(a)
    assert all(f['change']=='A' and f['before'] is None for f in diff['files'])
    assert len(diff['files'])==len(inspect_files(a/'product'))
    # Synthetic receipt tests the publication gate, NOT Docker execution.
    receipt={'format':'nexonova.web-validation.v1','status':'complete','inputHash':report['stableHash'],
      'sourceUnchanged':True,'temporaryCopyRemoved':True,
      'results':[{'action':x,'status':'complete','cleanup':True} for x in ['version','probe','install','typecheck','test-content','build']]}
    (a/'web-result.json').write_bytes(json_bytes(receipt))
    destination=g.materialize(a,digest(diff))
    assert destination.name=='nexonova-website'
    assert inspect_files(destination)==inspect_files(c/'product')
    metadata=json.loads((destination/'.nexonova/project.json').read_text())
    assert metadata['baseline']['hash']==digest(metadata['baseline']['files'])
    assert all(byte_hash((destination/f['path']).read_bytes())==f['sha256'] for f in metadata['baseline']['files'])
    assert not (destination/'generation-work-order.json').exists()
    with pytest.raises(StorageError):g.materialize(c,digest(diff))

@pytest.mark.parametrize('name',['../escape','/tmp/escape','./site','a/b','a\\b','NEXONOVA',''])
def test_invalid_destination_is_rejected_without_write(tmp_path,name):
    b=bundle();g,source=generator(tmp_path,b)
    with pytest.raises(StorageError):g.destination(name)
    assert list(g.output_root.iterdir())==[]

@pytest.mark.parametrize('kind',['file','directory','symlink','case'])
def test_destination_collision_does_not_change_existing_content(tmp_path,kind):
    b=bundle();g,source=generator(tmp_path,b);dest=g.output_root/'nexonova-website'
    if kind=='file':dest.write_text('preserved')
    elif kind=='directory':dest.mkdir();(dest/'custom.txt').write_text('preserved')
    elif kind=='symlink':dest.symlink_to(source,target_is_directory=True)
    else:(g.output_root/'NEXONOVA-WEBSITE').mkdir()
    before=list(g.output_root.iterdir())
    with pytest.raises(StorageError):g.stage(b,source)
    assert list(g.output_root.iterdir())==before
    if kind=='file':assert dest.read_text()=='preserved'
    if kind=='directory':assert (dest/'custom.txt').read_text()=='preserved'

def test_tampered_product_and_diff_are_not_publishable(tmp_path):
    b=bundle();g,source=generator(tmp_path,b);a=g.stage(b,source)
    report,diff=g.review(a)
    with pytest.raises(StorageError):g.materialize(a,'sha256:'+'0'*64)
    (a/'product/src/content/site.json').write_text('{}')
    with pytest.raises(StorageError):g.review(a)
    assert list(g.output_root.iterdir())==[]

@pytest.mark.parametrize('kind',['order','public','selection','template','spec'])
def test_changed_or_unapproved_inputs_block_before_writes(tmp_path,kind):
    b=bundle();g,source=generator(tmp_path,b)
    if kind=='order':b['order']['constraints']['destination']='replace'
    if kind=='public':b['public_config']['hero']['title']='Unapproved'
    if kind=='selection':b['selection']['assets']=['public/assets/brand/icon.png']
    if kind=='template':b['template_files']['README.md']+=b'changed'
    if kind=='spec':b['spec']['brand']['name']='Changed'
    with pytest.raises((StorageError,SchemaError)):g.stage(b,source)
    assert not g.staging_root.exists()

def test_semantically_inconsistent_bundle_even_with_new_hashes_is_rejected():
    b=bundle();b['public_config']['plans'][0]['price']='$1'
    b['order']['inputs']['public_config']=digest(b['public_config'])
    with pytest.raises(StorageError,match='plan data'):validate_inputs(b,[digest(b['order'])])

def test_unresolved_decision_even_rebound_is_rejected():
    b=bundle();b['selection']['resolved_for_scope']=[]
    b['order']['inputs']['selection']=digest(b['selection'])
    with pytest.raises(StorageError,match='Unresolved'):validate_inputs(b,[digest(b['order'])])

@pytest.mark.parametrize('kind',['symlink','hardlink'])
def test_linked_stage_input_rejected(tmp_path,kind):
    b=bundle();g,source=generator(tmp_path,b);a=g.stage(b,source);p=a/'product/linked'
    if kind=='symlink':p.symlink_to(source/'README.md')
    else:os.link(a/'product/README.md',p)
    with pytest.raises(StorageError):g.review(a)

def test_protected_source_and_linked_root_rejected(tmp_path):
    b=bundle();out=tmp_path/'out';out.mkdir()
    with pytest.raises(StorageError):Generator(out,ROOT/'bad',[],[digest(b['order'])])
    link=tmp_path/'linked';link.symlink_to(out,target_is_directory=True)
    with pytest.raises(StorageError):Generator(link,tmp_path/'stage',[],[])

def test_discard_only_own_intact_staging(tmp_path):
    b=bundle();g,source=generator(tmp_path,b);a=g.stage(b,source)
    with pytest.raises(StorageError):g.discard(source)
    g.discard(a);assert not a.exists();assert source.is_dir();assert list(g.output_root.iterdir())==[]

def test_existing_v1_never_becomes_a_generation_order():
    b=bundle();b['order']=json.loads((ROOT/'config/pilots/nexonova/work-order.json').read_text())
    with pytest.raises(SchemaError):validate_inputs(b,[digest(b['order'])])


def test_failed_validation_blocks_publication(tmp_path):
    b=bundle();g,source=generator(tmp_path,b);run=g.stage(b,source);_,diff=g.review(run)
    (run/'web-result.json').write_bytes(json_bytes({'format':'nexonova.web-validation.v1','status':'error'}))
    with pytest.raises(StorageError,match='validation'):g.materialize(run,digest(diff))
    assert list(g.output_root.iterdir())==[]
