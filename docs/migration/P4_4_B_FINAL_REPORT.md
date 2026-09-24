# P4.4-B — Informe final de implementación y validación de autenticación

**Recomendación: PASS_WITH_LIMITATIONS. Revisión humana pendiente. Readiness global: BLOCKED.**

Este cierre completa los subcasos del checkpoint de recuperación autorizado. No inicia P4.5,
InternalRequest, CRUD empresarial, generación, autonomía, deployment ni servicios externos.
La recomendación corresponde exclusivamente al piloto controlado de autenticación y probes de rol.

## Estado recuperado y trabajo nuevo

El intento anterior estaba incorporado en `a53035950d9789fe8214171117cf344503cbbc9d`,
con implementación en `templates/business-platform-auth` y 160 comprobaciones registradas.
El receipt histórico declaraba PASS agregado, pero carecía de cobertura granular suficiente y
hashes de fuente/validador capturados durante su ejecución. Su contenido no se modificó ni se
reinterpretó como evidencia de subcasos no ejecutados.

Se tomó [P4_4_B_RECOVERY_AUDIT.json](P4_4_B_RECOVERY_AUDIT.json) como checkpoint inmutable.
Se reutilizaron únicamente comprobaciones identificadas por nombre/índice. Los 43 hashes de
implementación recuperados siguen idénticos: **no hubo cambios en el código de la app, schema,
migración, grants, lockfile ni decisiones aprobadas** durante esta continuación.

El trabajo nuevo añadió validadores complementarios, pruebas Docker/PostgreSQL/navegador,
checkpoints por paso, snapshots de validadores, preservación, cleanup y cierre granular.
El [receipt final](P4_4_B_FINAL_RECEIPT.json) relaciona cada B01–B20 con estados, pruebas,
procedencia recuperada/nueva, hashes y limitaciones. Sus gates se derivan de checks concretos,
no del PASS anterior ni de la existencia de código.

## Ejecuciones de continuación

Se reconstruyó setup descartable cuando fue necesario preparar escenarios faltantes. No se
invocó el runner histórico de 160 checks. Tras los errores del validador se reanudó desde B10
y luego B15, reutilizando los checks ya pasados. Los receipts de fallo permanecen intactos:

| Run | Resultado del run | Interpretación |
|---|---|---|
| `p44bc-965191032d2d4a9a` | FAIL | 73 checks pasaron; expectativa demasiado estricta para slash final. Se verificó posteriormente normalización local 308→404 y ausencia de cambios DB. |
| `p44bc-92ad5e384d4c427d` | FAIL | 36 checks pasaron; variable de fixture ausente al reanudar B15. |
| `p44bc-267055cd7ca7429b` | FAIL | 16 checks de setup pasaron; segunda dependencia de fixture fuera del bloque reanudado. |
| `p44bc-7fc75bbecaab43f4` | PASS | 45 checks; rate limit/recovery, HTTPS y aislamiento entre dos bases completados. |

Los tres fallos fueron del validador, no se ocultaron ni se corrigieron modificando controles
productivos. Cada run realizó cleanup verificado. Los checks anteriores a los fallos se usan
individualmente, con sus referencias exactas; no se convierte un run FAIL en PASS.
Snapshots y receipts: [p4-4-b-continuation](p4-4-b-continuation/).

## Versiones e identidades

| Componente | Versión |
|---|---|
| Better Auth | 1.7.5 exacto; adaptador Prisma desde better-auth/adapters/prisma |
| Node | 22.23.2 |
| Next / React / react-dom | 15.5.25 / 19.2.8 / 19.2.8 |
| TypeScript | 5.9.3 |
| Prisma / client / adapter-pg | 7.5.0 |
| pg / PostgreSQL | 8.16.3 / 16.15 |
| OpenSSL / libssl3 | 3.0.20, paquete Debian 3.0.20-1~deb12u2 |

Imagen de ejecución OpenSSL:
`nexonova-p44b-node-openssl@sha256:0d0e3b31790d5b477357d4596d0c4b97f7fe2c7a43d7501821b7de1d90f52c16`.

Base Node:
`node@sha256:83f487e0a63425e5b4d146fb5e5be574bcbe1b7b843d3ebafdd95eaf7767a7e5`.

PostgreSQL:
`postgres@sha256:efedf3595f1d6f415c08568ba171029bf54052e754cc9f030e3f2412b21f3d67`.

Config digest del build reproducible:
`sha256:fac91b89cb39d1090f9afe0730810e05bb1d43686096e71b79f3fbabbffd338a`.

Se conservan la receta, snapshot Debian, hashes de paquetes y dos builds idénticos en
`infrastructure/images/node-openssl/image-lock.json`, P4_4_B_IMAGE.json y P4_4_B_IMAGE_REBUILD.json.
La matriz base P4.3 con la nueva imagen se reutiliza desde P4_4_B_BASE_MATRIX.json:
53 comprobaciones, sin aviso OpenSSL, sin reescribir la matriz original.

## Matriz B01–B20

PASS se refiere al escenario acotado y a las limitaciones de evidencia declaradas, no a readiness
productiva. No quedan subcasos del recovery audit BLOCKED o NOT_EXECUTED. Los FAIL intermedios
se mantienen en sus receipts y cuentan con resolución explícita.

| Caso | Estado | Evidencia y resultado |
|---|---|---|
| B01 | PASS | Imagen OpenSSL reproducible y versiones/lock; instalación, engines y generate recuperados. Setup nuevo recompila la misma fuente. |
| B02 | PASS | Migración/reaplicación recuperadas + inventario PostgreSQL real exacto: Account, Session, User, Verification y _prisma_migrations. |
| B03 | PASS | Bootstrap transaccional y login real recuperados; nuevos logins comprueban conservación de la contraseña original. |
| B04 | PASS | Carrera con mismo email: CREATED + ALREADY_INITIALIZED, 1 admin/1 cuenta/0 sesiones. Comparación completa de estado tras repetición, otro email, password inválida, member y cuenta parcial. Carrera con distinto email y rollback recuperados. |
| B05 | PASS | Negativas reales en navegador: contraseña incorrecta/email inexistente, 401 y mensaje idéntico, sin cookie. Timing registrado con límites. |
| B06 | PASS | Navegador real con sesión válida/ausente/forjada/expirada. rememberMe true/false/omitido y 28800 segundos en DB recuperados. |
| B07 | PASS | Fixture coherente de timestamps: permite antes de 8h, no cambia createdAt/updatedAt/expiresAt al consultar, deniega al alcanzar/superar 8h tanto probe como get-session. Constante productiva intacta. |
| B08 | PASS | Logout/replay recuperados. Login nuevo emite cookie diferente; cookie elegida por atacante no se adopta y sigue inválida. |
| B09 | PASS | Páginas/API: admin/member autenticados, anónimo denegado, member rechazado en probe admin. Evidencia recuperada de navegador. |
| B10 | PASS | Spoofing recuperado + rol desconocido rechazado por enum PostgreSQL y entrada HTTP; seis variantes encoded/slash cerradas, BD intacta. Dos normalizan con 308 local y terminan en 404. |
| B11 | PASS | Fallos PostgreSQL 42501 recuperados: runtime sin DDL, INSERT/UPDATE User/Account ni lectura Verification/historial; URLs intercambiadas rechazadas. |
| B12 | PASS | Tras reiniciar, sesiones expirada/revocada siguen denegadas en probe y get-session; control válido sigue autorizado. |
| B13 | PASS | Caída DB/revocación SELECT producen 503; fallo bootstrap no deja huérfanos. Evidencia recuperada. |
| B14 | PASS | Navegador HTTPS afirma Secure/HttpOnly/Lax/host-only/Path=/ y cookie de sesión. Forwards no evaden origen ni modifican política. Cookie A, incluso renombrada, denegada en B con DB/red/volumen y secreto independientes. |
| B15 | PASS | 429 con Retry-After:60; IPs declaradas diferentes no evaden presupuesto global. Recupera login tras ventana real sin reiniciar. Concurrencia recuperada. |
| B16 | PASS | Configuración fail-closed recuperada; login y bootstrap rechazan 129 caracteres BMP y 65 emojis (130 unidades UTF-16), conservando estado. |
| B17 | PASS | Scans de valores sintéticos conocidos en memoria contra logs y receipts nuevos, SSR recuperado, navegador sin requests externos. Scan secundario del receipt final. |
| B18 | PASS | Cleanup de todos los intentos y relays comprobado. Temporales antiguos eliminados por rutas verificadas. Inventario host final sin recursos P4.4-B; centinela/timeout/fallo recuperados. |
| B19 | PASS | Typecheck/tests/build/arranque/teclado/no-store recuperados; nuevo setup compile/build y navegador real complementario. |
| B20 | PASS | 148 hashes protegidos + 43 hashes recuperados sin cambios; 99 archivos prototipo y 31 fuentes por producto conservados; 71 tests + validadores contratos/estructura pasan. |

## Migraciones, privilegios y bootstrap

La migración `00000000000000_auth_initial` se conserva sin cambios, SHA256
`e060c8da9cacec4cf00343fef92c045cf35cd1ab6e0017f3b3cd485971a1993e`.
Se aplica con migrate deploy sobre schema app precreado y owned por bpmigrator. La reaplicación
estable tiene evidencia recuperada. El inventario real no contiene TechnicalSmoke ni InternalRequest;
la fixture histórica de TechnicalSmoke permanece separada e intacta.

Runtime: USAGE app, SELECT User/Account y CRUD Session; sin INSERT/UPDATE User/Account, DDL,
Verification ni historial de migración. Bootstrap técnico: conexión bpbootstrap efímera, distinta
de migrator/runtime, SELECT/INSERT User/Account y USAGE app. Se retiran LOGIN y grants al concluir
las operaciones finales; los contenedores, bases y credenciales efímeras se destruyen en cleanup.

Bootstrap es offline, transaccional con advisory lock y hashing público de Better Auth.
No hay signup público/temporal, endpoint de bootstrap, contraseña default ni promoción implícita.
La fixture de member solo opera offline en la validación. La repetición con contraseña distinta
no cambia credenciales: el login posterior usa la contraseña original.

## Better Auth, sesiones y rol

Se conserva Better Auth 1.7.5 con signup deshabilitado y allowlist de sign-in/email, sign-out y
get-session. Wrapper limita entrada, fuerza rememberMe=false y elimina forwards no confiables.
El rol es política propia: admin=ADMIN, member=USER, input:false, enum PostgreSQL.
La DB es autoritativa; los probes no implementan permisos por recurso.

Sesión persistida, máximo absoluto 28800 segundos, hook de expiración, guard de edad y refresh
deshabilitado. Cookie cache no autoritativa/deshabilitada. Cookies HttpOnly, SameSite=Lax,
host-only, Path=/ y Secure en production; HTTP solo para el perfil local-test explícito.
Las pruebas de borde alteran timestamps coherentes de fixture, sin cambiar constantes de producción.

Telemetría deshabilitada en configuración/entorno. Rate limit global conservador del proceso,
cinco intentos/minuto, sin confiar en IP aportada por headers. Aceptado solo para una instancia.

## Evidencia real, preservación y cleanup

- Docker/PostgreSQL reales: bases independientes, grants, concurrencia, inventario y sesiones.
  [Inspección de restricciones](P4_4_B_CONTINUATION_DOCKER.json): sin puertos publicados ni socket
  Docker montado, red interna, read-only, cap-drop ALL y límites de recursos.
- Chromium/Playwright reales: negativos de login/sesión y atributos Secure sobre HTTPS efímero;
  interacción por teclado y viewports desktop/mobile reutilizados de la evidencia anterior.
- [Preservación final](P4_4_B_CONTINUATION_PRESERVATION.json): 148 hashes protegidos, 43 hashes
  recuperados, 99 archivos de prototipo y 31 fuentes por producto. next-env.d.ts mantiene la
  excepción histórica conocida de Next; no se recalcula baseline para ocultarla.
- Regresión pertinente: 71 tests pasados; contratos y validación estructural pasados.
  La suite completa histórica 240 passed/10 skipped se conserva como histórica, no se atribuye
  a esta continuación. No se repitió Docker P2 ni el conjunto histórico completo.
- Todos los runs cerraron relays y eliminaron sus contenedores/redes/volúmenes/directorios.
  [Cleanup de staging anterior](P4_4_B_TEMP_CLEANUP.json) verifica propiedad, marcadores y ausencia
  de uso antes de eliminar las dos rutas exactas; conserva imagen instalada y Playwright compartido.
- [Inventario final del host](P4_4_B_HOST_FINAL.json): ningún temporal/proceso/recurso Docker P4.4-B;
  los dos contenedores ajenos detenidos permanecen. Solo redes bridge/host/none; cero volúmenes.
- Los nuevos receipts incluyen scan exacto de valores sintéticos conocidos en memoria antes de
  persistir, sin guardar esos secretos. El receipt final incluye además scan secundario de patrones y el
  [scan de artefactos finales](P4_4_B_FINAL_ARTIFACT_SCAN.json) coteja once archivos persistidos.

## Limitaciones y revisión humana

1. **Provenance histórica:** el receipt anterior no contiene hashes capturados al ejecutar auth.
   Se comprueba igualdad con el checkpoint y se conservan referencias, pero no se inventa esa
   trazabilidad retroactivamente. Los runs nuevos sí incluyen hashes y snapshots de validadores.
2. **Timing:** tres pares alternados dieron medianas aproximadas 428 ms (password incorrecta)
   y 109 ms (email inexistente), con arranques fríos y dispersión. Los mensajes/estados son iguales;
   estos datos no prueban indistinguibilidad temporal ni descartan enumeración por timing bajo
   medición adversarial. Requiere evaluación más amplia antes de una declaración productiva.
3. **Piloto:** rate limit en memoria, global y de una instancia; reiniciar borra contadores.
   Host/daemon confiables, Linux/amd64, límites de crash/recovery manual heredados.
4. **HTTPS:** certificado autofirmado local aceptado solo por el contexto de prueba; no demuestra
   terminación TLS, proxy o deployment productivo.
5. **Secretos/egress:** los scans exactos cubren valores conocidos; heurísticos no son una auditoría
   exhaustiva. Navegador observa cero llamadas externas y red interna impide egress exitoso del
   servidor; no se presenta captura de paquetes como prueba de ausencia de intentos de egress.
6. Revisión de vulnerabilidades y seguridad productiva pendiente. Sin email/OAuth, recuperación
   de cuentas, administración de contraseñas, recurso empresarial ni mecanismos de recuperación
   tras borrado manual total de tablas.

## Gates finales

| Gate | Estado |
|---|---|
| resource-authorization | NOT_IMPLEMENTED |
| module-crud | NOT_IMPLEMENTED |
| generation | NOT_IMPLEMENTED |
| autonomy | NOT_IMPLEMENTED |
| compatibility | PASS |
| database-migrations | PASS |
| authentication | PASS |
| auth-role-probes | PASS |
| build-tests | PASS |
| cleanup | PASS |
| readiness global | BLOCKED |

`auth-role-probes=PASS` acredita únicamente identidad/sesión y clasificación admin/member.
No satisface autorización horizontal, ownership ni gate global de recursos.

## Archivos de esta continuación

Se crearon, sin modificar código productivo ni archivos históricos:

- `scripts/validate_business_auth_continuation.py` y `scripts/check_business_auth_continuation.mjs`.
- `scripts/check_business_auth_preservation.py`, `scripts/check_business_auth_host.py`,
  `scripts/cleanup_business_auth_temporaries.py`, `scripts/finalize_business_auth.py` y
  `scripts/check_business_auth_final_artifacts.py`.
- `docs/migration/p4-4-b-continuation/`: cuatro receipts y snapshots de validadores por run.
- `P4_4_B_CONTINUATION_PRESERVATION.json`, `P4_4_B_CONTINUATION_DOCKER.json`,
  `P4_4_B_HOST_INITIAL.json`, `P4_4_B_HOST_FINAL.json`, `P4_4_B_TEMP_CLEANUP.json`.
- `P4_4_B_FINAL_RECEIPT.json`, este `P4_4_B_FINAL_REPORT.md` y el scan final de artefactos.

El recovery audit, P4_4_B_AUTH_PROGRESS.json y todos los receipts históricos permanecen intactos.
El documento previo P4_4_B.md se conserva como checkpoint histórico «EN CURSO»; este informe y
el nuevo receipt constituyen el cierre técnico de la continuación, no una aprobación humana.

**Se detiene P4.4-B para revisión humana. P4.5 no iniciada.**
