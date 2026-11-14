# Requisitos: 03 Ciclo de control

**Estado:** completo. Notación y tipos de prueba: `01-capa-de-entrada/requirements.md` sección 0.
**Cubre:** tareas y micro-pasos, aprobación, dial de autonomía, registro de logros, panel de progreso y la primera tarea de la sesión 1.
**Vertical aplicable:** V-01, V-02, V-03, V-04. Reglas AX-03, AX-09, AX-11, AX-13.

## 1. Ciclo que implementa esta spec

1. La persona elige una tarea concreta con resultado visible.
2. Los agentes ejecutan lo pesado.
3. La persona revisa y aprueba.
4. El resultado sale al mundo.
5. Queda registrado como logro, y la siguiente tarea es un poco más grande.

## 2. Niveles de autonomía

| Nivel | Qué hace la IA sola | Qué aprueba la persona |
| --- | --- | --- |
| **N0** (por defecto) | Nada: propone cada micro-paso. | Cada micro-paso y toda acción con efecto externo. |
| **N1** | Ejecuta sola los micro-pasos internos (borradores, búsquedas, ordenar). | La propuesta final y toda acción con efecto externo. |
| **N2** | Encadena los micro-pasos internos y prepara el paquete completo. | Una sola vez, el paquete final con vista previa, y con él toda acción con efecto externo. |

En ningún nivel desaparece la aprobación de una acción con efecto externo (C-08). El nivel se fija por tipo de tarea.

## 3. Requisitos funcionales

### Grupo A. Tareas y micro-pasos

**HU-03-A.** Como persona, quiero elegir yo una tarea concreta y ver sus pasos, para sentir que dirijo el trabajo.

- **REQ-03-001** THE SYSTEM SHALL mostrar a la persona el catálogo de tipos de tarea disponibles (los tres del MVP y los que aporten las herramientas que habilitó) y permitirle elegir uno con cualquier modalidad. Prueba: `e2e`.
- **REQ-03-002** THE SYSTEM SHALL NOT iniciar una tarea que la persona no haya elegido; el sistema puede proponer la siguiente tarea, pero no empezarla. Prueba: `unit`.
- **REQ-03-003** WHEN la persona elige una tarea, THE SYSTEM SHALL pedir solo los datos mínimos para empezar (por ejemplo destinatario y propósito) por dictado o selección, sin formularios largos. Prueba: `e2e`.
- **REQ-03-004** THE SYSTEM SHALL dividir cada tarea en micro-pasos, cada uno con un resultado que la persona pueda ver. Prueba: `unit`.
- **REQ-03-005** THE SYSTEM SHALL permitir pausar una tarea en cualquier momento y retomarla más tarde sin perder el avance, sin límite de tiempo. Prueba: `e2e`.
- **REQ-03-006** WHEN llega `control.stop`, THE SYSTEM SHALL dejar la tarea en estado detenido, mostrar qué se detuvo y qué quedó hecho, y ofrecer retomar, editar o descartar. Prueba: `e2e`.
- **REQ-03-007** WHEN la persona descarta una tarea, THE SYSTEM SHALL conservar lo ya hecho hasta que la persona decida borrarlo y NOT registrarlo como fallo ni como pérdida (AX-13). Prueba: `unit`.
- **REQ-03-008** THE SYSTEM SHALL mostrar en toda pantalla de tarea el estado actual (en plan, en ejecución, pendiente de aprobación, detenida, completada) con texto, además del color. Prueba: `a11y`.

### Grupo B. Aprobación

**HU-03-B.** Como persona, quiero revisar y aprobar o rechazar lo que la IA preparó, con la modalidad que uso, para que nada salga sin mi decisión.

- **REQ-03-010** WHEN una acción requiere aprobación, THE SYSTEM SHALL mostrar la tarjeta de aprobación con: qué se aprueba, el contenido exacto, a quién llega y qué efecto tiene, en lenguaje llano. Prueba: `e2e`.
- **REQ-03-011** THE SYSTEM SHALL ofrecer aprobar, rechazar y decidir después, sin opción preseleccionada, con el mismo tamaño y la misma facilidad para aprobar y para rechazar (AX-09). Prueba: `a11y`.
- **REQ-03-012** THE SYSTEM SHALL NOT aprobar por inacción: una aprobación pendiente permanece pendiente sin límite de tiempo. Prueba: `unit`.
- **REQ-03-013** WHEN la persona aprueba, THE SYSTEM SHALL enviar `approval.approve` con el `pending_action_id` y el `content_digest` mostrados, y SHALL aplicar el umbral de confianza del perfil (REQ-01-011). Prueba: `integration`.
- **REQ-03-014** WHEN la persona rechaza o elige decidir después, THE SYSTEM SHALL dejar la acción sin ejecutar y permitir editar la propuesta. Prueba: `e2e`.
- **REQ-03-015** IF la persona edita el contenido después de aprobar y antes del despacho, THEN THE SYSTEM SHALL pedir una nueva aprobación sobre el contenido modificado. Prueba: `integration`.
- **REQ-03-016** WHILE una acción está en retención, THE SYSTEM SHALL mostrarla como pendiente de despacho con un control de Alto visible, y la retención SHALL NOT limitar el tiempo de la persona para decidir. Prueba: `e2e`.
- **REQ-03-017** WHEN una acción se despacha, THE SYSTEM SHALL mostrar el resultado (enviada, falló y por qué) y registrarlo en la bitácora. Prueba: `integration`.
- **REQ-03-018** WHERE un cuidador/a con delegación vigente aprueba, THE SYSTEM SHALL mostrárselo a la persona de inmediato y marcar en la bitácora que aprobó el cuidador/a (SP-4). Prueba: `e2e`.
- **REQ-03-019** THE SYSTEM SHALL mostrar las solicitudes de aprobación pendientes en una lista que la persona pueda revisar cuando quiera, sin notificaciones insistentes (AX-13). Prueba: `e2e`.

### Grupo C. Dial de autonomía

- **REQ-03-021** THE SYSTEM SHALL ofrecer el dial de autonomía por tipo de tarea con los niveles N0, N1 y N2, con una descripción llana de lo que hace la IA sola y de lo que aprueba la persona en cada nivel. Prueba: `e2e`.
- **REQ-03-022** THE SYSTEM SHALL iniciar cada tipo de tarea en N0. Prueba: `unit`.
- **REQ-03-023** THE SYSTEM SHALL cambiar el nivel solo por una intención explícita de la persona (o de su cuidador/a con delegación específica) y NOT subirlo ni sugerir subirlo por su cuenta. Prueba: `unit`.
- **REQ-03-024** WHEN la persona baja el nivel, THE SYSTEM SHALL aplicarlo de inmediato, y WHEN lo sube, THE SYSTEM SHALL pedir una aprobación explícita que describa lo que cambia. Prueba: `e2e`.
- **REQ-03-025** THE SYSTEM SHALL mostrar en cada tarea el nivel vigente y permitir cambiarlo sin perder el avance. Prueba: `e2e`.
- **REQ-03-026** THE SYSTEM SHALL NOT dejar que ningún nivel omita la aprobación de una acción con efecto externo. Prueba: `unit`.

### Grupo D. Logros y progreso

**HU-03-D.** Como persona, quiero ver lo que hice y lo que decidí, para confirmar que tengo control.

- **REQ-03-030** WHEN una tarea se completa con su resultado aprobado, THE SYSTEM SHALL registrar un logro con el tipo de tarea, la fecha y lo que la persona decidió (por ejemplo «aprobaste el envío»), sin guardar el contenido salvo que la persona lo pida. Prueba: `integration`.
- **REQ-03-031** THE SYSTEM SHALL mostrar los logros como un registro que solo suma: sin rachas, sin contadores de pérdida y sin avisos de lo que no se hizo (AX-13). Prueba: `a11y` y `manual` (revisión del texto).
- **REQ-03-032** THE SYSTEM SHALL mostrar el panel de progreso con tareas completadas por semana y el tiempo transcurrido desde la primera tarea, calculados a partir de los logros. Prueba: `e2e`.
- **REQ-03-033** THE SYSTEM SHALL permitir a la persona ocultar, exportar o borrar sus logros. Prueba: `e2e`.
- **REQ-03-034** THE SYSTEM SHALL proponer una «siguiente tarea» un poco más grande que la última completada, calculada solo a partir de las tareas completadas (número de micro-pasos y tipos de herramientas) [SUPUESTO] y NOT a partir del estado de ánimo ni de la actividad de la persona. Prueba: `unit`.
- **REQ-03-035** WHEN la persona rechaza la siguiente tarea propuesta, THE SYSTEM SHALL ofrecer otra del mismo tamaño o una más pequeña sin mensaje de reproche. Prueba: `e2e`.
- **REQ-03-036** WHERE la persona dé su consentimiento, THE SYSTEM SHALL enviar al operador contadores agregados y anónimos de la métrica norte (tareas completadas por semana), sin identificadores ni contenido. Prueba: `security`.

### Grupo E. Primera tarea en la sesión 1

- **REQ-03-040** WHEN termina la calibración, THE SYSTEM SHALL ofrecer la **primera tarea** guiada dentro de la misma sesión, elegida por la persona entre las tareas del MVP más cortas. Prueba: `e2e`.
- **REQ-03-041** THE SYSTEM SHALL dejar la primera tarea siempre en N0, con cada micro-paso explicado en lenguaje llano y con la persona decidiendo en cada uno. Prueba: `e2e`.
- **REQ-03-042** WHEN la primera tarea termina, THE SYSTEM SHALL registrarla como el primer logro y mostrar a la persona qué decidió y qué resultado salió al mundo. Prueba: `e2e`.
- **REQ-03-043** IF la persona no quiere hacer la primera tarea en la sesión 1, THEN THE SYSTEM SHALL permitir dejarla para después sin penalización y recordarla solo una vez al volver. Prueba: `e2e`.
- **REQ-03-044** THE SYSTEM SHALL usar en la primera tarea una acción con efecto externo real o simulada claramente identificada [SUPUESTO: por defecto un envío a la propia persona], para que experimente el ciclo completo con riesgo mínimo. Prueba: `e2e`.

### Grupo F. Estados de pantalla

Pantallas: elegir tarea, plan, aprobación, dial, logros, progreso.

- **REQ-03-050** *Cargando.* WHILE se prepara un plan o una propuesta, THE SYSTEM SHALL mostrar qué está haciendo la IA, permitir Alto y permitir seguir editando. Prueba: `e2e`.
- **REQ-03-051** *Vacío.* WHEN no hay tareas ni logros, THE SYSTEM SHALL mostrar un único siguiente paso (elegir una tarea) y no una pantalla en blanco. Prueba: `e2e`.
- **REQ-03-052** *Error.* IF falla la preparación de una propuesta, THEN THE SYSTEM SHALL decir qué pasó, ofrecer reintentar, editar a mano o descartar, y NOT culpar a la persona. Prueba: `e2e`.
- **REQ-03-053** *Sin conexión.* WHILE no hay red, THE SYSTEM SHALL indicar que los agentes no están disponibles, conservar lo ya preparado y permitir editarlo a mano. Prueba: `e2e`.
- **REQ-03-054** THE SYSTEM SHALL cumplir los estados obligatorios de AX-11 en cada pantalla de esta spec. Prueba: `a11y`.

## 4. Requisitos no funcionales

- **REQ-03-060** THE SYSTEM SHALL cumplir WCAG 2.2 AA y, como objetivo AAA, 44×44 px CSS de tamaño de objetivo y ausencia de límites de tiempo en todas las pantallas de esta spec. Prueba: `a11y`.
- **REQ-03-061** THE SYSTEM SHALL mostrar la tarjeta de aprobación con el contenido completo accesible por lector de pantalla y por voz (leer en voz alta con la voz local). Prueba: `a11y`.
- **REQ-03-062** THE SYSTEM SHALL conservar las tareas, los logros y los puntos de control durante una caída del servicio y recuperarlos al volver. Prueba: `integration`.
- **REQ-03-063** THE SYSTEM SHALL NOT usar lenguaje clínico ni promesas de efectos en el panel de progreso ni en los logros (SF-01). Prueba: `audit` (lista de palabras prohibidas en el catálogo de textos).

## 5. Dependencias

| Spec | Relación |
| --- | --- |
| 00 | Tarjeta de aprobación, pantalla de estado, paso a paso |
| 01 | Intenciones `approval.*`, calibración, perfil |
| 02 | Políticas, sellos de aprobación, plan, retención |
| 04 | Herramientas y propuestas de las tres tareas |
| 06 | Delegaciones |
