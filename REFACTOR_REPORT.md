# Estado vigente — P4.1 documental, 2026-09-15

P3.7 y P3 cerrados y aprobados formalmente PASS_WITH_LIMITATIONS para uso interno/controlado. Baseline P3 original preservado sin actualizar hashes. Solo P4.1 autorizada: [auditoría y arquitectura propuesta business-platform](docs/business-platform/P4_1_PROPOSAL.md), [registro/validación](docs/migration/P4.md). No hay implementación P4 ni inicio P4.2. Derechos, publicación, deployment y material pendiente no aprobados por este cambio de fase.

Los encabezados siguientes conservan el historial de entregas; su estado de aprobación previo no sustituye este registro.

# Estado consolidado al cierre técnico P3 — 2026-09-12

**P3 PASS_WITH_LIMITATIONS; aprobación humana de P3.7 pendiente.** P3.1–P3.6 aprobadas. corporate-site es capacidad de piloto validada de uso interno/controlado, no production-ready. [Informe final y matriz](docs/migration/P3_FINAL_REPORT.md), [uso](docs/corporate-site-operator.md), [baseline](docs/migration/P3_BASELINE.json).

P3.7 reutiliza sin cambios template, generador y ambos productos. Añade comprobación real de autonomía en Docker sin Python/material privado, guía operativa, baseline de 105 archivos y test de preservación. Actualiza README/arquitectura/estado. No reemplaza ni elimina fuentes; no modifica prototipo ni añade funcionalidades de producto. Limitaciones y decisiones de publicación consolidadas en el informe final. P4–P7 no iniciadas.

Los registros siguientes son historia de entregas anteriores; sus estados pendientes no sustituyen este encabezado.

Estado vigente: P3.5 aprobado formalmente; P3.6 demuestra el segundo producto synthetic-website y queda para revisión humana. [Registro P3.6](docs/migration/P3_6.md). P3.7 no iniciada. Los estados siguientes son históricos.

Revisión puntual 2026-09-12: header correcto en producto y template; evidencia fullPage histórica afectada por scroll previo. [Causa y capturas limpias](docs/migration/P3_5_HEADER_REVIEW.md). Sin modificaciones de código ni avance a P3.6.

Estado vigente P3.5 (2026-09-11): P3.1–P3.4 aprobadas. Generador determinista implementado y `../nexonova-website` materializado; evidencia y límites en [P3.5](docs/migration/P3_5.md). P3.6 no iniciada. Las entregas anteriores que se conservan abajo son históricas.

# REFACTOR_REPORT — Entrega incremental parcial

Inicio: 2026-09-06. Actualización: 2026-09-11. **P2 PASS_WITH_LIMITATIONS aprobado por el usuario.** Carpetas normalizadas; P3.1 y P3.2 aprobadas. P3.3 aprobada. Interacciones locales P3.4 implementadas para revisión; P3.5 no iniciada. No se ha generado nexonova-website ni completado P3.

## Resultado

P0/P1 preservan su estado. P2 cuenta con aprobación humana explícita y límites aceptados. El usuario aprobó el piloto corporate-site con prototipo preservado, brief y selección separada, demostraciones locales y reconstrucción selectiva. Esta entrega se limita al renombrado, manifiesto de 99 archivos y contratos versionados de preparación. Véase [P3](docs/migration/P3.md). No hay plantilla, frontend, proveedor externo ni producto ejecutable nuevo. P4–P7 no se iniciaron.

No se cambiaron secretos, infraestructura externa o datos productivos; no se desplegó ni se ejecutaron migraciones de BD. No se inicializó Git ni se movió el historial/ERP. AGENTS.md y los tres documentos aprobados permanecen íntegros.

## Qué se reutilizó

- Paquete Python y CLI, secuencia OrchestratorGraph → HarnessRunner.
- Contratos WorkOrder/CycleState/AgentResult y dataclasses de registros.
- Decisiones de PolicyEngine, cadena de validadores y pruebas negativas útiles.
- Recuperación léxica, fuentes explícitas, hashing y logs JSONL.
- Material académico como referencia preservada, sin elevarlo a capacidad productiva.

## Qué se modificó

- Validación Docker P2: config/factory.json fija la imagen oficial Python por digest; no se modificó el runtime ni se redujeron políticas.

- P2/corrección: executor redacta valores delimitados completos, conserva evidencia parcial en checkpoints y persiste interrupciones antes de propagarlas; CLI añade código 130, --work-order, import-legacy-reference y recover-run. La política v2 invalida aprobaciones previas al cambio.

- tests/test_factory.py: aislamiento y comprobaciones semánticas; contexto sintético no vacío.
- factory/registry.py y harness.py: roles legacy bloqueados, rechazo de autorización pendiente y validación de resultados/rutas.
- factory/validators.py y schemas.py: evidencia resoluble, hashes del texto consumido, gates no implementados bloqueantes, límites numéricos e IDs seguros.
- factory/orchestrator.py y cli.py: cierre real, código de salida, estado externo al checkout, UUID y CLI de workspace/herramientas.
- factory/context.py: fuentes configurables y snapshots sin sobrescritura.
- factory/memory.py y policy.py: memoria desactivada; aprobación del productor insuficiente.
- factory/utils.py: escritura atómica, hashes de bytes, rechazo de NaN, eliminación del shell innecesario en env_hash.
- factory/observability.py: estimaciones locales identificadas, sin atribuirlas a modelos.
- factory/__init__.py y constants.py: identidad y versión del runtime coherentes con el empaquetado.

## Qué se reemplazó

- Cierre y matriz de trazabilidad estáticos por reports basado en resultados y manifiesto.
- verify basado solo en existencia por lectura de integridad/estado coherente; runs legados no certificables conservados.
- Aprobación implícita de controles de calidad por bloqueo si no existe verificación real.
- Detección que equiparaba comando presente con capacidad lista por disponibilidad no acreditada explícita.

Los cuerpos de agents.py **no fueron reescritos todavía**. Se impide ejecutarlos desde el harness; permanecen para revisión hasta que generadores reales sustituyan sus responsabilidades en P3. Esto evita una reescritura sin brief y no se presenta como generación implementada.

## Qué se eliminó

Ningún archivo fuente o legado. Se retiraron comportamientos de falsa aprobación, inicialización de memoria de fábrica al leer y contadores de allowlists como ejecución. Los cachés existentes permanecen ignorados; no se realizaron borrados cosméticos.

## Qué se creó

- P3.1/P3.2: product_contracts.py, schemas, registro de fuentes, contratos de dos pilotos, fixture sintética, validate_product_inputs.py y 25 pruebas nuevas; inventario y resultados en docs/migration/P3.md.

- Empaquetado: pyproject.toml, requirements-test.lock y exclusiones raíz.
- factory/reports.py: cierre y verificación de integridad.
- factory/storage.py: raíz privada por cliente, lock, UUID, aprobaciones y rutas acotadas.
- factory/config.py y config/factory.json: límites explícitos y ejecución desactivada sin imagen aprobada.
- factory/executor.py: adaptador experimental Docker local, snapshot filtrado, límites y resultados.
- tests/test_integrity.py y tests/test_storage.py: regresiones de evidencia y fronteras.
- tests/test_p2_validation.py: 15 comprobaciones de procesos, persistencia, escrituras y aprobaciones; las dos regresiones originales ahora pasan sin cambios.
- factory/execution_scope.py y state_transfer.py: restricciones WorkOrder, referencias portables y recuperación sin replay.
- tests/test_p2_fixes.py y test_p2_state.py: 22 casos adicionales de formatos de secretos, interrupción real, restricciones, referencia e interrupción/recuperación de estado.
- tests/test_p2_docker.py: 10 pruebas opt-in del executor con Docker real; registros sanitizados P2_DOCKER_RESULTS.json y P2_DOCKER_EVENTS.json.
- scripts/validate_repository.py: imports, estructura, enlaces, versiones y preservación de hashes.
- README.md, docs/architecture.md, docs/security.md, docs/maintenance.md, docs/deployment.md.
- Registros P0–P7, ajustes del plan, manifiesto de origen e inventario de cambios por hashes en docs/migration.

No se crearon carpetas vacías para templates, modules, prompts ni deployment. No hay nuevas dependencias runtime Python. pytest ya estaba requerido por las pruebas; setuptools se añadió únicamente para empaquetar. No se incorporó Bubblewrap como tecnología del producto.

## Validación

- P0 original: 9 pruebas aprobadas en copia temporal; 9 con aislamiento corregido.
- P1: 24 pruebas aprobadas.
- P2/cierre anterior: 58 pruebas aprobadas; evidencia histórica en [registro de cierre](docs/migration/FINAL_VALIDATION.md).
- P2/validación del 2026-09-08: 71 passed, 2 failed (histórico).
- P2/corrección del 2026-09-09: 95 passed; código 0. Redacción corregida y SIGINT con evidencia parcial redactada, estado terminal y CLI 130. Se verificó una referencia temporal a 128 archivos del legado real, sin cambiar su hash. Imports/estructura/hashes protegidos y arranque CLI pasan. Comandos y límites en [P2_FINAL_VALIDATION](docs/migration/P2_FINAL_VALIDATION.md).
- P2/Docker: 10 passed; test_p2_validation: 15 passed; fixes/state: 22 passed; suite completa con Docker: **105 passed en 12.37 s**, cero skips/xfails. Estructura/imports y CLI correctos.
- Daemon/cliente Docker 29.8.0, socket local unix:///var/run/docker.sock, Compose 5.5.1 (no requerido por el adaptador). Imagen oficial python:3.12-slim fijada a `python@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea`.
- 30 contenedores de diagnóstico/repeticiones registrados por eventos: todos destruidos, cero contenedores restantes y cero directorios temporales del cliente Docker. Tras crash la limpieza fue explícita, no atribuida a recover-run.
- CLI sigue iniciando; bootstrap legado devuelve fallo explícito, no éxito artificial.
- Empaquetado wheel probado sin dependencias runtime; comprobación instalada y validación estructural registradas al cierre.
- Los tests host siguen sin acreditar Docker por sí solos; la evidencia de contención ahora procede de tests/test_p2_docker.py con contenedores reales, sin mocks de transporte.
- No hay tests de aplicaciones web, E2E, BD ni despliegue porque esas capacidades no existen aún.

## Deuda técnica restante

Contratos aún contienen nombres y campos académicos; funciones legadas inactivas permanecen. El importador versionado de referencias ya existe y se probó con el legado, pero su ubicación privada definitiva sigue sin elegirse. La recuperación cierra runs sin repetir efectos; la reanudación automática, retención/backup y más herramientas quedan pendientes. El lock de tests fija versiones pero no hashes ni todas las plataformas. Falta una matriz de Python y CI. No se ha recuperado Git ni confirmado procedencia completa. Tras reiniciar el entorno se perdió el baseline temporal de código: existe inventario de hashes, pero la reversión exacta al código inicial exige recuperar originales. Se creó un checkpoint local del estado actual, sin presentarlo como baseline histórico.

## Riesgos pendientes

Las dos regresiones conocidas están corregidas y Docker fue validado localmente. El acceso desde el sandbox se bloqueó; las pruebas se ejecutaron con autorización fuera de él, conservando todas las restricciones del contenedor. La preparación descargó la imagen oficial sin credenciales; un fallo DNS inicial se resolvió en el segundo intento, sin cambiar servicios. El executor mantiene --pull=never, sin red ni puertos.

El usuario aprobó P2 y autorizó P3 por etapas; la aceptación no habilita producción ni fases posteriores. Tras SIGKILL puede quedar un contenedor y temporales: recover-run conserva incertidumbre y no repite herramientas; la prueba demostró inspección/limpieza explícita. La redacción sigue siendo heurística. CPU/memoria/PIDs se verificaron en HostConfig y cgroups, sin provocar OOM/saturación; el límite de archivo y noexec se ejercitaron realmente. No se validaron otras plataformas ni CVEs de imagen, SIGTERM o cortes eléctricos. La cuenta host/daemon se consideran confiables; los manifiestos no están firmados y la salida de unittest no certifica tests maliciosos. La aprobación P2 fue concedida; P3.1/P3.2 fueron aprobadas; P3.3 fue aprobada; P3.4 requiere revisión antes de P3.5.

## Funcionalidades todavía no implementadas

Generación Next.js, templates corporativa/business-platform, módulos, Better Auth/Prisma/PostgreSQL, actualización de proyectos, bug-fix automatizado, agentes con modelos, pipelines de producto, contenedores de entrega/Nginx/TLS, preparación de despliegue y operación/restauración de productos. No se atribuye avance funcional a P3–P7 por tener documentos de estado.

## Pasos recomendados hacia v0.2

1. Revisar P3.4 y su flujo local antes de P3.5. Material dudoso permanece excluido; Inter local y contenido definitivo siguen pendientes para su incorporación. Mantener las limitaciones P2 aceptadas y no publicar sin resolver Git/procedencia cuando corresponda.
2. Recuperar el repositorio Git real y resolver procedencia antes de publicar.
3. Implementar corporate-site con manifest, versiones y build/tests independientes de la fábrica.
4. Continuar business-platform y módulos con consumidor real, luego mantenimiento; integrar IA solo donde aporte valor.
5. Preparar entrega únicamente cuando exista producto validado, respetando los gates humanos del plan.

Esta entrega se detiene para revisión de lo construido y resolución de precondiciones. No se declara completado MIGRATION_PLAN.md ni se solicita volver a aprobar la autorización general ya concedida.

## Normalización y contratos P3

Factory: nexonova-factory. Fuente autorizada: nexonova-prototype (raíz hermana configurada relativamente). Producto futuro: nexonova-website, todavía inexistente. Los 99 archivos de la fuente conservan sus hashes. Sin cambios en el prototipo, dependencias nuevas ni contratos P2. Preparación válida no implica material aprobado: --require-ready bloquea correctamente. Evidencia final en [P3_VALIDATION.json](docs/migration/P3_VALIDATION.json).


## Cierre P3.1/P3.2 — 2026-09-11

133 pruebas aprobadas con Docker habilitado; estructura, imports, enlaces y CLI validados; cero contenedores temporales restantes. Los 99 archivos coinciden con el snapshot preservado. Se corrigió una carrera de confirmación de limpieza del executor sin relajar restricciones ni tests; política docker-unittest.v3, tres regresiones nuevas. Fallo inicial y resultado final preservados en [el registro P3](docs/migration/P3.md).

P3.1/P3.2 completas para revisión; P3 sigue parcial. Ambos pilotos validan sus contratos y fuentes. Material/procedencia, recursos ausentes, tipografía y contenido siguen pendientes. No existe nexonova-website ni se ha iniciado P3.3/P4–P7. Se requiere revisión humana antes de continuar.


## P3.3 — Base visual

Se creó templates/corporate-site con layout, tokens, componentes React propios y CSS Modules; contenido/configuración separado. Se reutilizaron referencias de paleta, composición y estilos del prototipo sin ejecutar/copiar sus scripts ni assets dudosos. No se sustituyó ni modificó runtime Python. No se implementó generador ni interacciones demo. Inventario, diferencias visuales, dependencias y evidencia en [P3_3.md](docs/migration/P3_3.md).

Las menciones previas de P3.1/P3.2 pendientes o P3.3 no iniciada documentan entregas anteriores. El usuario aprobó las precondiciones con omisión de material dudoso y fallback tipográfico. La siguiente autorización necesaria es P3.4, después de revisión humana de esta base. No hay aprobación productiva.

Validación final P3.3: 136 pruebas de fábrica aprobadas; ambas configuraciones pasan npm ci, typecheck y build, 2 pruebas de contenido por configuración y 3 pruebas de navegador por configuración. Capturas desktop/móvil conservadas. El prototipo se verifica contra sus 99 hashes. No se certifica equivalencia visual completa ni auditoría WCAG; revisión humana pendiente.


## P3.4 — Interacciones locales

Se reutilizan layout/tokens/componentes visuales aprobados. Se conectan selección de plan/servicios/dominio, Tu consulta y preparación/copia mediante InquiryProvider. ChatService separa respuestas locales de UI; diálogo con foco, Escape y accesos a secciones. Sin nuevas dependencias, endpoints, almacenamiento persistente o cambios al prototipo. Inventario, errores y evidencia en [P3_4.md](docs/migration/P3_4.md). Se requiere revisión humana antes de P3.5; los estados anteriores son históricos. No se ha cerrado P3 ni aprobado visualmente el producto final.

Cierre P3.4: ambos typechecks/builds aprobados, 32 casos de lógica + 14 de navegador + 4 de contenido aprobados; suite de fábrica 136 aprobadas. Se corrigieron foco cíclico, interacción sin JavaScript y desplazamiento del chat, conservando evidencia de los intentos. Capturas nuevas y límites en el registro P3.4. Prototipo intacto; sin P3.5, generador ni despliegue.
