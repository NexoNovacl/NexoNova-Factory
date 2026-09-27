# P4.6 — Propuesta de planificación y aclaración contractual

**Estado: READY_FOR_DESIGN_REVIEW / implementación NO autorizada.**
**Solo documentación; P4.6 y P4.7 no iniciadas.** Fecha: 2026-09-27.

## 1. Fuente de verdad y propósito original

`MIGRATION_PLAN.md` §7 define P4 como plataforma empresarial/módulos y contempla composición,
generadores y validadores. No enumera P4.6 individualmente. El desglose concreto está en
`docs/business-platform/P4_1_PROPOSAL.md` §9:

- **P4.6: Generación/generalidad.** Dos configs ficticias y productos nuevos, manifests/diffs/
  metadata, reproducibilidad, misma ruta por capacidad, rechazo de colisiones/módulos desconocidos,
  gates DB/auth bloqueantes y aceptación humana de ambos outputs.
- **P4.7: Autonomía/regresión.** Arranque independiente, datos persistentes, cleanup, baseline
  business/manual, sin Factory/Python en runtime y regresión P3.

P4.4-A §10 exige seleccionar explícitamente schema/historial de producto en P4.6 sin TechnicalSmoke.
P4.5-A §§9/19 y P4.5-B confirman que la composición de laboratorio todavía no es generación Factory.
No se encontró un propósito alternativo de P4.6 en esos documentos. No se confunde P4.6 con la
fase principal P6 (roles asistidos), ni P4.7 con P7 (preparación de entrega/operación).

El estado antiguo «pendiente de aprobación» del documento inicial de migración y los gates
NOT_IMPLEMENTED de receipts P4.2 describen sus momentos históricos. No se reescriben ni invalidan
las aprobaciones posteriores. Las restricciones de los WorkOrders P4.2 no autorizan ejecutar P4.6.

## 2. Aprobación de entrada y relación con fases previas

La instrucción humana actual registra **P4.5-B = HUMAN_APPROVED / PASS_WITH_LIMITATIONS**,
acepta C01–C40 y D02. Este documento registra esa aprobación sin modificar FINAL_REPORT,
FINAL_RECEIPT, PROGRESS, D02 ni evidencia anterior.

P4.4-B aporta auth/roles/bootstrap/sesiones aprobados. P4.5-B aporta InternalRequest y autorización
por recurso, migración/grants, UI y composición de laboratorio. P4.6 debe convertir esa composición
en productos generados reproducibles; no reimplementar sus reglas ni reabrir P4.5-B salvo evidencia
concreta de regresión/invalidez. Una diferencia contractual de inventario futuro no demuestra por sí
misma una regresión de auth o invalida C01–C40.

## 3. G01 resuelto humanamente: ALTERNATIVE_A

**G01 = HUMAN_APPROVED / ALTERNATIVE_A.** Aprobación actual limitada a nuevo inventario
versionado de rutas reales, /login explícito y adaptación trazable de reserva /sign-in, sin alias.
P4.2 permanece intacto. Esto no reabre ni invalida P4.2/P4.4-B/P4.5-B y no autoriza ejecución P4.6.

Decisión registrada en `docs/migration/P4_6_G01_DECISION.json`. Propuesta previa preservada en
`docs/migration/p4-6-planning-history/g01-pending/`.

El diseño concreto está en [P4_6_EXECUTION_INVENTORY_DESIGN.md](P4_6_EXECUTION_INVENTORY_DESIGN.md):
dos contratos nuevos v1, schemas y ejemplos completos, once rutas reales y allowlist auth,
adaptación paso a paso, determinismo y colisiones. Propone reservar /sign-in y descendientes
sin materializarlos; su alcance de subtree es una regla nueva del adaptador, no una reinterpretación
de P4.2. /api/auth/sign-in/email permanece permitido por la política auth existente.

**Estado del detalle: DESIGN_PROPOSED / pendiente revisión humana.** Se resolvió la alternativa;
los detalles nuevos aquí propuestos no se consideran aprobados por inferencia. No se crea alias,
redirect ni rewrite /sign-in; el startup obligatorio continúa scripts/start-requests.mjs.

## 4. Objetivo exacto y alcance común propuesto

Demostrar que un generador determinista por capacidad business-platform produce dos proyectos
ficticios nuevos, coherentes con la composición aprobada, a partir de dos configuraciones públicas,
con baseline, manifest, metadata y diff verificables y validación real de cada output.

Mismo core/módulo/versiones y algoritmo para ambos. Variaciones permitidas deben declararse
previamente: identidad pública, nombre/título/color y namespace de producto; ningún branch por
nombre de cliente. No agregar campos a la spec antigua silenciosamente. Configs nuevas, raíces de
salida nuevas, datos sintéticos y secretos suministrados privadamente por el operador/harness.

Separar plan sin efectos, staging de fuentes, materialización autorizada y validación con recursos
Docker/DB propios. El plan/render no ejecuta npm, migraciones, bootstrap ni arranca servicios.
Una autorización futura debe vincular hashes de inputs, acciones, destinos y presupuesto de recursos.

**Invariante arquitectónica:** InternalRequest requiere `scripts/start-requests.mjs`. El launcher
original de auth no es equivalente. El futuro descriptor de composición/metadata y la receta de
arranque deben apuntar al launcher específico; una selección distinta bloquea aceptación. D02
preserva Vary de Next más Cookie y no-store; el generador no sustituye ese comportamiento.

## 5. Fuera de alcance

P4.7/autonomía certificada, agentes/LLM, deployment, servicios externos, hosting/CDN/proxies nuevos,
actualización de dependencias, modificación de core/auth/contratos aprobados, nuevos módulos,
multitenancy, RLS, reasignación, DELETE físico/unarchive, administración de cuentas, recuperación
por email, carga productiva/SLA y mantenimiento de productos existentes (P5). No mover el ERP
sin aprobación independiente. No escribir sobre corporate-site ni productos existentes.

## 6. Componentes/archivos futuros, sujetos a diseño y aprobación

| Área | Acción futura prevista | Restricción |
|---|---|---|
| `factory/business_generation.py` (nuevo) | Adaptador por capacidad, plan/render/materialización | Sin refactor silencioso de generación P3 |
| `scripts/generate_business_product.py` (nuevo) | Entrada separada y estados/códigos de salida veraces | CLI corporate intacta |
| Schemas business de ejecución/generation-manifest/metadata/receipt (nuevos, inventario/adaptación v1 definidos en anexo; otros formatos pendientes) | Autorización por hashes, archivos/owners, migraciones, launcher, gates y evidencia | No ampliar enums/formatos v1 in situ; G01 aprobado; detalle sujeto a revisión |
| Configs de dos pilotos ficticios en raíces nuevas | Inputs públicos y selección de capacidad idéntica | No alterar fixtures P4.2, ni guardar secretos |
| Descriptor/allowlist de composición nuevo | Copias aprobadas, glue explícito, exclusiones y conflictos | Cada transformación debe indicar fuente y hash |
| `templates/business-platform-auth/` y `modules/internal-requests/0.1.0/files/` | Entradas de solo lectura | Bytes aprobados inmutables; auth/SQL/D02 intactos |
| Configs generadas del producto | Schema/historial combinados, compilación checks, receta de arranque | Transformaciones revisadas en output, no modificación de inputs |
| Validadores/pruebas de generación business nuevos | Reproducibilidad, negativos, materialización e integración real | No copiar política divergente ni reescribir runners/receipts P4.5-B |
| Docs y receipts P4.6 nuevos | Diseño final, entry, runs, comparación y cierre | Evidencia incremental inmutable |

No se decide ahora modificar archivos protegidos compartidos. Si el diseño requiere hacerlo,
se debe presentar diff/scope para aprobación antes de implementación. Reutilizar helpers puros
por import solo tras comprobar sus efectos; no asumir que todo helper histórico es ejecutable
sin sobrescribir sus receipts.

## 7. Contratos que permanecen intactos

AGENTS/MIGRATION_PLAN, baseline P3 y contratos corporate; schemas/config/authorization/plan
P4.2; TechnicalSmoke/P4.3 como fixture separada; auth P4.4 y aprobación P4.5-B con todos sus
receipts/artefactos. Conservar literales admin/member y open/closed, ownership de sesión,
404 uniforme, CAS expectedVersion, archivado lógico terminal y FK SQL RESTRICT sin inversa User.

No mover TechnicalSmoke a la DB del producto ni aplicar un diff que elimine la FK SQL. Mantener
migrate deploy separado del arranque y roles migrator/runtime/bootstrap con grants mínimos.
No introducir signup, defaults secretos, endpoints de bootstrap o cambios de sesión/cache.

## 8. Riesgos técnicos y tratamiento

- Inventario de rutas incompleto: G01 resuelto; validar el nuevo inventario propuesto y probar colisiones
  de todas las rutas reales y equivalencia de segmentos dinámicos.
- Confundir un piloto de laboratorio con generador: prohibir copiar node_modules/.next/DB,
  paths privados, envs, receipts o fixtures de usuarios al producto entregable sin necesidad revisada.
- Glue fuera del namespace del módulo: inventario explícito de rutas, scripts, configs y SQL;
  abortar ante conflictos, nunca «último archivo gana».
- Mutaciones Next en tsconfig/next-env: distinguir baseline de generación de derivados de build.
  P4.3 pide normalizar defaults antes de congelar producto; proponer transformación específica
  verificable sin tocar inputs aprobados ni recalcular baseline histórico. Aceptación exacta pendiente
  del diseño de composición, no excepción amplia automática.
- Generación no reproducible: rutas absolutas, timestamps, orden filesystem y secretos fuera de
  bytes deterministas; timestamps solo en receipts de ejecución, no en manifest determinista.
- Usar startup auth por defecto: comprobación contractual y negativa real del launcher obligatorio.
- Autorizar escritura/DB por metadata: autorización externa vinculada a inputs/destinos; rollback
  de staging sin borrar trabajo ajeno ni datos reales.

## 9. Limitaciones heredadas y trazabilidad

| Limitación aceptada | Tratamiento en P4.6 | Continuidad |
|---|---|---|
| Provenance histórica incompleta | Referenciarla como recuperada; hashes nuevos de generador/inputs/tests por run | No reconstruir evidencia anterior |
| Timing sin garantía formal | Mantener errores uniformes; medición descriptiva si procede | No certificar indistinguibilidad |
| Rate limiting de una instancia | Cada producto de prueba: una instancia; sin escalado | No resolverlo con Redis en esta fase |
| TLS local | HTTPS de prueba con certificado efímero y contexto acotado | No equivalencia a TLS productivo |
| Scans no exhaustivos | Valores sintéticos conocidos + heurísticos/logs/bundles/metadata | No auditoría completa de seguridad |
| Launcher específico D02 | Descriptor y comando explícitos; pruebas HTML/RSC/navegación/errores | Requisito arquitectónico obligatorio |
| Next/hosting/standalone/proxy/CDN | Mantener versiones/entorno probados | Cambios exigen nueva revisión/regresión, no garantía automática |
| Host confiable/crash manual | Recursos por run, cleanup normal/fallo/timeout | Recovery tras interrupción abrupta documentado |
| FK SQL y paginación | Preservar SQL y limitación de snapshot mutable | No aplicar diff destructivo/retry ciego |

El futuro manifest debe transportar referencias de estas limitaciones; no necesita incorporar
receipts con datos privados al runtime del producto.

## 10. Criterios de aceptación futuros

Dos outputs nuevos producidos por la misma ruta de capacidad, cada uno reproducible en dos renders
limpios. Conjunto de archivos/hashes/owners/inputs y modificaciones permitidas del output explícitos.
Comparación entre productos solo contiene diferencias públicas autorizadas, sin contaminación.

Ninguna autorización antigua P4.2 permite render/DB por inferencia. Unknown module, conflicto,
input alterado, path inseguro, destino existente y evidencia inválida bloquean sin efectos ajenos.

Build y pruebas sobre fuentes realmente materializadas, no sobre la plantilla de laboratorio.
Ambos productos verifican migraciones/FK/grants, auth, ownership/CAS/archivo y D02 con Docker,
PostgreSQL, HTTP y navegador cuando corresponde. No basta recuperar C01–C40 para afirmar
que el generador no dañó la composición. Preservación y cleanup completos son obligatorios.

## 11. Matriz propuesta (G01 aprobado; G02–G24 NOT_EXECUTED)

Cada caso requiere snapshot/hashes de input, comando/actor/exit, assertions, referencias de evidencia
saneada y cleanup. Los casos DB/HTTP/browser se ejecutan sobre ambos outputs cuando aplica.
Gates: GN generation, CP compatibility, DB database-migrations, AU authentication,
RA resource-authorization (InternalRequest), MC module-crud, BT build-tests, CL cleanup.

| ID | Setup / actor / operación | Resultado y evidencia requerida | Gates |
|---|---|---|---|
| G01 | Decisión humana registrada | HUMAN_APPROVED / ALTERNATIVE_A; detalle contractual propuesto en anexo, sin permiso de ejecución | CP, GN |
| G02 | Inputs correctos; planner sin permiso de ejecución | Plan determinista, cero producto/DB/procesos creados; inventario antes/después Incluir inventory/vínculo sin efectos; executionAuthority=none. | GN |
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

G01 es decisión de diseño, no un test automatizado capaz de otorgarse aprobación humana.
La cobertura concreta de regresión se vinculará a qué bytes transforma el generador; cualquier
supuesto modificado exige reejecutar su prueba, no aplicar exenciones retrospectivas.

## 12. Gates de entrada y salida

Entrada humana aprobada P4.5-B: database-migrations, resource-authorization (InternalRequest),
module-crud, authentication, compatibility, build-tests y cleanup PASS. Auth-role-probes sigue
limitado a sesión/rol. Verificar integridad al iniciar una futura ejecución sin reabrir la fase.
G01 ya está aprobado. Aún se requieren revisión del diseño concreto de nuevos contratos y autorización explícita
de ejecución por alcance. **La autorización actual es solo planificación.**

Ahora: generation=NOT_IMPLEMENTED; autonomy=NOT_IMPLEMENTED; readiness global=BLOCKED.
Ningún gate de implementación P4.6 se evalúa PASS con esta documentación.

Salida futura propuesta: generation puede pasar a PASS solo con G02–G24 completos, G01 aprobado,
dos outputs aceptados y todos sus gates técnicos válidos. CP/DB/AU/RA/MC/BT/CL se recalculan desde
evidencia de esos outputs; los PASS de entrada no sustituyen las pruebas afectadas. Autonomy
permanece NOT_IMPLEMENTED y readiness BLOCKED hasta P4.7 y su revisión.

PASS: todos los obligatorios ejecutados y válidos. PASS_WITH_LIMITATIONS: igual cumplimiento,
con límites explícitamente aceptados; no es un waiver para casos faltantes. FAIL: incumplimiento
reproducible. BLOCKED: precondición/autorización/herramienta ausente o decisión no resuelta.
NOT_EXECUTED queda por caso y bloquea su gate obligatorio. Este borrador está listo para revisión del diseño; ejecución permanece no autorizada.

## 13. Evidencia y receipts futuros

Nuevos `P4_6_ENTRY.json`, decisiones de contratos, catálogo de composición, dos manifests de
generación y metadata versionados, diffs A/A y B/B de reproducibilidad y A/B de generalidad,
receipts de ejecución por producto/run, matriz granular final, scan, preservación y cleanup;
`P4_6_FINAL_REPORT.md`/`P4_6_FINAL_RECEIPT.json` solo al finalizar una ejecución autorizada.

Cada run conserva hashes de source/validator/dependencias/digests, inputs, outputs y SQL;
estados PASS/FAIL/BLOCKED/NOT_EXECUTED, pruebas invocadas, evidencia recuperada vs nueva,
recursos propios, limitaciones y aprobación humana externa. Guardar progreso después de bloques.
No incluir secretos/DB URLs/tokens/HAR sensibles en receipts ni deducir aprobación de un booleano
suministrado por el generador. Separar determinismo de fuentes del tiempo real de la ejecución.

## 14. Fail-closed

Detener ante adaptación distinta de G01/ALTERNATIVE_A, detalle aún no aprobado; necesidad de alterar core/auth/baseline/contrato protegido;
launcher incorrecto; pérdida de Vary/no-store; nuevas dependencias o despliegue no autorizados;
colisión/escape de path; inputs modificados tras aprobación; falta de SQL FK/grants mínimos;
gate obligatorio fallido/ausente; contaminación, secretos o cleanup no demostrado.

No parchear Next/node_modules, ignorar hash, borrar FK, ampliar privilegios, reemplazar DB/browser
por mocks ni declarar todos los casos PASS por existir código. Una regresión concreta se documenta
con evidencia antes de solicitar revisión de un supuesto aprobado; no reabrir P4.5-B por conveniencia.

## 15. Rollback previsto

Antes de materializar, staging nuevo y descriptor de ownership. Ante fallo, no promoverlo; conservar
receipt y retirar solo recursos/paths del run identificado. Si falla después de materializar, marcar
output no aceptado y no sobrescribirlo en el siguiente intento. Reversión de código solo del trabajo
nuevo propio mediante diff revisado, nunca reset sobre trabajo del usuario.

En DB sintéticas descartables, preservar evidencia y retirar recursos propios; recreación autorizada
con migrate deploy para el siguiente intento. No prometer down-migrations ni rollback automático
de datos reales. No recalcular baselines para hacer pasar el rollback. Productos P3/recibos previos
quedan intactos aun si se abandona P4.6.

## 16. Readiness y pendientes P4.7

P4.6 demostraría generación/generalidad, no cierre total de P4. Readiness global continúa BLOCKED.
P4.7 deberá demostrar arranque/operación desde producto independiente sin Factory/Python,
infraestructura app+DB y persistencia/restart en ese contexto, regresión completa, cleanup,
baseline business y manual revisados, límites/seguridad y aprobación final. Que P4.6 ya ejecute
outputs para validarlos no equivale a certificar esa autonomía. P4.7 tampoco autoriza deployment
ni P5–P7 automáticamente.

**Cierre de esta preparación: READY_FOR_DESIGN_REVIEW.** G01 HUMAN_APPROVED / ALTERNATIVE_A;
contratos detallados propuestos, ejemplos en anexo y matriz actualizada. No se modificaron artefactos
aprobados. Detener para revisión humana del diseño antes de solicitar autorización de implementación.
P4.6 y P4.7 no iniciadas.
