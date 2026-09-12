"""Explicit operator CLI: stage, review, materialize or discard; never executes web code."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from factory.generation import configured_generator,load_bundle,read_json
from factory.storage import StorageError
from factory.schemas import SchemaError

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['stage','review','materialize','discard'])
    parser.add_argument('--pilot',default='nexonova');parser.add_argument('--run');parser.add_argument('--diff-hash')
    args=parser.parse_args()
    try:
        gen=configured_generator()
        if args.action=='stage':
            from factory.product_contracts import relative_path
            relative_path(args.pilot)
            pilot=ROOT/'config/pilots'/args.pilot
            bundle=load_bundle(pilot,ROOT/'templates/corporate-site',ROOT/'templates/corporate-site.manifest.json')
            registry=read_json(ROOT/'config/sources.json')['sources'];source=registry[bundle['spec']['source_id']]
            if source['access']!='read-only' or source['expected_tree_hash']!=bundle['source_manifest']['tree_hash']:raise StorageError('Source not authorized')
            print(gen.stage(bundle,(ROOT/source['relative_to_factory']).resolve()))
        else:
            if not args.run:raise StorageError('Staging run required')
            run=gen.staging_root/args.run
            if args.action=='review':print(json.dumps(gen.review(run)[1],indent=2))
            elif args.action=='discard':gen.discard(run);print('discarded')
            else:
                if not args.diff_hash:raise StorageError('Explicit reviewed diff hash required')
                print(gen.materialize(run,args.diff_hash))
        return 0
    except (ValueError,OSError,KeyError) as exc:
        # No contract values or file contents in diagnostics.
        reason=str(exc) if isinstance(exc,StorageError) else 'malformed or unsupported input contract'
        print('generation=blocked; '+reason,file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
