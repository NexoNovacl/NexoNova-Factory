# Cierre P3 — corporate-site

2026-09-12. **Resultado técnico: P3 PASS_WITH_LIMITATIONS.** `corporate-site = validated pilot capability` para uso interno/controlado dentro de los contratos y límites aquí descritos. **P3.7 y el cierre conjunto requieren aprobación humana**, todavía no otorgada. No significa production-ready, aprobación visual final ni permiso de publicación.

## Matriz consolidada P3.1–P3.7

| Etapa | Objetivo | Evidencia | Resultado técnico | Limitaciones | Aprobación humana existente |
|---|---|---|---|---|---|
| P3.1 | Congelar fuente y selección | [P3](P3.md), [fuente](../../config/pilots/nexonova/source-manifest.json), [renombrado](RENAME_VALIDATION.json) | 99 archivos preservados y verificados | Snapshot por hash, no backup ni derechos acreditados de todo material | Sí: aprobación explícita P3.1/P3.2 en conversación |
| P3.2 | Contratos versionados | [P3](P3.md), [validación](P3_VALIDATION.json), schemas y tests de contratos | Contratos estrictos y fuente autorizada | Preparación v1 no autoriza generación; v2 posterior fija alcance/hash | Sí: aprobación explícita antes de P3.3 |
| P3.3 | Base visual reutilizable | [P3.3](P3_3.md), [validación](P3_3_VALIDATION.json) | Next App Router, TypeScript, React, CSS Modules y tokens | Recursos omitidos, Inter fallback; fidelidad general, no visual final | Sí: base técnica/composición aprobadas antes de P3.4 |
| P3.4 | Flujo local integrado | [P3.4](P3_4.md), [resultados](P3_4_VALIDATION.json) | Dominios sintácticos, chat determinista, consulta y copia, memoria | Sin envío/integraciones, sin persistencia | Sí: flujo y validaciones aprobados antes de P3.5 |
| P3.5 | Generación real independiente | [P3.5](P3_5.md), [manifiesto](P3_5_GENERATION_MANIFEST.json), [reproducción](P3_5_REPRODUCIBILITY.json), [header](P3_5_HEADER_REVIEW.md) | Staging/diff, 31 archivos, materialización sin reemplazo, NexoNova independiente | Linux/mismo filesystem; recuperación manual; capturas antiguas postscroll sustituidas como referencia inicial | Sí: aprobación formal y capturas limpias aceptadas antes de P3.6 |
| P3.6 | Segundo producto y generalidad | [P3.6](P3_6.md), [comparación](P3_6_COMPARISON.json), [contaminación](P3_6_CONTAMINATION.json) | Segundo producto generado, sin filtración, reproducible; planes/sin planes | Dos configuraciones; colores secundarios compartidos | Sí: aprobación formal en solicitud de P3.7, límites aceptados |
| P3.7 | Autonomía, regresión, documentación y baseline | [Autonomía](P3_7_AUTONOMY.json), [pruebas](P3_7_TESTS.json), [cierre](P3_7_FINAL_CHECKS.json), [baseline](P3_BASELINE.json) | Consolidación y validación final para revisión | No equivale a release público; pendientes siguientes | **Pendiente: solo ejecución de P3.7 autorizada** |

Los documentos históricos conservan el estado de su entrega; las aprobaciones posteriores están registradas en esta matriz a partir de mensajes explícitos del usuario, no de firmas ni de valores autoaprobados en archivos.

## Criterios de salida de MIGRATION_PLAN.md

| Criterio obligatorio P3 | Evaluación |
|---|---|
| Dos configuraciones producen diferencias esperadas sin filtraciones | Verificado P3.6: 27 archivos compartidos, tres de configuración y una metadata distinta; detector con inyecciones negativas y navegador para ambos. |
| Mismas entradas/versiones → mismo contenido estable | Dos generaciones independientes por producto, comparación de bytes/hashes. Los nombres del staging y recibos operativos quedan fuera del producto. |
| Rechazo de sobrescritura no acordada | Tests de archivos/directorios existentes, colisiones/rutas/enlaces y renameat2 sin reemplazo; no hay --force. |
| Producto construye y funciona independientemente | P3.7 instala/construye/arranca copias exactas sin metadata privada, sin Python y sin montar fábrica/prototipo/staging. Los proyectos son directorios independientes; no se afirma haber recuperado/inicializado repositorios Git. |
| Reportes prueban ejecución real | Recibos con comandos, códigos, imágenes/contenedores y limpieza; mocks de gates separados de experimentos reales. |
| UI cumple criterios acordados | P3.3/P3.4 aprobados para alcance funcional/composición; P3.6 verifica ambos, P3.5 header limpio confirmado. Aprobación visual pública final sigue pendiente y no se sustituye por tests. |
| Fallo de build impide aceptación | Materialize exige recibo completo y mismo hash, incluye build; tests negativos de validación fallida y controles de integridad conservados. |

El brief/prototipo NexoNova más brief sintético sustituyen el caso inicial puramente ficticio según el ajuste explícitamente aprobado. CLI separado de generación es la implementación incremental autorizada; no reactiva agentes académicos. No hay GitLab/pipeline externo: el plan lo condicionó a un repositorio autorizado, todavía ausente.

## Productos y autonomía final

- `/home/germanleiks/NexoNova/nexonova-website`: piloto de NexoNova, con planes provisionales.
- `/home/germanleiks/NexoNova/synthetic-website`: Taller Sintético Arcilla, sin planes.

Ambos conservan sus fuentes y metadata portable. En P3.7 se copiaron únicamente archivos fuente enumerados por sus manifiestos a temporales nuevos; se excluyó `.nexonova` y se normalizó en la copia el bootstrap de next-env.d.ts según baseline conocido. No se copiaron node_modules, builds ni cachés.

Se ejecutaron npm ci con lock y sin lifecycle scripts, typecheck, tests de contenido y build por producto. El arranque posterior usó la misma imagen Node fijada, network=none y un único montaje del producto descartable en /work: sin fábrica, prototipo, WorkOrders, staging ni metadata. El proceso comprobó ausencia de esos directorios y que python/python3 no existían; levantó Next en loopback interno y verificó HTTP 200, identidad/contenido correcto y recursos locales referenciados por el HTML. Ningún puerto fue publicado. El servidor se detuvo y el contenedor se eliminó.

El experimento se implementa en [P3_7_AUTONOMY_CHECK.py](P3_7_AUTONOMY_CHECK.py), ejecutable por operador con `python3 -B docs/migration/P3_7_AUTONOMY_CHECK.py`. Python prepara la comprobación en el host, **no está disponible ni requerido por el producto dentro del contenedor**. No se añade un comando arbitrario al executor ni se declara soporte Docker de navegador.

La instalación requiere el registro público npm durante preparación; el runtime y build no tienen red externa. Independencia de la fábrica no significa instalación offline. La evidencia de navegador P3.6 —23 tests por producto más seis escenarios de generalidad/capturas limpias— sigue vigente porque template y fuentes de aplicación no cambiaron. No se repite esa suite de navegador en P3.7: se revalida el entorno limpio y el arranque aislado que faltaban, además de la regresión completa de fábrica.

## Versiones y baseline

| Componente | Versión/identidad |
|---|---|
| Factory Python | 0.1.0 |
| Generator | Integrado en factory 0.1.0; sin versión semántica independiente. Hash de generation.py y dependencias en baseline final |
| Template corporate-site | 0.1.0; inventario nexonova.template.v1 |
| Especificación | nexonova.corporate-site.v0.1.0 |
| WorkOrder producto | v1 preparación; v2 generación P3.5/P3.6; WorkOrders P2 preservados |
| Fuente/selección | nexonova.source-manifest.v1 / nexonova.generation-selection.v1 |
| Configuración pública | corporate-site.visual.v1 |
| Metadata producto / baseline producto | nexonova.project.v1 / nexonova.baseline.v1 |
| Manifiesto generación / diff | nexonova.generation.v1 / nexonova.creation-diff.v1 |
| Stack web | Next 15.5.25, React 19.2.8, TypeScript 5.9.3, Playwright 1.63.0 |
| Node aislado | 22.23.2, digest en recibos/autonomía |

[P3_BASELINE.json](P3_BASELINE.json) registra archivos críticos por SHA-256, inventario del template y hashes estables de ambos productos. El test test_p3_baseline.py falla si se altera un archivo fijado o el inventario del template. No cubre modificaciones arbitrarias de archivos ajenos al inventario. No es firma criptográfica ni protege de quien modifica baseline y código a la vez. P4/P5 deben revisar cambios, preservar esta evidencia y autorizar una nueva revisión; actualizar hashes a ciegas anula su propósito.

Next regenera next-env.d.ts durante el build; se informa la forma exacta conocida separada del baseline inicial. node_modules, .next y resultados de pruebas son derivados, no parte de la reproducibilidad de fuentes. No se promete build binario idéntico ni cadena de suministro auditada.

## Limitaciones clasificadas

| Limitación | Clasificación | Tratamiento |
|---|---|---|
| Procedencia/licencia del código original y assets no acreditados | **Blocker para publicación** cuando corresponda al material derivado | Resolver procedencia/Git y autorizar material antes de distribuir; REVIEW permanece excluido. |
| Contenido comercial, precios/garantías y aprobación visual final | **Blocker para publicación** | Piloto provisional; validación humana editorial/visual obligatoria. |
| Ausencia de receta operativa revisada y controles de release | **Blocker para publicación** | No existe autorización de exposición pública; revisar seguridad/operación en fase posterior. |
| Inter local no materializada | Deuda técnica | Se utiliza fallback sin descarga/runtime Google Fonts; incorporar solo material licenciado aprobado. |
| Recursos ausentes/assets omitidos | Deuda técnica del diseño | No referencias runtime rotas; no inventarlos. La ausencia no obliga a incorporarlos para publicar. |
| Linux y publicación en mismo filesystem | Deuda técnica/limitación de plataforma | renameat2 sin reemplazo; no se acredita portabilidad. |
| Crash/SIGKILL, daemon o corte eléctrico | Deuda técnica/limitación aceptada | Inspección/limpieza manual sin replay ni recuperación automática; host/daemon confiables. |
| Actualización automática/personalizaciones | Fuera de alcance P3 | Baseline permite comparar; mantenimiento seguro corresponde a P5. |
| Deployment, VPS, Nginx/TLS, GitLab CI externo | Fuera de alcance P3 | No servicios o infraestructura nuevos; P7 requiere autorización. |
| Auth/BD/business-platform | Fuera de alcance P3 | Sin dependencias nuevas anticipadas; P4 requiere brief/consumidor real. |
| WHOIS, IA externa, WHMCS, pagos, envío | Fuera de alcance P3 | Demos locales explícitas; ningún proveedor/credencial. |
| Navegador no integrado al adaptador Docker | Deuda técnica | Pruebas host de código revisado, aisladas lógicamente; no equivalen a sandbox de navegador. |
| Dos configuraciones, no personalización universal | Deuda técnica/límite aceptado | Composición concreta, planes opcionales; no se certifican variantes arbitrarias. |
| Colores secundarios compartidos | Deuda técnica/límite aceptado | Tres tokens de marca configurables, acentos/superficies compartidos. |
| Redacción heurística y mantenimiento de imagen/dependencias | Deuda técnica operativa | No sustituye evitar secretos ni revisión periódica de vulnerabilidades. |

No todos los pendientes bloquean el uso interno de esta capacidad. Los bloqueos de publicación se mantienen separados de los criterios funcionales del piloto.

## Seguridad, limpieza y cambios de cierre

[P3_7_FINAL_CHECKS.json](P3_7_FINAL_CHECKS.json) conserva inventario real de staging y recursos. Los dos directorios de runs materializados son evidencia intencional (manifiesto/diff/recibo/estado), no productos temporales abandonados. No se borran registros para aparentar limpieza. No se retiraron dependencias/builds de los productos: son artefactos locales de validación, no servidores activos.

P3.7 crea este informe, guía de operador, script/recibos del experimento de autonomía, baseline y test de preservación. Actualiza README, arquitectura, estado de migración y REFACTOR_REPORT. No cambia código funcional, template, configuración de productos, manifiestos originales ni prototipo. La suite Docker existente puede actualizar sus propios registros de ejecución. No se eliminan fuentes ni se amplían políticas.

## Recomendación

Aprobar o solicitar correcciones al cierre P3.7. Después, decidir un brief concreto para P4 (business-platform) conforme al orden del plan; no agregar auth/BD o módulos sin consumidor. Si la prioridad empresarial es mantener estos sitios, evaluar explícitamente la planificación de P5, sin interpretar este informe como autorización para saltar fases. Resolver procedencia y aprobación de publicación por separado. Trabajo detenido antes de P4–P7.

## Resultados finales ejecutados

- Suite completa de fábrica: **180 passed in 20.27s**, incluidos Docker P2 y el test nuevo de baseline; sin skips/xfails.
- Cada producto desde instalación limpia descartable: npm ci, typecheck, 2 tests de contenido y build aprobados. Node 22.23.2 en Docker 29.8.0 local; mismo digest Node autorizado en P3.5.
- Arranque autónomo por producto: HTTP 200, identidad correcta y ocho recursos locales del HTML servidos con HTTP 200; Python y metadata privada ausentes. No prueba navegador en contenedor: funcionalidad interactiva respaldada por P3.6 aprobado y hashes sin cambios.
- Integridad de ambos productos, configuración/contaminación, imports/enlaces y CLI correctos; 99 archivos del prototipo y fixture sintética verificados.
- Cero contenedores de prueba, cero listeners en 3183/3185/3187 y cero copias de autonomía restantes. Staging contiene solo generation-e3oc8qgy y generation-t500tk8w en estado materialized, sin subdirectorio product.
- Baseline de 105 archivos, template 0.1.0 preservado. No fallos nuevos encontrados durante el cierre.

No se repitieron las dos generaciones por producto: la evidencia byte a byte aprobada P3.5/P3.6 sigue siendo aplicable porque sus entradas, template y generador no cambiaron en P3.7. La suite final sí reejecuta sus pruebas de reproducibilidad y rechazo.
