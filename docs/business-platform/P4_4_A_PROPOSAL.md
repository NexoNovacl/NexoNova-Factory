# P4.4-A — Diseño de autenticación business-platform

Propuesta 0.1.0 · 2026-09-22 · **Solo análisis/documentación; pendiente de aprobación para P4.4-B.** P4.3 fue aprobada formalmente PASS_WITH_LIMITATIONS. No se instalaron dependencias en el core, no se ejecutó Better Auth, no se crearon tablas/usuarios y no se inició P4.5. `authentication=NOT_IMPLEMENTED`; readiness global `BLOCKED`.

## 1. Auditoría del estado real

Se revisaron AGENTS.md, MIGRATION_PLAN.md, propuesta P4.1, contratos/configuración P4.2, fuentes del core y evidencia/inventario P4.3. [Validación de preservación de esta fase](../migration/P4_4_A_VALIDATION.json).

| Elemento existente | Estado verificado documentalmente | Consecuencia para B |
|---|---|---|
| Core/template | business-platform 0.1.0, separado de corporate-site; página técnica sin API empresarial | Añadir auth como revisión explícita, no declarar producto generado |
| Frontend | Node22.23.2, Next15.5.25, React/react-dom19.2.8, TypeScript5.9.3; CSS Modules | Mantener estas versiones salvo incompatibilidad demostrada |
| Datos | prisma/client/adapter-pg7.5.0, pg8.16.3, PostgreSQL16.15 | Revalidar con auth; dos adaptadores con responsabilidades distintas |
| Prisma | prisma.config.ts apunta a validation/prisma; cliente explícito src/generated/prisma | Separar configuración/schema/historial auth de la fixture |
| TechnicalSmoke | Solo id/marker sintéticos, fixture sin endpoint público | **No es dominio ni auth**; no copiar su tabla/migración al futuro producto |
| DB | Schema app del migrador; runtime recibe CRUD solo en TechnicalSmoke | Diseñar grants auth explícitos; runtime sigue sin DDL |
| Compose | Proyecto preparado readonly, DB sin puerto publicado, red interna; NODE_ENV=production | Resolver perfil HTTP local frente a cookies Secure; no desactivar seguridad productiva global |
| Contratos P4.2 | Roles admin/member, máximo8h, registro cerrado, execution prohibida | Preservar bytes/semántica; no interpretar scopes contractuales como permiso de bootstrap |
| Evidencia P4.3 | 53 comprobaciones, 250 tests Factory +2 web, cleanup y persistencia; histórico aprobado | No atribuir esos resultados a Better Auth |

Limitaciones siguen vigentes: aviso OpenSSL, defaults que Next añade al tsconfig temporal, Compose no empaquetado como imagen app distribuible, Linux/amd64, host/daemon confiables, recuperación manual tras crash, revisión de vulnerabilidades pendiente, ausencia de generación/autonomía business. Ninguna queda resuelta por este documento.

## 2. Versión propuesta y compatibilidad

**Proponer `better-auth=1.7.5`**, publicada en npm el 2026-09-14. Se consultó el registro público para identificar la estable y después se inspeccionó **esa versión exacta**; la propuesta no es instalar una etiqueta móvil. Metadata pública y SRI en [evidencia de investigación](../migration/P4_4_A_RESEARCH.json). El tarball se leyó estáticamente en memoria, verificando SHA512 contra su integridad publicada, sin instalar/ejecutar el paquete. Ese cotejo no constituye firma ni auditoría de seguridad.

El paquete declara peers Next14/15/16, React18/19, Prisma/client5/6/7 y pg8. Incluye `@better-auth/prisma-adapter=1.7.5` como dependencia exacta y reexporta el adaptador; preferir `better-auth/adapters/prisma`, sin añadir un segundo adaptador directo redundante. El driver existente `@prisma/adapter-pg` conecta Prisma con pg/PostgreSQL; el adaptador Better Auth traduce sus operaciones al cliente Prisma. [Metadata exacta](https://registry.npmjs.org/better-auth/1.7.5), [adaptador exacto](https://registry.npmjs.org/@better-auth%2fprisma-adapter/1.7.5).

| Relación | Respaldo | Qué NO se ha demostrado aún |
|---|---|---|
| Next15.5.25/App Router | Peer incluye15 y guía oficial de Route Handlers/RSC | Compilación, cookies y rutas con nuestra configuración |
| React19.2.8 | Peer incluye19; cliente React oficial | UI/login, hidratación y navegador |
| Prisma/client7.5.0 | Peers incluyen7; guía específica Prisma7/PostgreSQL | Schema generado, migración y transacciones auth reales |
| PrismaPg7.5.0 / pg8.16.3 / PG16.15 | Adaptador compatible por diseño documentado; matriz base ya ejecutada P4.3 | Operaciones auth exactas, grants y reinicios |
| Node22.23.2 | Paquete principal sin engines explícito; CLI1.7 requiere Node>=22.12 | Resolución completa de engines transitivos/importación/hashing; **inferencia**, no certificación del runtime |
| TypeScript5.9.3/ESM | Core actual ESM; API tipada de biblioteca | Types exactos, exports, servidor/cliente y build |
| Better Auth futuro | Candidato estable exacto y revisión estática | Instalación/lock, ejecución y seguridad: **NOT_EXECUTED en A** |

Fuentes: [Prisma](https://better-auth.com/docs/adapters/prisma), [Next](https://better-auth.com/docs/integrations/next), [guía1.7](https://better-auth.com/docs/guides/1-7-upgrade-guide). La documentación viva puede cambiar: B debe contrastarla con el paquete fijado. 1.7.3 revirtió la exigencia `issuer` introducida en1.7.0–1.7.2; **no añadir issuer** basándose en esas versiones. Fijar también lockfile completo; no usar CLI `@latest`. No se necesita CLI para el MVP si el schema canónico se revisa manualmente contra1.7.5; si se decide usarlo, proponer su versión exacta antes de instalarlo.

## 3. OpenSSL: decisión propuesta, no aplicada

El recibo P4.3 contiene un aviso de detección de libssl y fallback a openssl-1.1.x en la imagen slim; las operaciones probadas pasaron. No demuestra una vulnerabilidad concreta ni ausencia absoluta de librerías. Tampoco permite asumir compatibilidad de herramientas adicionales. [Variantes oficiales Node](https://github.com/nodejs/docker-node), [antecedente del mantenedor sobre slim/OpenSSL](https://github.com/nodejs/docker-node/issues/1919).

| Alternativa | Ventajas | Coste/riesgo y reproducción |
|---|---|---|
| A. Derivar imagen del digest slim actual e instalar OpenSSL durante preparación | Mantiene Node22.23.2 y familia Debian; dependencia explícita y mínima | Requiere Dockerfile versionado, snapshot Debian/versiones exactas de openssl/libssl y dependencias, hashes de paquetes e ID/digest final; apt sin fijación no es reproducible |
| B. Node oficial22.23.2-bookworm completo | Menos mantenimiento de capa propia; misma libc/distribución | Mayor superficie/tamaño. Verificar que el tag exista, resolver digest y comprobar openssl/libssl reales; no asumirlo por nombre |
| C. Mantener fallback o cambiar a Alpine | Ningún trabajo inicial / menor tamaño respectivamente | Mantener warning perpetúa incertidumbre; Alpine introduce musl y otra matriz sin necesidad. No recomendado |

**Recomendar A para B**, con build preparatorio separado de los contenedores restringidos. No instalar durante arranque ni dar root/capabilities al runtime. Fijar repositorio snapshot, versiones disponibles y checksum sin inventarlas ahora; si no puede reproducirse, detener esa preparación y presentar B con digest concreto como alternativa. La imagen resultante tendrá identidad nueva, incluso usando la base antigua. Hoy no se construye ni cambia el digest `node@sha256:83f487e0a63425e5b4d146fb5e5be574bcbe1b7b843d3ebafdd95eaf7767a7e5`.

Gate previo a auth: inventario de paquetes + `openssl version`, detección Prisma sin aviso, npm ci, generate, typecheck/tests/build, migrate deploy/reaplicación, DDL negativo, persistencia/Compose y cleanup. Ejecutar matriz P4.3 en copia explícita con imagen candidata; mantener recibos/digest originales. Si requiere actualizar Node/Next u otra dependencia, presentar cambio de matriz, no sustituirlo silenciosamente.

## 4. Arquitectura y modelos mínimos

Flujo propuesto: navegador → Route Handler Node de Better Auth → adaptador Prisma → cliente PrismaPg runtime → PostgreSQL. RSC y endpoints privados → helper servidor de sesión/rol → misma instancia auth/DB. No Edge, plugins admin/organizations, OAuth, JWT stateless, Redis ni providers externos. Cliente React sirve UX; no decide privilegios. Una instancia Prisma reutilizada por proceso, con lifecycle explícito, evitando crear un pool por request como ocurriría usando sin más el factory actual runtimeClient().

Schema auth independiente en `prisma/auth/schema.prisma`, tablas dentro de `app`. Nombres Prisma User/Session/Account/Verification con mapping canónico revisado. UUID/IDs opacos generados en servidor; uniqueness/FK/índices definidos en migración.

| Modelo | Campos mínimos/canónicos previstos | Propiedad |
|---|---|---|
| User | id, name, email único normalizado, emailVerified=false, image nullable, createdAt, updatedAt; role con enum admin/member | Better Auth identidad; **role es política propia de aplicación** |
| Session | id, token único, userId FK, expiresAt, createdAt, updatedAt, ipAddress/userAgent nullable | Better Auth; datos sensibles, no DTO público completo |
| Account | id, userId FK, providerId, accountId, password(hash) nullable según schema, createdAt/updatedAt; campos OAuth canónicos nullable | Better Auth; necesario para contraseña local: providerId=credential y accountId=User.id |
| Verification | id, identifier, value, expiresAt, createdAt/updatedAt | Tabla base Better Auth; vacía en flujos aprobados, no habilita email |

No duplicar password en User ni crear Role/Permission/Organization/Bootstrap/Requests por anticipación. Account conserva columnas opcionales canónicas accessToken/refreshToken/idToken/scope y sus expiraciones como NULL: no significan OAuth habilitado. Índice único (providerId,accountId), índices de userId en Account/Session y PK/unique token/email. Restricciones exactas contra el schema1.7.5 en B.

**Justificación Verification:** `@better-auth/core@1.7.5/dist/db/get-tables.mjs` incluye esa tabla cuando no hay secondaryStorage. No añadimos Redis ni parches privados para suprimirla; se conserva por compatibilidad del schema base, no “por si acaso”. Account está usado realmente por sign-in/email en el código inspeccionado. [Schema oficial](https://better-auth.com/docs/concepts/database), [paquete core fijado](https://registry.npmjs.org/@better-auth%2fcore/1.7.5). No habilitar envío/verificación de email; `emailVerified=false` no debe mostrarse como identidad verificada.

## 5. Roles y discrepancia contractual

Evaluación: ADMIN puede acceder a una página técnica de prueba administrativa; USER puede acceder al área autenticada mínima pero no a la administrativa. Eso **no** implementa autorización por propietario de recursos. Autenticación identifica al usuario; rol lo clasifica; P4.5 aplicará política de registros.

P4.2 fija literalmente `admin/member`. **Recomendación:** conservar esos valores en DB/contrato y usar equivalencia documental ADMIN=admin, USER=member. Default member; valor desconocido denegado. No introducir cuatro roles ni un mapeo dependiente del cliente. Si el equipo exige guardar ADMIN/USER literalmente, hará falta nueva versión/revisión explícita de contratos, fixtures y tests; no autorizada aquí. Confirmar nomenclatura antes de B.

Campo adicional role con input:false y validación enum; sin edición vía UI/API, sin plugin admin. Leer rol desde DB a través de sesión validada, nunca de body/query/header/cookie controlada por cliente. Deshabilitar cache de sesión para evitar roles/revocaciones desactualizados. P4.4 solo acredita denegación básica por rol; acceso horizontal a InternalRequest sigue pendiente.

## 6. Registro cerrado y superficie HTTP

Config propuesta: emailAndPassword.enabled=true, disableSignUp=true, autoSignIn=false; sin socialProviders, anonymous plugin, email provider o endpoints de bootstrap. No crear /signup. [Opciones](https://better-auth.com/docs/reference/options).

Además, el wrapper servidor de `/api/auth/[...all]` permite únicamente POST sign-in/email, POST sign-out y GET get-session. Otros métodos/rutas, incluyendo sign-up/email, actualización de usuario/rol, account linking y password reset, responden denegación estable sin delegar. Canonicalizar/validar path y método; probar encoded paths, variantes y llamada directa. No sustituir controles de origen de Better Auth ni parchear node_modules.

La UI omite signup pero no es la barrera. Rechazar campos de elevación (role/userId) y forzar rememberMe=false en servidor, aunque el body omita el campo o envíe true. Mantener only-local callback/redirect, sin URL arbitraria proporcionada por cliente. Runtime no tendrá INSERT/UPDATE sobre User/Account: defensa adicional comprobada con PostgreSQL, no únicamente botones ocultos.

## 7. Bootstrap offline: contrato y flujo propuestos

Comando Node explícito futuro, no implementado: `bootstrap-admin`. Sin listener HTTP, sin ejecución automática en up/build/migrate, sin flags force/promote/reset. Requiere autorización manual del operador para DB sintética identificada.

Entradas: identificador de producto/DB esperado (no secreto), nombre/email del admin sintético y contraseña por stdin sin eco o archivo temporal0600 suministrado en el momento. Nunca contraseña en argv, default, shell history ni fixture aceptada. Credencial de conexión efímera **BOOTSTRAP_DATABASE_URL**, entregada solo al proceso offline y eliminada al finalizar. No registrarla ni incorporarla a WorkOrder/.nexonova. Rechazar configuración incompleta antes de escribir.

Proponer rol PostgreSQL técnico `bpbootstrap`, distinto de rol de aplicación admin: SELECT/INSERT solamente sobre User/Account y USAGE app, sin DDL ni edición de roles existentes. Credencial habilitada únicamente para operación explícita, retirada al terminar. Esto requiere **nuevo requisito privado de bootstrap separado** en B; no añadir un sexto campo silencioso a EnvironmentRequirements P4.2. Alternativa de reutilizar MIGRATION_DATABASE_URL no recomendada: mezcla consumidores y da privilegios DDL innecesarios. La autorización general de diseño no habilita ninguno ahora.

Flujo: validar política de email/password → hashing mediante export público `hashPassword` de `better-auth/crypto`1.7.5 → transacción Prisma con advisory lock transaccional específico en esa DB → comprobar tablas/estado de inicialización → insertar User(role=admin) y Account(credential) atómicamente → commit → emitir solo código/resultado saneado. SQL parametrizado para lock/consultas; sin hashing propio ni API privada de Better Auth. Login real posterior deberá demostrar que el hash y las filas son compatibles. No invocar signUpEmail deshabilitado ni abrir signup temporalmente.

| Caso | Resultado contractual propuesto |
|---|---|
| DB realmente vacía, sin migración auth | BLOCKED/SCHEMA_NOT_READY, no crear tablas |
| Schema auth listo y sin usuarios/cuentas | Crear un único admin y cuenta en una transacción; salida0 CREATED |
| Repetición con mismo email y admin/cuenta íntegros | Salida0 ALREADY_INITIALIZED, cero escrituras; no cambiar password/role ni autenticar contraseña presentada |
| Repetición con otro email, admin existente o usuarios previos | No crear/promover; salida no cero INITIALIZATION_CLOSED |
| Email duplicado/member existente/cuenta parcial | Conflicto no cero; rollback, revisión manual, sin reparación/promoción automática |
| Password inválida | Rechazo antes de DB/hash costoso; no mostrar valor |
| DB no disponible/permisos insuficientes | Fallo no cero saneado; ninguna creación parcial |
| Dos bootstraps concurrentes | Lock y constraints garantizan solo un commit inicial; segundo obtiene estado cerrado/no-op según identidad |

Idempotencia significa no repetir efectos, no reestablecer credenciales. No hace falta tabla extra de bootstrap: cualquier User existente cierra inicialización, y el lock serializa primeras creaciones. Recuperación tras borrado manual total de tablas no está cubierta; no es mecanismo de recuperación de cuentas. Miembros sintéticos para pruebas se crean en un fixture offline separado, explícitamente autorizado y nunca expuesto como herramienta administrativa genérica.

## 8. Passwords, sesiones y cookies

Propuesta NexoNova: contraseña de15–128 caracteres, sin truncar/trim ni imponer composición arbitraria; comprobar longitudes según semántica de1.7.5 e incluir Unicode en tests. Hash/verify delegados a Better Auth, sin algoritmo/salt propios. Login desconocido y password incorrecta comparten mensaje genérico; limitar tamaño de body antes de hashing. No registrar bodies, URL secretas, hashes, cookies ni tokens; logger controlado con códigos permitidos y sin serializar Error/contexto completo. Recuperación por email, cambio de contraseña y administración de cuentas quedan fuera de B.

Better Auth documenta límites configurables y credenciales locales; hashing queda a su implementación fijada. [Email/password](https://better-auth.com/docs/authentication/email-password). Las decisiones15–128 y errores son propuesta del piloto, no defaults atribuidos a la biblioteca.

**Hallazgo estático crítico:** en1.7.5 `dist/db/internal-adapter.mjs`, createSession usa **24 horas** cuando dontRememberMe=true. `expiresIn=28800` por sí solo **no garantiza 8h si rememberMe=false**. Proponer hook soportado `databaseHooks.session.create.before` que limite expiresAt al mínimo entre la fecha recibida y createdAt+28800s, con tiempo del servidor; disableSessionRefresh=true, cookieCache.enabled=false y sin secondaryStorage. Guard servidor adicional rechaza edad>=8h. Verificar también el propio get-session de Better Auth y la fila DB, no solo una página custom. No modificar la librería ni afirmar que el hook ya funciona. [Paquete1.7.5](https://registry.npmjs.org/better-auth/-/better-auth-1.7.5.tgz), [hooks](https://better-auth.com/docs/reference/options), [sesiones](https://better-auth.com/docs/concepts/session-management).

| Política | Propuesta a verificar en B |
|---|---|
| Persistencia | Session en PostgreSQL; secreto estable durante reinicio del run; no JWT/cache autoritativa |
| Expiración | Máximo absoluto8h, no sliding refresh, sin “recordarme”; manipulación del body no lo amplía |
| Cookies | HttpOnly, SameSite=Lax explícito, Path=/, host-only sin Domain; prefijo derivado del productId sin ramas por cliente |
| Producción | Secure=true, HTTPS requerido, origen configurado exacto; configuración inválida bloquea inicio |
| Desarrollo local | Perfil explícito interno/loopback HTTP permite Secure=false solo en ese perfil; no atribuirle seguridad productiva |
| Logout | POST con protección origen; invalidar sesión DB y expirar cookie; token/cookie previo no vuelve a autorizar |
| Revocación | Comprobar sesión revocada en cada acceso; sin caché que retrase efecto. Gestión masiva/cambio password futuro no implementado |
| Secretos | BETTER_AUTH_SECRET aleatorio de alta entropía (mínimo32 bytes propuesto), separado por producto, nunca default ni NEXT_PUBLIC |

[Cookies](https://better-auth.com/docs/concepts/cookies). Una cookie de sesión puede restaurarse por el navegador; “cerrar navegador” no sustituye al máximo servidor de8h. Puertos distintos no aíslan cookies: prefijos únicos, secretos y DB independientes; probar cookie A en B. No loguear respuestas auth completas ni HAR con tokens. SSR transmite solo DTO mínimo de identidad/rol, no el objeto Session completo.

El Compose actual usa NODE_ENV=production y HTTP interno. B debe proponer un **perfil auth local de prueba**, con excepción HTTP estrictamente limitada y validación de flags/origen; no bajar Secure globalmente. Para comprobar semántica Secure usar HTTPS efímero local de test o comprobación negativa/configuración y navegador seguro cuando esté disponible; sin deployment, VPS ni Nginx/TLS productivo. Documentar cualquier escenario no ejecutado.

## 9. Rutas y fronteras servidor/cliente

Archivos propuestos: `src/server/auth.ts` (server-only), `src/server/auth-guards.ts`, `src/client/auth-client.ts`, `src/app/api/auth/[...all]/route.ts` (runtime=nodejs), `/login`, `/auth-check`, `/admin-check`, `/api/auth-check` y `/api/admin-check`. Las dos últimas son probes mínimos, sin datos empresariales ni CRUD. /login pública; páginas privadas redirigen a /login sin sesión; APIs retornan401 sin sesión y403 para member en probe admin. DB inaccesible:503 saneado/fail closed, nunca usuario anónimo convertido en permitido.

Servidor usa auth.api.getSession con `await headers()` y comprueba DB/expiración/rol en cada operación. Página o layout no protege por sí solo el Route Handler: cada entrada repite guard. No confiar en mera presencia de cookie ni middleware; middleware opcional solo UX y no necesario para MVP. Cliente llama Better Auth para login/logout y maneja errores; no importa Prisma/config/secretos. Next App Router no requiere actualizar a16 para este enfoque. [Integración oficial](https://better-auth.com/docs/integrations/next).

No plugins nextCookies/Server Actions inicialmente: login/logout por Route Handlers que sí pueden emitir Set-Cookie. Cache-Control:no-store en respuestas privadas; no caching global de sesión entre requests. Una sesión presente no confiere rol admin, y rol admin no sustituye futura autorización de recursos.

## 10. Schema, migraciones y grants

Nuevo `prisma/auth/schema.prisma` y configuración auth separada (`prisma.auth.config.ts` propuesta; comprobar flag --config de Prisma7.5.0 en B). Output auth diferente del cliente de fixture para evitar colisión. Historial `prisma/auth/migrations/00000000000000_auth_initial/` fijo/revisable. Generar SQL en entorno descartable/revisar constraints, luego migrate deploy desde DB vacía y reaplicar sin cambios. Sin db push/reset ni auto-migrate al arrancar.

**No migrar la DB de TechnicalSmoke “convirtiéndola” en auth.** Conservar su fixture/historial y evidencia; crear DB auth nueva y descartable. No hay datos empresariales existentes que deban migrarse en B. Mantener secuencias de pruebas P4.3 separadas. En P4.6 seleccionar schema/historial de producto explícitamente, sin TechnicalSmoke.

Migrador mantiene DDL en app y ownership de nuevas tablas. Runtime: USAGE schema; SELECT User/Account; CRUD Session por lifecycle; sin INSERT/UPDATE User/Account, sin acceso al historial de migraciones, sin CREATE/TEMP de DB ni DDL. Verification inicialmente sin grants de runtime porque no hay flujos permitidos que la consuman; schema canónico existe y permanece vacío. Si una ruta interna exige más grants, documentar consulta/caso y revisar privilegio mínimo; no conceder ALL por conveniencia. Bootstrap solo SELECT/INSERT User/Account con su conexión efímera; sin sesiones ni modificación de cuentas existentes. Probar los grants reales tras migraciones; no asumir que URL/nombre de rol garantice permisos.

Variables existentes: DATABASE_URL solo app; MIGRATION_DATABASE_URL solo migración; BETTER_AUTH_SECRET solo servidor; BETTER_AUTH_URL origen público configurable; NODE_ENV privado. Nuevos requisitos propuestos para perfil B/bootstrap: identificador/prefijo de producto, modo local HTTP explícito y BOOTSTRAP_DATABASE_URL/input por stdin. Se representan fuera de contratos cerrados P4.2 hasta aprobar un contrato adicional; jamás valores secretos. Telemetría Better Auth deshabilitada explícitamente (`telemetry.enabled=false`, entorno BETTER_AUTH_TELEMETRY=0), sin endpoints externos. [Telemetría oficial](https://better-auth.com/docs/reference/telemetry).

## 11. Threat model y límites

Actores: visitante anónimo, miembro autenticado malicioso, atacante con cookie capturada, operador que configura mal. Host/daemon confiables como P4.3; comprometer DB/host no queda resuelto por auth. Datos exclusivamente sintéticos.

| Amenaza | Control propuesto | Evidencia exigida en B |
|---|---|---|
| Signup anónimo / admin autoasignado | disableSignUp + allowlist servidor + role input:false + grants DB | POST directo, rutas codificadas, bodies con role; cero filas nuevas |
| USER→ADMIN / rol cliente | Enum cerrado, DB autoritativa, runtime sin UPDATE User | Manipulación body/header/cookie y SQL negativo;403 en probe admin |
| Sesión robada/fijada | Token nuevo al login, cookies protegidas, revocación/max8h | Token previo/forjado/revocado rechazado; no afirmar invulnerabilidad XSS |
| CSRF/login CSRF | Origin/trustedOrigins exactos, controles Better Auth conservados, SameSite; POST mutaciones | Origin ajeno, null/ausente y Sec-Fetch-Site hostil; no basta SameSite |
| Cookies/proxy inseguros | HTTPS productivo, host-only, prefijo propio; no confianza arbitraria en X-Forwarded-* | Perfil producción HTTP rechazado, inspección Set-Cookie, cookie entre productos |
| Enumeración | Error uniforme y sin serializar causas DB; hashing de biblioteca | Email inexistente/password incorrecta misma respuesta; timing revisado sin prometer indistinguibilidad formal |
| Fuerza bruta/DoS hash | Body acotado; rateLimit.enabled=true explícito, regla login propuesta5/min; límites contenedor | Sexto intento429, concurrentes, identidad cliente no falsificable por header |
| Logs/credenciales default | Sin valores default, logger allowlist, no HAR auth, detector secundario | Buscar valores sintéticos/URL/password/hash/token en recibos/logs sin mostrarlos |
| Bootstrap repetido/concurrente | Solo offline, lock transaccional+unique, no promote/reset | Dos procesos: un único admin; rollback sin huérfanos |
| Acceso sin sesión/expirada | Guard servidor por entrada, DB lookup, sin cache, clamp8h | Página/API/direct request, expiry DB y límite absoluto |
| DB caída/permisos erróneos | Fail closed503, transacción atómica | Parar DB descartable y quitar permisos en fixture; nunca éxito parcial |
| XSS/exposición SSR | React escaping, sin HTML arbitrario; DTO mínimo | No tokens/hashes en HTML/logs, no uso de dangerouslySetInnerHTML |
| Config producción incorrecta | URL/origen/secreto/rol DB requeridos; sin defaults seguros supuestos | Rechazar HTTP productivo, secretos ausentes y URLs de roles intercambiadas |

Rate limit en memoria de un único proceso para piloto cerrado; reinicio borra contadores y no protege multiinstancia/ataques distribuidos. Aceptación explícita requerida; no añadir Redis ni otra tabla por anticipación. Si se exige contador persistente antes de B, proponer tabla RateLimit y migración revisada, no introducirla silenciosamente. En acceso directo no confiar en X-Forwarded-For arbitrario; probar extracción de IP de versión exacta; si no es fiable, usar límite conservador global de instancia para piloto y documentar su impacto. [Rate limit](https://better-auth.com/docs/concepts/rate-limit), [seguridad](https://better-auth.com/docs/reference/security). Estos son controles propuestos, no amenazas “eliminadas” por el framework.

## 12. Plan de pruebas P4.4-B y criterios de salida

Todas usarán credenciales/datos sintéticos, DB/red/volumen por run, sin puertos DB publicados, sin daemon remoto ni socket dentro de contenedores. Preparación de imágenes/npm separada; luego --pull=never y red interna cerrada. Recibos sin secretos; cleanup solo de recursos propios. No se ejecuta nada de esta tabla durante A.

| ID | Nivel | Escenario y resultado exigido |
|---|---|---|
| B01 | Preparación+Docker | Imagen OpenSSL y versiones exactas/lock; engine detection sin warning; npm ci/imports/Prisma generate reales |
| B02 | Integración DB | Migración auth desde vacío/reaplicación; schema esperado sin TechnicalSmoke ni InternalRequest |
| B03 | Integración DB | Bootstrap válido crea un User admin/Account credential, sin Session; login comprueba hash real |
| B04 | Docker concurrente | Bootstrap mismo/diferente email, dos procesos, duplicado, estado parcial, password inválida; no segundo admin/huérfanos |
| B05 | Integración+navegador | Login correcto, incorrecto y email inexistente; mensajes genéricos, no enumeración obvia |
| B06 | Navegador+DB | Session válida/ausente/forjada/expirada; creación con rememberMe true/false/omitido siempre<=8h; fila DB y auth get-session |
| B07 | Integración | disableSessionRefresh; avanzar reloj controlado o timestamps de fixture para borde8h, sin esperar8h ni relajar constantes de producción |
| B08 | Navegador+API | Logout y replay de cookie/token revocado rechazado; nueva sesión no reutiliza una fijada |
| B09 | Servidor+navegador | /auth-check y API: admin/member permitidos; anónimo401/redirección; probe admin rechaza member403 |
| B10 | Unitario+integración | Role body/query/header/cookie, valores desconocidos, update-user y signup directo: ninguna promoción/creación |
| B11 | Docker PostgreSQL | Runtime sin DDL ni INSERT/UPDATE User/Account; URLs intercambiadas y bootstrap con runtime denegados |
| B12 | Docker reinicio | Reiniciar app conserva usuarios y sesión aún válida con mismo secreto/DB; revocada/expirada no revive |
| B13 | Docker fallo | DB apagada/permisos insuficientes: fallo saneado, sin conceder acceso ni escrituras parciales |
| B14 | Navegador/HTTP | Cookies HttpOnly/SameSite/Secure, ausencia de Domain, namespace por producto, origen/CSRF/redirect/forwards maliciosos |
| B15 | Integración concurrente | Rate limit habilitado también en pruebas,429/retry; límite tras reinicio documentado |
| B16 | Unitario+integración | Config faltante/producción HTTP/secreto corto/origen incorrecto fail closed; política password Unicode y máximo |
| B17 | Evidencia real | Detección de valores sintéticos en logs/recibos/SSR/capturas; cero llamadas externas incluidas telemetry |
| B18 | Docker | Cleanup éxito/fallo/timeout; centinela ajeno preservado, inventario final ausente; crash manual según límites P4.3 |
| B19 | Web | Typecheck, tests, build, arranque real, login/logout por teclado; rutas protegidas sin caché pública |
| B20 | Regresión | Baseline P3, contratos P4.2, fixture P4.3 original y nueva revisión autorizada; productos/prototipo intactos |

No sustituir pruebas DB por mocks ni marcar lo no ejecutado como PASS. Unitarios: validación/políticas/mapeo/envelope/rutas/gates; integración: adaptador/SQL/transacciones/session; Docker: stack/red/privilegios/reinicio/cleanup; navegador: cookies/flujo/teclado. Un test sin DOM no acredita cookies de navegador.

## 13. Gates y alcance de recibos

| Gate | Ahora A | Condición en B |
|---|---|---|
| compatibility | P4.3 PASS histórico; extensión auth NOT_EXECUTED | B01+B19 y matriz nueva documentada; ningún peer/engine ignorado |
| database-migrations | P4.3 PASS histórico; auth NOT_EXECUTED | B02–B04+B11–B13, reaplicación estable y runtime sin DDL |
| authentication | NOT_IMPLEMENTED | B03–B08+B10+B14–B17 pasan con Better Auth real |
| resource-authorization | NOT_IMPLEMENTED | Puede PASS solo con scope **probes sesión/rol**, B09–B11; ownership InternalRequest sigue NOT_IMPLEMENTED y no satisface gate completo P4 |
| build-tests | Core P4.3 PASS histórico; auth NOT_EXECUTED | Typecheck/tests/build/arranque/navegador B19 |
| cleanup | P4.3 PASS histórico; B NOT_EXECUTED | B18 comprobado, no solo invocar rm |
| module-crud / generation / autonomy | NOT_IMPLEMENTED | No cambian en B |
| readiness global | BLOCKED | Continúa BLOCKED hasta fases restantes |

Cualquier defecto reproducible en control obligatorio: FAIL; precondición externa ausente: BLOCKED; prueba no ejecutada: NOT_EXECUTED. Los receipts históricos no se reescriben. Recomendación: mantener gate agregado resource-authorization en NOT_IMPLEMENTED y publicar subgate auth-role-probes PASS cuando corresponda, para impedir que un consumidor confunda probes con autorización horizontal completa.

## 14. Archivos afectados en B (propuesta; ninguno cambiado hoy)

Los siguientes cambios requieren aprobar **nueva revisión de P4.3**, no recalcular su inventario antiguo:

| Archivo/área existente | Motivo/consumidores | Impacto propuesto |
|---|---|---|
| templates/business-platform/package.json y package-lock.json | Scripts/core/harness; dependencia auth exacta | Lock nuevo explícito; core previo preservado por inventario y copia verificable |
| src/server/db.ts | db-check técnico importa runtimeClient; futuro auth necesita pool único/cliente auth distinto | Preferir nuevo auth-db.ts y preservar helper fixture; modificar solo si prueba exige cambio |
| compose.yaml | Runner business P4.3 usa archivo; nuevas env/cookies/perfil imagen | Preferir compose.auth.yaml separado; no cambiar digest global ni overrides P3 |
| tsconfig.json/tsconfig.checks.json/next-env.d.ts | Next/tests/core | Normalizar allowJs/incremental/isolatedModules y compilación auth como revisión explícita; probar build sin mutaciones sorpresa |
| prisma.config.ts / validation/prisma / runtime-grants.sql | Fixture P4.3 y su runner | Preservar; añadir config/schema/grants auth paralelos |
| tests/core.test.mjs / scripts/db-check.ts / start-check.mjs | Prueban ausencia de auth/modelo técnico en fixture | Conservar objetivo; tests auth nuevos, no relajar aserciones para fingir preservación |
| factory/business_infrastructure.py | Matriz/expectations P4.3 fijas; 13 tests de política | Preferir nuevo runner business_auth_validation y nuevo recibo; no cambiar expected_versions de evidencia anterior |

Creados propuestos: Dockerfile de preparación OpenSSL y su inventario; compose.auth.yaml; prisma.auth.config.ts, prisma/auth/schema/historial/grants; auth-db/auth/auth-guards/server-config, auth-client y rutas mínimas; bootstrap-admin offline, fixtures sintéticas, tests auth/navegador/DB; requisitos/autoridad auth-bootstrap separados y recibos versionados.

Consumidores protegidos P3: helpers importados/root/hashes/generación no necesitan modificación. Contratos P4.2 no deben ampliar scopes/actions/significado; permisos B son un perfil experimental explícito nuevo. MIGRATION_PLAN.md conserva P4: A/B es desglose del gate de autenticación, no expansión a P5 mantenimiento, P6 agentes ni P7 deployment.

## 15. Decisiones humanas y recomendación

Propuesta lista para revisión, **no autorización implícita de B**:

1. Aceptar1.7.5 como candidato fijo y opciónA OpenSSL con nueva imagen/matriz, sin asumir compatibilidad ejecutada.
2. Confirmar equivalencia ADMIN→admin y USER→member manteniendo contratos, o solicitar revisión de nomenclatura versionada.
3. Aprobar esquema canónico de cuatro tablas (Verification por requisito de biblioteca), extensión role propia y exclusión de TechnicalSmoke.
4. Aprobar bootstrap offline transaccional con credencial técnica efímera separada y nuevo requisito privado, sin cambiar contratos P4.2.
5. Aprobar máximo8h con hook de expiración probado, sin renovación/recordarme/cache; el default de24h descubierto no satisface la política.
6. Aprobar perfil HTTP local explícito y límite rate-limit en memoria para una instancia controlada; ambos siguen siendo blockers para una declaración productiva general.
7. Aprobar los archivos/revisiones enumerados y la matriz de pruebas/gates. Sin ello no se modifica el core.

**Recomendación: proceder con P4.4-B solo después de aprobar esta propuesta y sus decisiones.** No hay impedimento documental evidente de peers para la matriz; sí hay ajustes necesarios de sesión, permisos, schema e imagen que requieren prueba real. No se recomienda habilitar auth usando defaults. Publicación, producción, datos reales, servicios de email/IA/OAuth, recuperación de contraseña, módulo empresarial y fases posteriores siguen fuera del alcance.

## 16. Evidencia de A

Preservación y comandos ejecutados se registran en P4_4_A_VALIDATION.json: baseline P3, hashes P4.2, inventario P4.3, contratos completos, ambos productos y99 archivos del prototipo. Tests de preservación/contratos/política ejecutados; no se repiten Docker/build P4.3 porque no cambia código ni se autoriza infraestructura nueva. Es evidencia histórica válida de P4.3, no evidencia de auth.

Esta fase crea solo este documento y dos archivos de evidencia. No modifica el core, lockfiles, configuración, contratos, inventarios aprobados, MIGRATION_PLAN.md ni productos. Finaliza para revisión humana.
