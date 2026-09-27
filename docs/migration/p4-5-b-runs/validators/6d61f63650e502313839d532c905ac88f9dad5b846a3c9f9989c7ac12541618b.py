#!/usr/bin/env python3
"""Finalize C01–C40 from immutable granular evidence, with explicit reuse and limitations."""
from validate_business_requests import *
from check_business_requests_evidence import evaluate,sethash
import re

def main():
 mainfile='p45b-3d044de39b4d4ba1.json';observed='p45b-24984b962cb0466e.json';schema='p45b-1c3e8a00fe4249d3.json';schemaresume='p45b-ba2c6a6f1698418a.json';build='p45b-b38e4bd8e33b4b57.json';closure='final-preservation-cleanup-d02.json'
 primary=json.loads((OUT/mainfile).read_text());observe=json.loads((OUT/observed).read_text());closed=json.loads((OUT/closure).read_text());approved=json.loads((ROOT/'docs/migration/P4_5_A_VALIDATION.json').read_text())
 assert primary['status']==observe['status']==closed['status']=='PASS'
 assert primary['cleanupPassed'] and observe['cleanupPassed'] and primary['secretScanPassed'] and observe['secretScanPassed']
 report={'format':'nexonova.p45b.granular-receipt.v2','phase':'P4.5-B','status':'IN_PROGRESS','humanReview':'REQUIRED_AFTER_COMPLETION','D02':{'authorization':'APPROVED_FOR_CONTROLLED_RESOLUTION / option A','resolution':'IMPLEMENTED_AND_VALIDATED','originalDiagnostic':'docs/migration/p4-5-b-runs/D02-page-vary.json','design':'docs/business-platform/P4_5_B_D02_RESOLUTION.md','priorCheckpointArchive':'docs/migration/p4-5-b-runs/d02-entry/','noRequirementRelaxation':True,'coreAuthUnchanged':True,'dependenciesUnpatched':True},'cases':{},'sourceHashes':{},'entry':{'path':'docs/migration/P4_5_B_ENTRY.json','sha256':sha(ROOT/'docs/migration/P4_5_B_ENTRY.json')},'continuationEntry':{'path':'docs/migration/p4-5-b-runs/D02_RESOLUTION_ENTRY.json','sha256':sha(OUT/'D02_RESOLUTION_ENTRY.json')},'versions':{**closed['versions'],'postgresql':'16.15','openssl':closed['openssl']},'images':closed['imageReferences'],'imageIds':closed['imageIds'],'readiness':'BLOCKED','generation':'NOT_IMPLEMENTED','autonomy':'NOT_IMPLEMENTED'}
 notes={
 'C01':'Fresh deploy/inventory/FK/CHECK/indexes recovered from schema run; new catalog verifies all nine types/nullability/defaults and literal enum.',
 'C02':'Reexecuted: auth-only upgrade with real credentials/sessions and unchanged auth data; combined migration reapply unchanged. Fresh path evidence also retained.',
 'C03':'Real 42501 negatives and allowed SQL recovered; new runtime effective INSERT9/SELECT9/UPDATE6 column grants exactly verified; bootstrap has no module grant.',
 'C04':'Real FK23503 orphan/User delete/User ID update, archived reference and bootstrap42501 recovered unchanged; module schema/SQL/grants hashes match.',
 'C05':'New HTTP creates A/B/admin, exact ownership/defaults/nine-field DTO and DB persistence; supplemental server-time window and UUIDv4 assertions.',
 'C06':'Real FK rejection followed by unchanged full business/User role snapshot.',
 'C07':'A/admin strict DTO negatives for owner/user/role/system/nested fields, constructor and __proto__; DB unchanged.',
 'C08':'A/B lists and complete owner-filtered pagination; archived excluded.',
 'C09':'Admin global active list/detail via HTTP and actual browser access to foreign resource; archived excluded.',
 'C10':'Own edit, close, edit while closed; versions and immutable identity values checked against DB/DTO.',
 'C11':'Member and admin valid reopen plus invalid close/reopen409 with full no-change snapshots.',
 'C12':'Member/admin archive from open/closed204; retained rows, original status, version+1 and archivedAt=updatedAt.',
 'C13':'Both member/admin: every command with missing/invalid/stale/maxInt versions;400/409 and unchanged DB.',
 'C14':'All actors API and actual browser archived invisibility, all mutation404, repeated archive404; retained DB rows.',
 'C15':'Own direct detail/edit, exact nine-field DTO and actual SSR own title without auth fields; full known-secret SSR scan in C36.',
 'C16':'Admin foreign edit/close/reopen/archive with same version rules and unchanged owner; browser admin edit/archive included.',
 'C17':'Foreign/absent/archived uniform404 signatures; forged cursor and identity headers retain owner filter.',
 'C18':'Horizontal edit current/stale versions plus forged role/owner headers404; full DB unchanged.',
 'C19':'Horizontal close/reopen/archive current/stale versions in open/closed/archived/absent cases, no changes.',
 'C20':'No cookie/forged/expired/revoked: all API operations401, pages login; real browser contexts and no DB effects.',
 'C21':'Real PG enum rejects invalid role; pure guard and actual service-entry deny-default unit probe (explicitly not a mock auth integration).',
 'C22':'Encoded/malformed/inexistent/foreign/archived ID cases across member/admin and commands; exact status/body/static headers, no cookie/metadata; timings descriptive only.',
 'C23':'Six synchronized real HTTP two-connection races A/A and A/admin; exactly one200+one409, version+1 and unmixed winning payload.',
 'C24':'Synchronized edit/close, close/archive, reopen/archive and owner/nonowner; one commit/version, no archive resurrection or foreign effect.',
 'C25':'214 tied-timestamp fixtures plus lifecycle rows; A/admin default20/1/100 traversal equals SQL ordered IDs without duplicates/omissions.',
 'C26':'Invalid/oversized/duplicated query400; forged canonical cursor never bypasses owner; archive between pages respects visibility.',
 'C27':'Unicode/scalar/length/whitespace/NUL/surrogate/body16KiB/media validation via unit+HTTP/DB; hostile text rendered without XSS in actual browser.',
 'C28':'Complete CSRF/method/header checks; original-vs-new launcher HTML/RSC comparison preserves all Next Vary tokens plus one Cookie. Browser navigation/final headers and anonymous redirect verified; no-store throughout.',
 'C29':'Separate real app and DB restarts; complete DB snapshot stable, live session valid, permitted detail and archived404 remain.',
 'C30':'DB stopped and SELECT/INSERT/UPDATE grants withdrawn separately:503 sane/fail-closed; restored DB equals snapshot, no partial writes.',
 'C31':'Two DB/network/volume/secret/cookie-prefix products with valid controls; cross-cookie401, cross-ID404, foreign cursor empty and zero row contamination.',
 'C32':'Deterministic composition/generate/validate/diff recovered; final recomposition hash identical and auth files identical. Only known SQL FK diff, never applied.',
 'C33':'Fixed npm ci; generated both clients; compile/typecheck/10 unit tests/build; real new launcher; no server DB imports in client JS; exact versions/digests verified.',
 'C34':'Playwright desktop keyboard create/list/detail/edit/close/reopen; two-tab409 preserves draft; horizontal denial, mobile admin edit/archive, archived invisible and no JS errors.',
 'C35':'Integrated generic login/signup-closed/probes/logout-replay; controlled before/at8h and no-refresh; session cookies local HTTP and real HTTPS browser secure attributes; original auth/core/bootstrapping intact.',
 'C36':'Known synthetic values scanned in app logs/SSR/client JS and serialized run; supplemental DB logs scanned with parameter logging disabled; browser no external calls, internal networks and negative egress probe. Final artifact heuristic scan separate.',
 'C37':'Final412 entry hashes; P3/P4.2/P4.3/P4.4 protected artifacts and prior receipts intact; products/prototype99 exact baselines;88 regression tests.',
 'C38':'Reexecuted success/failure/timeout/sentinel, both new runs cleaned; final own Docker/path/process inventory empty and prepared workspace removed.',
 'C39':'Consumer fail-closed checks case statuses, proof hashes/step indices, proof-set/source-set fingerprints, current sources; missing/altered evidence and non-PASS statuses tested.',
 'C40':'Actual parameterized Prisma SQL shows owner+active scope and LIMIT/CAS predicates; EXPLAIN, real pagination/load, connection counts8/8/8 and Docker resource measurements (not SLA).'}
 def refs(file,prefixes):
  path=OUT/file;data=json.loads(path.read_text());indexes=[i for i,s in enumerate(data.get('steps',[])) if any(s['name'].startswith(prefix) for prefix in prefixes)]
  assert indexes,(file,prefixes)
  assert all(data['steps'][i].get('passed') is True for i in indexes),(file,prefixes)
  return {'path':str(path.relative_to(ROOT)),'sha256':sha(path),'stepIndexes':indexes}
 recovered={'C01','C03','C04','C32'}
 for spec in approved['futureValidationMatrix']:
  c=spec['id'];e=[]
  if c in recovered:
   e.append(refs(schemaresume,['C32-']) if c=='C32' else refs(schema,[c+'-']))
  elif c=='C37':e.append(refs(closure,['C37-']))
  elif c=='C38':e.append(refs(closure,['C38-']))
  elif c=='C39':e.append(refs('evidence-consumer-d02.json',['C39-']))
  else:
   assert primary['cases'][c]['status']=='PASS',c
   e.append(refs(mainfile,[c+'-']))
  if c=='C01':e += [refs(mainfile,['C01-']),refs(observed,['C01-'])]
  if c=='C03':e.append(refs(observed,['C03-']))
  if c=='C05':e.append(refs(observed,['C05-']))
  if c=='C08':e.append(refs(mainfile,['C25-']))
  if c in ['C09','C14','C20','C27','C28']:e.append(refs(mainfile,['C34-browser-']))
  if c=='C16':e.append(refs(mainfile,['C09-','C34-browser-flow']))
  if c=='C17':e.append(refs(mainfile,['C22-identical-errors']))
  if c=='C21':e.append(refs(build,['C33-unit']))
  if c=='C28':e.append(refs(observed,['C28-']));e.append(refs(closure,['C28-']))
  if c=='C32':e.append(refs(closure,['C32-']))
  if c=='C33':e.append(refs(build,['C33-']));e.append(refs(closure,['C33-']));e.append(refs(mainfile,['start-requests-app']))
  if c in ['C36','C40']:e.append(refs(observed,[c+'-']))
  report['cases'][c]={'status':'PASS','objective':spec['objective'],'executed':notes[c],'evidence':e,'proofSetSha256':sethash(e),'recoveredEvidence':c in recovered,'reuseJustification':'Schema/migration/grants and auth inputs byte-identical; D02 only changes module response emission. Final recomposition/catalog/grants verification corroborates reuse.' if c in recovered else 'New execution after D02; no prior aggregate PASS inherited.','limitations':[]}
 # Source/validator archive: exact bytes remain reviewable even if a future continuation changes files.
 sources=[*OVERLAY.rglob('*'),*ROOT.glob('scripts/*business_requests*'),ROOT/'scripts/business_requests_probe.py',ROOT/'scripts/validate_business_auth.py',ROOT/'factory/business_infrastructure.py',ROOT/'templates/business-platform-auth/package-lock.json',ROOT/'docs/business-platform/P4_5_A_PROPOSAL.md',ROOT/'docs/migration/P4_5_A_VALIDATION.json',ROOT/'docs/business-platform/P4_5_B_D02_RESOLUTION.md']
 for p in sources:
  if p.is_file():report['sourceHashes'][str(p.relative_to(ROOT))]=sha(p)
 report['sourceSetSha256']=sethash(report['sourceHashes'])
 for p in sources:
  if p.is_file() and p.parent==ROOT/'scripts':shutil.copyfile(p,OUT/'validators'/(sha(p)+p.suffix))
 # Verify source correspondence for reused schema evidence rather than silently rebaselining it.
 report['recoveredInputChecks']={}
 oldschema=json.loads((OUT/schema).read_text())
 for p,h in oldschema['sourceHashes'].items():
  if p.startswith('modules/'):
   assert sha(ROOT/p)==h,p;report['recoveredInputChecks'][p]=h
 report['limitations']=[
  'Inherited historical P4.4-B recovered provenance is incomplete; this phase does not strengthen it retrospectively. New runs have explicit source hashes and validator archives.',
  'No formal timing indistinguishability; uniform errors do not prove absence of timing enumeration. P4.4-B measured timing differences remain an accepted limitation.',
  'In-memory login rate limiting only for controlled single-instance pilot; restart resets counters. No production scalability/availability/SLA claim.',
  'Linux/amd64 trusted Docker host; local self-signed HTTPS tests do not demonstrate production TLS/proxy/deployment.',
  'Known-value and heuristic scans are not exhaustive security audits. Browser observes zero external calls; internal-network negative probe is not packet capture of every attempt.',
  'A hard host/daemon interruption may require manual cleanup recovery; ordinary success/failure/timeout and owned-resource isolation were tested.',
  'D02 requires the new start-requests.mjs launcher. Hosting/standalone/proxy or Next version changes require header/SSR/RSC/auth regression. No dependency patch or core/auth modification.',
  'SQL-managed FK is intentionally absent from Prisma relation metadata. Never apply migrate diff blindly; its expected FK DROP was not applied.',
  'Pagination is deterministic on a stable dataset, not a snapshot across concurrent writes. No auto retry after uncertain write outcomes; archiving is terminal.',
  'Resource authorization PASS covers this InternalRequest module only, not a generic authorization engine or multitenancy. Generation/autonomy remain NOT_IMPLEMENTED and global readiness BLOCKED.',
  'Production vulnerability/security review, password recovery, account administration and deployment remain outside this phase.'
 ]
 report['cases']['C22']['limitations']=['No formal timing guarantee.'];report['cases']['C35']['limitations']=['Inherited timing, single-instance rate limit and local TLS limitations.'];report['cases']['C36']['limitations']=['Exact known values plus heuristics; not exhaustive audit.'];report['cases']['C38']['limitations']=['Manual recovery may be needed after abrupt host/daemon failure.'];report['cases']['C40']['limitations']=['Pilot measurements only, no SLA.']
 report['evaluation']=evaluate(report);assert not report['evaluation']['invalidCases'],report['evaluation'];report['gates']=report['evaluation']['gates'];assert all(x['status']=='PASS' for x in report['gates'].values())
 report['gates']['resource-authorization']['scope']='InternalRequest server-side ownership/admin policy only; no generic global authorization implementation.'
 report['gates']['auth-role-probes']={'status':'PASS','scope':'Integrated unchanged P4.4-B session/role probes; C35.'}
 report['gates']['generation']={'status':'NOT_IMPLEMENTED'};report['gates']['autonomy']={'status':'NOT_IMPLEMENTED'}
 report['status']='PASS_WITH_LIMITATIONS';report['runtimeConnections']=primary['runtimeConnectionCounts'];report['browserChecks']=primary['browser'];report['secureBrowser']=primary['secureBrowser'];report['D02BrowserHeaders']=observe['browser'];report['cleanup']={'status':'PASS','receipt':str((OUT/closure).relative_to(ROOT)),'ownResourcesRemaining':False}
 report['artifactIndex']=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in sorted(OUT.glob('*.json'))]
 new=[str(p.relative_to(ROOT)) for p in sources if p.is_file() and str(p.relative_to(ROOT)) not in json.loads((ROOT/'docs/migration/P4_5_B_ENTRY.json').read_text())['hashes']];report['implementationAndValidatorFiles']=sorted(set(new))
 write(ROOT/'docs/migration/P4_5_B_FINAL_RECEIPT.json',report)
 lines=['# P4.5-B — Informe final','','**Recomendación: PASS_WITH_LIMITATIONS. C01–C40: PASS. Pendiente revisión humana.**','','## Estado recuperado y resolución D02','','Se partió del checkpoint bloqueado, sin reiniciar schema/FK/grants. Sus hashes y artefactos se verificaron antes de cambiar implementación. El checkpoint previo está preservado byte a byte en `p4-5-b-runs/d02-entry/`; `D02-page-vary.json` permanece intacto. La autorización humana fue `D02 = APPROVED_FOR_CONTROLLED_RESOLUTION`, opción A exclusivamente.', '', 'La solución agrega `scripts/start-requests.mjs` y `requests-response-boundary.mjs` dentro del overlay. Usa la API pública de Next y una frontera propia por respuesta, limitada a `/requests` y `/api/requests`. En emisión final conserva los tokens Vary de Next y agrega Cookie sin duplicados; mantiene no-store. No parchea dependencias/prototipos globales, no cambia core/auth ni la política de C28, ni altera respuestas de rutas ajenas.', '', 'Comparación real con launcher original: member/admin, HTML/RSC, éxito/error, exacta unión de tokens y rutas login/auth ajenas. Navegación real y redirect anónimo confirmaron headers finales. El producto compuesto con este módulo debe usar el launcher nuevo; el launcher auth original permanece intacto y no incorpora D02.', '', 'D02 obligó a repetir la integración HTTP/navegador afectada por el launcher. Solo se recuperaron pruebas independientes del schema/SQL/grants con inputs idénticos y nueva corroboración. Ningún PASS agregado previo sustituyó checks individuales.', '', '## Implementación y pruebas','','Overlay aislado con InternalRequest, migración SQL, grants, DTO estricto, servicios/repositorio, autorización por owner/admin, CAS, handlers contractuales y UI mínima. No se generó producto Factory ni hubo deployment.', '', 'Persistencia: nueve campos, open/closed, owner de sesión, archivado terminal invisible a todos. FK real hacia app.User(id), RESTRICT/RESTRICT, validada/no diferible, User intacto sin inversa Prisma. Composición auth+business reproducible; migración mediante migrate deploy, DB vacía/upgrade con credenciales y sesiones reales, reaplicación estable. TechnicalSmoke permanece separado y no aparece en DB auth/business.', '', 'Grants runtime: SELECT; INSERT nueve columnas; UPDATE únicamente title/description/status/updatedAt/archivedAt/version. DDL/DELETE/TRUNCATE/id/ownerId/createdAt/historial rechazados. Bootstrap técnico separado sin privilegios del módulo; Better Auth, roles y sesiones sin cambios.', '', 'CAS atómico probado con dos conexiones HTTP sincronizadas, seis carreras edit/edit y carreras de estado/archivo/non-owner. Rechazos uniformes404, versiones inválidas/obsoletas/overflow, spoofing y entradas hostiles probados. Paginación comparada contra SQL sobre más de200 filas con timestamps iguales.', '', 'Playwright real: flujo teclado, desktop/mobile, dos pestañas409 conservando borrador, admin y rechazo horizontal, XSS como texto, archivo invisible. SSR/RSC/navegación y headers comparados. Auth integrada: login genérico, signup cerrado, logout/replay, límite8h controlado y sin refresh, Secure/HttpOnly/SameSite en HTTPS real local.', '', 'App y PostgreSQL reiniciados; datos/sesiones/archivo conservaron la política. DB caída y grants retirados dieron503 sin escrituras parciales. Dos productos aislados por DB/red/volumen/secreto/prefijo rechazaron cookies/IDs cruzados sin contaminación.', '', 'SQL real emitido por Prisma mostró filtro owner/activo y LIMIT; UPDATE incluyó owner/activo/versión. EXPLAIN y cargas medidas; conexiones runtime8/8/8 (pool empresarial máximo5, pool auth separado). Son mediciones de piloto, no SLA.', '', 'Scans conocidos cubrieron logs app/DB, SSR, bundle y serialización. La instrumentación SQL final deshabilitó parámetros antes de loguear; su scan DB pasó. Un probe anterior registró solo statements saneados y no completa el scan DB: para C36 se usa el receipt posterior. Navegador0 llamadas externas, redes internas y probe de egress negativo.', '', '## Evidencia principal','','| Artefacto | Alcance |','|---|---|',f'| {build} | npm ci fijo, generate, compile/typecheck,10 unitarios y build |',f'| {mainfile} | Integración real completa,2170 checks, PostgreSQL/HTTP/Playwright/HTTPS |',f'| {observed} | SQL real, grants/defaults exactos, headers navegador, scan DB y egress |',f'| {closure} | Preservación, versiones/digests, recomposición y cleanup final |','| evidence-consumer-d02.json | Consumer fail-closed,10 pruebas |','| preservation-tests-d02.json | 88 tests P3/P4.2/productos |','| cleanup-scenarios-d02.json | Éxito/fallo/timeout y centinela |','','Los receipts originales fallidos siguen disponibles. Las referencias por índice y SHA256 de cada caso están en `P4_5_B_FINAL_RECEIPT.json`; los validadores se archivan por hash. El código escrito pero no ejecutado en el checkpoint anterior fue ejecutado durante esta continuación antes de promover casos.', '', '## Versiones y digests','']
 lines+=['- '+k+': `'+v+'`' for k,v in report['versions'].items()]+['', 'Node/OpenSSL: `'+auth.IMAGE+'`','', 'PostgreSQL: `'+auth.base.PG+'`','','## Matriz final','','| Caso | Estado | Evidencia y alcance |','|---|---|---|']
 lines+=['| '+c+' | PASS | '+row['executed'].replace('|','/')+' |' for c,row in report['cases'].items()]
 lines+=['','## Gates','','| Gate | Estado |','|---|---|']+['| '+g+' | '+row['status']+' |' for g,row in report['gates'].items()]+['| readiness global | BLOCKED |','','Resource-authorization PASS está limitado a InternalRequest; no declara una autorización global genérica. No quedó caso obligatorio FAIL/BLOCKED/NOT_EXECUTED. El consumer recalculó los gates desde referencias válidas, sin heredar gates del checkpoint.', '', '## Preservación y cleanup','','412 hashes de entrada idénticos; P3/P4.2/P4.3/P4.4-A/P4.4-B y contratos sin reescritura. Corporate-site preservado en snapshot; nexonova-website/synthetic-website contra manifests originales, con excepción histórica next-env.d.ts reportada separadamente; prototipo99 archivos con conjunto/hash exactos.88 pruebas finales aprobadas.', '', 'Cleanup final: cero contenedores/redes/volúmenes con label propio, workspace preparado y directorios temporales propios eliminados; sin procesos Node de validadores ni browsers Playwright pendientes. Centinela de otro owner intacto y luego retirado por su creador. Contenedores ajenos no modificados. No se borraron caches compartidas del operador.', '', '## Archivos creados/modificados','','Durante P4.5-B se crearon los archivos bajo `modules/internal-requests/0.1.0/files/`, runners propios y documentación/receipts. D02 añadió launcher/frontera y pruebas, adaptó runners y actualizó el cierre/checkpoint. El core y los contratos aprobados permanecieron byte-idénticos. Inventario completo en `implementationAndValidatorFiles` y sourceHashes del receipt.', '', '## Limitaciones restantes','']
 lines+=['- '+x for x in report['limitations']]
 lines+=['','## Operación y revisión humana','','El overlay es una composición validada de laboratorio, no un deployment. Para reproducir: ejecutar el runner de build (recrea workspace si no existe), luego integración; el arranque compuesto usa `node scripts/start-requests.mjs`. Migraciones se aplican separadamente con `prisma migrate deploy --config prisma.requests.config.ts`, nunca al arrancar ni con db push. No aplicar el DROP FK sugerido por diff. La DB auth-only puede ampliarse con el historial combinado revisado.', '', 'Los runners de observabilidad, cleanup y cierre tienen receipts independientes. Un nuevo ciclo debe generar nuevos receipts y no sobrescribir los ya aprobados. Revalidar headers/SSR/RSC/auth si cambia Next, launcher o infraestructura HTTP.', '', '**P4.5-B se detiene aquí para revisión humana. No se inició P4.6/P4.7, generación ni autonomía.**']
 (ROOT/'docs/migration/P4_5_B_FINAL_REPORT.md').write_text('\n'.join(lines)+'\n')
 progress={'phase':'P4.5-B','status':'PASS_WITH_LIMITATIONS','humanReviewRequired':True,'D02':'RESOLVED — controlled option A, no C28 relaxation','receipt':'docs/migration/P4_5_B_FINAL_RECEIPT.json','report':'docs/migration/P4_5_B_FINAL_REPORT.md','cases':{c:'PASS' for c in report['cases']},'gates':report['gates'],'readiness':'BLOCKED','generation':'NOT_IMPLEMENTED','autonomy':'NOT_IMPLEMENTED','temporaryWorkspaceRemoved':True,'historicalReceiptsUnchanged':True,'nextAction':'Human review only. Do not start P4.6/P4.7.'};write(ROOT/'docs/migration/P4_5_B_PROGRESS.json',progress)
 # Scan newly serialized final documents and JSON artifacts. Known-value scans were performed
 # inside each live fixture before its secrets were destroyed, rather than persisting those values.
 files=[ROOT/'docs/migration/P4_5_B_FINAL_RECEIPT.json',ROOT/'docs/migration/P4_5_B_FINAL_REPORT.md',ROOT/'docs/migration/P4_5_B_PROGRESS.json',*OUT.glob('*.json')]
 patterns=[r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'postgres(?:ql)?://[^\s\"\'<>]+:[^\s\"\'<>]+@']
 hits=[str(p.relative_to(ROOT)) for p in files if any(re.search(pattern,p.read_text()) for pattern in patterns)];assert not hits,hits
 scan={'phase':'P4.5-B','status':'PASS','scope':'Final serialized documents/run JSON heuristic scan, source/evidence consumer verification','filesScanned':len(files),'matches':hits,'knownValuesScanReceipts':[mainfile,observed],'limitations':'Heuristic scan complements live-fixture exact known-value scans; not exhaustive audit.','finalReceiptSha256':sha(files[0]),'finalReportSha256':sha(files[1]),'allCasesPass':True,'allRequiredGatesPass':True};write(ROOT/'docs/migration/P4_5_B_CHECKPOINT_CHECK.json',scan)
 print(json.dumps({'recommendation':report['status'],'cases':len(report['cases']),'gates':report['gates'],'cleanup':'PASS'},indent=2))
if __name__=='__main__':main()
