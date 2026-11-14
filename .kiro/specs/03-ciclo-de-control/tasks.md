# Tareas: 03 Ciclo de control

**Requisitos:** `requirements.md`. **Diseño:** `design.md`. **Marcas:** `[CODEX]` paralelizable por Codex; `[UI]` interfaz.

**Contexto común (léelo una vez).**
- Backend en `apps/orchestrator/src/coalsense_orchestrator/tasks/` y `.../achievements/`; interfaz en `apps/web/src/features/` (Next.js + `packages/ui`); pruebas en `apps/orchestrator/tests/tasks/` y `apps/web/tests/`.
- Estados de una tarea: elegida, en plan, en ejecución, pendiente de aprobación, en retención, despachada, completada, pausada, detenida, descartada. **Ninguna transición ocurre por tiempo.**
- Niveles de autonomía: N0 (por defecto), N1, N2. Ningún nivel elimina la aprobación de una acción con efecto externo.
- El progreso solo suma: sin rachas, sin contadores de pérdida, sin lenguaje clínico ni de reproche.
- Aprobaciones: intenciones `approval.approve` y `approval.reject` con `pending_action_id` y `content_digest`.

## Orden de dependencias

```
Ola 0 (specs 00, 01, 02): T-00-014, T-00-015, T-02-011, T-02-013, T-02-014, T-02-015, T-02-018, T-01-040
Ola 1: T-03-001
Ola 2: T-03-002, T-03-005, T-03-009, T-03-011
Ola 3: T-03-003, T-03-004, T-03-006, T-03-007, T-03-008, T-03-010, T-03-013, T-03-014
Ola 4: T-03-012, T-03-015, T-03-017
Ola 5: T-03-016
```

---

### T-03-001 Modelo de tareas, micro-pasos y máquina de estados
- **Requisitos:** REQ-03-002, REQ-03-004, REQ-03-005, REQ-03-007
- **Depende de:** T-02-002, T-02-016
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/tasks/{models,state_machine,steps}.py`, `apps/orchestrator/migrations/0005_tasks.sql`, `apps/orchestrator/tests/tasks/test_state_machine.py`
- **Qué hacer:** modelo de `task`, `step` y `task_type` con la máquina de estados del diseño. Una tarea solo la inicia la persona (o su cuidador/a con `tasks.start`); el sistema puede proponer pero no empezar. Pausar y retomar sin perder avance. Descartar conserva lo hecho hasta que la persona lo borre y no se registra como fallo.
- **Prueba:** `apps/orchestrator/tests/tasks/test_state_machine.py` (unit y propiedades): ninguna transición ocurre por el paso del tiempo; el sistema no puede iniciar una tarea; descartar no crea un registro de fallo.
- **Terminado cuando:** la prueba pasa.

### T-03-002 API de tareas y catálogo de tipos
- **Requisitos:** REQ-03-001, REQ-03-003
- **Depende de:** T-03-001
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/tasks/api.py`, `apps/orchestrator/tests/tasks/test_api.py`
- **Qué hacer:** endpoints para listar los tipos de tarea disponibles (los tres del MVP y los que aporten herramientas habilitadas), crear una tarea con los datos mínimos para empezar (por ejemplo destinatario y propósito) y consultar su estado.
- **Prueba:** `apps/orchestrator/tests/tasks/test_api.py` (integration): el catálogo incluye los tres tipos; crear una tarea no exige formularios largos; una herramienta no habilitada no ofrece su tipo.
- **Terminado cuando:** la prueba pasa.

### T-03-003 Pantalla para elegir tarea [UI]
- **Requisitos:** REQ-03-001, REQ-03-003, REQ-03-051
- **Depende de:** T-03-002, T-00-015
- **Archivos:** `apps/web/src/features/tasks/{ChooseTask,MinimalInputs}.tsx`, `apps/web/tests/e2e/choose-task.spec.ts`
- **Qué hacer:** catálogo de tareas elegible con cualquier modalidad; pedir solo datos mínimos por dictado o selección. Estado vacío con un único siguiente paso (elegir una tarea). Estados cargando, error, sin conexión.
- **Prueba:** `apps/web/tests/e2e/choose-task.spec.ts` (e2e y a11y): flujo solo con teclado e intenciones simuladas; axe-core sin violaciones.
- **Terminado cuando:** la prueba pasa.

### T-03-004 Plan, estado y control de la tarea [UI]
- **Requisitos:** REQ-03-005, REQ-03-006, REQ-03-008, REQ-03-050, REQ-03-052, REQ-03-053
- **Depende de:** T-03-001, T-02-015, T-00-015
- **Archivos:** `apps/web/src/features/tasks/{PlanView,TaskStatus,StoppedTask}.tsx`, `apps/web/tests/e2e/task-flow.spec.ts`
- **Qué hacer:** mostrar el plan de micro-pasos editable, el estado actual con texto (no solo color), y los controles de pausar y retomar sin límite de tiempo. Tras Alto mostrar qué se detuvo y qué quedó hecho, con retomar, editar o descartar. Estados *cargando* (qué hace la IA, con Alto y edición posibles), *error* (reintentar, editar a mano o descartar, sin culpar) y *sin conexión* (conservar lo preparado, edición manual).
- **Prueba:** `apps/web/tests/e2e/task-flow.spec.ts` (e2e y a11y).
- **Terminado cuando:** la prueba pasa.

### T-03-005 Servicio de aprobación en el ciclo
- **Requisitos:** REQ-03-012, REQ-03-013, REQ-03-014, REQ-03-015
- **Depende de:** T-02-011, T-03-001
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/tasks/approvals.py`, `apps/orchestrator/tests/tasks/test_approvals.py`
- **Qué hacer:** conectar las solicitudes de aprobación del motor de políticas con las tareas: aprobar envía `approval.approve` con el `pending_action_id` y `content_digest` mostrados y aplica el umbral de confianza del perfil; rechazar o «decidir después» deja la acción sin ejecutar y permite editar; editar tras aprobar y antes del despacho exige una nueva aprobación. **Nunca aprobar por inacción**: una aprobación pendiente permanece pendiente sin límite de tiempo.
- **Prueba:** `apps/orchestrator/tests/tasks/test_approvals.py` (unit e integration): sin acción de la persona no hay aprobación aunque pase el tiempo; editar tras aprobar invalida el sello.
- **Terminado cuando:** la prueba pasa.

### T-03-006 Tarjeta de aprobación integrada y lista de pendientes [UI]
- **Requisitos:** REQ-03-010, REQ-03-011, REQ-03-019, REQ-03-061
- **Depende de:** T-03-005, T-00-015
- **Archivos:** `apps/web/src/features/approvals/{ApprovalScreen,PendingList}.tsx`, `apps/web/tests/e2e/approval-card.spec.ts`
- **Qué hacer:** usar la `ApprovalCard` de `packages/ui` con el contenido exacto, destinatarios y efecto en lenguaje llano; aprobar, rechazar y decidir después con el mismo tamaño, sin opción preseleccionada. Lista de aprobaciones pendientes consultable cuando la persona quiera, sin notificaciones insistentes. Contenido completo accesible por lector de pantalla y por voz (leer en voz alta con la voz local).
- **Prueba:** `apps/web/tests/e2e/approval-card.spec.ts` (e2e y a11y): sin preselección; aprobar y rechazar equivalentes en tamaño y acceso; lectura en voz alta disponible.
- **Terminado cuando:** la prueba pasa.

### T-03-007 Retención visible y resultado del despacho [UI]
- **Requisitos:** REQ-03-016, REQ-03-017
- **Depende de:** T-02-014, T-03-006
- **Archivos:** `apps/web/src/features/approvals/{HoldView,DispatchResult}.tsx`, `apps/web/tests/e2e/hold-dispatch.spec.ts`
- **Qué hacer:** durante la retención mostrar la acción como pendiente de despacho con la barra de Alto visible; la retención no limita el tiempo de la persona para decidir. Tras el despacho mostrar el resultado (enviada, falló y por qué) y registrarlo en la bitácora.
- **Prueba:** `apps/web/tests/e2e/hold-dispatch.spec.ts` (e2e): Alto durante la retención cancela; el resultado se muestra y queda en la bitácora.
- **Terminado cuando:** la prueba pasa.

### T-03-008 Aprobación de cuidador/a visible a la persona
- **Requisitos:** REQ-03-018
- **Depende de:** T-02-012, T-03-005
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/tasks/caregiver_notice.py`, `apps/web/src/features/approvals/CaregiverApprovedNotice.tsx`, `apps/web/tests/e2e/caregiver-notice.spec.ts`
- **Qué hacer:** cuando un cuidador/a con delegación vigente aprueba, mostrárselo de inmediato a la persona, marcarlo en la bitácora y mantener la acción en retención para que la persona pueda usar Alto.
- **Prueba:** `apps/web/tests/e2e/caregiver-notice.spec.ts` (e2e): la persona ve el aviso y puede cancelar con Alto durante la retención.
- **Terminado cuando:** la prueba pasa.

### T-03-009 Dial de autonomía: configuración y reglas
- **Requisitos:** REQ-03-022, REQ-03-023, REQ-03-024, REQ-03-026
- **Depende de:** T-02-013, T-03-001
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/tasks/autonomy_settings.py`, `apps/orchestrator/tests/tasks/test_autonomy_settings.py`
- **Qué hacer:** guardar el nivel por tipo de tarea (inicia en N0). Solo la persona (o su cuidador/a con `autonomy.set`) lo cambia, con una intención explícita; el sistema no lo sube ni lo sugiere. Subir exige una aprobación que describa lo que cambia; bajar es inmediato. Verificar que ningún nivel omite la aprobación externa.
- **Prueba:** `apps/orchestrator/tests/tasks/test_autonomy_settings.py` (unit): todos los tipos inician en N0; subir sin aprobación se rechaza; bajar aplica de inmediato.
- **Terminado cuando:** la prueba pasa.

### T-03-010 Pantalla del dial de autonomía [UI]
- **Requisitos:** REQ-03-021, REQ-03-025
- **Depende de:** T-03-009, T-00-015
- **Archivos:** `apps/web/src/features/autonomy/{AutonomyDial,LevelDescriptions}.tsx`, `apps/web/tests/e2e/autonomy-dial.spec.ts`
- **Qué hacer:** pantalla con los niveles N0, N1 y N2 por tipo de tarea, con una descripción llana de lo que hace la IA sola y de lo que aprueba la persona en cada uno; mostrar el nivel vigente en cada tarea y permitir cambiarlo sin perder el avance.
- **Prueba:** `apps/web/tests/e2e/autonomy-dial.spec.ts` (e2e y a11y).
- **Terminado cuando:** la prueba pasa.

### T-03-011 Logros: registro, ocultar, exportar y borrar
- **Requisitos:** REQ-03-030, REQ-03-033
- **Depende de:** T-03-001
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/achievements/{models,service,api}.py`, `apps/orchestrator/migrations/0006_achievements.sql`, `apps/orchestrator/tests/achievements/test_achievements.py`
- **Qué hacer:** al completarse una tarea con resultado aprobado, crear un logro con tipo de tarea, fecha y las decisiones de la persona («aprobaste el envío»), **sin guardar el contenido**. La persona puede ocultar, exportar y borrar sus logros.
- **Prueba:** `apps/orchestrator/tests/achievements/test_achievements.py` (integration y security): el logro no contiene texto de la tarea; ocultar, exportar y borrar funcionan.
- **Terminado cuando:** la prueba pasa.

### T-03-012 Logros y progreso sin rachas [UI]
- **Requisitos:** REQ-03-031, REQ-03-032
- **Depende de:** T-03-011, T-00-015
- **Archivos:** `apps/web/src/features/achievements/{AchievementsList,ProgressPanel}.tsx`, `apps/web/tests/e2e/achievements.spec.ts`
- **Qué hacer:** lista de logros que solo suma y panel de progreso con tareas completadas por semana y tiempo desde la primera tarea. Sin rachas, sin contadores de pérdida y sin «días sin actividad». Estado vacío con un único siguiente paso.
- **Prueba:** `apps/web/tests/e2e/achievements.spec.ts` (e2e y a11y): ningún elemento muestra pérdida o reproche; el estado vacío ofrece elegir una tarea.
- **Terminado cuando:** la prueba pasa.

### T-03-013 Siguiente tarea propuesta
- **Requisitos:** REQ-03-034, REQ-03-035
- **Depende de:** T-03-011
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/tasks/next_task.py`, `apps/orchestrator/tests/tasks/test_next_task.py`
- **Qué hacer:** proponer una tarea un poco más grande que la última completada, calculada solo con el número de micro-pasos y los tipos de herramienta de las tareas completadas [SUPUESTO: un micro-paso o una herramienta más]. No usa estado de ánimo, frecuencia de uso ni tiempo entre sesiones. Si la persona la rechaza, ofrecer otra del mismo tamaño o más pequeña sin mensaje de reproche.
- **Prueba:** `apps/orchestrator/tests/tasks/test_next_task.py` (unit): la propuesta solo depende de tareas completadas; el rechazo no empeora el tamaño ni registra reproche.
- **Terminado cuando:** la prueba pasa.

### T-03-014 Métrica norte agregada con consentimiento
- **Requisitos:** REQ-03-036
- **Depende de:** T-03-011
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/achievements/metrics.py`, `apps/orchestrator/tests/achievements/test_metrics.py`
- **Qué hacer:** con el consentimiento `aggregate_metrics` (spec 05), enviar al operador contadores agregados y anónimos de tareas completadas por semana, sin identificador ni contenido. Sin consentimiento no se envía nada.
- **Prueba:** `apps/orchestrator/tests/achievements/test_metrics.py` (security): sin consentimiento no hay envío; con consentimiento el payload no contiene identificadores.
- **Terminado cuando:** la prueba pasa.

### T-03-015 Primera tarea de la sesión 1
- **Requisitos:** REQ-03-040, REQ-03-041, REQ-03-042, REQ-03-043, REQ-03-044
- **Depende de:** T-03-005, T-03-011, T-01-040, T-03-003
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/tasks/first_task.py`, `apps/web/src/features/onboarding/FirstTask.tsx`, `apps/web/tests/e2e/first-task.spec.ts`
- **Qué hacer:** al terminar la calibración (`calibration.completed`), ofrecer la primera tarea guiada en la misma sesión, elegida por la persona entre las más cortas del MVP. Siempre en N0, con cada micro-paso explicado en lenguaje llano. Incluye una acción con efecto externo real o simulada claramente identificada [SUPUESTO: por defecto un envío a la propia persona]. Al terminar, registrar el primer logro y mostrar qué decidió y qué salió al mundo. Si la persona la deja para después, sin penalización y con un solo recordatorio al volver.
- **Prueba:** `apps/web/tests/e2e/first-task.spec.ts` (e2e): de la calibración simulada a la primera tarea completada; dejarla para después no deja marca de fallo y recuerda una sola vez.
- **Terminado cuando:** la prueba pasa.

### T-03-016 Accesibilidad y textos de 03 [CODEX]
- **Requisitos:** REQ-03-054, REQ-03-060, REQ-03-063
- **Depende de:** T-03-006, T-03-010, T-03-012, T-03-004
- **Archivos:** `apps/web/tests/a11y/control-cycle.spec.ts`, `tools/audit/tests/test_copy_control_cycle.py`
- **Qué hacer:** suite que recorre las pantallas y estados de 03 con axe-core (WCAG 2.2 AA), 44×44 px y ausencia de límites de tiempo; auditoría de textos que falla si hay lenguaje clínico, rachas o reproche en el panel de progreso y los logros.
- **Prueba:** `apps/web/tests/a11y/control-cycle.spec.ts` (a11y) y `tools/audit/tests/test_copy_control_cycle.py` (audit).
- **Terminado cuando:** ambas pruebas pasan en la CI.

### T-03-017 Recuperación tras una caída del servicio [CODEX]
- **Requisitos:** REQ-03-062
- **Depende de:** T-03-001, T-02-016
- **Archivos:** `apps/orchestrator/tests/tasks/test_recovery.py`
- **Qué hacer:** probar que tareas, logros y puntos de control se conservan al reiniciar el servicio y que una tarea en estado detenido o pendiente de aprobación sigue así tras la recuperación.
- **Prueba:** `apps/orchestrator/tests/tasks/test_recovery.py` (integration).
- **Terminado cuando:** la prueba pasa.
