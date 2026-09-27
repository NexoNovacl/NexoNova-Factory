# P4.6 — Diseño del inventario de generación/ejecución v1

**DESIGN_PROPOSED / pendiente revisión humana del detalle.** G01: **HUMAN_APPROVED /
ALTERNATIVE_A**. La aprobación resuelve la dirección contractual, no aprueba por inferencia
este schema ni autoriza implementación/materialización. Solo ejemplos en Markdown; no se han
creado schemas ejecutables, configs de producto ni generador.

## 1. Separación de contratos

Nuevo `nexonova.business-execution-inventory.v1` describe rutas/owners/orígenes/launcher de la
composición aprobada. Nuevo `nexonova.business-route-adaptation.v1` describe su vínculo con P4.2.
Ambos son datos deterministas, **executionAuthority=none**: no son WorkOrder, permiso ni receipt
que demuestre ejecución. No sustituyen ni reescriben business-plan.v1, spec, catálogo o authorization
P4.2. Generation manifest, metadata y validation receipt futuros los referenciarán por hash.

Política propuesta `p42-to-approved-runtime.v1`, perfil cerrado
`business-auth-internal-requests-0.1.0-d02`. No se deduce contenido runtime a partir de coreVersion
0.1.0 solamente: hashes de fuentes aprobadas identifican la composición exacta. Otro perfil,
versión, módulo o formato es BLOCKED hasta diseño/revisión, no fallback.

## 2. Reglas exactas de adaptación propuestas

1. Leer inputs como JSON UTF-8, rechazar claves duplicadas, propiedades desconocidas, valores no
   finitos y tipos incorrectos. Validar v1 histórico con su validador de solo lectura; no ejecutar
   el WorkOrder ni alterar gates/outputsWritten. Comprobar sus hashes usando su algoritmo histórico,
   no reutilizar el algoritmo nuevo para validar un digest antiguo.
2. Exigir formato plan v1 y `coreRoutes` exactamente `["/sign-in","/api/auth/[...all]"]`, core y
   módulo 0.1.0, rutas contractuales InternalRequest aprobadas y bindings a inputs especificados.
   Si se aporta otro plan válido pero con distinta selección/perfil, no adaptarlo implícitamente.
3. Verificar decisión G01 externa y hashes del core, módulo, receipt P4.5-B, Next config,
   despachadores, middleware, launcher y frontera. No confiar en un `approved:true` aportado por
   el generador. En ejecución futura deben vincularse a snapshot aprobado por operador.
4. Mapear `/sign-in` a **reserva histórica no materializable**; registrar `/login` como página
   real leída del core, no como rewrite ni equivalencia de URL. No generar `/sign-in`.
5. Retener el handler `/api/auth/[...all]`, reservar `/api/auth` para auth y registrar la allowlist
   exacta del dispatcher como operaciones hijas, no como tres nuevos Route Handlers.
6. Inventariar todos los archivos page/route del core y overlay y asignar owner + origen + hash
   + destino. Añadir `/`, `/login`, probes y rutas de requests: la lista P4.2 **no es exhaustiva**.
   Reconciliar descubrimiento, tabla esperada y ejemplo: igualdad de conjuntos y propiedades.
7. Registrar también fuentes de routing indirecto (next.config, middleware, launcher), assets y
   namespace framework. En este perfil no hay public assets ni aliases/rewrites añadidos.
   Un nuevo archivo de metadata HTTP o regla de routing invalida el inventario, aunque conserve
   los mismos 11 nombres. No analizar código desconocido como si fuera el core aprobado.
8. Validar conflictos antes de planificar escritura. Exigir startup específico y frontera D02.
   Construir el inventario sin copiar secretos ni convertir NOT_IMPLEMENTED histórico en PASS.
9. Serializar determinísticamente, crear el vínculo de adaptación y referencias de metadata;
   registrar resultado de adaptación separado de pruebas runtime y autorización de ejecución.
10. Futuro: comparar inventario planificado con fuentes materializadas y manifests de rutas
    realmente producidos por Next fijado. Cualquier extra/falta/hash cambiado bloquea promoción;
    build exitoso por sí solo no prueba igualdad del inventario.

El inventario es de **composición**, reutilizable por ambos pilotos; no copia productId, nombre
público ni autorización del plan P4.2 al producto nuevo. Cada configuración pública futura tendrá
su propio contrato/hash y WorkOrder de ejecución autorizado que vincule su identidad al mismo
inventario. El plan histórico es referencia declarativa de procedencia, no permiso ni spec
ejecutiva del nuevo cliente. Esta separación debe comprobarse también en G03/G09/G10.

## 3. Tratamiento exacto de /sign-in

Propuesta conservadora explícita: reservar **el segmento /sign-in y todos sus descendientes**
para colisiones, para todos los métodos y owners de producto. No existe excepción que permita
materializar esa reserva: ni core, ni módulo, ni glue. Es una restricción nueva del adaptador, más
estricta que la reserva exacta antigua; no se atribuye retrospectivamente al contrato P4.2.

Rechazar `/sign-in`, `/sign-in/x`, un catch-all que los capture, assets equivalentes y cualquier
alias/redirect/rewrite añadido que use ese origen o destino. `/signin` y `/sign-in-other` no son
ese namespace por prefijo textual, aunque tampoco están permitidos en el perfil cerrado actual.
`/api/auth/sign-in/email` es una operación real distinta y **se conserva**: no contiene el segmento
reservado en la raíz. No eliminarla por coincidencia de substring.

Conservar redirects existentes de páginas privadas a `/login`; `newRedirects=[]` se refiere a
reglas nuevas de generación, no prohíbe los redirects server-side ya aprobados. La URL histórica
no se sirve: en validación futura, GET `/sign-in` debe dar404 y no un redirect de compatibilidad.
La respuesta404 normal de Next no cuenta como ruta generada. Métodos negativos se comparan con
Next fijado sin inventar una nueva política runtime.

## 4. Inventario inicial: 11 rutas de archivos

Los paths source del ejemplo completo son reales y sus hashes se leyeron en esta revisión.
P = page; H = Route Handler. `allowedOperationsMethods` describe operaciones admitidas por la
aplicación; **no autoriza roles**. Guards aprobados siguen decidiendo sesión/owner/admin.

| Patrón | Tipo/owner | Métodos de operación | Archivo de producto |
|---|---|---|---|
| / | P/auth-core | GET | src/app/page.tsx |
| /login | P/auth-core | GET | src/app/login/page.tsx |
| /auth-check | P/auth-core | GET | src/app/auth-check/page.tsx |
| /admin-check | P/auth-core | GET | src/app/admin-check/page.tsx |
| /api/auth/[...all] | H/auth-core | GET,POST con dispatcher | src/app/api/auth/[...all]/route.ts |
| /api/auth-check | H/auth-core | GET | src/app/api/auth-check/route.ts |
| /api/admin-check | H/auth-core | GET | src/app/api/admin-check/route.ts |
| /requests | P/internal-requests | GET | src/app/requests/page.tsx |
| /requests/[id] | P/internal-requests | GET | src/app/requests/[id]/page.tsx |
| /api/requests | H/internal-requests | GET,POST | src/app/api/requests/route.ts |
| /api/requests/[id] | H/internal-requests | GET,PATCH | src/app/api/requests/[id]/route.ts |

Auth allowlist: GET `/api/auth/get-session`; POST `/api/auth/sign-in/email` y `/api/auth/sign-out`.
El resto del catch-all sigue rechazado por el wrapper; jamás implica signup u operaciones nuevas.
Los handlers requests exportan siete verbos, incluidos los que responden405. El inventario registra
los exports y los métodos permitidos por separado. HEAD/OPTIONS derivados de Next en rutas que
no los exportan se verifican durante G14/G15/G17 con Next15.5.25; no se publicitan como nuevas
operaciones ni sirven para compartir una ruta entre owners.

`layout.tsx`, `logout.tsx`, `editor.tsx`, CSS, scripts offline y fixtures no son endpoints.
El POST auth de logout está en el dispatcher, no en un `/logout` generado. `/_next` es namespace
reservado al framework y sus assets, no una página business. No existe favicon/public asset en
estos inputs inspeccionados. Middleware y frontera actúan sobre rutas existentes, no añaden rutas.

## 5. Detección de colisiones (política de composición, no router nuevo)

- Declaraciones: raíz `/` o segmentos ASCII lowercase `[a-z0-9-]+`, parámetro `[name]` o catch-all
  terminal `[...name]`; nombres `[a-z][a-z0-9]*`. Sin URL absoluta, query/hash, %, backslash, controles,
  espacios, `.`/`..`, doble slash o slash final salvo `/`. Rechazar, **no corregir silenciosamente**.
  `/_next` es una reserva especial y no una declaración aceptable de módulo.
- Canonicalizar solo para comparación: literal exacto; `[id]` y `[other]` son el mismo token
  dinámico `:param`; catch-all terminal consume uno o más segmentos. También comprobar variantes
  case-insensitive para paths de archivos/owners; las rutas con mayúsculas se rechazan al parsear.
- Dos patrones colisionan si existe algún path que ambos pueden consumir. Dinámico puede consumir
  cualquier segmento aunque el dominio valide UUID. Catch-all intersecta cualquier sufijo no vacío.
  Longitudes fijas diferentes no intersectan. No se utiliza prioridad estático/dinámico de Next
  para justificar un solapamiento: `/requests/new` vs `/requests/[id]` se rechaza.
- Rechazar intersecciones incluso con owner igual o métodos disjuntos; exactamente un archivo
  route o page por patrón. Ejemplo `/api/requests/[id]` vs `[slug]` falla; page+handler mismo path
  falla. Las operaciones auth son hijos declarativos de **un solo handler**, no rutas competidoras.
- Reservas por segmentos: /sign-in no admite claimant; /api/auth admite únicamente el handler
  auth-core esperado con su fuente/hash y operaciones aprobadas; /_next solo infraestructura
  framework, nunca archivos del generador ni módulo. Un catch-all raíz que toque reservas falla.
- Rechazar file ownership solapado, destino duplicado aun con bytes iguales, symlink/traversal,
  archivo vs directorio, colisión casefold y assets vs páginas/handlers/reservas. Nunca last-write-wins.
- Route groups, parallel/intercepting routes, optional catch-all, basePath, i18n, rewrites nuevos,
  route extensions distintas, metadata endpoints nuevos y cambios de trailingSlash no están
  soportados por el perfil v1. Detectarlos y BLOCKED para revisión; no ignorar carpetas especiales.
- Comprobar rutas faltantes/sobrantes contra perfil y fuentes conocidas, no solo entre las 11
  filas que suministre el solicitante. Un archivo extra no puede ocultarse omitiéndolo del JSON.

No se ejecuta código del proyecto para descubrir rutas; se inspeccionan convenciones conocidas y
hashes aprobados. El JSON Schema valida forma; parser/intersección/conjuntos/hashes necesitan
validación semántica separada y tests. No se afirma que un pattern de JSON Schema resuelva todo.

## 6. Determinismo y fingerprints

Definir serializer propio `inventory-json.v1`: UTF-8 sin BOM, keys de objetos ordenadas por código
Unicode, sin espacios, números enteros, sin NaN/infinito y un único LF final. Ejemplo Python de
formato, no generador implementado: json.dumps(sort_keys=True,ensure_ascii=False,separators=(',',':'),
allow_nan=False) + LF. Sin normalización Unicode silenciosa. Paths ASCII; ningún timestamp o
ubicación absoluta del host forma parte del inventario.

Ordenar routes por pattern; métodos lexicográficamente; authOperations por path/method;
reservations por pattern; futuras listas de assets por path. Valores const deben coincidir con ese
orden. SHA256 de bytes canónicos tiene prefijo `sha256:`. `source.sha256` siempre hash de bytes
originales, no JSON reserializado. Mantener separados legacy digest, file SHA y canonical SHA.

Orden de dependencias sin ciclos: aprobación G01 y sources → inventario → vínculo de adaptación
→ generation manifest/metadata → receipt de validación. El inventario no contiene su propio hash
ni el hash del receipt de adaptación que lo referencia. Los receipts de ejecución pueden contener
fecha/runId sin participar en reproducibilidad de fuentes. No inventar timestamps de aprobación.

## 7. Schemas propuestos (solo documentación)

Futuros `schemas/business-execution-inventory.v1.json` y
`schemas/business-route-adaptation.v1.json`. Dialecto declarativo mostrado: JSON Schema2020-12.
No instalar librería para esta revisión. La implementación futura debe probar soporte de las
restricciones usadas o validarlas explícitamente; jamás ignorar keywords no soportadas.
El perfil cerrado exige 11 rutas y los valores fijos actuales; añadir rutas requiere versión/revisión.
La igualdad con la tabla y hashes es validación semántica adicional, no queda garantizada por count.

### 7.1 Forma completa propuesta del inventario

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "format",
    "adaptationPolicy",
    "executionAuthority",
    "compositionId",
    "sources",
    "launch",
    "routes",
    "authOperations",
    "reservations",
    "publicAssets",
    "routeAliases",
    "newRedirects",
    "newRewrites"
  ],
  "properties": {
    "format": {
      "const": "nexonova.business-execution-inventory.v1"
    },
    "adaptationPolicy": {
      "const": "p42-to-approved-runtime.v1"
    },
    "executionAuthority": {
      "const": "none"
    },
    "compositionId": {
      "const": "business-auth-internal-requests-0.1.0-d02"
    },
    "sources": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "legacyPlan",
        "g01Decision",
        "approvedReceipt",
        "nextConfig",
        "authDispatch",
        "moduleDispatch",
        "middleware"
      ],
      "properties": {
        "legacyPlan": {
          "$ref": "#/$defs/sourceRef"
        },
        "g01Decision": {
          "$ref": "#/$defs/sourceRef"
        },
        "approvedReceipt": {
          "$ref": "#/$defs/sourceRef"
        },
        "nextConfig": {
          "$ref": "#/$defs/sourceRef"
        },
        "authDispatch": {
          "$ref": "#/$defs/sourceRef"
        },
        "moduleDispatch": {
          "$ref": "#/$defs/sourceRef"
        },
        "middleware": {
          "$ref": "#/$defs/sourceRef"
        }
      }
    },
    "launch": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "command",
        "source",
        "boundarySource"
      ],
      "properties": {
        "command": {
          "const": [
            "node",
            "scripts/start-requests.mjs"
          ]
        },
        "source": {
          "$ref": "#/$defs/sourceRef"
        },
        "boundarySource": {
          "$ref": "#/$defs/sourceRef"
        }
      }
    },
    "routes": {
      "type": "array",
      "minItems": 11,
      "maxItems": 11,
      "items": {
        "$ref": "#/$defs/route"
      }
    },
    "authOperations": {
      "const": [
        {
          "path": "/api/auth/get-session",
          "method": "GET",
          "handlerPattern": "/api/auth/[...all]"
        },
        {
          "path": "/api/auth/sign-in/email",
          "method": "POST",
          "handlerPattern": "/api/auth/[...all]"
        },
        {
          "path": "/api/auth/sign-out",
          "method": "POST",
          "handlerPattern": "/api/auth/[...all]"
        }
      ]
    },
    "reservations": {
      "const": [
        {
          "pattern": "/_next",
          "match": "segment-subtree",
          "owner": "framework",
          "materialize": false
        },
        {
          "pattern": "/api/auth",
          "match": "segment-subtree",
          "owner": "auth-core",
          "materialize": false
        },
        {
          "pattern": "/sign-in",
          "match": "segment-subtree",
          "owner": "historical-p42",
          "materialize": false
        }
      ]
    },
    "publicAssets": {
      "const": []
    },
    "routeAliases": {
      "const": []
    },
    "newRedirects": {
      "const": []
    },
    "newRewrites": {
      "const": []
    }
  },
  "$defs": {
    "sourceRef": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "path",
        "sha256"
      ],
      "properties": {
        "path": {
          "type": "string",
          "pattern": "^[^/\\\\]+(?:/[^/\\\\]+)*$"
        },
        "sha256": {
          "type": "string",
          "pattern": "^sha256:[a-f0-9]{64}$"
        }
      }
    },
    "route": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "pattern",
        "kind",
        "owner",
        "source",
        "outputPath",
        "exportedMethods",
        "allowedOperationsMethods",
        "frameworkMethodPolicy"
      ],
      "properties": {
        "pattern": {
          "type": "string",
          "pattern": "^/(?:[a-z0-9-]+|\\[[a-z][a-z0-9]*\\]|\\[\\.\\.\\.[a-z][a-z0-9]*\\])(?:/(?:[a-z0-9-]+|\\[[a-z][a-z0-9]*\\]|\\[\\.\\.\\.[a-z][a-z0-9]*\\]))*$|^/$"
        },
        "kind": {
          "enum": [
            "page",
            "handler"
          ]
        },
        "owner": {
          "enum": [
            "auth-core",
            "internal-requests"
          ]
        },
        "source": {
          "$ref": "#/$defs/sourceRef"
        },
        "outputPath": {
          "type": "string",
          "minLength": 1
        },
        "exportedMethods": {
          "type": "array",
          "uniqueItems": true,
          "items": {
            "enum": [
              "DELETE",
              "GET",
              "HEAD",
              "OPTIONS",
              "PATCH",
              "POST",
              "PUT"
            ]
          }
        },
        "allowedOperationsMethods": {
          "type": "array",
          "uniqueItems": true,
          "items": {
            "enum": [
              "DELETE",
              "GET",
              "HEAD",
              "OPTIONS",
              "PATCH",
              "POST",
              "PUT"
            ]
          },
          "minItems": 1
        },
        "frameworkMethodPolicy": {
          "const": "verify-next-15.5.25-no-new-operations"
        }
      }
    }
  }
}
```

### 7.2 Ejemplo completo del inventario (observación estática, no ejecución)

```json
{
  "format": "nexonova.business-execution-inventory.v1",
  "adaptationPolicy": "p42-to-approved-runtime.v1",
  "executionAuthority": "none",
  "compositionId": "business-auth-internal-requests-0.1.0-d02",
  "sources": {
    "legacyPlan": {
      "path": "docs/migration/P4_2_PLAN.json",
      "sha256": "sha256:cd65bb8b5f44fcf14881b327544e88b41563e53b995a71790911c53d0bb13db2"
    },
    "g01Decision": {
      "path": "docs/migration/P4_6_G01_DECISION.json",
      "sha256": "sha256:ef9330c7d9140eb8326e878649eabf5a615e2d9a43835c32c04e3d82d3bc9112"
    },
    "approvedReceipt": {
      "path": "docs/migration/P4_5_B_FINAL_RECEIPT.json",
      "sha256": "sha256:81a3f4cb62f1828b582f1f43ff29e554941a443532a2d4579b8ff367c4f3745b"
    },
    "nextConfig": {
      "path": "templates/business-platform-auth/next.config.ts",
      "sha256": "sha256:c12defa1b9b367d8f30bb793c50e5b0e5966a15a4717375ab2c41e9f5ba49de9"
    },
    "authDispatch": {
      "path": "templates/business-platform-auth/src/server/http.ts",
      "sha256": "sha256:f56890f99edf74f946032886b6354056678359c2283fb4e18b9cd4b78d04beec"
    },
    "moduleDispatch": {
      "path": "modules/internal-requests/0.1.0/files/src/modules/internal-requests/http.ts",
      "sha256": "sha256:d1833953c505c686b3c662d2cf04c7dfb21c9f4be73a569a3d32e1638ed43003"
    },
    "middleware": {
      "path": "modules/internal-requests/0.1.0/files/src/middleware.ts",
      "sha256": "sha256:6fc29ff315d0b9139c6c0ddddf635c2a549720f98f54d34df97d1da4ebce4a60"
    }
  },
  "launch": {
    "command": [
      "node",
      "scripts/start-requests.mjs"
    ],
    "source": {
      "path": "modules/internal-requests/0.1.0/files/scripts/start-requests.mjs",
      "sha256": "sha256:4cde0848456d6b5eb46fb09560602177007213f66c18338cc16d599a6376d9c8"
    },
    "boundarySource": {
      "path": "modules/internal-requests/0.1.0/files/scripts/requests-response-boundary.mjs",
      "sha256": "sha256:de46a42b5bc3084d24de60ca9ae70946a217dbcb4876112b3e8aee0c8fee3b3d"
    }
  },
  "routes": [
    {
      "pattern": "/",
      "kind": "page",
      "owner": "auth-core",
      "source": {
        "path": "templates/business-platform-auth/src/app/page.tsx",
        "sha256": "sha256:74b63148d0cdab53fb0a571c206d739e17b669ab6e0991e2a9eb25456d453f33"
      },
      "outputPath": "src/app/page.tsx",
      "exportedMethods": [],
      "allowedOperationsMethods": [
        "GET"
      ],
      "frameworkMethodPolicy": "verify-next-15.5.25-no-new-operations"
    },
    {
      "pattern": "/admin-check",
      "kind": "page",
      "owner": "auth-core",
      "source": {
        "path": "templates/business-platform-auth/src/app/admin-check/page.tsx",
        "sha256": "sha256:0f5d76e95da139019b9b90c13bc0ce79cd591a3e7a81c97c200e4bbce5ea55a6"
      },
      "outputPath": "src/app/admin-check/page.tsx",
      "exportedMethods": [],
      "allowedOperationsMethods": [
        "GET"
      ],
      "frameworkMethodPolicy": "verify-next-15.5.25-no-new-operations"
    },
    {
      "pattern": "/api/admin-check",
      "kind": "handler",
      "owner": "auth-core",
      "source": {
        "path": "templates/business-platform-auth/src/app/api/admin-check/route.ts",
        "sha256": "sha256:5ba2a1df5af1fc6fd57333a56b72265387f8a433060fdf224adf61a03c84e139"
      },
      "outputPath": "src/app/api/admin-check/route.ts",
      "exportedMethods": [
        "GET"
      ],
      "allowedOperationsMethods": [
        "GET"
      ],
      "frameworkMethodPolicy": "verify-next-15.5.25-no-new-operations"
    },
    {
      "pattern": "/api/auth-check",
      "kind": "handler",
      "owner": "auth-core",
      "source": {
        "path": "templates/business-platform-auth/src/app/api/auth-check/route.ts",
        "sha256": "sha256:961d30ff77a747986130d82c3864bc53ef01b7bc15dd066a969819bec515c703"
      },
      "outputPath": "src/app/api/auth-check/route.ts",
      "exportedMethods": [
        "GET"
      ],
      "allowedOperationsMethods": [
        "GET"
      ],
      "frameworkMethodPolicy": "verify-next-15.5.25-no-new-operations"
    },
    {
      "pattern": "/api/auth/[...all]",
      "kind": "handler",
      "owner": "auth-core",
      "source": {
        "path": "templates/business-platform-auth/src/app/api/auth/[...all]/route.ts",
        "sha256": "sha256:d5a4b854c6095e9775f2875048bfece08dce1aa99f20087e81bc9442cf784cf0"
      },
      "outputPath": "src/app/api/auth/[...all]/route.ts",
      "exportedMethods": [
        "GET",
        "POST"
      ],
      "allowedOperationsMethods": [
        "GET",
        "POST"
      ],
      "frameworkMethodPolicy": "verify-next-15.5.25-no-new-operations"
    },
    {
      "pattern": "/api/requests",
      "kind": "handler",
      "owner": "internal-requests",
      "source": {
        "path": "modules/internal-requests/0.1.0/files/src/app/api/requests/route.ts",
        "sha256": "sha256:2dac8dd41f67d6a2fe5182446f466f455d0560687f42ac2e25dcd594d02a2016"
      },
      "outputPath": "src/app/api/requests/route.ts",
      "exportedMethods": [
        "DELETE",
        "GET",
        "HEAD",
        "OPTIONS",
        "PATCH",
        "POST",
        "PUT"
      ],
      "allowedOperationsMethods": [
        "GET",
        "POST"
      ],
      "frameworkMethodPolicy": "verify-next-15.5.25-no-new-operations"
    },
    {
      "pattern": "/api/requests/[id]",
      "kind": "handler",
      "owner": "internal-requests",
      "source": {
        "path": "modules/internal-requests/0.1.0/files/src/app/api/requests/[id]/route.ts",
        "sha256": "sha256:2424a0fb9034fb308e83a1c60701a8cd156ca72c84dff2bab5b9b4ea2b2d03eb"
      },
      "outputPath": "src/app/api/requests/[id]/route.ts",
      "exportedMethods": [
        "DELETE",
        "GET",
        "HEAD",
        "OPTIONS",
        "PATCH",
        "POST",
        "PUT"
      ],
      "allowedOperationsMethods": [
        "GET",
        "PATCH"
      ],
      "frameworkMethodPolicy": "verify-next-15.5.25-no-new-operations"
    },
    {
      "pattern": "/auth-check",
      "kind": "page",
      "owner": "auth-core",
      "source": {
        "path": "templates/business-platform-auth/src/app/auth-check/page.tsx",
        "sha256": "sha256:794534a0609c7ee6fd2f3ad2632500f015d1427941bd1f2f818a3e959ca38cea"
      },
      "outputPath": "src/app/auth-check/page.tsx",
      "exportedMethods": [],
      "allowedOperationsMethods": [
        "GET"
      ],
      "frameworkMethodPolicy": "verify-next-15.5.25-no-new-operations"
    },
    {
      "pattern": "/login",
      "kind": "page",
      "owner": "auth-core",
      "source": {
        "path": "templates/business-platform-auth/src/app/login/page.tsx",
        "sha256": "sha256:1f0e1b16745aa2056a1fd81be307c4df33c35f264d18bfc2a35544f2576b4f10"
      },
      "outputPath": "src/app/login/page.tsx",
      "exportedMethods": [],
      "allowedOperationsMethods": [
        "GET"
      ],
      "frameworkMethodPolicy": "verify-next-15.5.25-no-new-operations"
    },
    {
      "pattern": "/requests",
      "kind": "page",
      "owner": "internal-requests",
      "source": {
        "path": "modules/internal-requests/0.1.0/files/src/app/requests/page.tsx",
        "sha256": "sha256:a6233e58fc5d1d272c29e59547b467dc9fef4349c4ad08b64327da6ba6359593"
      },
      "outputPath": "src/app/requests/page.tsx",
      "exportedMethods": [],
      "allowedOperationsMethods": [
        "GET"
      ],
      "frameworkMethodPolicy": "verify-next-15.5.25-no-new-operations"
    },
    {
      "pattern": "/requests/[id]",
      "kind": "page",
      "owner": "internal-requests",
      "source": {
        "path": "modules/internal-requests/0.1.0/files/src/app/requests/[id]/page.tsx",
        "sha256": "sha256:ff758cf0cb597b2eb8d3ed9440091280a588b4a4b5fe76bcaadd932283fcb765"
      },
      "outputPath": "src/app/requests/[id]/page.tsx",
      "exportedMethods": [],
      "allowedOperationsMethods": [
        "GET"
      ],
      "frameworkMethodPolicy": "verify-next-15.5.25-no-new-operations"
    }
  ],
  "authOperations": [
    {
      "path": "/api/auth/get-session",
      "method": "GET",
      "handlerPattern": "/api/auth/[...all]"
    },
    {
      "path": "/api/auth/sign-in/email",
      "method": "POST",
      "handlerPattern": "/api/auth/[...all]"
    },
    {
      "path": "/api/auth/sign-out",
      "method": "POST",
      "handlerPattern": "/api/auth/[...all]"
    }
  ],
  "reservations": [
    {
      "pattern": "/_next",
      "match": "segment-subtree",
      "owner": "framework",
      "materialize": false
    },
    {
      "pattern": "/api/auth",
      "match": "segment-subtree",
      "owner": "auth-core",
      "materialize": false
    },
    {
      "pattern": "/sign-in",
      "match": "segment-subtree",
      "owner": "historical-p42",
      "materialize": false
    }
  ],
  "publicAssets": [],
  "routeAliases": [],
  "newRedirects": [],
  "newRewrites": []
}
```

### 7.3 Forma completa y ejemplo del vínculo de adaptación

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "format",
    "policy",
    "executionAuthority",
    "legacyPlan",
    "inventoryCanonicalSha256",
    "decision",
    "mappings",
    "legacyStateHandling",
    "runtimeValidation"
  ],
  "properties": {
    "format": {
      "const": "nexonova.business-route-adaptation.v1"
    },
    "policy": {
      "const": "p42-to-approved-runtime.v1"
    },
    "executionAuthority": {
      "const": "none"
    },
    "legacyPlan": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "path",
        "sha256"
      ],
      "properties": {
        "path": {
          "type": "string",
          "pattern": "^[^/\\\\]+(?:/[^/\\\\]+)*$"
        },
        "sha256": {
          "type": "string",
          "pattern": "^sha256:[a-f0-9]{64}$"
        }
      }
    },
    "inventoryCanonicalSha256": {
      "type": "string",
      "pattern": "^sha256:[a-f0-9]{64}$"
    },
    "decision": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "path",
        "sha256"
      ],
      "properties": {
        "path": {
          "type": "string",
          "pattern": "^[^/\\\\]+(?:/[^/\\\\]+)*$"
        },
        "sha256": {
          "type": "string",
          "pattern": "^sha256:[a-f0-9]{64}$"
        }
      }
    },
    "mappings": {
      "const": [
        {
          "legacyPattern": "/sign-in",
          "disposition": "reservation-only",
          "runtimeAuthenticationPage": "/login",
          "materializeLegacyPath": false
        },
        {
          "legacyPattern": "/api/auth/[...all]",
          "disposition": "retain-handler-and-reserve-namespace",
          "runtimePattern": "/api/auth/[...all]"
        }
      ]
    },
    "legacyStateHandling": {
      "const": "preserve-do-not-promote"
    },
    "runtimeValidation": {
      "const": "NOT_EXECUTED"
    }
  }
}
```

```json
{
  "format": "nexonova.business-route-adaptation.v1",
  "policy": "p42-to-approved-runtime.v1",
  "executionAuthority": "none",
  "legacyPlan": {
    "path": "docs/migration/P4_2_PLAN.json",
    "sha256": "sha256:cd65bb8b5f44fcf14881b327544e88b41563e53b995a71790911c53d0bb13db2"
  },
  "inventoryCanonicalSha256": "sha256:31bb01135d7d8da52720e112e9b10a6c6bd8bf0f5c7bbc2308724242d5f59eb5",
  "decision": {
    "path": "docs/migration/P4_6_G01_DECISION.json",
    "sha256": "sha256:ef9330c7d9140eb8326e878649eabf5a615e2d9a43835c32c04e3d82d3bc9112"
  },
  "mappings": [
    {
      "legacyPattern": "/sign-in",
      "disposition": "reservation-only",
      "runtimeAuthenticationPage": "/login",
      "materializeLegacyPath": false
    },
    {
      "legacyPattern": "/api/auth/[...all]",
      "disposition": "retain-handler-and-reserve-namespace",
      "runtimePattern": "/api/auth/[...all]"
    }
  ],
  "legacyStateHandling": "preserve-do-not-promote",
  "runtimeValidation": "NOT_EXECUTED"
}
```

## 8. Metadata/receipts consumidores propuestos

Generation manifest y metadata deben referenciar `inventoryCanonicalSha256`, hash del vínculo de
adaptación, política/version, hash de decisión G01 y launcher obligatorio. No copiar un PASS de
P4.5-B como validación del producto nuevo. El futuro validation receipt registra por separado:
`inventory-validation` (estructural/semántica), `materialized-inventory-match`, `runtime-routing`,
`D02-launcher`, y matriz G02–G24 con referencias y hashes. Ninguno es un gate nuevo aprobado por
este documento; son subchecks que alimentan los gates existentes.

Ejemplo de fragmento de metadata (NO schema completo de metadata; símbolos HASH son placeholders):

```json
{
  "executionInventory": {"format":"nexonova.business-execution-inventory.v1","canonicalSha256":"sha256:HASH"},
  "routeAdaptation": {"format":"nexonova.business-route-adaptation.v1","policy":"p42-to-approved-runtime.v1","canonicalSha256":"sha256:HASH"},
  "requiredLauncher": ["node","scripts/start-requests.mjs"],
  "limitationsReference": {"phase":"P4.5-B","receiptSha256":"sha256:HASH"}
}
```

Los ejemplos completos anteriores usan hashes reales de lectura. El fragmento usa placeholders
para relaciones de contratos posteriores; no es un fixture listo para validación. Metadata no
contiene autorización de ejecución, tokens, DB URLs ni credenciales. WorkOrder ejecutivo nuevo
sigue requiriendo diseño/revisión y autorización externa separada; G01 no permite derivarlo de
`execution=forbidden` de P4.2.

## 9. Validaciones fail-closed y cambios previstos

Rechazar formatos/políticas/perfiles desconocidos; source/hash no aprobado; props duplicadas o
extra; route/asset no inventariado; declaración insegura; intersección; reserva omitida/mutable;
/sign-in materializado o mapeado por redirect; /login faltante; allowlist auth expandida; exports
mal clasificados; launcher/core auth elegido para InternalRequest; D02 faltante; referencias sin
hash/inconsistentes; estados históricos promovidos; uso de G01 como permiso de render.

Fallos de implementación reproducibles → FAIL. Información/feature/permisos no soportados →
BLOCKED. No escribir productos ni ejecutar npm/DB durante parse/adapt/plan. La implementación
futura debe usar staging/ownership para verificar antes de promoción y conservar evidencia al fallar.

Futuros archivos nuevos, no creados aquí:
- Los dos schemas anteriores; descriptor aprobado en `config/business/compositions/` con inventario
  source y hashes; nuevos inputs públicos de dos pilotos.
- `factory/business_execution_inventory.py`: lector/adaptador/validador semántico independiente.
- `tests/test_business_execution_inventory.py`: estructura, mapping, intersecciones, invariantes.
- `factory/business_generation.py`, CLI separado y contratos manifest/metadata/receipts/WorkOrder
  ejecutivos descritos en la propuesta principal, tras revisión de sus diseños específicos.

**Modificaciones existentes necesarias para este diseño: ninguna** en código, schemas históricos,
config, dependencias, auth, migraciones o artefactos aprobados. Solo se actualizan las dos piezas de
planificación P4.6 y se añade este anexo/decisión/documentación histórica. Si después se necesita
modificar CLI/registro compartido, su diff requerirá autorización; no está supuesto aquí.

## 10. Impacto en G02–G24 y gates

G01 es HUMAN_APPROVED / ALTERNATIVE_A, no una prueba runtime PASS. G02–G24 siguen NOT_EXECUTED.
G02 añade plan sin efectos con inventario/vínculo; G03 prueba que G01 no autoriza ejecución;
G04/G05 incluyen reservas, intersecciones y formatos no soportados; G06 incluye inputs cambiados;
G07/G08 incluyen canon/hash estables; G09 diferencia identidad pública de inventario compartido;
G10 verifica referencias/adaptación; G11 igualdad exacta discovery/output y ausencia /sign-in;
G14 contrasta manifests Next; G15 prueba /login y ausencia de alias sin cambiar auth;
G17 obliga al launcher y D02; G20 inspecciona nuevos metadata/receipts; G21 preserva historia;
G23 rechaza mappings/hashes/sets alterados; G24 revisa inventario de ambos outputs. G12/G13/G16/
G18/G19/G22 conservan los objetivos aprobados de la propuesta y se vinculan al inventory hash.

Gates de entrada P4.5-B permanecen aprobados. Los gates futuros de generación se calculan desde
evidencia nueva y adaptación válida, jamás desde el documento de diseño. generation y autonomy
siguen NOT_IMPLEMENTED; readiness BLOCKED; no P4.7. Próximo paso: revisión humana del detalle
contractual, no solicitud ni ejecución automática de implementación.
