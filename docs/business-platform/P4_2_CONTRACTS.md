# P4.2 — Contratos business-platform

2026-09-15. P4.1 aprobada formalmente; ejecución de P4.2 autorizada con internal-requests y reglas del usuario. **Entrega contractual para revisión humana; P4.3 no iniciada.** No existe todavía aplicación, template business, DB, usuario ni migración.

## Implementación y uso

Nuevo módulo `factory/business_contracts.py`: composición de contratos usando helpers/validación estricta de P3 mediante imports, sin modificar su significado ni archivos. `scripts/validate_business_contracts.py` lee entradas y política de operador; no escribe archivos, ejecuta herramientas ni crea directorios de producto.

```sh
python3 -B scripts/validate_business_contracts.py
python3 -B scripts/validate_business_contracts.py --pilot config/business/internal-requests-pilot --plan
```

Salida por defecto: contracts=valid y planHash, **execution=BLOCKED; futureGates=NOT_IMPLEMENTED**. Código 0 significa solo validación contractual; código 2 significa contrato/lectura/autorización inválidos. --plan emite JSON por stdout, sin renderizar producto. No hay flags para infraestructura, secretos, migrar, bootstrap o materializar.

Ejemplo aceptado: `config/business/internal-requests-pilot/` contiene spec.json, catalog.json, environment.json y work-order.json. `config/business/authorization.json` es la política **externa al bundle** bajo autoridad del operador, con hash exacto del WorkOrder. Modificar/recalcular hashes dentro del bundle no concede autorización. No hay acciones P3 válidas para P4; las únicas acciones actuales son validate-contracts y plan-contracts con scope P4.2-contracts-only, execution=forbidden. Los valores no se incluyen en mensajes de error, incluso si un error del validador compartido pudiera imprimirlos.

## Schemas y semántica

| Schema implementado | Responsabilidad |
|---|---|
| business-platform.v0.1.0 | productId/capability, core objetivo 0.1.0, módulo/version, marca pública mínima, auth/policy/persistencia/targets/restricciones exactos |
| business-module.v1 | Descriptor de módulo: compatibilidad, grafo, conflictos, rutas/métodos, ownership de archivos, modelos/campos, permisos, intención de migración y gates |
| business-environment.v1 | Nombres/clasificación/consumidores/requisito obligatorio; sin valores, defaults o secretos |
| business-work-order.v1 | Hashes de spec/catalog/environment y scope/acciones contractuales explícitas |
| business-plan.v1 | Plan completo determinista, inputs por hash, core/spec/módulo/env/rutas/gates y bloqueo de ejecución |

Los JSON están exportados en schemas/ y se comparan con sus definiciones Python en tests. Usar validación semántica `build_plan` además de validación estructural: JSON Schema por sí solo no demuestra catálogo autorizado, ausencia de ciclos, hashes correctos o propiedad compatible. El core 0.1.0 es **versión objetivo del contrato**, no un core implementado/certificado. Next/App Router, Prisma major 7 y PostgreSQL major 16 son objetivos; exactCompatibility=PENDING_P4.3, sin versiones de Better Auth/adaptadores fijadas ni @latest.

El contrato fija deliberadamente el perfil MVP. Roles admin/member, member own-only, admin all-in-product, owner derivado de sesión, clientOwnerId/reasignación/edición de roles prohibidos, estados open/closed, archivedAt lógico, sin delete, denegación uniforme 404 y concurrencia expected-version-or-409. Auth: signup cerrado, bootstrap offline, sin defaultPassword, max 28800 segundos, sin rememberMe, logout revoca, sin OAuth/email/MFA/recuperación por email. Estas son **políticas declaradas**, enforcement=NOT_IMPLEMENTED.

Campos de InternalRequest: id identificador opaco servidor, title string 1–120, description string 0–2000, status enum, ownerId referencia desde sesión, fechas servidor, archivedAt nullable y version integer mínimo 1 con compare-and-increment. Se valida que no se alteren esos tipos/límites conceptuales; no se valida aún un payload HTTP ni se ejecuta semántica ORM/concurrencia.

Environment contiene exactamente DATABASE_URL y MIGRATION_DATABASE_URL como secretos con consumidores separados app/migration-tool, BETTER_AUTH_SECRET solo app, BETTER_AUTH_URL public-configurable y NODE_ENV private-runtime. El requisito secret no admite nombre NEXT_PUBLIC_*. No hay campo value/default en ninguno. No se guardan credenciales de ejemplo. Separación de DB/red/volumen/secreto/sesión por producto está declarada, todavía no demostrada.

La configuración pública tiene únicamente name/title/color, texto corto acotado y filtro adicional de indicadores sensibles; los demás contratos usan campos cerrados. Esto bloquea campos secretos, valores de env, metadata/receipts inyectados y patrones de secretos probados. **Ningún detector puede distinguir de forma absoluta una credencial arbitraria de un nombre inocuo**: evitar secretos desde el origen y revisión humana siguen siendo obligatorios; el filtro es secundario, no autorización para introducirlos.

## Catálogo y composición

Solo hay un descriptor productivo: internal-requests 0.1.0. Se verifica contra el descriptor MVP aprobado; no permite registrar módulos desde el brief. `validate_graph` separa la lógica de composición para probarla con fixtures sintéticas: módulos duplicados/desconocidos, dependencias ausentes/ciclos, conflictos, rutas duplicadas incluso con distinto nombre de parámetro, colisiones con rutas auth/core, rutas no canónicas, owners incompatibles, prefijos de archivos superpuestos, modelos duplicados y versión de core incompatible.

Las rutas `/requests`, `/requests/[id]`, `/api/requests`, `/api/requests/[id]` y ownership `src/modules/internal-requests`, `prisma/modules/internal-requests.prisma` son **destinos conceptuales previstos**, no archivos existentes. El último path no decide todavía composición física de Prisma: pertenece a P4.3. Los métodos son GET/POST/PATCH, sin DELETE. Las pruebas no amplían el catálogo ni crean módulos ficticios en producción. El grafo válido sintético también se rechaza como catálogo no aprobado.

## Plan determinista y contratos diferidos

[Plan real emitido](../migration/P4_2_PLAN.json): incluye spec/core, módulo completo, modelos/rutas/permisos, requisitos env y todos los gates futuros. outputsWritten=[] significa que **ningún archivo de producto fue escrito**, no que no exista este documento de evidencia.

Hash del plan: `sha256:6dd2027e5b74d65f3b1afe0eb1378ff6744112b8ff9bc789003fb852631d21cc`.

Hash del WorkOrder: `sha256:f6c5c445d0833a8259f038005e51cea1009ba5e28bc82816c5719353ee159015`.

Plan sin timestamps/UUID/paths privados. Dos ejecuciones con las mismas entradas producen bytes/hash iguales; tests también comparan archivos temporales independientes y el ejemplo registrado. Los hashes de spec/catalog/environment/order están en inputs. [Verificación y hashes](../migration/P4_2_VALIDATION.json).

Gates obligatorios todavía **NOT_IMPLEMENTED**: compatibility, database-migrations, authentication, resource-authorization, module-crud, generation, build-tests, autonomy y cleanup. Readiness permanece BLOCKED. No se permite sustituir el perfil por lista vacía ni introducir PASS.

Decisión de alcance: el gate profile ya está integrado en business-plan.v1. Se difieren **GenerationManifest, ProductMetadata v2 y ValidationReceipt ejecutado** hasta contar con renderer/archivos/ejecución reales. El plan lista estos contratos como diferidos; no emite metadata de un producto inexistente ni reutiliza recibos P3 para fingir pruebas P4. El source manifest y creation diff P3 no se duplican ni amplían: aquí no se consume una fuente externa de código ni se escribe staging de producto; su integración vendrá con generación. Ningún contrato corporate cambia.

## Pruebas y preservación

[Test cases](../../tests/test_business_contracts.py) contiene el ejemplo positivo, mutaciones parametrizadas y fixture `pair()` de grafo fuera del catálogo. Casos cubiertos: campos/versiones/roles/owner/estados inválidos, delete/reasignación, bool vs integer, público sensible, env con valor o consumidor erróneo, hash/grant/scope incorrectos, combinación no soportada, modelo alterado, grafo inválido y plan/CLI sin efectos. Los diagnósticos no incluyen marcadores sintéticos privados introducidos por tests.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest tests/test_business_contracts.py tests/test_p3_baseline.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q -p no:cacheprovider --tb=short
python3 -B scripts/validate_repository.py
```

La regresión final se ejecuta sin opt-in Docker: los casos Docker saltados quedan explícitos en [resultados](../migration/P4_2_TESTS.json), no se presentan como aprobados nuevamente. No se modificaron archivos protegidos del baseline, su JSON/hash, MIGRATION_PLAN.md, productos ni prototipo. No se instalaron dependencias ni se levantó servicio alguno.

## Incidencias y decisiones antes de P4.3

Durante construcción del módulo nuevo se corrigieron un import mal escrito y el uso de un helper string para declarar un booleano. Se añadió comparación de enum sensible al tipo JSON para impedir que false se confunda con 0 al comparar objetos fijos. Ninguna corrección afectó el validador P3 ni relajó sus pruebas.

Revisión requerida: aceptar los contratos declarativos y el aplazamiento explícito de contratos de ejecución/metadata; confirmar que P4.3 materializará el core y la compatibilidad antes de declarar gates cumplidos. Revisar el mecanismo offline de bootstrap en P4.4 sin asumir que Better Auth resuelve su atomicidad automáticamente. Toda futura extracción/cambio de helper protegido requiere identificar consumidores y aprobación de revisión de baseline; no existe esa autorización implícita en estos contratos.

P4.2 no incluye datos de negocio, persistencia, Route Handlers, Prisma schema, Compose, usuarios o producto. Trabajo detenido antes de P4.3.

Cierre de validación: **58 pruebas específicas/preservación aprobadas**; suite completa **227 aprobadas, 10 Docker NOT_EXECUTED** (sin opt-in, no infraestructura iniciada). Estructura/imports/enlaces correctos, plan idéntico por bytes/hash, ambos productos íntegros y fuente NexoNova verificada. El baseline original conserva sus 105 hashes y su SHA-256 sin cambios.
