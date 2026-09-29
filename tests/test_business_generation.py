import copy
import io
import runpy
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch
from factory.business_execution_contracts import ROOT, ContractError, loads, canonical, object_hash
from factory.business_generation import plan,validate_bundle


class GenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.specs={x:loads((ROOT/f'config/business/generation-pilots/{x}/spec.json').read_bytes()) for x in ('atlas','brisa')}
        cls.bundles={x:plan(s) for x,s in cls.specs.items()}

    def test_determinism_both_specs(self):
        for name,b in self.bundles.items():
            with self.subTest(product=name):
                again=plan(dict(reversed(list(self.specs[name].items()))))
                self.assertEqual(b,again)
                self.assertEqual(object_hash(b['plan']),object_hash(again['plan']))
                self.assertEqual(b['payload'],again['payload'])
                self.assertEqual(validate_bundle(b)['executionAuthority'],'none')

    def test_public_differences_only(self):
        a,b=(self.bundles[x] for x in ('atlas','brisa'))
        self.assertEqual(set(a['payload']),set(b['payload']))
        changed={p for p in a['payload'] if a['payload'][p]!=b['payload'][p]}
        self.assertEqual(changed,{'product-public.json','GENERATION.md','factory-generation/manifest.json','factory-generation/metadata.json'})
        self.assertEqual(a['inventory'],b['inventory']);self.assertEqual(a['adaptation'],b['adaptation'])

    def test_schema_user_and_sql_preserved(self):
        payload=self.bundles['atlas']['payload']
        original=(ROOT/'templates/business-platform-auth/prisma/auth/schema.prisma').read_bytes()
        self.assertEqual(payload['prisma/auth/schema.prisma'],original)
        self.assertIn(original.replace(b'../../src/generated/auth',b'../../src/generated/requests'),payload['prisma/business/schema.prisma'])
        self.assertNotIn(b'TechnicalSmoke',payload['prisma/business/schema.prisma'])
        self.assertNotIn(b'InternalRequest[]',payload['prisma/business/schema.prisma'])
        for migration in ('00000000000000_auth_initial','00000000000001_internal_requests'):
            target=payload['prisma/business/migrations/'+migration+'/migration.sql']
            prefix='prisma/auth/migrations/' if 'auth_initial' in migration else 'prisma/requests-migrations/'
            self.assertEqual(target,payload[prefix+migration+'/migration.sql'])
        self.assertIn(b'ON DELETE RESTRICT',payload['prisma/business/migrations/00000000000001_internal_requests/migration.sql'])

    def test_no_disk_network_or_subprocess_effects(self):
        import builtins
        real_open=builtins.open
        import io as iomodule
        real_io=iomodule.open
        def guard(original):
            def call(file,mode='r',*args,**kwargs):
                if any(x in mode for x in 'wax+'):raise AssertionError('write attempted')
                return original(file,mode,*args,**kwargs)
            return call
        with patch('builtins.open',guard(real_open)),patch('io.open',guard(real_io)),\
             patch('subprocess.Popen',side_effect=AssertionError('process attempted')),\
             patch('socket.socket',side_effect=AssertionError('socket attempted')),\
             patch('os.mkdir',side_effect=AssertionError('directory attempted')),\
             patch('os.rename',side_effect=AssertionError('promotion attempted')):
            bundle=plan(self.specs['atlas']);validate_bundle(bundle)

    def test_payload_tamper_rejected(self):
        for kind in ('bytes','extra','missing','metadata','adaptation','owner'):
            b=copy.deepcopy(self.bundles['atlas'])
            if kind=='bytes':b['payload']['src/app/page.tsx']+=b'\n'
            if kind=='extra':b['payload']['src/app/sign-in/page.tsx']=b'bad'
            if kind=='missing':del b['payload']['src/app/page.tsx']
            if kind=='metadata':b['metadata']['launcher']=['node','scripts/start.mjs']
            if kind=='adaptation':b['adaptation']['mappings'][0]['materializeLegacyPath']=True
            if kind=='owner':b['manifest']['files'][0]['owner']='unknown'
            with self.subTest(kind=kind),self.assertRaises(ContractError):validate_bundle(b)

    def test_bad_specs(self):
        for key,value in [('profile','other'),('executionAuthority','approved'),('modules',[]),('ownerId','admin')]:
            s=copy.deepcopy(self.specs['atlas']);s[key]=value
            with self.subTest(key=key),self.assertRaises(ContractError):plan(s)

    def test_cli_stdout_only_and_no_effect_commands(self):
        module=runpy.run_path(str(ROOT/'scripts/generate_business_product.py'))
        out=io.StringIO()
        with redirect_stdout(out):
            rc=module['main'](['plan','--spec','config/business/generation-pilots/atlas/spec.json','--stdout'])
        self.assertEqual(rc,0);self.assertEqual(loads(out.getvalue())['executionAuthority'],'none')
        for command in ('stage','promote','build','cleanup'):
            with self.subTest(command=command),redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                module['main']([command,'--spec','config/business/generation-pilots/atlas/spec.json','--stdout'])

    def test_unchanged_launcher_and_configs(self):
        payload=self.bundles['atlas']['payload']
        for p in ('package.json','package-lock.json','tsconfig.json','tsconfig.checks.json'):
            self.assertEqual(payload[p],(ROOT/'templates/business-platform-auth'/p).read_bytes())
        self.assertEqual(payload['scripts/start-requests.mjs'],(ROOT/'modules/internal-requests/0.1.0/files/scripts/start-requests.mjs').read_bytes())

    def test_self_consistent_forgery_does_not_pass(self):
        b=copy.deepcopy(self.bundles['atlas'])
        b['metadata']['public']['name']='Forged public name'
        b['payload']['factory-generation/metadata.json']=canonical(b['metadata'])
        with self.assertRaises(ContractError):validate_bundle(b)
        b=copy.deepcopy(self.bundles['atlas'])
        b['manifest']['limitations']=[]
        with self.assertRaises(ContractError):validate_bundle(b)

    def test_entire_source_set_matches_manifest(self):
        from factory.business_execution_inventory import load_descriptor
        descriptor=load_descriptor()
        b=self.bundles['atlas']
        from factory.business_execution_contracts import digest
        for row in descriptor['files']:
            with self.subTest(source=row['source']):
                self.assertEqual(digest(b['payload'][row['destination']]),row['sha256'])

    def test_closed_catalog_rejects_unknown_incompatible_cycle_conflict(self):
        variants=[
          [{'id':'unknown','version':'0.1.0'}],
          [{'id':'internal-requests','version':'9.0.0'}],
          [{'id':'internal-requests','version':'0.1.0','requires':['internal-requests']}],
          [{'id':'internal-requests','version':'0.1.0'},{'id':'internal-requests','version':'0.1.0'}],
        ]
        for modules in variants:
            s=copy.deepcopy(self.specs['atlas']);s['modules']=modules
            with self.subTest(modules=modules),self.assertRaises(ContractError):plan(s)
