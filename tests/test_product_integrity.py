from pathlib import Path
import pytest
from factory.constants import ROOT
from factory.generation import Generator,load_bundle,digest,read_json,StorageError
from factory.product_integrity import validate_product_integrity,NEXT_ENV

@pytest.fixture
def generated(tmp_path):
    bundle=load_bundle(ROOT/'config/pilots/nexonova',ROOT/'templates/corporate-site',ROOT/'templates/corporate-site.manifest.json')
    output=tmp_path/'out';output.mkdir();g=Generator(output,tmp_path/'staging',[ROOT.parent/'nexonova-prototype'],[digest(bundle['order'])])
    run=g.stage(bundle,ROOT.parent/'nexonova-prototype')
    return run/'product',read_json(run/'generation.json')

def test_initial_baseline_and_exact_framework_output_are_distinguished(generated):
    root,report=generated
    assert validate_product_integrity(root,report,[ROOT])['frameworkManagedChanges']==[]
    (root/'next-env.d.ts').write_bytes(NEXT_ENV)
    assert validate_product_integrity(root,report,[ROOT])['frameworkManagedChanges']==['next-env.d.ts']

@pytest.mark.parametrize('kind',['extra','source','metadata','framework'])
def test_unapproved_changes_block_integrity(generated,kind):
    root,report=generated
    if kind=='extra':(root/'work-order.json').write_text('{}')
    if kind=='source':(root/'src/content/site.json').write_text('{}')
    if kind=='metadata':(root/'.nexonova/project.json').unlink()
    if kind=='framework':(root/'next-env.d.ts').write_text('unexpected extra code')
    with pytest.raises(StorageError):validate_product_integrity(root,report,[ROOT])
