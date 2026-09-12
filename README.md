# NexoNova Factory

Fábrica local experimental en Python. **corporate-site es una capacidad de piloto validada para uso interno/controlado.** P3.1–P3.6 tienen aprobación humana; el cierre técnico **P3 PASS_WITH_LIMITATIONS** de P3.7 está pendiente de revisión humana. No está aprobada para producción pública. P4–P7 no se iniciaron.

Productos independientes materializados como carpetas hermanas: `../nexonova-website` y `../synthetic-website`. Comparten template/generador y usan configuraciones distintas; no necesitan Python, prototipo, WorkOrders ni runtime de la fábrica para funcionar.

- [Informe final P3 y matriz de etapas](docs/migration/P3_FINAL_REPORT.md).
- [Guía de operador: contratos → staging → diff → validación → materialización](docs/corporate-site-operator.md).
- [Arquitectura](docs/architecture.md), [estado de migración](docs/migration/README.md), [informe de cambios](REFACTOR_REPORT.md).

## Requisitos

La fábrica usa Linux y Python >=3.11, biblioteca estándar en runtime. pytest y setuptools corresponden al desarrollo/empaquetado. Staging/materialización utiliza flock y renameat2; destino y staging deben estar en el mismo filesystem.

Las herramientas restringidas requieren Docker **local**, imágenes ya disponibles y fijadas por digest, y autorización del contenido exacto. No hay fallback implícito a ejecución host. La preparación npm requiere red; typecheck/tests/build restringidos y el runtime demostrado funcionan sin red externa.

El producto usa Node 22, Next.js App Router, TypeScript, React, CSS Modules y componentes propios. Su README contiene los comandos independientes. Chromium para pruebas debe prepararse explícitamente; no se confunde su validación host con aislamiento Docker.

## Desarrollo

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-test.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q -p no:cacheprovider
python3 -B scripts/validate_repository.py
python3 -B -m factory.cli --help
```

Los tests Docker son opt-in con `NEXONOVA_TEST_DOCKER=1` y requieren el entorno local aprobado. Sin ese opt-in no constituyen evidencia de aislamiento. El baseline de P3 está fijado en docs/migration/P3_BASELINE.json; su test exige revisar cualquier modificación de archivos protegidos, no actualizar hashes automáticamente.

## Responsabilidades

- `factory/`: núcleo, contratos, políticas, almacenamiento por cliente, executor Python, generador determinista, herramientas Node y validación.
- `templates/corporate-site/`: base congelada, frontend y pruebas independientes.
- `config/` y `schemas/`: fuentes, contratos, selección pública y autorización de operador separadas.
- `scripts/`: CLIs explícitas de generación/validación; no ejecutan comandos arbitrarios del brief.
- `tests/`: regresiones, seguridad, generación, contaminación e integridad.
- `docs/migration/`: evidencia histórica y cierre; no requerida por el producto.
- `project/`: material académico preservado, no usar como producto cliente.

Los 13 agentes académicos no se reactivaron. Los comandos heredados de orquestación conservan diagnósticos/gates; no sustituyen al generador corporate-site. `MIGRATION_PLAN.md`, `CURRENT_ARCHITECTURE.md` y `TARGET_ARCHITECTURE.md` son documentos aprobados históricos preservados, no el estado vigente del código.

## Límites y siguiente paso

Pendientes: procedencia/Git y derechos de material derivado, contenido comercial y revisión visual final, Inter local, preparación de publicación y mantenimiento operativo. No hay actualización automática, deployment, auth/BD ni integraciones reales. Dominios/chat/contacto son demostraciones locales explícitas; ninguna consulta se envía.

Revisar **P3.7** antes de decidir el siguiente trabajo. Este repositorio no autoriza crear servicios externos, desplegar, usar secretos reales o avanzar automáticamente a otras fases.
