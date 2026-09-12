"""Freeze the reviewed P3 implementation; intentional revisions require a new baseline."""
import hashlib,json
from factory.constants import ROOT

def test_p3_baseline_files_remain_identical():
    baseline=json.loads((ROOT/'docs/migration/P3_BASELINE.json').read_text())
    paths=[entry['path'] for entry in baseline['files']]
    assert len(paths)==len(set(paths))
    for entry in baseline['files']:
        path=ROOT/entry['path']
        assert path.is_file() and not path.is_symlink(),entry['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'],entry['path']
    template_paths=sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/'templates/corporate-site').rglob('*') if p.is_file())
    assert template_paths==sorted(p for p in paths if p.startswith('templates/corporate-site/'))
