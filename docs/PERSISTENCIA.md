# Persistencia: primera integración con PostgreSQL

Avance de T-02-002 y T-02-003. No cierra el servicio de persistencia del MVP, la memoria ni los
entregables. Las tareas de la web todavía viven en memoria y no llaman este servicio.

## Contrato disponible

`PersistenceService` permite crear tareas, listar y consultar las de la persona y
pausar una tarea usando la revisión esperada. Sus filas tienen identificadores,
persona, tipo, estado, N0, revisión y fechas. No tienen título, destinatarios, cuerpo,
prompts ni respuestas. Guardar esos contenidos requiere el cifrado de T-07-003 y las
versiones de T-04-003; no se añadieron columnas de texto en claro para adelantarlo.

La identidad se obtiene del `Principal` autenticado que entregará la API. Solo se
admite el rol persona con el alcance correspondiente. No se aceptan aprobaciones
del cuidador/a por defecto; falta integrar su delegación. La API todavía no expone
estas operaciones ni autentica solicitudes de tareas hacia este servicio.

Las escrituras consultan un puerto de política con persona, operación y recurso.
Sin implementación, ante error o sin un `True` exacto se deniegan. La implementación
que permite escribir existe únicamente en las pruebas; no es una política desplegada.

## Aislamiento y transacciones

La migración crea los grupos sin LOGIN `app_rw`, `app_ro_audit` y `admin`, y el
esquema `coalsense`. Los usuarios de ejecución se provisionan por separado. El
servicio rechaza usuarios superadministradores, BYPASSRLS, permisos de administración,
pertenencia a `admin` y un grupo `app_rw` inseguro. No entrega conexiones ni SQL a
los agentes. El único import de asyncpg en código de producto está en persistencia.

Las tablas activan y fuerzan RLS, incluido el propietario. Cada operación abre una
transacción y fija su persona con `set_config(..., true)`. La configuración termina
con la transacción, y las consultas no necesitan un filtro manual de propietario.
La selección sin contexto no ve filas. El permiso de actualización no incluye
cambiar persona, identificador ni autonomía. La semántica corresponde a la
[documentación de RLS](https://www.postgresql.org/docs/16/ddl-rowsecurity.html) y a
[configuración local de transacción](https://www.postgresql.org/docs/16/functions-admin.html#FUNCTIONS-ADMIN-SET).

Cada escritura de tarea inserta un evento mínimo en la misma transacción. Si no
puede insertar el evento, la tarea se revierte. La referencia del evento incluye
persona y recurso; no puede apuntar a una tarea de otra persona. El usuario de
ejecución no puede modificar, borrar ni truncar eventos. La migración `0003_audit.sql`
incorpora la bitácora encadenada de T-02-003 y convierte los eventos provisionales
conservando identificadores, fechas y persona. La tabla anterior queda en lectura.
Los detalles, el formato y los límites están en `docs/BITACORA.md`.

Los errores públicos son códigos fijos nuevos, sin mensaje, consulta, parámetros
ni contexto de excepción del controlador. La integración encontró que `contextlib`
podía volver a adjuntar un error interno; el límite público descarta esa cadena.
También normaliza el UUID del controlador al tipo de la biblioteca estándar.

## Prueba disponible

`infra/compose.test.yaml` fija la imagen por digest y usa únicamente datos sintéticos
en memoria temporal, puerto loopback y contraseñas aleatorias que no se versionan.
`pnpm --filter @coalsense/orchestrator test:integration` exige la infraestructura y
ejecuta los casos reales. La fixture borra solo su proyecto aleatorio al terminar.
La etapa de CI se configuró para descargar la imagen y ejecutar esta tarea junto a
las pruebas web; no se ejecutó un pipeline remoto en esta sesión.

Se comprueban aislamiento entre personas, consultas concurrentes por el pool, RLS
directo sin filtro de aplicación, rol del propietario, rechazo de roles de ejecución
privilegiados, revisión obsoleta, reinicio del servicio, reversión por fallo de registro
y por cancelación, credenciales ausentes en un proceso hijo y conservación del pool.
El proceso hijo sin credenciales falla al autenticarse; eso **no prueba** bloqueo de
red. `agent_environment` prepara un entorno mínimo para un lanzador todavía pendiente.

## Límites pendientes

La variable de persona en PostgreSQL protege las consultas del servicio de filtros
de aplicación omitidos; no convierte una credencial de BD comprometida en una
identidad autenticada. Las credenciales son exclusivas del servicio de persistencia,
cuya conexión es de confianza. Faltan el lanzador de agentes y su aislamiento de red.

El migrador versionado aplica también los esquemas históricos de autenticación,
pero su repositorio de ejecución sigue en memoria. Falta adaptar esa persistencia,
además de memoria por persona, cifrado, claves, almacenamiento durable,
consentimientos reales, conexión de la bitácora a todos los ejecutores y políticas completas. El inventario de
datos de T-07-001 y las revisiones humanas y cruzadas siguen pendientes. No se
acredita un entorno productivo con la instancia de prueba temporal.

`0004_policy.sql` ya guarda políticas por persona, versiones inmutables y un puntero
activo que solo avanza. La activación y su evento de bitácora son atómicos. El motor
interno las consulta, pero todavía no hay despacho ni interfaz conectados. Véase
`POLITICAS.md` para las guardas y los límites de esta integración parcial.

## Migraciones administrativas

`tools/migrate.py` consulta el plan por defecto y solo aplica con `--apply`.
Requiere `COALSENSE_MIGRATION_DATABASE_URL`, separada de las credenciales de la
aplicación. Su valor se configura fuera del repositorio; no se imprime. Ejemplos
desde la raíz, una vez configurada esa variable para la base correspondiente:

```powershell
uv run --locked python apps/orchestrator/tools/migrate.py
uv run --locked python apps/orchestrator/tools/migrate.py --apply
```

TLS verificado es el valor por defecto. `--local-test` admite exclusivamente la
excepción loopback ya validada por `DatabaseSettings`, para la instancia sintética.
Se exige un rol administrativo separado y se rechaza el usuario de ejecución.
El comando devuelve JSON con nombres de archivos o un código fijo de error.

El historial guarda el nombre completo y SHA-256 del SQL con finales de línea
normalizados. Los prefijos numéricos históricos repetidos se distinguen por el
nombre completo. Solo se permite extender el historial: cambiar, omitir o insertar
antes un archivo aplicado invalida el plan. La aplicación de archivos pendientes y
su registro ocurren en una transacción con exclusión entre migradores. Un fallo de
SQL revierte el lote. Los archivos son código administrativo de confianza del repo;
no se cargan migraciones aportadas por personas usuarias ni por agentes.

La conversión de la bitácora bloquea las escrituras antiguas mientras recorre el
registro provisional. Restaura y fuerza RLS antes de terminar. Las pruebas usan una
base sintética separada para conservar eventos preexistentes y para ejecutar dos
migradores simultáneos. No se ejecutaron migraciones contra una base productiva.

## Consentimientos

`0009_consent.sql` agrega una tabla de solo inserción para el rol de aplicación
con RLS forzada. PostgreSQL recibe el ID de la persona, el ID del registro, el
orden y un sobre opaco. Categoría, proveedor, versión, decisión, modalidad y
fecha se empaquetan dentro del sobre. El puerto `ConsentCipher` requiere cifrado
autenticado con la DEK de la persona y contexto asociado al ID de ambos.
Su implementación y gestión de claves de producción dependen de T-07-003.
El doble de prueba usa referencias en memoria para verificar el contrato.

El servicio consulta el historial en orden, sin caché ni vencimiento temporal.
La última decisión solo vale para el mismo proveedor y categoría y para la
versión activa del aviso. Rechazar o revocar impide usar los datos y suprime
la solicitud repetida de esa versión. El catálogo de avisos se configura al
construir el servicio. Un despliegue que actualice avisos debe mantener la misma
versión activa en todos los procesos. Falta exponer una pantalla autenticada
y exportación para la persona.
