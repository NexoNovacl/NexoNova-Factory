# D02 — Resolución controlada P4.5-B

Autorización humana: `APPROVED_FOR_CONTROLLED_RESOLUTION`, opción A, 2026-09-27.
La opción B no está autorizada. El diagnóstico original y el checkpoint bloqueado permanecen
intactos en `docs/migration/p4-5-b-runs/` y `d02-entry/`.

La composición del módulo se inicia con `node scripts/start-requests.mjs`. Es un launcher nuevo,
propio de P4.5-B, que usa la API pública de servidor Next y el servidor HTTP de Node. Invoca la
misma función aprobada `authEnvironment()` al arrancar. No reemplaza ni modifica
`templates/business-platform-auth/scripts/start.mjs`; tampoco modifica auth, dependencias,
configuración Next ni prototipos globales.

`requests-response-boundary.mjs` se aplica únicamente a `/requests`, `/requests/...`,
`/api/requests` y `/api/requests/...`, incluidos sus equivalentes codificados. Antes de emitir
los headers de esa respuesta, une los tokens de Vary sin duplicados case-insensitive y agrega
Cookie. Conserva los tokens generados por Next y establece Cache-Control: no-store. Un Vary
wildcard no se convierte silenciosamente en una lista de campos. La frontera no autentica ni
autoriza; esas comprobaciones siguen en servicios/handlers. No modifica el body, status ni
routing. Las rutas ajenas pasan directamente a Next sin instalar esa frontera en su respuesta.

La instancia HTTP recibe sus propios handlers de SIGINT/SIGTERM, espera cierre y tiene timeout
de diez segundos. El launcher no ejecuta migraciones ni bootstrap, y no instala paquetes.
El producto con este módulo debe utilizar este launcher; usar el launcher auth original omite
la solución D02. Esto debe conservarse como parte de su composición validada, no como una
configuración opcional para producción. No se realizó deployment ni generación Factory.

Validación prioritaria: comparar el launcher nuevo y el original sobre PostgreSQL real y la
misma composición, incluyendo member/admin, HTML/RSC, éxito/error, no-store, igualdad de todos
los tokens Next más Cookie exactamente una vez y rutas auth/login ajenas sin cambio de headers.
El receipt `p45b-a8da2f074f8349f8.json` demuestra ese bloque HTTP. La matriz integrada y navegador
se completan con receipts posteriores; el bloque aislado no otorga por sí solo PASS a C28.

No implica compatibilidad automática con otras versiones de Next, hosting administrado,
standalone output ni proxies/CDN externos. Cualquier cambio de versión o entrada de arranque
requiere repetir la comparación de headers, SSR/RSC, navegación y regresión auth.
