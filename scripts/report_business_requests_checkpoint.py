#!/usr/bin/env python3
"""Evidence index for mandatory D02 stop. Does not turn pending cases into PASS."""
from validate_business_requests import *
from check_business_requests_evidence import evaluate

def main():
 schema='p45b-1c3e8a00fe4249d3.json';resume='p45b-ba2c6a6f1698418a.json';integration='p45b-8602d754baa04267.json';build='p45b-fe121295780248bc.json';diagnostic='p45b-0a12a2069e164369.json'
 approved=json.loads((ROOT/'docs/migration/P4_5_A_VALIDATION.json').read_text())
 report={'format':'nexonova.p45b.granular-receipt.v1','phase':'P4.5-B','status':'BLOCKED','completion':'INCOMPLETE — mandatory stop for human review; not approval to start P4.6/P4.7','entry':{'path':'docs/migration/P4_5_B_ENTRY.json','sha256':sha(ROOT/'docs/migration/P4_5_B_ENTRY.json')},'blocker':{'id':'D02','status':'PENDING_HUMAN_REVIEW','path':str((OUT/'D02-page-vary.json').relative_to(ROOT)),'sha256':sha(OUT/'D02-page-vary.json')},'cases':{},'sourceHashes':{},'versions':{'node':'22.23.2','next':'15.5.25','react':'19.2.8','typescript':'5.9.3','prisma':'7.5.0','better-auth':'1.7.5','pg':'8.16.3','postgresql':'16.15','openssl':'3.0.20'},'images':{'node':auth.IMAGE,'postgres':auth.base.PG},'readiness':'BLOCKED','generation':'NOT_IMPLEMENTED','autonomy':'NOT_IMPLEMENTED'}
 passed={'C01','C02','C03','C04','C05','C06','C07','C08','C10','C12','C16','C18','C23','C24','C25','C26','C32','C37','C38','C39'}
 notes={
 'C01':'Fresh deploy/tables/nine columns/FK/CHECK/indexes from schema run; types/defaults/enum/validated nondeferrable FK independently inspected in integration.',
 'C02':'Fresh reapply and auth-only upgrade with real users, credentials and sessions; data byte-identical and migration history stable.',
 'C03':'Real runtime INSERT/SELECT/UPDATE and 42501 DDL/DELETE/TRUNCATE/immutable columns/history negatives; grants captured in integration.',
 'C04':'Real bootstrap module denials, orphan FK, User delete/update RESTRICT, archived owner RESTRICT and no-orphan assertion.',
 'C05':'Three actors create, persisted SQL row, exact nine-field DTO, ownership and defaults.',
 'C06':'Invalid FK insert and complete business/User role snapshot unchanged.',
 'C07':'Create/PATCH unknown fields including owner/user/role/system fields and nested payloads rejected; A/admin; full snapshot unchanged.',
 'C08':'A/B own lists; extended A/admin pagination evidence in C25. No archived rows returned.',
 'C09':'HTTP admin list/detail passed; required browser assertions NOT_EXECUTED.',
 'C10':'Owner edit/close/edit-closed with successive versions and immutable identity fields.',
 'C11':'Member valid reopen and invalid close/reopen passed; admin invalid-transition variant remains NOT_EXECUTED.',
 'C12':'Archive from open by member and closed by admin; DB retained, status unchanged, timestamp equality and version increment.',
 'C13':'Member invalid/stale/overflow commands passed; full admin variant set remains NOT_EXECUTED.',
 'C14':'All actors API list/detail/mutations on archived passed; required browser assertions NOT_EXECUTED.',
 'C15':'Owner direct API detail/edit and page HTTP200 observed; granular HTML/DTO exposure scan remains NOT_EXECUTED.',
 'C16':'Admin cross-owner detail (C09), edit/close/reopen/archive, owner invariant after each operation.',
 'C17':'Foreign/absent HTTP404 body equal; expanded header comparison/cursor impersonation set remains partial.',
 'C18':'Foreign edit with current/stale version and spoofed role/owner headers404; DB snapshot unchanged.',
 'C19':'Foreign open and absent actions/current-stale versions, archived actions passed; active-closed foreign variant remains NOT_EXECUTED.',
 'C20':'NOT_EXECUTED; stopped before session-tail block. Login setup is not this case.',
 'C21':'Real PostgreSQL invalid-role rejection and pure guard test passed; explicit service-entry deny tests remain NOT_EXECUTED. Earlier provisional case PASS is not inherited.',
 'C22':'Member malformed/encoded/foreign/absent/archived IDs yielded uniform404 per action; full admin variants/header comparison remain NOT_EXECUTED.',
 'C23':'Six real HTTP races with two worker threads/connections synchronized by barrier, A/A and A/admin, exactly one200+one409, version+1, no mixed payload.',
 'C24':'Real edit/close, close/archive, reopen/archive and owner/nonowner races; one commit/version increment, nonowner404, archived invisible.',
 'C25':'214 tied-time fixtures plus lifecycle rows; default/1/100 limits for A/admin; exact SQL ordered IDs, no duplicate/omission.',
 'C26':'Malformed/oversized/duplicate/unknown query400; forged well-formed cursor retains owner scope; archive between pages hidden.',
 'C27':'HTTP Unicode/length/NUL/surrogate/contenttype/body cap passed; DOM/XSS/browser checks NOT_EXECUTED.',
 'C28':'FAIL: APIs origins/methods/no-store/Vary Cookie pass. Page200/no-store, but Next replaces Vary and removes Cookie. Confirmed raw repeated headers; D02.',
 'C29':'NOT_EXECUTED; app/DB persistence restart stage not reached.',
 'C30':'NOT_EXECUTED; DB down/revoked-grants stage not reached.',
 'C31':'NOT_EXECUTED; second-product runtime fixture not reached.',
 'C32':'Two deterministic compositions, generate/validate, unchanged auth files; real diff only expected manually managed FK omission; DROP never applied.',
 'C33':'npm fixed install, compile, 8 unit tests, typecheck/build and actual app start passed; client-bundle secret/server-import scan NOT_EXECUTED.',
 'C34':'NOT_EXECUTED; browser runner written but never invoked. No browser PASS claimed.',
 'C35':'NOT_EXECUTED; real login setup is not the auth regression matrix.',
 'C36':'Per-run serialized known-secret scans passed; broader logs/SSR/browser/bundle/network scans NOT_EXECUTED.',
 'C37':'412 entry hashes, products and prototype99 exact sets/hashes preserved; 88 pytest tests passed. Historical next-env exception retained.',
 'C38':'Real success/failure/timeout cleanup, foreign sentinel survives then owner removes; final no owned Docker/temp resources.',
 'C39':'10 evidence-consumer tests: missing cases/evidence/hash/steps/source and FAIL/BLOCKED/NOT_EXECUTED fail closed. Synthetic tests validate consumer only.',
 'C40':'NOT_EXECUTED; EXPLAIN/pool/load/resource measurement block not reached.'}
 def refs(file,prefixes):
  p=OUT/file;data=json.loads(p.read_text());indexes=[i for i,s in enumerate(data.get('steps',[])) if any(s['name'].startswith(prefix) for prefix in prefixes)]
  return [{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'stepIndexes':indexes}] if indexes else []
 for spec in approved['futureValidationMatrix']:
  c=spec['id'];evidence=refs(integration,[c+'-'])
  if c in ['C01','C03','C04']:evidence+=refs(schema,[c+'-'])
  if c=='C08':evidence+=refs(integration,['C25-'])
  if c=='C16':evidence+=refs(integration,['C09-'])
  if c=='C32':evidence=refs(resume,['C32-'])+refs(schema,['C01-real-fk'])
  if c=='C33':evidence+=refs(build,['C33-'])+refs(integration,['start-auth-app'])
  if c=='C28':evidence+=refs(diagnostic,['C28-'])
  if c=='C37':evidence=refs('preservation-final.json',['C37-'])
  if c=='C38':evidence=refs('cleanup-final.json',['C38-'])
  if c=='C39':evidence=refs('evidence-consumer.json',['C39-'])
  report['cases'][c]={'status':'FAIL' if c=='C28' else 'PASS' if c in passed else 'NOT_EXECUTED','objective':spec['objective'],'evidence':evidence,'executedAndRemaining':notes[c],'historicalEvidenceReused':'Entry baselines only; no historical aggregate PASS substitutes C-case execution.'}
 files=[*OVERLAY.rglob('*'),*ROOT.glob('scripts/*business_requests*')]
 for p in files:
  if p.is_file():report['sourceHashes'][str(p.relative_to(ROOT))]=sha(p)
 report['sourceHashes']['docs/business-platform/P4_5_A_PROPOSAL.md']=sha(ROOT/'docs/business-platform/P4_5_A_PROPOSAL.md')
 report['sourceHashes']['docs/migration/P4_5_A_VALIDATION.json']=sha(ROOT/'docs/migration/P4_5_A_VALIDATION.json')
 report['limitations']=['D02 is a blocking unsatisfied approved requirement, not an accepted limitation.','Unexecuted source/browser scripts are provisional and must be reviewed/executed after D02 resolution.','Inherited: incomplete provenance of historical recovered auth evidence; no formal timing indistinguishability; in-memory rate limit for a controlled single instance; trusted local Docker host/TLS fixtures; manual recovery on abrupt host failure; known-value/heuristic scans are not exhaustive.','Scalar Prisma ownerId with SQL FK: migrate diff reports expected FK removal; never apply automatically.','Keyset pagination is not a stable snapshot under writes; no automatic retry after uncertain write response.']
 report['evaluation']=evaluate(report);report['gates']=report['evaluation']['gates'];report['resourceAuthorizationScope']='InternalRequest only; gate BLOCKED, not global authorization implementation.'
 report['inheritedEntryGates']={x:'PASS' for x in ['compatibility','database-migrations','authentication','auth-role-probes','build-tests','cleanup']};report['entryGateNote']='Approved P4.4-B entry remains intact; P4.5-B integrated gates below are independently BLOCKED until all required cases pass.'
 report['artifactIndex']=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in sorted(OUT.glob('*.json'))]
 write(ROOT/'docs/migration/P4_5_B_FINAL_RECEIPT.json',report)
 lines=['# P4.5-B — Checkpoint de cierre por revisión humana D02','','**Resultado: BLOCKED. Implementación parcial; P4.5-B no está completada ni aprobada.**','','## Motivo de detención','', 'C28 exige `Cache-Control: no-store` y `Vary: Cookie` también en páginas. Next **15.5.25** reemplaza el Vary configurado por middleware al renderizar App Router. Se observó HTTP 200, `no-store` y Vary exclusivo de Next/Accept-Encoding. La inspección raw `get_all(Vary)` descartó un error de aplanamiento del validador. Las APIs sí conservan `Vary: Cookie`.', '', 'El template instalado `next/dist/build/templates/app-page.js:293` ejecuta `res.setHeader(\'Vary\', varyHeader)`. D02 contiene hashes, líneas y observaciones reproducidas. No se parcheó Next, core, arranque, auth ni el criterio aprobado. No se afirma una fuga de caché demostrada; se informa el incumplimiento preciso del diseño. La regla humana 9 requiere detenerse antes de cambiar esos controles.', '', '### Decisión humana pendiente','', '**Opción A recomendada:** revisar una frontera de respuesta específica del módulo que agregue `Cookie` después del render de Next, preservando los valores Vary del framework. Debe mantener intactos core/auth y validar HTML/RSC, navegación, errores, redirect/login, bootstrap, lifecycle y cleanup. Es una propuesta de revisión, no una solución implementada o demostrada.', '', '**Opción B:** revisar explícitamente C28 para aceptar `no-store` verificado en páginas sin exigir `Vary Cookie`, manteniéndolo en APIs. Cambia el requisito aprobado y no se adoptó automáticamente. No se deben reescribir los receipts aprobados para hacerlo pasar.', '', '## Trabajo y evidencia','', 'Snapshot de entrada propio anterior a cambios: `P4_5_B_ENTRY.json`, 412 hashes. Se creó exclusivamente overlay `modules/internal-requests/0.1.0/files`, runners de validación y documentación P4.5-B. Los documentos P4.5-A ya existían y permanecieron intactos.', '', 'Implementados schema compuesto, migración SQL, grants, DTO estricto, servicios/repository, visibilidad server/DB, CAS atómico, handlers contractuales y UI mínima. **La UI y los runners de navegador/extra no se ejecutaron**; su existencia no es evidencia.', '', 'La FK PostgreSQL real `InternalRequest.ownerId → app.User(id)` es RESTRICT/RESTRICT, validada/no diferible. User y auth permanecen intactos, sin relación inversa. La migración se aplicó con migrate deploy a DB vacía y DB auth con credenciales/sesiones reales; reaplicación estable. Diff únicamente anuncia la FK SQL no representada por Prisma: nunca aplicado.', '', 'Runtime: SELECT tabla; INSERT nueve columnas; UPDATE solo title/description/status/updatedAt/archivedAt/version. Negativas reales42501 para DDL/DELETE/TRUNCATE/owner/id/createdAt/historial. Bootstrap sin acceso módulo. No ALL, RLS ni ampliación auth.', '', 'Se ejecutaron carreras HTTP con barrera y conexiones distintas respaldadas por PostgreSQL: un commit por versión; también carreras de transiciones/archivo/no-owner. Paginación comparada con SQL sobre más de200 filas. Los checks detallados y los índices de pasos están en el receipt granular.', '', 'Fallos conservados: comparación C32 inicialmente demasiado estricta sobre schema qualifier, nombre erróneo de script npm, symlinks perdidos en copia temporal, lectura inicial case-sensitive de headers, y fallo real C28. Los arreglos de preparación/validador se reejecutaron sin ocultar receipts anteriores. El runner ahora conserva symlinks. Los PASS granulares recuperables de un run fallido se enlazan por índice y hash; no se hereda su estado agregado.', '', '## Versiones e imágenes','']
 lines+=['- '+k+': `'+v+'`' for k,v in report['versions'].items()]
 lines+=['','Node/OpenSSL: `'+auth.IMAGE+'`','', 'PostgreSQL: `'+auth.base.PG+'`','','## Matriz C01–C40','','PASS indica caso completo de este checkpoint; NOT_EXECUTED puede contener subchecks válidos pero queda incompleto. FAIL conserva el requisito incumplido.','','| Caso | Estado | Ejecutado / pendiente |','|---|---|---|']
 lines += ['| '+c+' | '+v['status']+' | '+v['executedAndRemaining'].replace('|','/')+' |' for c,v in report['cases'].items()]
 lines+=['','## Gates P4.5-B','','| Gate | Estado |','|---|---|']+['| '+g+' | '+v['status']+' |' for g,v in report['gates'].items()]
 lines+=['| generation | NOT_IMPLEMENTED |','| autonomy | NOT_IMPLEMENTED |','| readiness global | BLOCKED |','','Los gates de entrada de P4.4-B siguen preservados; no equivalen al PASS de la composición ampliada. Resource-authorization/module-crud **no fueron promovidos a PASS**. No hubo P4.6/P4.7 ni generación/deployment.', '', '## Preservación, cleanup y límites','', 'Comparados todos los412 hashes de entrada sin diferencias. Productos nexonova-website/synthetic-website contra sus manifests originales; prototipo99 archivos con conjunto exacto; corporate-site/contracts/receipts históricos contenidos en snapshot. Excepción histórica next-env.d.ts de Next mantenida separadamente. **88 tests de preservación/contratos PASS**. El primer intento con Python de sistema carecía de pytest; se usó la venv existente, sin instalar dependencias.', '', 'Cleanup PASS: éxito/fallo/timeout con centinela; cero recursos Docker con label propio, ningún directorio temporal propio pendiente, workspace preparado eliminado. Contenedores ajenos se inventariaron sin modificarlos. Relays cerrados al finalizar cada runner. No navegador fue iniciado. Evidencia: cleanup-scenarios.json y cleanup-final.json.', '', 'Scans conocidos por run antes de serialización pasaron; el scan integral C36 no se ejecutó. No fortalecer las limitaciones heredadas de P4.4-B: provenance histórica, timing sin garantía formal, rate limit en memoria de una instancia, TLS/host de prueba, recovery tras interrupción y scans no exhaustivos.', '', '## Reanudación autocontenida','', '1. Resolver D02 humanamente antes de cambiar arquitectura, core o requisito; registrar nueva decisión sin alterar receipts históricos.', '2. Leer ENTRY, FINAL_RECEIPT, D02 y PROGRESS; verificar sourceHashes actuales y todos los hashes históricos.', '3. Recrear workspace desde core+overlay con compose; instalar desde lockfile y generar ambos clientes. El workspace temporal anterior fue eliminado. Para build, adaptar el runner que hoy apunta al preparedWorkspace anterior: no asumir que ese path existe.', '4. Tras la resolución, probar C28 prioritariamente. `--resume-pages` limita la reanudación; el fixture puede necesitar setup nuevo. Los runners extra/browser siguen sin validación real y no deben considerarse listos por existir.', '5. Completar cada subcaso pendiente indicado, reevaluar source changes y repetir solo dependencias/casos invalidados. Guardar nuevos receipts inmutables. No repetir indiscriminadamente la matriz demostrada.', '6. Completar browser/auth/isolation/restarts/EXPLAIN/scans y cierre de gates; cleanup y revisión humana final.', '', 'El índice de archivos y hashes fuente está en `P4_5_B_FINAL_RECEIPT.json`. Este documento cierra el intento por el bloqueo, **no la fase**.']
 (ROOT/'docs/migration/P4_5_B_FINAL_REPORT.md').write_text('\n'.join(lines)+'\n')
 progress={'phase':'P4.5-B','status':'BLOCKED','blocker':'D02 — C28 pages Vary Cookie overridden by Next 15.5.25','humanReviewRequired':True,'entry':'docs/migration/P4_5_B_ENTRY.json','receipt':'docs/migration/P4_5_B_FINAL_RECEIPT.json','report':'docs/migration/P4_5_B_FINAL_REPORT.md','cases':{c:v['status'] for c,v in report['cases'].items()},'gates':report['gates'],'readiness':'BLOCKED','generation':'NOT_IMPLEMENTED','autonomy':'NOT_IMPLEMENTED','temporaryWorkspaceRemoved':True,'historicalReceiptsUnchanged':True,'nextAction':'Resolve D02 before implementation continuation. No P4.6/P4.7.'}
 write(ROOT/'docs/migration/P4_5_B_PROGRESS.json',progress)
 print(json.dumps({'status':report['status'],'cases':{state:sum(v['status']==state for v in report['cases'].values()) for state in ['PASS','FAIL','NOT_EXECUTED']},'gates':report['gates']},indent=2))
if __name__=='__main__':main()
