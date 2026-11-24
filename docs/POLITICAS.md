# Motor de políticas

Avance de T-02-010 y de las guardas de autonomía de la spec 03. El motor, las
aprobaciones y el ejecutor se integran por interfaces internas del servidor.
La ruta autenticada y la interfaz de persona siguen pendientes.

## Fuentes de confianza

`EvaluationRequest` admite identificador de acción, identificador de tarea y nombre
de herramienta. El registro de manifiestos determina la clase de efecto. El servidor
obtiene la persona del `Principal`, consulta la política activa y lee el contexto
persistido. La solicitud no puede declarar autonomía, alcance, salud del Alto,
pausa ni clase de efecto.

`TaskContextLookup` lee pertenencia, revisión, estado y autonomía de la tarea.
El llamador de confianza selecciona la etapa. Todas las tareas actuales permanecen
en N0; no existe una operación para elevarlas. La clasificación de primera tarea
está sin conectar y se devuelve como desconocida. En N1/N2 esa ausencia impide
permitir pasos automáticamente.

`HeartbeatStopHealth` consulta el receptor compartido de latidos. El transporte debe
enlazarlo a la sesión autenticada correspondiente; ese transporte sigue pendiente.
Las pruebas usan un receptor real con reloj simulado. `DenyStopHealth` niega siempre.
Los casos SQL que simulan salud disponible no acreditan una conexión física.

## Decisiones

Se niega ante actor o alcance insuficiente, herramienta desconocida, política o
contexto ausente, pertenencia incorrecta, tarea pausada, Alto inaccesible o fallo
de una dependencia. Las modificaciones exigen permiso de escritura. Después se
aplica esta tabla, sin que un agente pueda cambiarla:

| Condición | Resultado |
| --- | --- |
| Regla configurada que niega | `deny` |
| Efecto externo | `require_approval` |
| Primera tarea declarada | `require_approval` |
| N0 | `require_approval` |
| N1/N2 con primera tarea desconocida | `deny` |
| Resultado final en N1/N2 | `require_approval` |
| Paso interno en N1/N2 con contexto completo | Regla configurada |

Cada evaluación intenta registrar resultado, acción, regla, versión, herramienta,
clase de efecto y referencias de pertenencia verificadas. Espera el commit antes
de devolver una decisión que permita continuar o solicite aprobación. Un fallo de
registro devuelve denegación sin identificador de evento; no se afirma que ese
fallo haya quedado guardado. Las cancelaciones se propagan.

[SUPUESTO] Consultas y registro tienen sendos límites técnicos de dos segundos,
configurables al construir el componente. No son plazos de aprobación humana.

La decisión incluye revisión de contexto y digest de política. El servicio de
aprobaciones comprueba esos valores otra vez cuando se aprueba y cuando el
gateway consume el sello. También exige una evaluación vigente con Alto accesible.
Estas consultas no reservan los valores en las dependencias remotas.

## Configuración y persistencia

`apps/orchestrator/config/policies/default.yaml` usa el subconjunto JSON de YAML
para no añadir un parser. El esquema cerrado exige versión positiva segura para
JavaScript y una regla por clase de efecto, con identificadores únicos y decisiones
cerradas. Una regla externa con `allow` es inválida en Python y SQL.
[SUPUESTO] Los prefijos `guard.` y `policy.` se reservan para reglas del servidor;
los identificadores usan la gramática compartida de nombres de herramientas.

`activate_policy` es una operación interna, sin endpoint de cliente. Guarda por
persona una instantánea canónica y su SHA-256, actualiza el puntero activo y agrega
el evento de activación en una sola transacción. No modifica autonomía. Repetir la
misma versión y contenido es idempotente; reemplazar una versión o retroceder se
rechaza. Un fallo de bitácora conserva la versión anterior.

`0004_policy.sql` fuerza RLS y separa versiones inmutables del puntero activo. La
aplicación puede insertar y leer versiones propias, pero no modificarlas, borrarlas
ni truncarlas. El puntero solo avanza. Configuración y digest no contienen texto de
tareas. El rol compartido de base de datos sigue siendo una frontera de confianza;
estas comprobaciones no sustituyen la autenticación del servicio.

Registrar una evaluación de lectura exige alcance de lectura, porque es
instrumentación obligatoria del servidor. Esto no concede permiso para editar
contenido ni activar políticas. No hay una API pública para insertar bitácora.

## Aprobación y despacho

`ApprovalService` conserva la vista y la entrada aprobada en memoria de un único
proceso. Calcula el SHA-256 de una representación JSON que incluye herramienta,
resumen, destinos y entrada validada. La interfaz deberá mostrar la entrada
exacta junto con el resumen y los destinos. Editar retira la versión anterior
antes de proponer otra. El transporte debe atribuir las intenciones a un
`Principal` autenticado y vigente. Por ahora solo se admite aprobación personal.

Tras registrar la aprobación, el servicio emite un sello HMAC-SHA-256 ligado a la
acción, el contenido, la persona, la sesión, la política y la revisión. No tiene
vencimiento por tiempo. El consumo retira la acción y su sello antes de devolver
la entrada congelada. El reinicio pierde las solicitudes y revoca sus sellos.
La copia exacta, sus destinos, el digest y el sello quedan fuera de la bitácora.

`ExternalExecutor` verifica el sello antes de consultar la solicitud. Tras esperar
la retención fijada por su llamador interno, registra el intento y revalida la
política. Consulta el consentimiento antes de consumir el sello y llamar al
adaptador registrado con la copia aprobada
y el ID de acción como clave de idempotencia. No reintenta automáticamente. Alto
cancela la retención, elimina las solicitudes de esa persona y pide cancelar
los trabajos en curso. Si un proveedor aceptó un efecto antes de la cancelación
o de un fallo de registro, el resultado puede quedar sin confirmar.

## Pendiente

El servicio de consentimiento ya consulta un historial por persona y versión de
aviso. Falta conectar el cifrado autenticado por persona y el catálogo de avisos
en producción. También están pendientes la activación por persona, los adaptadores reales y
verificación de la idempotencia en cada proveedor. También faltan la recepción
autenticada de Alto y aprobaciones, la presentación de retención y resultados en
la interfaz y la coordinación entre procesos. La pérdida de borradores privados
al reiniciar se resolverá con almacenamiento cifrado cuando se implemente. Siguen
pendientes las delegaciones y la clasificación de primera tarea.
