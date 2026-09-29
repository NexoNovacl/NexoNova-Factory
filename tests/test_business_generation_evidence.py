import copy
import unittest
from factory.business_execution_contracts import ROOT, ContractError, canonical, digest, loads
from factory.business_generation_evidence import REQUIRED, evaluate


class EvidenceTests(unittest.TestCase):
    def fixture(self,status='PASS'):
        h='sha256:'+'1'*64;source=b'source fixture';validator=b'validator fixture'
        sources=[{'path':'source.txt','sha256':digest(source)}]
        validators=[{'path':'validator.txt','sha256':digest(validator)}]
        assertions=[{'id':s,'passed':True} for s in REQUIRED['G02']]
        envelope={'caseId':'G02','productId':'atlas','generationManifestHash':h,'sourceHash':h,
                  'validatorHash':h,'runId':'unit-only','assertions':assertions}
        evidence=canonical(envelope);ref={'path':'unit-evidence.json','sha256':digest(evidence)}
        case={'id':'G02','status':status,'requiredSubcases':list(REQUIRED['G02']),
              'executedSubcases':list(REQUIRED['G02']),'evidence':[ref],
              'sourceHashes':sources,'validatorHashes':validators,'recoveredEvidence':[],
              'newEvidence':[ref],'limitations':['UNIT FIXTURE ONLY'],'gateIds':['generation'],
              'assertions':assertions,'commands':[{'argv':['unit-fixture'],'exitCode':0}]}
        receipt={'format':'nexonova.business-generation-validation.v1','runId':'unit-only','productId':'atlas',
                 'entryHash':h,'authorizationHash':h,'generationManifestHash':h,'sourceHash':h,'validatorHash':h,
                 'versions':[{'path':'fixture-version','sha256':h}],'images':[],'cases':[case],
                 'resources':[],'cleanup':'NOT_EXECUTED','limitations':['UNIT FIXTURE ONLY'],
                 'gates':[{'id':'generation','status':'PASS'}]}
        artifacts={'source.txt':source,'validator.txt':validator,'unit-evidence.json':evidence}
        kw={'expected_manifest_hash':h,'expected_source_hash':h,'expected_validator_hash':h,'expected_product_id':'atlas'}
        return receipt,artifacts,kw

    def test_valid_partial_fixture_never_promotes_global_gate(self):
        r,a,k=self.fixture();out=evaluate(r,a,**k)
        self.assertEqual(out['cases']['G02'],'PASS')
        self.assertEqual(out['cases']['G12'],'NOT_EXECUTED')
        self.assertEqual(out['gates']['generation'],'BLOCKED')
        self.assertEqual(out['readiness'],'BLOCKED');self.assertEqual(out['executionAuthority'],'none')

    def test_statuses_preserved(self):
        f=loads((ROOT/'tests/fixtures/p46/evidence-cases.json').read_bytes())
        for status in f['invalidStatuses']:
            r,a,k=self.fixture(status)
            out=evaluate(r,a,**k)
            self.assertEqual(out['cases']['G02'],status);self.assertEqual(out['gates']['generation'],'BLOCKED')

    def test_missing_or_altered_artifacts(self):
        for p in ('source.txt','validator.txt','unit-evidence.json'):
            for missing in (True,False):
                r,a,k=self.fixture()
                if missing:del a[p]
                else:a[p]+=b'tamper'
                with self.subTest(path=p,missing=missing):
                    self.assertEqual(evaluate(r,a,**k)['cases']['G02'],'BLOCKED')

    def test_required_assertions_commands(self):
        for key,value in [('executedSubcases',[]),('assertions',[]),('commands',[]),('newEvidence',[])]:
            r,a,k=self.fixture();r['cases'][0][key]=value
            with self.subTest(key=key):self.assertEqual(evaluate(r,a,**k)['cases']['G02'],'BLOCKED')
        r,a,k=self.fixture();r['cases'][0]['assertions'][0]['passed']=False
        self.assertEqual(evaluate(r,a,**k)['cases']['G02'],'BLOCKED')
        r,a,k=self.fixture();r['cases'][0]['commands'][0]['exitCode']=1
        self.assertEqual(evaluate(r,a,**k)['cases']['G02'],'BLOCKED')

    def test_cannot_redefine_coverage(self):
        r,a,k=self.fixture();r['cases'][0]['requiredSubcases']=['made-up']
        with self.assertRaises(ContractError):evaluate(r,a,**k)
        r,a,k=self.fixture();r['cases'].append(copy.deepcopy(r['cases'][0]))
        with self.assertRaises(ContractError):evaluate(r,a,**k)

    def test_cross_product_or_run_even_with_rehashed_artifact(self):
        for field in ('productId','runId','generationManifestHash','sourceHash','validatorHash'):
            r,a,k=self.fixture();env=loads(a['unit-evidence.json']);env[field]='other';a['unit-evidence.json']=canonical(env)
            h=digest(a['unit-evidence.json'])
            for key in ('evidence','newEvidence'):r['cases'][0][key][0]['sha256']=h
            with self.subTest(field=field):self.assertEqual(evaluate(r,a,**k)['cases']['G02'],'BLOCKED')

    def test_trust_anchors(self):
        for key in ('expected_manifest_hash','expected_source_hash','expected_validator_hash','expected_product_id'):
            r,a,k=self.fixture();k[key]='other'
            with self.subTest(key=key),self.assertRaises(ContractError):evaluate(r,a,**k)

    def test_unsafe_evidence_path(self):
        r,a,k=self.fixture();a['../secret']=b'x'
        with self.assertRaises(ContractError):evaluate(r,a,**k)

    def test_human_case_requires_external_output_approval(self):
        r,a,k=self.fixture();case=r['cases'][0];case['id']='G24'
        case['requiredSubcases']=list(REQUIRED['G24']);case['executedSubcases']=list(REQUIRED['G24'])
        case['assertions']=[{'id':s,'passed':True} for s in REQUIRED['G24']]
        env=loads(a['unit-evidence.json']);env.update(caseId='G24',assertions=case['assertions'])
        a['unit-evidence.json']=canonical(env)
        for key in ('evidence','newEvidence'):case[key][0]['sha256']=digest(a['unit-evidence.json'])
        self.assertEqual(evaluate(r,a,**k)['cases']['G24'],'BLOCKED')
        out=evaluate(r,a,**k,approved_output_hashes=frozenset({k['expected_manifest_hash']}))
        self.assertEqual(out['cases']['G24'],'PASS')
        self.assertEqual(out['gates']['generation'],'BLOCKED')

    def test_claimed_cleanup_pass_does_not_hide_live_resources(self):
        r,a,k=self.fixture();r['cleanup']='PASS';r['resources']=['owned-container-still-present']
        self.assertEqual(evaluate(r,a,**k)['gates']['cleanup'],'BLOCKED')
