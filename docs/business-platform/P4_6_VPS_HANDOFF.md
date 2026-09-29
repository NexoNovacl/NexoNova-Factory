# P4.6 — Handoff al VPS de desarrollo

Fecha: 2026-09-29. Alcance de esta entrega: documentación y verificación de bytes únicamente.
**El handoff no constituye autorización ejecutiva.** No autoriza EXECUTION_B2, WorkOrders,
materialización de Atlas/Brisa, promoción ni P4.7. El prompt final permite solicitar exclusivamente
la repetición de B1 en el VPS. El cambio de host no cambia roadmap, contratos ni decisiones humanas.

## 1. Estado y precedencia histórica

| Etapa | Estado relevante y dependencia |
| --- | --- |
| P1 | Contención del flujo académico implementada/validada; resultados y gates derivados de evidencia, no flags. No certifica generación empresarial. Fuente: `docs/migration/P1.md`. |
| P2 | Resultado técnico PASS_WITH_LIMITATIONS; fronteras de ejecución/configuración, exclusión y recuperación. Su informe registra 105 pruebas locales, no una garantía universal de host. Fuente: `docs/migration/P2_FINAL_VALIDATION.md`. No inferir de ello autoridad actual. |
| P3 | PASS_WITH_LIMITATIONS / CLOSED, aprobado humanamente como entrada de P4. Corporate-site y dos productos históricos, baseline y prototipo preservados; no production-ready ni autorización de deployment. |
| P4.1 | APPROVED: diseño business-platform y desglose P4.6 generación/generalidad; P4.7 autonomía/regresión. |
| P4.2 | APPROVED: contratos versionados de plataforma y módulo; artefactos inmutables, no órdenes ejecutivas para P4.6. |
| P4.3 | PASS_WITH_LIMITATIONS / APPROVED: infraestructura PostgreSQL/Prisma y separación técnica, sin reutilizar TechnicalSmoke como negocio. |
| P4.4-A | APPROVED: diseño auth, Better Auth 1.7.5, OpenSSL, roles/bootstrap/sesiones. |
| P4.4-B | PASS_WITH_LIMITATIONS / APPROVED: autenticación real y probes de rol, no autorización general de recursos. |
| P4.5-A | APPROVED / READY_WITH_LIMITATIONS: diseño InternalRequest, D01 resuelto open/closed. |
| P4.5-B | HUMAN_APPROVED / PASS_WITH_LIMITATIONS: C01–C40 aceptados, D02 aceptado, gates técnicos PASS; resource-authorization limitado a InternalRequest. |
| P4.6 diseño | DESIGN_APPROVED: G01 ALTERNATIVE_A y detalle inventory/adaptation aprobados. |
| IMPLEMENTATION_A | IMPLEMENTATION_A_COMPLETED, checkpoint aceptado humanamente; componentes puros y 50 tests. |
| IMPLEMENTATION_B | IMPLEMENTATION_B_COMPLETED, cierre aprobado humanamente; cuatro componentes B, 48 tests B + 50 A; sin ejecución de productos. |
| EXECUTION_B1 anterior | BLOCKED por precondiciones del host anterior; no WorkOrders/recetas ejecutables emitidos. |
| EXECUTION_B2 / promoción / P4.7 | NO AUTORIZADOS. Ningún producto P4.6 materializado/aceptado. |

Las aprobaciones humanas aquí registradas proceden de las instrucciones explícitas del usuario
que originaron este handoff; no son firmas criptográficas ni aprobación autoemitida por el agente.
Los informes P3/P4.4/P4.5 y la propuesta/runbook A conservan texto de su fecha de entrega
(«pendiente», «B no implementado»). Las decisiones posteriores y receipts separados establecen
la secuencia vigente; no editar documentos antiguos para modernizar su estado.

P4.6 demuestra generación determinista y generalidad con dos configuraciones ficticias Atlas/Brisa
sobre la composición aprobada. No equivale a la fase principal P6. P4.7 demuestra autonomía y
regresión, no es P7/deployment. Generation sigue **NOT_IMPLEMENTED como gate**, aunque exista
código generador; autonomy NOT_IMPLEMENTED, readiness global BLOCKED. Readiness no es PASS
ni un componente ejecutado por haber terminado implementación A/B.

## 2. Decisiones humanas que deben conservarse

- P4.2 permanece byte-identical: no reinterpretar `coreRoutes` como inventario exhaustivo actual,
  no cambiar estados históricos ni versionar contratos por el traslado.
- InternalRequest tiene exactamente id/title/description/status/ownerId/createdAt/updatedAt/
  archivedAt/version. title 1–120, description máximo2000. Únicos literales `open`/`closed`,
  inicial `open`; cerrar/reabrir son transiciones entre ambos.
- Archivo terminal por `archivedAt != null`, invisible a owner/admin; sin tercer estado archived,
  unarchive, DELETE físico, reasignación ni multitenancy.
- ownerId procede exclusivamente de sesión; DTO estricto rechaza spoofing/mass assignment.
  member solo recursos propios; admin recursos permitidos de cualquier owner. Rol desconocido
  deny-by-default. Predicado de visibilidad servidor/DB; ajeno/inexistente/archivado →
  `404 RESOURCE_NOT_FOUND` uniforme, sin garantía temporal formal.
- PATCH contractual con edit/close/reopen/archive, expectedVersion y CAS atómico, 409 al conflicto;
  paginación keyset (createdAt,id). FK SQL real a app.User(id), RESTRICT/RESTRICT, sin cambiar User
  ni inversa Prisma; grants mínimos por operación/columna, sin ALL/DDL runtime ni ampliar bootstrap.
- Better Auth **1.7.5**, Prisma **7.5.0**, Next **15.5.25**, OpenSSL mediante imagen reproducible
  aprobada. ADMIN=admin, USER=member. User/Session/Account/Verification mínimos, role política propia;
  TechnicalSmoke separado. Bootstrap offline transaccional con credencial PostgreSQL técnica efímera
  independiente, sin signup público/temporal, contraseña por defecto ni endpoint bootstrap.
- Sesión absoluta máxima8h, sin refresh ni cookie cache autoritativa; telemetría auth deshabilitada,
  Secure productivo obligatorio. HTTP local solo tests, rate limit en memoria solo piloto de una instancia.
- D02: frontera específica de InternalRequest después del render Next, conserva tokens Vary y añade
  Cookie sin duplicados; Cache-Control no-store. No parchear Next/node_modules ni core/auth.
  **Launcher obligatorio `node scripts/start-requests.mjs`**. El launcher auth original no es equivalente.
  Fuente en Factory: `modules/internal-requests/0.1.0/files/scripts/start-requests.mjs`.
- G01=HUMAN_APPROVED/ALTERNATIVE_A: `nexonova.business-execution-inventory.v1` y
  `nexonova.business-route-adaptation.v1`, política `p42-to-approved-runtime.v1`, perfil cerrado
  `business-auth-internal-requests-0.1.0-d02`, once rutas reales y allowlist auth documentada.
  `/login` real; `/sign-in` y descendientes reservados segment-subtree NO materializable: sin página,
  redirect, rewrite o alias. Regla nueva del adaptador, no reinterpretación retroactiva P4.2.
  `/api/auth/[...all]` conserva `/api/auth/sign-in/email` permitido.
- IMPLEMENTATION_A, IMPLEMENTATION_B y EXECUTION_B son autorizaciones distintas. Un contexto puro
  de hashes no ejecuta efectos. Ningún receipt, diseño, orden P4.2 ni flag local produce
  `EXECUTION_B_APPROVED`. Mínimo ejecutivo: workOrderHash, generationManifestHash, adaptationHash;
  además plan/metadata/code/validator/input hashes, acciones, destinos, vigencia y revocación.

## 3. Lectura mínima obligatoria, en orden

Rutas relativas a raíz Factory. Leer secciones señaladas; no recorrer toda la historia P1–P4.
Los JSON voluminosos pueden procesarse para extraer campos indicados sin imprimir cada hash.

| Orden | Fuente | Propósito / condición |
| --- | --- | --- |
| 1 | Este handoff, `AGENTS.md`, `MIGRATION_PLAN.md` §7 | Límites actuales, reglas locales y propósito; roadmap histórico protegido. |
| 2 | `docs/business-platform/P4_6_PROPOSAL.md` | Objetivo, exclusiones y matriz G; propuesta histórica aprobada posteriormente. |
| 3 | `docs/migration/P4_6_DESIGN_APPROVAL.json` y `docs/business-platform/P4_6_EXECUTION_INVENTORY_DESIGN.md` | Detalle G01, once rutas, allowlist, serializer y adaptación; decisión y diseño inmutables. Consultar parentDecision G01 solo si hay duda concreta. |
| 4 | `docs/business-platform/P4_6_IMPLEMENTATION_PLAN.md` | Separación A/B, autoridad, staging y gates; plan aprobado inmutable. |
| 5 | `docs/migration/P4_6_IMPLEMENTATION_A_RECEIPT.json`, `docs/business-platform/P4_6_GENERATION_RUNBOOK.md` | Archivos A, hashes, tests, casos, APIs puras y límites; checkpoint histórico (su descripción de B pendiente ya fue superada). |
| 6 | `docs/migration/P4_6_IMPLEMENTATION_B_RECEIPT.json`, `docs/business-platform/P4_6_IMPLEMENTATION_B_NOTES.md` | Implementación efectiva B, pruebas, fronteras API y precondiciones; inmutables. CLI descriptiva, no usar comandos ejecutivos ilustrativos del plan como si existieran. |
| 7 | `docs/migration/P4_6_EXECUTION_B1_PREFLIGHT.json`, `docs/business-platform/P4_6_EXECUTION_B2_PLAN.md` | Snapshot del host anterior, blockers, propuestas NO ejecutables y matriz; históricos, no sobrescribir. |
| 8 | `docs/migration/P4_6_ENTRY.json`, `docs/migration/P4_6_IMPLEMENTATION_B_ENTRY.json` | Procesar mapas hashes para integridad; snapshots inmutables, no renovar baselines. |
| 9 | `docs/business-platform/P4_2_CONTRACTS.md`, `docs/migration/P4_5_B_FINAL_REPORT.md`, `docs/business-platform/P4_5_B_D02_RESOLUTION.md` | Contratos/roles/rutas y composición/launcher aprobados; históricos. |
| 10 | `docs/migration/P4_4_B_FINAL_REPORT.md`; campos gates/limitations/versiones/referencias de `P4_4_B_FINAL_RECEIPT.json` y `P4_5_B_FINAL_RECEIPT.json` | Auth, limitaciones y evidencia de entrada; no repetir runners. |
| 11 | `docs/migration/P3_BASELINE.json`, manifests `P3_5_GENERATION_MANIFEST.json`/`P3_6_GENERATION_MANIFEST.json`, `config/pilots/nexonova/source-manifest.json` | Solo definición de preservación externa; procesar listas/hashes, no reejecutar historia. |

Consulta dirigida, solo si surge necesidad: P4.1 §9 para desglose, P4.3 para contrato infra,
P4.4-A para una decisión auth y P4.5-A para un criterio C afectado. Los schemas/configs y código
A/B se inspeccionan después de verificar bytes, al comprobar consumibilidad de propuestas VPS.

## 4. Bloqueo observado en el host anterior

Fuente exacta: `P4_6_EXECUTION_B1_PREFLIGHT.json`, snapshot UTC2026-09-28; no medirlo de nuevo
para este handoff. **Nada de esta tabla acredita ni bloquea por sí mismo al VPS.**

| Precondición | Observación anterior | Qué falta en VPS |
| --- | --- | --- |
| RAM | MemTotal3495444KiB ≈3,33GiB; MemAvailable912868KiB; harness exige mínimo4096MiB por ejecución | RAM/cgroups/swap no equivalente a RAM, concurrencia y margen OS/browser nuevos. No reducir mínimo. |
| npm offline | 195 entradas lock; 0 objetos de integridad disponibles en cache examinada `/home/germanleiks/.npm/_cacache/content-v2` | Verificar cache suficiente por lock/integridad/plataforma; no afirmar ausencia universal de otras caches. |
| Prisma | Cache predeterminada `/home/germanleiks/.cache/prisma` ausente | Engines/version/plataforma/OpenSSL y visibilidad real desde receta offline. |
| Browser | Driver Playwright1.63.0 leído en website hermano; Chromium/headless-shell1243, versión153.0.8010.12; cache predeterminada ausente | Driver/binario compatibles y hashes; no adoptarlos implícitamente ni instalar. |
| Docker | Cliente/daemon29.8.1 linux amd64; sandbox negó primero socket/netlink, consultas read-only escaladas respondieron | Daemon/permisos/arquitectura/contexto inventariados desde cero, sin arrancar recursos. |
| Imágenes | Node y PostgreSQL exactos presentes (ver abajo) | Disponibilidad local por digest y plataforma; no pull implícito. |
| Filesystem | ext4 device2053, ancestro UID1000 modo0775; libc exporta renameat2 | Símbolo no prueba RENAME_NOREPLACE efectivo. Destinos/controlRoots ausentes, mismo device futuro no probado. |
| Recursos | 4CPU; libre96771506176 bytes; dos hello-world detenidos, redes bridge/host/none, sin volúmenes | Inventario nuevo con IDs/ownership; nunca limpiar/adoptar ajenos. |
| Puertos | Propuestos4161/4461 Atlas,4162/4462 Brisa libres en ss; no reservados | Revalidar conflicto IPv4/IPv6 y reserva futura; no abrir servidores B1. |

Imágenes contractuales, no sustituir tags/versiones:

- `nexonova-p44b-node-openssl@sha256:0d0e3b31790d5b477357d4596d0c4b97f7fe2c7a43d7501821b7de1d90f52c16`
- `postgres@sha256:efedf3595f1d6f415c08568ba171029bf54052e754cc9f030e3f2412b21f3d67`

No hubo descarga, materialización ni infraestructura B1 creada. WorkOrders/recetas son null;
workOrderHash/runtimeRecipeHash también null, deliberadamente. Los hashes de plan/manifest/
adaptation/metadata/code/validator existentes son resultados en memoria, no permiso. La lista
inputHashesKnown es conservadora y **no** una lista ejecutiva final. Presupuesto anterior propuesto:
3contenedores,4096MiB,3CPU,12288MiB disco,7200s por producto, instalación/compilación secuencial;
G18 necesita ambos vivos. Red/recursos agregados y enforcement requieren nueva revisión.

## 5. Copia e integridad sin regenerar baselines

Copiar el estado completo de `nexonova-factory` que figure en inventarios, incluidos archivos
**untracked**, dotfiles públicos, schemas, fixtures, evidencia binaria/logs saneados y receipts.
Hay archivos A/B todavía untracked: `git clone`/`git archive HEAD` solos no garantizan esta entrega.
No ejecutar git reset/clean, autofix, formateo, conversión LF/CRLF ni regeneradores. No trasladar
secretos, caches/builds/venvs como si fueran código aprobado. No hace falta copiar node_modules
para comprobar bytes. No convertir exclusiones genéricas de `.gitignore` en autoridad para omitir
un path explícito del inventario. `.git` es útil para provenance/status, no reemplaza hashes.

Antes de importar código copiado, usar lector stdlib read-only sobre receipts, con rechazo de claves
JSON duplicadas/rutas inseguras. Mapas canónicos:

1. `P4_6_ENTRY.json.hashes`: 533 archivos protegidos originales.
2. `P4_6_IMPLEMENTATION_B_ENTRY.json.hashes`: 564 preexistentes al comenzar B.
3. A/B `newArtifactHashes`: artefactos añadidos; verificar también bytes de cada receipt mediante
   referencias posteriores. Su `receiptIntegrity` es hash canónico excluyendo ese campo, no hash
   del archivo completo ni firma humana.
4. `P4_6_EXECUTION_B1_PREFLIGHT.json.protectedFiles.hashes`: unión de 571 paths, corroborar contra
   los mapas anteriores, no usar este snapshot como sustituto de baselines históricos.
5. `P4_6_VPS_HANDOFF_RECEIPT.json`: ancla de transferencia de los 573 preexistentes, incluido B1
   y B2_PLAN, más hash de este documento. Conservar copia confiable de su hash fuera de la copia
   si se necesita detectar manipulación conjunta; los hashes solos no autentican al emisor.

Comparar SHA256 de bytes exactos por ruta relativa a nueva raíz, rechazar ausencias/extras inesperados
(distinguir .git/caches ignorados del inventario fuente), symlinks/hardlinks y contradicciones entre
mapas. No seguir enlaces para aceptar una copia. Verificar nombres/case, contenidos y conjuntos.
mtime/UID/GID/device nuevos no son diferencias de bytes; registrarlos aparte para seguridad de
paths/ownership. Nunca «actualizar baseline» para hacer pasar una diferencia. Cualquier mismatch
bloquea antes de host/workflow; conservar diagnóstico y pedir revisión.

Serialización `inventory-json.v1`: JSON UTF-8 sin BOM, claves ordenadas, separadores `,`/`:`,
ensure_ascii=False, allow_nan=False, LF final; no floats ni normalización Unicode. object_hash es
`sha256:` del resultado; mapas históricos raw SHA256 generalmente no llevan prefijo. Primero
verificar bytes del helper, después usarlo para comprobar integridad canónica. Mantener
PYTHONDONTWRITEBYTECODE=1; una lectura de integridad no debe instalar ni escribir caches.

## 6. Paths y portabilidad: revisar, no editar

Inspección de esta entrega: búsqueda literal `/home/germanleiks` en `factory/`, `scripts/`,
`tests/`, `config/` y `schemas/` no encontró coincidencias. Eso **no** prueba portabilidad completa:
existen dependencias relativas externas, semántica Linux y paths absolutos suministrados como datos.

| Clase | Hallazgo / tratamiento |
| --- | --- |
| Documentación/receipts | B1/B2_PLAN contienen `/home/germanleiks/NexoNova/p46-execution-b2/...`, cache/browser/host anteriores; son evidencia inmutable, no editar ni ejecutar literalmente. Otros informes P3 guardan ubicaciones históricas. |
| Configuración | Descriptor/configs P4.6 referencian fuentes relativas a Factory; revisar datos de configs heredadas y rutas hermanas. No reemplazar strings globalmente. |
| Contratos | WorkOrder exige destinos absolutos canónicos; receta controlRoot/env/cache/TLS concretos. No se emitió WO válido anterior. Nuevos paths implican nuevos bytes/hashes y aprobación; schema no se cambia. |
| Código A/B | `business_execution_contracts.ROOT = Path(__file__).resolve().parents[1]`; entradas relativas a repo. Materializador usa Linux fd/O_NOFOLLOW/flock/renameat2, UID actual y mismo filesystem; harness usa UID/GID actuales y `/work`, `/tmp`, `/npm-cache`, `/tls` dentro de contenedores. No cambiar mounts por confundirlos con paths host. |
| Tests | Fixtures `/unit/...` o temporales son sintéticas, no controlRoots reales. Suite B usa Node y procesos fork, requiere Linux; no ejecutar suites en masa que activen infraestructura histórica. |
| Scripts históricos | Browser auth/requests resuelve `../nexonova-website/package.json` o `../../nexonova-website` desde script. Preservación usa ROOT.parent/nexonova-prototype y productos hermanos. No ejecutar finalizers: escriben receipts históricos. |

Fuente launcher protegida: `modules/internal-requests/0.1.0/files/scripts/start-requests.mjs`,
SHA256 `4cde0848456d6b5eb46fb09560602177007213f66c18338cc16d599a6376d9c8`.
Si ubicación nueva requiere cambiar implementación A/B, detener y proponer revisión, no parchear.
No usar sed para reescribir paths dentro de receipts. B1 nuevo documenta mapping old→new.

## 7. Inputs que no viajan simplemente con Factory

| Input | B1 VPS | B2 y tratamiento |
| --- | --- | --- |
| Python stdlib/herramientas lectura | Necesarios para verificar localmente; no instalar implícitamente | Node para unitarios, versiones/herramientas fijadas y verificación posterior. |
| Docker daemon/config/permisos | Inventario read-only obligatorio para READY; ausente/inaccesible se registra | Ejecución requerirá permiso explícito, imágenes exactas y aislamiento. No copiar socket/config secreta. |
| Imágenes Docker, incluida Node propia | Inspeccionar digest/plataforma; pueden no existir en registry público | Transferencia/carga/pull son provisión separada, no autorizadas por handoff; no reconstruir imagen equivalente por tag. |
| Caches npm/Prisma | Verificar suficiencia e integridad offline; ausencia bloquea readiness B1 | Aprovisionamiento independiente; no npm ci/download para «comprobar» B1. Deben ser visibles en mounts aprobados. |
| Playwright/Chromium | Verificar driver/browser fijados, arquitectura y librerías sin launch | No copiar node_modules de otro OS a ciegas; instalación/descarga requiere permiso separado. |
| Credenciales/env técnicos | B1 define paths/roles/lifecycle, sin inventar secretos | Runtime/migrator/bootstrap/postgres separados por producto; secretos fuera de receipts/WO,0600, cleanup propio. |
| Certificado/clave TLS local | B1 diseña lifecycle y referencias | Proveer bajo autoridad específica, clave privada, SAN local, sin truststore global. |
| `nexonova-website`, `synthetic-website`, `nexonova-prototype` | Declarar disponibilidad; no indispensables para verificar bytes internos de Factory, sí precondición para G21 completo | Copias auténticas separadas, mismas relaciones de paths si validators las exigen. Manifests P3.5/P3.6 y source-manifest99 archivos viajan con Factory; fuentes externas no. Ausencia no se suplanta regenerando producto/prototipo. |
| Baseline corporate-site | Template/contratos/baseline internos viajan en inventario | Preservar además productos externos; excepción histórica next-env.d.ts se informa según validator existente, no nueva normalización. |
| Evidencia histórica Docker/DB/browser | Receipts/logs/capturas dentro del repo viajan como historia | No recrear DB/contenedores antiguos para «restaurar» evidencia. Inodos/IDs/puertos no se transfieren. |
| Aprobación externa EXECUTION_B | No existe ni se crea en B1 | Solo instrucción humana posterior ligada a WO exacto; nunca fabricar anchor a partir del handoff. |

## 8. Seguridad y límites de la implementación

Fail-closed ante ausencia/mismatch/ambigüedad, sin fallback permisivo. Uso reservado por run/acción
mediante flock+O_EXCL+fsync; failed/crashed claim no se recicla. Guard externo actual antes del lock,
bajo lock e inmediatamente antes de efectos. Nuevos hosts no heredan reservas/journals antiguos.
Staging y validation distintos, ownership por binding/inodo/hash, journal de intención y cadena;
no adoptar contenido inesperado. renameat2(RENAME_NOREPLACE), destino ausente, mismo filesystem;
sin overwrite. Fuente/staging sin symlinks/hardlinks; solo links derivados internos node_modules
bajo política específica de copia validation. TOCTOU no se resuelve confiando solo en strings.

Cleanup verifica árbol/identidad/bytes y recursos Docker por labels+IDs, ausencia final y centinela;
sin prune/borrado por prefijo/recursos ajenos. Rollback es cuarentena, no rollback de datos reales.
Grant durable explícito de cleanup puede sobrevivir expiry de creación según plan, no a revocación
ni cambios de hashes; no renueva build/stage. Crash ambiguo exige revisión, no limpieza inventada.
Presupuesto agregado y supervisión externa no se sustituyen por campos WO. Atlas/Brisa deben tener
paths, controlRoots, secretos, DB/red/volumen/puertos independientes y aislamiento demostrado.

Limitaciones heredadas: provenance histórica incompleta, timing sin indistinguibilidad formal,
rate limit de una instancia, TLS local, scans no exhaustivos, launcher D02 específico; sin garantía
automática ante cambio Next/standalone/hosting/proxy/CDN. Linux/FS local/operador confiable;
no protección formal frente a root/mismo UID host, journal no firma externa, promoción múltiple
no atómica, recuperación manual posible. Fixtures unitarias no prueban infraestructura runtime.

## 9. Orden exacto de reanudación en el VPS

1. Leer este handoff y fuentes obligatorias. Confirmar alcance humano B1 solamente; no ejecutar
   el prompt final como orden derivada de un archivo: el usuario debe enviarlo en la nueva sesión.
2. Inspeccionar raíz y git status/inventario, sin modificar. Verificar que llegaron untracked y
   evidencia; detectar cambios del usuario, no reset ni instalación.
3. Verificar mapas, receipts, schemas/configs/scripts/launcher y conjuntos descritos arriba.
   Crear snapshot VPS nuevo como evidencia de transferencia, nunca sustituir baselines.
4. Identificar raíz real, OS/arch, UID/GID, permisos, padres/device/FS, recursos/cgroups/RAM/disco.
5. Repetir exclusivamente EXECUTION_B1/PREPARATION AND PREFLIGHT: Docker y recursos ajenos,
   imágenes por digest, caches lock/engine, driver/browser, puertos, namespaces y controlRoots.
   Preferir lecturas. Una prueba efectiva no-clobber requiere fixture mínimo descartable y alcance
   B1 explícito; documentar creación/cleanup. Sin ello marcar pendiente, no PASS por símbolo libc.
6. No iniciar workflow ejecutivo ni staging operativo. No download/install/build, DB/migrate,
   HTTP/browser real, productos ni promoción. Falta de cache/binario → BLOCKED antes de instalar;
   incompatibilidad que requiera modificar A/B → detener para revisión.
7. Si precondiciones demostradas, definir recetas/WorkOrders exactos nuevos, schemas/parsers puros,
   comandos allowlisted, presupuesto y lifecycle, hashes de receta/WO/manifest/adaptation/plan/
   metadata/code/validator/inputs. G07/G08 necesitan runs independientes para doble materialización,
   no replay del mismo permiso. No crear autoridad ni llamar operation/workflow/run/stage/promote.
8. Emitir `docs/migration/P4_6_EXECUTION_B1_VPS_PREFLIGHT.json`, con host/path mapping,
   hashes/provenance, verificaciones PASS/FAIL/BLOCKED/NOT_EXECUTED y alcance exacto. Si ya existe,
   no sobrescribir: nueva revisión identificada. Plan complementario nuevo `P4_6_EXECUTION_B2_VPS_PLAN.md`
   si necesario; conservar B1/B2_PLAN antiguos intactos.
9. Comparar propiedades anteriores y VPS, separar bloqueos resueltos/nuevos/no comprobados. No
   heredar BLOCKED ni PASS dependientes de host. Integridad histórica sí se reutiliza y corrobora.
10. Concluir READY_FOR_EXECUTION_B2, BLOCKED o FAILED solo según evidencia; preservar/cleanup
    de eventuales fixtures, registrar archivos creados/modificados y detener para revisión humana.
    READY no autoriza B2: pedir aprobación separada del paquete exacto después de su revisión.

## 10. Estado vigente G02–G24

| Casos | Estado completo vigente | Alcance / siguiente evidencia |
| --- | --- | --- |
| G02 | PASS solo alcance A | Planner puro determinista sin efectos; revalidar integridad. No equivale a generation PASS. |
| G03 | NOT_EXECUTED | Negativas autoridad A/B fixtures PASS; ejecutor/FS reales futuros B2. |
| G04 | PASS solo alcance A | Perfil/catálogo incompatibles rechazados antes de efectos; no gate global. |
| G05–G06 | NOT_EXECUTED | Colisiones/path/ownership/TOCTOU: unitarios no reemplazan escenarios reales. |
| G07–G08 | NOT_EXECUTED | Dos materializaciones reales deterministas por producto; solo B2 autorizado. |
| G09–G11 | NOT_EXECUTED | Comparación A/B, metadata y composición/rutas/schema reales. |
| G12–G14 | NOT_EXECUTED | Migraciones/grants/negativas y build/typecheck/tests reales, dependientes de host. |
| G15–G17 | NOT_EXECUTED | Auth/CRUD/CAS/IDOR y D02/HTML/RSC/browser reales. |
| G18–G19 | NOT_EXECUTED | Aislamiento simultáneo, caída DB/permisos/procesos; B2. |
| G20–G23 | NOT_EXECUTED | Scans runtime, preservación externa/regresión, cleanup y consumer completo. |
| G24 | BLOCKED | Revisión humana independiente de ambos candidatos exactos tras evidencia completa; no outputs actuales. |

La matriz individual/setup/assertions/evidencia está en propuesta P4.6 y B2_PLAN histórico.
B1 VPS solo demuestra precondiciones; no promueve estos casos runtime aunque todo el host pase.
Gates históricos database-migrations/authentication/compatibility/build-tests/cleanup PASS y
resource-authorization/module-crud PASS P4.5-B no certifican outputs nuevos. RA no es global genérica.
Generation/autonomy NOT_IMPLEMENTED, readiness BLOCKED hasta decisiones/evidencia propias.

## 11. Evidencia de creación de este handoff

Operación limitada a dos archivos nuevos: este documento y
`docs/migration/P4_6_VPS_HANDOFF_RECEIPT.json`. Receipt registra hash de handoff, inventario previo,
verificación 533/571 más dos documentos B1, hashes A/B/receipts, cero modificaciones existentes.
No se repitió B1, no se consultó infraestructura, no se copiaron productos ni se resolvieron bloqueos.
El receipt de creación es evidencia documental, no permiso ni prueba VPS.

## Prompt sugerido para nueva sesión Codex

```text
Estamos en un VPS de desarrollo nuevo. El repositorio y sus receipts son fuente de verdad.
Lee primero docs/business-platform/P4_6_VPS_HANDOFF.md y la lista mínima ordenada de fuentes
obligatorias que contiene. No reconstruyas el historial del chat ni releas toda P1–P4.

Autorizo exclusivamente repetir P4.6 EXECUTION_B1 / PREPARATION AND PREFLIGHT en este VPS.
El traslado no cambia contratos/roadmap. IMPLEMENTATION_A/B están aprobadas y sus bytes protegidos;
B1 del host anterior está BLOCKED y es evidencia histórica, no el estado del VPS.

Primero inspecciona repo y verifica integridad de la copia: 533 protegidos originales, mapas A/B,
571 paths del snapshot B1, documentos históricos B1/B2 y handoff según su receipt. Incluye archivos
untracked. No reemplaces baselines ni cambies bytes, receipts, launcher, schemas o implementación.
Mismatch/ausencia/contenido inesperado: detente y reporta; metadata de host se evalúa aparte.

Después inspecciona el host read-only: recursos/RAM/cgroups, Docker/permisos/recursos ajenos,
filesystem/device/renameat2, imágenes exactas, caches npm/Prisma offline, browser/driver fijado,
puertos y paths/controlRoots nuevos. No heredes PASS/BLOCKED de host anterior. Define aislamiento
Atlas/Brisa, recetas, WorkOrders y hashes exactos solo si precondiciones permiten un paquete válido.
No inventes valores/hashes/autorización; incompleto es BLOCKED. No ajustes A/B para adaptar el host.

No descargues/instales dependencias o imágenes; no npm ci/build, DB/migraciones, servidores HTTP,
browser real, staging operacional, materialización, workflow/WorkOrder, promoción ni P4.7.
Una prueba mínima de filesystem estrictamente necesaria para no-clobber puede usar únicamente
fixtures descartables propios sin productos, con inventario/cleanup; nunca tocar recursos ajenos.
Si falta cache/binario o se necesita cambiar código/contratos, registra BLOCKED y detente para revisión.
No generes secretos: documenta paths y lifecycle de env/TLS que requerirá futura autorización.

Conserva P4_6_EXECUTION_B1_PREFLIGHT.json y P4_6_EXECUTION_B2_PLAN.md intactos. Emite un receipt
nuevo docs/migration/P4_6_EXECUTION_B1_VPS_PREFLIGHT.json (sin sobrescribir si existe) y, si procede,
un nuevo P4_6_EXECUTION_B2_VPS_PLAN.md. Compara resultados antiguos/nuevos; registra hashes,
comandos read-only, limitaciones, recursos/cleanup y estado individual. No promuevas G runtime,
generation/autonomy/readiness. Finaliza READY_FOR_EXECUTION_B2, BLOCKED o FAILED y detente.

Este permiso es B1 exclusivamente. EXECUTION_B2, materializar Atlas/Brisa, ejecutar WorkOrders,
derivar EXECUTION_B_APPROVED, promover outputs y P4.7 siguen prohibidos sin autorización humana
posterior explícita vinculada al paquete exacto. Entrega la evidencia para revisión humana.
```
