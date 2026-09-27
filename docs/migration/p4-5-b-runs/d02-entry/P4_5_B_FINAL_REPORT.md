# P4.5-B — Checkpoint de cierre por revisión humana D02

**Resultado: BLOCKED. Implementación parcial; P4.5-B no está completada ni aprobada.**

## Motivo de detención

C28 exige `Cache-Control: no-store` y `Vary: Cookie` también en páginas. Next **15.5.25** reemplaza el Vary configurado por middleware al renderizar App Router. Se observó HTTP 200, `no-store` y Vary exclusivo de Next/Accept-Encoding. La inspección raw `get_all(Vary)` descartó un error de aplanamiento del validador. Las APIs sí conservan `Vary: Cookie`.

El template instalado `next/dist/build/templates/app-page.js:293` ejecuta `res.setHeader('Vary', varyHeader)`. D02 contiene hashes, líneas y observaciones reproducidas. No se parcheó Next, core, arranque, auth ni el criterio aprobado. No se afirma una fuga de caché demostrada; se informa el incumplimiento preciso del diseño. La regla humana 9 requiere detenerse antes de cambiar esos controles.

### Decisión humana pendiente

**Opción A recomendada:** revisar una frontera de respuesta específica del módulo que agregue `Cookie` después del render de Next, preservando los valores Vary del framework. Debe mantener intactos core/auth y validar HTML/RSC, navegación, errores, redirect/login, bootstrap, lifecycle y cleanup. Es una propuesta de revisión, no una solución implementada o demostrada.

**Opción B:** revisar explícitamente C28 para aceptar `no-store` verificado en páginas sin exigir `Vary Cookie`, manteniéndolo en APIs. Cambia el requisito aprobado y no se adoptó automáticamente. No se deben reescribir los receipts aprobados para hacerlo pasar.

## Trabajo y evidencia

Snapshot de entrada propio anterior a cambios: `P4_5_B_ENTRY.json`, 412 hashes. Se creó exclusivamente overlay `modules/internal-requests/0.1.0/files`, runners de validación y documentación P4.5-B. Los documentos P4.5-A ya existían y permanecieron intactos.

Implementados schema compuesto, migración SQL, grants, DTO estricto, servicios/repository, visibilidad server/DB, CAS atómico, handlers contractuales y UI mínima. **La UI y los runners de navegador/extra no se ejecutaron**; su existencia no es evidencia.

La FK PostgreSQL real `InternalRequest.ownerId → app.User(id)` es RESTRICT/RESTRICT, validada/no diferible. User y auth permanecen intactos, sin relación inversa. La migración se aplicó con migrate deploy a DB vacía y DB auth con credenciales/sesiones reales; reaplicación estable. Diff únicamente anuncia la FK SQL no representada por Prisma: nunca aplicado.

Runtime: SELECT tabla; INSERT nueve columnas; UPDATE solo title/description/status/updatedAt/archivedAt/version. Negativas reales42501 para DDL/DELETE/TRUNCATE/owner/id/createdAt/historial. Bootstrap sin acceso módulo. No ALL, RLS ni ampliación auth.

Se ejecutaron carreras HTTP con barrera y conexiones distintas respaldadas por PostgreSQL: un commit por versión; también carreras de transiciones/archivo/no-owner. Paginación comparada con SQL sobre más de200 filas. Los checks detallados y los índices de pasos están en el receipt granular.

Fallos conservados: comparación C32 inicialmente demasiado estricta sobre schema qualifier, nombre erróneo de script npm, symlinks perdidos en copia temporal, lectura inicial case-sensitive de headers, y fallo real C28. Los arreglos de preparación/validador se reejecutaron sin ocultar receipts anteriores. El runner ahora conserva symlinks. Los PASS granulares recuperables de un run fallido se enlazan por índice y hash; no se hereda su estado agregado.

## Versiones e imágenes

- node: `22.23.2`
- next: `15.5.25`
- react: `19.2.8`
- typescript: `5.9.3`
- prisma: `7.5.0`
- better-auth: `1.7.5`
- pg: `8.16.3`
- postgresql: `16.15`
- openssl: `3.0.20`

Node/OpenSSL: `nexonova-p44b-node-openssl@sha256:0d0e3b31790d5b477357d4596d0c4b97f7fe2c7a43d7501821b7de1d90f52c16`

PostgreSQL: `postgres@sha256:efedf3595f1d6f415c08568ba171029bf54052e754cc9f030e3f2412b21f3d67`

## Matriz C01–C40

PASS indica caso completo de este checkpoint; NOT_EXECUTED puede contener subchecks válidos pero queda incompleto. FAIL conserva el requisito incumplido.

| Caso | Estado | Ejecutado / pendiente |
|---|---|---|
| C01 | PASS | Fresh deploy/tables/nine columns/FK/CHECK/indexes from schema run; types/defaults/enum/validated nondeferrable FK independently inspected in integration. |
| C02 | PASS | Fresh reapply and auth-only upgrade with real users, credentials and sessions; data byte-identical and migration history stable. |
| C03 | PASS | Real runtime INSERT/SELECT/UPDATE and 42501 DDL/DELETE/TRUNCATE/immutable columns/history negatives; grants captured in integration. |
| C04 | PASS | Real bootstrap module denials, orphan FK, User delete/update RESTRICT, archived owner RESTRICT and no-orphan assertion. |
| C05 | PASS | Three actors create, persisted SQL row, exact nine-field DTO, ownership and defaults. |
| C06 | PASS | Invalid FK insert and complete business/User role snapshot unchanged. |
| C07 | PASS | Create/PATCH unknown fields including owner/user/role/system fields and nested payloads rejected; A/admin; full snapshot unchanged. |
| C08 | PASS | A/B own lists; extended A/admin pagination evidence in C25. No archived rows returned. |
| C09 | NOT_EXECUTED | HTTP admin list/detail passed; required browser assertions NOT_EXECUTED. |
| C10 | PASS | Owner edit/close/edit-closed with successive versions and immutable identity fields. |
| C11 | NOT_EXECUTED | Member valid reopen and invalid close/reopen passed; admin invalid-transition variant remains NOT_EXECUTED. |
| C12 | PASS | Archive from open by member and closed by admin; DB retained, status unchanged, timestamp equality and version increment. |
| C13 | NOT_EXECUTED | Member invalid/stale/overflow commands passed; full admin variant set remains NOT_EXECUTED. |
| C14 | NOT_EXECUTED | All actors API list/detail/mutations on archived passed; required browser assertions NOT_EXECUTED. |
| C15 | NOT_EXECUTED | Owner direct API detail/edit and page HTTP200 observed; granular HTML/DTO exposure scan remains NOT_EXECUTED. |
| C16 | PASS | Admin cross-owner detail (C09), edit/close/reopen/archive, owner invariant after each operation. |
| C17 | NOT_EXECUTED | Foreign/absent HTTP404 body equal; expanded header comparison/cursor impersonation set remains partial. |
| C18 | PASS | Foreign edit with current/stale version and spoofed role/owner headers404; DB snapshot unchanged. |
| C19 | NOT_EXECUTED | Foreign open and absent actions/current-stale versions, archived actions passed; active-closed foreign variant remains NOT_EXECUTED. |
| C20 | NOT_EXECUTED | NOT_EXECUTED; stopped before session-tail block. Login setup is not this case. |
| C21 | NOT_EXECUTED | Real PostgreSQL invalid-role rejection and pure guard test passed; explicit service-entry deny tests remain NOT_EXECUTED. Earlier provisional case PASS is not inherited. |
| C22 | NOT_EXECUTED | Member malformed/encoded/foreign/absent/archived IDs yielded uniform404 per action; full admin variants/header comparison remain NOT_EXECUTED. |
| C23 | PASS | Six real HTTP races with two worker threads/connections synchronized by barrier, A/A and A/admin, exactly one200+one409, version+1, no mixed payload. |
| C24 | PASS | Real edit/close, close/archive, reopen/archive and owner/nonowner races; one commit/version increment, nonowner404, archived invisible. |
| C25 | PASS | 214 tied-time fixtures plus lifecycle rows; default/1/100 limits for A/admin; exact SQL ordered IDs, no duplicate/omission. |
| C26 | PASS | Malformed/oversized/duplicate/unknown query400; forged well-formed cursor retains owner scope; archive between pages hidden. |
| C27 | NOT_EXECUTED | HTTP Unicode/length/NUL/surrogate/contenttype/body cap passed; DOM/XSS/browser checks NOT_EXECUTED. |
| C28 | FAIL | FAIL: APIs origins/methods/no-store/Vary Cookie pass. Page200/no-store, but Next replaces Vary and removes Cookie. Confirmed raw repeated headers; D02. |
| C29 | NOT_EXECUTED | NOT_EXECUTED; app/DB persistence restart stage not reached. |
| C30 | NOT_EXECUTED | NOT_EXECUTED; DB down/revoked-grants stage not reached. |
| C31 | NOT_EXECUTED | NOT_EXECUTED; second-product runtime fixture not reached. |
| C32 | PASS | Two deterministic compositions, generate/validate, unchanged auth files; real diff only expected manually managed FK omission; DROP never applied. |
| C33 | NOT_EXECUTED | npm fixed install, compile, 8 unit tests, typecheck/build and actual app start passed; client-bundle secret/server-import scan NOT_EXECUTED. |
| C34 | NOT_EXECUTED | NOT_EXECUTED; browser runner written but never invoked. No browser PASS claimed. |
| C35 | NOT_EXECUTED | NOT_EXECUTED; real login setup is not the auth regression matrix. |
| C36 | NOT_EXECUTED | Per-run serialized known-secret scans passed; broader logs/SSR/browser/bundle/network scans NOT_EXECUTED. |
| C37 | PASS | 412 entry hashes, products and prototype99 exact sets/hashes preserved; 88 pytest tests passed. Historical next-env exception retained. |
| C38 | PASS | Real success/failure/timeout cleanup, foreign sentinel survives then owner removes; final no owned Docker/temp resources. |
| C39 | PASS | 10 evidence-consumer tests: missing cases/evidence/hash/steps/source and FAIL/BLOCKED/NOT_EXECUTED fail closed. Synthetic tests validate consumer only. |
| C40 | NOT_EXECUTED | NOT_EXECUTED; EXPLAIN/pool/load/resource measurement block not reached. |

## Gates P4.5-B

| Gate | Estado |
|---|---|
| database-migrations | BLOCKED |
| resource-authorization | BLOCKED |
| module-crud | BLOCKED |
| authentication | BLOCKED |
| compatibility | BLOCKED |
| build-tests | BLOCKED |
| cleanup | PASS |
| generation | NOT_IMPLEMENTED |
| autonomy | NOT_IMPLEMENTED |
| readiness global | BLOCKED |

Los gates de entrada de P4.4-B siguen preservados; no equivalen al PASS de la composición ampliada. Resource-authorization/module-crud **no fueron promovidos a PASS**. No hubo P4.6/P4.7 ni generación/deployment.

## Preservación, cleanup y límites

Comparados todos los412 hashes de entrada sin diferencias. Productos nexonova-website/synthetic-website contra sus manifests originales; prototipo99 archivos con conjunto exacto; corporate-site/contracts/receipts históricos contenidos en snapshot. Excepción histórica next-env.d.ts de Next mantenida separadamente. **88 tests de preservación/contratos PASS**. El primer intento con Python de sistema carecía de pytest; se usó la venv existente, sin instalar dependencias.

Cleanup PASS: éxito/fallo/timeout con centinela; cero recursos Docker con label propio, ningún directorio temporal propio pendiente, workspace preparado eliminado. Contenedores ajenos se inventariaron sin modificarlos. Relays cerrados al finalizar cada runner. No navegador fue iniciado. Evidencia: cleanup-scenarios.json y cleanup-final.json.

Scans conocidos por run antes de serialización pasaron; el scan integral C36 no se ejecutó. No fortalecer las limitaciones heredadas de P4.4-B: provenance histórica, timing sin garantía formal, rate limit en memoria de una instancia, TLS/host de prueba, recovery tras interrupción y scans no exhaustivos.

## Reanudación autocontenida

1. Resolver D02 humanamente antes de cambiar arquitectura, core o requisito; registrar nueva decisión sin alterar receipts históricos.
2. Leer ENTRY, FINAL_RECEIPT, D02 y PROGRESS; verificar sourceHashes actuales y todos los hashes históricos.
3. Recrear workspace desde core+overlay con compose; instalar desde lockfile y generar ambos clientes. El workspace temporal anterior fue eliminado. Para build, adaptar el runner que hoy apunta al preparedWorkspace anterior: no asumir que ese path existe.
4. Tras la resolución, probar C28 prioritariamente. `--resume-pages` limita la reanudación; el fixture puede necesitar setup nuevo. Los runners extra/browser siguen sin validación real y no deben considerarse listos por existir.
5. Completar cada subcaso pendiente indicado, reevaluar source changes y repetir solo dependencias/casos invalidados. Guardar nuevos receipts inmutables. No repetir indiscriminadamente la matriz demostrada.
6. Completar browser/auth/isolation/restarts/EXPLAIN/scans y cierre de gates; cleanup y revisión humana final.

El índice de archivos y hashes fuente está en `P4_5_B_FINAL_RECEIPT.json`. Este documento cierra el intento por el bloqueo, **no la fase**.
