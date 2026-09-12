# Arquitectura vigente — cierre técnico P3

corporate-site es la primera capacidad funcional de piloto validada para uso interno/controlado. P3.1–P3.6 aprobadas; cierre P3.7 PASS_WITH_LIMITATIONS pendiente de aprobación humana. No production-ready. [Matriz/evidencia](migration/P3_FINAL_REPORT.md).

## Núcleo y fronteras

Un paquete Python conserva contratos, políticas y almacenamiento privado por cliente/run. Los agentes académicos permanecen desactivados. El executor experimental P2 controla procesos Python en Docker local; WorkOrders, permisos y evidencia están separados del producto. La memoria automática sigue desactivada. Recuperación/checkpoints no significan replay seguro tras SIGKILL.

## Capacidad corporate-site

Entradas: fuente preservada + especificación + selección explícita + configuración pública + template congelado, enlazados por WorkOrder v2 y hash autorizado por operador. Los contratos v1 de preparación no conceden generación. Configuración se mantiene fuera de componentes y no contiene condiciones por cliente.

Flujo: validación semántica y fuente → staging externo identificado → manifiesto/diff → validación Node en copia descartable → materialización atómica sin reemplazo. generation.py no ejecuta código web; web_tools.py expone acciones acotadas y mantiene instalación separada de checks/build. No se incorporan herramientas arbitrarias desde el brief. product_integrity.py verifica fuentes/metadata/referencias; generality.py contrasta contenido de los dos pilotos.

El producto Next/React/TypeScript/CSS Modules tiene una landing, selección en memoria, dominios sintácticos, chat local sustituible y contacto preparado/copiado sin envío. No hay backend persistente, auth, BD o integraciones. Los dos productos comparten componentes y difieren por JSON público, nombre de paquete y metadata portable.

## Estado y autonomía

Productos fuera del checkout: nexonova-website y synthetic-website. La aplicación no consume .nexonova/project.json. Fábrica, prototipo, WorkOrders, staging, permisos y Python no se montaron durante el arranque autónomo Docker final. Solo instalación preparatoria accede al registro npm; runtime local sin red externa ni puertos publicados.

Los registros de staging materializado se preservan como evidencia intencional. Fuentes generadas son deterministas; builds/cachés no lo son por contrato. La regeneración exacta conocida de next-env.d.ts se informa aparte. No hay actualización automática de productos aceptados.

## Versionado y evolución

Factory y template 0.1.0; generator identificado por hash dentro de factory, sin semver independiente. Schemas y metadata versionados; [baseline final](migration/P3_BASELINE.json) y test detectan cambios en archivos fijados. No es firma criptográfica. P4/P5 deben revisar y autorizar nuevos baselines, no silenciar diferencias.

[Guía operativa](corporate-site-operator.md) y [límites del cierre](migration/P3_FINAL_REPORT.md). Linux/mismo filesystem, host confiable, recuperación manual, dos configuraciones y acentos compartidos permanecen como límites. Procedencia/Git, aprobación editorial/visual y preparación operativa impiden declarar publicación lista. P4–P7 no iniciadas.
