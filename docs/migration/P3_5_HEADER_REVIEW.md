# Revisión puntual del header P3.5 — 2026-09-12

**Resultado: defecto de preparación de la evidencia, no del header ni de la materialización.** P3.5 sigue pendiente de aprobación humana; P3.6 no iniciada.

## Causa y alcance

El test `tests/browser/visual.spec.ts` toma la captura fullPage después de enfocar y abrir un FAQ y, en móvil, abrir/cerrar el menú. El focus desplaza la página. No restablece scroll/foco antes de capturar; activa reducedMotion solo al final, cuando el scroll suave ya pudo comenzar. La posición depende del momento de captura. El test de interacciones también toma su captura flow después de navegar por secciones: es evidencia de interacción, no una carga limpia.

El header usa `position: sticky; top: 0; z-index: 5`. En una captura fullPage desde scroll previo, Chromium representa los elementos sticky/fixed dentro de las coordenadas de documento capturadas: la barra aparece atravesando contenido y deja su espacio de flujo arriba. El enlace fijo de salto y el launcher del chat también pueden aparecer desplazados. Esto no corresponde al viewport que ve el visitante. Se reprodujo el artefacto en producto y template sin cambiar CSS. El desplazamiento exacto de la captura histórica varía por el scroll suave y su momento; no se usa como comparación pixel a pixel determinista.

La geometría medida antes de capturar mantuvo el header en top=0/left=0 y en la capa superior. En escritorio, la secuencia histórica dejó scrollY=484 en el producto; la captura posterior pudo avanzar más. Las pruebas móviles de menú devolvieron scroll al inicio. No se encontró un offset o stacking context distinto introducido por el generador.

## Verificación real

Se inició el producto materializado con Next start en 127.0.0.1:3185, desde un contexto de Chromium nuevo por viewport. Se construyó una copia temporal del template actual con la misma configuración pública NexoNova y dependencias ya instaladas, y se ejecutó la misma revisión. No se instalaron dependencias ni se modificaron fuentes. Ambos servidores fueron detenidos; la copia temporal fue eliminada.

| Viewport | Header al cargar, ambos | Altura | Scroll explícito 600 px |
|---|---|---|---|
| 1440 × 960 | top 0, left 0, ancho 1440 | 81 px | top 0 |
| 390 × 960 | top 0, left 0, ancho 390 | 81 px | top 0 |
| 320 × 960 | top 0, left 0, ancho 320 | 122.34375 px | top 0 |

La mayor altura a 320 px se debe al wrap responsive del menú; ocurre en ambos y no es un desplazamiento. Sin overflow horizontal, errores JavaScript o solicitudes externas observadas. Recarga con scroll restaurado explícitamente a cero también correcta. Se inspeccionaron las capturas limpias y la reproducción del artefacto. La revisión no certifica todos los offsets de anclas ni accesibilidad/visual final del sitio.

Se compararon bytes de Navigation.tsx, Site.module.css, globals.css, layout.tsx y visual.spec.ts: idénticos entre template y producto. También se validaron el manifiesto completo del template y la integridad del producto, preservando la excepción declarada de next-env.d.ts generado por Next. La fuente autorizada del prototipo vuelve a validar sus hashes.

## Evidencia corregida

- Producto: [escritorio, viewport limpio](p3-5-header-evidence/product-clean-1440.png), [móvil 390](p3-5-header-evidence/product-clean-390.png), [móvil 320](p3-5-header-evidence/product-clean-320.png).
- Landing completa limpia: [1440](p3-5-header-evidence/product-landing-1440.png), [390](p3-5-header-evidence/product-landing-390.png), [320](p3-5-header-evidence/product-landing-320.png).
- Template: [escritorio](p3-5-header-evidence/template-clean-1440.png), [móvil](p3-5-header-evidence/template-clean-390.png).
- Reproducción del problema: [fullPage después de interacciones](p3-5-header-evidence/product-historical-1440.png), [viewport después de esa captura](p3-5-header-evidence/product-scrolled-viewport-1440.png).
- [Mediciones del producto](p3-5-header-evidence/product.json), [template](p3-5-header-evidence/template.json), [build/ejecución](p3-5-header-evidence/execution.json), [integridad y limpieza](p3-5-header-evidence/integrity.json).

Las capturas antiguas se conservan como historial; las nuevas sustituyen su uso como referencia de carga inicial. No se retocaron imágenes ni se ocultó el header.

## Archivos y pruebas

Creados: este informe, P3_5_HEADER_CHECK.mjs y p3-5-header-evidence (capturas y JSON). Actualizados: P3_5.md y REFACTOR_REPORT.md con esta aclaración. Sin cambios en template, producto, contratos, manifiestos, generador ni prototipo.

Se ejecutó build de la copia del template (incluye comprobación de tipos), seis escenarios de navegador —dos orígenes por tres viewports— con carga limpia, secuencia histórica, scroll y recarga; verificaciones de integridad y fuente. No se repitió la suite completa de 171 tests ni el build del producto porque no se modificó código; se sirvió su build existente. No se presenta la cifra anterior como una ejecución nueva.

El script de reproducción recibe proyecto con Playwright instalado, URL loopback, etiqueta y directorio existente de evidencia. Con el servidor local iniciado:

```sh
PLAYWRIGHT_BROWSERS_PATH=/var/tmp/nexonova-p33-browsers node docs/migration/P3_5_HEADER_CHECK.mjs "$PWD/../nexonova-website" http://127.0.0.1:3185 product /tmp/p35-header-evidence
```

La corrección mínima del procedimiento es capturar la landing desde contexto nuevo antes de interacciones, esperando fuentes y comprobando scrollY=0; para capturas posteriores, restaurar scroll instantáneo y esperar geometría estable. Este script conserva la reproducción histórica separada de la evidencia limpia. No se cambia el test congelado dentro del template en esta revisión: hacerlo requeriría versionar de nuevo esa entrada sin aportar un arreglo al sitio.

## Impacto y gate

**No afecta la validez del generador P3.5:** no existe diferencia de fuentes ni comportamiento exclusivo del producto. Sí limita el valor de las capturas históricas como evidencia visual de carga inicial, corregido con nuevas capturas. No se cambió sticky a fixed ni se aplicó un parche exclusivo al producto. Revisión humana pendiente; sin P3.6, despliegue ni aprobación visual final.
