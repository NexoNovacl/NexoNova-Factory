# Operación de corporate-site — piloto validado de uso controlado

El operador necesita Linux, Python para la fábrica, Docker local y la imagen Node aprobada ya preparada. Los productos solo necesitan Node/npm. Esta guía describe la implementación existente; no autoriza nuevos clientes, descargas, destinos o publicación por sí misma. Estado y límites: [cierre P3](migration/P3_FINAL_REPORT.md).

## 1. Preparar y autorizar entradas

Tomar como referencia config/pilots/nexonova o config/pilots/synthetic-generation. Preparar en un directorio nuevo de config/pilots los cinco archivos: corporate-site.json, source-manifest.json, visual-content.json, generation-selection.json y generation-work-order.json. Mantener versiones/estructura de schemas/ y restricciones vigentes. El project_id debe ser un slug nuevo, con destino inexistente bajo la raíz del operador. No cambiar el nombre de un producto existente para eludir una colisión.

La especificación define marca/servicios/planes; visual-content aporta contenido público coherente. Los planes pueden ser una lista vacía. La selección debe resolver cada decisión para el alcance y listar todas las fuentes omitidas; actualmente no se copian assets. No convertir materiales REVIEW en aprobados por inferencia. Registrar fuente y tree_hash en config/sources.json con acceso read-only. Nunca incluir secretos.

La orden v2 fija hashes SHA-256 canónicos de spec, source_manifest, public_config, selection y template. La función `factory.generation.digest` calcula esos hashes. Un operador autorizado revisa las entradas y registra el hash exacto de la orden en config/generation.json; los datos del cliente no pueden concederse permiso. Los scopes existentes son P3.5-internal-pilot y P3.6-internal-pilot; no representan autorización genérica para cualquier nuevo proyecto o fase. Un nuevo alcance requiere revisión explícita del contrato/política.

Antes de generar se pueden validar contratos v2 sin escribir:

```sh
python3 -B - <<'PY'
from pathlib import Path
from factory.generation import load_bundle, validate_inputs, configured_generator
root = Path.cwd()
bundle = load_bundle(root / 'config/pilots/synthetic-generation',
                     root / 'templates/corporate-site',
                     root / 'templates/corporate-site.manifest.json')
validate_inputs(bundle, configured_generator().allowed_orders)
print('generation_contracts=valid')
PY
```

Ese chequeo verifica inputs/hashes y template, no modifica el producto. La verificación de la fuente registrada se vuelve a ejecutar en stage. `scripts/validate_product_inputs.py --pilot config/pilots/synthetic` sigue siendo el validador de preparación **v1**; no confundir su autorización de inspección con generación v2.

## 2. Generar staging y revisar

Desde la raíz de fábrica, para un piloto autorizado cuyo destino aún no exista:

```sh
python3 -B scripts/generate_corporate_site.py stage --pilot synthetic-generation
python3 -B scripts/generate_corporate_site.py review --run generation-IDENTIFICADOR
```

Reemplazar generation-IDENTIFICADOR por el nombre real retornado por stage. Los dos pilotos actuales ya están materializados: repetir stage para ellos debe rechazar la colisión. No borrar ni sobrescribir productos para repetir estos ejemplos.

El staging está separado del checkout, bajo la raíz configurada. Revisar generation.json, diff.json y archivos reales de product. Solo se admite creación nueva. El manifiesto registra archivos, hashes, origen, omisiones y decisiones. Guardar el diffHash exacto; cambiar contenido/diff invalida esa revisión.

## 3. Validar antes de aceptar

El operador autoriza el stableHash concreto en config/web-tools.json tras revisar la propuesta; nunca autorizar automáticamente un hash aportado por el cliente. La imagen debe existir localmente con el digest fijado; no se descarga durante ejecución. Prepararla es una acción distinta que requiere autorización de operador.

```sh
python3 -B scripts/validate_generated_web.py --run generation-IDENTIFICADOR
```

Separa instalación preparatoria (npm ci con lock y sin scripts de instalación, única acción con red) de typecheck, tests de contenido y build sin red. No ejecuta comandos arbitrarios ni la suite de navegador: esta última se realiza explícitamente sobre código revisado. Revisar web-result.json, resultados, identidad del contenido y limpieza. Un fallo bloquea materialización.

## 4. Materializar o descartar

```sh
python3 -B scripts/generate_corporate_site.py materialize --run generation-IDENTIFICADOR --diff-hash sha256:HASH_REAL_REVISADO
```

No copiar literalmente el placeholder. Exige diff correcto, recibo web exitoso para el mismo contenido y destino todavía inexistente. Usa renameat2 sin reemplazo y requiere mismo filesystem. No hay --force ni modo de actualizar productos existentes.

Antes de materializar, un staging reconocido e íntegro puede descartarse con:

```sh
python3 -B scripts/generate_corporate_site.py discard --run generation-IDENTIFICADOR
```

Si está incompleto, alterado o ya materializado, inspeccionar manualmente; no usar borrados generales ni replay tras crash. Conservar los registros de materialización como evidencia intencional.

## 5. Verificar producto

Revalidación web en copia descartable del producto materializado:

```sh
python3 -B scripts/validate_generated_web.py --run generation-IDENTIFICADOR --materialized
```

Chequeo de integridad existente, sin inventar una CLI adicional:

```sh
python3 -B - <<'PY'
from pathlib import Path
from factory.generation import read_json
from factory.product_integrity import validate_product_integrity
root = Path.cwd()
manifest = read_json(root / 'docs/migration/P3_6_GENERATION_MANIFEST.json')
print(validate_product_integrity(root.parent / 'synthetic-website', manifest,
      [root, root.parent / 'nexonova-prototype']))
PY
```

El manifiesto anterior es el del piloto sintético real; utilizar el registro correspondiente para otro producto. Se comparan fuentes contra baseline; la forma conocida regenerada de next-env.d.ts se informa aparte. Dependencias/builds no forman parte del hash fuente determinista.

Desde la carpeta del producto, independientemente de la fábrica:

```sh
npm ci --ignore-scripts --no-audit --no-fund
npm run typecheck
npm test
npm run build
npm run test:browser
npm start -- --port 3185
```

Node 22 y el navegador Chromium compatible con Playwright deben estar previamente preparados por un operador; no se descargan por implicación de esta guía. Las pruebas de navegador usan el puerto local 3183 y requieren que esté libre; cerrar el servidor interactivo al terminar. No utilizar esto como receta de producción. Las capturas de carga inicial deben usar contexto nuevo, scrollY=0 y geometría estable antes de interacciones.

## Baseline y cambios posteriores

[P3_BASELINE.json](migration/P3_BASELINE.json) fija hashes del núcleo pertinente, template, schemas, políticas, contratos y evidencia de cierre. El test tests/test_p3_baseline.py detecta cambios de los archivos fijados. No es firma, historial Git ni defensa contra un operador que altere baseline y código simultáneamente. Antes de P4/P5, revisar diferencias, conservar este baseline como evidencia y autorizar explícitamente una nueva revisión; no actualizar hashes solo para silenciar un fallo.
