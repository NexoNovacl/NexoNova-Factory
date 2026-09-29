# P4.6 — Plan de implementación para revisión humana

**READY_FOR_HUMAN_REVIEW — propuesta, no autorización de implementación ni ejecución.**

El detalle contractual G01/ALTERNATIVE_A está **DESIGN_APPROVED** mediante
`docs/migration/P4_6_DESIGN_APPROVAL.json`, que referencia por SHA256 los tres documentos
revisados. Sus textos históricos «pendiente revisión» permanecen intactos: la decisión posterior
registra la aprobación sin reescribirlos. Este plan amplía el diseño operativo pendiente de revisión;
no atribuye aprobación previa a los contratos ejecutivos que aquí se proponen.

Propósito conservado: P4.6 generación/generalidad de dos productos ficticios mediante una misma
capacidad. P4.7 autonomía/regresión independiente sigue fuera de alcance. No se implementó código,
no se crearon schemas ejecutables ni se ejecutaron G02–G24 durante esta preparación.

## 1. Límites A/B y autorización

**A — implementación sin efectos externos:** archivos nuevos de schemas, parsers, adaptación,
planner, render puro en memoria, validadores, tests y documentación. Los tests pueden escribir
fixtures mínimas en un directorio temporal propio; no crean productos, instalan paquetes, abren
puertos, consultan Docker ni ejecutan código de plantillas. El planner produce bytes en memoria
/stdout; guardar su plan/receipt es una escritura documental explícita, no materialización.
No imports con efectos ni descubrimiento de rutas ejecutando Next. A requiere autorización futura
de implementación; actualmente solo está autorizada esta documentación.

**B — efectos sujetos a autorización ejecutiva:** escritura de productos/staging, promoción,
npm/Prisma/build, procesos, Docker, DB, migraciones, bootstrap, HTTP/browser, tests con filesystem
real de materialización, alteración controlada de permisos/DB y cleanup de esos recursos. Se puede
escribir la lógica del materializer/harness bajo autorización de implementación; su ejecución,
incluso «solo render a staging», pertenece a B. Pruebas unitarias del código B usan fixtures mínimas;
no sustituyen las integraciones reales de B.

Ni el diseño aprobado, ni un inventario `executionAuthority=none`, ni un WorkOrder histórico,
ni la aprobación de A autorizan B. Toda transición a B exige un paquete de autorización concreto
vinculado a hashes. No se pedirá aprobar un destino o conjunto de efectos aún indeterminado.

## 2. Inventario exacto de cambios propuestos

Todos los paths siguientes son **nuevos y futuros**. Si alguno existe al comenzar, comparar con
el checkpoint y detener ante ownership ambiguo; nunca sobrescribir por conveniencia.

| Componente | Archivos futuros | Presupuesto aproximado |
|---|---|---|
| Contratos | `schemas/business-execution-inventory.v1.json`, `business-route-adaptation.v1.json`, `public-business-generation.v1.json`, `business-composition.v1.json`, `business-generation-plan.v1.json`, `business-generation-manifest.v1.json`, `business-generation-metadata.v1.json`, `business-generation-validation.v1.json`, `business-execution-work-order.v1.json`, `business-execution-authorization.v1.json` (todos bajo `schemas/`) | 10 archivos, 900–1500 líneas JSON |
| Validación aislada | `factory/business_execution_contracts.py`, `factory/business_execution_inventory.py` | 2 archivos, 600–950 líneas |
| Pipeline puro | `factory/business_generation.py` | 1 archivo, 350–550 líneas |
| Efectos y autorización | `factory/business_materialization.py`, `factory/business_execution_authority.py` | 2 archivos, 550–900 líneas |
| Consumidor de evidencia | `factory/business_generation_evidence.py` | 1 archivo, 300–500 líneas |
| Entradas CLI | `scripts/generate_business_product.py`, `scripts/validate_business_generation.py`, `scripts/check_business_generation_evidence.py` | 3 archivos, 450–750 líneas |
| Browser real | `scripts/check_business_generation_browser.mjs` | 1 archivo, 200–350 líneas |
| Tests | `tests/test_business_execution_contracts.py`, `test_business_execution_inventory.py`, `test_business_generation.py`, `test_business_materialization.py`, `test_business_generation_evidence.py` (bajo `tests/`) | 5 archivos, 900–1500 líneas |
| Fixtures | `tests/fixtures/p46/contract-cases.json`, `route-cases.json`, `evidence-cases.json` | 3 archivos, 250–500 líneas |
| Descriptor | `config/business/compositions/business-auth-internal-requests-0.1.0-d02.json` | 1 archivo, 150–300 líneas |
| Configs públicas | `config/business/generation-pilots/atlas/spec.json`, `config/business/generation-pilots/brisa/spec.json` | 2 archivos, 40–100 líneas |
| Guía | `docs/business-platform/P4_6_GENERATION_RUNBOOK.md` | 1 archivo, 150–250 líneas |

Estimación: **32 archivos de implementación/config/tests/guía, 4840–8150 líneas**, más receipts,
manifest por output y logs acotados. Son bandas de revisión, no cuota ni permiso para ampliar scope.
Si hace falta otro componente, nueva dependencia o más del 25% sobre el límite superior, presentar
el cambio antes de seguir. No se instala una librería de validación nueva.

**Archivos existentes que requieren modificación: ninguno previsto.** No tocar `factory/cli.py`,
`factory/schemas.py`, generador corporate, contratos P4.2, runners históricos, core/auth ni overlay.
Entrada CLI nueva separada. No cambiar AGENTS/MIGRATION_PLAN para anunciar un gate no demostrado.
Las modificaciones de configuración descritas abajo ocurren únicamente en outputs nuevos y mediante
transformaciones enumeradas; no modifican sus fuentes aprobadas.

## 3. Contratos a implementar y reglas comunes

Los dos primeros schemas deben transcribir el detalle aprobado del anexo, no rediseñarlo:
`nexonova.business-execution-inventory.v1`, `nexonova.business-route-adaptation.v1`;
política `p42-to-approved-runtime.v1`; perfil `business-auth-internal-requests-0.1.0-d02`.
Once rutas reales, `/login`, catch-all y tres operaciones auth, subtree `/sign-in` no materializable,
D02 y launcher obligatorio. Ningún alias, redirect o rewrite nuevo; la reserva es regla nueva del
adaptador, no cambio retroactivo de P4.2. `/api/auth/sign-in/email` sigue permitido.

Todos los nuevos contratos: versión exacta, campos desconocidos rechazados, claves duplicadas
rechazadas en carga, tipos estrictos (boolean no es integer), sin NaN/infinito, hashes SHA256
identificados como bytes originales o bytes canónicos, paths relativos normalizados por rechazo
(no corrección silenciosa), sin secretos. Schemas validan forma y validadores puros verifican
relaciones/conjuntos/hashes. Implementar solo el subconjunto de JSON Schema necesario y documentar
sus keywords; rechazar schemas con keywords de aserción no soportadas. No anunciar cumplimiento
general de JSON Schema. Tests positivos y negativos para cada keyword usado, especialmente
`$ref` local, `const`, límites de arrays, `uniqueItems`, `additionalProperties` y composiciones si
se utilizan. No delegar silenciosamente esas reglas al validador histórico incompleto.

| Formato nuevo propuesto (prefijo `nexonova.`) | Campos y semántica obligatoria |
|---|---|
| `public-business-generation.v1` | `productId`, `public{name,title,primaryColor}`, perfil fijo, selección única internal-requests 0.1.0. Slug ASCII limitado; nombre/title públicos acotados; color hex. Sin políticas auth/ownership configurables, rutas, credenciales, paths arbitrarios ni autoridad. |
| `business-composition.v1` | Perfil, referencias SHA a fuentes aprobadas, lista completa source→destination/owner, exclusiones explícitas, transforms versionadas, SQL/migraciones, launcher, outputs derivados permitidos, referencias de limitaciones. No globs abiertos para copiar archivos nuevos no aprobados. |
| `business-generation-plan.v1` | Spec/descriptor/inventory/adaptation/code/schema hashes, lista determinista de archivos esperados con hash/owner/transform, manifest y metadata esperados, limitaciones, `executionAuthority:none`. Sin destinos absolutos, reloj ni decisiones de infraestructura. |
| `business-generation-manifest.v1` | ProductId, hashes de inputs/plan/inventory/adaptation/generador, files ordenados con path/bytes/SHA/owner/provenance, historial SQL/launcher, exclusiones y transform IDs. Manifest de fuentes generado antes de build, no baseline histórico recalculado. |
| `business-generation-metadata.v1` | Identidad pública, capacidad/perfil, manifest SHA, inventory/adaptation SHA, versiones, comando startup, selector Prisma, restricciones y referencias de limitaciones. `validationState:NOT_EXECUTED`, `executionAuthority:none`; resultado runtime solo en receipt externo. |
| `business-generation-validation.v1` | Run/productId, entrada/autorización/manifest/source/validator hashes, versiones/digests reales, subcasos, comandos saneados/exit/assertions/evidence hashes, recursos, cleanup, limitaciones, gates calculados. Estado por subcaso PASS/FAIL/BLOCKED/NOT_EXECUTED; sin PASS por existencia de código. |
| `business-execution-work-order.v1` | Solicitud inmutable: plan/inputs/code/validators SHA, destinos exactos, action allowlist, límites de recursos/tiempo/red, identificadores run/productos, rollback/cleanup, vigencia y usos máximos. No boolean `approved` autoemitido como permiso. |
| `business-execution-authorization.v1` | WorkOrder bytes SHA, aprobación humana trazable externa al output, actions subset exacto, vencimiento/revocación y uso por stage/run. No transporta secretos. Verificación exige ancla de confianza del operador, no solo que exista este archivo. |

### 3.1 Manifest y metadata: ejemplo estructural de diseño

Los marcadores H_* son hashes simbólicos; no son fixtures ejecutables ni valores aceptables por schema.
Las referencias de manifest no incorporan su propio hash, el hash de metadata ni receipts posteriores.

```json
{
  "format": "nexonova.business-generation-manifest.v1",
  "productId": "atlas",
  "profile": "business-auth-internal-requests-0.1.0-d02",
  "planSha256": "H_PLAN",
  "inventorySha256": "H_INVENTORY",
  "adaptationSha256": "H_ADAPTATION",
  "generatorSha256": "H_CODESET",
  "files": [{"path":"scripts/start-requests.mjs","sha256":"H_SOURCE","bytes":123,"owner":"internal-requests","provenance":{"source":"modules/internal-requests/0.1.0/files/scripts/start-requests.mjs","transform":"copy-bytes.v1"}}],
  "launcher": ["node","scripts/start-requests.mjs"],
  "limitationsRef": {"path":"docs/migration/P4_5_B_FINAL_RECEIPT.json","sha256":"H_APPROVED_RECEIPT"}
}
```

El ejemplo abrevia files: implementación exige el conjunto completo. `bytes:123` es ilustrativo.
Metadata en `factory-generation/metadata.json` referencia `factory-generation/manifest.json` por
hash; inventario/adaptación van en el mismo directorio. Manifest cubre todas las fuentes y contratos
copiados excepto manifest/metadata: el receipt enumera y hashea estos dos por separado. La exclusión
está cerrada, no permite ocultar otros archivos. No se distribuyen receipts históricos con secretos
ni copias de evidencia de laboratorio al runtime.

Grafo: inputs y código → inventory → adaptation → plan → manifest → metadata → WorkOrder →
authorization → receipts por etapa → receipt final. El plan contiene hashes previstos de payload,
no hash del manifest que lo referencia. WorkOrder puede fijar hashes de manifest/metadata calculados
en memoria antes de materializar. Los hashes de código del materializer y validadores son propios
además del hash del generador puro. Arrays ordenados y serializer `inventory-json.v1` para nuevos
contratos deterministas; nunca sustituir algoritmos históricos. Reloj/run paths solo en contratos
ejecutivos/receipts, no en fuentes deterministas.

### 3.2 Receipt granular

Cada caso tiene `status`, `requiredSubcases`, `executedSubcases`, `evidence[{path,sha256}]`,
`sourceHashes`, `validatorHashes`, `recoveredEvidence`, `newEvidence`, `limitations` y `gateIds`.
Toda referencia debe resolverse dentro del evidence root autorizado, sin symlinks ni escapes.
`recoveredEvidence` conserva procedencia y límites, no equivale a ejecutar el output nuevo.
Un comando con exit 0 sin assertions requeridas no basta. G24 necesita aceptación humana posterior
de **ambos outputs exactos por hash**; no inferirla del diseño aprobado ni de la autorización B.

## 4. Pipeline y composición concreta

1. **Planner** carga configs públicas y descriptor cerrado, valida contratos, produce un plan sin
   efectos y hashes previstos. El plan P4.2 es antecedente, no spec ni permiso del nuevo cliente.
2. **Adapter** verifica bytes históricos y diseño aprobado, conserva sus estados, descubre/reconcilia
   las once rutas y genera inventory/adaptation. No ejecuta WorkOrders ni imports de runners.
3. **Generator** transforma en memoria un mapa de archivos aprobado, rechaza conflictos, produce
   bytes deterministas/manifest/metadata. No subprocess, npm, sockets o escritura de producto.
4. **Materializer** recibe mapa y autorización externa; revalida todos los hashes/paths antes de
   escribir en staging propio. No decide políticas ni transforma nuevamente con inputs cambiantes.
5. **Validators** puros y luego reales, separados; consumidor independiente de evidencia vuelve a
   calcular cobertura/hashes/gates. No confiar en el resumen que produzca el harness.

Transformaciones propuestas en outputs, exactas y allowlisted:

- Copiar core y overlay por mapping sin sobrescribir paths; bytes source permanecen idénticos,
  salvo derivados explícitos siguientes. No copiar `.git`, node_modules, .next, envs, secretos,
  evidence, estado del laboratorio o clientes Prisma ya generados.
- Crear `prisma/business/schema.prisma`: composición aprobada P4.5-B, cambiando únicamente el
  output del generator de auth a requests en esta **copia derivada** y concatenando el fragmento
  InternalRequest. Auth schema/User originales byte-identical; sin relación inversa.
- Crear `prisma/business/migrations/` copiando SQL auth + requests y migration_lock exactos.
  FK SQL RESTRICT permanece real; el diff conocido que sugeriría eliminarla es observación,
  jamás instrucción aplicable. `prisma.requests.config.ts` copiado intacto.
- Crear `tsconfig.generation-checks.json` derivado de checks aprobado con includes adicionales
  `src/modules/internal-requests/**/*.ts` y `validation/requests-users.ts`, sin duplicados, mismo
  compilerOptions. Mantener `tsconfig.checks.json` y `tsconfig.json` originales byte-identical.
  Next podrá regenerar `next-env.d.ts` solo en copia de validación: forma exacta esperada fijada
  en descriptor antes de B a partir de evidencia de la versión aprobada; nunca una exclusión
  genérica. `.next/`, `build-checks/`, `src/generated/`, node_modules y tsbuildinfo son derivados
  declarados por herramienta, escaneados pero no incorporados al manifest de fuentes.
  Si Next requiere cambiar tsconfig/config core fuera de esa receta, BLOCKED para revisión;
  no normalizar ni aceptar automáticamente defaults nuevos.
- No cambiar package.json/package-lock del core: identidad pública en `product-public.json`,
  README generado y metadata. Dos configs varían nombre/título/color como datos públicos;
  no se promete branding visible nuevo en UI. No alterar auth/UI aprobados para aplicar tema.
  Arranque documentado **solo** `node scripts/start-requests.mjs`; `npm start` heredado no es
  receta válida del producto compuesto. Validator rechaza cualquier receta ejecutiva auth-only.
- Crear `GENERATION.md` con comandos explícitos de generate/migrate/checks/start, referencias
  locales a manifest y límites. No incluir Docker daemon/Factory/Python en fuentes de app.

Antes de autorizar B, descriptor debe contener mapa completo y hashes de todos los derivados;
si no es posible fijar una transformación sin cambiar core/auth, detener para revisión. No es
permiso para inventar una excepción durante la ejecución.

## 5. Autorización ejecutiva por hashes

El WorkOrder propuesto vincula dos specs (atlas/brisa), descriptor, schemas, inventory/adaptation,
plan por producto, árbol de código y tests, fuentes/migraciones/lockfiles, manifest esperado,
destinos absolutos canónicos, workspace de validación y límites. Acciones separadas:
`stage`, `promote`, `install`, `build`, `docker`, `migrate`, `bootstrap-fixtures`, `http-browser`,
`fault-injection`, `cleanup`. No comandos shell arbitrarios; argv de recetas allowlisted.

El operador aprobará el SHA256 del WorkOrder y las acciones. Ancla propuesta: argumento explícito
`--approved-work-order-sha256` junto con referencia de aprobación humana verificable fuera del
árbol generado; el executor compara ambos y el receipt registra la procedencia. No firma digital
ni resistencia frente a un operador malicioso en el mismo host. Un JSON creado por el generador
no establece esa ancla. Validar expiry, revocation y registro de usos protegido por lock exclusivo;
runId/stage únicos, no reutilizar una autorización consumida ni reintentar después de crash a ciegas.
La aprobación de implementación A no se reutiliza como ancla B.

Revalidar bytes desde snapshots privados antes de cada stage con efectos. Input/código cambiado,
destino diferente, presupuesto excedido, permiso revocado o etapa fuera de orden → BLOCKED.
El hash es integridad/vinculación, no autenticación humana por sí mismo. Credenciales efímeras
se suministran por canal privado, sin formar parte de datos públicos ni aparecer en argv/logs.
Si implementación A cambia después de emitir WorkOrder, generar nuevo paquete para aprobación;
no actualizar el hash aprobado dentro del mismo receipt.

## 6. Staging, ownership y promoción

Destinos propuestos para futura aprobación: `products/p46-atlas` y `products/p46-brisa`, nuevos;
si no existen esos padres se autorizan explícitamente en WorkOrder. Staging hermano en el mismo
filesystem `.p46-staging/<runId>/<productId>/`, privado 0700. Nunca escribir dentro de productos
históricos ni reutilizar `/var/tmp/nexonova-p45b-*`.

Registrar journal de intención **antes** de cada creación, token de ownership local no secreto
más runId/WorkOrder SHA, IDs/inodos cuando corresponda. `lstat`, no seguir symlinks; destino
inexistente, paths relativos cerrados, rechazo casefold/traversal y archivos especiales/hardlinks.
Usar creación exclusiva y promoción no-clobber bajo lock en padre propio; no asumir que un
`rename` común impide reemplazar un directorio existente. Si falta garantía no-replace en el host,
bloquear, no emular con check-then-rename vulnerable. El modelo sigue asumiendo host confiable.

A1/A2 y B1/B2 renders en staging independientes deben ser idénticos. Un staging inmutable fuente
se valida y se promueve solo tras gates técnicos; instalar/build en copia de validación propia,
registrando hash inicial igual a manifest y diff final de derivados permitido. Así npm/.next/
Prisma generado no contamina el baseline de fuentes. Receipt liga copia validada al exacto staging.
Promoción atómica por producto; dos renames no son una transacción global: si solo uno tiene éxito,
registrar promoción parcial, bloquear aceptación del par y no borrar automáticamente el primero.
Outputs promovidos permanecen candidatos, no HUMAN_ACCEPTED, hasta G24.

## 7. Secuencia de implementación y checkpoints

| Bloque, orden obligatorio | Trabajo / prueba | Casos que prepara o ejecutará después | Detención |
|---|---|---|---|
| A0 | Autorización A, snapshot propio P4.6 y comparación histórica; ningún ajuste de baseline | G21 | Drift/no autorización: BLOCKED |
| A1 | Schemas, parser estricto, fixtures; tests por keyword/format | G02–G05,G10,G23 | Error contractual: no planner |
| A2 | Adapter/discovery/intersección rutas y reserva; hashes y serializer | G02,G04–G06,G10,G11 | Incompatibilidad/diff core: revisión |
| A3 | Descriptor completo, dos configs, plan y render en memoria, transforms exactas | G02,G07–G11 | Derivado no fijable: no materializar |
| A4 | WorkOrder/authority/materializer; tests sin productos; journal/rollback/locks | G03,G06,G19,G22 | Negativa insegura: no B |
| A5 | Harness/consumer/browser scripts; tests de receipts y cobertura, revisión de scope | G12–G24 | Evidencia falsa/incompleta: no B |
| H1 | Paquete concreto A validado, comandos/digests/destinos y presupuesto; revisión humana B | G03 | Sin permiso ejecutivo: detener |
| B1 | Revalidar snapshot y permisos; negativos FS reales y plan sin efectos | G02–G06 | Cualquier efecto ajeno: FAIL, cleanup |
| B2 | Materialización repetida A/B y comparación independiente de manifest/rutas/SQL | G07–G11 | Divergencia: no infraestructura |
| B3 | Setup de toolchain (npm/engine/generate, dependencia parcial G14), luego DB vacías/upgrade, migrate/reapply/FK/grants y negativas reales | G12,G13,G14 parcial | No FK/cambio User/DDL runtime: FAIL |
| B4 | Completar checks/typecheck/tests/build con toolchain de B3; comparación rutas Next | G14 | Drift/versión/error: no HTTP |
| B5 | Auth, CRUD/IDOR/CAS, D02, navegador, aislamiento y fallos | G15–G19 | Fallo obligatorio: no promoción |
| B6 | Scans, preservación, cleanup éxito/fallo/timeout/cancelación; consumer negativo | G20–G23 | Cleanup/evidencia inválida bloquea |
| B7 | Promoción candidata autorizada, dossier exacto A/B y revisión humana | G24 | Esperar aceptación de ambos |

Ningún PASS de A prueba G07–G19 real. G02–G24 quedan hoy NOT_EXECUTED. Progreso por bloque
se guarda en checkpoint; FAIL bloquea dependientes y permite únicamente recoger evidencia y
cleanup ya autorizado. Ausencia de herramienta/permiso = BLOCKED; no sustituir por mocks.

## 8. Tests previos a toda materialización

Parser: claves duplicadas, extras, boolean como entero, NaN, formatos/refs desconocidos, keywords
no implementadas, hashes de bytes vs canónicos. Inventario: las once rutas, allowlist auth,
/sign-in/subtree, catch-all intersectado, static/dynamic, parámetros renombrados, page/handler,
métodos disjuntos, casefold, metadata route/grupos/rewrites inesperados, D02/launcher alterado.

Pipeline: orden de filesystem no cambia bytes, dos public specs usan mismo camino, sin branch por
cliente; fuente cambiada invalida plan; graph/hash sin ciclos; transformación exacta User/SQL;
no TechnicalSmoke; lista completa de archivos; diferenciación file vs dir y paths inseguros.

Autoridad: orden P4.2, G01 y DESIGN_APPROVED rechazados como permisos; hash/acción/destino/expiry/
revocation incorrectos, stage replay y falta de ancla. Tests de scheduler/journal simulan crash,
no ejecutan Docker. Consumer: artifact faltante/truncado/alterado, evidencia cruzada A/B,
subcaso ausente, hash de validator cambiado, FAIL/BLOCKED/NOT_EXECUTED bloquean su gate.

Los tests de fixtures no cuentan como pruebas de TOCTOU/promoción/cleanup reales: B1/B6 las
repite en paths autorizados con centinela ajeno. Mantener assertions independientes de helpers
de producción para no probar únicamente que una función coincide consigo misma.

## 9. Comandos previstos (no ejecutados; CLI nueva por implementar)

Desde raíz Factory, A sin productos/infraestructura:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_business_execution_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_business_generation*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_business_materialization.py'
python3 scripts/generate_business_product.py plan --spec config/business/generation-pilots/atlas/spec.json --stdout
python3 scripts/generate_business_product.py plan --spec config/business/generation-pilots/brisa/spec.json --stdout
```

B requiere archivos ejecutivos exactos y autorización externa; variables son marcadores que el
WorkOrder deberá resolver, no comodines permitidos:

```text
python3 scripts/generate_business_product.py stage --work-order <WO> --authorization <AUTH> --approved-work-order-sha256 <SHA> --product atlas
python3 scripts/generate_business_product.py stage --work-order <WO> --authorization <AUTH> --approved-work-order-sha256 <SHA> --product brisa
python3 scripts/validate_business_generation.py --work-order <WO> --authorization <AUTH> --approved-work-order-sha256 <SHA> --stage database
python3 scripts/validate_business_generation.py --work-order <WO> --authorization <AUTH> --approved-work-order-sha256 <SHA> --stage build
python3 scripts/validate_business_generation.py --work-order <WO> --authorization <AUTH> --approved-work-order-sha256 <SHA> --stage integration
python3 scripts/validate_business_generation.py --work-order <WO> --authorization <AUTH> --approved-work-order-sha256 <SHA> --stage preservation-cleanup
python3 scripts/check_business_generation_evidence.py --run <RUN_RECEIPT> --read-only
python3 scripts/generate_business_product.py promote --work-order <WO> --authorization <AUTH> --approved-work-order-sha256 <SHA> --technical-receipt <RECEIPT>
```

Recetas internas B en copia de validación aislada (por producto): `npm ci --ignore-scripts
--no-audit --no-fund`; postinstall Prisma engine exacto revisado; `node node_modules/prisma/build/index.js
generate` y `generate --config prisma.requests.config.ts`; `validate --config prisma.requests.config.ts`;
`migrate deploy --config prisma.requests.config.ts` dos veces mediante migrator; auth-only upgrade
sintético separado; `tsc -p tsconfig.generation-checks.json`, `npm test`, `npm run typecheck`,
`npm run build`; `node scripts/start-requests.mjs`. Migraciones/grants no se ejecutan al arrancar.
SQL de grants exacto y probes de permisos/FK se incluyen por hash. No `db push` ni diff aplicado.

No ejecutar runners P4.4/P4.5 históricos que escriben paths/receipts fijos: trasladar assertions
necesarias al harness nuevo, referenciar source SHA y conservar el alcance; nunca importar sus
entrypoints con efectos. Regresión P3/P4.2: primero auditar tests seleccionados y ejecutar solo
los que no reescriben artefactos aprobados, con reporte nuevo G21; si requieren efectos, incluirlos
en el WorkOrder o quedar BLOCKED, no omitirlos silenciosamente.

## 10. Docker, DB, navegador y presupuesto de ejecución

Fijar las referencias aprobadas y comprobar disponibilidad sin sustituir tags:

- Node/OpenSSL: `nexonova-p44b-node-openssl@sha256:0d0e3b31790d5b477357d4596d0c4b97f7fe2c7a43d7501821b7de1d90f52c16`.
- PostgreSQL: `postgres@sha256:efedf3595f1d6f415c08568ba171029bf54052e754cc9f030e3f2412b21f3d67`.
- Next 15.5.25, Better Auth 1.7.5, Prisma 7.5.0 y lockfile aprobado. No nuevas dependencias.
- Browser real con tooling disponible previamente: versión/binario/hash se capturan en H1.
  Si falta, BLOCKED; instalar/descargar una dependencia no queda autorizado por este plan.

Cada producto: red Docker interna, volumen PostgreSQL, DB, credenciales migrator/runtime/bootstrap,
secreto auth y prefijo cookie propios. Roles/secretos aislados; bootstrap técnico temporal sin grants
InternalRequest. Hosts/orígenes HTTPS locales distintos; no considerar dos puertos aislamiento de
cookie suficiente (cookies no se aíslan por puerto). Certificados efímeros separados y browser
contexts A/B, más un contexto adversario para transferir cookie/IDs y demostrar rechazo con
controles positivos. No cambiar trust store global. TLS local no certificado productivo.

Propuesta de máximo simultáneo: 2 app + 2 DB + 1 helper build + 1 browser; DB upgrade temporal
sustituye una DB de prueba, no expande silenciosamente el límite. Dos redes/volúmenes activos y
hasta dos temporales adicionales solo durante pruebas recovery, registrados con labels
`nexonova.p46.run`/`product`. App 1 GiB/2 CPU/pids256; DB 1 GiB/1 CPU; build 2 GiB/2 CPU;
browser 2 GiB/2 CPU; máximo agregado 8 GiB y 10 CPU de cuotas (no promesa de rendimiento).
Tope propuesto disco temporal 12 GiB y ejecución 120 min, build 10 min por intento; revisar recursos
del host en H1. No retries indefinidos. Límite excedido → checkpoint/BLOCKED y cleanup seguro.

Solo loopback publicado, puertos exactos asignados y aprobados antes de B; colisión no cambia
puerto automáticamente. Sin montaje socket Docker dentro de producto, sin privileged/host network.
Red de instalación temporal separada para npm/engine fijados, permitida solo si autorización la
incluye; ningún proveedor externo funcional. Aplicaciones sin salida a Internet. El harness opera
Docker desde host confiable con privilegios acotados. Sin deployment ni datos reales.

## 11. Preservación byte-identical

Comparar con baselines históricos usando su algoritmo, más snapshot de entrada P4.6. El snapshot
nuevo no reemplaza un baseline antiguo ni puede normalizar diferencias. Conjuntos protegidos:

- AGENTS.md, MIGRATION_PLAN.md; todos los schemas/configs/plans/contracts P4.2 existentes,
  `factory/business_contracts.py`, `factory/schemas.py`, CLI/generación corporate existentes.
- Todos los archivos existentes `templates/business-platform-auth/`,
  `modules/internal-requests/0.1.0/`, SQL auth/requests y grants; imagen-lock y fuentes OpenSSL.
- P3 baselines/receipts, P4.3 evidencia/TechnicalSmoke, P4.4-A/B y P4.5-A/B docs/receipts/runs/
  validators; ninguna sobrescritura de FINAL_RECEIPT/FINAL_REPORT.
- `corporate-site`, `nexonova-website`, `synthetic-website` y `nexonova-prototype` según paths,
  exclusiones y hashes ya inventariados en P4.5-B ENTRY y receipts finales; no inventar otra
  ubicación a partir del nombre. Archivos fuera del repo se leen, nunca escriben.
- Propuesta/inventario/review G01, archivos de historia y nueva decisión DESIGN_APPROVED.

`P4_6_ENTRY.json` futuro contendrá los hashes por archivo, referencias a baselines y estado Git
previo (incluyendo trabajo del usuario). Comparación independiente final no confía en manifest del
generador para elegir qué proteger. Solo nuevos paths de implementación aprobados pueden variar;
si hay diferencias previas, describirlas y bloquear antes de atribuirlas a la fase. No `git reset`.

## 12. Rollback, cleanup y recuperación

Registrar recursos antes de creación y completar IDs tras éxito; manejar ventana crash entre ambas
por labels + inspección, nunca eliminación por prefijo solo. Cleanup en finally, señales/timeout y
comando recovery separado con mismo WorkOrder/ownership. El permiso incluye cleanup de sus
recursos aunque venza permiso de creación; no permite crear nuevos ni borrar candidatos aceptados.

Antes de promoción: conservar evidencia saneada, eliminar únicamente staging/copia de validación/
secrets temporales/containers/redes/volúmenes propios. Después de promoción fallida/parcial:
cuarentena/no aceptación del candidato; cualquier eliminación exige ownership/hash sin cambios del
usuario y alcance cleanup explícito. Si fue modificado externamente, bloquear eliminación y reportar.
DB sintéticas: descartar recursos propios tras captura; no down-migrations ni rollback de datos reales.
Código nuevo: revertir solo paths/diffs propios mediante revisión, no borrar trabajo ajeno.

Cleanup demuestra ausencia final de recursos propios y centinela ajeno intacto. Imágenes preexistentes
no se borran; no `docker system prune`. Artefactos/evidencia quedan preservados. Crash host/SIGKILL
puede requerir recovery manual; no declarar limpieza hasta inspección real. Si cleanup falla,
gate cleanup BLOCKED/FAIL y generación no PASS aunque app funcione.

## 13. Receipts/checkpoints de futura ejecución

Bajo `docs/migration/`: `P4_6_ENTRY.json`, `P4_6_IMPLEMENTATION_CHECKPOINT.json`,
`P4_6_EXECUTION_WORK_ORDER.json`, `P4_6_EXECUTION_AUTHORIZATION.json`,
`P4_6_FINAL_RECEIPT.json`, `P4_6_FINAL_REPORT.md` (solo cierre real).
Bajo `docs/migration/p4-6-runs/<runId>/`: `stage-<NN>.json`, `resource-journal.jsonl`,
`hash-index.json`, `preservation.json`, `cleanup.json`, `scan.json`, `route-build-diff.json`,
`reproducibility-atlas.json`, `reproducibility-brisa.json`, `generality-diff.json`,
`consumer-negatives.json`, `human-output-acceptance.json` y evidencia saneada por producto/caso.

Checkpoint puede actualizarse atómicamente como puntero; stage receipts cerrados son inmutables.
Nunca sobrescribir un run previo; continuación referencia hashes de lo recuperado y explica qué
supuestos siguen válidos. Logs con cuotas, redacción antes de persistir, sin cookies/passwords/URLs
DB/keys; scan final incluye manifest/metadata/inventory/adaptation/WorkOrder/receipts. Los scans
siguen no exhaustivos. Evidencia truncada que elimina assertions obligatorias bloquea el caso.

## 14. Gates, riesgos y condición de cierre

Entrada: aprobación humana P4.5-B y detalle G01, integridad, revisión de **este plan**, autorización A
antes de implementar y autorización B por hashes antes de efectos. Gates históricos PASS se conservan
como entrada, no prueba de productos nuevos. Salida: generation solo PASS con G02–G24 completos,
consumer válido, aceptación humana A/B y CP/DB/AU/RA/MC/BT/CL válidos según matriz original.
Resource-authorization continúa limitado a InternalRequest. NOT_EXECUTED obligatorio bloquea gate;
PASS_WITH_LIMITATIONS requiere todas las pruebas y límites aceptados, no es waiver de faltantes.

Riesgos principales: drift de archivos/Next, transformación no fijada, confianza de operador,
TOCTOU/promoción parcial, evidencia insuficiente, permisos DB, recursos disponibles. Fail-closed
ante modificación core/auth, nueva dependencia, FK ausente, privilegios ampliados, alias /sign-in,
launcher errado, pérdida de Vary/no-store, contrato ambiguo, secreto filtrado o cleanup no demostrado.
No hay contradicción nueva detectada con contratos aprobados; cualquier incompatibilidad durante A
se presenta para revisión, no se resuelve mediante cambio silencioso de scope.

Limitaciones heredadas permanecen trazables a P4.5-B: provenance histórica incompleta; sin garantía
formal de timing; rate limit de una instancia; TLS local; scans no exhaustivos; dependencia del
launcher; sin garantía automática ante versiones Next, standalone, hosting, proxies/CDN. Se añaden
límites explícitos del plan: autorización basada en operador/host confiable, validación Schema
acotada, identidad pública en datos/documentación sin tema UI nuevo y promoción no atómica del par.

**Hoy:** G01 detalle DESIGN_APPROVED; G02–G24 NOT_EXECUTED; generation/autonomy NOT_IMPLEMENTED;
readiness BLOCKED. La revisión documental no calcula PASS de runtime ni prueba cleanup de B.
P4.7 conserva autonomía sin Factory/Python, persistencia/restart independiente, baseline/manual y
regresión final. Este plan no adelanta ese gate.

**Detener aquí para revisión humana del plan. No se solicita ni presume autorización de ejecución.**
