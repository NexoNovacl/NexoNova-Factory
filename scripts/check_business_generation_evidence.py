#!/usr/bin/env python3
"""Read-only receipt checking with explicit independently supplied bindings."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
from factory.business_execution_contracts import ROOT, canonical, loads, read_relative, ContractError
from factory.business_generation_evidence import evaluate


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--read-only', required=True, action='store_true')
    for key in ('manifest-hash','source-hash','validator-hash','product-id'):
        parser.add_argument('--expected-'+key, required=True)
    args = parser.parse_args(argv)
    try:
        receipt = loads(read_relative(ROOT,args.run))
        refs = [ref for c in receipt['cases'] for key in
                ('evidence','newEvidence','recoveredEvidence','sourceHashes','validatorHashes') for ref in c[key]]
        root = ROOT / Path(args.run).parent
        artifacts = {r['path']:read_relative(root,r['path']) for r in refs}
        result = evaluate(receipt,artifacts,expected_manifest_hash=args.expected_manifest_hash,
                          expected_source_hash=args.expected_source_hash,
                          expected_validator_hash=args.expected_validator_hash,
                          expected_product_id=args.expected_product_id)
        sys.stdout.write(canonical(result).decode('utf-8'))
        return 0 if all(v == 'PASS' for v in result['gates'].values()) else 2
    except (ContractError,OSError,KeyError,TypeError) as exc:
        print('BLOCKED: '+str(exc),file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
