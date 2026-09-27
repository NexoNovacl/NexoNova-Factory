# P4.5-A — Diseño de internal-requests y autorización por recurso

Revisión de diseño 0.1.0 · 2026-09-26 · **READY_WITH_LIMITATIONS — pendiente de revisión humana del diseño.**
Solo análisis, contratos de comportamiento y plan de validación. P4.5-B NO iniciada.
Este documento es el handoff propuesto para B; no autoriza ejecución ni acredita el módulo.

## 1. Estado de entrada, alcance y decisiones

Aprobación humana recibida en esta sesión: P3 PASS_WITH_LIMITATIONS/CLOSED; P4.1 y P4.2
APPROVED; P4.3 PASS_WITH_LIMITATIONS/APPROVED; P4.4-A APPROVED;
P4.4-B PASS_WITH_LIMITATIONS/APPROVED. Los receipts históricos no se actualizan para alterar
su revisión pendiente en el momento de emisión.

Entrada heredada: compatibility, database-migrations, authentication, auth-role-probes,
build-tests y cleanup PASS para el core aprobado. resource-authorization, module-crud,
generation y autonomy NOT_IMPLEMENTED; readiness global BLOCKED. No son resultados nuevos.

Objetivo B: persistencia de un recurso, CRUD lógico/ciclo de vida, ownership y autorización
horizontal/admin, concurrencia optimista e integración real con auth/DB. Una organización
por producto/instancia; no multitenancy. Solo datos sintéticos y recursos locales descartables.
Sin reasignación, adjuntos, comentarios, prioridad, SLA, email, analytics, búsqueda avanzada,
integraciones, formularios dinámicos, nuevas dependencias, deployment, generación o autonomía.

### Matriz técnica que B debe conservar

Better Auth 1.7.5; Node 22.23.2; Next 15.5.25; React/react-dom 19.2.8;
TypeScript 5.9.3; Prisma/client/adapter-pg 7.5.0; pg 8.16.3; PostgreSQL 16.15;
OpenSSL/libssl3 3.0.20 (paquete 3.0.20-1~deb12u2). Lockfile auth sin cambios.
Imagen runtime/preparación:
`nexonova-p44b-node-openssl@sha256:0d0e3b31790d5b477357d4596d0c4b97f7fe2c7a43d7501821b7de1d90f52c16`.
PostgreSQL:
`postgres@sha256:efedf3595f1d6f415c08568ba171029bf54052e754cc9f030e3f2412b21f3d67`.
No usar latest, actualizar dependencias ni resolver incompatibilidad cambiando esta matriz
sin revisión. Los digests/versiones provienen del receipt aprobado P4.4-B; no se revalidaron en A.

### D01 — RESOLVED / APPROVED

El usuario confirmó explícitamente conservar **open/closed** como literales de contratos,
API, validación, dominio, persistencia y tests. Inicial `open`; cerrar `open → closed`;
reabrir `closed → open`. OPEN/CLOSED son solo etiquetas conceptuales. No existe estado
`archived`: archivado exclusivamente `archivedAt != null`. Sin cambio/versionado de P4.2.
La discrepancia inicial y su resolución quedan registradas en P4_5_A_VALIDATION.json.

Las restantes decisiones de este documento son **propuestas para aprobar al cerrar A**,
no decisiones humanas ya concedidas: DTOs/PATCH por comando, archivo terminal invisible,
paginación keyset, CAS, FK SQL explícita y preparación aislada del módulo para B.
No se identificó otra contradicción que obligue a cambiar P4.2 o la implementación P4.4-B.

## 2. Fuentes inspeccionadas y autoridad

| Fuente | Qué fija o verifica |
|---|---|
| AGENTS.md / MIGRATION_PLAN.md | Stack, separación, revisión humana y orden de fases |
| config/business/internal-requests-pilot/{catalog,spec,environment,work-order}.json | Nueve campos, roles, estados, rutas, restricciones contractuales |
| schemas/business-module.v1.json / business-platform.v0.1.0.json | Contratos cerrados; no campos/acciones/roles añadidos silenciosamente |
| factory/business_contracts.py | POLICY, FIELDS, ROUTES y descriptor exacto |
| docs/business-platform/P4_2_CONTRACTS.md §módulos | Rutas/path de schema son destinos conceptuales, no composición física ya impuesta |
| docs/business-platform/P4_1_PROPOSAL.md §piloto/§autorización | Listado paginado, admin crea propia, member own-only, consultas con owner |
| docs/migration/P4_4_B_FINAL_REPORT.md y FINAL_RECEIPT.json | Evidencia granular y limitaciones aceptadas |
| templates/business-platform-auth/prisma/auth/schema.prisma y prisma.config.ts | User.id String/TEXT, schema app, cliente auth y migraciones separados |
| templates/business-platform-auth/src/server/auth.ts | identity(headers) devuelve id/name/role o null; consulta real de sesión; máximo 8h |
| templates/business-platform-auth/validation/runtime-grants.sql y package.json | Grants previos y dependencias fijadas |

Los flags NOT_IMPLEMENTED de los contratos P4.2 son el snapshot de planificación cerrado,
no una autorización de ejecución ni gates dinámicos. No se editan para reflejar progreso.
El nuevo receipt de B aportará resultados; un futuro contrato de generación pertenece a P4.6.

## 3. Modelo y validación de datos

Solo estos nueve campos de negocio; nada adicional persistido:

| Campo | Diseño propuesto para B | Autoridad/validación |
|---|---|---|
| id | String/TEXT, PK; UUID v4 canónico minúsculo generado con crypto.randomUUID | Servidor; opaco para cliente, no secuencia enumerable |
| title | String/TEXT NOT NULL; 1–120 puntos de código Unicode | Input explícito; sin trim/normalización silenciosa; no solo whitespace |
| description | String/TEXT NOT NULL; 0–2000 puntos de código | Texto plano, vacío válido, obligatorio en create/edit; no null |
| status | Enum InternalRequestStatus: open, closed; default open | Comando validado; no valor libre en body |
| ownerId | String/TEXT NOT NULL, FK a app.User.id | Solo identity.id; inmutable; no asumir que IDs User son UUID |
| createdAt | timestamp(3) NOT NULL | Date servidor en creación; inmutable |
| updatedAt | timestamp(3) NOT NULL | Mismo instante que createdAt inicialmente; Date servidor en cada mutación aceptada |
| archivedAt | timestamp(3) nullable | null inicialmente; Date servidor al archivar, mismo instante que updatedAt |
| version | Int/INTEGER NOT NULL, default 1; CHECK >=1 | CAS e incremento de uno; máximo 2147483647 |

Semántica Unicode: contar puntos de código, no unidades UTF-16 ni bytes; rechazar surrogate
solitario y U+0000. No truncar. No HTML rico; React escapa texto, prohibido dangerouslySetInnerHTML.
Whitespace en description se conserva; title con espacios alrededor se conserva si no está vacío
semánticamente. La decisión no cambia los límites P4.2; concretiza “caracteres”.
CHECK SQL char_length(title) BETWEEN 1 AND 120, char_length(description)<=2000 y version>=1;
“title no solo whitespace” se valida en servidor, sin prometer equivalencia de regex Unicode en SQL.
No CHECK de monotonía temporal contra createdAt: los relojes pueden ajustarse; version es la
referencia de concurrencia. Reloj runtime según P4.2, UTC ISO en DTO, precisión milisegundos.

El DTO de salida permite exactamente los nueve campos (fechas ISO UTC; archivedAt null en
recursos visibles). No incluye User.email, Account, Session, tokens ni relaciones auth. No hay
endpoint de usuarios. List y detail comparten DTO por simplicidad y datos acotados.

## 4. Ownership, roles y matriz de autorización

Crear: `ownerId = identity(headers).id`, incluido admin creando para sí mismo.
Estrategia exacta: **rechazar** campos no permitidos, nunca ignorarlos. ownerId, userId, role,
owner, createdAt, updatedAt, archivedAt, status, id o equivalentes no están en DTO de entrada.
No spread del body hacia Prisma. No navegación por filtros owner suministrados por cliente.
Rechazar query/header de control inventada no es necesario para seguridad: headers role/userId/
ownerId se ignoran como autoridad; query desconocida sí se rechaza por contrato HTTP cerrado.

| Actor | Create | List | Detail | Edit | Close | Reopen | Archive |
|---|---|---|---|---|---|---|---|
| anonymous o sesión inválida/expirada/revocada | 401 | 401 | 401 | 401 | 401 | 401 | 401 |
| member owner, recurso activo | Propia | Propias activas | 200 | Permitido | Si open | Si closed | Permitido |
| member non-owner | Solo propia nueva | Nunca ajenas | 404 | 404 | 404 | 404 | 404 |
| admin | Propia | Todas activas del producto | 200 | Permitido | Si open | Si closed | Permitido |
| rol desconocido | Denegado | Denegado | Denegado | Denegado | Denegado | Denegado | Denegado |

identity actual devuelve null ante rol desconocido: el módulo responde 401 (página → login),
sin modificar el guard. Servicio además valida enum del actor recibido y falla cerrado; solo
código servidor puede construir el actor. No conceder admin por presencia de una cookie o header.
Admin no puede cambiar owner/rol ni superar reglas de estado, versión o archivado.

**Predicado de visibilidad único:** archivedAt IS NULL AND (admin OR ownerId=actor.id).
Se incluye en cada SELECT y UPDATE; nunca obtener una fila sin scope y filtrar después en React.
No tenantId ni discriminador de organización: el límite organizacional es DB/instancia/producto.

## 5. Estados y política de archivado

| Comando | Precondición | Efecto |
|---|---|---|
| create | Sesión/rol permitido, DTO válido | open, owner de sesión, archivedAt=null, version=1 |
| edit | Activa; open o closed; versión correcta | title/description reemplazados; conserva status/owner |
| close | Activa y open; versión correcta | status=closed |
| reopen | Activa y closed; versión correcta | status=open |
| archive | Activa; open o closed; versión correcta | archivedAt=ahora, conserva status |

Toda mutación aceptada incrementa version una vez y cambia updatedAt. Editar texto idéntico
cuenta como mutación aceptada; no se devuelve éxito sin aplicar el control de versión.
Cerrar closed o reabrir open → 409 OPERATION_CONFLICT, sin cambios ni incremento.

**Archivo terminal para esta API:** todas las filas archivadas se excluyen de list/detail y de
mutaciones, para owner y admin. No unarchive, lectura de archivo, borrado o exportación en MVP.
Después de archive se devuelve 204 sin body; la UI vuelve al listado. Repetición, incluso con
versión nueva → 404 RESOURCE_NOT_FOUND. La fila sigue en PostgreSQL, conserva FK y status;
las assertions de retención se hacen por fixture técnica, no por una ruta privilegiada añadida.

## 6. HTTP, rutas y errores

Se conservan únicamente las rutas y métodos P4.2:

| Ruta / método | Entrada exacta | Éxito |
|---|---|---|
| GET /requests | limit y cursor opcionales como API | Página servidor: listado/crear |
| GET /requests/[id] | ID canónico, sin query | Página servidor: detalle/formulario/acciones |
| GET /api/requests | limit/cursor opcionales | 200 {items, nextCursor} |
| POST /api/requests | {title, description} | 201 {item}; Location: /api/requests/{id} |
| GET /api/requests/[id] | ID canónico, sin query | 200 {item} |
| PATCH /api/requests/[id] | Unión de comandos descrita debajo | 200 {item} o archive 204 |

PATCH edit: `{action:"edit", expectedVersion:3, title:"...", description:"..."}`.
PATCH close/reopen/archive: `{action:"close"|"reopen"|"archive", expectedVersion:3}`.
Son campos de transporte, no nuevas columnas ni nuevos estados del modelo.
No aceptar actualización genérica de status/archivedAt. No PUT/DELETE ni rutas de acciones extra;
método no soportado → 405 con Allow contractual. No method override, ni mutaciones por GET.

Errores API: JSON fijo `{error: CODE}` sin datos del recurso, dueño, versión actual ni explicación
SQL. 400 INPUT_REJECTED (forma/query/acción/versión/tipos/límites); 401 UNAUTHORIZED;
403 ORIGIN_REJECTED; 404 RESOURCE_NOT_FOUND; 409 OPERATION_CONFLICT;
413 BODY_TOO_LARGE; 415 UNSUPPORTED_MEDIA_TYPE; 503 SERVICE_UNAVAILABLE.
No 403 de ownership: ajeno e inexistente comparten 404, body, headers y estructura.

Orden: método/ruta → identidad válida → protección origen para mutación → límite/content-type/
DTO/query → ID → consulta autorizada/CAS. IDs malformados tras autenticación → mismo 404,
sin DB lookup. Errores de forma no dependen de la existencia del ID. Anónimo recibe 401 sin
consulta empresarial aunque mande un ID propio, ajeno o inexistente.

POST/PATCH: application/json con charset opcional utf-8, lectura acotada a 16 KiB reales (no
confiar en Content-Length); JSON objeto sin claves desconocidas, sin coerción de tipos, número
expectedVersion entero positivo <=2147483647. Usar JSON.parse estándar: para claves repetidas prevalece la última; no afirmar detección de
duplicados. Validar el objeto resultante con allowlist y mapeo explícitos: ningún campo protegido
se incorpora, repetido o no. Probar duplicados de campos protegidos y estructuras __proto__/
constructor como entradas desconocidas. No añadir dependencia para parsear JSON.

CSRF: Origin debe coincidir exactamente con origen validado por authEnvironment; rechazar
Origin ausente/null/ajeno y Sec-Fetch-Site cross-site en mutaciones. GET cross-site →403 genérico.
No confiar en Forwarded/X-Forwarded-* para origen/actor; no CORS permisivo. Sin redirects
controlados por usuario. Reutilizar configuración pública/guard existentes, no modificar Better Auth.

Todas las respuestas privadas, errores y páginas: Cache-Control:no-store, Vary:Cookie;
no cache global de identity, no force-cache ni revalidate de recursos. Páginas sin sesión redirigen
solo a /login; recurso no visible usa notFound con mensaje genérico. DB caída muestra indisponibilidad,
no página vacía que parezca éxito. Route Handlers verifican todo aunque la UI o RSC ya lo haya hecho.

## 7. IDOR y enumeración

Para member, ID ajeno, inexistente y archivado responden exactamente 404 RESOURCE_NOT_FOUND
a igual operación/entrada válida. El diagnóstico tras un CAS fallido también lleva owner+activo:
una versión “correcta” o “incorrecta” de una fila ajena nunca produce 409 ni revela su presencia.
UUID opaco es defensa adicional, no autorización. Probar IDs secuenciales arbitrarios, UUID de
otro usuario, encoded delimiters, mayúsculas y payloads SQL-like; no interpolar identificadores.

No contadores globales, owner/email en mensajes, metadata de existencia ni currentVersion en
conflictos. Body validado incorrecto tiene error uniforme independiente del ID. No se promete
igualdad temporal: lookup indexado vs rechazo sintáctico, cachés DB y distribución de datos
pueden variar. La política no oculta a un usuario que su propio recurso fue archivado tras verlo.

## 8. Concurrencia optimista y errores de carrera

Create no recibe versión; list/detail son lecturas. **Todos los PATCH** requieren expectedVersion.
Un UPDATE único lleva id + scope owner/admin + archivedAt IS NULL + version=expectedVersion +
precondición de estado (close/open, reopen/closed) + version<2147483647. Asignaciones explícitas,
`version = version + 1`, updatedAt del servidor; archive escribe también archivedAt. No UPDATE
por ID después de un SELECT de permisos sin repetir esas condiciones.

Propuesta Prisma: transacción interactiva ReadCommitted; updateMany con where completo y
count. Si count=1, leer DTO dentro de la misma transacción (la actualización conserva el lock
hasta commit). Archive retorna sin lectura/body. Si count=0, SELECT de solo id con el mismo
scope de visibilidad, sin versión/estado: ausencia →404; presencia →409 genérico. No consultar
existencia global. El fallo diagnóstico puede ver un archive concurrente y devolver 404;
es comportamiento aceptado de visibilidad, no una garantía de snapshot del error.

No se incrementa en fracaso ni se reintenta automáticamente un conflicto del usuario con versión
nueva. Error DB/timeout/permiso → rollback y 503 saneado. No reintentar una escritura después de
respuesta perdida: puede haber commit aunque el cliente no haya recibido éxito; mostrar estado
incierto y pedir recarga. No idempotency key en este MVP. En overflow de versión →409, no wrap.

Dos requests con misma versión y recurso activo: máximo un commit; el otro 409 mientras la fila
siga visible, o 404 si el ganador la archivó. Carrera edit/close/reopen/archive preserva predicados
tras espera de lock; ninguna operación obsoleta resucita un archivo. DB conserva una única fila.
Comprobar también actor member no autorizado compitiendo con owner/admin: cero efecto ajeno.

Base técnica: PostgreSQL 16 reevalúa el WHERE de UPDATE tras una actualización concurrente
confirmada bajo Read Committed. Es la propiedad usada para el CAS, no una prueba ya ejecutada
([documentación PostgreSQL](https://www.postgresql.org/docs/16/transaction-iso.html)).
La API concreta de transacciones/updateMany se contrastará con Prisma 7.5.0 instalado en B;
la documentación de [transacciones Prisma 7](https://docs.prisma.io/docs/orm/v7/prisma-client/queries/transactions)
orienta el diseño, sin cambiar la versión fijada.

## 9. Arquitectura servidor y consumidores

Flujo: UI/RSC → HTTP o servicio servidor → actor de identity → autorización → validación de
comando → repositorio Prisma → PostgreSQL. Runtime Node. Sin middleware como barrera ni Server
Actions nuevas. Los RSC llaman servicios con actor obtenido en servidor, no al API con cookies reenviadas.

- HTTP: parsing/size/método/origen, status/DTO y headers; no reglas SQL dispersas.
- Autenticación: importar identity y authEnvironment aprobados; null deniega, excepción no se
  transforma en anónimo permitido. No copiar ni debilitar política de ocho horas.
- Autorización: función cerrada actor→scope reutilizada en read/list/update y diagnóstico CAS;
  deny-by-default. No aceptar un actor por body ni desde un componente cliente.
- Servicios: create/list/detail/edit/close/reopen/archive; reglas de estado, ownership, versión.
- Repositorio: Prisma singleton empresarial con @prisma/adapter-pg y misma URL runtime;
  transacciones y predicados. Sin SQL dinámico inseguro; parámetros para valores.
- Validación: funciones puras de DTO/paginación/IDs; sin acceso DB en cliente como autoridad.
- Presentación: DTO mínimo plano y componentes CSS Modules. Servidor nunca serializa PrismaClient,
  objetos Session completos, errores internos ni conexiones.

El cliente auth actual es privado dentro de createAuth. Proponer cliente empresarial separado
para no cambiar ese archivo; reutilizado por proceso y desconectado al finalizar probes CLI.
Dos pools por proceso (auth y módulo), límites explícitos para piloto; carga/conexiones en C40.
No prometer una frontera de seguridad entre esos pools: ambos usan bpruntime.

## 10. Paginación acotada

Keyset: `limit` default 20, rango entero 1–100; decimal ASCII canónico, sin duplicados,
negativos, floats ni coerción. `cursor` opcional base64url canónico <=256 caracteres, JSON exacto
{createdAt,id}; fecha UTC ISO canónica a milisegundos, id UUID v4 minúsculo. Cursor vacío/roto,
campos desconocidos, límites inválidos o query adicional →400. No page/offset, filtros owner,
status, archived, search ni sort personalizados.

Orden estable ascending (createdAt, id). Cursor agrega condición lexicográfica “mayor que”; no
busca por ID la fila del cursor. Siempre aplicar scope antes de paginar; traer limit+1, devolver
máximo limit y nextCursor de último elemento entregado solo si existe siguiente. nextCursor null
al final; lista vacía 200. No total/count global. Un cursor fabricado puede elegir un límite de
recorrido, no eludir owner ni revelar filas ajenas; no es token de permiso ni necesita firma.

Orden determinista en dataset estable incluso con timestamps iguales. Entre páginas no hay
snapshot: nuevas filas, archivo concurrente o reloj atrasado pueden variar la vista. La UI permite
recargar desde inicio; no prometer recorrido consistente de una colección mutable. Índices abajo.

## 11. Prisma, FK y migraciones sin cambiar User

**Diseño propuesto para aprobación: FK gestionada explícitamente en SQL, ownerId escalar en
Prisma; sin relation field inverso en User.** Esto preserva exactamente User y el schema auth
aprobados. No simular integridad solo en aplicación: la FK real debe existir y fallar en PostgreSQL.
No añadir un User reducido/stub que pueda provocar drops de columnas auth.

La FK `InternalRequest_ownerId_fkey` referencia app.User(id), tipos TEXT coincidentes,
ON DELETE RESTRICT, ON UPDATE RESTRICT, validada y no diferible. No CASCADE/SET NULL ni
reasignación. Borrado/cambio de ID de User con requests (incluidas archivadas) falla; la aplicación
no permite eliminar usuarios y runtime no tiene ese grant. Las FK auth ya existentes User→Session/
Account permanecen intactas. Restrict se comprueba con fixture administrativa sin ampliar runtime.
Si se habilitara borrado de cuentas posteriormente necesitaría nuevo diseño/revisión.

Proponer índice ownerId (también útil para la FK), índice (ownerId,archivedAt,createdAt,id) para
member y (archivedAt,createdAt,id) para admin. PK id ya permite CAS unitario; no índice version
extra. Enum propio y CHECK de longitudes/version. No triggers para ownership ni RLS en esta fase:
la autorización por fila está en servicios/predicados, mientras grants limitan columnas/operaciones.
Un runtime comprometido podría afectar otras filas mediante SQL: límite explícito del piloto.

**Composición de validación prevista:** copiar core auth aprobado a workspace efímero, superponer
solo archivos del módulo; generar allí `prisma/business/schema.prisma` desde bloques auth byte-
idénticos + `prisma/modules/internal-requests.prisma`, cambiando únicamente bloque generator/output
para cliente empresarial `src/generated/requests`. Conservar el cliente auth y su generación original.
No emitir nuevas tablas User ni cambiar nombres/tipos existentes. El archivo compuesto es artefacto
local verificable de test, no un nuevo baseline ni generador business de fábrica.

Nuevo config `prisma.requests.config.ts` apunta al schema compuesto y a un **único historial
combinado** `prisma/business/migrations`: copia exacta de `00000000000000_auth_initial` y nueva
`00000000000001_internal_requests`. No ejecutar dos gestores distintos sobre el mismo historial.
Para DB vacía: provisionar app/migrator, deploy historial combinado, grants auth+módulo,
bootstrap offline autorizado como fixture y app. Para DB con auth aplicada: mismo checksum/nombre
inicial y solo migración adicional. Probar ambos caminos y segunda aplicación inalterada.

Migration SQL revisado agrega enum, tabla, constraints/índices y FK; ninguna alteración destructiva
ni reescritura de auth. Se aplica con `prisma migrate deploy --config prisma.requests.config.ts`
(en B verificar CLI 7.5.0); sin db push/reset ni auto-migrate al arrancar. TechnicalSmoke permanece
exclusivamente en fixture histórica. Inventario app esperado: las cuatro tablas auth, InternalRequest
y _prisma_migrations; ningún otro modelo empresarial.

**Coste deliberado de preservar User:** Prisma schema no describe esa FK relacional, aunque la
DB sí la impone. El SQL de migración y un contrato de constraints versionado del módulo son la
fuente de verdad conjunta; introspección podría proponer relation/inversa y migrate diff podría
proponer quitar la FK. Nunca aplicar ese diff automáticamente ni afirmar “drift cero”. Se debe
comparar pg_constraint/pg_indexes con inventario exacto esperado y revisar diferencias Prisma;
solo la omisión documentada de esta FK y CHECKs manuales es conocida, cualquier diferencia
adicional bloquea. No ejecutar db pull sobre auth. No utilizar connect/include owner en Prisma.

Esta es una decisión de implementación propuesta, no una incompatibilidad que requiera cambiar
P4.4-B: agregar una FK en la tabla nueva no añade campo/relación a User ni modifica Better Auth.
Si B demuestra que esta composición no funciona con 7.5.0, detener y revisar; no agregar inversa
a User, ampliar privilegios, eliminar FK o introducir preview flags como arreglo automático.
SQL revisable para constraints y acciones referenciales se fundamenta en
[PostgreSQL 16 constraints](https://www.postgresql.org/docs/16/ddl-constraints.html).
La [documentación Prisma de migraciones personalizadas](https://docs.prisma.io/docs/orm/prisma-migrate/workflows/unsupported-database-features)
permite completar SQL fuera del schema; no se presenta la FK como una función no soportada de
Prisma: se omite deliberadamente la navegación ORM para mantener User intacto.

## 12. Grants mínimos

Migrator: ownership/DDL en app conforme a P4.4-B, incluyendo crear FK al User que ya posee;
no superuser ni CREATE global/DB por conveniencia. Runtime conserva grants auth aprobados.
Sobre InternalRequest proponer solo:

- SELECT (nueve columnas).
- INSERT (id,title,description,status,ownerId,createdAt,updatedAt,archivedAt,version), para create
  explícito; defaults no se usan como defensa de ownership.
- UPDATE (title,description,status,updatedAt,archivedAt,version), mediante grants de columnas;
  **sin UPDATE id/ownerId/createdAt**.
- Sin DELETE, TRUNCATE, REFERENCES, TRIGGER, CREATE ni acceso al historial; sin ALL ni default
  privileges sobre tablas futuras. Sin secuencias (UUID generado en servidor).

Bootstrap queda con sus permisos exclusivamente auth; ningún grant en InternalRequest ni
necesidad de esa tabla para inicializar auth. Probar denegación real con bpbootstrap tanto al leer
como al escribir el módulo. Las fixtures administrativas no se distribuyen como panel/endpoint.
Grants no implementan ownership por fila: es responsabilidad comprobada del servicio.

## 13. UI mínima

/requests: título, listado acotado con status/version, botón siguiente si cursor, volver a inicio,
formulario title/description y crear. Mensaje lista vacía que no revela conteos globales. Sin selector
owner/rol/estado inicial. Admin ve todas las activas, sin UI de usuarios ni reasignación.

/requests/[id]: texto plano, estado y versión; editar ambos textos, cerrar si open, reabrir si closed,
archivar con confirmación accesible. Los botones se deshabilitan durante envío para UX, nunca como
control de autorización. Mantener expectedVersion leído. Ante 409 conservar borrador local,
informar “La solicitud cambió o la acción ya no está disponible; recarga para revisar”, sin auto-retry
ni merge. Ante 404 mostrar recurso no disponible; ante 401 login; 503 permitir recarga y advertir
posible estado incierto de escritura. No guardar borradores/secretos en localStorage en este MVP.

Labels explícitos, foco/teclado, mensajes role=status/alert apropiados, confirmación archive con
cancelación y retorno de foco. Probar desktop/mobile, navegación directa/refresh y API directa.
Sin dashboard, gráficos, diseño visual complejo, loading global de todos los registros ni búsqueda.

## 14. Threat model específico

Actores: visitante, member A malicioso, member B víctima, admin legítimo, cliente con versión
obsoleta, operador con configuración errónea. Host/daemon/rol migrator son confiables para el
piloto; no hay datos reales. Activos: contenido/owner/estado de requests, integridad de versiones,
credenciales y aislamiento por producto. La siguiente tabla enlaza controles con pruebas de §15.

| Amenaza | Control previsto | Prueba | Límite |
|---|---|---|---|
| IDOR/lectura horizontal | Scope DB owner+activo en list/detail | C08,C09,C17,C22 | UUID no es permiso; timing no formal |
| Escritura horizontal | WHERE owner+id+version+activo en todas mutaciones | C18,C19,C24 | Runtime SQL comprometido fuera de modelo |
| Escalada vertical/role spoofing | identity autoritativa; enum cerrado; rol desconocido denegado | C07,C20,C21 | Sin edición de roles en producto |
| Owner spoofing | Create con identity.id, DTO allowlist; grants sin UPDATE ownerId | C05,C07,C18 | INSERT técnico no restringe owner por fila |
| Mass assignment | DTO por comando, campos desconocidos rechazados, mapeo explícito | C07,C27 | JSON parser no se usa como autoridad |
| Lost update/stale write | CAS atómico, incremento único, no retry con nueva versión | C13,C23,C24 | Commit con respuesta perdida requiere recarga |
| Enumeración | 404 uniforme, sin diagnóstico global ni metadata | C17,C19,C22 | No indistinguibilidad temporal formal |
| Acceso archivado | archivedAt null en todo scope; archive terminal | C12,C14,C19,C24 | Retención ocupa almacenamiento; sin recuperación UI |
| IDs malformados/inyección | UUID canónico y valores parametrizados | C22,C27 | Rechazo sintáctico puede ser más rápido |
| Abuso paginación | limit<=100, cursor<=256, DTO cerrado, índices | C25,C26,C40 | No protección distribuida ni rate limit empresarial nuevo |
| Transiciones inválidas | Estado en WHERE; 409 genérico sin mutación | C10,C11,C13 | Admin sujeto a la misma máquina |
| Carreras | Predicados reevaluados; transacción y rollback | C23,C24,C30 | Sin serialización global de sesiones/roles |
| Sesión inválida/expirada/revocada | identity en cada entrada, sin caché | C20,C21,C35 | Request ya autorizado puede terminar si revocación ocurre después del guard |
| Bypass API de UI | Mismas reglas servidor, sin confiar en botones/middleware | C18,C19,C28,C34 | XSS del origen es riesgo separado |
| CSRF/forwards | Origin exacto, cross-site denegado, URL configuración | C28 | TLS/proxy productivos no cubiertos |
| XSS/texto almacenado | Texto plano, React escaping, sin HTML arbitrario | C27,C34,C36 | No auditoría formal de todos los paquetes |
| DB overprivilege | Grants por operación/columna, sin ALL/DDL/DELETE | C03,C04 | No RLS; actor app no es rol PostgreSQL individual |
| Secret leakage | DTO seguro, logs por código, scan valores sintéticos/HTML/receipts | C36 | Heurístico secundario no exhaustivo |
| DB unavailable/permisos retirados | 503, rollback, no éxito vacío ni fall-open | C30 | Resultados inciertos de red no se ocultan |
| Contaminación cross-product/DB | URL/secret/prefijo/red/volumen independientes | C31 | Host/daemon confiables |
| Eliminación de User/orfandad | FK RESTRICT real, bootstrap sin grants de módulo | C04,C06 | Administración offline necesita política futura |
| Drift de FK manual | Inventario exacto de constraints y revisión del diff | C01,C02,C32 | FK fuera del modelo de relaciones ORM requiere disciplina |

## 15. Plan granular de validación futura P4.5-B

**Todos los casos C01–C40 están NOT_EXECUTED en A.** La máquina de evidencia en
P4_5_A_VALIDATION.json replica IDs, setup, actor, operación, esperado, evidencia y gates.
No mezclar estados de planes con resultados. Un caso PASS requiere todos sus subcasos requeridos;
registrar FAIL/BLOCKED/NOT_EXECUTED individualmente cuando corresponda.

Fixture común F: imagen OpenSSL y PostgreSQL por digests de P4.4-B; copia verificada de core auth
más overlay; base/red/volumen únicos; migrator/runtime/bootstrap separados; un admin y dos
members A/B creados por bootstrap/fixture offline autorizados con credenciales aleatorias privadas.
RA/RB activos pertenecen respectivamente a A/B, RX archivado, ID0 válido inexistente. Sesiones
reales Better Auth, cookies solo en memoria. Sin credenciales por argv o receipts.

Gates abreviados: DM=database-migrations, RA=resource-authorization, MC=module-crud,
AT=authentication, CP=compatibility, BT=build-tests, CL=cleanup. “Operador” siempre sobre F,
no producción. DB/browser reales cuando se especifican; unitarios no sustituyen integración.

| ID / objetivo | Setup | Actor / operación | Esperado | Evidencia requerida | Gates |
|---|---|---|---|---|---|
| C01 — Migración y coexistencia | DB vacía, app provisionado; historial combinado | migrator: migrate deploy; inventario tablas/columnas/enum/constraints/índices | Auth + InternalRequest + historial, nueve columnas nuevas, FK/CHECK/índices exactos; sin TechnicalSmoke ni drops auth | SQL revisado + checksum; salida CLI; pg_catalog saneado | DM, CP |
| C02 — Upgrade/reaplicación estable | Una DB vacía y otra con auth+usuarios/sesiones previos | migrator: Aplicar combinado a ambas y reaplicar | Una migración adicional; checksums auth y datos/sesiones iguales; segunda aplicación cero cambios | Historial antes/después y comparación en memoria; versiones | DM, CP |
| C03 — Privilegio mínimo runtime | F con grants por columna | bpruntime: SELECT/INSERT/PATCH positivos; DDL, DELETE, TRUNCATE, UPDATE ownerId/id/createdAt e historial negativos | Operaciones permitidas funcionan; negativas 42501 sin efectos | SQL real por conexión runtime, privilegios efectivos; snapshots | DM, RA |
| C04 — Bootstrap/FK separación | F con request incluso archivado y usuario dueño | bpbootstrap y fixture técnica: Intentar acceso módulo; insertar owner inexistente; borrar/cambiar ID User referenciado | Bootstrap 42501; FK 23503 y rollback; sin huérfanos ni ampliación auth | pg_constraint y fallos PostgreSQL reales; comparar datos | DM, RA |
| C05 — Creación y defaults | F, sesión A y admin | member A; admin: POST title/description válidos, leer tras commit | 201; UUID distinto, owner sesión, open, version1, archivo null, fechas servidor; admin crea propia | HTTP saneado + SELECT DB; DTO sin auth | MC, RA |
| C06 — Rollback create y FK | F; fixture fuerza dueño inexistente solo desde integración técnica | repositorio técnico: INSERT inválido y repetir conteo | FK real bloquea toda fila, sin escritura parcial; no cambia User | Error FK saneado y snapshot cero efectos | DM, MC |
| C07 — Spoofing y mass assignment | F; snapshot de todos los owners/roles/recursos | A; admin: Create/PATCH con ownerId,userId,role,status,archivedAt,id,createdAt,version,objetos anidados; headers falsos | Campos body desconocidos 400; headers no confieren actor; estado entero intacto | Requests/resultados por variante y comparación DB sin secretos | RA, MC |
| C08 — Listado owner | F RA/RB/RX; varios elementos | A; B: GET list y recorrer todas las páginas | Solo propias activas; cero RB para A; cero archived; sin count global | IDs esperados vs DTO de cada página y DB fixture | RA, MC |
| C09 — Listado y detail admin | F con owners distintos | admin: GET list y detail RA/RB | Todas las activas, nunca RX; ownership original intacto | HTTP/API + assertions browser y DB | RA, MC |
| C10 — Edit/close propios | F RA open y luego closed | A: PATCH edit; close con versión vigente; edit closed | 200; texto/estado esperado; cada éxito +1; owner/id/createdAt inmutables | DTO/DB antes-después de cada operación | MC, RA |
| C11 — Reopen/transiciones inválidas | F RA open/closed | A; admin: close closed, reopen open, reopen closed con versiones actuales | Inválidas 409 sin cambios; válida200 closed→open +1 | HTTP y snapshot de todas las columnas | MC |
| C12 — Archive desde ambos estados | F dos recursos propios open/closed | A; admin: PATCH archive con expectedVersion actual | 204; fila retenida, status conservado, archivedAt=updatedAt servidor y version+1 | API + SELECT de fixture técnica, no endpoint nuevo | MC, RA |
| C13 — Versión inválida/obsoleta/overflow | F recurso visible en versión3/4 y fixture maxInt | A; admin: Todos los PATCH con versión faltante/no entero/cadena/obsoleta/maxInt | Forma400; obsoleta/overflow409; cero cambios; no wrap ni retry implícito | Variantes por acción, DB snapshots | MC |
| C14 — Archivo terminal | F RX propio/ajeno | A; B; admin: List/detail/edit/close/reopen/archive de RX | No aparece; detail/mutaciones404 uniforme, incluso admin y repetición; DB conserva fila | API/browser y snapshot DB postintentos | RA, MC |
| C15 — Detail/edición owner | F RA y sesión válida | A: GET detail y PATCH edit directamente sin UI | 200, versión aplicada, solo DTO nueve campos; no Session/User joins expuestos | API, DB y HTML mínimo | RA, MC |
| C16 — Admin sobre ajeno | F RB activo, sesión admin | admin: Detail/edit/close/reopen/archive RB en secuencia versionada | Permitido con mismas reglas/versiones; ownerId B nunca cambia | HTTP por operación + DB state graph | RA, MC |
| C17 — Lectura horizontal | F RB y ID0, mismos inputs | A: GET detail RB y ID0; listar tras manipular cursor/header | 404 idéntico para detail, lista sigue own-only | Comparación status/body/headers estáticos; no metadata de owner | RA |
| C18 — Edición horizontal | F RB, versiones actual/obsoleta | A: PATCH edit con ambas versiones y rol/owner de header falsos | 404 en ambas, jamás409; RB y User intactos | HTTP y comparación DB completa | RA |
| C19 — Acciones horizontales | F RB open/closed/archivado; ID0 | A: PATCH close/reopen/archive en cada fixture con versiones varias | 404 uniforme ajeno/inexistente/archivo; ninguna transición ni incremento | Matriz request-respuesta y snapshots DB | RA, MC |
| C20 — Anónimo y sesiones inválidas | F, sin cookie/forjada/expirada/revocada | visitante: Todas las APIs GET/POST/PATCH y páginas directas | API401; páginas login; cero lectura/escritura empresarial; no fallback permitido | HTTP, navegador y DB; sesiones reales expiradas/revocadas por fixture | AT, RA |
| C21 — Rol desconocido | F + enum real; prueba pura de actor inválido | actor desconocido de fixture: Intentar persistir rol inválido y llamar guard/servicios con actor fuera de enum | PG rechaza; guard/servicio deny-default. No debilitar enum para fabricar integración | Error real DB + prueba unitaria marcada como tal; auth aprobado preservado | AT, RA |
| C22 — ID/404 uniforme | F RA/RB/RX/ID0 y IDs inválidos | A; admin: Detail y cada PATCH con sintaxis válida o IDs malformados/encoded | 404 para no visibles; malformado404 tras auth; sin SQL/metadata; no timing formal | Comparación body/status/headers por acción; muestras de timing descriptivas | RA |
| C23 — Carrera real misma versión | F RA versión n; dos conexiones/procesos con barrera | A + A; A + admin: Dos edit simultáneos con expectedVersion n y payload distinto | Exactamente un200 y un409; version n+1; un payload ganador íntegro, no mezcla | Tiempos/barrera/IDs de workers; resultados HTTP + DB final; repetir varios ensayos | RA, MC |
| C24 — Carreras de ciclo de vida | F nuevo por ensayo; barrera real | A/admin; B no-owner: edit vs close; close vs archive; reopen vs archive; mutación owner vs B | Máximo un éxito por versión; perdedor409 si visible o404 tras archivo; nunca resurrección; B sin efecto | Casos concurrentes por combinación, snapshots/versión final | RA, MC |
| C25 — Paginación y orden | F >100 registros sintéticos; empates createdAt y dos owners | A; admin: limit default/1/100, recorrer cursores, empty/final | Orden (createdAt,id) asc estable en dataset quieto; sin omisiones/duplicados; nextCursor correcto; owner scope | Lista esperada DB vs todas las páginas; no secretos en cursor | MC, RA |
| C26 — Abuso/manipulación cursor | F, cursor ajeno/fabricado y límites extremos | A: Cursor alterado, query desconocida/duplicada, tamaño>256, limit0/101/float; paginar con archive concurrente | Inválidos400; cursor bien formado nunca elimina scope; respuestas acotadas; cambios entre páginas documentados | HTTP por variante y controles de visibilidad/tamaño | MC, RA |
| C27 — Validación/XSS/entrada | F | A: Límites Unicode título1/120/121, description0/2000/2001; whitespace, null, surrogate, NUL, body>16KiB, HTML y SQL-like | Válidos conservan texto; inválidos400/413/415; HTML escapado; sin inyección/overposting | Unitarios + HTTP/DB + DOM real para texto hostil | MC, RA, BT |
| C28 — CSRF/métodos/cache | F con cookies | A; atacante cross-site: POST/PATCH Origin ausente/null/ajeno; forwards; GET mutante; DELETE/PUT; private GET | 403 origen;405 métodos; GET no muta; no-store y Vary Cookie en éxito/error/páginas | HTTP headers sanitizados y DB snapshots; browser cross-site cuando corresponda | RA, BT |
| C29 — Persistencia/restart | F recursos open/closed/archivados y sesiones | A; admin: Reiniciar app y DB separadamente; repetir lectura permitida/denegada | Datos/versiones/owner persisten; archivo sigue invisible; sesión válida sigue política auth | Inventario persistente y HTTP antes/después de ambos reinicios | MC, DM, AT |
| C30 — DB/permisos no disponibles | F | A; runtime: Detener DB o retirar grants SELECT/UPDATE/INSERT durante operaciones | 503 saneado y fail-closed; no escrituras parciales; restaurar confirma integridad; escritura de resultado incierto documentada | Fallos reales y snapshots después de recuperar; logs escaneados | MC, RA, DM |
| C31 — Aislamiento productos | Dos F con DB/red/volumen/secreto/prefijo distintos | A de producto1: Cookie/ID/cursor de1 contra2; control válido en cada producto | Sesión cruzada rechazada; con sesión2 ID1 inexistente404; ninguna fila contaminada | SQL por ambas DB, HTTP y restricciones Docker; no compartir fixtures de datos | RA, DM |
| C32 — Reproducibilidad schema/FK manual | Copias nuevas del core+overlay | migrator/validador: Componer dos veces, generate/validate, inspeccionar diff/inventario | Auth model/migración idénticos; SQL personalizado exacto; solo FK/CHECKs documentados fuera de representación; ningún drop aplicado | Hashes por input/output, diff revisado y pg_catalog independiente | DM, CP |
| C33 — Tipos/tests/build/start | Workspace compuesto F | validador: npm ci fijo, auth y business generate, typecheck, unitarios, build y arranque | Sin errores; mismas dependencias; rutas disponibles; imports server no terminan en bundle cliente | Comandos/exit/salidas/versiones y hashes, sin claims de navegador por unitarios | CP, BT |
| C34 — Flujo navegador empresarial | F en desktop/mobile | A; B; admin: Teclado create/list/detail/edit/close/reopen/archive; tabs con conflicto; ID ajeno directo | Flujo completo; foco/errores; borrador conservado409; B denegado; admin permitido; archivo invisible | Playwright real, assertions DOM/API; sin HAR/token ni screenshots con secretos | BT, MC, RA |
| C35 — Regresión auth integrada | Core+overlay y baseline auth conservado | A; admin; visitante: Login genérico, signup cerrado, logout/replay, borde8h/no refresh, cookies HTTP/HTTPS, probes, bootstrap no cambios | Controles P4.4-B permanecen; nueva FK no rompe flujos permitidos; no ampliar grants User/Account | Subchecks B relevantes reejecutados contra nueva composición con hashes; resto recuperado identificado | AT, CP, RA |
| C36 — Secretos/DTO/logs/egress | F, valores sintéticos conocidos solo en memoria | validador: Escanear DB/app/browser/SSR/receipts finales y bundles; observar browser y redes runtime | Cero valores secretos conocidos persistidos; DTO mínimo; telemetry desactivada; sin egress exitoso | Scan antes/después serialización; métricas browser; inventario red; límites de heurístico explícitos | RA, BT |
| C37 — Preservación histórica | Manifiestos enumerados en §17, snapshots entrada | validador: Comparar hashes/sets y tests P3/P4.2; productos/prototipo; P4.3/P4.4 receipts | Sin diferencias no autorizadas ni baselines recalculados; excepción next-env histórica separada | Receipt hashes y comandos reales; cambios autorizados nuevos aislados | CP, BT |
| C38 — Cleanup normal/fallo/timeout | F y centinela de otro owner | validador: Éxito, fallo inducido, timeout; limpieza por label/ID | Ningún recurso propio residual ni secreto temporal; centinela intacto y luego cleanup por creador | Inventarios antes/después contenedores/redes/volúmenes/procesos/paths; receipts incluso fallo | CL |
| C39 — Gates/evidencia fail-closed | Copias de receipts saneados | validador: Quitar prueba/hash, alterar fuente, inyectar FAIL/BLOCKED/NOT_EXECUTED | Ningún gate obligatorio pasa; no heredar PASS agregado; reporte conserva causas | Pruebas de consumidor de evidencia y matriz de casos completa | CP, BT, CL |
| C40 — Consultas y recursos acotados | F dataset paginado mayor; pools auth+business | validador: Inspeccionar índices, planes de list/CAS y conexiones; repetir requests acotadas | Scope en SQL y límite real; índices disponibles; no crecimiento de pools por request; sin hard SLA ficticio | EXPLAIN en fixture, conteo conexiones/controles Docker; límites y medición declarados | CP, MC |

## 16. Gates, resultados y aceptación futura

Cada gate usa todos los casos etiquetados con su abreviatura en §15; el receipt JSON contiene
la expansión exacta de IDs. Ningún gate se deriva del número de checks, una carpeta creada o un
PASS previo. Subcasos negativos deben afirmar código esperado **y ausencia de efectos**; un exit
no cero no basta. Conservar fallos/resoluciones y separar setup de validación.

- **resource-authorization → PASS** solo tras todos los RA: owner desde sesión, list/detail/PATCH
  scoped, admin positivo, member A/B horizontales, archivo, 404 uniforme, auth inválida/rol extraño,
  carreras, restricciones DB y scans. Alcance entonces: InternalRequest y sus siete operaciones,
  una organización/producto; no autorización universal para futuros módulos.
- **module-crud → PASS** solo tras todos los MC: siete operaciones, estados/archivo, persistencia,
  validación, CAS/carreras, límites, UI real y errores fail-closed, más migraciones DM válidas.
- Mantener/revalidar CP, DM, AT y BT según etiquetas, sin afirmar que el PASS de auth anterior
  certifica el módulo. CL requiere inventario final vacío incluso tras fallo/timeout.
- Aceptación global de P4.5-B exige **todos C01–C40** y todos los gates requeridos de su alcance.
  Si un gate tiene dependencias bloqueadas (por ejemplo DM), no aprobar RA/MC sobre simulaciones.
- generation y autonomy permanecen NOT_IMPLEMENTED; readiness global BLOCKED, incluso con módulo
  aprobado. P4.6/P4.7 y deployment no se habilitan por ese resultado.

| Resultado B | Regla |
|---|---|
| PASS | Todo obligatorio ejecutado y válido, sin defectos ni limitaciones materiales adicionales dentro del alcance declarado |
| PASS_WITH_LIMITATIONS | Todos los controles obligatorios pasan, límites explícitos aceptables del piloto; ninguna prueba obligatoria omitida como “limitación” |
| FAIL | Defecto reproducible, bypass, pérdida de actualización, integridad/privilegio/secretos incorrectos o evidencia inconsistente no resuelta |
| BLOCKED | Precondición/herramienta/permiso o aprobación requerida ausente; no reemplazar ejecución por mocks |
| NOT_EXECUTED (caso) | No ejecutado; bloquea el gate que lo necesita, nunca se transforma en PASS |

Con limitaciones heredadas, el resultado esperable favorable de B es PASS_WITH_LIMITATIONS,
no una garantía productiva. En A: propuesta READY_WITH_LIMITATIONS; pruebas NOT_EXECUTED;
resource-authorization/module-crud/generation/autonomy siguen NOT_IMPLEMENTED.

## 17. Preservación y hashes de referencia

No recalcular ni reemplazar baseline existente. B toma un manifiesto de entrada adicional del
árbol actual, con git HEAD/status y hashes; sirve para comparar la ejecución nueva, no para borrar
cambios anteriores ni reemplazar oráculos históricos.

| Área | Referencia que deberá usar B |
|---|---|
| P3/corporate-site | docs/migration/P3_BASELINE.json: files y hash del propio baseline; tests/test_p3_baseline.py; 105 fuentes históricas |
| P4.2 | Hashes protegidos de docs/migration/P4_4_A_VALIDATION.json#protectedHashesAfter para factory/business_contracts.py, schemas/business-*, config/business/*, scripts/tests contratos; P4_2_PLAN/VALIDATION/CONTRACTS sin reescritura |
| P4.3 | docs/migration/P4_3_CORE_INVENTORY.json y receipts P4_3_INFRASTRUCTURE/VALIDATION; templates/business-platform y fixture TechnicalSmoke |
| P4.4-A | P4_4_A_PROPOSAL.md, RESEARCH.json y VALIDATION.json, incluidos sus propios hashes |
| P4.4-B core | P4_4_B_RECOVERY_AUDIT.json#currentImplementationHashes (43); sources de continuationRuns en FINAL_RECEIPT; core templates/business-platform-auth completo |
| P4.4-B evidencia | FINAL_RECEIPT/FINAL_REPORT/FINAL_ARTIFACT_SCAN, continuation receipts/snapshots y todos P4_4_B* actuales, hashes propios y referencias internas; no ejecutar finalizers viejos sobre sus destinos históricos |
| nexonova-website | P3_5_GENERATION_MANIFEST.json y stableHash vinculado por P3_BASELINE.json.products; validate_product_integrity, incluyendo metadata |
| synthetic-website | P3_6_GENERATION_MANIFEST.json y stableHash vinculado por P3_BASELINE.json.products |
| nexonova-prototype | config/pilots/nexonova/source-manifest.json: 99 entries SHA256; también conjunto de paths, sin archivos nuevos/perdidos |
| Diseño A | SHA256 de esta propuesta, del receipt A y de las fuentes consultadas; D01 aprobada y propuesta aceptada antes de B |

Los hashes concretos de los documentos referencia están en P4_5_A_VALIDATION.json. B debe
verificar todos los hashes/pathsets antes y después; detener ante diferencias no autorizadas.
En productos, conservar excepción exacta histórica next-env.d.ts generada por Next, reportarla
separadamente; .next/node_modules/test-results no son baseline fuente. No ocultar cambios de código
bajo “derived”. No tocar el prototipo ni usar su runtime/dependencias para la app empresarial.

Regresión B: tests baseline P3, business-contracts y business-infrastructure, validadores estructura/
contratos; auth integrado C35. Reutilizar evidencia de P4.3 y matriz OpenSSL si imagen/fuentes no
cambian; no repetir indiscriminadamente 160 checks ni Docker P2. Si cambia dependencia/imagen/core,
exigir nueva matriz explícita y revisión, no reescribir expected versions o recibos para pasar.

## 18. Evidencia, checkpoints y cleanup de B

Nuevo runner y destino `docs/migration/p4-5-b-runs/{runId}.json`; checkpoint atómico
`{runId}.running.json` tras bloques/steps significativos. Sin sobrescribir P4.4-B. Registrar:
comandos saneados, versiones/digests, fuente/module/validator SHA256, schema/migration/grants hashes,
IDs Cxx/subcasos, actor lógico, resultado esperado/real, timestamps/barreras de concurrencia,
artefactos con hash, errores y motivo de cualquier repetición. Archive del validador exacto por run.
Un checkpoint RUNNING/interrumpido nunca es PASS.

Preparación npm/build aislada de runtime; instalación por lock y versiones fijas, imagen por digest;
checks reales con pull=never. Run nuevo DB/red/volumen propios, red interna, sin publicar DB ni
montar socket Docker, runtime sin root/capabilities, límites CPU/memoria/PID, relays loopback de
validación y TLS local efímero según patrón aprobado. Ningún servicio externo.

Credenciales sintéticas por stdin/env privado del proceso, archivos temporales0600, sin argv,
HAR auth, grabaciones de cookies o screenshots con secretos. Scans exactos en memoria de password,
hash, token, URL y cuerpos sensibles contra raw logs/SSR/receipts antes de persistir; scan secundario
tras informe final. No afirmar ausencia absoluta de secretos ni de intentos de egress.

finally registra cleanup por owner/label/nombre exacto, cierra procesos/relays y elimina envs/TLS/
workspace/volúmenes/redes propios. Verificar ausencia con inventario, no basta llamar remove.
Centinela con owner distinto se preserva y solo su creador lo elimina. Ante timeout/fallo escribir
receipt saneado con pruebas restantes NOT_EXECUTED. Crash del controlador requiere recuperación
manual por inventario/identidad, sin prune global ni borrar datos ajenos.

## 19. Riesgos, decisiones técnicas y limitaciones

1. **FK SQL deliberadamente fuera del grafo Prisma:** evitar modificar User tiene coste de drift
   conocido y composición explícita. C01/C02/C04/C32 son gates, no “se asume que funcionará”.
   No aprobar B si la FK falta aunque Prisma genere/build pase. Añadir inversa en User requeriría
   revisión separada, no está autorizado por este diseño.
2. **Autorización aplicación:** grants por columna no son RLS ni multitenancy. Cuenta runtime
   comprometida es un riesgo distinto; SQL injection se reduce por parametrización y DTO cerrado.
3. **Concurrencia:** proteger cada UPDATE, incluida transición/archive. Un SELECT aislado previo
   no es control suficiente. No prometer exactly-once ante fallo de red ni snapshot paginado.
4. **Archivo terminal:** no restauración, vista archivada ni borrado; retención sin housekeeping.
   Requiere aceptación de UX. No deducir que admin puede saltarse esa regla por all-in-product.
5. **Entrada Unicode:** límites por puntos de código, no grafemas; emoji compuesto puede contar
   varios. Rechazo de NUL/surrogates explícito; sin truncamiento silencioso.
6. **Recursos:** dos pools reutilizados, list acotado y sin limitador empresarial distribuido nuevo.
   Validación local no demuestra capacidad o SLA productivo.
7. **Límites heredados P4.4-B:** provenance histórica incompleta no se reconstruye retroactivamente;
   timing auth sin indistinguibilidad formal (medianas observadas distintas), rate limit en memoria
   de una instancia y reseteable, host/daemon confiables/Linux amd64, recuperación tras crash manual,
   HTTPS autofirmado local sin proxy/deployment, scans conocidos/heurísticos no exhaustivos y
   ausencia de captura de paquetes para intentos de egress. Revisión de vulnerabilidades y seguridad
   productiva pendiente. No resolver deuda fuera de alcance por conveniencia.
8. Sesión se valida al entrar; no hay transacción distribuida con logout/rol. Revocación posterior al
   guard puede coexistir con una escritura en curso; siguiente request debe denegarse. No fortalecer
   silenciosamente la semántica auth ni relajar su expiración/cache.

## 20. Archivos previstos exclusivamente para P4.5-B

Proponer código del módulo en `modules/internal-requests/0.1.0/files/` usando rutas relativas al
producto. Es un overlay local para validar el consumidor del módulo; no una nueva implementación
de generación Factory ni cambio de contratos. Root/core 0.1.0 y versión módulo 0.1.0 se conservan.
El runner de test copia core aprobado y overlay a un workspace descartable, no publica producto
ni modifica CLI, manifests de generación o metadata P3/P4.6.

| Ruta bajo files/ (o raíz indicada) | Propósito futuro |
|---|---|
| src/modules/internal-requests/{validation,authorization,service,repository,dto}.ts | DTO/actor/scope/CAS/modelo dominio; servidor |
| src/modules/internal-requests/db.ts | Singleton Prisma empresarial y configuración runtime aprobada |
| src/modules/internal-requests/components/*.tsx y *.module.css | UI mínima, sin autoridad cliente |
| src/app/requests/page.tsx y [id]/page.tsx | Adaptadores RSC con guard y visibilidad |
| src/app/api/requests/route.ts y [id]/route.ts | GET/POST/PATCH contractuales, parsing/origin/status |
| prisma/modules/internal-requests.prisma | Modelo/enum escalar del módulo, nueve campos; sin User inverse |
| prisma/requests-migrations/00000000000001_internal_requests/migration.sql | Migración nueva revisable con FK/CHECKs/índices |
| prisma.requests.config.ts | Config para schema/historial combinados en workspace |
| validation/requests-runtime-grants.sql | Grants de módulo explícitos, sin bootstrap |
| validation/requests-constraints.json | Inventario esperado de tabla/constraints/índices, no datos |
| tests/requests*.test.mjs y validation/requests-*.ts | Unitarios y probes PostgreSQL; no fixture exportada a UI |
| scripts/validate_business_requests.py (raíz Factory) | Preparación de copia, composición verificada y runner Cxx; no generation CLI |
| scripts/check_business_requests_browser.mjs (raíz Factory) | Navegador real, tooling de validación existente |
| docs/migration/P4_5_B_*.json/.md y p4-5-b-runs/ (raíz Factory) | Nuevos receipts/checkpoints/informe, sin sobrescribir A/B previos |

Rutas fuera del namespace del módulo (adaptadores app, config, grants) son glue explícito previsto,
no nuevas rutas HTTP ni extensión del catálogo P4.2. La composición copia migración auth byte a byte
y agrega la nueva; no cambia prisma/auth/schema.prisma ni historial auth original. Ejecutar generate
con ambos configs explícitos y compilar sources del overlay; el runner puede ampliar la lista de
archivos de comprobación en **config temporal** sin reescribir tsconfig/package-lock del core.
No instalar server-only ni una librería de validación adicional: mantener imports de módulo solo
en entradas servidor y comprobar el bundle. Si el build exige tocar fuentes auth protegidas,
detener antes de hacerlo y presentar el motivo/diff para revisión.

## 21. Secuencia de handoff y revisión

1. Revisar/aprobar este diseño, especialmente archivo terminal, DTO/PATCH, paginación y FK SQL
   sin inversa. D01 ya está aprobada, no pedir nuevamente aprobación de su casing.
2. Tras autorización explícita de B, verificar fuentes/baselines/recursos y fijar snapshot propio.
3. Implementar overlay y composición de test. Primero schema/migración/grants/FK y C01–C04/C32;
   detener ante cambios auth necesarios o incompatibilidad central, sin redesign silencioso.
4. Implementar servicio/DTO/CAS y HTTP; validar C05–C31 por grupos con checkpoints persistidos.
5. UI y navegador, regresión/build/scans/recursos C33–C40. Completar matriz, gates, informe y cleanup.
6. Parar para revisión humana; ni PASS del módulo autoriza P4.6, P4.7, generation o deployment.

**Recomendación A: READY_WITH_LIMITATIONS.** Diseño completo propuesto; D01 resuelta, sin otra
contradicción contractual detectada. No hay código/migración empresarial implementados ni prueba
Cxx ejecutada. Los riesgos enumerados se validarán en B y las limitaciones heredadas no se elevan
a garantías más fuertes. resource-authorization y module-crud siguen NOT_IMPLEMENTED;
readiness global BLOCKED. Revisión humana de A y autorización de B todavía pendientes.
