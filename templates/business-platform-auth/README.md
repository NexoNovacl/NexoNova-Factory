# Business-platform auth core — revisión P4.4-B 0.1.0

Revisión de autenticación de la capacidad business-platform, separada físicamente
para preservar el core/fixture histórico P4.3 en `../business-platform`.
No es un producto generado ni una nueva capacidad. Sin TechnicalSmoke/InternalRequest.
El informe de aceptación y limitaciones está en `../../docs/migration/P4_4_B.md`.

## Validación autorizada

Desde Factory: `python3 -B scripts/validate_business_auth.py`.
El runner prepara una copia temporal, instala desde lock, compila y usa DB/red/volumen
por run. No utiliza WorkOrders P3 ni amplía scopes de contratos P4.2. Es una operación
explícita del operador autorizada para pruebas, no ejecución autónoma por cliente.

Preparación separada de ejecución: npm ci con scripts deshabilitados; postinstall
Prisma explícito en preparación; después generate/typecheck/tests/build sin red.
La imagen con OpenSSL está fijada en `../../infrastructure/images/node-openssl/image-lock.json`.
No existe comando de generación o deployment de este core en esta fase.

## Comandos del package (en copia preparada y entorno autorizado)

- `npm ci --ignore-scripts --no-audit --no-fund`
- `node node_modules/@prisma/engines/dist/scripts/postinstall.js` (preparación)
- `npm run generate`
- `npm run compile:checks`
- `npm run typecheck`
- `npm test`
- `npm run build`
- `npm run migrate` (solo migrador; DB y schema app ya provisionados)
- `npm run bootstrap-admin` (JSON por stdin; solo credencial bpbootstrap)
- `npm start` (contenedor restringido; no arranca migraciones/bootstrap)

Estos comandos no autorizan una DB externa ni publicar el puerto de una app host.
El runner usa app y PostgreSQL en red Docker interna y un relay de prueba en loopback.
El Compose histórico P4.3 no fue cambiado ni se presenta como Compose auth distribuible.

## Entradas y fronteras

| Variable | Consumidor | Naturaleza |
|---|---|---|
| DATABASE_URL | app | Secreta; rol bpruntime |
| MIGRATION_DATABASE_URL | migrate | Secreta; rol bpmigrator; nunca bootstrap/app |
| BOOTSTRAP_DATABASE_URL | bootstrap offline | Secreta y efímera; rol bpbootstrap |
| BETTER_AUTH_SECRET | app | Secreta, alta entropía; mínimo32 bytes; independiente por instancia |
| BETTER_AUTH_URL | app | Origen explícito, sin path/query; no inferido del navegador |
| AUTH_PRODUCT_ID | app | Slug público, prefijo propio de cookies |
| AUTH_PROFILE | app | local-test o production; sin default |
| NODE_ENV | Next | production en validación del build |
| BETTER_AUTH_TELEMETRY / NEXT_TELEMETRY_DISABLED | validación | 0 / 1; telemetría auth también deshabilitada en código |

Son requisitos del perfil auth, no una extensión silenciosa de EnvironmentRequirements P4.2.
Nunca poner valores secretos en JSON público, Next public env, logs o metadatos.

Bootstrap recibe un objeto JSON UTF-8 por stdin con database, email, name y password.
No hay password default, argumentos de password, signup temporal, force/promote/reset
ni endpoint HTTP. Verifica DB esperada y rol de conexión; el operador habilita la credencial
solo para la operación autorizada y la retira después. Hash público Better Auth, transacción
con lock y cuentas atómicas. Repetir la misma identidad íntegra retorna ALREADY_INITIALIZED
sin cambiar ni verificar la contraseña presentada: **no es un login ni un reset**.
Otros estados fallan con BOOTSTRAP_REJECTED sin detalles sensibles. La fixture de member
solo se compila para validación offline; no hay UI/API de administración de usuarios.

## Política de piloto

Roles admin/member; User.role es política propia de app y no es editable desde cliente.
Sesión máxima8h, sin refresh ni cache autoritativa; rememberMe se fuerza a false.
Passwords15–128 unidades UTF-16, coherentes con la comprobación JavaScript de esta
integración; no trim de contraseña, hashing/verificación delegados a Better Auth.
Cookie HttpOnly, host-only, SameSite=Lax; Secure obligatorio en production y HTTPS requerido.
HTTP solo en perfil explícito local-test para 127.0.0.1. Los certificados de la prueba
HTTPS son efímeros: no constituyen infraestructura TLS productiva.

Rate limit conservador adicional global por proceso:5 intentos de login/minuto;
no confía en IP enviada por headers. Se reinicia con el proceso, puede afectar a otros
usuarios del mismo piloto y no sirve como defensa distribuida/multiinstancia.

/login; /auth-check; /admin-check y probes API. Solo sign-in/email, sign-out y get-session
se delegan a Better Auth. No OAuth, email/reset, MFA, dashboard, CRUD ni autorización
horizontal de recursos. La ausencia de esos módulos no se marca como gate aprobado.

Runtime: SELECT User/Account y CRUD Session; sin DDL ni escritura User/Account.
Bootstrap: SELECT/INSERT User/Account; migrador propietario de app y del historial.
Verification existe por schema canónico y no se usa ni tiene grants runtime.
La migración estable presupone app provisionado; nunca db push/reset ni migración en up/start.

## Límites

Uso interno/controlado, una instancia; host y daemon confiables; Linux/amd64.
El navegador utiliza la herramienta/cache existente de P3 en el host como infraestructura
de pruebas, no como dependencia de la aplicación. Sin producto business materializado,
Compose auth empaquetado, actualización, recuperación de cuentas, deployment ni autonomía
formal. Ante SIGKILL se inspeccionan y limpian recursos manualmente; no replay automático.
La redacción/detección de secretos es secundaria y heurística, no garantía absoluta.
