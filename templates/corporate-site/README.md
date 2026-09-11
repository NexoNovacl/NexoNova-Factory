# Corporate-site — base visual v0.1.0

Aplicación Next.js App Router, TypeScript y CSS Modules. La configuración pública de ejemplo es sintética: src/content/site.json. Los componentes reciben SiteContent y no importan la fábrica. No contiene precios comerciales generales, imágenes, fuentes descargadas ni secretos.

Node 22 (probado 22.22.1), npm 9 (probado 9.2.0):

```sh
npm ci --ignore-scripts --no-audit --no-fund
npm run typecheck
npm test
NEXT_TELEMETRY_DISABLED=1 npm run build
npm start
```

start/dev escuchan solo en 127.0.0.1. La instalación es preparación con acceso al registro público; no forma parte del executor P2. P3.4 añade interacciones locales conectadas por InquiryProvider: formato de dominio, selección de intereses, preparación/copia y chat determinista. No hay envío ni contratación. FAQ y navegación usan HTML nativo; el chat usa dialog modal con teclado/foco. CSP impide envíos nativos.

Inter es referencia; sin archivo local autorizado se usa fallback del sistema mediante --font-sans. Los colores vienen de configuración. No se incluye ningún asset de procedencia pendiente. Esta base requiere revisión humana y no certifica fidelidad visual final, accesibilidad completa ni preparación productiva.

El lockfile fija dependencias e integridad. Next 15 se conserva respecto del origen, con revisión de parches; React/ReactDOM y TypeScript se necesitan para el stack aprobado. Tipos son herramientas de desarrollo. No hay biblioteca UI, auth, BD o API.

Pruebas de navegador (preparación separada; no instala paquetes del sistema):

```sh
npx --no-install playwright install chromium --only-shell
NEXT_TELEMETRY_DISABLED=1 npm run test:browser
```

Puede configurarse TMPDIR y PLAYWRIGHT_BROWSERS_PATH a un directorio temporal propio con espacio suficiente. Playwright es solo dependencia de desarrollo. Su servidor usa 127.0.0.1:3183 y se detiene al terminar las pruebas. No se admite reutilizar un servidor ajeno para aprobar la prueba.

La selección, campos e historial viven en memoria y se pierden al recargar. Copiar escribe explícitamente al portapapeles del sistema; si no está permitido, se ofrece selección manual. Cambiar campos/intereses invalida la vista previa. No se utiliza localStorage, API ni SDK. ChatService permite sustituir el servicio bajo una autorización futura; solo se incluye createLocalChat.
