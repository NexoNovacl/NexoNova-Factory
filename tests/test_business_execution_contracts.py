import copy
import hashlib
import unittest
from dataclasses import FrozenInstanceError
from factory.business_execution_contracts import (ROOT, ContractError, canonical, contract,
    digest, loads, object_hash, path_set, relative_path, validate)
from factory.business_execution_authority import authorization_context
from factory.business_generation import plan


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=loads((ROOT/'tests/fixtures/p46/contract-cases.json').read_bytes())

    def test_strict_json(self):
        for raw in self.fixture['invalidJson']:
            with self.subTest(raw=raw),self.assertRaises(ContractError):loads(raw)
        with self.assertRaises(ContractError):loads(b'\xff')
        self.assertEqual(loads('{"x":1}'),{'x':1})

    def test_canonical_known_bytes(self):
        value={'z':[1,True,None],'a':'é'}
        expected=b'{"a":"\xc3\xa9","z":[1,true,null]}\n'
        self.assertEqual(canonical(value),expected)
        self.assertEqual(digest(expected),'sha256:'+hashlib.sha256(expected).hexdigest())
        self.assertNotEqual(digest(b'{ "a":1 }'),object_hash({'a':1}))
        self.assertEqual(canonical({'b':2,'a':1}),canonical({'a':1,'b':2}))
        for bad in (1.2,float('nan'),float('inf'),{1:'x'},'\ud800'):
            with self.subTest(bad=repr(bad)),self.assertRaises(ContractError):canonical(bad)

    def test_unsupported_schema_keywords(self):
        for key in self.fixture['unimplementedSchemaKeywords']:
            with self.subTest(key=key),self.assertRaises(ContractError):validate({key:[]},None)
        with self.assertRaises(ContractError):validate({'type':'number'},1)
        with self.assertRaises(ContractError):validate({'additionalProperties':True},{})

    def test_types_const_and_enum(self):
        for schema,value in [({'type':'integer'},True),({'const':1},True),({'enum':[1]},True),
                            ({'type':'string'},1),({'type':'object'},[]),({'type':'array'},{}),
                            ({'type':'boolean'},0),({'type':'null'},'null')]:
            with self.subTest(schema=schema),self.assertRaises(ContractError):validate(schema,value)
        validate({'enum':['member','admin']},'member');validate({'const':False},False)

    def test_refs_siblings_and_depth(self):
        schema={'$defs':{'x':{'type':'integer','minimum':2}},'$ref':'#/$defs/x','maximum':4}
        validate(schema,3)
        for v in (True,1,5):
            with self.subTest(value=v),self.assertRaises(ContractError):validate(schema,v)
        for ref in ('https://invalid/schema','#/missing','#/$defs/missing'):
            with self.subTest(ref=ref),self.assertRaises(ContractError):validate({'$ref':ref},1)
        with self.assertRaises(ContractError):
            validate({'$defs':{'x':{'$ref':'#/$defs/x'}},'$ref':'#/$defs/x'},1)

    def test_object_and_array_bounds(self):
        s={'type':'object','required':['a'],'additionalProperties':False,'properties':{
          'a':{'type':'array','minItems':1,'maxItems':2,'uniqueItems':True,'items':{'type':'integer'}}}}
        validate(s,{'a':[1,2]})
        for v in ({},{'a':[]},{'a':[1,1]},{'a':[1,2,3]},{'a':[True]},{'a':[1],'extra':0}):
            with self.subTest(value=v),self.assertRaises(ContractError):validate(s,v)

    def test_string_bounds_and_patterns(self):
        s={'type':'string','minLength':2,'maxLength':4,'pattern':'^[a-z]+$'}
        validate(s,'ab')
        for v in ('a','abcde','AB','a1'):
            with self.subTest(value=v),self.assertRaises(ContractError):validate(s,v)

    def test_paths(self):
        for p in self.fixture['invalidPaths']:
            with self.subTest(path=p),self.assertRaises(ContractError):relative_path(p)
        for paths in (['a','a'],['A','a'],['a','a/b']):
            with self.subTest(paths=paths),self.assertRaises(ContractError):path_set(paths)
        path_set(['src/app/requests/[id]/page.tsx','a.b'])


class AuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle=plan(loads((ROOT/'config/business/generation-pilots/atlas/spec.json').read_bytes()))

    def fixture(self):
        b=self.bundle; mh=object_hash(b['manifest']);ah=object_hash(b['adaptation'])
        inputs={'fixture/input.json':b'fixture-only'}
        wo={'format':'nexonova.business-execution-work-order.v1','runId':'unit-only','productId':'atlas',
            'planHash':object_hash(b['plan']),'generationManifestHash':mh,'adaptationHash':ah,
            'metadataHash':object_hash(b['metadata']),'inputHashes':[{'path':p,'sha256':digest(v)} for p,v in inputs.items()],
            'codeHash':b['manifest']['generatorHash'],'validatorHash':'sha256:'+'1'*64,
            'destinations':{'output':'/unit-only/output','staging':'/unit-only/staging','validation':'/unit-only/validation'},
            'actions':['stage'],'resources':{'maxContainers':0,'maxMemoryMiB':0,'maxCpu':0,'maxDiskMiB':0,
                'maxDurationSeconds':60,'network':'none'},'notBefore':100,'expiresAt':200,'maxUses':1,
            'cleanup':'owned-resources-only','rollback':'quarantine-no-overwrite'}
        wh=object_hash(wo)
        approval=canonical({'decision':'EXECUTION_B_APPROVED','workOrderHash':wh,'actions':['stage']})
        ref={'path':'/unit-only/operator/approval.json','sha256':digest(approval)}
        auth={'format':'nexonova.business-execution-authorization.v1','workOrderHash':wh,
              'generationManifestHash':mh,'adaptationHash':ah,'runId':'unit-only','productId':'atlas',
              'actions':['stage'],'humanApprovalRef':ref,'expiresAt':200,'revoked':False,
              'executionAuthority':'external-operator-context-only'}
        kwargs={'approved_work_order_hash':wh,'trusted_approval_ref':copy.deepcopy(ref),'approval_bytes':approval,
                'requested_action':'stage','now':150,'consumed_uses':frozenset(),'revoked_hashes':frozenset(),
                'current_inputs':inputs,'current_code_hash':wo['codeHash'],'current_validator_hash':wo['validatorHash']}
        return wo,auth,kwargs

    def invoke(self,wo,auth,kwargs,manifest=None,adaptation=None):
        return authorization_context(canonical(wo),canonical(auth),
            canonical(manifest or self.bundle['manifest']),canonical(adaptation or self.bundle['adaptation']),**kwargs)

    def test_context_only_no_execution(self):
        wo,auth,kw=self.fixture();ctx=self.invoke(wo,auth,kw)
        self.assertEqual(ctx.workOrderHash,object_hash(wo))
        self.assertEqual(ctx.generationManifestHash,object_hash(self.bundle['manifest']))
        self.assertFalse(ctx.effectExecutionImplemented);self.assertTrue(ctx.requiresAtomicUseReservation)
        with self.assertRaises(FrozenInstanceError):ctx.runId='modified'
        self.assertFalse(hasattr(ctx,'execute'))

    def test_required_hashes_fail_closed(self):
        for field in ('workOrderHash','generationManifestHash','adaptationHash'):
            for mode in ('missing','mismatch'):
                wo,auth,kw=self.fixture()
                if mode=='missing':del auth[field]
                else:auth[field]='sha256:'+'0'*64
                with self.subTest(field=field,mode=mode),self.assertRaises(ContractError):self.invoke(wo,auth,kw)

    def test_manifest_adaptation_tamper(self):
        wo,auth,kw=self.fixture();m=copy.deepcopy(self.bundle['manifest']);m['productId']='other'
        with self.assertRaises(ContractError):self.invoke(wo,auth,kw,manifest=m)
        a=copy.deepcopy(self.bundle['adaptation']);a['mappings'][0]['materializeLegacyPath']=True
        with self.assertRaises(ContractError):self.invoke(wo,auth,kw,adaptation=a)

    def test_external_anchor_revocation_replay_time(self):
        mutations=[('approved_work_order_hash','sha256:'+'0'*64),('trusted_approval_ref',{}),
                   ('approval_bytes',b'{}'),('now',99),('now',200),('now',True),
                   ('consumed_uses',frozenset({('unit-only','stage')})),
                   ('requested_action','docker'),('current_code_hash','sha256:'+'0'*64),
                   ('current_validator_hash','sha256:'+'0'*64),('current_inputs',{}),
                   ('current_inputs',{'fixture/input.json':b'changed'})]
        for key,value in mutations:
            wo,auth,kw=self.fixture();kw[key]=value
            with self.subTest(key=key,value=str(value)),self.assertRaises(ContractError):self.invoke(wo,auth,kw)
        wo,auth,kw=self.fixture();kw['revoked_hashes']=frozenset({object_hash(wo)})
        with self.assertRaises(ContractError):self.invoke(wo,auth,kw)

    def test_design_and_historical_approval_are_not_executive(self):
        for decision in ('DESIGN_APPROVED','IMPLEMENTATION_A','ALTERNATIVE_A_APPROVED'):
            wo,auth,kw=self.fixture()
            kw['approval_bytes']=canonical({'decision':decision,'workOrderHash':object_hash(wo),'actions':['stage']})
            ref={'path':'/unit-only/operator/approval.json','sha256':digest(kw['approval_bytes'])}
            auth['humanApprovalRef']=ref;kw['trusted_approval_ref']=ref
            with self.subTest(decision=decision),self.assertRaises(ContractError):self.invoke(wo,auth,kw)
        wo,auth,kw=self.fixture()
        for path in ('docs/migration/P4_2_PLAN.json','docs/migration/P4_6_DESIGN_APPROVAL.json'):
            with self.subTest(path=path),self.assertRaises(ContractError):
                authorization_context((ROOT/path).read_bytes(),canonical(auth),canonical(self.bundle['manifest']),
                                      canonical(self.bundle['adaptation']),**kw)

    def test_destination_and_budget_schema(self):
        wo,auth,kw=self.fixture();wo['resources']['maxContainers']=7
        with self.assertRaises(ContractError):contract('business-execution-work-order.v1',wo)
        wo,auth,kw=self.fixture();wo['destinations']['output']='/unit-only/../output'
        # Rebind fixture approval to changed WO to reach semantic validation.
        wh=object_hash(wo);auth['workOrderHash']=wh;kw['approved_work_order_hash']=wh
        approval=canonical({'decision':'EXECUTION_B_APPROVED','workOrderHash':wh,'actions':['stage']})
        ref={'path':'/unit-only/operator/approval.json','sha256':digest(approval)}
        auth['humanApprovalRef']=ref;kw.update(approval_bytes=approval,trusted_approval_ref=ref)
        with self.assertRaises(ContractError):self.invoke(wo,auth,kw)

    def test_authority_has_no_effect_calls(self):
        from unittest.mock import patch
        wo,auth,kw=self.fixture()
        with patch('subprocess.Popen',side_effect=AssertionError('process')),patch('socket.socket',side_effect=AssertionError('network')),patch('os.mkdir',side_effect=AssertionError('mkdir')),patch('os.rename',side_effect=AssertionError('rename')):
            self.assertFalse(self.invoke(wo,auth,kw).effectExecutionImplemented)

    def test_missing_contract_properties_all_required(self):
        wo,auth,kw=self.fixture()
        for name,value in [('business-execution-work-order.v1',wo),('business-execution-authorization.v1',auth)]:
            for key in value:
                bad=copy.deepcopy(value);del bad[key]
                with self.subTest(contract=name,key=key),self.assertRaises(ContractError):contract(name,bad)
        for name,value in [('business-generation-plan.v1',self.bundle['plan']),
                           ('business-generation-manifest.v1',self.bundle['manifest']),
                           ('business-generation-metadata.v1',self.bundle['metadata'])]:
            for key in value:
                bad=copy.deepcopy(value);del bad[key]
                with self.subTest(contract=name,key=key),self.assertRaises(ContractError):contract(name,bad)
