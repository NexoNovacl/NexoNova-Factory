# P4.5-B — Informe final

**Recomendación: PASS_WITH_LIMITATIONS. C01–C40: PASS. Pendiente revisión humana.**

## Estado recuperado y resolución D02

Se partió del checkpoint bloqueado, sin reiniciar schema/FK/grants. Sus hashes y artefactos se verificaron antes de cambiar implementación. El checkpoint previo está preservado byte a byte en `p4-5-b-runs/d02-entry/`; `D02-page-vary.json` permanece intacto. La autorización humana fue `D02 = APPROVED_FOR_CONTROLLED_RESOLUTION`, opción A exclusivamente.

La solución agrega `scripts/start-requests.mjs` y `requests-response-boundary.mjs` dentro del overlay. Usa la API pública de Next y una frontera propia por respuesta, limitada a `/requests` y `/api/requests`. En emisión final conserva los tokens Vary de Next y agrega Cookie sin duplicados; mantiene no-store. No parchea dependencias/prototipos globales, no cambia core/auth ni la política de C28, ni altera respuestas de rutas ajenas.

Comparación real con launcher original: member/admin, HTML/RSC, éxito/error, exacta unión de tokens y rutas login/auth ajenas. Navegación real y redirect anónimo confirmaron headers finales. El producto compuesto con este módulo debe usar el launcher nuevo; el launcher auth original permanece intacto y no incorpora D02.

D02 obligó a repetir la integración HTTP/navegador afectada por el launcher. Solo se recuperaron pruebas independientes del schema/SQL/grants con inputs idénticos y nueva corroboración. Ningún PASS agregado previo sustituyó checks individuales.

## Implementación y pruebas

Overlay aislado con InternalRequest, migración SQL, grants, DTO estricto, servicios/repositorio, autorización por owner/admin, CAS, handlers contractuales y UI mínima. No se generó producto Factory ni hubo deployment.

Persistencia: nueve campos, open/closed, owner de sesión, archivado terminal invisible a todos. FK real hacia app.User(id), RESTRICT/RESTRICT, validada/no diferible, User intacto sin inversa Prisma. Composición auth+business reproducible; migración mediante migrate deploy, DB vacía/upgrade con credenciales y sesiones reales, reaplicación estable. TechnicalSmoke permanece separado y no aparece en DB auth/business.

Grants runtime: SELECT; INSERT nueve columnas; UPDATE únicamente title/description/status/updatedAt/archivedAt/version. DDL/DELETE/TRUNCATE/id/ownerId/createdAt/historial rechazados. Bootstrap técnico separado sin privilegios del módulo; Better Auth, roles y sesiones sin cambios.

CAS atómico probado con dos conexiones HTTP sincronizadas, seis carreras edit/edit y carreras de estado/archivo/non-owner. Rechazos uniformes404, versiones inválidas/obsoletas/overflow, spoofing y entradas hostiles probados. Paginación comparada contra SQL sobre más de200 filas con timestamps iguales.

Playwright real: flujo teclado, desktop/mobile, dos pestañas409 conservando borrador, admin y rechazo horizontal, XSS como texto, archivo invisible. SSR/RSC/navegación y headers comparados. Auth integrada: login genérico, signup cerrado, logout/replay, límite8h controlado y sin refresh, Secure/HttpOnly/SameSite en HTTPS real local.

App y PostgreSQL reiniciados; datos/sesiones/archivo conservaron la política. DB caída y grants retirados dieron503 sin escrituras parciales. Dos productos aislados por DB/red/volumen/secreto/prefijo rechazaron cookies/IDs cruzados sin contaminación.

SQL real emitido por Prisma mostró filtro owner/activo y LIMIT; UPDATE incluyó owner/activo/versión. EXPLAIN y cargas medidas; conexiones runtime8/8/8 (pool empresarial máximo5, pool auth separado). Son mediciones de piloto, no SLA.

Scans conocidos cubrieron logs app/DB, SSR, bundle y serialización. La instrumentación SQL final deshabilitó parámetros antes de loguear; su scan DB pasó. Un probe anterior registró solo statements saneados y no completa el scan DB: para C36 se usa el receipt posterior. Navegador0 llamadas externas, redes internas y probe de egress negativo.

## Evidencia principal

| Artefacto | Alcance |
|---|---|
| p45b-b38e4bd8e33b4b57.json | npm ci fijo, generate, compile/typecheck,10 unitarios y build |
| p45b-3d044de39b4d4ba1.json | Integración real completa,2170 checks, PostgreSQL/HTTP/Playwright/HTTPS |
| p45b-24984b962cb0466e.json | SQL real, grants/defaults exactos, headers navegador, scan DB y egress |
| final-preservation-cleanup-d02.json | Preservación, versiones/digests, recomposición y cleanup final |
| evidence-consumer-d02.json | Consumer fail-closed,10 pruebas |
| preservation-tests-d02.json | 88 tests P3/P4.2/productos |
| cleanup-scenarios-d02.json | Éxito/fallo/timeout y centinela |

Los receipts originales fallidos siguen disponibles. Las referencias por índice y SHA256 de cada caso están en `P4_5_B_FINAL_RECEIPT.json`; los validadores se archivan por hash. El código escrito pero no ejecutado en el checkpoint anterior fue ejecutado durante esta continuación antes de promover casos.

## Versiones y digests

- node: `v22.23.2`
- next: `15.5.25`
- react: `19.2.8`
- prisma: `7.5.0`
- pg: `8.16.3`
- typescript: `5.9.3`
- betterAuth: `1.7.5`
- postgresql: `16.15`
- openssl: `OpenSSL 3.0.20 7 Apr 2026 (Library: OpenSSL 3.0.20 7 Apr 2026)`

Node/OpenSSL: `nexonova-p44b-node-openssl@sha256:0d0e3b31790d5b477357d4596d0c4b97f7fe2c7a43d7501821b7de1d90f52c16`

PostgreSQL: `postgres@sha256:efedf3595f1d6f415c08568ba171029bf54052e754cc9f030e3f2412b21f3d67`

## Matriz final

| Caso | Estado | Evidencia y alcance |
|---|---|---|
| C01 | PASS | Fresh deploy/inventory/FK/CHECK/indexes recovered from schema run; new catalog verifies all nine types/nullability/defaults and literal enum. |
| C02 | PASS | Reexecuted: auth-only upgrade with real credentials/sessions and unchanged auth data; combined migration reapply unchanged. Fresh path evidence also retained. |
| C03 | PASS | Real 42501 negatives and allowed SQL recovered; new runtime effective INSERT9/SELECT9/UPDATE6 column grants exactly verified; bootstrap has no module grant. |
| C04 | PASS | Real FK23503 orphan/User delete/User ID update, archived reference and bootstrap42501 recovered unchanged; module schema/SQL/grants hashes match. |
| C05 | PASS | New HTTP creates A/B/admin, exact ownership/defaults/nine-field DTO and DB persistence; supplemental server-time window and UUIDv4 assertions. |
| C06 | PASS | Real FK rejection followed by unchanged full business/User role snapshot. |
| C07 | PASS | A/admin strict DTO negatives for owner/user/role/system/nested fields, constructor and __proto__; DB unchanged. |
| C08 | PASS | A/B lists and complete owner-filtered pagination; archived excluded. |
| C09 | PASS | Admin global active list/detail via HTTP and actual browser access to foreign resource; archived excluded. |
| C10 | PASS | Own edit, close, edit while closed; versions and immutable identity values checked against DB/DTO. |
| C11 | PASS | Member and admin valid reopen plus invalid close/reopen409 with full no-change snapshots. |
| C12 | PASS | Member/admin archive from open/closed204; retained rows, original status, version+1 and archivedAt=updatedAt. |
| C13 | PASS | Both member/admin: every command with missing/invalid/stale/maxInt versions;400/409 and unchanged DB. |
| C14 | PASS | All actors API and actual browser archived invisibility, all mutation404, repeated archive404; retained DB rows. |
| C15 | PASS | Own direct detail/edit, exact nine-field DTO and actual SSR own title without auth fields; full known-secret SSR scan in C36. |
| C16 | PASS | Admin foreign edit/close/reopen/archive with same version rules and unchanged owner; browser admin edit/archive included. |
| C17 | PASS | Foreign/absent/archived uniform404 signatures; forged cursor and identity headers retain owner filter. |
| C18 | PASS | Horizontal edit current/stale versions plus forged role/owner headers404; full DB unchanged. |
| C19 | PASS | Horizontal close/reopen/archive current/stale versions in open/closed/archived/absent cases, no changes. |
| C20 | PASS | No cookie/forged/expired/revoked: all API operations401, pages login; real browser contexts and no DB effects. |
| C21 | PASS | Real PG enum rejects invalid role; pure guard and actual service-entry deny-default unit probe (explicitly not a mock auth integration). |
| C22 | PASS | Encoded/malformed/inexistent/foreign/archived ID cases across member/admin and commands; exact status/body/static headers, no cookie/metadata; timings descriptive only. |
| C23 | PASS | Six synchronized real HTTP two-connection races A/A and A/admin; exactly one200+one409, version+1 and unmixed winning payload. |
| C24 | PASS | Synchronized edit/close, close/archive, reopen/archive and owner/nonowner; one commit/version, no archive resurrection or foreign effect. |
| C25 | PASS | 214 tied-timestamp fixtures plus lifecycle rows; A/admin default20/1/100 traversal equals SQL ordered IDs without duplicates/omissions. |
| C26 | PASS | Invalid/oversized/duplicated query400; forged canonical cursor never bypasses owner; archive between pages respects visibility. |
| C27 | PASS | Unicode/scalar/length/whitespace/NUL/surrogate/body16KiB/media validation via unit+HTTP/DB; hostile text rendered without XSS in actual browser. |
| C28 | PASS | Complete CSRF/method/header checks; original-vs-new launcher HTML/RSC comparison preserves all Next Vary tokens plus one Cookie. Browser navigation/final headers and anonymous redirect verified; no-store throughout. |
| C29 | PASS | Separate real app and DB restarts; complete DB snapshot stable, live session valid, permitted detail and archived404 remain. |
| C30 | PASS | DB stopped and SELECT/INSERT/UPDATE grants withdrawn separately:503 sane/fail-closed; restored DB equals snapshot, no partial writes. |
| C31 | PASS | Two DB/network/volume/secret/cookie-prefix products with valid controls; cross-cookie401, cross-ID404, foreign cursor empty and zero row contamination. |
| C32 | PASS | Deterministic composition/generate/validate/diff recovered; final recomposition hash identical and auth files identical. Only known SQL FK diff, never applied. |
| C33 | PASS | Fixed npm ci; generated both clients; compile/typecheck/10 unit tests/build; real new launcher; no server DB imports in client JS; exact versions/digests verified. |
| C34 | PASS | Playwright desktop keyboard create/list/detail/edit/close/reopen; two-tab409 preserves draft; horizontal denial, mobile admin edit/archive, archived invisible and no JS errors. |
| C35 | PASS | Integrated generic login/signup-closed/probes/logout-replay; controlled before/at8h and no-refresh; session cookies local HTTP and real HTTPS browser secure attributes; original auth/core/bootstrapping intact. |
| C36 | PASS | Known synthetic values scanned in app logs/SSR/client JS and serialized run; supplemental DB logs scanned with parameter logging disabled; browser no external calls, internal networks and negative egress probe. Final artifact heuristic scan separate. |
| C37 | PASS | Final412 entry hashes; P3/P4.2/P4.3/P4.4 protected artifacts and prior receipts intact; products/prototype99 exact baselines;88 regression tests. |
| C38 | PASS | Reexecuted success/failure/timeout/sentinel, both new runs cleaned; final own Docker/path/process inventory empty and prepared workspace removed. |
| C39 | PASS | Consumer fail-closed checks case statuses, proof hashes/step indices, proof-set/source-set fingerprints, current sources; missing/altered evidence and non-PASS statuses tested. |
| C40 | PASS | Actual parameterized Prisma SQL shows owner+active scope and LIMIT/CAS predicates; EXPLAIN, real pagination/load, connection counts8/8/8 and Docker resource measurements (not SLA). |

## Gates

| Gate | Estado |
|---|---|
| database-migrations | PASS |
| resource-authorization | PASS |
| module-crud | PASS |
| authentication | PASS |
| compatibility | PASS |
| build-tests | PASS |
| cleanup | PASS |
| auth-role-probes | PASS |
| generation | NOT_IMPLEMENTED |
| autonomy | NOT_IMPLEMENTED |
| readiness global | BLOCKED |

Resource-authorization PASS está limitado a InternalRequest; no declara una autorización global genérica. No quedó caso obligatorio FAIL/BLOCKED/NOT_EXECUTED. El consumer recalculó los gates desde referencias válidas, sin heredar gates del checkpoint.

## Preservación y cleanup

412 hashes de entrada idénticos; P3/P4.2/P4.3/P4.4-A/P4.4-B y contratos sin reescritura. Corporate-site preservado en snapshot; nexonova-website/synthetic-website contra manifests originales, con excepción histórica next-env.d.ts reportada separadamente; prototipo99 archivos con conjunto/hash exactos.88 pruebas finales aprobadas.

Cleanup final: cero contenedores/redes/volúmenes con label propio, workspace preparado y directorios temporales propios eliminados; sin procesos Node de validadores ni browsers Playwright pendientes. Centinela de otro owner intacto y luego retirado por su creador. Contenedores ajenos no modificados. No se borraron caches compartidas del operador.

## Archivos creados/modificados

Durante P4.5-B se crearon los archivos bajo `modules/internal-requests/0.1.0/files/`, runners propios y documentación/receipts. D02 añadió launcher/frontera y pruebas, adaptó runners y actualizó el cierre/checkpoint. El core y los contratos aprobados permanecieron byte-idénticos. Inventario completo en `implementationAndValidatorFiles` y sourceHashes del receipt.

## Limitaciones restantes

- Inherited historical P4.4-B recovered provenance is incomplete; this phase does not strengthen it retrospectively. New runs have explicit source hashes and validator archives.
- No formal timing indistinguishability; uniform errors do not prove absence of timing enumeration. P4.4-B measured timing differences remain an accepted limitation.
- In-memory login rate limiting only for controlled single-instance pilot; restart resets counters. No production scalability/availability/SLA claim.
- Linux/amd64 trusted Docker host; local self-signed HTTPS tests do not demonstrate production TLS/proxy/deployment.
- Known-value and heuristic scans are not exhaustive security audits. Browser observes zero external calls; internal-network negative probe is not packet capture of every attempt.
- A hard host/daemon interruption may require manual cleanup recovery; ordinary success/failure/timeout and owned-resource isolation were tested.
- D02 requires the new start-requests.mjs launcher. Hosting/standalone/proxy or Next version changes require header/SSR/RSC/auth regression. No dependency patch or core/auth modification.
- SQL-managed FK is intentionally absent from Prisma relation metadata. Never apply migrate diff blindly; its expected FK DROP was not applied.
- Pagination is deterministic on a stable dataset, not a snapshot across concurrent writes. No auto retry after uncertain write outcomes; archiving is terminal.
- Resource authorization PASS covers this InternalRequest module only, not a generic authorization engine or multitenancy. Generation/autonomy remain NOT_IMPLEMENTED and global readiness BLOCKED.
- Production vulnerability/security review, password recovery, account administration and deployment remain outside this phase.

## Operación y revisión humana

El overlay es una composición validada de laboratorio, no un deployment. Para reproducir: ejecutar el runner de build (recrea workspace si no existe), luego integración; el arranque compuesto usa `node scripts/start-requests.mjs`. Migraciones se aplican separadamente con `prisma migrate deploy --config prisma.requests.config.ts`, nunca al arrancar ni con db push. No aplicar el DROP FK sugerido por diff. La DB auth-only puede ampliarse con el historial combinado revisado.

Los runners de observabilidad, cleanup y cierre tienen receipts independientes. Un nuevo ciclo debe generar nuevos receipts y no sobrescribir los ya aprobados. Revalidar headers/SSR/RSC/auth si cambia Next, launcher o infraestructura HTTP.

**P4.5-B se detiene aquí para revisión humana. No se inició P4.6/P4.7, generación ni autonomía.**
