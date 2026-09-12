from copy import deepcopy
import pytest
from factory.constants import ROOT
from factory.generation import load_bundle,configured_generator,read_json,Generator,inspect_files
from factory.generality import audit_generalization

def setup_product(tmp_path):
 b=load_bundle(ROOT/'config/pilots/synthetic-generation',ROOT/'templates/corporate-site',ROOT/'templates/corporate-site.manifest.json')
 output=tmp_path/'products';output.mkdir();g=Generator(output,tmp_path/'staging',[ROOT],configured_generator().allowed_orders)
 a=g.stage(b,ROOT/'tests/fixtures/p3-source');return b,g,a

def test_synthetic_reproducible_authorized_without_plans(tmp_path):
 b,g,a=setup_product(tmp_path);c=g.stage(b,ROOT/'tests/fixtures/p3-source')
 files=inspect_files(a/'product');assert files==inspect_files(c/'product');assert not b['public_config']['plans']
 other=read_json(ROOT/'config/pilots/nexonova/visual-content.json')
 assert audit_generalization(files,b['template_files'],b['public_config'],other,[str(ROOT)])['status']=='complete'
 g.discard(a);g.discard(c);assert not a.exists() and not c.exists()

@pytest.mark.parametrize('leak',['NexoNova','nexonova-prototype','$4.990','#075dff','/home/operator/private','Cuéntanos tu idea para revisar juntos su alcance.'])
def test_detects_actual_injected_leak(tmp_path,leak):
 b,g,a=setup_product(tmp_path);files=inspect_files(a/'product');files['src/components/Navigation.tsx']+=('\n// '+leak).encode()
 result=audit_generalization(files,b['template_files'],b['public_config'],read_json(ROOT/'config/pilots/nexonova/visual-content.json'),['/home/operator/private'])
 assert result['status']=='fail' and result['issues']

def test_generic_labels_are_not_contamination(tmp_path):
 b,g,a=setup_product(tmp_path);files=inspect_files(a/'product');files['README.md']+=b'\nContacto Servicios FAQ'
 assert audit_generalization(files,b['template_files'],b['public_config'],read_json(ROOT/'config/pilots/nexonova/visual-content.json'),[])['status']=='complete'
