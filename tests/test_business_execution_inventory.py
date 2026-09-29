import copy
import unittest
from factory.business_execution_contracts import ROOT, ContractError, loads, object_hash
from factory.business_execution_inventory import (adapt, check_route_collisions, intersects,
    pattern_tokens, validate_inventory, source_snapshot, load_descriptor)


class InventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d,cls.sources,cls.inventory,cls.adaptation = adapt()
        cls.fixture = loads((ROOT/'tests/fixtures/p46/route-cases.json').read_bytes())

    def test_exact_real_routes(self):
        expected = {'/','/login','/auth-check','/admin-check','/api/auth/[...all]',
                    '/api/auth-check','/api/admin-check','/requests','/requests/[id]',
                    '/api/requests','/api/requests/[id]'}
        self.assertEqual({r['pattern'] for r in self.inventory['routes']},expected)
        self.assertEqual(len(self.inventory['routes']),11)
        self.assertEqual(self.inventory['launch']['command'],['node','scripts/start-requests.mjs'])

    def test_mapping_and_auth_allowlist(self):
        self.assertEqual(self.adaptation['inventoryCanonicalSha256'],object_hash(self.inventory))
        self.assertEqual(self.adaptation['mappings'][0],{'legacyPattern':'/sign-in',
          'disposition':'reservation-only','runtimeAuthenticationPage':'/login','materializeLegacyPath':False})
        self.assertEqual(len(self.inventory['authOperations']),3)
        self.assertIn('/api/auth/sign-in/email',str(self.inventory['authOperations']))
        self.assertEqual(self.adaptation['runtimeValidation'],'NOT_EXECUTED')

    def test_intersections(self):
        for left,right in self.fixture['intersect']:
            with self.subTest(left=left,right=right):
                self.assertTrue(intersects(left,right));self.assertTrue(intersects(right,left))
        for left,right in self.fixture['disjoint']:
            with self.subTest(left=left,right=right):
                self.assertFalse(intersects(left,right));self.assertFalse(intersects(right,left))

    def test_invalid_conventions(self):
        for pattern in self.fixture['invalid']:
            with self.subTest(pattern=pattern),self.assertRaises(ContractError):pattern_tokens(pattern)

    def test_reservations(self):
        for pattern in self.fixture['reserved']:
            with self.subTest(pattern=pattern),self.assertRaises(ContractError):
                check_route_collisions([{'pattern':pattern,'owner':'auth-core','outputPath':'src/page.tsx'}])

    def test_same_route_disjoint_methods_not_exception(self):
        routes=[{'pattern':'/requests/[id]','owner':'internal-requests','outputPath':'a.ts','methods':['GET']},
                {'pattern':'/requests/[slug]','owner':'internal-requests','outputPath':'b.ts','methods':['POST']}]
        with self.assertRaises(ContractError):check_route_collisions(routes)

    def test_auth_namespace_cannot_be_claimed(self):
        with self.assertRaises(ContractError):
            check_route_collisions([{'pattern':'/api/auth/sign-in/email','owner':'internal-requests','outputPath':'a.ts'}])

    def test_inventory_mutations(self):
        changes=[lambda x:x['routes'].pop(),lambda x:x['routes'].append(copy.deepcopy(x['routes'][0])),
                 lambda x:x['launch'].update(command=['node','scripts/start.mjs']),
                 lambda x:x.update(reservations=[]),lambda x:x.update(newRedirects=[{'source':'/sign-in','destination':'/login'}]),
                 lambda x:x.update(executionAuthority='approved'),lambda x:x.update(compositionId='unknown')]
        for change in changes:
            v=copy.deepcopy(self.inventory);change(v)
            with self.subTest(change=change),self.assertRaises(ContractError):
                validate_inventory(v,self.inventory,self.sources)

    def test_source_tamper_in_memory(self):
        changed=dict(self.sources);path=self.inventory['routes'][0]['source']['path'];changed[path]+=b'\n'
        with self.assertRaises(ContractError):validate_inventory(self.inventory,self.inventory,changed)

    def test_source_map_contract_fail_closed(self):
        d=copy.deepcopy(self.d);d['files'].pop()
        with self.assertRaises(ContractError):source_snapshot(ROOT,d)
        d=copy.deepcopy(self.d);d['files'][0]['sha256']='sha256:'+'0'*64
        with self.assertRaises(ContractError):source_snapshot(ROOT,d)

    def test_deterministic_adapter(self):
        _,_,inventory,adaptation=adapt()
        self.assertEqual(inventory,self.inventory);self.assertEqual(adaptation,self.adaptation)
        self.assertEqual(self.inventory['executionAuthority'],'none')

    def test_descriptor_policy_tamper_rejected_before_adaptation(self):
        from unittest.mock import patch
        from factory.business_execution_contracts import canonical
        changed=copy.deepcopy(self.d);changed['inventory']['adaptationPolicy']='unknown-policy'
        with patch('factory.business_execution_inventory.read_relative',return_value=canonical(changed)):
            with self.assertRaises(ContractError):load_descriptor()

    def test_extra_metadata_route_not_silently_ignored(self):
        from pathlib import Path
        from unittest.mock import patch
        original=Path.rglob
        def discovery(p,pattern):
            return list(original(p,pattern))+[p/'src/app/robots.ts']
        with patch.object(Path,'rglob',discovery):
            with self.assertRaises(ContractError):source_snapshot(ROOT,self.d)
