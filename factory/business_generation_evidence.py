"""Pure evidence consumer. Fixtures cannot stand in for runtime evidence."""
from __future__ import annotations
from .business_execution_contracts import contract, digest, loads, path_set, require

REQUIRED = {
 'G02':('deterministic-plan','zero-effects'),
 'G03':('historical-order','revoked','altered-hash','design-not-authority'),
 'G04':('unknown-module','incompatible','cycle','unknown-policy','unsupported-routing'),
 'G05':('files','owners','models','dynamic-routes','sign-in-subtree','auth-namespace'),
 'G06':('traversal','symlink','existing-target','changed-source','foreign-data-intact'),
 'G07':('atlas-two-stagings','canonical-contracts'),
 'G08':('brisa-two-stagings','same-algorithm'),
 'G09':('independent-public-diff','no-contamination'),
 'G10':('input-output-hashes','adaptation-reservation','tamper-negatives'),
 'G11':('auth-unchanged','sql-fk','no-smoke','launcher','eleven-routes'),
 'G12':('empty-db','upgrade','reapply','fk','grants'),
 'G13':('runtime-ddl-denied','bootstrap-denied','fk-negative'),
 'G14':('install','generate','typecheck','tests','build','next-routes','head-options'),
 'G15':('login','session','signup-denied','logout','absolute-8h','cookies','sign-in-404'),
 'G16':('crud','cas-race','archive','idor','affected-c01-c40'),
 'G17':('launcher-negative','vary-cookie-union','no-store','html-rsc','browser-navigation'),
 'G18':('simultaneous-products','cross-cookie','cross-id','cross-db','positive-controls'),
 'G19':('db-unavailable','grants-removed','process-failure','recovery'),
 'G20':('logs','bundles','metadata','receipts','temporary-env','browser-network'),
 'G21':('historic-hashes','products','prototype','p3-p42-regression'),
 'G22':('success','failure','timeout','cancellation','foreign-sentinel','zero-resources'),
 'G23':('missing','altered-hash','fail','blocked','not-executed','adaptation-tamper'),
 'G24':('human-atlas','human-brisa','inventory-launcher-review'),
}
GATES = {
 'generation':('G02','G03','G04','G05','G06','G07','G08','G09','G10','G11','G17','G20','G23','G24'),
 'compatibility':('G04','G05','G09','G10','G11','G14','G17','G21'),
 'database-migrations':('G11','G12','G13','G18','G19'),
 'authentication':('G15','G18','G19'),
 'resource-authorization':('G13','G16','G18'),
 'module-crud':('G16','G19'),
 'build-tests':('G14','G15','G16','G17','G20','G21','G23'),
 'cleanup':('G06','G22','G23'),
}


def evaluate(receipt, artifacts, *, expected_manifest_hash, expected_source_hash,
             expected_validator_hash, expected_product_id, approved_output_hashes=frozenset()):
    """Inputs are bytes maps, not paths to execute or fetch. Does not persist receipts."""
    contract('business-generation-validation.v1', receipt)
    require(receipt['generationManifestHash'] == expected_manifest_hash and
            receipt['sourceHash'] == expected_source_hash and receipt['validatorHash'] == expected_validator_hash
            and receipt['productId'] == expected_product_id, 'receipt binding mismatch')
    path_set(artifacts)
    require(len({c['id'] for c in receipt['cases']}) == len(receipt['cases']), 'duplicate case')
    states = {key:'NOT_EXECUTED' for key in REQUIRED}
    reasons = {}
    for case in receipt['cases']:
        cid = case['id']
        require(set(case['requiredSubcases']) == set(REQUIRED[cid]), 'coverage contract changed')
        require(set(case['executedSubcases']) <= set(REQUIRED[cid]), 'unknown subcase')
        state = case['status']
        if state == 'PASS':
            try:
                require(set(case['executedSubcases']) == set(REQUIRED[cid]), 'subcase missing')
                assertions = case['assertions']
                require(len(assertions) == len(REQUIRED[cid]) and
                        {a['id'] for a in assertions} == set(REQUIRED[cid]) and
                        all(a['passed'] for a in assertions), 'assertions missing/failed')
                require(case['commands'] and all(c['exitCode'] == 0 for c in case['commands']), 'command missing/failed')
                require(case['evidence'] and case['newEvidence'], 'new evidence required')
                require(case['sourceHashes'] and case['validatorHashes'], 'provenance absent')
                for ref in (case['evidence']+case['newEvidence']+case['recoveredEvidence']+
                            case['sourceHashes']+case['validatorHashes']):
                    require(ref['path'] in artifacts and digest(artifacts[ref['path']]) == ref['sha256'], 'artifact missing/altered')
                # Runtime assertions require an output-bound envelope, not arbitrary test logs.
                for ref in case['newEvidence']:
                    envelope = loads(artifacts[ref['path']])
                    require(type(envelope) is dict and envelope.get('caseId') == cid and
                            envelope.get('productId') == expected_product_id and
                            envelope.get('generationManifestHash') == expected_manifest_hash and
                            envelope.get('sourceHash') == expected_source_hash and
                            envelope.get('validatorHash') == expected_validator_hash and
                            envelope.get('runId') == receipt['runId'], 'evidence envelope mismatch')
                    require(envelope.get('assertions') == assertions, 'evidence assertions differ')
                if cid == 'G24':
                    require(expected_manifest_hash in approved_output_hashes, 'external human output approval absent')
            except ValueError as exc:
                state = 'BLOCKED'
                reasons[cid] = str(exc)
        states[cid] = state
    gates = {}
    for gate, cases in GATES.items():
        gates[gate] = 'PASS' if all(states[c] == 'PASS' for c in cases) else 'BLOCKED'
    if receipt['cleanup'] != 'PASS' or receipt['resources']:
        gates['cleanup'] = 'BLOCKED'
    # Generation final acceptance also depends on all technical gates and every mandatory case.
    if any(s != 'PASS' for s in states.values()) or any(s != 'PASS' for s in gates.values()):
        gates['generation'] = 'BLOCKED'
    return {'cases':states,'gates':gates,'invalidEvidence':reasons,
            'autonomy':'NOT_IMPLEMENTED','readiness':'BLOCKED','executionAuthority':'none'}
