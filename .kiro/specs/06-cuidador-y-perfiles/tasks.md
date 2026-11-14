# Tareas: 06 Cuidador y perfiles

**Requisitos:** `requirements.md`. **Diseño:** `design.md`. **Marcas:** `[CODEX]` paralelizable por Codex; `[UI]` interfaz.

**Contexto común (léelo una vez).**
- Backend en `apps/orchestrator/src/coalsense_orchestrator/caregivers/`; interfaz en `apps/web/src/features/caregivers/`; pruebas en `apps/orchestrator/tests/caregivers/` y `apps/web/tests/`.
- Alcances de delegación del MVP: `devices.configure`, `profile.edit`, `progress.view`, `content.view`, `tasks.start`, `tools.manage`, `autonomy.set`, `consents.assist`, `approval.grant` (este último limitado a tipos de tarea que indique la persona).
- **Solo la persona crea o cambia una delegación**; el cuidador/a solo puede pedirla. Todo permiso es visible, revocable al instante y deja rastro. El filtro de lo que ve el cuidador/a se aplica **en el servidor**.
- La condición declarada **nunca** es visible para un cuidador/a.

## Orden de dependencias

```
Ola 0 (specs 00, 01, 02): T-00-011, T-00-015, T-02-012, T-01-016
Ola 1: T-06-001
Ola 2: T-06-002, T-06-003
Ola 3: T-06-004, T-06-005, T-06-006, T-06-009, T-06-010
Ola 4: T-06-007, T-06-008, T-06-011
Ola 5: T-06-012
```

---

### T-06-001 Modelo de datos de cuidadores, invitaciones y delegaciones
- **Requisitos:** REQ-06-010, REQ-06-062
- **Depende de:** T-00-011, T-02-002
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/caregivers/{models,signing}.py`, `apps/orchestrator/migrations/0010_caregivers.sql`, `apps/orchestrator/tests/caregivers/test_models_signing.py`
- **Qué hacer:** tablas `caregiver`, `invitation`, `delegation` (cuidador/a, alcances, tipos de tarea, inicio, fin opcional elegido por la persona, estado vigente, revocada o vencida) y `caregiver_activity`. Firmar cada delegación y rechazar las alteradas. Cifrar en reposo.
- **Prueba:** `apps/orchestrator/tests/caregivers/test_models_signing.py` (contract y security): una delegación con un byte alterado se rechaza; el esquema valida los campos.
- **Terminado cuando:** la prueba pasa.

### T-06-002 Invitación, cuenta del cuidador/a y reglas de invitación
- **Requisitos:** REQ-06-001, REQ-06-002, REQ-06-003, REQ-06-004, REQ-06-005, REQ-06-006
- **Depende de:** T-06-001
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/caregivers/{invitations,accounts}.py`, `apps/orchestrator/tests/caregivers/test_invitations.py`
- **Qué hacer:** la persona invita a un cuidador/a por correo o código y define en la misma invitación los alcances; un cuidador/a recién invitado no tiene **ningún** alcance salvo los marcados. Cuenta y sesión propias con rol `caregiver`. Soportar varios o ningún cuidador/a. Al aceptar, mostrar a la persona quién aceptó y qué puede hacer y registrarlo. Un cuidador/a no puede invitar a otro ni otorgarse alcances; rechazar que una persona se invite a sí misma como cuidador/a.
- **Prueba:** `apps/orchestrator/tests/caregivers/test_invitations.py` (unit y security).
- **Terminado cuando:** la prueba pasa.

### T-06-003 Creación y consulta de delegaciones
- **Requisitos:** REQ-06-011, REQ-06-013, REQ-06-014, REQ-06-016
- **Depende de:** T-06-001
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/caregivers/{delegations,query}.py`, `apps/orchestrator/tests/caregivers/test_delegations.py`
- **Qué hacer:** crear, ampliar o cambiar una delegación solo por una intención de la persona (`actor_origin = person`); una solicitud del cuidador/a solo crea una petición. El alcance `approval.grant` exige indicar tipos de tarea y una aprobación explícita de la persona que describa su efecto. Servicio de consulta de delegación vigente (cuidador/a, alcance, persona, tipo de tarea) que responde con el estado del momento; una delegación con fecha de fin queda vencida al llegar.
- **Prueba:** `apps/orchestrator/tests/caregivers/test_delegations.py` (security y contract): un cuidador/a no se amplía permisos; `approval.grant` sin tipos de tarea se rechaza; vencida no se usa.
- **Terminado cuando:** la prueba pasa.

### T-06-004 Revocación inmediata y rechazo sin delegación
- **Requisitos:** REQ-06-012, REQ-06-015, REQ-06-061
- **Depende de:** T-06-003, T-02-014
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/caregivers/{revocation,guard}.py`, `apps/orchestrator/tests/caregivers/test_revocation.py`
- **Qué hacer:** revocar por cualquier modalidad (intención `delegation.revoke` o pantalla) aplica de inmediato: invalida las sesiones de acción del cuidador/a para ese alcance y cancela sus acciones pendientes de despacho. Una acción sin delegación vigente que la cubra se rechaza, se registra el intento y el cuidador/a recibe un mensaje claro. Aplicar la revocación en ≤ 2 s p95 [SUPUESTO].
- **Prueba:** `apps/orchestrator/tests/caregivers/test_revocation.py` (integration, security y perf): tras revocar, una acción en retención del cuidador/a se cancela; sin delegación se rechaza.
- **Terminado cuando:** la prueba pasa.

### T-06-005 Registro de actividad de acompañantes
- **Requisitos:** REQ-06-017, REQ-06-018
- **Depende de:** T-06-001, T-02-003
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/caregivers/activity.py`, `apps/orchestrator/tests/caregivers/test_activity.py`
- **Qué hacer:** registrar cada uso de una delegación (quién, alcance, acción, cuándo) sin contenido y mostrarlo a la persona. El cuidador/a no puede ocultar, borrar ni alterar su propio registro.
- **Prueba:** `apps/orchestrator/tests/caregivers/test_activity.py` (security): un cuidador/a no puede modificar ni borrar su actividad; el registro no contiene contenido.
- **Terminado cuando:** la prueba pasa.

### T-06-006 Control por alcance en la API
- **Requisitos:** REQ-06-031, REQ-06-032, REQ-06-035, REQ-06-036
- **Depende de:** T-06-003, T-00-011
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/caregivers/scope_guard.py`, `apps/orchestrator/tests/caregivers/test_scope_guard.py`
- **Qué hacer:** cada recurso declara el alcance requerido; sin él la API no devuelve datos. El cuidador/a no ve contenido, memoria ni bitácora de contenido sin `content.view`; con `progress.view` ve solo contadores sin títulos; **nunca** ve la condición declarada; no puede exportar ni borrar datos de la persona; no recibe alertas de crisis salvo que sea además el contacto de confianza autorizado.
- **Prueba:** `apps/orchestrator/tests/caregivers/test_scope_guard.py` (security): matriz de alcances × recursos; la condición declarada devuelve vacío para todos los alcances.
- **Terminado cuando:** la prueba pasa.

### T-06-007 Pantallas de la persona sobre sus cuidadores/as [UI]
- **Requisitos:** REQ-06-019, REQ-06-050
- **Depende de:** T-06-004, T-06-005, T-00-015
- **Archivos:** `apps/web/src/features/caregivers/{MyCaregivers,Delegations,CaregiverActivity}.tsx`, `apps/web/tests/e2e/my-caregivers.spec.ts`
- **Qué hacer:** «Mis cuidadores/as y permisos» (lista, invitar, revocar en un paso, alcances en lenguaje llano, `approval.grant` destacado) y «Lo que hicieron mis cuidadores/as». Estados: vacío (sin cuidadores: ofrecer invitar sin presionar), cargando, error, sin conexión.
- **Prueba:** `apps/web/tests/e2e/my-caregivers.spec.ts` (e2e y a11y): revocar con intención simulada de voz; axe-core sin violaciones.
- **Terminado cuando:** la prueba pasa.

### T-06-008 Panel del cuidador/a [UI]
- **Requisitos:** REQ-06-030, REQ-06-034, REQ-06-050
- **Depende de:** T-06-006, T-06-009, T-00-015
- **Archivos:** `apps/web/src/features/caregivers/panel/{CaregiverPanel,DevicesView,ProgressCounters}.tsx`, `apps/web/tests/e2e/caregiver-panel.spec.ts`
- **Qué hacer:** panel limitado por los alcances: estado de dispositivos y modalidades, ayuda con la calibración, perfiles, contadores de progreso y su propia actividad. Cada acción indica que actúa por delegación de la persona y bajo qué alcance. Estados: cargando, vacío, error, sin conexión y modalidad no detectada (vista de dispositivos).
- **Prueba:** `apps/web/tests/e2e/caregiver-panel.spec.ts` (e2e y a11y): un cuidador/a sin `content.view` no ve contenido; los alcances limitan las secciones.
- **Terminado cuando:** la prueba pasa.

### T-06-009 Calibración asistida con origen de cuidador/a
- **Requisitos:** REQ-06-033
- **Depende de:** T-06-003, T-01-040, T-01-032
- **Archivos:** `apps/companion/src/coalsense_companion/calibration/assisted.py`, `apps/companion/tests/calibration/test_assisted.py`
- **Qué hacer:** con `devices.configure`, el cuidador/a inicia la calibración asistida del companion y prueba dispositivos con teclado y mouse; las intenciones llevan `actor_origin = caregiver`. Sin delegación no puede iniciarla.
- **Prueba:** `apps/companion/tests/calibration/test_assisted.py` (integration): la calibración asistida marca el origen; sin delegación se rechaza.
- **Terminado cuando:** la prueba pasa.

### T-06-010 Versiones de perfil pendientes y cuenta de la persona
- **Requisitos:** REQ-06-040, REQ-06-041, REQ-06-042, REQ-06-043, REQ-06-044
- **Depende de:** T-06-003, T-01-016
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/caregivers/profile_versions.py`, `apps/orchestrator/tests/caregivers/test_profile_versions.py`
- **Qué hacer:** listar los perfiles de capacidad con su historial de versiones (para la persona y para un cuidador/a con `profile.edit`). Un cambio de cuidador/a crea una versión en estado `proposed` que la persona aprueba o revierte y **no** sustituye la versión en uso sin su aprobación. Validar con las invariantes de la spec 01 (ruta de Alto y Deshacer en cada modalidad habilitada) también al proponer. Mantener separados los datos de la cuenta (nombre, idioma, preferencias, condición declarada opcional) y el perfil de capacidad. Exportar y borrar perfiles y cuenta solo por la persona (spec 07).
- **Prueba:** `apps/orchestrator/tests/caregivers/test_profile_versions.py` (unit y security): una versión propuesta sin Alto y Deshacer se rechaza; no se aplica sin aprobación de la persona.
- **Terminado cuando:** la prueba pasa.

### T-06-011 Vista de perfiles y versión pendiente [UI]
- **Requisitos:** REQ-06-040, REQ-06-041
- **Depende de:** T-06-010, T-01-017
- **Archivos:** `apps/web/src/features/caregivers/{ProfilesList,PendingVersion}.tsx`, `apps/web/tests/e2e/pending-profile-version.spec.ts`
- **Qué hacer:** lista de perfiles con historial y pantalla de versión pendiente que muestra qué cambió en lenguaje llano y permite aprobar o revertir con cualquier modalidad.
- **Prueba:** `apps/web/tests/e2e/pending-profile-version.spec.ts` (e2e y a11y).
- **Terminado cuando:** la prueba pasa.

### T-06-012 Accesibilidad y cifrado de 06 [CODEX]
- **Requisitos:** REQ-06-060, REQ-06-063
- **Depende de:** T-06-007, T-06-008, T-06-011
- **Archivos:** `apps/web/tests/a11y/caregivers.spec.ts`, `apps/orchestrator/tests/caregivers/test_encryption.py`
- **Qué hacer:** suite de accesibilidad (WCAG 2.2 AA, 44×44 px, sin límites de tiempo) del panel y de la vista de delegaciones de la persona; prueba de que delegaciones y actividad se guardan cifradas.
- **Prueba:** `apps/web/tests/a11y/caregivers.spec.ts` (a11y) y `apps/orchestrator/tests/caregivers/test_encryption.py` (security).
- **Terminado cuando:** ambas pasan.
