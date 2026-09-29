#!/usr/bin/env python3
"""Phase A CLI: stdout-only planning. Materialization commands do not exist."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
from factory.business_execution_contracts import ROOT, canonical, loads, read_relative, ContractError
from factory.business_generation import plan, validate_bundle


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['plan'])
    parser.add_argument('--spec', required=True, help='Repository-relative spec path')
    parser.add_argument('--stdout', required=True, action='store_true')
    args = parser.parse_args(argv)
    try:
        bundle = plan(loads(read_relative(ROOT,args.spec)))
        validate_bundle(bundle)
        sys.stdout.write(canonical(bundle['plan']).decode('utf-8'))
        return 0
    except (ContractError, OSError) as exc:
        print('BLOCKED: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
