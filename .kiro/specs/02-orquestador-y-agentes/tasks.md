# Tareas: 02 Orquestador y agentes

**Requisitos:** `requirements.md`. **Diseño:** `design.md`. **Marcas:** `[CODEX]` paralelizable por Codex; `[UI]` interfaz.

**Contexto común (léelo una vez).**
- Código en `apps/orchestrator/src/coalsense_orchestrator/` (FastAPI, Python 3.12, uv) con las carpetas `api/`, `gateway/`, `policy/`, `agents/`, `memory/`, `audit/`, `persistence/`; pruebas en `apps/orchestrator/tests/`.
- **Ley de Arthur:** solo `gateway/` hace llamadas salientes (incluidas las de modelos); los agentes no tienen credenciales de BD ni de terceros; ninguna acción `external_effect` sin sello de aprobación; todo se registra en la bitácora sin contenido.
- Clases de efecto: `read`, `internal_write`, `external_effect`. Sin clase = `external_effect`.
- Sello de aprobación (`ApprovalGrant`): atado a `pending_action_id`, `content_digest` y actor; de un solo uso; **sin vencimiento por tiempo**; se invalida por uso, Alto, cambio de contenido o revocación.
- Las aprobaciones llegan como intenciones `approval.approve` y `approval.reject` (esquema de `packages/intents`).

## Orden de dependencias

```
Ola 0 (spec 00): T-00-007, T-00-008, T-00-010, T-00-011 ; (spec 01): T-01-001, T-01-002
Ola 1: T-02-001, T-02-002
Ola 2: T-02-003, T-02-006, T-02-010
Ola 3: T-02-004, T-02-007, T-02-008, T-02-011, T-02-017
Ola 4: T-02-009, T-02-012, T-02-013, T-02-014, T-02-016, T-02-019, T-02-021, T-02-022, T-02-025
Ola 5: T-02-005, T-02-015, T-02-018, T-02-020, T-02-023, T-02-026, T-02-027
Ola 6: T-02-024, T-02-028
```

---

### T-02-001 API base, contrato versionado y límites
- **Requisitos:** REQ-02-091, REQ-02-092, REQ-02-096
- **Depende de:** T-00-007, T-00-011, T-01-002
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/api/{app,intents_ws,versioning,rate_limit}.py`, `apps/orchestrator/tests/api/test_api_base.py`
- **Qué hacer:** aplicación FastAPI con WebSocket para intenciones y rutas HTTP para clientes. Exigir TLS. Versionar el contrato de intenciones y rechazar con un error claro (formato común de la spec 00) a los clientes con una versión incompatible. Límite de frecuencia por persona que **nunca** aplica a `control.stop`, `control.undo` ni `help.request_human`.
- **Prueba:** `apps/orchestrator/tests/api/test_api_base.py` (contract y unit): versión incompatible rechazada; el límite no afecta a las intenciones `preemptive`; HTTP sin TLS rechazado.
- **Terminado cuando:** la prueba pasa.

### T-02-002 Servicio de persistencia y aislamiento por persona
- **Requisitos:** REQ-02-012, REQ-02-072
- **Depende de:** T-00-007
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/persistence/{service,roles}.py`, `apps/orchestrator/migrations/0002_rls.sql`, `apps/orchestrator/tests/persistence/test_rls.py`
- **Qué hacer:** único módulo con credenciales de BD (roles `app_rw`, `app_ro_audit`, `admin`). Todo acceso con seguridad por filas por `person_id`. Los procesos de agentes se ejecutan sin esas credenciales (variable de entorno ausente y red a la BD bloqueada en su contexto). Escrituras con registro y política.
- **Prueba:** `apps/orchestrator/tests/persistence/test_rls.py` (security): una consulta con la identidad de otra persona no devuelve filas; un proceso sin credenciales no puede conectar.
- **Terminado cuando:** la prueba pasa.

### T-02-003 Bitácora de solo agregado con cadena de hash
- **Requisitos:** REQ-02-080, REQ-02-053
- **Depende de:** T-02-002
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/audit/{log,chain,events}.py`, `apps/orchestrator/migrations/0003_audit.sql`, `apps/orchestrator/tests/audit/test_chain.py`
- **Qué hacer:** tabla `audit_event` solo de inserción (sin permisos UPDATE ni DELETE) con `prev_hash` y `hash`; eventos: plan, paso, llamada a herramienta, decisión de política, aprobación, Alto, Deshacer, derivación (sin contenido). `log.append()` devuelve error si no puede escribir, y el llamador debe no ejecutar acciones `external_effect`.
- **Prueba:** `apps/orchestrator/tests/audit/test_chain.py` (unit y security): alterar una fila rompe la cadena; ningún evento contiene campos de contenido; la imposibilidad de escribir se propaga como error.
- **Terminado cuando:** la prueba pasa.

### T-02-004 Fusión de la bitácora local y permisos de lectura
- **Requisitos:** REQ-02-084, REQ-02-082, REQ-02-083
- **Depende de:** T-02-003, T-00-011
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/audit/{merge,read_api}.py`, `apps/orchestrator/tests/audit/test_merge_read.py`
- **Qué hacer:** aceptar la bitácora local del companion y fusionarla sin duplicados al reconectar (por `id`). API de lectura para la persona; para el cuidador/a solo lo que cubre su delegación; **el rol `operator` no tiene ninguna vía de lectura de la bitácora de contenido** (solo métricas agregadas).
- **Prueba:** `apps/orchestrator/tests/audit/test_merge_read.py` (integration y security): fusión idempotente; `operator` recibe 403; cuidador/a ve solo su alcance.
- **Terminado cuando:** la prueba pasa.

### T-02-005 Pantalla de la bitácora en lenguaje llano [UI]
- **Requisitos:** REQ-02-081
- **Depende de:** T-02-004, T-00-015
- **Archivos:** `apps/web/src/features/audit/{LogView,filters}.tsx`, `apps/web/tests/e2e/audit-log.spec.ts`
- **Qué hacer:** pantalla donde la persona lee la bitácora en lenguaje llano (plantillas deterministas, no generadas por un modelo), la filtra por tarea o fecha y la exporta. Estados cargando, vacío, error, sin conexión.
- **Prueba:** `apps/web/tests/e2e/audit-log.spec.ts` (e2e y a11y).
- **Terminado cuando:** la prueba pasa.

### T-02-006 Manifiesto de herramientas y registro [CODEX]
- **Requisitos:** REQ-02-021, REQ-02-022
- **Depende de:** T-00-007
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/gateway/{manifest,registry}.py`, `packages/intents/schema/tool-manifest.schema.json`, `apps/orchestrator/tests/gateway/test_manifest.py`
- **Qué hacer:** manifiesto por herramienta con nombre, esquema de entrada y salida, clase de efecto, reversibilidad y compensación, categorías de datos que envía y proveedor destino. Si falta la clase de efecto, el registro la trata como `external_effect`.
- **Prueba:** `apps/orchestrator/tests/gateway/test_manifest.py` (contract y unit): manifiesto incompleto falla; sin clase = `external_effect`.
- **Terminado cuando:** la prueba pasa.

### T-02-007 Gateway: ejecución con verificación de sello e idempotencia
- **Requisitos:** REQ-02-020, REQ-02-023, REQ-02-024, REQ-02-032
- **Depende de:** T-02-006, T-02-003
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/gateway/{executor,grant_verify,idempotency,rate_limit}.py`, `apps/orchestrator/tests/gateway/test_executor.py`
- **Qué hacer:** único punto de salida. Para herramientas `external_effect` verifica por sí mismo la firma del sello, el `content_digest` y que no esté usado ni revocado; si no, rechaza. Claves de idempotencia para reintentos. Registra cada llamada (herramienta, clase de efecto, resultado) sin contenido. Cancelación de llamadas en curso.
- **Prueba:** `apps/orchestrator/tests/gateway/test_executor.py` (security): sin sello, con sello de otro contenido o reutilizado, se rechaza; un reintento no repite el efecto.
- **Terminado cuando:** la prueba pasa.

### T-02-008 Constructor de prompts con lista permitida y consentimiento
- **Requisitos:** REQ-02-005, REQ-02-006
- **Depende de:** T-02-006
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/agents/prompt_builder.py`, `apps/orchestrator/src/coalsense_orchestrator/gateway/consent_client.py`, `apps/orchestrator/tests/agents/test_prompt_builder.py`
- **Qué hacer:** el constructor recibe un objeto tipado con solo campos permitidos (instrucción del paso, texto de la tarea, preferencias de memoria) y lanza un error ante cualquier otro; nunca incluye perfil de capacidad, condición declarada ni eventos de crisis. Antes de enviar, consulta el consentimiento vigente de la categoría y proveedor mediante la interfaz `ConsentChecker` (`consent.check`, spec 05) y minimiza el contenido. Hasta que exista T-05-011, usar una implementación simulada que **niega por defecto** (falla cerrada); T-05-011 aporta la real.
- **Prueba:** `apps/orchestrator/tests/agents/test_prompt_builder.py` (security): campos prohibidos lanzan error; sin consentimiento no se construye el envío.
- **Terminado cuando:** la prueba pasa.

### T-02-009 Herramienta `llm.complete`, enrutador y presupuesto
- **Requisitos:** REQ-02-003, REQ-02-004, REQ-02-007
- **Depende de:** T-02-007, T-02-008
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/gateway/tools/llm.py`, `apps/orchestrator/src/coalsense_orchestrator/agents/router.py`, `apps/orchestrator/config/routing.yaml`, `apps/orchestrator/tests/agents/test_router.py`
- **Qué hacer:** `llm.complete` como herramienta del gateway (Claude por API principal; OpenRouter respaldo). Tabla configurable `task_type → modelo principal → respaldo`. Si falla el principal, cambiar al respaldo sin perder estado **solo si hay consentimiento para ese proveedor**; si no, pausar la tarea e informar. Presupuesto de costo por tarea y por persona [SUPUESTO]: al alcanzarlo, detener, informar y dejar que la persona decida.
- **Prueba:** `apps/orchestrator/tests/agents/test_router.py` (unit e integration con proveedores simulados): respaldo con y sin consentimiento; presupuesto detiene.
- **Terminado cuando:** la prueba pasa.

### T-02-010 Motor de políticas núcleo
- **Requisitos:** REQ-02-040, REQ-02-041, REQ-02-049, REQ-02-052
- **Depende de:** T-02-003
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/policy/{engine,rules,loader,versions}.py`, `apps/orchestrator/config/policies/default.yaml`, `apps/orchestrator/tests/policy/test_engine.py`
- **Qué hacer:** el motor decide (permitir, requerir aprobación, denegar), no el agente. Toda acción `external_effect` requiere aprobación; **al cargar una política que permita una acción externa sin aprobación, rechazarla**. Falla cerrada: si el motor falla o no responde, denegar efectos externos. Versionar políticas y registrar cada decisión y cada cambio en la bitácora.
- **Prueba:** `apps/orchestrator/tests/policy/test_engine.py` (unit y security): política permisiva se rechaza al cargar; caída del motor deniega; las decisiones quedan registradas.
- **Terminado cuando:** la prueba pasa.

### T-02-011 Solicitud de aprobación y sello
- **Requisitos:** REQ-02-042, REQ-02-043, REQ-02-044
- **Depende de:** T-02-010, T-02-007
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/policy/{pending_action,grant}.py`, `apps/orchestrator/tests/policy/test_grant.py`
- **Qué hacer:** crear `pending_action` con resumen llano, destino, herramienta, `pending_action_id` y `content_digest` (resumen criptográfico del contenido exacto). Al recibir `approval.approve` válida, emitir el sello firmado atado a esos campos y al actor, de un solo uso y sin `expires_at`. Si el contenido cambia después, invalidar el sello y pedir una nueva aprobación.
- **Prueba:** `apps/orchestrator/tests/policy/test_grant.py` (unit y security): sello de un solo uso; cambiar un byte del contenido lo invalida; no hay vencimiento por tiempo.
- **Terminado cuando:** la prueba pasa.

### T-02-012 Origen y delegaciones en las aprobaciones
- **Requisitos:** REQ-02-045, REQ-02-046
- **Depende de:** T-02-011
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/policy/{origin_check,delegation_client}.py`, `apps/orchestrator/tests/policy/test_origin.py`
- **Qué hacer:** rechazar aprobaciones con `actor_origin = system` o venidas de un agente. Para `actor_origin = caregiver`, consultar la delegación vigente por cuidador/a, alcance, persona y tipo de tarea (spec 06) mediante la interfaz `DelegationLookup` y rechazar si no existe, registrando el intento. Hasta que exista T-06-003, usar una implementación simulada que **niega por defecto**; T-06-003 aporta la real.
- **Prueba:** `apps/orchestrator/tests/policy/test_origin.py` (security): sin delegación el cuidador/a no obtiene sello; con delegación sí y queda marcado el origen; `system` y agentes se rechazan.
- **Terminado cuando:** la prueba pasa.

### T-02-013 Niveles de autonomía en las políticas
- **Requisitos:** REQ-02-047, REQ-02-048
- **Depende de:** T-02-010
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/policy/autonomy.py`, `apps/orchestrator/config/policies/autonomy.yaml`, `apps/orchestrator/tests/policy/test_autonomy.py`
- **Qué hacer:** aplicar N0, N1 y N2 por tipo de tarea a los pasos `read` e `internal_write` según la tabla del diseño de la spec 03. Ningún nivel elimina la aprobación de `external_effect`. Cambiar el nivel solo con una intención de la persona (o de su cuidador/a con delegación específica); el sistema no lo sube ni lo sugiere.
- **Prueba:** `apps/orchestrator/tests/policy/test_autonomy.py` (unit y propiedades): para todas las combinaciones de nivel y clase de efecto, `external_effect` siempre exige aprobación; el nivel solo cambia con intención de la persona.
- **Terminado cuando:** la prueba pasa.

### T-02-014 Retención y despacho
- **Requisitos:** REQ-02-050
- **Depende de:** T-02-011, T-02-007
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/policy/hold.py`, `apps/orchestrator/tests/policy/test_hold.py`
- **Qué hacer:** tras la aprobación, la acción entra en retención con la duración que configuró la persona [SUPUESTO: activada por defecto con un valor corto] y se muestra como pendiente de despacho. `control.stop` durante la retención cancela la acción y revoca el sello.
- **Prueba:** `apps/orchestrator/tests/policy/test_hold.py` (integration): Alto durante la retención cancela y no despacha; sin Alto despacha una sola vez.
- **Terminado cuando:** la prueba pasa.

### T-02-015 Planificador con plan editable
- **Requisitos:** REQ-02-001, REQ-02-002
- **Depende de:** T-02-009, T-02-016
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/agents/planner.py`, `apps/orchestrator/tests/agents/test_planner.py`
- **Qué hacer:** al elegir una tarea, producir un plan de micro-pasos y mostrarlo antes de ejecutar cualquier paso; permitir editarlo, quitar pasos o rechazarlo. Si la persona lo edita, replanificar desde la edición y no ejecutar el plan anterior.
- **Prueba:** `apps/orchestrator/tests/agents/test_planner.py` (integration y unit): nada se ejecuta antes de aprobar el plan; una edición invalida el plan anterior.
- **Terminado cuando:** la prueba pasa.

### T-02-016 Agentes: base, lista permitida, aislamiento, propuestas y puntos de control
- **Requisitos:** REQ-02-010, REQ-02-011, REQ-02-013, REQ-02-014, REQ-02-015, REQ-02-016
- **Depende de:** T-02-007, T-02-002
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/agents/{base,runner,checkpoints,proposals}.py`, `apps/orchestrator/tests/agents/test_agents.py`
- **Qué hacer:** clase base de agente con lista permitida de herramientas y rechazo de las demás; contexto aislado sin estado compartido salvo vía persistencia; su salida es una **propuesta** sin efecto externo; punto de control tras cada micro-paso para reanudar sin repetir pasos aprobados; solo la persona reanuda una tarea detenida; un tiempo de espera técnico de un paso no hace expirar una decisión pendiente.
- **Prueba:** `apps/orchestrator/tests/agents/test_agents.py` (unit e integration): herramienta fuera de lista rechazada; reanudar sin intención se rechaza; timeout técnico no expira una decisión.
- **Terminado cuando:** la prueba pasa.

### T-02-017 Auditoría de límites del gateway y de credenciales [CODEX]
- **Requisitos:** REQ-02-008, REQ-02-020
- **Depende de:** T-00-004
- **Archivos:** `tools/audit/tests/test_gateway_boundaries.py`
- **Qué hacer:** pruebas que usan la auditoría de importaciones de la spec 00 sobre el código real del orquestador: ningún módulo fuera de `gateway/` importa clientes HTTP salientes; `agents/` no importa el cliente de BD de producción.
- **Prueba:** `tools/audit/tests/test_gateway_boundaries.py` (audit).
- **Terminado cuando:** pasa sobre el código del orquestador y corre en la CI.

### T-02-018 Alto en el orquestador
- **Requisitos:** REQ-02-060, REQ-02-061, REQ-02-063
- **Depende de:** T-02-016, T-02-001
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/agents/{halt,supervisor}.py`, `apps/orchestrator/tests/agents/test_halt.py`
- **Qué hacer:** `control.stop` publica `halt` en Redis para la persona; el supervisor cancela todos sus agentes en el siguiente punto de control, cancela llamadas a modelos y herramientas cancelables y despachos no iniciados, y deja las tareas en estado detenido. Notificar a los agentes en un máximo de 500 ms [SUPUESTO]. El Alto local del companion no depende de esta ruta.
- **Prueba:** `apps/orchestrator/tests/agents/test_halt.py` (integration y perf): tras `control.stop` no queda ejecución viva de la persona; la notificación cumple el presupuesto.
- **Terminado cuando:** la prueba pasa.

### T-02-019 Deshacer con compensación
- **Requisitos:** REQ-02-062, REQ-02-064
- **Depende de:** T-02-007
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/gateway/undo.py`, `apps/orchestrator/tests/gateway/test_undo.py`
- **Qué hacer:** `control.undo` ejecuta la compensación declarada de la última acción reversible; si no existe, lo dice con claridad y no revierte otra cosa. Una acción `external_effect` ya despachada y no reversible no se marca como revertida; se informa a la persona.
- **Prueba:** `apps/orchestrator/tests/gateway/test_undo.py` (unit): reversible compensa; irreversible informa.
- **Terminado cuando:** la prueba pasa.

### T-02-020 Bloqueo por `stop_reachable`
- **Requisitos:** REQ-02-051
- **Depende de:** T-02-010, T-01-011
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/policy/stop_gate.py`, `apps/orchestrator/tests/policy/test_stop_gate.py`
- **Qué hacer:** mientras el estado `stop_reachable` de la persona sea falso (o falte el latido del companion), el motor no autoriza ejecución de agentes y se informa a la persona por qué.
- **Prueba:** `apps/orchestrator/tests/policy/test_stop_gate.py` (integration): sin latido o con `stop_reachable = false` no se ejecuta ningún paso.
- **Terminado cuando:** la prueba pasa.

### T-02-021 n8n opcional detrás del gateway [CODEX]
- **Requisitos:** REQ-02-025
- **Depende de:** T-02-007
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/gateway/tools/n8n.py`, `infra/n8n/README.md`, `apps/orchestrator/tests/gateway/test_n8n.py`
- **Qué hacer:** conector que invoca flujos deterministas de n8n solo desde el gateway y solo con sello cuando son `external_effect`. n8n no es alcanzable por los agentes. Está desactivado por defecto hasta resolver su licencia (PA-09).
- **Prueba:** `apps/orchestrator/tests/gateway/test_n8n.py` (audit y integration): ningún agente tiene ruta a n8n; sin sello no se invoca.
- **Terminado cuando:** la prueba pasa.

### T-02-022 MCP: registro, catálogo curado y habilitación por la persona
- **Requisitos:** REQ-02-026, REQ-02-027, REQ-02-030, REQ-02-031
- **Depende de:** T-02-006, T-02-011
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/gateway/mcp/{catalog,enablement,client}.py`, `apps/orchestrator/config/mcp_catalog.yaml`, `apps/orchestrator/tests/gateway/test_mcp_enablement.py`
- **Qué hacer:** registrar servidores MCP como fuente de herramientas del gateway. Catálogo curado por el operador `[SUPUESTO]` con licencia y origen anotados en `THIRD_PARTY.md`. Habilitar un servidor exige una aprobación de la persona (o de su cuidador/a con `tools.manage`) que describa en lenguaje llano las herramientas, los datos que reciben y su clase de efecto; **el sistema nunca habilita ni sugiere habilitar una herramienta por su cuenta**. Cada herramienta nueva se clasifica; sin clase, `external_effect`. Al deshabilitar, dejar de ofrecerla de inmediato y cancelar acciones pendientes que la usen.
- **Prueba:** `apps/orchestrator/tests/gateway/test_mcp_enablement.py` (unit y e2e): sin aprobación no se habilita; no hay ruta de habilitación automática; deshabilitar cancela pendientes.
- **Terminado cuando:** la prueba pasa.

### T-02-023 MCP: aislamiento y salidas no confiables
- **Requisitos:** REQ-02-028, REQ-02-029
- **Depende de:** T-02-022
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/gateway/mcp/{sandbox,untrusted}.py`, `apps/orchestrator/tests/gateway/test_mcp_security.py`
- **Qué hacer:** cada servidor MCP corre con credenciales propias, lista permitida de destinos de red y sin acceso al perfil de capacidad ni a datos de otras personas. Toda salida de una herramienta entra por un canal marcado como **datos**, nunca como instrucciones; no puede ampliar la lista de herramientas ni cambiar políticas.
- **Prueba:** `apps/orchestrator/tests/gateway/test_mcp_security.py` (security): un servidor simulado que intenta salir a un destino no permitido o devolver instrucciones no cambia permisos ni políticas.
- **Terminado cuando:** la prueba pasa.

### T-02-024 Conjunto de pruebas de inyección de prompts [CODEX]
- **Requisitos:** REQ-02-097
- **Depende de:** T-02-023, T-02-011, T-02-016
- **Archivos:** `apps/orchestrator/tests/security/test_prompt_injection.py`, `apps/orchestrator/tests/security/injection_corpus.yaml`
- **Qué hacer:** corpus de documentos, correos y salidas MCP con instrucciones maliciosas (enviar datos, cambiar destinatarios, deshabilitar políticas, pedir aprobar). Verificar que ninguno provoca una acción `external_effect` sin sello ni cambia herramientas permitidas.
- **Prueba:** `apps/orchestrator/tests/security/test_prompt_injection.py` (security).
- **Terminado cuando:** todos los casos del corpus pasan.

### T-02-025 Memoria por persona
- **Requisitos:** REQ-02-070, REQ-02-071, REQ-02-073
- **Depende de:** T-02-002
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/memory/{store,crypto,api}.py`, `apps/orchestrator/migrations/0004_memory.sql`, `apps/orchestrator/tests/memory/test_memory.py`
- **Qué hacer:** memoria en pgvector (preferencias, tono, resúmenes de entregables) cifrada con la clave de datos de la persona; la persona puede verla, editarla y borrarla. Nunca guarda el perfil de capacidad, la condición declarada ni el contenido de eventos de crisis. Los embeddings los calcula un modelo con consentimiento o uno local en el servidor [SUPUESTO].
- **Prueba:** `apps/orchestrator/tests/memory/test_memory.py` (security y e2e): la memoria se cifra; un intento de guardar campos prohibidos se rechaza; borrar un elemento lo elimina.
- **Terminado cuando:** la prueba pasa.

### T-02-026 Modos degradados
- **Requisitos:** REQ-02-090
- **Depende de:** T-02-009
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/api/degraded.py`, `apps/orchestrator/tests/api/test_degraded.py`
- **Qué hacer:** sin modelo o sin servicio, devolver estados claros (sin conexión o error de AX-11) y dejar que la persona conserve el control del PC y la edición manual. Mensajes con el formato de error común.
- **Prueba:** `apps/orchestrator/tests/api/test_degraded.py` (e2e): con el proveedor de modelo caído la API responde con el estado degradado y la edición manual sigue disponible.
- **Terminado cuando:** la prueba pasa.

### T-02-027 Métricas operativas sin contenido y retención cero de prompts
- **Requisitos:** REQ-02-093, REQ-02-098
- **Depende de:** T-00-008, T-02-009
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/observability/metrics.py`, `apps/orchestrator/tests/observability/test_metrics.py`
- **Qué hacer:** emitir métricas (latencias, errores, costos agregados) sin contenido; no almacenar ni registrar el texto de prompts y respuestas de modelos más allá de lo que la persona ve en sus propuestas.
- **Prueba:** `apps/orchestrator/tests/observability/test_metrics.py` (security e integration): un prompt de muestra no aparece en ningún registro ni métrica.
- **Terminado cuando:** la prueba pasa.

### T-02-028 Pruebas de rendimiento de plan y aprobación [CODEX]
- **Requisitos:** REQ-02-094, REQ-02-095
- **Depende de:** T-02-015, T-02-011
- **Archivos:** `apps/orchestrator/tests/perf/test_latency.py`
- **Qué hacer:** medir con un proveedor simulado el tiempo hasta mostrar el plan (p95 ≤ 10 s) y hasta presentar una solicitud de aprobación (≤ 1 s) [SUPUESTO]; reportar y ajustar los valores con datos reales del proveedor.
- **Prueba:** `apps/orchestrator/tests/perf/test_latency.py` (perf).
- **Terminado cuando:** la prueba pasa o los presupuestos se actualizan con una nota.

