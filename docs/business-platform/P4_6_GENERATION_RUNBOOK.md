# P4.6 IMPLEMENTATION_A — uso y checkpoint humano

Solo componentes puros. La autorización humana de IMPLEMENTATION_A no autoriza implementar
ni ejecutar B. Los documentos aprobados anteriores permanecen byte-identical; el cierre y los
hashes de esta ejecución están en `docs/migration/P4_6_IMPLEMENTATION_A_RECEIPT.json`.

## Componentes disponibles

- Diez schemas aislados. Inventory/adaptation transcritos del diseño aprobado; los restantes
  concretan el plan ejecutivo sin otorgar autoridad. Parser estricto de claves/tipos/formatos.
- `business_execution_contracts`: serialización inventory-json.v1, hashes, subconjunto Schema,
  paths y lecturas sin symlinks/hardlinks. No nuevas dependencias.
- `business_execution_inventory`: descriptor fijado por SHA256, igualdad del árbol fuente
  completo de 58 archivos, once rutas, exports, referencias y digests históricos; reservas y
  colisiones antes de producir cualquier plan. El perfil se actualiza solo con revisión humana.
- `business_generation`: render y plan en memoria, manifest, metadata y validación de bundle;
  69 entradas de bytes previstas por piloto, **ningún archivo de producto escrito**.
- `business_execution_authority`: validación pura de WorkOrder, manifest y adaptación, ancla
  externa, tiempo, acciones, referencias, código, inputs y snapshot de revocación/usos.
- `business_generation_evidence`: consumidor puro de forma, cobertura, hashes y bindings de
  evidence envelopes; recalcula gates, jamás confía en PASS agregado. Las pruebas usan fixtures
  explícitas de unidad, no las presentan como evidencia runtime.
- CLI de planificación stdout y CLI de lectura de receipts con bindings independientes obligatorios.

Los nombres de hash concretos de plan/manifest son `planHash`, `inventoryHash`, `adaptationHash`,
`generatorHash` y `generationManifestHash`. Se distinguen hashes de bytes de entrada (WorkOrder,
manifest/adaptation ejecutivos) de hashes canónicos (`object_hash`). Los contratos generados son
bytes canónicos UTF-8 + LF, sin reloj, destino absoluto, normalización Unicode o secretos.

El manifiesto enumera todas las fuentes/contratos salvo manifest y metadata, cuyo hash se vincula
por metadata/WorkOrder/receipt sin ciclo. Los outputs conservan package/lock/auth/User/SQL/launcher;
los derivados autorizados se calculan solo en memoria. Identidad pública: datos y documentación,
no implementación de un tema UI nuevo.

## Verificación permitida A

Desde raíz Factory, sin bytecode/cache:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_business_execution_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_business_generation*.py'
PYTHONDONTWRITEBYTECODE=1 python3 scripts/generate_business_product.py plan --spec config/business/generation-pilots/atlas/spec.json --stdout
PYTHONDONTWRITEBYTECODE=1 python3 scripts/generate_business_product.py plan --spec config/business/generation-pilots/brisa/spec.json --stdout
```

La CLI no ofrece `stage`, `promote`, `build` ni `cleanup`. No redirigir su output a un producto.
Tests trabajan en memoria; la defensa contra escrituras/procesos/red se comprueba interceptando
intentos durante el planner. Esto es evidencia contractual de A, no aislamiento del sistema
operativo ni prueba real de TOCTOU.

El consumidor read-only requiere `--run`, `--read-only`, `--expected-manifest-hash`,
`--expected-source-hash`, `--expected-validator-hash` y `--expected-product-id`. Sin prueba G24
externa, un receipt no obtiene aprobación humana por contener una cadena PASS. No hay receipts
runtime P4.6 válidos todavía. No ejecutar un harness histórico para fabricarlos.

## Autorización no equivale a ejecución

`authorization_context` recibe bytes y parámetros explícitos, incluyendo el SHA de WorkOrder
aprobado, approval externo, tiempo y snapshots inmutables de usos/revocaciones. Valida al menos
`workOrderHash`, `generationManifestHash`, `adaptationHash`. Falta/mismatch lanza `ContractError`.
G01, DESIGN_APPROVED, IMPLEMENTATION_A y órdenes P4.2 no pasan como permiso ejecutivo.

El resultado inmutable declara `effectExecutionImplemented=false` y
`requiresAtomicUseReservation=true`. **No consume usos ni reserva locks**: hacerlo sería Fase B.
Dos verificaciones puras con el mismo snapshot pueden devolver el mismo contexto. Un futuro
executor deberá reservar atómicamente el uso, revalidar hashes/paths y consultar estado vigente
antes de efectos. Ningún caller puede presentar esta función como prevención atómica de replay.
El modelo confía en operador/host; hashes no sustituyen autenticación humana ni firma digital.

## Límites del validador Schema

Soporta solo `$schema` 2020-12, `$defs`, `$ref` local a defs, `type` (object/array/string/integer/
boolean/null), properties/required/additionalProperties=false, items, min/maxItems, uniqueItems,
min/maxLength, pattern, minimum/maximum, const, enum y anotaciones description/title.
Cualquier otro keyword o referencia externa se rechaza. No es implementación general de JSON
Schema. Reglas semánticas (conjuntos, rutas, hashes, fuentes, autoridad) se comprueban aparte.
Los defaults HEAD/OPTIONS de Next siguen pendientes de runtime, no son nuevos permisos del módulo.

## Archivos deliberadamente no creados de los 32 previstos

- `factory/business_materialization.py`: sin executor, filesystem staging, locks, journal o promoción.
- `scripts/validate_business_generation.py`: sin harness de Docker/DB/build/HTTP.
- `scripts/check_business_generation_browser.mjs`: sin automatización browser real.
- `tests/test_business_materialization.py`: no existe materializer que probar; autorización pura
  se prueba en `tests/test_business_execution_contracts.py`.

Quedan 28 archivos de implementación/config/tests/guía, más ENTRY, CHECKPOINT y receipt de A.
No se modificó código existente. No se implementa B como «código dormido».

## Checkpoint y limitaciones pendientes

Revisión humana del receipt A. Antes de B se requerirá autorización separada de IMPLEMENTATION_B
para componentes diferidos y, posteriormente, EXECUTION_B sobre un WorkOrder concreto por hashes.
No crear hoy un WorkOrder ejecutivo aparentemente autorizado.

Antes de EXECUTION_B: fijar receta exacta del next-env derivado usando evidencia aprobada, destinos,
puertos, herramientas/browser/digests, presupuesto y regla de promoción no-clobber. No se ha
inspeccionado el estado de Docker ni creado DB/redes/volúmenes/procesos. Hacer esa preparación
solo bajo el alcance futuro correspondiente. La atomicidad, ownership real, cleanup, FK/migraciones,
SSR/RSC/cookies/D02 y comparación de manifests Next requieren pruebas B reales.

Consumer A valida consistencia de envelopes y referencias; no prueba que un comando declarado
se ejecutó realmente. La confianza en el harness futuro y su evidencia deberá evaluarse en B.
Fixtures unitarias no satisfacen casos runtime aunque su estructura sea válida. El consumer liga
producto/run/manifests/source/validator y bloquea ausencias, FAIL, BLOCKED y NOT_EXECUTED.

Preservar limitaciones P4.5-B: provenance histórica incompleta, timing sin garantía formal,
rate limit de una instancia, TLS local, scans no exhaustivos, launcher específico y sin garantías
sobre nuevas versiones Next, standalone, hosting o proxies/CDN. `/login` sigue real; `/sign-in`
y descendientes son reserva nueva del adaptador no materializable; `/api/auth/sign-in/email`
permanece permitido. No cambian estados históricos.

Generation sigue NOT_IMPLEMENTED en el gate global (no hay productos materializados aceptados),
autonomy NOT_IMPLEMENTED y readiness BLOCKED. No iniciar P4.7.
