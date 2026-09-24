#!/usr/bin/env python3
"""Derive final P4.4-B evidence from explicit checks, never from an aggregate PASS."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text())
OLD='docs/migration/P4_4_B_AUTH_PROGRESS.json'
AUDIT='docs/migration/P4_4_B_RECOVERY_AUDIT.json'
PRES='docs/migration/P4_4_B_CONTINUATION_PRESERVATION.json'
HOST='docs/migration/P4_4_B_HOST_FINAL.json'
CLEAN='docs/migration/P4_4_B_TEMP_CLEANUP.json'
OUT='docs/migration/P4_4_B_FINAL_RECEIPT.json'
# Explicit recovered check references. Every named reference must exist and pass.
REC={
'B01':['install','engine','exact-versions','openssl','generate'],
'B02':['migrate','migrate-repeat','migration-stable','reviewed-migration-identical'],
'B03':['bootstrap','single-admin','bootstrap-concurrent-atomic','login-True'],
'B04':['bootstrap-repeat','bootstrap-concurrent-outcomes','bootstrap-concurrent-atomic','bootstrap-rollback-no-orphan','partial-not-repaired'],
'B05':['generic-login-rejection'],
'B06':[f'{x}-{v}' for v in ['True','False','omitted'] for x in ['login','session','absolute-eight-hours','cookie-policy']]+['anonymous-api','forged-session','expired-get-session','expired-protected'],
'B07':['no-session-refresh'],
'B08':['logout','logout-database-row-removed','revoked-replay'],
'B09':['anonymous-api','admin-probe','member-authenticated','member-admin-denied','browser'],
'B10':['closed-email','closed-update-user','closed-set-role','role-body-rejected','spoofed-role-header','spoofed-role-query','spoofed-role-cookie'],
'B11':[f'privilege-{i}' for i in range(7)]+['runtime-direct-migrate-permission-error','migrator-url-swapped','bootstrap-runtime-denied','bootstrap-migrator-denied','config-swapped-runtime'],
'B12':['session-after-restart','database-restarted-session-valid'],
'B13':['insufficient-permissions','database-down','bootstrap-database-down','bootstrap-insufficient-permission','bootstrap-rollback-no-orphan'],
'B14':['origin-rejected','missing-origin-rejected','null-origin-rejected','cross-site-get-rejected','redirect-rejected','secure-login','secure-session','cookie-namespace-isolation','cookie-signing-secret-isolation','browser-https'],
'B15':['rate-limit','concurrent-rate-limit'],
'B16':['unit','config-missing','config-production-http','config-short-secret','config-swapped-runtime','member-login'],
'B17':['ssr-no-secrets','app-logs-no-known-secrets','final-log-scan-app','final-log-scan-db','browser','browser-https'],
'B18':['ordinary-process-cleaned','timeout-process-cleaned','foreign-resource-preserved','sentinel-absent'],
'B19':['typecheck','unit','build','start-auth-app','browser','browser-https','private-page-no-store','private-api-no-store-True'],
'B20':[]}
NEW={
'B02':['B02-exact-live-table-inventory'],
'B04':['B04-same-email-concurrent-outcomes','B04-same-email-one-admin-account-no-session','B04-repeat-all-state-unchanged','B04-other-all-state-unchanged','B04-invalid-all-state-unchanged','B04-member-no-promotion-state-unchanged','B04-partial-full-state-unchanged','B04-original-password-retained'],
'B05':['browser-negative-login-']+[f'B05-timing-generic-{k}-{i}' for i in range(3) for k in ['wrong','unknown']],
'B06':['browser-session-'+k for k in ['valid','absent','forged','expired']],
'B07':['B07-before-eight-hours-probe','B07-before-eight-hours-better-auth','B07-no-refresh-near-boundary','B07-at-or-after-eight-hours-probe','B07-at-or-after-eight-hours-better-auth'],
'B08':['B08-new-session-different','B08-fixation-rejected','B08-forged-still-invalid-probe','B08-forged-still-invalid-better-auth'],
'B10':['B10-encoded-closed-'+str(i) for i in range(6)]+['B10-encoded-no-state-change','B10-unknown-role-database-rejected','B10-unknown-role-input-rejected'],
'B12':[f'B12-{k}-after-restart-{p}' for k in ['expired','revoked'] for p in ['probe','better-auth']]+['B12-live-control-after-restart-probe','B12-live-control-after-restart-better-auth'],
'B14':['B14-forwarded-origin-cannot-bypass','B14-forwarded-host-cookie-policy','B14-source-control-valid','B14-product-a-valid-probe','B14-product-b-cookie-a-rejected-probe','B14-product-b-cookie-a-rejected-better-auth','B14-product-b-renamed-cookie-rejected-probe','B14-product-b-renamed-cookie-rejected-better-auth','B14-independent-database-empty-session','B14-distinct-networks-volumes','browser-secure-login-'],
'B15':['B15-budget-'+str(i) for i in range(5)]+['B15-429-retry-after','B15-recovery-without-restart'],
'B16':['B16-overlong-integrated-0','B16-overlong-integrated-1','B16-overlong-bootstrap-state-0','B16-overlong-bootstrap-state-1'],
}
SCOPES={
'B01':'Fixed OpenSSL image/dependencies, actual install and Prisma generation',
'B02':'Migration/reapplication and exact live schema inventory',
'B03':'Offline admin bootstrap, real credential hash/login',
'B04':'Concurrency, idempotency, rollback and unchanged full state',
'B05':'Generic login failures in HTTP/browser; observational timing',
'B06':'DB lifetime and real browser valid/absent/forged/expired session',
'B07':'Coherent DB timestamps at either side of absolute 8h; no refresh',
'B08':'Logout replay and fresh token/fixation rejection',
'B09':'Session/role probes only; no resource authorization',
'B10':'Client role spoofing, enum rejection, direct and encoded closed routes',
'B11':'Real PostgreSQL least privilege and credential separation',
'B12':'Valid session survives restart; expired/revoked sessions do not revive',
'B13':'Database/permission outage fail closed and transactional rollback',
'B14':'Browser Secure cookies, origin/forwards and independent products/databases',
'B15':'Concurrent throttling, Retry-After and real window recovery',
'B16':'Fail-closed configuration and integrated Unicode password maximum',
'B17':'Known synthetic secret scans and constrained runtime/browser egress',
'B18':'Owned-resource cleanup, negative cleanup and foreign sentinel',
'B19':'Actual web build/start, keyboard browser flows and no-store',
'B20':'Historical hashes, products/prototype and targeted regression'}

def ref(path,**extra):return {'path':path,'sha256':sha(ROOT/path),**extra}
def main():
 historical=read(OLD);audit=read(AUDIT);pres=read(PRES);host=read(HOST);cleanup=read(CLEAN)
 runs=[]
 for p in sorted((ROOT/'docs/migration/p4-4-b-continuation').glob('p44bc-*.json')):
  if p.name.endswith('.running.json'):raise RuntimeError('Active checkpoint; finalization forbidden')
  d=json.loads(p.read_text())
  runner=ROOT/'docs/migration/p4-4-b-continuation/validators'/(d['runId']+'.py')
  browser=ROOT/'docs/migration/p4-4-b-continuation/validators'/(d['runId']+'.mjs')
  if not browser.exists():browser=browser.parent/'browser-v1.mjs'
  assert sha(runner)==d['sourceHashes']['scripts/validate_business_auth_continuation.py']
  assert sha(browser)==d['sourceHashes']['scripts/check_business_auth_continuation.mjs']
  runs.append((str(p.relative_to(ROOT)),d))
 assert runs and sha(ROOT/OLD)==audit['recoveredReceipt']['sha256']
 assert all(d['recoveryCheckpoint']['sha256']==sha(ROOT/AUDIT) for _,d in runs)
 for path,h in audit['currentImplementationHashes'].items():assert sha(ROOT/path)==h,path
 entries=[];missing=[]
 for case in REC:
  row={'id':case,'scope':SCOPES[case],'status':'PASS','recoveredEvidence':[],'continuationEvidence':[],'limitations':[]}
  for name in REC[case]:
   indexes=[i for i,s in enumerate(historical['steps']) if s['name']==name and s['passed']]
   if not indexes:missing.append(case+':historical:'+name);continue
   row['recoveredEvidence'].append(ref(OLD,step=name,index=indexes[0]))
  for name in NEW.get(case,[]):
   found=[(path,i) for path,d in runs for i,s in enumerate(d['steps']) if s['name']==name and s['passed']]
   if not found:missing.append(case+':continuation:'+name);continue
   path,i=found[-1];row['continuationEvidence'].append(ref(path,step=name,index=i))
  if row['recoveredEvidence']:row['limitations'].append('Historical auth receipt has no run-time source hash. Reused named checks remain historical; unchanged recovery hashes do not establish retroactive provenance.')
  if case=='B01':row['recoveredEvidence'] += [ref('docs/migration/'+f) for f in ['P4_4_B_IMAGE.json','P4_4_B_IMAGE_REBUILD.json','P4_4_B_BASE_MATRIX.json']]
  if case in ['B17','B18']:
   for path,d in runs:
    required=d['receiptSecretScan']['passed'] and d['cleanupPassed'] and d['temporaryDirectoryRemoved'] and d['sourceUnchanged'] and bool(d['rawLogScan']) and all(x['passed'] for x in d['rawLogScan'])
    if not required:missing.append(case+':scan/cleanup:'+path)
    row['continuationEvidence'].append(ref(path,fields=['receiptSecretScan','rawLogScan'] if case=='B17' else ['cleanup','cleanupPassed','hostRelaysClosed','temporaryDirectoryRemoved']))
  if case=='B18':
   clean=not host['temporaryDirectories'] and not host['matchingProcesses'] and all(v['exitCode']==0 for v in host['docker'].values()) and not any('p44' in n for v in host['docker'].values() for n in v['items']) and cleanup['status']=='PASS'
   if not clean:missing.append('B18:host cleanup')
   row['continuationEvidence'] += [ref(HOST),ref(CLEAN)]
  if case=='B17':row['continuationEvidence'].append(ref('docs/migration/P4_4_B_CONTINUATION_DOCKER.json'))
  if case=='B20':
   if pres['status']!='PASS':missing.append('B20:preservation')
   row['continuationEvidence'] += [ref(PRES)]
  if case=='B05':row['limitations'].append('Three alternating timing pairs include cold-start noise; observed medians differ. No statistical or formal timing indistinguishability demonstrated.')
  if case=='B07':row['limitations'].append('Boundary uses coherent fixture timestamps (8h lifetime), not eight hours of wall-clock waiting; production constants unchanged.')
  if case=='B14':row['limitations'].append('Ephemeral self-signed local HTTPS tests Secure transport; not a production TLS/proxy deployment.')
  if case=='B15':row['limitations'].append('Global in-memory single-instance budget resets on process restart; no distributed persistence.')
  if case=='B17':row['limitations'].append('Exact scans cover known synthetic values; secondary final-artifact scan is heuristic. Browser observes no external requests; internal Docker networks prevent successful server egress. No packet-level proof of absence of attempted egress.')
  row['relevantSourceHashes']={p:h for p,h in audit['currentImplementationHashes'].items() if p.startswith('templates/business-platform-auth/') or p.endswith('image-lock.json')}
  entries.append(row)
 for row in entries:
  if any(m.startswith(row['id']+':') for m in missing):row['status']='BLOCKED'
 known_failures={'p44bc-965191032d2d4a9a':'InfrastructureError: Step failed: B10-encoded-closed-4','p44bc-92ad5e384d4c427d':'UnboundLocalError: details withheld','p44bc-267055cd7ca7429b':'UnboundLocalError: details withheld'}
 for path,d in runs:
  if d['status']=='FAIL' and known_failures.get(d['runId'])!=d.get('error'):missing.append('unresolved-run:'+d['runId'])
 passed=not missing
 gates={k:'NOT_IMPLEMENTED' for k in ['resource-authorization','module-crud','generation','autonomy']}
 byid={r['id']:r['status'] for r in entries}
 mapping={'compatibility':['B01','B19'],'database-migrations':['B02','B03','B04','B11','B12','B13'],'authentication':['B03','B04','B05','B06','B07','B08','B10','B14','B15','B16','B17'],'auth-role-probes':['B09','B10','B11'],'build-tests':['B19'],'cleanup':['B18']}
 for gate,ids in mapping.items():gates[gate]='PASS' if all(byid[i]=='PASS' for i in ids) else 'BLOCKED'
 result={'format':'nexonova.p44b.granular-receipt.v1','phase':'P4.4-B','status':'PASS_WITH_LIMITATIONS' if passed else 'BLOCKED','readiness':'BLOCKED','humanReview':'PENDING','recoveryCheckpoint':ref(AUDIT),'matrix':entries,'gates':gates,'gateRequirements':mapping,'authRoleProbeScope':'Session and admin/member probes only; InternalRequest ownership is NOT_IMPLEMENTED','missingEvidence':missing,'validatorArchives':'docs/migration/p4-4-b-continuation/validators: SHA256 verified against each run','continuationRuns':[ref(p,status=d['status'],error=d.get('error'),sourceHashes=d['sourceHashes']) for p,d in runs],'preservation':ref(PRES),'hostCleanup':[ref(HOST),ref(CLEAN)],'versions':historical['versions'],'postgresVersion':historical['postgresVersion'],'imageLock':read('infrastructure/images/node-openssl/image-lock.json'),'finalizerSha256':sha(Path(__file__)),'historicalReceiptsModified':False,'productImplementationChanged':False,'intermediateFailures':[{'runId':d['runId'],'error':d.get('error'),'disposition':'Validator normalization expectation / resume variable corrected; passing checks reused individually; original FAIL retained.'} for p,d in runs if d['status']=='FAIL'],'limitations':['Historical auth provenance cannot be reconstructed retrospectively.','Controlled single-instance pilot; host and Docker daemon trusted; Linux/amd64 only.','Offline bootstrap recovery after total manual deletion and automatic crash recovery are not implemented.','Production vulnerability/security review remains pending; no deployment or external integration.','Rate limit memory only; no account recovery, external email/OAuth, resource authorization, CRUD, generation or autonomy.']}
 # Only sanitized referenced results and public source/image hashes enter the final artifact.
 text=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
 patterns=[r'postgres(?:ql)?://[^\s"\\]+:[^\s"\\]+@',r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----',r'(?i)(?:set-cookie|authorization):\s*[^\s]',r'(?i)session_token=[A-Za-z0-9%_.+/-]{16,}']
 matches=sum(len(re.findall(p,text)) for p in patterns)
 result['finalReceiptScan']={'status':'PASS' if matches==0 else 'FAIL','matches':matches,'method':'Secondary credential/cookie/private-key patterns over final JSON; exact synthetic-value scans live in each referenced continuation run receipt.'}
 if matches:raise RuntimeError('Final artifact withheld: secret pattern')
 (ROOT/OUT).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 print(result['status'],json.dumps(missing));return 0 if passed else 1
if __name__=='__main__':sys.exit(main())
