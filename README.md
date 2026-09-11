# NexoNova Factory

Núcleo local en Python para evolucionar hacia una fábrica de software de NexoNova. **Estado actual: migración parcial y experimental. No genera todavía aplicaciones web ni está aprobado para producción.**

P0 estableció la línea base y P1 eliminó la aceptación del bootstrap documental como trabajo real. P2 incorpora almacenamiento privado y un adaptador validado con Docker real: PASS_WITH_LIMITATIONS aprobado por el usuario. P3.1 y P3.2 incorporan entradas preservadas y contratos versionados; aprobados por el usuario; la base visual P3.3 está aprobada y P3.4 añade interacciones locales para revisión. Consulte [el informe de cambios](REFACTOR_REPORT.md) y [el estado de las fases](docs/migration/README.md).

## Requisitos

- Linux y Python 3.11 o superior; esta entrega se probó con Python 3.14.4. El lock usa flock y el adaptador asume un socket Docker local de Linux.
- Runtime sin dependencias Python externas. pytest se usa solo para desarrollo; setuptools es el backend de empaquetado.
- Docker local e imagen oficial Python fijada por digest **solo para el adaptador experimental de procesos**. La imagen no se descarga automáticamente. No se implementa un fallback de ejecución en host.
- Los productos futuros seguirán el stack de [AGENTS.md](AGENTS.md). La base corporate-site usa Next.js; no incorpora autenticación, BD ni infraestructura de clientes.

## Desarrollo y pruebas

En un equipo con soporte de `venv` y `pip`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-test.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider
python3 -B scripts/validate_repository.py
```

El entorno de esta sesión no incluía pip/ensurepip: se utilizó `/tmp/nexonova-migration-venv` con descargas oficiales autorizadas. Al reiniciarse el entorno el 2026-09-07 se perdió esa ubicación y se recrearon las mismas dependencias en .venv, con pip oficial en .migration-tools (ambos ignorados). Esas ubicaciones auxiliares no son requisitos del runtime. Si falta ensurepip en tu equipo, prepara el soporte de entorno virtual antes de seguir los comandos. El lock fija versiones del entorno de desarrollo; aún no contiene hashes ni acredita compatibilidad multiplataforma.

## Operación local disponible

Crear un workspace **fuera del checkout**; el comando solo prepara estado y directorios:

```bash
python3 -B -m factory.cli init-workspace --root /tmp/nexonova-workspaces --client demo --project-id piloto
python3 -B -m factory.cli list
```

Vista previa del adaptador de pruebas, sin ejecutar procesos ni consumir aprobaciones:

```bash
python3 -B -m factory.cli run-tool --root /tmp/nexonova-workspaces --client demo --project-id piloto --tool python.unittest --config config/factory.json --dry-run
```

La vista previa devuelve `needs_user_input` y código 1 porque no acredita una prueba ejecutada. Sin Docker o imagen aprobada, la ejecución devuelve `not_answerable`. Ninguno de esos estados significa un test aprobado.

Para reproducir la validación, un operador debe disponer de Docker local y revisar una imagen `python@sha256:<digest real de 64 caracteres hexadecimales>` y guardarla en una configuración privada basada en `config/factory.json`. `approve-tool` requiere esa misma configuración y un actor host; la autorización se consume una vez y caduca. Véase [seguridad y límites](docs/security.md). No sustituir el digest por el ejemplo literal ni ejecutar clientes antes de la revisión humana de seguridad.

Los comandos `run` e `init-project` permanecen como compatibilidad diagnóstica. `run --project <directorio externo> --objective <texto>` devuelve un cierre bloqueado: los 13 agentes académicos no ejecutan sus reportes estáticos. `verify --run <directorio de run>` comprueba formato/integridad y no modifica evidencia. Un run académico sin manifiesto nuevo no se certifica como actual.

## Responsabilidades

- `factory/`: CLI, orquestador, contratos, políticas, validación, contexto, estado y executor.
- `config/factory.json`: configuración explícita sin secretos; memoria desactivada e imagen Docker experimental fijada por digest.
- `tests/`: regresiones del núcleo, evidencia y fronteras de almacenamiento/ejecución.
- `docs/migration/`: decisiones, resultados y bloqueos por fase.
- `project/`: snapshot académico preservado; no utilizarlo para nuevos clientes.

No se movieron ni eliminaron archivos legados. La ausencia de historial Git está documentada; no se ejecutó `git init`. Los tres documentos de auditoría de la raíz son snapshots previos aprobados, no descripciones del estado implementado. La descripción actual está en [docs/architecture.md](docs/architecture.md).

## Próximo paso

Revisar las interacciones P3.4 antes de autorizar P3.5. Las fases posteriores permanecen fuera del alcance actual. No se han realizado despliegues, cambios de servicios externos ni migraciones de datos.

## Preparación P3: entradas y contratos

La fábrica reside en nexonova-factory y la fuente preservada en la carpeta hermana nexonova-prototype. El registro config/sources.json usa rutas relativas al checkout. P2 está aprobado; P3.1/P3.2 están aprobadas y P3.3 incorpora templates/corporate-site. Todavía no existe nexonova-website ni se inicia P3.5.

Validar sin ejecutar el prototipo:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_product_inputs.py --pilot config/pilots/nexonova
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_product_inputs.py --pilot config/pilots/synthetic
```

Añadir --require-ready exige que el material esté aprobado: actualmente devuelve código 2 por decisiones pendientes. Detalles y archivos en [P3](docs/migration/P3.md). Abrir la nueva carpeta en el IDE; no existe alias operativo con el nombre anterior.

Base visual, instrucciones y límites: [P3.3](docs/migration/P3_3.md) y [README del template](templates/corporate-site/README.md).

Flujo local integrado y límites: [P3.4](docs/migration/P3_4.md).
