# companion

Python 3.12 (uv). Control del sistema operativo, adaptadores de entrada, calibración y actuador. Windows primero.

`auth/credential_store.py` implementa la parte local de T-00-011 (REQ-00-022):
credencial por dispositivo en Windows Credential Manager, aislada por servicio HTTPS
y dispositivo. No tiene vencimiento ni cierre por inactividad y no usa archivos de
texto como alternativa. `save` reemplaza la credencial tras una rotación; `clear`
elimina la credencial local al cerrar o revocar la sesión.

El transporte autenticado entre companion y orquestador todavía no existe: debe guardar la
credencial emitida al ingresar o emparejar y cada `X-Credential-Rotated` antes del
siguiente pedido. El almacén por sí solo no conecta el companion al orquestador.

Pruebas desde la raíz: `.venv/Scripts/python.exe -m pytest apps/companion/tests -q`.
La prueba nativa usa un destino aleatorio y lo elimina al terminar. Fuera de Windows
se omite solo esa prueba; el backend nativo falla explícitamente, sin alternativa
insegura. En Windows el proceso necesita acceso al almacén del usuario actual.

## Bus local y perfil

`bus/core.py` valida las publicaciones con `coalsense-intents`, fija el origen del
actor desde la sesión registrada y entrega controles de seguridad antes de las
intenciones normales. La capacidad de referencia de la cola solo activa
coalescencia o descarte de movimiento continuo: no descarta controles ni
aprobaciones. Cada consumidor recibe una copia y un fallo suyo no bloquea al resto.

El registro interno emite credenciales efímeras sin guardarlas en disco y las
revoca de inmediato. Un actor `system` no puede aprobar; el origen `caregiver`
llega intacto al futuro motor de políticas. El umbral de aprobación se proporciona
explícitamente y una aprobación incierta queda fuera de la cola. Existe un puerto
de retroalimentación para conectarlo con la interfaz.

Alto invoca el puerto síncrono `on_stop` antes de encolar, sin tomar el bloqueo de
los consumidores. Un fallo de ese puerto deja el estado `stop_fault` y conserva
la intención para su entrega; no se afirma que la detención física haya ocurrido.
Los fallos de bitácora y retroalimentación tienen contadores observables.

El núcleo ya dispone de named pipe con ACL y host Windows para el supervisor. Las
entregas para actuación llevan un permiso de un solo uso y una generación local;
`ActuationGate` rechaza llamadas directas, entregas de otro bus y actuaciones
anteriores a Alto. La generación no proviene del mensaje del adaptador ni se
añade al esquema que cruza procesos. Tampoco se fusiona movimiento a través de
una generación de Alto.

`HaltController` empieza pausado y da una autorización a cada actuación. Cada
primitiva debe comprobarla mediante `step`; Alto invalida las autorizaciones,
intenta soltar todas las teclas y botones adquiridos por el companion y cancela
las actividades registradas. Si una liberación o cancelación falla, conserva el
recurso para reintentar Alto y bloquea la reanudación. No suelta una tecla que ya
estaba pulsada fuera del companion. Las operaciones del backend deben ser locales
y acotadas; los callbacks de cancelación señalan al trabajador, sin esperar su cierre.

`actuator/windows.py` aporta el backend Win32 SendInput, sin dependencias nuevas:
teclas, botones, movimiento en el escritorio virtual, desplazamiento y caracteres
Unicode. Los pares sustitutos se envían juntos y una inserción parcial intenta
soltar las unidades pendientes. Rechaza fallos de SendInput, coordenadas fuera del
entero nativo y plataformas incompatibles. La marca `COAL` identifica entradas
propias para la futura supresión de eco; no es una credencial de autenticación.

Las pruebas de entrada verifican estructuras y llamadas con una API controlada:
no escriben ni mueven el cursor en el escritorio real. Las pruebas del inspector
de destino también incluyen una consulta Win32 real de solo lectura. La revisión
nativa de entrada con aplicaciones reales, permisos elevados y distintas escalas
DPI sigue pendiente.

## Consumidor de actuación local

`actuator/runtime.py` conecta bus, Alto, permisos de actuación y consumidor. La
factoría inyectable `create_runtime` sirve para pruebas; `create_windows_runtime`
construye el backend SendInput y el inspector Win32. Ambas composiciones empiezan
pausadas y no inician dispositivos, procesos ni servidores. Su `state` exige
evidencia de una ruta de Alto sana antes de permitir reanudar o actuar. Estas
factorías son internas: no deben exponerse a modelos ni al orquestador.

`NativeActuator` se suscribe a puntero, teclas, texto y controles locales. Las
entregas deben proceder de su bus, estar vigentes y no haberse consumido. El origen
`system` puede pausar y emitir Alto, pero no reanudar, deshacer ni inyectar entradas.
La ejecución se serializa con Deshacer. Alto conserva su puerto síncrono separado,
invalida los permisos y se comprueba entre caracteres y primitivas de entrada.

`windows_target.py` consulta identificadores de ventanas, foco y procesos y compara
los niveles de integridad de los tokens. Rechaza ventanas con privilegios más altos
y consultas fallidas. Para puntero revisa la ventana bajo el cursor y el primer
plano, porque el destino de la rueda depende de la configuración de Windows. El
foco de teclado debe pertenecer a la ventana inspeccionada. No lee títulos ni
contenido. Un cambio de destino interrumpe la secuencia; las liberaciones siguen
permitidas para limpiar los recursos adquiridos.

El estado `actuator.dragging` permite consultar el arrastre. Un segundo toggle,
Deshacer o Alto lo termina; un destino no controlable también fuerza la limpieza.
Un fallo de liberación conserva el recurso en el controlador y bloquea reanudar.
El estado y los resultados todavía necesitan el puente al HUD para ser visibles
a la persona; T-01-033 sigue parcial por esa integración y la validación nativa.

Los resultados contienen ID, tipo, código, mensaje del catálogo y una bandera de
posible ejecución parcial. «Se envió la acción» confirma la llamada local, no la
aceptación semántica de una aplicación externa. Un fallo de retroalimentación se
cuenta y no reintenta la entrada. Los acordes validan todas las teclas antes de
comenzar y liberan en orden inverso. El dictado provisional no se inserta. Texto
sin un verificador de edición se registra como irreversible: no se envía un
Backspace genérico para aparentar Deshacer.

Deshacer obtiene un permiso limitado que puede operar mientras la entrada general
está pausada. No la reanuda, no actúa durante una limpieza pendiente y un nuevo
Alto invalida también ese permiso. La pila no ejecuta callbacks bajo el bloqueo
de primitivas del controlador.

`UndoStack` conserva una historia acotada en memoria. Cada clase declara su
reversibilidad y una ocurrencia puede ser irreversible aunque su clase admita
reversión. El texto exige verificación del destino. Una acción irreversible, un
destino no verificado o un fallo incierto no hacen que se revierta otra entrada.
Las excepciones de resultado incierto bloquean el reintento ciego; `UndoNotApplied`
solo corresponde a cancelación anterior a cualquier efecto. El ejecutor debe
serializar las actuaciones nuevas con Deshacer. Los resultados solo contienen
clase, código y mensajes del catálogo, sin contenido del texto.

`profile/validate.py` comprueba rutas de seguridad, el mínimo de 44 px, histéresis,
tiempos de dwell y consentimiento confirmado para una condición declarada. Devuelve
errores comunes sin contenido y no modifica el perfil anterior. El almacenamiento
cifrado y el cambio de perfiles todavía deben usar esta validación.

`uv run --locked python apps/companion/tools/benchmark_bus.py` mide publicación,
validación y entrega local. Es una medición de esta máquina sin cámara ni voz,
no la certificación del hardware de referencia de T-01-047.

## Salud de Alto, latido y supervisión

`bus/stop_state.py` implementa salud por ruta con evidencia de dispositivo
transmitiendo, adaptador respondiendo y Alto vinculado; voz, cabeza y mirada
también exigen modelo cargado. El supervisor conserva el token de cada ruta.
Registrar no demuestra salud, y renovar un token invalida informes del proceso
anterior. Solo se aceptan booleanos reales. No se guardan cuadros, audio ni
condiciones personales en estos estados.

La evidencia caduca en dos segundos `[SUPUESTO]`, configurable mediante
`StopState.max_age_ns`. Los consumidores consultan `snapshot()` antes de actuar;
el bucle de supervisión también debe consultarlo periódicamente. Una pérdida de
la última ruta sana llama primero al puerto interno de Alto e invalida la cola
anterior. La recuperación conserva la pausa hasta una orden nueva de reanudar.
Deshacer sigue disponible con su permiso limitado. Los fallos de limpieza y aviso
se cuentan; no se interpreta un fallo de UI como prueba de una detención física.

`supervisor.py` administra un puerto de proceso por adaptador. Las factorías son
configuración confiable, no comandos del bus. Entrega una credencial efímera en
memoria, la revoca antes de reiniciar y renueva el token de salud. Comprueba salida
y respuestas nuevas; nunca usa salud almacenada en caché para prolongar la vida
de una ruta. Aplica espera exponencial de 250 ms hasta 30 s `[SUPUESTO]`; el conteo
se reinicia tras 30 s estables `[SUPUESTO]`. El arranque sin informes admite hasta
30 s `[SUPUESTO]`, siempre con la ruta no verificada. Un dispositivo desconectado
que sigue reportando salud negativa no se confunde con un proceso caído.

Si una terminación falla, conserva el puerto y reintenta la limpieza, sin lanzar
un segundo proceso que pueda retener el mismo dispositivo. Apagar un adaptador
no programa reinicios hasta volver a habilitarlo. `tick()` debe ejecutarse en el
bucle de aplicación; las consultas y señales del puerto deben ser no bloqueantes.
`process_host.py` implementa el puerto real de Windows descrito más abajo. Las
pruebas combinan puertos controlados y procesos reales con un adaptador de
diagnóstico. Aún no prueban voz, visión ni calibración reales sin conexión.

`uplink/heartbeat.py` produce latidos periódicos validados por el esquema compartido
`packages/intents/schema/heartbeat.schema.json`. Su puerto `send` aún debe conectarse
al WebSocket autenticado sobre TLS. El periodo nominal es un segundo `[SUPUESTO]`.
El receptor compartido `coalsense_intents.heartbeat.HeartbeatReceiver` exige enlazar
explícitamente una instancia autenticada, rechaza repeticiones y revisiones viejas,
y considera falso el estado tras tres segundos sin latidos `[SUPUESTO]`. Usa el
reloj monotónico de recepción, sin confiar en la fecha del otro equipo. Una nueva
conexión a la misma instancia conserva el contador para no admitir mensajes ya
usados; desconectar exige volver a enlazar antes de aceptar datos.

El latido contiene solo identidad técnica de instancia y rutas, secuencia, salud,
motivos enumerados y fechas. No admite biometría, perfil, texto ni órdenes de
actuación. El esquema exige correspondencia entre salud de rutas y estado global.
Los motivos y estados todavía necesitan representación en el HUD; los avisos
urgentes del puerto `on_health` y el receptor aún necesitan su integración real
con interfaz, enlace y consumidores de políticas. T-01-011 y T-01-056 siguen parciales.

## Canal local y host de procesos Windows

`bus/windows_pipe.py` crea una instancia aleatoria por adaptador, con ACL protegida
que permite únicamente el SID del usuario actual. Rechaza conexiones remotas y
comprueba el PID del cliente. El cliente comprueba el PID del servidor antes de
enviar la credencial. No hay herencia de handles del canal ni listeners TCP. La
prueba nativa lee el descriptor real y comprueba la ACE exacta, sin `Everyone`.

El modo mensaje conserva los límites de cada solicitud. La E/S solapada permite
cancelar desde otro hilo. El buffer y OVERLAPPED permanecen vivos hasta terminar
la cancelación; si el mensaje completó justo al vencer la espera, se entrega.
Los plazos técnicos `[SUPUESTO]` son 1 s por operación, hasta 30 s para conectar
y consultas cancelables cada 250 ms. No limitan decisiones de la persona.

`bus/session.py` valida envelopes JSON cerrados, versión y secuencia estrictas,
credencial de la sesión y su vigencia en el registro. Rechaza duplicados de claves,
NaN, JSON inválido y mensajes mayores de 64 KiB `[SUPUESTO]`. Nunca usa pickle.
Una violación cierra la sesión; no hay reintento automático de acciones inciertas.
Las intenciones se publican exclusivamente en el bus, que fija el origen del actor.
Alto sigue siendo síncrono antes de entregar al resto de consumidores. La salud
conserva el tiempo monotónico de recepción: recoger un informe tarde no lo rejuvenece.

`process_host.py` conecta el supervisor con un hijo Python real, oculto y aislado
con `-I`, sin stdout/stderr de contenido. Recibe la credencial una vez por stdin;
no se pone en argumentos, variables de entorno ni archivos. Su entorno contiene
solo variables necesarias de Windows y la selección del venv, sin claves de
proveedores, PYTHONPATH ni PYTHONHOME. El catálogo de módulos es estático; añadir
otro adaptador exige cambiar código y pasar las auditorías. No se importan módulos
elegidos dinámicamente desde mensajes.

En CPython 3.12 Windows el redirector de venv crea otro PID. `process_launch.py`
ejecuta el intérprete base con la selección de venv de CPython para que el PID de
Popen sea el comprobado por el kernel en el pipe. Esto se verificó con un hijo real.
`windows_job.py` asigna el hijo a un Job Object no heredado con terminación al cerrar
el último handle. El cierre del núcleo termina también los procesos asociados.
`stop()` señala/cancela sin esperar; `wait_closed()` permite comprobar el cierre
fuera de la ruta de Alto. Un hijo muerto se considera caído aunque el hilo del canal
esté terminando de limpiar.

El único módulo habilitado es `adapters.idle`, de diagnóstico: informa adaptador
vivo y dispositivo/modelo/Alto no disponibles. Nunca habilita una ruta sana. Las
pruebas reales verifican arranque, intercambio, ACL, rechazo de PID o credencial,
limpieza, revocación y reinicio de un hijo sin reiniciar el otro. No se enviaron
teclas, texto ni movimiento al escritorio real. Siguen pendientes adaptadores
físicos, restricción de egreso por proceso, HUD, enlace remoto y revisión cruzada.

Referencias de implementación: [seguridad de named pipes](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights),
[vida de la E/S cancelada](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelioex),
[Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[selección del intérprete en CPython 3.12](https://github.com/python/cpython/blob/3.12/Modules/getpath.py).
