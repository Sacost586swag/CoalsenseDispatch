# Orden de construcción

Estado: **propuesta del orquestador (2026-11-14), pendiente del visto bueno del operador.** Faltaba en el repo (lo cita `structure.md`). Se armó a partir de las olas de dependencias de cada `tasks.md` y del orden de partida del operador. El detalle por tarea vive en `docs/PLAN.md`.

## Principios

1. **Lo que protege a la persona va antes de lo que la expone.** Alto, Deshacer y Ayuda humana existen antes que cualquier actuación. Las reglas de crisis existen antes de la primera llamada a un modelo de lenguaje. El motor de políticas existe antes de la primera herramienta con efecto externo.
2. **Se respetan las olas de cada `tasks.md`.** Ninguna tarea entra en un hito anterior al de sus dependencias (comprobado sobre las 190 tareas).
3. **Una modalidad completa antes que dos a medias.** La voz se cierra antes que la cabeza, para tener pronto un recorrido completo sin manos.
4. **El hito termina con evidencia**, no con afirmaciones.

## Hitos

| Hito | Nombre | Specs y tareas | Por qué en este lugar |
| --- | --- | --- | --- |
| P | Preparación | P-01 y P-02: reparar `01/tasks.md` y `02/tasks.md` (están dañados, ver abajo). P-03: base de datos local para pruebas. | Sin specs legibles los subagentes trabajarían sobre texto corrupto. |
| H1 | Fundaciones y design system accesible | 00 completa (T-00-001 a T-00-017). | Todo depende del monorepo, la CI, las auditorías, la autenticación y `packages/ui`. |
| H2 | Bus de intenciones, Alto y Deshacer | 01: esquema, bus, aprobaciones locales, fixtures, Alto, Deshacer, Ayuda humana, perfil, teclado y mouse, actuador, egreso, controles de Alto y Deshacer. | SP-2 (Alto siempre detiene) antes de cualquier modalidad. |
| H3 | Entrada por voz | 01: archivos de comandos, voz, palabras de control, comandos, dictado, números en pantalla, cuadrícula, retroalimentación. | Primera modalidad completa. |
| H4 | Entrada por cabeza y gestos | 01: cámara, puntero, gestos, modo web, calibración, indicadores, panel de modalidades, rendimiento, accesibilidad y fiabilidad de 01. | Cierra la spec 01, incluida la calibración que necesita la primera tarea. |
| H5 | Orquestador, gateway y motor de políticas | 02 completa, T-01-056 (enlace TLS) y, adelantadas de 05, T-05-001 a T-05-003 (reglas de crisis antes de los modelos). | "Reglas antes de modelos" (T-05-003) debe existir cuando exista `llm.complete` (T-02-009). |
| H6 | Ciclo de control y logros | 03 completa, con la primera tarea de la sesión 1 (T-03-015). | Es la unidad del producto (V-02). |
| H7 | Las tres herramientas del MVP | 04 completa: correo, documento y publicación. | Necesita aprobación, retención y agentes. |
| H8 | Seguridad y bienestar | Resto de 05: derivación, rutas humanas, contacto de confianza, límites de la IA, consentimientos. | Cierra SP-5 y SP-7 sobre el producto completo. |
| H9 | Panel del cuidador/a | 06 completa. | Necesita delegaciones (02) y calibración (01). |
| H10 | Privacidad | 07 completa: claves, exportación, borrado, terceros, operador. | Necesita logros (03) y revocación (06) para exportar y borrar todo. |
| H11 | Despliegue y guion de demo | 09 completa, más el guion de demo y `docs/checklist-humano.md`. | Empaqueta lo anterior. |
| — | Fase 2 | 08 (mercado B2B) y las tareas `[POST-MVP]` de 01 (mirada, switch, comandos propios). | Fuera del MVP. |

## Cortes

- **Corte de demo interna: H1 a H8.** Una persona completa su primera tarea en la sesión 1 usando solo voz o solo cabeza. Es el corte que pidió el operador.
- **MVP completo según las specs: H1 a H11.** `product.md` incluye el "panel básico del cuidador" en el alcance del MVP, y `TRAZABILIDAD.md` cuenta como MVP los requisitos de 06, 07 y 09. Por la regla "si chocan, gana la spec", el MVP no queda cerrado hasta H11.
- **Puerta antes de ofrecerlo a personas reales** (SF-06, no bloquea la construcción): una ruta humana configurada y probada, consentimiento revisado bajo LOPDP y mensajes de crisis revisados por un profesional.

## Defectos de spec detectados (propuesta de corrección)

| ID | Defecto | Propuesta |
| --- | --- | --- |
| D-SPEC-01 | `01-capa-de-entrada/tasks.md` no contiene ninguna "c" minúscula: todas se volvieron "o" ("intenoiones", `apps/oompanion`). | P-01: reparar con un subagente, usando `requirements.md`, `design.md` y `TRAZABILIDAD.md` (intactos) como referencia, y revisar el diff completo en Opus antes de aceptarlo. Si el operador tiene el original, se usa ese. |
| D-SPEC-02 | `02-orquestador-y-agentes/tasks.md` no contiene ninguna "g" minúscula: todas se volvieron "a" ("aareaado", `miarations`). | P-02: igual que P-01. |
| D-SPEC-03 | T-02-002 prueba la seguridad por filas contra PostgreSQL (H5), pero el docker-compose con PostgreSQL está en T-09-008 (H11). | P-03: crear en H5 `infra/docker-compose.dev.yml` (PostgreSQL con pgvector y Redis, solo para desarrollo y pruebas). T-09-008 lo amplía después para los entornos. |
| D-SPEC-04 | `CLAUDE.md` citaba `THIRD_PARTY_NOTICES.md`; las specs usan `THIRD_PARTY.md`. | Se usa `THIRD_PARTY.md` (gana la spec). Las atribuciones de Apache 2.0 de Gameface van ahí. |
