# P4.3 — Base técnica business-platform 0.1.0

Solo core técnico experimental. No hay producto business generado, autenticación, usuarios de aplicación, sesiones, autorización de recursos ni módulo internal-requests. Los roles PostgreSQL `bpmigrator` y `bpruntime` son identidades técnicas de conexión; no son roles admin/member del producto. Better Auth no está instalado. Readiness global permanece BLOCKED.

## Arquitectura y límites

`templates/business-platform` es independiente de corporate-site. Next App Router/React/TypeScript, CSS Modules y tokens técnicos propios sirven una única página informativa. No hay API pública de persistencia. `src/server/db.ts` centraliza el cliente Prisma y rechaza una identidad de conexión distinta de bpruntime. El servidor debe ejercer futuros permisos de dominio en P4.4/P4.5; el nombre del rol por sí solo no demuestra privilegios, por eso se prueba también PostgreSQL directamente.

La fixture `validation/prisma/schema.prisma` contiene únicamente TechnicalSmoke(id, marker). Demuestra el adaptador y persistencia sin anticipar InternalRequest. Su salida explícita es `src/generated/prisma`, ignorada en fuentes; se genera antes de typecheck/build. No debe trasladarse automáticamente al producto futuro: en P4.5/P4.6 habrá que seleccionar schema/historial de producto expresamente. El nombre fijo `00000000000000_technical_smoke` conserva el formato de historial Prisma, sin timestamps variables por generación. No hay db push, reset, rollback ni migración al arrancar Next o Compose.

`prisma.config.ts` define schema, historial y URL exclusiva del migrador según Prisma 7. `scripts/migrate-check.mjs` requiere MIGRATION_DATABASE_URL con usuario bpmigrator; `src/server/db.ts` requiere DATABASE_URL con bpruntime. No se reciben valores desde configuración pública o WorkOrders. Las credenciales efímeras se crean en memoria para cada run; archivos temporales 0600 pasan variables a Docker y se eliminan. Ninguna contraseña predeterminada está almacenada.

## Dos usos de Docker

1. **Factory:** `factory/business_infrastructure.py` ejecuta un experimento de operador P4.3, no un WorkOrder P4.2. Fija socket local, imágenes por digest, comandos cerrados, límites, timeout y nombres/labels por run. Preparación npm/engine utiliza bridge sin credenciales ni puertos; generate/typecheck/tests/build usan network=none. Pruebas app/DB usan redes Docker internas, sin salida pública ni puertos publicados. No cambia los perfiles P2/P3.
2. **Base del futuro producto:** `compose.yaml` define app+DB con red interna y volumen propio por proyecto Compose. La app usa el Node fijado y monta únicamente el proyecto preparado como readonly; no es todavía una imagen empaquetada para distribución/producción. No hay instalación ni migración como efecto de up. La validación utiliza overrides temporales para conectar Compose a la red/volumen previamente creados por ese mismo run, sin permitir recursos externos arbitrarios al cliente.

App: usuario host sin root, capabilities vacías, root readonly, no-new-privileges, 1 GiB/2 CPU/256 PIDs en Compose (herramientas Node: 2 GiB/2 CPU/256 PIDs). PostgreSQL: UID/GID999, capabilities vacías, root readonly, 512 MiB/1 CPU/128 PIDs y tmpfs limitados para sockets/temporales. Una herramienta separada de preparación del volumen usa root con **solo CHOWN**, sin red, 128 MiB/32 PIDs; no se concede ese privilegio a app o DB.

PostgreSQL usa SCRAM en TCP. Trust local queda limitado al socket dentro del contenedor de DB para preparar las identidades de conexión; no se monta ese socket en app/host. El host/daemon siguen siendo confiables. Runtime no recibe contraseña administrativa o del migrador, no tiene CREATE/TEMP de DB ni propiedad de schema; recibe USAGE de app y CRUD únicamente sobre la tabla técnica. Migrador es dueño del schema app, no superusuario ni creador de DB. La tabla de historial de Prisma no se concede a runtime. El volumen guarda los datos; reiniciar app no demuestra backup/restore.

## Acciones separadas y comandos reales

Desde la raíz Factory, con imágenes disponibles localmente y autorización para el experimento:

```sh
python3 -B scripts/validate_business_infrastructure.py
```

Este comando **crea y elimina infraestructura local efímera**. No consume scopes P3 ni interpreta la autorización contractual P4.2 como permiso de infraestructura. No acepta comandos o rutas de un cliente. Produce recibo sanitizado actual y archivo por run bajo docs/migration/p4-3-runs.

Etapas separadas del runner, en una copia temporal del core:

```sh
npm ci --ignore-scripts --no-audit --no-fund
node node_modules/@prisma/engines/dist/scripts/postinstall.js
npm run generate
npm run typecheck
npm test
npm run compile:checks
npm run build
```

Las dos primeras son preparación con red pública de descarga de dependencias fijadas; no se usan credenciales. Generación/build se prueban después sin red. Para DB, el runner prepara volumen, inicia PostgreSQL, espera TCP y provisiona roles técnicos mediante stdin SQL sin imprimir contraseñas. Después ejecuta por separado `npm run migrate` con entorno exclusivo del migrador, concede los permisos de la fixture y ejecuta `node build-checks/scripts/db-check.js write/read` con entorno exclusivo de runtime.

Compose admite las acciones separadas `docker compose --profile prepare run --rm volume-init`, `docker compose up -d db` y `docker compose up -d app`, **solo una vez preparados los requisitos de entorno y roles**, fuera del repositorio. `up` no provisiona roles técnicos ni migra. No ejecutar manualmente estos comandos sobre bases existentes: P4.3 los prueba en recursos efímeros identificados. El runner valida `compose config --quiet`, `up -d --wait app`, HTTP interno, `restart app` y lectura posterior. No se imprimen configuraciones expandidas con secretos. No hay puerto app publicado por defecto; una futura revisión local puede definir un override loopback explícitamente autorizado.

Variables de Compose: COMPOSE_PROJECT_NAME (namespace exclusivo), APP_UID/GID, POSTGRES_DB, POSTGRES_ADMIN_PASSWORD efímera y DATABASE_URL secreta. MIGRATION_DATABASE_URL se entrega solo al paso migrador, nunca al servicio app. VALIDATION_RUN_ID etiqueta recursos del experimento. Ningún valor secreto pertenece al lockfile, contrato, fuente o recibo. Docker conserva temporalmente su env en metadata privada del daemon confiable hasta eliminar el contenedor.

## Gates y deuda

Compatibility solo cubre versiones probadas de P4.3; no compatibilidad Better Auth. Database-migrations exige DB vacía, historial estable, DDL denegado a runtime, Prisma write/read y persistencia. Build-tests cubre core/arranque, no UI empresarial. Cleanup debe verificar eliminación, no solo invocar rm. Authentication/resource-authorization/module-crud/generation/autonomy siguen NOT_IMPLEMENTED.

La detección/redacción de secretos es secundaria y heurística, no garantía formal. Una caída abrupta del host/daemon/SIGKILL puede requerir inspección/limpieza manual por identidad del run; no ejecutar prune ni borrar recursos ajenos. No hay backup, distribución de imágenes, despliegue, TLS, producción ni actualización automática. Revisión de vulnerabilidades y compatibilidad exacta de Better Auth quedan pendientes; no hay declaración production-ready.
