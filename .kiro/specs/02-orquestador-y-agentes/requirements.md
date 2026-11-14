# Requisitos: 02 Orquestador y agentes

**Estado:** completo. Notación y tipos de prueba: `01-capa-de-entrada/requirements.md` sección 0.
**Cubre:** planificador y enrutador, agentes de trabajo, gateway de herramientas (nativas, n8n y servidores MCP), motor de políticas, memoria y bitácora.
**Vertical aplicable:** V-01, V-03, V-04, V-08, V-09, V-11, V-12. Propiedades: SP-1, SP-2, SP-4, SP-6.

## 1. Alcance

Dentro: razonar, planificar y delegar; ejecutar herramientas por el gateway; decidir con políticas; recordar; registrar en la bitácora.
Fuera: pantallas de aprobación y logros (03), herramientas concretas de las tres tareas (04), detección de crisis (05), delegaciones del cuidador/a (06, aquí solo se verifican), retención y borrado a nivel plataforma (07).

## 2. Requisitos funcionales

### Grupo A. Planificador y enrutador

**HU-02-A.** Como persona, quiero ver qué va a hacer la IA antes de que lo haga y poder cambiarlo, para que la decisión siga siendo mía.

- **REQ-02-001** WHEN la persona elige una tarea, THE SYSTEM SHALL producir un plan de micro-pasos y mostrarlo a la persona antes de ejecutar cualquier paso, permitiendo editarlo, quitar pasos o rechazarlo. Prueba: `integration`.
- **REQ-02-002** WHEN la persona edita el plan, THE SYSTEM SHALL replanificar a partir de la edición y NOT ejecutar el plan anterior. Prueba: `unit`.
- **REQ-02-003** THE SYSTEM SHALL enrutar cada llamada a un modelo según el tipo de tarea con una tabla configurable (Claude por API como proveedor principal y OpenRouter como respaldo). Prueba: `unit`.
- **REQ-02-004** IF el proveedor principal no está disponible, THEN THE SYSTEM SHALL cambiar al respaldo sin perder el estado de la tarea, siempre que la persona haya dado consentimiento para ese proveedor; si no lo hay, THE SYSTEM SHALL pausar la tarea e informar a la persona. Prueba: `integration`.
- **REQ-02-005** THE SYSTEM SHALL construir los prompts con un constructor que solo admite campos de una lista permitida, y SHALL NOT incluir el perfil de capacidad, la condición declarada ni el contenido de eventos de crisis (SP-6). Prueba: `security`.
- **REQ-02-006** THE SYSTEM SHALL enviar a los proveedores de modelos el mínimo contenido necesario para el paso (minimización) y solo con consentimiento vigente de la categoría correspondiente (spec 05). Prueba: `security`.
- **REQ-02-007** THE SYSTEM SHALL aplicar un presupuesto de costo por tarea y por persona [SUPUESTO], y WHEN se alcanza, SHALL detener la ejecución, informar y permitir que la persona decida si continúa. Prueba: `unit`.
- **REQ-02-008** THE SYSTEM SHALL NOT incluir en el orquestador ni en los agentes llamadas HTTP salientes fuera del gateway de herramientas. Prueba: `audit`.

### Grupo B. Agentes de trabajo

- **REQ-02-010** THE SYSTEM SHALL definir cada agente con una lista permitida de herramientas (mínimo privilegio) y rechazar cualquier llamada a una herramienta fuera de ella. Prueba: `unit`.
- **REQ-02-011** THE SYSTEM SHALL ejecutar cada agente en un contexto aislado, sin estado mutable compartido salvo a través del servicio de persistencia. Prueba: `unit`.
- **REQ-02-012** THE SYSTEM SHALL NOT dar a los agentes credenciales de la base de datos de producción; toda escritura pasa por el servicio de persistencia, que aplica política. Prueba: `audit` y `security`.
- **REQ-02-013** THE SYSTEM SHALL tratar la salida de un agente como una **propuesta** (borrador, documento, publicación preparada) sin efecto externo hasta que la persona la apruebe. Prueba: `integration`.
- **REQ-02-014** THE SYSTEM SHALL guardar un punto de control tras cada micro-paso, de modo que una tarea detenida pueda reanudarse sin repetir pasos ya aprobados. Prueba: `integration`.
- **REQ-02-015** THE SYSTEM SHALL NOT reanudar una tarea detenida sin una intención explícita de la persona. Prueba: `integration`.
- **REQ-02-016** THE SYSTEM SHALL NOT dejar que un tiempo de espera técnico de un paso haga expirar una decisión pendiente de la persona. Prueba: `unit`.

### Grupo C. Gateway de herramientas (nativas, n8n y MCP)

**HU-02-C.** Como persona, quiero que mi catálogo de herramientas crezca según lo que necesito, y decidir yo cuáles se conectan, para trabajar con mis propias cuentas sin perder el control.

- **REQ-02-020** THE SYSTEM SHALL exponer toda capacidad externa como una herramienta del gateway, con esquema de entrada y salida, y SHALL NOT permitir al orquestador ni a los agentes llamar APIs por otra vía (V-08). Prueba: `audit`.
- **REQ-02-021** THE SYSTEM SHALL exigir en el manifiesto de cada herramienta: nombre, esquema, clase de efecto (`read`, `internal_write`, `external_effect`), si es reversible, categorías de datos que envía y proveedor destino. Prueba: `contract`.
- **REQ-02-022** IF una herramienta no declara su clase de efecto, THEN THE SYSTEM SHALL tratarla como `external_effect`. Prueba: `unit`.
- **REQ-02-023** THE SYSTEM SHALL rechazar la ejecución de una herramienta `external_effect` que no presente un sello de aprobación válido (SP-1). Prueba: `security`.
- **REQ-02-024** THE SYSTEM SHALL usar claves de idempotencia en las herramientas `external_effect` para que un reintento no repita el efecto. Prueba: `integration`.
- **REQ-02-025** THE SYSTEM SHALL invocar las acciones externas deterministas mediante flujos de n8n solo desde el gateway, y NOT exponer n8n a los agentes. Prueba: `audit`.
- **REQ-02-026** WHERE la persona (o su cuidador/a con delegación) conecta un servidor MCP, THE SYSTEM SHALL registrarlo como fuente de herramientas del gateway, mostrar en lenguaje llano qué herramientas aporta, qué datos reciben y su clase de efecto, y habilitarlo solo con la intención explícita de la persona. Prueba: `e2e`.
- **REQ-02-027** THE SYSTEM SHALL NOT habilitar ni sugerir activar por su cuenta una herramienta o servidor MCP; el catálogo solo crece por decisión de la persona. Prueba: `unit`.
- **REQ-02-028** THE SYSTEM SHALL tratar toda salida de una herramienta, incluidas las de servidores MCP, como **datos no confiables**, nunca como instrucciones, y SHALL NOT permitir que el contenido de una salida cambie la lista de herramientas permitidas ni las políticas. Prueba: `security` (pruebas de inyección de prompt).
- **REQ-02-029** THE SYSTEM SHALL ejecutar cada servidor MCP con mínimo privilegio: credenciales propias de ese servidor, lista permitida de destinos de red y ningún acceso al perfil de capacidad ni a datos de otras personas. Prueba: `security`.
- **REQ-02-030** THE SYSTEM SHALL admitir en el MVP solo servidores MCP de un catálogo curado por el operador `[SUPUESTO]`, y SHALL registrar la licencia y el origen de cada uno en `THIRD_PARTY.md`. Prueba: `audit`.
- **REQ-02-031** WHEN la persona deshabilita una herramienta o servidor MCP, THE SYSTEM SHALL dejar de ofrecerlo de inmediato y cancelar las acciones pendientes que lo usen. Prueba: `e2e`.
- **REQ-02-032** THE SYSTEM SHALL registrar en la bitácora cada llamada a una herramienta (herramienta, clase de efecto, resultado) sin incluir su contenido. Prueba: `integration`.

### Grupo D. Motor de políticas

- **REQ-02-040** THE SYSTEM SHALL decidir en el motor de políticas, y no en el agente, si una acción se permite, requiere aprobación o se deniega. Prueba: `unit`.
- **REQ-02-041** THE SYSTEM SHALL exigir aprobación para toda acción `external_effect`, y SHALL rechazar al cargar cualquier política que permita una acción externa sin aprobación (gana V-01). Prueba: `unit`.
- **REQ-02-042** WHEN una acción requiere aprobación, THE SYSTEM SHALL crear una solicitud con un resumen en lenguaje llano, el destino o destinatarios, la herramienta, el `pending_action_id` y el resumen criptográfico (`content_digest`) del contenido exacto. Prueba: `unit`.
- **REQ-02-043** WHEN llega una `approval.approve` válida para una solicitud pendiente, THE SYSTEM SHALL emitir un sello de aprobación atado al `pending_action_id`, al `content_digest` y al actor, de un solo uso y sin vencimiento por tiempo. Prueba: `unit`.
- **REQ-02-044** IF el contenido de la acción cambia después de la aprobación, THEN THE SYSTEM SHALL invalidar el sello y pedir una nueva aprobación. Prueba: `unit`.
- **REQ-02-045** WHEN llega una aprobación con `actor_origin = caregiver`, THE SYSTEM SHALL verificar una delegación vigente que cubra ese tipo de aprobación y esa persona, y IF no la hay, THEN rechazarla (SP-4). Prueba: `security`.
- **REQ-02-046** IF una aprobación llega con `actor_origin = system` o desde un agente, THEN THE SYSTEM SHALL rechazarla y registrar el intento. Prueba: `security`.
- **REQ-02-047** THE SYSTEM SHALL aplicar el nivel de autonomía de la tarea (N0, N1, N2; spec 03) a los pasos internos, y NOT permitir que ningún nivel elimine la aprobación de una acción `external_effect` (C-08). Prueba: `unit`.
- **REQ-02-048** THE SYSTEM SHALL cambiar el nivel de autonomía solo por una intención de la persona (o de su cuidador/a con delegación explícita para ello) y NOT subirlo por su cuenta ni sugerir subirlo. Prueba: `unit`.
- **REQ-02-049** IF el motor de políticas falla o no responde, THEN THE SYSTEM SHALL denegar toda acción `external_effect` (falla cerrada). Prueba: `security`.
- **REQ-02-050** WHEN una acción aprobada entra en retención, THE SYSTEM SHALL mostrarla como pendiente de despacho y cancelarla si llega `control.stop` durante la retención. La duración de la retención la configura la persona [SUPUESTO: activada por defecto con un valor corto]. Prueba: `integration`.
- **REQ-02-051** WHILE `stop_reachable` es falso, THE SYSTEM SHALL no ejecutar acciones de agentes y SHALL informar a la persona por qué. Prueba: `integration`.
- **REQ-02-052** THE SYSTEM SHALL versionar las políticas, registrar en la bitácora cada decisión (acción, decisión, regla) y cada cambio de política. Prueba: `integration`.
- **REQ-02-053** IF no se puede escribir en la bitácora, THEN THE SYSTEM SHALL NOT ejecutar acciones `external_effect`. Prueba: `security`.

### Grupo E. Alto y Deshacer en el orquestador

- **REQ-02-060** WHEN llega `control.stop` de una persona, THE SYSTEM SHALL cancelar todas las ejecuciones de esa persona (agentes, llamadas a modelos y herramientas cancelables), cancelar los despachos no iniciados y dejar las tareas en estado detenido (SP-2). Prueba: `integration`.
- **REQ-02-061** THE SYSTEM SHALL notificar `control.stop` a todos los agentes de la persona en un tiempo máximo de 500 ms [SUPUESTO] y los agentes SHALL detenerse en su siguiente punto de control. Prueba: `perf`.
- **REQ-02-062** WHEN llega `control.undo`, THE SYSTEM SHALL revertir la última acción cuya herramienta declare una compensación reversible, y IF no existe, THEN decirlo con claridad y sin revertir otra cosa. Prueba: `unit`.
- **REQ-02-063** THE SYSTEM SHALL NOT hacer depender el Alto local del companion de la respuesta del orquestador (01 REQ-01-019). Prueba: `integration`.
- **REQ-02-064** THE SYSTEM SHALL impedir que una acción `external_effect` ya despachada se marque como revertida si su herramienta no es reversible, y SHALL informar a la persona. Prueba: `unit`.

### Grupo F. Memoria

- **REQ-02-070** THE SYSTEM SHALL guardar por persona una memoria (preferencias, tono, resúmenes de entregables anteriores) que la persona pueda ver, editar y borrar. Prueba: `e2e`.
- **REQ-02-071** THE SYSTEM SHALL NOT guardar en la memoria el perfil de capacidad, la condición declarada ni el contenido de eventos de crisis. Prueba: `security`.
- **REQ-02-072** THE SYSTEM SHALL aislar la memoria por persona a nivel de base de datos (seguridad por filas) de modo que una consulta de otra persona no devuelva nada. Prueba: `security`.
- **REQ-02-073** THE SYSTEM SHALL cifrar el contenido de la memoria con una clave por persona. Prueba: `security`.

### Grupo G. Bitácora

- **REQ-02-080** THE SYSTEM SHALL registrar en una bitácora de solo agregado todo lo que se ejecuta (plan, paso, llamada a herramienta, decisión de política, aprobación, Alto, Deshacer) como metadatos, sin contenido privado, con encadenamiento por hash para detectar alteraciones [SUPUESTO]. Prueba: `unit`.
- **REQ-02-081** THE SYSTEM SHALL permitir a la persona leer la bitácora en lenguaje llano, filtrarla y exportarla, con una pantalla accesible. Prueba: `e2e`.
- **REQ-02-082** THE SYSTEM SHALL NOT dar al operador ninguna vía para leer el contenido de la bitácora ni de las tareas; el operador solo ve métricas agregadas de operación (V-11). Prueba: `security`.
- **REQ-02-083** WHERE el cuidador/a tiene una delegación, THE SYSTEM SHALL mostrarle de la bitácora solo lo que la delegación cubre. Prueba: `security`.
- **REQ-02-084** THE SYSTEM SHALL aceptar la bitácora local del companion (generada sin conexión) y fusionarla sin duplicados al reconectar. Prueba: `integration`.

### Grupo H. Operación

- **REQ-02-090** THE SYSTEM SHALL ofrecer modos degradados: sin modelo disponible, la persona conserva el control del PC y la edición manual; el sistema lo dice con claridad (estado sin conexión o error de AX-11). Prueba: `e2e`.
- **REQ-02-091** THE SYSTEM SHALL versionar el contrato de intenciones y rechazar con un error claro a los clientes con una versión incompatible. Prueba: `contract`.
- **REQ-02-092** THE SYSTEM SHALL limitar la frecuencia de solicitudes por persona sin afectar a `control.stop`, `control.undo` ni `help.request_human`. Prueba: `unit`.
- **REQ-02-093** THE SYSTEM SHALL NOT almacenar ni registrar el texto de los prompts ni de las respuestas de los modelos salvo lo que la persona vea en sus propuestas. Prueba: `security`.

## 3. Requisitos no funcionales [SUPUESTO en las cifras]

- **REQ-02-094** THE SYSTEM SHALL mostrar el plan de una tarea al menos al 95% de las solicitudes en un máximo de 10 s con el proveedor principal disponible [SUPUESTO]. Prueba: `perf`.
- **REQ-02-095** THE SYSTEM SHALL presentar una solicitud de aprobación a la persona en un máximo de 1 s tras generarse [SUPUESTO]. Prueba: `perf`.
- **REQ-02-096** THE SYSTEM SHALL cifrar con TLS todo el tráfico entre clientes, orquestador, gateway y proveedores. Prueba: `security`.
- **REQ-02-097** THE SYSTEM SHALL resistir las pruebas de inyección de prompt del conjunto de seguridad: ninguna salida de herramienta o de documento de la persona puede provocar una acción `external_effect` sin aprobación. Prueba: `security`.
- **REQ-02-098** THE SYSTEM SHALL emitir métricas operativas sin contenido (latencias, errores, costos agregados) para el operador. Prueba: `integration`.

## 4. Dependencias

| Spec | Relación |
| --- | --- |
| 01 | Consume intenciones; usa `stop_reachable`, latido y `actor_origin` |
| 03 | Define niveles de autonomía y pantallas de aprobación |
| 04 | Aporta las herramientas y agentes de las tres tareas |
| 05 | Aporta consentimientos vigentes y la ruta humana |
| 06 | Aporta delegaciones vigentes |
| 07 | Aporta claves, retención, exportación y borrado |
