"""Separate operator-approved Node validation; not a generation side effect."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from factory.generation import configured_generator,read_json
from factory.web_tools import validate_product

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--materialized',action='store_true');args=p.parse_args()
 try:
  gen=configured_generator();run=gen.run_path(gen.staging_root/args.run)
  manifest=read_json(run/'generation.json')
  if manifest['order_hash'] not in gen.allowed_orders:raise ValueError('Unapproved generation')
  source=gen.output_root/manifest['projectId'] if args.materialized else run/'product'
  result=validate_product(source,read_json(ROOT/'config/web-tools.json'),run,manifest=manifest)
  print('web_validation='+result['status']);return 0 if result['status']=='complete' else 1
 except KeyboardInterrupt:return 130
 except (OSError,ValueError,KeyError):print('web_validation=blocked; invalid authorization, source or policy',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
