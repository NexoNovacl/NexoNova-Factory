# P4.6 EXECUTION_B2 — plan de reanudación desde preflight B1 bloqueado

**B1 = BLOCKED. EXECUTION_B2 no autorizada.** Cierre humano de IMPLEMENTATION_B aceptado
como entrada; ningún receipt histórico fue cambiado. Este documento registra una preparación
interrumpida por las condiciones de parada del usuario, no un paquete ejecutivo listo.

## Resultado y parada

Los 533 archivos históricos, artefactos A/B y launcher permanecen byte-identical. Se verificaron
571 paths preexistentes únicos y la integridad canónica de ambos receipts A/B. Docker 29.8.1
responde mediante consultas read-only; ambas imágenes aprobadas están presentes. El sandbox
inicial negó socket Docker/netlink; las mismas consultas read-only se completaron con permiso
escalado, sin crear ni modificar recursos.

Se detectaron cuatro bloqueos: 0/195 objetos npm del lockfile en la cache examinada; cache Prisma
predeterminada ausente; binario Chromium revision 1243 no verificado (driver Playwright 1.63.0
existente); RAM física de unos 3,33 GiB, inferior al mínimo de 4 GiB exigido por el harness.
No se afirma que no exista otra cache en todo el host. No hubo búsqueda indiscriminada de archivos
privados ni descargas. Se detuvo la preparación ejecutiva según las condiciones 9, 10 y 23.
No se detectó ni corrigió una incompatibilidad de implementación; la consumibilidad completa
queda NOT_EXECUTED. Si resolver Prisma/cache exige cambiar A/B, se requiere revisión separada.

## Asignación propuesta, sin creación ni reserva

| Producto | Namespace | HTTP local | HTTPS local | DB |
| --- | --- | --- | --- | --- |
| Atlas | p46-b2-20260928-atlas | 4161 | 4461 | atlas_p46 |
| Brisa | p46-b2-20260928-brisa | 4162 | 4462 | brisa_p46 |

Base por producto: `/home/germanleiks/NexoNova/p46-execution-b2/<producto>`; destinos separados
`staging`, `validation`, `output`, y `control` para controlRoot. Red `namespace-net`, volumen
`namespace-data`, contenedores `namespace-db` y `namespace-app`; helpers con nombres cerrados
del harness. PostgreSQL no publica puertos. Los cuatro puertos propuestos estaban libres en ss;
esto no los reserva. Ningún directorio fue creado. Ancestro existente ext4, device 2053, UID1000,
modo0775: controlRoot futuro deberá ser propio 0700, sin links y con padres seguros verificados.
La libc exporta renameat2; no se realizó prueba efectiva RENAME_NOREPLACE en destinos ausentes.
La validación real de no-clobber/filesystem exacto queda pendiente, no PASS por presencia del símbolo.

Imágenes exactas (disponibles, sin pull ni ejecución):

- Node: `nexonova-p44b-node-openssl@sha256:0d0e3b31790d5b477357d4596d0c4b97f7fe2c7a43d7501821b7de1d90f52c16`.
- PostgreSQL: `postgres@sha256:efedf3595f1d6f415c08568ba171029bf54052e754cc9f030e3f2412b21f3d67`.

Presupuesto propuesto por producto: máximo3 contenedores concurrentes, 4096MiB, 3CPU, 12288MiB
temporales, 7200s totales; helper600s, readiness DB30s, red loopback/interna y npm offline. Instalar/
compilar secuencialmente; G18 requiere ambos productos vivos y presupuesto agregado revisado,
incluyendo navegador/OS. El host actual no satisface ni el mínimo individual. Disco libre observado
aproximadamente96,8GB decimales; no cuota ni reserva. Los límites de tiempo/disco agregados deben
quedar supervisados explícitamente antes de ejecutar; no asumir enforcement por tener campos WO.

## Paquete ejecutivo pendiente

El receipt B1 conserva hashes exactos de plan/manifest/adaptation/metadata/code/validators,
calculados exclusivamente en memoria, y hashes de fuentes existentes. No materializa payloads.
**workOrderHash y runtimeRecipeHash son null**, con causa explícita: no hay WorkOrders/recetas
consumibles emitidos después de la parada. No son placeholders válidos ni permiso implícito.
La lista inputHashesKnown es un inventario conservador de entradas, no el inputHashes ejecutivo final.

Para reanudar: resolver bloqueos, repetir preflight, fijar bytes exactos de receta por producto
(incluyendo expectedNextEnvHash aprobado y cache/controlRoot), registrar receta como input real,
validar `validate_recipe`/`recipes` y schemas sin efectos, fijar notBefore/expiresAt <=7200s y
calcular WorkOrders canónicos. Revalidar todos los hashes y recién entonces someter cada triple
workOrderHash/generationManifestHash/adaptationHash a aprobación humana separada. No construir
EXECUTION_B_APPROVED a partir de B1. No llamar stage/workflow/run/promote durante esta preparación.
G07/G08 requieren dos generaciones reales por producto: los WorkOrders finales deben describir
runs/destinos distintos y usos independientes; no reciclar una reserva consumida.

Acciones candidatas: stage, install, build, docker, migrate, bootstrap-fixtures, http-browser,
fault-injection, cleanup. **Promote excluida** de este borrador: requiere revisión posterior de
candidatos exactos y permiso expreso; ningún output actual que aprobar.

## Inputs privados y lifecycle

Por controlRoot: runtime.env, migrator.env, bootstrap.env y postgres.env, propios modo0600.
Operador proporciona credenciales técnicas distintas por rol/producto, secretos Better Auth
independientes y fixtures sintéticos admin/member. Nada de secretos en recetas/WorkOrders/receipt.
Bootstrap se revoca tras fixtures; recursos DB sintéticos se descartan con cleanup propio.
Directorio tls privado con certificado SAN localhost/127.0.0.1 y clave0600, vigencia acotada al run;
no cambiar truststore global. Registrar fingerprints públicos, nunca clave. Cache offline verificada
propia o de solo lectura según contrato; no adoptar/modificar caches/productos preexistentes.
La preparación o copia de inputs privados aún requiere alcance ejecutivo explícito. Cleanup no
elimina inputs ajenos: operador debe fijar ownership/disposición de todos los secretos temporales.

## Matriz futura y orden

G03–G06: negativas de autoridad/colisiones/path antes de outputs. G07–G11: materialización doble,
comparación independiente, metadata, rutas/schema/FK/launcher. G12–G14: DB/grants y compilación
real; G15–G19: auth/CRUD/D02/aislamiento/fallos. G20–G23: scans, preservación, cleanup y consumer.
Conservar evidencia saneada por bloque, comandos/exit/assertions/hashes; un exit0 no es PASS.
La siguiente tabla reproduce el criterio vigente, no registra ejecuciones:

| Caso | Setup/operación | Resultado y evidencia requeridos | Gates |
| --- | --- | --- | --- |
| G03 | Orden P4.2/revocada/hash alterado; ejecutor intenta render | Rechazo antes de efectos; causa y snapshot Incluir intento de usar G01 como permiso ejecutivo y reserva histórica como ruta. | GN |
| G04 | Catálogo desconocido/incompatible/ciclo/conflicto; planner | Bloqueo explícito por cada variante, sin fallback Bloquear policy/profile/version desconocidos y convenciones routing no soportadas. | CP, GN |
| G05 | Colisiones archivos/owners/modelos/rutas dinámicas y rutas core resueltas | Rechazo, ningún overwrite; fixtures negativas y hashes Probar /sign-in y descendientes, catch-all, /login, auth namespace, static/dynamic y page/handler incluso métodos disjuntos. | CP, GN |
| G06 | Traversal/symlink/destino existente/inputs cambiados tras plan | Fallo seguro, datos ajenos intactos; filesystem real Incluir cambio de dispatcher, next.config o launcher después del plan. | GN, CL |
| G07 | Config A; generador materializa dos veces en staging limpio | Sets y SHA256 idénticos; manifests y comandos Comparar bytes canónicos inventory/adaptation además de output. | GN |
| G08 | Config B; mismo generador, dos staging limpios | Igual reproducibilidad; sin rama específica por cliente Misma política/serializer que A, sin adaptación por cliente. | GN |
| G09 | A/B; comparación independiente | Solo diferencias públicas declaradas; ningún secreto/path/asset cruzado Inventory de composición compartido; diferencias públicas fuera de rutas, sin alias. | GN, CP |
| G10 | Outputs; consumidor verifica metadata/manifests | Hashes input/source/output/SQL/launcher coinciden; negativos por alteración Validar mapping /sign-in→reserva, /login real, referencias sin ciclos y estados históricos intactos. | GN, CP |
| G11 | Composición; verificadores inspeccionan schema/historial | Auth intacto, SQL FK conservado, no TechnicalSmoke, launcher D02 requerido Discovery/output exactos de11 rutas; cero /sign-in/aliases; reservas presentes. | CP, DB, GN |
| G12 | Dos DB vacías + upgrade sintético; migrator aplica/reaplica | Historial estable/FK real/grants correctos; SQL/CLI; sin db push/auto-migrate | DB |
| G13 | Runtime/bootstrap; intentos fuera de privilegios | Negativas42501/FK23503, cero efectos; SQL real | DB, RA |
| G14 | Dos outputs; CI local instala/genera/compila/typecheck/tests/build | Versiones/lock/digests fijos y salidas reales; no dependencia nueva Contrastar manifests de routing Next con inventario cerrado; defaults HEAD/OPTIONS verificados. | CP, BT |
| G15 | Admin/member/visitante; login/sesión/signup/logout/borde8h | Regresión P4.4-B aplicable y cookies reales; sin cambios auth /login real; GET /sign-in404 sin alias; allowlist auth conserva sign-in/email. | AU, BT |
| G16 | A/B/admin; CRUD/CAS/archivos/IDOR con dos conexiones | Regresión C01–C40 afectada por transformación; evidencia DB/HTTP | RA, MC, BT |
| G17 | Launcher correcto y selección auth-only negativa; HTML/RSC/browser | Vary unión sin duplicados, no-store, navegación y rutas ajenas preservadas; incorrecto no aceptable Descriptor/metadata/startup obligan start-requests.mjs; negativos auth launcher. | GN, CP, BT |
| G18 | Productos simultáneos con DB/red/volumen/secreto/prefijo propios | Cookie/ID/datos cruzados rechazados, controles positivos por producto | DB, AU, RA |
| G19 | Fixture DB indisponible/grants retirados y fallos de proceso | Fail-closed, receipts parciales veraces, recuperación sin datos falsos | DB, AU, MC |
| G20 | Logs/bundle/metadata/receipts/env temporal; scanner | Sin secretos conocidos/contaminación; observación navegador/red y límites del scan Scans incluyen inventario/vínculo/metadata nuevos. | GN, BT |
| G21 | Hashes históricos/productos/prototipo y pruebas P3/P4.2 | Igualdad con baselines previos, sin recalcular; reporte por excepción histórica Incluir contratos P4.2, decisión G01 y artefactos P4.5-B sin reinterpretar estados. | CP, BT |
| G22 | Éxito/fallo/timeout/cancelación y centinela ajeno | Cero recursos propios, ajenos intactos, cierre persistido también al fallar | CL |
| G23 | Consumidor recibe falta/hash alterado/FAIL/BLOCKED/NOT_EXECUTED | Gates afectados bloqueados; no hereda PASS agregado Alterar/omitir reservas, mapping, route/source hashes y referencias debe bloquear gates. | GN, BT, CL |
| G24 | Revisor evalúa outputs/diffs/evidencia y límites | Aceptación humana separada; ninguna promoción automática a autonomía/readiness Revisión explícita de inventario/rutas y launcher de ambos outputs. | GN |

G24 exige revisión humana independiente de ambos productos exactos: hashes de árbol/manifests,
inventory/adaptation/launcher, diferencias públicas, receipts runtime consumidos y cleanup. Ningún
PASS de tests A/B reemplaza esta revisión. generation/autonomy siguen NOT_IMPLEMENTED y readiness
BLOCKED; los gates históricos aceptados no se reinterpretan.

## Preservación, rollback y cierre

No tocar contenedores ajenos `dazzling_moore`/`xenodochial_mendeleev`, redes bridge/host/none ni
imágenes preexistentes. No volúmenes observados. No detener procesos/puertos del host. Cleanup
futuro solo por journal/labels/ID/hash y ownership, no por prefijo ni prune. Fallo/timeout/cancelación
exigen cleanup verificable y receipt parcial; objetos ambiguos se conservan y bloquean. Evidencia
se preserva, no rollback de DB real ni borrado de candidatos humanos. Revisar alcances de permisos
cleanup vencidos/revocados y recuperación manual antes del run.

B1 creó exclusivamente sus dos documentos: ningún fixture, controlRoot, staging ni recurso temporal;
cleanup operativo NOT_APPLICABLE. Persisten límites de provenance, timing no formal, una instancia,
TLS local, scans no exhaustivos, launcher D02 y ninguna garantía de otros Next/hosting/proxies/CDN.
Próximo checkpoint: revisión humana de bloqueos y provisión de precondiciones; repetir B1 y emitir
paquete exacto revisable antes de pedir EXECUTION_B2. No P4.7.
