# Registro de migración

El usuario aprobó explícitamente MIGRATION_PLAN.md el 2026-09-06. Los documentos raíz conservan sus encabezados históricos; el estado de ejecución se registra aquí.

| Fase | Estado | Registro |
|---|---|---|
| P0 | Línea base técnica establecida; procedencia/Git pendientes | [P0](P0.md) |
| P1 | Correcciones y contención del legado verificadas | [P1](P1.md) |
| P2 | PASS_WITH_LIMITATIONS aprobado por el usuario; limitaciones aceptadas | [Validación final P2](P2_FINAL_VALIDATION.md), [implementación](P2.md) |
| P3 | P3.1/P3.2 implementadas para revisión; P3.3 no iniciada | [P3](P3.md) |
| P4 | No iniciada; depende de P3 | [P4](P4.md) |
| P5 | No iniciada; depende de productos/manifiestos | [P5](P5.md) |
| P6 | No iniciada; opcional y dependiente de piloto/seguridad | [P6](P6.md) |
| P7 | No iniciada; requiere producto y entorno de validación | [P7](P7.md) |

Véanse [los ajustes documentados](PLAN_ADJUSTMENTS.md), [la arquitectura actual](../architecture.md) y [el informe de esta entrega parcial](../../REFACTOR_REPORT.md).

No se ha declarado completa la migración. Las pruebas disponibles se ejecutan al cierre de cada fase preparada; las pruebas de producto y aislamiento Docker no se sustituyen por mocks ni por existencia de archivos.

Estado posterior: P3.1/P3.2 aprobadas; [P3.3 base visual](P3_3.md) implementada para revisión. P3.4 no iniciada.

P3.3 aprobada. [P3.4: interacciones](P3_4.md), entrega para revisión antes de P3.5.
