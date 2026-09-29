"""Pure authorization context validation. No executor, journal writer or effect API."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import PurePosixPath
from .business_execution_contracts import contract, digest, loads, require

@dataclass(frozen=True)
class AuthorizationContext:
    workOrderHash: str
    generationManifestHash: str
    adaptationHash: str
    runId: str
    productId: str
    actions: tuple[str, ...]
    expiresAt: int
    effectExecutionImplemented: bool = False
    # An effectful executor would still need atomic reservation and revalidation.
    requiresAtomicUseReservation: bool = True


def authorization_context(work_order_bytes, authorization_bytes, manifest_bytes, adaptation_bytes,
                          *, approved_work_order_hash, trusted_approval_ref, approval_bytes,
                          requested_action, now, consumed_uses, revoked_hashes,
                          current_inputs, current_code_hash, current_validator_hash):
    """All trust/time/use-state supplied explicitly by caller. Never performs an action.

    A successful result is NOT an atomic use reservation and cannot be passed to an
    executor in this phase: no executor exists. Host/operator trust is not cryptographic.
    """
    wo, auth, manifest, adaptation = map(loads, (work_order_bytes, authorization_bytes,
                                                manifest_bytes, adaptation_bytes))
    for name, data in [('business-execution-work-order',wo),('business-execution-authorization',auth),
                       ('business-generation-manifest',manifest),('business-route-adaptation',adaptation)]:
        contract(name+'.v1',data)
    wh, mh, ah = map(digest, (work_order_bytes, manifest_bytes, adaptation_bytes))
    require(type(now) is int and now >= 0, 'explicit trusted time required')
    require(type(consumed_uses) is frozenset and type(revoked_hashes) is frozenset,
            'explicit immutable usage/revocation snapshot required')
    require(approved_work_order_hash == wh == auth['workOrderHash'], 'workOrderHash mismatch')
    require(mh == wo['generationManifestHash'] == auth['generationManifestHash'], 'generationManifestHash mismatch')
    require(ah == wo['adaptationHash'] == auth['adaptationHash'] == manifest['adaptationHash'], 'adaptationHash mismatch')
    require(wo['planHash'] == manifest['planHash'], 'plan binding mismatch')
    require(wo['productId'] == auth['productId'] == manifest['productId'], 'product binding mismatch')
    require(wo['runId'] == auth['runId'], 'run binding mismatch')
    require(adaptation['inventoryCanonicalSha256'] == manifest['inventoryHash'], 'inventory/adaptation mismatch')
    require(wo['notBefore'] <= now < auth['expiresAt'] <= wo['expiresAt'], 'expired/not-yet-valid authority')
    require(wo['expiresAt']-wo['notBefore'] <= 7200, 'authority window exceeds budget')
    require(wh not in revoked_hashes and (wo['runId'],requested_action) not in consumed_uses,
            'revoked/replayed authority')
    require(requested_action in auth['actions'] and set(auth['actions']) <= set(wo['actions']), 'action not authorized')
    require(auth['humanApprovalRef'] == trusted_approval_ref and
            digest(approval_bytes) == trusted_approval_ref.get('sha256'), 'missing external approval anchor')
    human = loads(approval_bytes)
    require(type(human) is dict and set(human) == {'decision','workOrderHash','actions'}, 'invalid executive approval')
    require(human['decision'] == 'EXECUTION_B_APPROVED' and human['workOrderHash'] == wh and
            set(auth['actions']) <= set(human['actions']), 'design/A approval is not executive authority')
    require(wo['codeHash'] == current_code_hash == manifest['generatorHash'] and wo['validatorHash'] == current_validator_hash,
            'code/validator changed')
    require(type(current_inputs) is dict and set(current_inputs) == {x['path'] for x in wo['inputHashes']},
            'missing/extra input snapshot')
    require(len(wo['inputHashes']) == len(current_inputs), 'duplicate input refs')
    for ref in wo['inputHashes']:
        require(digest(current_inputs[ref['path']]) == ref['sha256'], 'input changed')
    from .business_execution_contracts import relative_path
    for ref in wo['inputHashes']:
        relative_path(ref['path'])
    destinations = list(wo['destinations'].values())
    for p in destinations:
        require(type(p) is str and p.startswith('/') and str(PurePosixPath(p)) == p and
                '..' not in PurePosixPath(p).parts and p != '/', 'noncanonical destination')
        require(p.isascii() and all(ord(c)>32 for c in p) and not any(c in p for c in '\\%?#'), 'unsafe destination')
    require(len(set(destinations)) == 3, 'destinations overlap')
    for i,p in enumerate(destinations):
        require(not any(p.startswith(q+'/') or q.startswith(p+'/') for q in destinations[i+1:]), 'nested destinations')
    approval_path = trusted_approval_ref.get('path','')
    require(approval_path.startswith('/') and str(PurePosixPath(approval_path)) == approval_path and
            '..' not in PurePosixPath(approval_path).parts, 'noncanonical approval reference')
    require(approval_path.startswith('/') and not any(approval_path == p or approval_path.startswith(p+'/')
            for p in destinations), 'approval must be external to generated outputs')
    return AuthorizationContext(wh,mh,ah,wo['runId'],wo['productId'],tuple(auth['actions']),auth['expiresAt'])
