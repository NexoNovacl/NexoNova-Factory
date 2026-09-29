# P4.6 — IMPLEMENTATION_B: entrega para revisión humana

Estado: componentes implementados y tests aislados completados. **executionAuthority=none**.
Este documento y el receipt B no autorizan EXECUTION_B, ningún WorkOrder, Atlas, Brisa ni P4.7.
El plan aprobado, contratos A y evidencia histórica se conservan sin modificaciones.

## Componentes entregados

| Archivo nuevo | Responsabilidad |
| --- | --- |
| `factory/business_materialization.py` | Frontera ejecutiva futura; revalidación externa y de hashes, reservas, journal, staging, ownership, promoción no-clobber y cleanup/recovery. |
| `scripts/validate_business_generation.py` | Recetas runtime cerradas, transporte acotado, recursos etiquetados, PostgreSQL/grants/fixtures, build y cleanup; relay TLS local. CLI exclusivamente descriptiva. |
| `scripts/check_business_generation_browser.mjs` | Harness inyectable de navegador, sesión/UI/API/SSR-RSC y headers D02. CLI exclusivamente descriptiva; no carga un browser por defecto. |
| `tests/test_business_materialization.py` | Fixtures descartables, carreras, negativas, recuperación y contratos de harnesses sin infraestructura real. |

No se agregó dependencia ni schema ejecutable adicional. El contrato de receta runtime se valida
estrictamente dentro del nuevo harness. No cambió el generador A ni su `codeHash`: los cuatro
archivos B deben figurar en `inputHashes`; además `validatorHash` fija el array ordenado
`[{path, sha256: digest(bytes)}]` de esos cuatro paths mediante `object_hash` de A.

## Autoridad y consumo

`ExecutionSession` conserva `executionAuthority=none`; no emite permisos. Antes de efectos exige
bundle válido, WorkOrder y autorización separados, aprobación externa EXECUTION_B_APPROVED,
`workOrderHash`, `generationManifestHash`, `adaptationHash`, plan/metadata/code/validator/input
hashes vigentes, acciones, revocaciones, tiempo actual y destinos exactos. El callback del operador
es una frontera de confianza externa: nunca debe derivar aprobación de este receipt ni de un flag
local. El tiempo suministrado debe coincidir con el reloj actual (tolerancia de dos segundos).

El controlRoot privado queda ligado tanto a la receta hasheada como al estado externo. `flock`
serializa procesos; O_EXCL y fsync reservan cada par runId/acción antes de su uso. Un cambio de
binding no recicla ese par. `workflow` reserva las acciones únicas de una secuencia y no convierte
cada comando en una nueva autorización. Fallo o interrupción consume la reserva; no hay retry
permisivo. Una reserva parcial queda bloqueada, no disponible para reuso.

La revalidación ocurre antes del lock y nuevamente bajo lock e inmediatamente antes de efectos.
El permiso de cleanup ya registrado puede sobrevivir al vencimiento del permiso de creación,
como exige el plan §12. El journal conserva la hora y aprobación originales: no renueva stage/build.
Cambios de aprobación, hashes, revocación u ownership siguen bloqueando cleanup. Esto requiere
un journal protegido y un operador confiable; no constituye una firma externa nueva.

## Staging, promoción y recuperación

Staging y copia de validación son árboles distintos con ownership ligado al triple de hashes.
El journal encadena hashes y registra intención antes del efecto, inodos y hashes posteriores.
No se adopta contenido inesperado. La promoción usa Linux renameat2(RENAME_NOREPLACE), mismo
filesystem y destino inexistente; ausencia de esa primitiva bloquea, sin fallback overwrite.
Requiere consumer independiente con los siete gates técnicos PASS y manifest coincidente.
El resultado es un candidato, nunca aceptación humana ni G24 PASS.

Cleanup verifica el árbol completo antes de borrar, luego identidad y bytes por entrada; no sigue
symlinks. ControlRoot/raíz propios son privados; subdirectorios derivados de paquetes pueden ser
0755 dentro de esa raíz privada. Solo la copia de validación permite links relativos de paquetes
bajo node_modules cuyo destino permanezca dentro de node_modules; nunca fuentes/staging.
Recovery acepta únicamente ausencia demostrada por intención de borrado o rename pendiente
con el mismo snapshot. Un crash entre mkdir y registro de ownership requiere revisión manual.
Journal corrupto, objeto ajeno o bytes cambiados bloquean. No hay borrado por prefijo, prune ni
rollback de bases reales. Cleanup runtime reconcilia intención/labels/ID y ausencia posterior.
`retain_candidate=True` conserva explícitamente el staging inmutable para promoción, no un
recurso runtime oculto. Candidatos promovidos necesitan disposición explícita y revisión si fallan.

## Receta runtime futura (ejemplo estructural, no ejecutable)

```json
{
  "format": "nexonova.business-runtime-recipe.v1",
  "executionAuthority": "none",
  "runId": "run-human-approved",
  "productId": "atlas",
  "namespace": "p46-run-human-approved-atlas",
  "nodeImage": "<NODE_IMAGE exacto del harness>",
  "postgresImage": "<POSTGRES_IMAGE exacto del harness>",
  "port": 4443,
  "httpPort": 4000,
  "controlRoot": "/ruta/aprobada/control",
  "sourceDirectory": "/ruta/aprobada/validation",
  "envFiles": {
    "runtime": "/ruta/aprobada/control/runtime.env",
    "migrator": "/ruta/aprobada/control/migrator.env",
    "bootstrap": "/ruta/aprobada/control/bootstrap.env",
    "postgres": "/ruta/aprobada/control/postgres.env"
  },
  "tlsDirectory": "/ruta/aprobada/control/tls",
  "cacheDirectory": "/ruta/aprobada/control/cache",
  "expectedNextEnvHash": "sha256:<64 hex aprobados>"
}
```

Los placeholders se rechazan. La receta concreta deberá estar en inputHashes del WorkOrder;
ninguna fue creada para ejecución. Los paths de secretos son referencias, nunca credenciales
embebidas en el WorkOrder/receipt. Env files separados, privados y estables durante el workflow;
SQL verifica identidades y credenciales independientes. Bootstrap se revoca al terminar fixtures.
Los bytes de passwords/output no se escriben en el journal: solo resultados y hashes saneados.

## Precondiciones exactas para EXECUTION_B

1. Revisión humana de este receipt. Luego autorización ejecutiva externa separada para WorkOrder(s)
   concretos, triple de hashes, acciones y presupuesto. Esta fase no produjo dicha autorización.
2. Revalidar los 533 históricos, todos los archivos A y cuatro B; fijar receta, imágenes exactas,
   inputs, destinos y validatorHash. Inventario de 11 rutas, /login real, /sign-in subtree reservado
   no materializable, /api/auth/sign-in/email permitido y launcher start-requests.mjs intacto.
3. ControlRoot privado preexistente, padres de destinos seguros, mismo filesystem para promoción,
   permisos del host/daemon revisados; identificadores/puertos/red/volumen/DB independientes por
   producto. Inventario inicial y centinela ajeno. No compartir credenciales entre productos.
4. Imágenes fijadas disponibles y cache npm/Prisma preparado y verificado; npm ci es offline,
   engine setup sin red. Cache insuficiente bloquea: no descarga ni ampliación silenciosa.
5. Env files/certificado local/clave y fixtures técnicos privados preparados por el operador bajo
   autorización específica; TTL y disposición final de esos inputs explícitos. No borrar caches
   o secretos preexistentes no propios. Presupuesto total/timeout y supervisión de señales revisados.
6. Driver de navegador instalado y fijado provisto por operador, callback de guard con reserva
   http-browser vigente; relay TLS loopback exclusivamente local. No instalación automática.
7. Harness por API: reservar acciones del workflow una sola vez. Las CLI `--describe` no ejecutan.
   Los comandos CLI ilustrativos del plan no son una interfaz ejecutiva disponible en esta entrega.
8. Ejecutar las assertions reales completas G03–G24 conforme a propuesta/runbook, incluyendo
   aislamiento, negativas, fallo DB, restart, scans, comparación y cleanup. Las recetas son piezas
   de infraestructura; exit 0 o el resumen `runtimeGate=NOT_EVALUATED` no certifica esos casos.
   La orquestación/consumer confiables deben conservar evidencia granular y detener dependientes.
9. Conservar receipts/evidencia independiente, cleanup y preservación; promover únicamente con
   consumer técnico válido. Revisión humana de ambos candidatos para G24; no P4.7 automático.

## Validación de IMPLEMENTATION_B y límites

Receipt y checkpoint registran 50 tests A y 48 B, IDs/subtests y resultados. La corrida final bloqueó
sockets y `ExecutionSession.operation/workflow`; solo permitió un proceso Node del test unitario
con browser falso y fetch prohibido. Cuatro procesos transitorios compitieron por una reserva de
fixture y fueron unidos/cerrados. No se ejecutó un WorkOrder. Los tiny trees temporales usados para
probar rename/delete son fixtures, no productos ni staging operativo. No quedaron fixtures/hilos.

Los resultados no demuestran Docker/PostgreSQL/build/HTTP/browser runtime. G02/G04 conservan
PASS de A; los demás casos completos siguen NOT_EXECUTED, G24 BLOCKED. Generation/autonomy
NOT_IMPLEMENTED y readiness BLOCKED. Gates históricos aprobados no se reabren.

Limitaciones adicionales: Linux/local FS y host confiable; no prueba formal contra actor host con
mismo UID/root; journal no es firma externa; promoción entre productos no es atómica; recuperación
ambigua requiere revisión y no recicla permisos; helpers offline requieren cache; integración real
y cobertura runtime del harness siguen pendientes. Inputs privados del operador no se eliminan
sin ownership/autorización. No hay garantía automática de tolerancia a SIGKILL/crash del host.

Persisten provenance histórica incompleta, ausencia de garantía formal de timing, rate limit de
una instancia, TLS local, scans no exhaustivos, launcher específico D02 y ausencia de garantías
frente a cambios Next/standalone/hosting/proxies/CDN. Ninguna implementación B fortalece esas
limitaciones por sí sola. Se detiene aquí para revisión humana.
