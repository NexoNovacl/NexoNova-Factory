"""Implementation-B fixtures only: no product, WorkOrder or network execution; isolated unit workers only."""
import ast
import concurrent.futures
import errno
import io
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

from factory.business_execution_contracts import ROOT, ContractError, canonical, digest
from factory.business_materialization import (
    Directory, Journal, UseRegistry, OwnedTree, ExecutionSession,
    rename_noreplace, secure_read, snapshot,
)


def fixture_permission():
    """Unit-test permission to mutate disposable fixtures, not executive authority."""


class FilesystemFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='p46-unit-b-')
        self.root = Path(self.temp.name)
        (self.root/'control').mkdir(mode=0o700)
        self.control = Directory(self.root/'control',private=True)
        self.journal = Journal(self.control)
        self.binding = {'fixtureOnly':True,'executionAuthority':'none'}

    def tearDown(self):
        self.control.close()
        self.temp.cleanup()
        self.assertFalse(self.root.exists())

    def tree(self,name='tiny-fixture'):
        return OwnedTree(self.root/name,self.journal,self.binding)

    def test_fixture_create_and_cleanup(self):
        tree = self.tree()
        state = tree.create({'a.txt':b'a','nested/b.txt':b'b'},fixture_permission)
        self.assertEqual((tree.path/'a.txt').read_bytes(),b'a')
        self.assertEqual(state,tree.verify())
        tree.cleanup(fixture_permission)
        self.assertFalse(tree.path.exists())
        self.assertEqual(self.journal.read()[-1]['event']['kind'],'tree-cleaned')

    def test_existing_destination_never_overwritten(self):
        tree=self.tree();tree.path.mkdir();(tree.path/'foreign.txt').write_bytes(b'keep')
        with self.assertRaises(FileExistsError):tree.create({'a.txt':b'a'},fixture_permission)
        self.assertEqual((tree.path/'foreign.txt').read_bytes(),b'keep')
        with self.assertRaises(ContractError):tree.cleanup(fixture_permission)

    def test_foreign_extra_blocks_all_cleanup(self):
        tree=self.tree();tree.create({'a.txt':b'a'},fixture_permission)
        (tree.path/'foreign.txt').write_bytes(b'keep')
        with self.assertRaises(ContractError):tree.cleanup(fixture_permission)
        self.assertEqual((tree.path/'a.txt').read_bytes(),b'a')
        self.assertEqual((tree.path/'foreign.txt').read_bytes(),b'keep')

    def test_modified_bytes_block_cleanup(self):
        tree=self.tree();tree.create({'a.txt':b'a'},fixture_permission)
        (tree.path/'a.txt').write_bytes(b'modified')
        with self.assertRaises(ContractError):tree.cleanup(fixture_permission)
        self.assertEqual((tree.path/'a.txt').read_bytes(),b'modified')

    def test_wrong_ownership_binding(self):
        tree=self.tree();tree.create({'a.txt':b'a'},fixture_permission)
        wrong=OwnedTree(tree.path,self.journal,{'fixtureOnly':'other'})
        with self.assertRaises(ContractError):wrong.cleanup(fixture_permission)

    def test_symlink_input_and_parent_rejected(self):
        outside=self.root/'outside';outside.mkdir();(outside/'x').write_bytes(b'keep')
        link=self.root/'link';link.symlink_to(outside,target_is_directory=True)
        with self.assertRaises((OSError,ContractError)):secure_read(link/'x')
        tree=self.tree();tree.create({'x':b'a'},fixture_permission)
        (tree.path/'x').unlink();(tree.path/'x').symlink_to(outside/'x')
        with self.assertRaises((OSError,ContractError)):tree.cleanup(fixture_permission)
        self.assertEqual((outside/'x').read_bytes(),b'keep')

    def test_hardlink_rejected(self):
        tree=self.tree();tree.create({'x':b'a'},fixture_permission)
        os.link(tree.path/'x',self.root/'alias')
        with self.assertRaises(ContractError):snapshot(tree.path)
        with self.assertRaises(ContractError):secure_read(tree.path/'x')

    def test_special_file_rejected_without_blocking(self):
        tree=self.tree();tree.create({'x':b'a'},fixture_permission)
        os.mkfifo(tree.path/'fifo')
        with self.assertRaises(ContractError):snapshot(tree.path)

    def test_path_traversal_and_casefold(self):
        for files in ({'../bad':b'x'},{'a':b'x','A':b'y'},{'a':b'x','a/b':b'y'}):
            with self.subTest(files=files),self.assertRaises(ContractError):self.tree().create(files,fixture_permission)
        self.assertFalse(self.tree().path.exists())

    def test_directory_swap_detected_before_write(self):
        child=self.root/'child';child.mkdir(mode=0o700)
        with Directory(child,private=True) as pinned:
            child.rename(self.root/'old');child.mkdir(mode=0o700)
            with self.assertRaises(ContractError):pinned.create('x',b'x',fixture_permission)
        self.assertFalse((child/'x').exists());self.assertFalse((self.root/'old'/'x').exists())

    def test_guard_denial_has_no_payload_effect(self):
        def denied():raise ContractError('fixture revocation')
        with self.assertRaises(ContractError):self.tree().create({'a':b'a'},denied)
        self.assertFalse(self.tree().path.exists())

    def test_parent_swap_during_guard_fails_closed(self):
        child=self.root/'child';child.mkdir(mode=0o700)
        with Directory(child,private=True) as pinned:
            def swap():
                child.rename(self.root/'old');child.mkdir(mode=0o700)
            with self.assertRaises(ContractError):pinned.create('x',b'x',swap)
        self.assertFalse((child/'x').exists());self.assertFalse((self.root/'old'/'x').exists())

    def test_fixture_promotion_no_clobber(self):
        tree=self.tree();tree.create({'a':b'a'},fixture_permission)
        target=self.root/'candidate-fixture'
        promoted=tree.promote(target,fixture_permission)
        self.assertFalse(tree.path.exists());self.assertEqual((target/'a').read_bytes(),b'a')
        promoted.verify();promoted.cleanup(fixture_permission)
        self.assertFalse(target.exists())

    def test_promotion_existing_empty_or_nonempty_destination(self):
        for suffix,nonempty in [('empty',False),('nonempty',True)]:
            tree=self.tree('tiny-'+suffix);tree.create({'x':b'x'},fixture_permission)
            target=self.root/suffix;target.mkdir(mode=0o700)
            if nonempty:(target/'keep').write_bytes(b'keep')
            with self.assertRaises(FileExistsError):tree.promote(target,fixture_permission)
            self.assertTrue(tree.path.exists());self.assertTrue(target.exists())
            if nonempty:self.assertEqual((target/'keep').read_bytes(),b'keep')

    def test_promotion_racing_target_no_replace(self):
        tree=self.tree();tree.create({'x':b'x'},fixture_permission)
        target=self.root/'raced'
        with Directory(self.root) as parent:
            def race():target.mkdir(mode=0o700)
            with self.assertRaises(FileExistsError):rename_noreplace(parent,tree.path.name,parent,target.name,race)
        self.assertTrue(tree.path.exists());self.assertTrue(target.exists())

    def test_no_fallback_when_atomic_rename_unavailable(self):
        tree=self.tree();tree.create({'x':b'x'},fixture_permission)
        with Directory(self.root) as parent,patch('factory.business_materialization.ctypes.CDLL',return_value=object()):
            with self.assertRaises(ContractError):rename_noreplace(parent,tree.path.name,parent,'candidate',fixture_permission)
        self.assertTrue(tree.path.exists());self.assertFalse((self.root/'candidate').exists())

    def test_journal_chain_and_torn_tail(self):
        self.journal.append({'kind':'fixture'},fixture_permission)
        self.journal.append({'kind':'fixture-2'},fixture_permission)
        rows=self.journal.read();self.assertEqual(rows[1]['previous'],rows[0]['hash'])
        p=self.root/'control/journal.jsonl';p.write_bytes(p.read_bytes()+b'{')
        with self.assertRaises(ContractError):self.journal.read()
        with self.assertRaises(ContractError):self.journal.append({'kind':'must-not-repair'},fixture_permission)

    def test_journal_tamper_rejected(self):
        self.journal.append({'kind':'fixture'},fixture_permission)
        p=self.root/'control/journal.jsonl';p.write_bytes(p.read_bytes().replace(b'fixture',b'changed'))
        with self.assertRaises(ContractError):self.journal.read()

    def test_atomic_use_reservation_threads(self):
        def contender(_):
            with Directory(self.root/'control',private=True) as control:
                try:
                    with UseRegistry(control).reserve('fixture-run','fixture-action',self.binding,fixture_permission):
                        return 'won'
                except FileExistsError:
                    return 'blocked'
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(contender,range(8)))
        self.assertEqual(results.count('won'),1);self.assertEqual(results.count('blocked'),7)

    def test_failed_claim_cannot_be_reused(self):
        registry=UseRegistry(self.control)
        with self.assertRaises(RuntimeError):
            with registry.reserve('fixture-run','fixture-action',self.binding,fixture_permission):raise RuntimeError('interrupted fixture')
        with self.assertRaises(FileExistsError):
            with registry.reserve('fixture-run','fixture-action',self.binding,fixture_permission):self.fail('replayed')

    def test_new_binding_does_not_recycle_run_action(self):
        registry=UseRegistry(self.control)
        with registry.reserve('fixture-run','fixture-action',self.binding,fixture_permission):pass
        with self.assertRaises(FileExistsError):
            with registry.reserve('fixture-run','fixture-action',{'different':True},fixture_permission):self.fail('replayed')

    def test_registry_revalidates_after_lock(self):
        calls=[]
        def deny_after_first():
            calls.append(1)
            if len(calls)>1:raise ContractError('revoked after lock')
        with self.assertRaises(ContractError):
            with UseRegistry(self.control).reserve('fixture','action',self.binding,deny_after_first):self.fail('effect')
        self.assertEqual(list((self.root/'control').glob('use-*')),[])

    def test_cleanup_identity_swap_blocks_foreign_data(self):
        tree=self.tree();tree.create({'x':b'x'},fixture_permission)
        original=tree.path/'x'
        original.rename(tree.path/'original');original.write_bytes(b'foreign')
        with self.assertRaises(ContractError):tree.cleanup(fixture_permission)
        self.assertEqual(original.read_bytes(),b'foreign')


class NoExecutiveEffectsTests(unittest.TestCase):
    def test_implementation_approval_is_not_external_authority(self):
        # Constructor/negative revalidation only: no WorkOrder is executed.
        with patch('factory.business_materialization.validate_bundle',return_value=None),\
             patch('factory.business_materialization.contract',return_value=None):
            b={'manifest':{},'adaptation':{}}
            for decision in ('IMPLEMENTATION_B','IMPLEMENTATION_A','DESIGN_APPROVED'):
                session=ExecutionSession(b,b'{}',b'{}',operator_state=lambda:{'decision':decision},control_root='/unit-not-created')
                with patch('os.open',side_effect=AssertionError('must fail before opening effect paths')):
                    with self.assertRaises(ContractError):session.revalidate('stage')

    def test_no_new_effects_on_import(self):
        with patch('subprocess.Popen',side_effect=AssertionError('process')),patch('socket.socket',side_effect=AssertionError('network')),patch('os.mkdir',side_effect=AssertionError('directory')):
            import factory.business_materialization
            self.assertTrue(callable(factory.business_materialization.snapshot))


class HarnessContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch('subprocess.Popen',side_effect=AssertionError('no runtime process on import')),patch('socket.socket',side_effect=AssertionError('no runtime network on import')):
            cls.h=runpy.run_path(str(ROOT/'scripts/validate_business_generation.py'))

    def recipe(self):
        wo={'runId':'unit-only','productId':'fixture','destinations':{'validation':'/unit/validation'},
            'resources':{'maxContainers':3,'maxMemoryMiB':4096,'maxDurationSeconds':600}}
        recipe={'format':'nexonova.business-runtime-recipe.v1','executionAuthority':'none','runId':'unit-only',
                'productId':'fixture','namespace':'p46-unit-only-fixture','nodeImage':self.h['NODE_IMAGE'],
                'postgresImage':self.h['POSTGRES_IMAGE'],'port':4443,'httpPort':4000,'controlRoot':'/unit/control','sourceDirectory':'/unit/validation',
                'envFiles':{k:'/unit/control/'+k+'.env' for k in ('runtime','migrator','bootstrap','postgres')},
                'tlsDirectory':'/unit/control/tls','cacheDirectory':'/unit/control/cache','expectedNextEnvHash':'sha256:'+'1'*64}
        return recipe,wo

    def test_recipe_is_only_data(self):
        recipe,wo=self.recipe()
        with patch('subprocess.Popen',side_effect=AssertionError('runtime process')),patch('socket.socket',side_effect=AssertionError('runtime network')):
            self.h['validate_recipe'](recipe,wo,Path('/unit/control'))
            steps=self.h['recipes'](recipe,wo)
        self.assertGreater(len(steps),15)
        self.assertTrue(all(s['runtimeStatus']=='NOT_EXECUTED' for s in steps))
        app=next(s for s in steps if s['name']=='app')
        self.assertEqual(app['argv'][-2:],['node','scripts/start-requests.mjs'])
        self.assertNotIn('scripts/start.mjs',app['argv'])
        install=next(s for s in steps if s['name']=='install')
        self.assertIn('--offline',install['argv']);self.assertIn('--ignore-scripts',install['argv'])
        self.assertIn('127.0.0.1:4000:3000',app['argv'])
        self.assertIn('--memory=1g',app['argv']);self.assertNotIn('--memory=2g',app['argv'])
        self.assertTrue(all(s['resource'] for s in steps if s['argv'][:2]==['docker','run']))

    def test_recipe_rejects_unapproved_paths_images_and_identity(self):
        for key,value in [('executionAuthority','IMPLEMENTATION_B'),('nodeImage','node:latest'),
                          ('namespace','foreign'),('port',True),('sourceDirectory','/foreign'),('httpPort',4443)]:
            recipe,wo=self.recipe();recipe[key]=value
            with self.subTest(key=key),self.assertRaises(ContractError):self.h['validate_recipe'](recipe,wo,Path('/unit/control'))
        recipe,wo=self.recipe();recipe['envFiles']['runtime']='/elsewhere/secret'
        with self.assertRaises(ContractError):self.h['validate_recipe'](recipe,wo,Path('/unit/control'))

    def test_resource_labels_and_ids_before_cleanup(self):
        verify=self.h['verify_resource']
        record={'kind':'container','name':'p46-fixture','runId':'unit','productId':'fixture','id':'owned-id'}
        data=[{'Name':'/p46-fixture','Id':'owned-id','Config':{'Labels':{'nexonova.p46.run':'unit','nexonova.p46.product':'fixture'}}}]
        self.assertEqual(verify(record,data),'owned-id')
        data[0]['Id']='foreign-id'
        with self.assertRaises(ContractError):verify(record,data)
        data[0]['Id']='owned-id';data[0]['Config']['Labels']['nexonova.p46.run']='foreign'
        with self.assertRaises(ContractError):verify(record,data)
        with self.assertRaises(ContractError):verify(record,[])

    def test_sql_provisioning_is_pure_and_credentials_separated(self):
        recipe,_=self.recipe();db='unitdb';env={'postgres':{'POSTGRES_DB':db}}
        for idx,(role,key,user) in enumerate([('runtime','DATABASE_URL','bpruntime'),('migrator','MIGRATION_DATABASE_URL','bpmigrator'),('bootstrap','BOOTSTRAP_DATABASE_URL','bpbootstrap')]):
            env[role]={key:'postgresql://'+user+':'+format(idx+1,'x')*48+'@'+recipe['namespace']+'-db:5432/'+db}
        result=self.h['database_sql']('roles',recipe,{},env)
        self.assertIn(b'NOSUPERUSER NOCREATEDB NOCREATEROLE',result)
        self.assertIn(b'CREATE SCHEMA app AUTHORIZATION bpmigrator',result)
        self.assertNotIn(b'GRANT ALL',result)
        env['runtime']['DATABASE_URL']=env['runtime']['DATABASE_URL'].replace('p46-unit-only-fixture-db','foreign-db')
        with self.assertRaises(ContractError):self.h['database_sql']('roles',recipe,{},env)

    def test_private_env_duplicate_rejected(self):
        self.assertEqual(self.h['parse_private_env'](b'A=one\nB=two\n'),{'A':'one','B':'two'})
        with self.assertRaises(ContractError):self.h['parse_private_env'](b'A=one\nA=two\n')

    def test_runtime_boundary_rejects_fake_authority_before_transport(self):
        recipe,_=self.recipe()
        with patch('subprocess.Popen',side_effect=AssertionError('runtime process')):
            with self.assertRaises(ContractError):self.h['RuntimeHarness'](object(),canonical(recipe))

    def test_cli_descriptive_only(self):
        from contextlib import redirect_stdout,redirect_stderr
        output=io.StringIO()
        with redirect_stdout(output):self.assertEqual(self.h['main'](['--describe']),0)
        self.assertEqual(json.loads(output.getvalue())['executionAuthority'],'none')
        with redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):self.h['main'](['--execute'])


class RecoveryFixtureTests(unittest.TestCase):
    setUp = FilesystemFixtureTests.setUp
    tearDown = FilesystemFixtureTests.tearDown
    tree = FilesystemFixtureTests.tree

    def test_recover_promotion_after_record_interruption(self):
        from factory.business_materialization import recover_promoted_tree
        tree=self.tree();tree.create({'x':b'x'},fixture_permission)
        expected=tree.verify();target=self.root/'candidate-fixture'
        self.journal.append({'kind':'promote-intent','path':str(tree.path),'target':str(target),
                             'binding':self.binding,'snapshot':expected},fixture_permission)
        with Directory(self.root) as parent:rename_noreplace(parent,tree.path.name,parent,target.name,fixture_permission)
        restored=recover_promoted_tree(target,self.journal,self.binding,fixture_permission)
        restored.verify();restored.cleanup(fixture_permission)

    def test_recover_cleanup_only_recorded_missing_entries(self):
        from factory.business_materialization import recover_cleanup
        tree=self.tree();tree.create({'a':b'a','b':b'b'},fixture_permission);before=tree.verify()
        self.journal.append({'kind':'cleanup-intent','path':str(tree.path),'binding':self.binding,'snapshot':before},fixture_permission)
        self.journal.append({'kind':'cleanup-entry-intent','path':str(tree.path),'binding':self.binding,'relative':'a',
                             'entry':before['entries']['a']},fixture_permission)
        (tree.path/'a').unlink()
        recover_cleanup(tree,fixture_permission);self.assertFalse(tree.path.exists())

    def test_unexplained_disappearance_blocks_recovery(self):
        from factory.business_materialization import recover_cleanup
        tree=self.tree();tree.create({'a':b'a','b':b'b'},fixture_permission);before=tree.verify()
        self.journal.append({'kind':'cleanup-intent','path':str(tree.path),'binding':self.binding,'snapshot':before},fixture_permission)
        (tree.path/'a').unlink()
        with self.assertRaises(ContractError):recover_cleanup(tree,fixture_permission)
        self.assertTrue((tree.path/'b').exists())

    def test_derived_link_cleanup_never_follows_link(self):
        tree=self.tree();tree.create({'node_modules/tool.js':b'fixture'},fixture_permission)
        (tree.path/'node_modules/tool').symlink_to('tool.js')
        with self.assertRaises(ContractError):snapshot(tree.path)
        actual=snapshot(tree.path,build_links=True)
        self.journal.append({'kind':'tree-state','path':str(tree.path),'binding':self.binding,'snapshot':actual},fixture_permission)
        tree.verify();tree.cleanup(fixture_permission);self.assertFalse(tree.path.exists())

    def test_cleanup_derived_directory_with_package_permissions(self):
        tree=self.tree();tree.create({'node_modules/tool/index.js':b'unit'},fixture_permission)
        (tree.path/'node_modules').chmod(0o755)
        (tree.path/'node_modules/tool').chmod(0o755)
        tree.cleanup(fixture_permission)
        self.assertFalse(tree.path.exists())

    def test_derived_link_escape_rejected(self):
        tree=self.tree();tree.create({'node_modules/tool.js':b'fixture'},fixture_permission)
        (self.root/'foreign').write_bytes(b'keep')
        (tree.path/'node_modules/tool').symlink_to('../../foreign')
        with self.assertRaises(ContractError):snapshot(tree.path,build_links=True)
        self.assertEqual((self.root/'foreign').read_bytes(),b'keep')

    def test_multiple_action_reservations_are_nonreusable(self):
        registry=UseRegistry(self.control)
        with registry.reserve_many('fixture',['first','second'],self.binding,fixture_permission):pass
        for action in ('first','second'):
            with self.subTest(action=action),self.assertRaises(FileExistsError):
                with registry.reserve('fixture',action,self.binding,fixture_permission):self.fail('replay')


BROWSER_UNIT_PROGRAM = r"""
import assert from 'node:assert/strict';
import {checkHeaders,validateConfig,runBrowserValidation,executionAuthority}
  from './scripts/check_business_generation_browser.mjs';
globalThis.fetch=()=>{throw new Error('real HTTP forbidden in this unit fixture');};
const tokens=['rsc','next-router-state-tree','next-router-prefetch'];
const headers={'cache-control':'no-store','vary':tokens.join(', ')+', Cookie'};
assert.equal(executionAuthority,'none');
assert.equal(checkHeaders(headers,{page:true}).cookieVary,true);
for (const invalid of [ {...headers,vary:'Cookie'}, {...headers,vary:'Cookie, cookie'},
                        {...headers,'cache-control':'public, max-age=60'},
                        {...headers,'cache-control':'public, no-store'} ]) {
  assert.throws(()=>checkHeaders(invalid,{page:true}));
}
const binding={workOrderHash:'sha256:'+'1'.repeat(64),generationManifestHash:'sha256:'+'2'.repeat(64),adaptationHash:'sha256:'+'3'.repeat(64)};
const config={executionAuthority:'none',origin:'https://127.0.0.1:4443',productId:'unit-fixture',binding,nextVaryTokens:tokens};
validateConfig(config);
assert.throws(()=>validateConfig({...config,origin:'https://external.invalid'}));
assert.throws(()=>validateConfig({...config,executionAuthority:'IMPLEMENTATION_B'}));
let loaded=0,closed=0,contextClosed=0,guarded=0,uiActions=0;
function makeBrowser() {
  return {async newContext() {
    let logged=false;
    const reply=status=>({status:()=>status,allHeaders:async()=>headers});
    const locator={async fill(){uiActions++;},async click(){uiActions++;},async waitFor(){}};
    return {request:{async post(path){logged=!path.includes('sign-out');return reply(200);},
      async get(path){return reply(path==='/sign-in'||path.startsWith('/api/requests/')?404:logged?200:401);}},
      async newPage(){return {async goto(){return reply(200);},getByLabel(){return locator;},getByRole(){return locator;}};},
      async cookies(){return [{name:'unit-session',secure:true,httpOnly:true}];},async close(){contextClosed++;}};
    },async close(){closed++;}};
}
const guard=async action=>{guarded++;return {...binding,action,reservationActive:true,origin:config.origin,nextVaryTokens:tokens};};
const loadBrowser=async()=>{loaded++;return makeBrowser();};
const credentials={member:{email:'unit@example.invalid',password:'unit-fixture-only'},admin:{email:'admin@example.invalid',password:'unit-fixture-only'}};
const result=await runBrowserValidation({config,loadBrowser,guard,credentials});
assert.equal(result.checks.length,2);assert.equal(result.executionAuthority,'none');
assert.equal(loaded,1);assert.equal(closed,1);assert.equal(contextClosed,3);assert.ok(guarded>20);assert.ok(uiActions>10);
await assert.rejects(()=>runBrowserValidation({config,loadBrowser,credentials,guard:async()=>({...binding,action:'http-browser',reservationActive:false})}));
assert.equal(loaded,1);
await assert.rejects(()=>runBrowserValidation({config,loadBrowser,credentials:{},guard}));
assert.equal(closed,2);
console.log(JSON.stringify({fixtureOnly:true,realBrowserLoaded:false,realHttpUsed:false,status:'PASS'}));
"""


class BrowserPureContractTests(unittest.TestCase):
    def test_javascript_contract_with_fake_browser_no_http(self):
        import subprocess
        # Transient Node unit program, not ProcessTransport, npm, build or browser runtime.
        result=subprocess.run(['node','--input-type=module','-e',BROWSER_UNIT_PROGRAM],cwd=ROOT,
                              capture_output=True,text=True,timeout=20,check=False)
        self.assertEqual(result.returncode,0,result.stderr)
        evidence=json.loads(result.stdout)
        self.assertTrue(evidence['fixtureOnly']);self.assertFalse(evidence['realBrowserLoaded'])
        self.assertFalse(evidence['realHttpUsed'])


class BoundaryFailureTests(unittest.TestCase):
    def test_incomplete_technical_gates_cannot_promote(self):
        session=ExecutionSession.__new__(ExecutionSession)
        session.binding={'generationManifestHash':'sha256:'+'1'*64}
        for gates in ({},{'invented':'PASS'},{'cleanup':'PASS'}):
            with self.subTest(gates=gates),patch.object(session,'operation',side_effect=AssertionError('no effect before gate rejection')):
                with self.assertRaises(ContractError):
                    session.promote({},lambda _: {'generationManifestHash':session.binding['generationManifestHash'],'technicalGates':gates})

    def test_process_transport_not_invoked_for_invalid_stdin(self):
        harness=runpy.run_path(str(ROOT/'scripts/validate_business_generation.py'))
        with patch('subprocess.Popen',side_effect=AssertionError('no process')):
            with self.assertRaises(ContractError):harness['ProcessTransport']().run(['unit-command'],1,b'x'*4097)

    def test_harness_cleanup_on_failure_uses_fake_transport_only(self):
        harness=runpy.run_path(str(ROOT/'scripts/validate_business_generation.py'))
        instance=harness['RuntimeHarness'].__new__(harness['RuntimeHarness'])
        cleaned=[]
        instance._run=lambda:(_ for _ in ()).throw(ContractError('simulated runtime failure'))
        instance.cleanup_resources=lambda:cleaned.append('unit cleanup callback')
        with patch('subprocess.Popen',side_effect=AssertionError('real process forbidden')),patch('socket.socket',side_effect=AssertionError('real socket forbidden')):
            with self.assertRaises(ContractError):instance.run()
        self.assertEqual(cleaned,['unit cleanup callback'])

    def test_failed_cleanup_never_reported_as_success(self):
        harness=runpy.run_path(str(ROOT/'scripts/validate_business_generation.py'))
        instance=harness['RuntimeHarness'].__new__(harness['RuntimeHarness'])
        instance._run=lambda:(_ for _ in ()).throw(ContractError('unit failure'))
        instance.cleanup_resources=lambda:(_ for _ in ()).throw(ContractError('unit foreign resource'))
        with self.assertRaisesRegex(ContractError,'cleanup is BLOCKED'):instance.run()


class CleanupGrantFixtureTests(unittest.TestCase):
    setUp = FilesystemFixtureTests.setUp
    tearDown = FilesystemFixtureTests.tearDown

    def test_grant_lookup_is_bound_and_not_a_new_authorization(self):
        from factory.business_materialization import cleanup_grant_time
        with self.assertRaises(ContractError):cleanup_grant_time(self.journal,self.binding,300,'unit-approval-hash')
        self.journal.append({'kind':'cleanup-grant','binding':self.binding,'validatedAt':100,
                             'approvalHash':'unit-approval-hash'},fixture_permission)
        self.assertEqual(cleanup_grant_time(self.journal,self.binding,300,'unit-approval-hash'),100)
        for binding,now,approval in [(self.binding,99,'unit-approval-hash'),
                                     ({'foreign':True},300,'unit-approval-hash'),
                                     (self.binding,300,'changed-approval')]:
            with self.subTest(binding=binding,now=now),self.assertRaises(ContractError):
                cleanup_grant_time(self.journal,binding,now,approval)

    def test_source_changed_before_fixture_write(self):
        source=self.root/'input';source.write_bytes(b'original');expected=digest(source.read_bytes())
        def guard():
            if digest(secure_read(source))!=expected:raise ContractError('source changed')
        source.write_bytes(b'changed')
        with self.assertRaises(ContractError):self.control.create('output',b'fixture',guard)
        self.assertFalse((self.root/'control/output').exists())


def _fixture_process_claim(root, queue):
    # Joined, disposable unit worker; no executive context or product payload exists.
    try:
        with Directory(Path(root)/'control',private=True) as control:
            with UseRegistry(control).reserve('process-fixture','unit-action',{'fixtureOnly':True},fixture_permission):
                queue.put('won')
    except FileExistsError:
        queue.put('blocked')


class AtomicProcessFixtureTests(unittest.TestCase):
    setUp = FilesystemFixtureTests.setUp
    tearDown = FilesystemFixtureTests.tearDown

    def test_independent_process_claim_exactly_once(self):
        import multiprocessing
        context=multiprocessing.get_context('fork')
        queue=context.Queue()
        processes=[context.Process(target=_fixture_process_claim,args=(str(self.root),queue)) for _ in range(4)]
        try:
            for process in processes:process.start()
            for process in processes:
                process.join(timeout=5)
                self.assertFalse(process.is_alive(),'unit worker failed to exit')
                self.assertEqual(process.exitcode,0)
            results=[queue.get(timeout=2) for _ in processes]
            self.assertEqual(results.count('won'),1);self.assertEqual(results.count('blocked'),3)
        finally:
            for process in processes:
                if process.is_alive():process.terminate();process.join(timeout=5)
                process.close()
            queue.close();queue.join_thread()

    def test_ownership_record_does_not_adopt_racing_foreign_file(self):
        tree=OwnedTree(self.root/'tiny-fixture',self.journal,self.binding)
        original=Directory.create
        def race(directory,name,raw,guard):
            inode=original(directory,name,raw,guard)
            if directory.path==tree.path:(tree.path/'foreign').write_bytes(b'keep')
            return inode
        with patch.object(Directory,'create',race),self.assertRaises(ContractError):
            tree.create({'a':b'a'},fixture_permission)
        with self.assertRaises(ContractError):tree.cleanup(fixture_permission)
        self.assertEqual((tree.path/'foreign').read_bytes(),b'keep')
