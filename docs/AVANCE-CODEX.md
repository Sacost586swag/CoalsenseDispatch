# Avance de construcción — 16 al 18 de noviembre de 2026

## Punto de partida

Se conservaron los cambios existentes de autenticación y navegación accesible.
El repositorio contenía sesiones, roles y revocación en desarrollo (T-00-011),
pero el companion todavía era un esqueleto y faltaba T-00-017.

## Construcción de esta sesión

- T-00-011, parte local (REQ-00-022): `CredentialStore`, con Windows Credential
  Manager mediante `ctypes`, sin dependencias nuevas ni archivos de texto.
  Aislamiento por origen HTTPS y dispositivo, persistencia entre instancias,
  reemplazo de credenciales al rotar, borrado idempotente y errores sin secretos.
- T-00-017 (REQ-00-049, REQ-00-062): catálogo Vite de los once componentes
  existentes, con 28 ejemplos y URLs por estado. Suite Playwright de 59 casos,
  ambos temas, axe-core con contraste activo, geometría real de 44 px y 64 px en
  modo cabeza, teclado, restauración del foco y reflujo al ampliar texto.
- CI: tareas `test:a11y`, `test:integration` y `build:catalog`, instalación de
  Chromium y bibliotecas del sistema para las etapas de navegador. El catálogo
  se compila antes de las pruebas, para evitar recargas del servidor de desarrollo.
- Se corrigieron dos pruebas anteriores de navegación: geometría simulada en
  jsdom y actualización del registro antes de leerlo. No se eliminó la exclusión
  de controles ocultos o de tamaño cero.
- Registro de las dependencias Vite y Playwright ya presentes en el workspace,
  documentación de uso y `packages/ui/DESIGN.md`. Reflujo corregido para etiquetas
  largas del catálogo con texto al 200 %.

## Evidencia local

| Comprobación                                                            | Resultado       |
| ----------------------------------------------------------------------- | --------------- |
| pytest, autenticación del orquestador y common-py                       | 118 pasan       |
| pytest, companion, incluido almacén nativo de Windows                   | 24 pasan        |
| Vitest, componentes y registro                                          | 106 pasan       |
| node:test, tokens                                                       | 11 pasan        |
| Playwright, catálogo compilado                                          | 59 pasan        |
| pytest, contrato de CI actualizado                                      | 57 pasan        |
| mypy, companion y orquestador                                           | Sin errores     |
| tsc, UI incluido catálogo y pruebas de navegador                        | Sin errores     |
| ESLint, UI y regla geométrica                                           | Sin errores     |
| Ruff, módulos Python cambiados                                          | Sin errores     |
| Prettier, paquete UI                                                    | Sin diferencias |
| Build de UI y del catálogo                                              | Correctos       |
| Auditorías de textos, licencias, secretos, importaciones y trazabilidad | Pasan           |

La suite completa de auditorías produjo inicialmente 621 pruebas correctas, dos
omitidas y un fallo en el contrato de CI, que esperaba el comando anterior sin
instalar Chromium. Se actualizó ese contrato y se añadieron dos regresiones que
rechazan omitir la instalación. Los 57 casos del contrato actualizado pasan.
Las dos pruebas omitidas requieren instalaciones con red; no se declararon verdes.

El sandbox denegó acceso a Windows Credential Manager y detuvo pruebas locales
con procesos/servidores. La verificación nativa y las suites afectadas se ejecutaron
fuera del sandbox. La credencial nativa de prueba usó un destino aleatorio y se
eliminó al terminar. `pnpm` inicialmente intentó descargarse sin red; las pruebas
se ejecutaron con los binarios ya instalados.

## Pendientes concretos

1. Completar la integración de despliegue del acceso web con persistencia,
   cifrado y proveedor de correo reales. T-00-012 ya tiene pantallas y puente del
   servidor; la verificación de navegador usa respuestas HTTP sustituidas.
2. Integrar el almacén del companion con el futuro transporte autenticado:
   guardar las credenciales emitidas y cada `X-Credential-Rotated` antes de enviar
   otro pedido. El almacén está probado, pero esa integración todavía no existe.
3. Completar las revisiones cruzadas del hito y la lista manual con personas
   reales. La revisión de Impeccable realizada aquí fue local; no se ejecutó su
   crítica formal de dos agentes. Tampoco se invocaron los plugins de Claude.
4. Ejecutar CI en un entorno limpio en Windows y Linux. La evidencia anterior es
   local en Windows y no certifica un pipeline remoto.

H0 no se declara cerrado. El catálogo no sustituye la aplicación ni conecta un
proveedor de correo real. No se publicaron resultados ni se configuraron servicios
externos.

Las revisiones del plugin Codex solo las inicia el operador según `CLAUDE.md`:
`/codex:review --scope working-tree` y
`/codex:adversarial-review --scope working-tree` para la autenticación.

## Segunda iteración: acceso web

`apps/web` ya es una aplicación Next.js 16.4.6 con ingreso por código de correo,
solicitud de vinculación del companion y cierre de sesión. Reutiliza los controles
y temas del paquete UI. Sus cinco recorridos en Chromium pasan: teclado completo,
selección/dictado simulados a través de objetivos registrados, error y falta de
conexión, Alto durante una espera y alto contraste. Incluyen axe-core con contraste
activo, geometría de 44 px y reflujo al ampliar texto al 200 %.

El puente del servidor tiene diez pruebas de seguridad correctas. Mantiene las
credenciales en una cookie HttpOnly/Secure/SameSite Strict, conserva las rotaciones,
rechaza orígenes falsos y no devuelve secretos en JSON. Cerrar sesión consulta y
revoca la sesión autenticada; si la revocación falla, mantiene la credencial vigente
y comunica el error. Se añadió `/auth/session` a FastAPI: 42 pruebas de sesiones y
roles pasan, incluidas sesión revocada y metadatos propios del operador.

El arranque de Next.js sin los orígenes HTTPS requeridos se comprobó con salida 1
y el nombre de la variable faltante. La compilación no exige variables de despliegue.
La generación de tipos de rutas forma parte de `typecheck` para checkouts limpios.

Se excluye `next>sharp` del bloqueo por sus binarios LGPL y se desactiva el
optimizador nativo de imágenes. La auditoría tiene una excepción limitada al dataset
`caniuse-lite` 1.0.30001826, con atribución y licencia CC-BY-4.0 conservadas. No se
habilitó esa licencia globalmente para código. Las auditorías de licencias, secretos,
textos, importaciones y trazabilidad pasan.

La verificación global `pnpm exec turbo run lint typecheck build` completó sus 17
tareas correctamente. La auditoría de textos tiene 185 pruebas correctas y una
omitida; se añadieron como propiedades técnicas `autoCapitalize` y `state` para
reconocer atributos reales de las pantallas.

`COALSENSE_SKIP_NETWORK_TESTS=1 pnpm test` completó las siete suites del workspace.
La suite de auditorías terminó con 624 pruebas correctas y dos omitidas. El resto
incluye 94 pruebas del orquestador, 26 de common-py, 24 del companion, 117 de UI y
10 del puente web, además de common-ts. La instalación congelada
`pnpm install --frozen-lockfile` terminó correctamente. Los cinco recorridos de
autenticación se repitieron contra la configuración final y pasan.

La entrada por voz y cabeza todavía necesita el bus y los adaptadores de la spec 01;
el recorrido simulado no certifica esos adaptadores. El paso de Ayuda humana indica
que las rutas aún no están configuradas. No se declara H0 ni el MVP cerrados.

## Tercera iteración: contrato compartido y núcleo de entrada

Se construyeron los esquemas de intenciones y del perfil (T-01-001), la generación
de tipos Python/TypeScript y la auditoría de deriva (T-01-002). Los 26 tipos tienen
cargas útiles cerradas. Las aprobaciones requieren identificador, digest y
confianza. Fechas inválidas, números no representables como JSON y campos de
contenido ajenos al contrato se rechazan. El paquete distribuido incluye sus
esquemas generados; no depende de encontrar archivos del repositorio en ejecución.

El núcleo del bus (T-01-003) tiene dos colas, prioridad fija desde el catálogo,
coalescencia exclusiva de movimiento continuo, copia por consumidor y fallos
aislados. Las pruebas de propiedades verifican el orden y que la saturación no
descarte controles ni aprobaciones. Alto invoca el puerto síncrono antes de encolar
y no depende de que termine un consumidor normal bloqueado.

También se añadió el registro interno de adaptadores con credenciales efímeras,
origen del actor desde la sesión y prohibición de aprobación por `system`. Es parte
de T-01-004, pero todavía falta el named pipe con ACL y el supervisor real. La
guarda de T-01-005 rechaza aprobaciones bajo el umbral y ofrece un puerto de
retroalimentación; falta conectarlo con los adaptadores y la interfaz. No se
declaran verificadas las fixtures reales de ruido ni la separación entre procesos.

La validación del perfil (T-01-013) protege las tres rutas de seguridad de cada
modalidad habilitada, el mínimo de 44 px, histéresis y tiempos de dwell. Una
condición declarada necesita un consentimiento confirmado por el servicio
correspondiente; una referencia escrita en el perfil no basta. La propuesta
inválida no modifica el perfil anterior. El almacenamiento cifrado aún debe
integrarse con esa validación.

Verificación:

- 51 pruebas del contrato y del validador distribuido.
- 19 pruebas del bus, el adaptador ficticio y la guarda de aprobaciones, incluidas
  propiedades con Hypothesis. Diez pruebas de invariantes del perfil.
- Siete pruebas de deriva: fuente sin regenerar, cambio de una restricción,
  salida Python/TypeScript alterada, archivo faltante y ejecución desde otra carpeta.
- La suite global completó ocho paquetes; la auditoría tuvo 634 pruebas correctas
  y dos omitidas. Tras ampliar la guarda y estabilizar el generador se ejecutaron
  nuevamente sus 80 pruebas focalizadas y las siete de deriva.
- `pnpm exec turbo run lint typecheck build audit`: 25 tareas correctas, incluidas
  las seis auditorías y los tipos de ambos lenguajes. Instalaciones congeladas de
  pnpm y uv correctas.

Medición local de publicación, validación y entrega de `nav.next`: 1000 muestras,
100 de calentamiento, p50 1.4078 ms y p95 2.408 ms. Se ejecutó en esta máquina,
sin cámara ni voz y con consumidor en memoria. No acredita T-01-047 ni el
presupuesto del hardware de referencia.

Se fijaron y registraron JSON Schema, su comprobación RFC 3339, anotaciones de tipos
y Hypothesis. La auditoría reconoce únicamente los nombres históricos exactos
`MIT license` y `Apache 2.0`; una expresión SPDX declarada tiene precedencia y no
se aceptan coincidencias parciales. Los textos instalados se revisaron.

Siguiente bloque: conectar el bus con StopGuard, el actuador y el canal autenticado
de Windows. El puerto de Alto actual no prueba una detención física del equipo.

## Cuarta iteración: Alto, permisos de actuación y Deshacer

Se añadió `HaltController` y su conexión con `StopGuard` (T-01-009): bandera de
parada, autorizaciones por actuación, liberación de teclas y botones propios,
cancelación de actividades y reintento de recursos que no se pudieron liberar.
No permite reanudar si queda un recurso pendiente. Las pruebas de propiedades
combinan modalidades, estados lógicos y recursos, con independencia de la red.
También verifican operaciones en curso y fallos de liberación o cancelación.

El bus ahora asigna generaciones internas y permisos de entrega de un solo uso.
`ActuationGate` impide iniciar una acción con un diccionario directo, con una
entrega de otro bus o con una entrega anterior a Alto. Cada paso vuelve a comprobar
su autorización. Se evita también coalescer movimientos anteriores y posteriores
a Alto. La generación y el permiso no son campos elegidos por el adaptador.

Se construyó la pila de Deshacer y la tabla de clases (T-01-010). El texto requiere
un destino verificado. Una acción irreversible no deja buscar otra más antigua;
un resultado incierto no se reintenta automáticamente. La pila conserva solo sus
callbacks en memoria y comunica el resultado con textos fijos del catálogo. Está
lista para que el ejecutor registre las actuaciones reales.

El backend de Windows implementa SendInput mediante ctypes, sin incorporar otra
dependencia. Incluye ABI de 32/64 bits, teclas extendidas, botones, coordenadas de
escritorio virtual, desplazamiento firmado y Unicode con pares sustitutos en un
solo lote. Las pruebas detectaron y corrigieron el desbordamiento que podía ocurrir
al redondear una coordenada al límite del entero de 32 bits.

Se corrigió el grafo de Turborepo: lint, tipos, pruebas y build dependen de las
tareas de sus dependencias. Los paquetes Python declaran sus vínculos internos
también en el grafo del workspace. El indicador de omisión de pruebas de red forma
parte de la clave de caché. El dry run real confirma la dependencia de build web
sobre UI; se añadieron seis pruebas del grafo. Esto evita reutilizar una compilación
web anterior cuando cambia el paquete compartido.

Verificación focalizada: 50 pruebas de bus y actuación correctas, incluidos ocho
casos Win32 y doce de Deshacer; mypy y Ruff sin errores. Las pruebas de entrada
Win32 usan una API controlada y no envían entradas al escritorio de la persona.
No se certifica todavía una detención física con hardware o aplicaciones reales.

Pendiente inmediato: conectar las primitivas al consumidor de actuación de
T-01-033, comprobar el destino y los privilegios de la ventana y cerrar el transporte
named pipe con ACL y el supervisor. El control real del PC, las modalidades físicas
y el MVP siguen en construcción.

La composición debe mantener Deshacer operable tras Alto sin reanudar las demás
actuaciones y comprobar cada paso de esa reversión frente a un nuevo Alto. La pila
actual y el bus ya están separados para esa integración, pero todavía no existe
el consumidor nativo de Deshacer.

La verificación global final completó 25 tareas de lint, tipos, build y auditorías
y las ocho suites de pruebas con el grafo corregido. El companion tiene 84 pruebas
correctas; las auditorías, 641 correctas y dos omitidas por requerir red. El dry run
de Turborepo mostró `@coalsense/web#build` dependiente de `@coalsense/ui#build`.

La medición local actualizada del bus produjo p50 1.9776 ms, p95 4.5115 ms y máximo
29.1503 ms sobre 1000 muestras, con 100 de calentamiento y otras verificaciones
ejecutándose. No representa una prueba de latencia del actuador ni del hardware
de referencia.

## Quinta iteración: consumidor del actuador y destino Win32

Se conectó el bus al consumidor de T-01-033 mediante una composición que empieza
pausada. Ejecuta movimiento relativo/absoluto, clic y doble clic, arrastre,
desplazamiento, acordes y texto Unicode. El dictado provisional no se inserta.
Los resultados comunican envío, bloqueo, destino no controlable, cambio de foco,
fallo y posible ejecución parcial sin guardar texto ni detalles del sistema.

El inspector Win32 consulta ventana bajo el cursor, primer plano, foco y proceso;
compara la integridad de sus tokens con la del companion. Rechaza un destino
elevado o una consulta fallida y ofrece alternativas del catálogo. Las consultas
son de solo lectura. No elevan el proceso ni intentan eludir UIAccess. Para la
rueda se inspeccionan ambos destinos posibles según la configuración de Windows.
Cada carácter, tecla adquirida y segundo clic vuelve a comprobar el destino.
Windows no ofrece aquí una transacción entre inspección y SendInput; se conserva
la necesidad de validación nativa y de verificar el efecto en la aplicación.

El arrastre mantiene estado consultable y termina con segundo toggle, Deshacer,
Alto o un destino denegado. La liberación no exige que el destino siga disponible.
Los errores inciertos intentan limpiar teclas, botones y Unicode; si no termina
la limpieza, conservan los recursos para reintentar Alto y bloquean reanudar.
Las teclas ajenas al companion no se liberan. Los nombres y alias del acorde se
validan completos antes de enviar la primera tecla.

Se añadió un permiso limitado para Deshacer con la entrada pausada: no reactiva
otras acciones y un nuevo Alto lo invalida. Las pruebas detectaron y corrigieron
que ese permiso bloqueaba la reversión de un arrastre activo. Las entradas viejas
de arrastre tampoco pueden revertir un arrastre posterior. Se rechazan entradas,
reanudación y Deshacer de origen `system`; ese origen conserva Alto y pausa.

La suite del actuador incluye 60 pruebas correctas. Comprueba cambios de foco a
mitad del texto o acorde, segundo clic sobre otro destino, Unicode inválido,
fallos de limpieza, callbacks de retroalimentación fallidos, recursos ajenos,
interrupción concurrente por Alto, ABI y cierre de handles Win32. Las llamadas
de entrada usan hardware controlado: no se ha enviado SendInput al escritorio.
Solo se ejecutó una inspección nativa de destino de solo lectura.

La verificación de calidad completó las 25 tareas de lint, tipos, build y
auditorías con la versión final del consumidor. Las limitaciones continúan:
falta mostrar estado y resultados en el HUD, verificar ediciones para Deshacer
texto, comprobar salud de rutas de Alto al iniciar, integrar el transporte con
ACL/supervisor y probar entradas nativas en aplicaciones de muestra. No se cierra
T-01-033, H0, H1 ni el MVP. Tampoco se han configurado proveedores o desplegado.

La regresión global completó las ocho suites: auditorías con 641 pruebas correctas
y dos omitidas por depender de red. Tras los últimos casos de destino y arrastre,
la suite completa del companion terminó con 119 pruebas correctas. Los tipos del
companion y Ruff también pasaron con los archivos finales.

## Sexta iteración: salud de Alto, latido y ciclo de adaptadores

Se implementó el estado de T-01-011 con rutas por modalidad y evidencia booleana
verificada: dispositivo transmitiendo, adaptador respondiendo y Alto vinculado;
voz y visión también requieren modelo cargado. Registrar no habilita una ruta.
La evidencia caduca y renovar el token de una ruta rechaza informes del proceso
anterior. Los avisos de pérdida se ejecutan antes que el aviso de interfaz, con
contadores de fallos independientes. No se guardan datos de sensores ni del perfil.

La composición del actuador ahora bloquea reanudación y acciones normales sin una
ruta sana. Perder la última ruta pausa, limpia e invalida la generación del bus,
incluidas las acciones pendientes. Recuperar salud no reanuda automáticamente.
Deshacer conserva su permiso limitado. Se retiraron consultas anidadas de salud
bajo el bloqueo de primitivas para evitar invertir bloqueos al expirar una ruta.

Se añadió el contrato versionado del latido, tipos Python/TypeScript generados y
validación de forma e invariantes: una ruta sana debe tener motivo sano, el estado
global corresponde a sus rutas y no hay IDs de ruta duplicados. No se admiten
campos de biometría, perfil, texto ni órdenes remotas. La deriva del contrato nuevo
tiene una prueba explícita en auditoría.

El emisor tiene un bucle periódico cancelable y un puerto de transporte. El
receptor compartido exige enlazar una instancia autenticada, comprueba secuencia
y revisión y usa tiempo monotónico de recepción. Repeticiones, revisiones viejas
e instancias ajenas no prolongan la salud. Desconectar o un paquete inválido deja
estado falso; reconectar la misma instancia conserva el contador de reproducción.

El supervisor administra puertos de proceso, entrega credenciales efímeras en
memoria y las revoca antes de limpiar o reiniciar. Aísla fallos de arranque y salud,
espera cada vez más entre intentos y solo reinicia su contador tras salud estable.
No confunde un dispositivo desconectado que sigue reportando con un proceso caído.
Si no se confirma la terminación, conserva el puerto, reintenta limpieza y evita
duplicar procesos sobre el mismo dispositivo. Apagar un adaptador conserva esa
decisión hasta habilitarlo otra vez.

Verificación: 158 pruebas correctas del companion, incluidas salud, latido,
caducidad entre caracteres, cola vieja tras recuperación, reinicios y revocación,
espera creciente y supervivencia del bus/otra modalidad ante un fallo de visión.
Las pruebas de ciclo de procesos usan puertos controlados. Las 25 tareas de lint,
tipos, build y auditorías completaron correctamente la versión de código actual.

Los periodos técnicos se marcan `[SUPUESTO]`: evidencia fresca 2 s, emisión 1 s,
recepción 3 s; reinicio 250 ms hasta 30 s, arranque y estabilidad 30 s. Son
configurables y no limitan las decisiones de la persona.

Falta implementar el host de procesos Windows y el named pipe con ACL, conectar
los puertos de estado al HUD y los avisos urgentes/latidos al WebSocket autenticado
y consumidores reales de políticas. No se ha probado control por voz, visión o
calibración reales sin red. T-01-004, T-01-011 y T-01-056 siguen parciales; no se
cierran H0, H1 ni el MVP, ni las revisiones humanas y cruzadas pendientes.

La regresión global final completó las ocho suites. Las auditorías terminaron con
642 pruebas correctas y dos omitidas por depender de red; no quedaron procesos de
verificación activos. Se mantienen los cambios previos del repositorio.

## Séptima iteración: named pipe y procesos Windows reales — 17 de noviembre

Se construyó el canal de T-01-004 con una instancia aleatoria por adaptador, ACL
protegida solo para la cuenta actual, rechazo de clientes remotos y comprobación
de los PID de ambos extremos antes de enviar credenciales. La prueba nativa lee
la ACL real y compara su única ACE con el SID de la cuenta. La E/S es solapada y
cancelable; una operación que completó al vencer el plazo no pierde el mensaje.

El protocolo local usa JSON acotado y cerrado, sin pickle. Valida credencial
vigente del adaptador, secuencia y versión. Rechaza claves duplicadas, NaN,
campos no permitidos y datos grandes o inválidos. Las respuestas contienen solo
metadatos. El cliente no reintenta acciones cuyo resultado sea incierto. Las
intenciones siguen pasando por el bus, que deriva actor y modalidad. Las pruebas
nativas de extremo a extremo comprueban Alto síncrono, origen no falsificable y
que una credencial no vinculada no publique nada.

El host ya inicia hijos reales sin consola. Entrega el secreto exclusivamente por
stdin, limpia el entorno heredado y usa Python aislado con un catálogo estático
de adaptadores. La auditoría de importaciones rechazó la carga dinámica inicial;
se sustituyó por importaciones fijas sin rebajar la auditoría. La auditoría de
secretos también detectó un token ficticio literal en una prueba: se reemplazó por
una credencial efímera generada en cada ejecución.

La primera prueba con un hijo detectó que el redirector de venv de Windows añade
un proceso y cambia el PID observado. Se corrigió el arranque con el intérprete
base y la selección de venv de CPython 3.12. Las pruebas verifican el PID real,
intercambio con el hijo, ausencia del secreto en argv/salida y entorno sin claves
de proveedores ni variables de inyección de Python.

Un Job Object privado termina el proceso y sus descendientes al cerrar su último
handle. Se comprobó su terminación sin cooperación del hijo. Se corrigió también
la espera del canal cuando el hijo muere antes de conectar. El supervisor reinicia
un hijo real caído con credencial nueva, mientras el otro proceso conserva su PID
y sigue vivo. Los informes de salud conservan su instante original de recepción;
consumir tarde un informe no renueva artificialmente una ruta caducada.

Se corrigieron tipos de los bordes Win32 para que mypy pase tanto con plataforma
Windows como Linux. La ejecución nativa final del companion tiene 201 pruebas
correctas, incluidas 15 de pipe y siete de host/procesos. Las pruebas no enviaron
entrada al escritorio. El adaptador habilitado es solo diagnóstico: informa vivo,
pero sin dispositivo/modelo/ruta de Alto, y no habilita actuación. Las modalidades
físicas siguen pendientes.

La regresión global completó las ocho suites y las auditorías tuvieron 642 pruebas
correctas y dos omitidas por depender de red; después se comprobó la suite final
del companion con los últimos dos casos nativos. Siguen pendientes HUD, restricción
de egreso de procesos, voz y visión reales, calibración, enlace remoto y políticas.
No se cierran los hitos ni las revisiones humanas y cruzadas requeridas.

La comprobación final de esta iteración completó las 25 tareas de lint, tipos,
build y auditorías con todos los archivos finales. No se añadieron dependencias
externas ni se relajaron las auditorías de importaciones o secretos.

## Octava iteración: adaptación de Stitch — 18 de noviembre

Se implementaron las siete composiciones españolas de `Stitch UI-UX` en la web:
bienvenida, preparación del control, primera práctica, Inicio, tarea en curso,
revisión y Logros. Se añadieron lista y creación de tareas, ajustes y estados
explícitos para autonomía y cuidador sin configurar. La autenticación y el puente
de sesión existentes se conservaron. El mapa de rutas y las diferencias funcionales
están en `docs/STITCH-ADAPTACION.md`.

El tema Stitch usa la paleta verde y cálida de los originales, superficies claras,
selección menta y aprobación ámbar. Atkinson Hyperlegible Next se sirve localmente;
se conservó su licencia OFL y se registraron procedencia y hash. No se añadieron
dependencias npm ni scripts o CDN del prototipo. Los textos españoles mantienen
paridad literal entre TypeScript y Python. El tema histórico del catálogo no fue
reemplazado por la variante de la aplicación.

El recorrido prepara texto aportado por la persona, permite editar, revisar,
decidir después, cancelar, pausar y deshacer. Aprobar copia al portapapeles; no
envía ni publica. Solo una copia confirmada registra un logro, ligado a la versión
aprobada. Logros permite consultar fecha, versión e identificador reales, y
exportar títulos y fechas sin cuerpos ni destinatarios. No se inventan ingresos,
compensaciones, hashes de transmisión ni validaciones externas.

Los borradores y ediciones sin guardar permanecen en memoria del espacio de
trabajo, incluso al visitar Ajustes y volver. Cambiar de tipo de tarea conserva el
texto. Guardar consume la edición temporal y Deshacer recupera la versión previa.
Ir al acceso o recargar descarta el estado; se informa en la interfaz. No hay
localStorage, sessionStorage ni llamadas a un proveedor de IA. Este recorrido no
sustituye la persistencia cifrada ni una sesión remota de ejecución autenticada.

La cámara ofrece únicamente vista previa local bajo permiso explícito. Alto y
salir cierran pistas; las respuestas de permiso tardías se descartan. No se
simulan malla ni calibración. El micrófono sigue bloqueado. La lectura y los avisos
opcionales solo usan voces españolas declaradas locales por el navegador, sin
reemplazo remoto. Las preferencias de voz, cabeza y mirada no afirman que sus
adaptadores estén conectados.

Las pruebas encontraron y permitieron corregir estos fallos: una pista de voz con
contraste insuficiente; una regresión del orden de Tab en el acceso; controles
cuyos identificadores publicados no resolvían al DOM; pérdida de texto al cambiar
el tipo de tarea; éxito de práctica visible tras Deshacer; foco móvil detrás de
las barras; y una carrera de navegación al terminar una copia tras abandonar la
revisión. Alto bloquea también el envío directo de formularios y no depende solo
del estado visual del botón. Los errores identifican y enfocan el campo que falta.

Verificación ejecutada:

- 31 pruebas de navegador correctas sobre compilación de producción; incluyen
  las siete pantallas mediante selección y dictado simulados sin mouse ni teclado,
  autenticación, ambos contrastes, axe-core, 44/64 px, texto al 200 %, móvil,
  edición sin conexión, exportación y detalle, Alto durante cámara/copia y
  conservación del texto. No implican voz ni visión físicas.
- 106 pruebas de componentes y navegación compartidos correctas; 12 pruebas de
  tokens y contraste, incluidas las parejas semánticas de `stitchTheme`.
- 10 pruebas del puente web y 26 del paquete Python común correctas.
- 22 tareas correctas de lint, tipos y auditorías de copia, importaciones,
  licencias, secretos, esquemas y trazabilidad; sin relajar reglas.

Se inspeccionaron las capturas de las siete pantallas en navegador. La revisión
final con personas, las modalidades físicas, el enlace del companion, los
conectores de envío, la persistencia y las revisiones cruzadas siguen pendientes.
Esta adaptación no cierra el MVP ni los hitos del plan.

## Novena iteración: recuperación y reflujo — 18 de noviembre

Se añadieron carga, error de página y 404 con la identidad de Stitch. La carga se
anuncia desde que empieza la navegación, antes de su primera respuesta. Una prueba
que retenía la respuesta descubrió que el fallback del segmento no bastaba en ese
intervalo; el estado de transición ahora se comunica desde el espacio. Alto
abandona esa navegación y conserva el editor sin recargar.

Un error de página permite reintentar manteniendo el proveedor de tareas. La prueba
provoca el fallo, comprueba la recuperación de una edición sin guardar y verifica
el foco del título tras el reintento. Los objetos de excepción no se muestran ni
se reenvían desde las pantallas de recuperación. Los títulos estáticos identifican
la pantalla sin incluir texto privado de los borradores.

Un fallo del layout usa una recuperación independiente del proveedor, con contraste,
Alto, Deshacer deshabilitado con explicación y Ayuda humana. Explica que los datos
solo en memoria pueden haberse perdido. Se comprobó el cierre de la cámara al caer
el layout y que reintentar no vuelve a activarla. El componente también está
conectado a `global-error`; no se provocó un fallo del documento raíz del servidor.
La prueba de 404 verifica la respuesta HTTP, el texto español y los controles.

Se eliminaron nombres de controles repetidos en bienvenida, ajustes y revisión.
La pista visual «Di: …» no se agrega al nombre accesible ni a la etiqueta publicada
para selección. La auditoría de navegador comprueba que no hay controles con
etiquetas duplicadas en las pantallas y estados examinados.

La prueba con un título de 180 caracteres y un borrador de 50.000 encontró que,
al ampliar el texto al 200 % en móvil, las barras podían consumir casi toda la
pantalla y bloquear el acceso a Preparar. La barra ahora publica una señal de
reflujo según su ancho y la fuente real; la web la reorganiza en dos columnas y
coloca Ayuda humana en su propia fila. La barra de entrada conserva la modalidad
no conectada y solo oculta una leyenda redundante. No se reducen texto ni objetivos.
La copia del contenido completo y los controles de 64 px pasan en ese modo.

La regresión de navegador completó 37 pruebas de la aplicación y 59 del catálogo
compartido. Los componentes y navegación tienen 106 pruebas correctas, más 12 de
tokens y contraste. El catálogo Python común completó sus 26 pruebas. Se mantienen
la compilación de producción y las auditorías del proyecto; las capturas nuevas
incluyen carga, error, error del contenedor, 404 y reflujo al 200 %.

Siguen pendientes las modalidades físicas, la persistencia cifrada, los conectores
y el enlace de ejecución real, además de la revisión con personas y las revisiones
cruzadas del plan. No se cierran hitos ni se presenta el espacio local como el MVP
completo.

## Décima iteración: bloques, versiones y lectura local — 18 de noviembre

Se construyó el editor numerado dentro de la composición de Stitch. Reconoce
párrafos, encabezados, viñetas y bloques de código sin normalizar el texto original.
La persona puede saltar a un número, reemplazar, insertar o borrar, comparar Antes
y Después y aplicar únicamente el cambio elegido. Las listas se paginan y los
controles no publican el texto privado dentro de sus etiquetas de navegación.

Los cambios aplicados crean versiones inmutables con título, destinatario, asunto,
tipo y cuerpo. Deshacer conserva el historial; recuperar otra versión compara todos
los campos y crea una revisión nueva. La revisión bloquea copiar texto antiguo si
hay ediciones pendientes. La navegación conserva esas ediciones. Una regresión nueva
encontró que Deshacer podía eliminar la tarea recién creada mientras se editaba;
ahora explica la dependencia y conserva el texto antes de cambiar la base.

La lectura del bloque añade pausa y reanudación con voz española local. El motor
comparte un dueño de lectura: un componente anterior no puede cancelar una lectura
posterior al desmontarse ni mediante eventos tardíos. Alto cancela la lectura; un
fallo de cancelación impide iniciar otra. Las pruebas simulan el motor del sistema,
sin acreditar voz física ni reconocimiento de comandos reales.

El orquestador incorpora `agents/document/blocks.py` y `edit_commands.py` como
avance de T-04-001. Modela bloques inmutables con identificador, tipo, texto y orden;
interpreta una gramática completa y devuelve propuestas de antes/después. Aceptar
requiere la misma base completa; no sobrescribe cambios de otro bloque. Insertar
y borrar conservan las identidades restantes. Abreviar y formalizar necesitan un
puerto de reescritura y fallan sin él; no se añadió un proveedor de IA ni una llamada
de red. Los errores no reflejan el texto y las representaciones de los objetos lo
omiten. La gramática y sus supuestos están documentados en el README del orquestador.

Verificación ejecutada:

- 42 pruebas de navegador sobre compilación de producción, incluidas edición por
  número con selección/dictado simulados, comparación, inserción, borrado, recuperación,
  Alto, Deshacer y lectura con pausa/reanudación. Capturas de bloques e historial
  inspeccionadas; se conserva la composición y la barra de seguridad de Stitch.
- 19 pruebas unitarias web correctas: puente de acceso, rangos de bloques,
  inmutabilidad de versiones, límites y propiedad del motor de voz.
- 133 pruebas correctas del orquestador, incluidas 39 nuevas de bloques y comandos
  y una propiedad que comprueba que editar no cambia los bloques vecinos.
- 26 pruebas correctas del paquete común Python y paridad del catálogo español.
- 22 tareas correctas de lint, tipos y seis auditorías, con los módulos nuevos.

El primer intento de la suite completa Python se quedó sin avanzar dentro del
sandbox y se interrumpió; la repetición fuera del sandbox completó las 133 pruebas
en ocho segundos. FastAPI emite una advertencia de deprecación de su cliente de
pruebas con httpx; no se modificaron las dependencias fijadas para ocultarla.

Las versiones y las ediciones web siguen en memoria y se pierden al recargar. El
modelo del servidor aún no está conectado al editor. Faltan el servicio de versiones
con control atómico de revisión, la persistencia cifrada, el gateway con consentimiento,
los agentes y conectores reales, las modalidades físicas y las revisiones humanas y
cruzadas. No se cierran las tareas de Kiro ni se declara terminado el proyecto.

## Undécima iteración: contratos del gateway — 18 de noviembre

Se construyeron `gateway/manifest.py` y `registry.py`, como avance de T-02-006.
Un manifiesto declara esquemas de entrada y salida, reversibilidad y compensación,
categorías de datos y proveedor. La clase de efecto ausente se guarda como
`external_effect`; valores desconocidos o nulos se rechazan. No se deduce `read`
a partir del nombre. El registro es explícito, rechaza duplicados y devuelve
contratos inmutables con exportaciones aisladas.

El contrato reside en `packages/intents/schema/tool-manifest.schema.json` y genera
los tipos Python y TypeScript y el esquema embebido. La auditoría de deriva cubre
también cambios en sus restricciones. El compilador detectó una referencia circular
en el alias JSON generado con `Record`; el generador ahora usa una firma de índice
compatible con JSON recursivo. No se editaron a mano las salidas generadas.

El gateway valida los esquemas y sus valores sin red, rechaza referencias externas,
comprueba formatos y devuelve códigos sin entrada ni contexto privado de excepción.
Se probaron campos ausentes, clases inválidas, datos que no son JSON, ciclos,
referencias, cambios posteriores del manifiesto y de sus copias, nombres repetidos
y saltos de línea en identificadores. Los supuestos de nombres y las limitaciones
de resolución local están documentados.

Se reutilizó `jsonschema==4.26.0`, ya instalado y registrado, como dependencia directa
del orquestador; se añadió su vínculo con `coalsense-intents` en uv y Turborepo.
Los lockfiles se resolvieron sin conexión y no se introdujo otra biblioteca externa.
La justificación de la dependencia existente se amplió en `THIRD_PARTY.md`.

La verificación completó 257 pruebas del orquestador, contratos y auditorías de deriva
y dependencias, y las 22 tareas de lint, tipos y auditorías. La advertencia del cliente
de pruebas FastAPI/httpx permanece.

La regresión general `pnpm test` completó los ocho paquetes correctamente: 16 pruebas
TypeScript comunes, 26 Python comunes, 12 de tokens y 106 de componentes, 78 de
contratos, 201 del companion, 164 del orquestador, 19 web y 644 de auditoría. Son
1.266 aprobadas y una omitida porque Windows no permite crear el enlace simbólico
de esa prueba; las 42 de navegador se ejecutaron por separado.
No se cuentan como aprobadas las revisiones manuales: se creó
`docs/checklist-humano.md`, con todas sus casillas pendientes.

Registrar una herramienta no la habilita ni ejecuta, y no equivale a aprobarla.
Continúan pendientes el catálogo curado real, habilitaciones por persona, gateway
de ejecución, política, sellos, idempotencia y bitácora. No se presenta este registro
como una protección completa de acciones externas ni se cierra T-02-006 con sus
dependencias y revisiones pendientes.

## Duodécima iteración: preparación mínima y consentimiento — 18 de noviembre

Se construyeron `agents/prompt_builder.py` y `gateway/consent_client.py`, avance de
T-02-008. El constructor solo admite instrucción del paso, texto de tarea y
preferencias de texto. Rechaza los campos desconocidos, también en preferencias;
no descarta silenciosamente un perfil de capacidad, condición declarada, eventos de
crisis, credenciales o mensajes arbitrarios. No se transmitieron datos a un modelo.

Un rango explícito selecciona el texto necesario y conserva sus caracteres exactos,
incluidos Unicode y saltos de línea. Las preferencias no salen por defecto: se
solicitan por nombre y usan un vocabulario cerrado inicial de tono, idioma y formato
marcado como supuesto. El objeto preparado no conserva el documento completo ni
incluye identificadores de persona o proveedor en su carga para el modelo. Sus
representaciones no muestran el contenido.

La consulta de consentimiento es asíncrona y está ligada a persona, categoría
`llm_content` y proveedor. El adaptador por defecto siempre niega. No se almacena
un permiso reutilizable: cada preparación vuelve a consultar. Fallos, respuestas
no booleanas y revocación impiden obtener el prompt. Cancelar se propaga y no crea
un reintento. El gateway tendrá que repetir la consulta justo antes de transmitir;
preparar datos no concede autorización para una llamada posterior.

Las 55 pruebas nuevas incluyen campos prohibidos y una propiedad sobre cualquier
clave desconocida, selección de texto y preferencias, contexto inmutable, revocación,
proveedor distinto, error privado del consultor y cancelación. El registro de
consentimientos, proveedores reales, filtrado de entrada/salida y el ejecutor del
gateway siguen pendientes. No se presenta la lista permitida de campos como una
verificación semántica del contenido de una tarea ni como un filtro de crisis.

## Decimotercera iteración: persistencia PostgreSQL real — 18 de noviembre

Se verificó Docker operativo y una imagen local de pgvector, fijada por digest.
La imagen examinada contiene PostgreSQL 16.15 y pgvector 0.8.7. Se añadió
`asyncpg==0.32.0` (Apache-2.0, publicado el 6 de octubre de 2026), comprobado en PyPI
y con el controlador instalado. El motivo y la infraestructura de prueba constan
en `THIRD_PARTY.md`; no se añadió una excepción a la auditoría de paquetes.

La migración `0002_rls.sql` crea grupos sin LOGIN y un esquema con tareas sin
contenido y eventos mínimos de escritura. La persona sale del `Principal` del
servidor. Se fuerza seguridad por filas, incluso para el propietario; las consultas
concurrentes no comparten contexto de persona. Se rechazan roles administrativos o
con BYPASSRLS y un grupo de ejecución inseguro. El rol de auditoría no puede leer
tareas ni eventos individuales.

Crear y pausar requieren una política explícita y registran el cambio en la misma
transacción. La referencia del evento liga persona y recurso. Si falla el registro,
se revierte el cambio; también se revierte al cancelar. Pausar exige la revisión
esperada, y la autonomía queda en N0. Cerrar y volver a abrir el servicio conserva
los metadatos en la base. No se guardan títulos, destinatarios ni cuerpos: la web
continúa en memoria hasta integrar cifrado y versiones de entregables.

Las pruebas reales encontraron y permitieron corregir dos fallos: normalización
del UUID devuelto por el controlador y contexto de errores internos reintroducido
por `contextlib`. El límite público devuelve excepciones nuevas de código fijo,
sin esa cadena. La auditoría de secretos también rechazó plantillas de URL de las
pruebas; se sustituyeron por un constructor de componentes que codifica credenciales,
incluidos delimitadores y errores Unicode. No se relajó el auditor.

`compose.test.yaml` crea una instancia sintética en `tmpfs`, con contraseña aleatoria,
puerto loopback y proyecto Compose único que se limpia al terminar. Docker recibe la
contraseña por entorno; no se crea un archivo de credenciales en el repositorio.
Se ejecutó un proceso hijo con entorno reducido y se comprobó que no autentica sin
credenciales. Esa prueba no acredita bloqueo de red; el lanzador aislado sigue abierto.

La tarea `test:integration` del orquestador exige esta instancia real. CI de Linux
se configuró para descargar la imagen fijada y ejecutar la tarea junto a la web;
la auditoría rechaza quitar esa descarga o reducir la etapa a pruebas web. No se
ejecutó un pipeline remoto. Turborepo incorpora la opción de PostgreSQL real a la
clave de pruebas para no reutilizar resultados que lo hayan omitido.

Verificación local: 246 pruebas del orquestador, incluidas 55 del constructor y 27
de persistencia (11 con PostgreSQL real); las 22 tareas de lint, tipos y auditorías
pasaron. La regresión general con `COALSENSE_TEST_POSTGRES=1` completó los ocho
paquetes: 1.353 pruebas aprobadas y una omitida por permisos de enlace simbólico en
Windows. Incluye los 246 casos del orquestador y 649 de auditoría. Los contenedores
de prueba se eliminaron al terminar. La advertencia FastAPI/httpx sigue presente.

La implementación y sus límites se describen en `docs/PERSISTENCIA.md`. Faltan
cifrado y gestión de claves, integración de los borradores web, migrador versionado,
repositorio persistente de autenticación, memoria, consentimiento real, políticas,
bitácora encadenada y aislamiento de agentes. No se cierran T-02-002, T-02-008,
los hitos ni las revisiones humanas y cruzadas por estas pruebas.

## Decimocuarta iteración: migrador y bitácora encadenada — 18 de noviembre

Se construyó `persistence/migrations.py`: plan sin DDL por defecto, archivos SQL
identificados por su nombre completo, SHA-256 con finales de línea normalizados y
verificación de que el historial aplicado sea un prefijo exacto del conjunto actual.
Cambiar u omitir un archivo aplicado se rechaza. El SQL pendiente y su historial se
aplican en una transacción con exclusión entre migradores; un fallo revierte el lote.
Se conservan los nombres históricos con prefijos numéricos repetidos.

`tools/migrate.py` usa `COALSENSE_MIGRATION_DATABASE_URL`, separada de la configuración
de ejecución. Por defecto devuelve pendientes en JSON; `--apply` ejecuta. TLS sigue
verificado salvo la excepción loopback explícita `--local-test`. Los errores no
imprimen URL, credenciales ni SQL. Se probaron configuración ausente, plan sobre
base vacía sin creación de esquemas, uso del comando y rechazo del usuario de
aplicación. No se aplicaron migraciones a una base productiva.

`audit/events.py`, `chain.py` y `log.py` implementan la bitácora de metadatos como
avance de T-02-003. Los tipos y resultados son cerrados; las referencias admiten
UUID, nombre de herramienta, clase de efecto, origen del actor y versión de política.
Se rechazan claves de contenido y estructuras arbitrarias, con una propiedad sobre
cualquier clave no declarada. El nombre de herramienta reutiliza el esquema compartido
de manifiestos mediante `validate_tool_name`, sin mantener otro patrón Python.

`0003_audit.sql` incorpora `audit_event`, RLS forzada, privilegios de solo selección
e inserción y comprobaciones SQL de huella, secuencia y enlace anterior. Python y
PostgreSQL usan el mismo framing SHA-256 con campos ASCII en orden fijo, UTC con
microsegundos y referencias ausentes explícitas. Se probaron todos los campos de
referencia y la coincidencia al leer desde la base. La clave foránea compuesta
mantiene la pertenencia de la tarea a la persona.

Crear y pausar una tarea ya insertan en esta cadena, dentro de su misma transacción.
Un fallo de bitácora revierte la tarea. El puerto interno `append_audit` retorna tras
el commit y sus eventos ya son visibles desde otra conexión; sigue sin existir una
ruta de cliente para inventar eventos. La escritura verifica la cadena completa
antes de extenderla y se serializa por persona. Diez escrituras simultáneas no
generan ramas, huecos ni duplicaciones de secuencia.

La actualización conserva identificadores, instantes y persona de los eventos
provisionales, y deja la tabla histórica en lectura. Las pruebas de actualización
usan otra base aleatoria dentro del contenedor propio. Dos migradores concurrentes
aplican una migración nueva una sola vez. La corrupción simulada con privilegios
administrativos se detecta antes de leer o agregar; los datos y el CHECK se restauran
mediante rollback del caso de prueba.

Verificación ejecutada: 281 pruebas del orquestador (incluidas 19 unitarias de cadena
y 43 de persistencia, de las cuales 26 usan PostgreSQL real), 83 del contrato
compartido y 22 tareas correctas de lint, tipos y auditorías. La regresión general
completó los ocho paquetes: 1.393 pruebas aprobadas y una omitida por permisos de
enlace simbólico en Windows; reutilizó caché de cuatro paquetes sin cambios.
La advertencia del cliente de pruebas FastAPI/httpx permanece. La descarga por digest
de la imagen configurada en CI se comprobó contra el registro; no se ejecutó un
pipeline remoto ni se hizo push. Los recursos temporales se eliminaron al terminar.

`docs/BITACORA.md` describe el formato y sus límites: verificar cuesta tiempo lineal
por escritura; detectar que se ha quitado el final requiere una cabecera conocida;
no hay aún un anclaje externo ni resistencia acreditada a una reescritura privilegiada
completa. El gateway tendrá que esperar el registro confirmado y propagar sus fallos
antes de despachar; ese ejecutor aún no está implementado. Las lecturas de API,
delegaciones, fusión del companion, pantalla y exportación, cifrado, políticas y
registro de todos los componentes siguen abiertos. No se cierran T-02-002,
T-02-003 ni los hitos o revisiones del plan. Los borradores web siguen en memoria.

## Decimoquinta iteración: políticas auditadas y versionadas — 19 de noviembre

Se construyó `policy/` como avance de T-02-010. Una solicitud cerrada identifica
acción, tarea y herramienta. El servidor determina clase de efecto desde el
registro de manifiestos y lee contexto, política activa y salud del Alto. N0
requiere aprobación; todo efecto externo la requiere en cualquier nivel. Una
política que permite un efecto externo sin aprobación se rechaza al cargar y en
SQL. Fallos, pausas, permisos insuficientes y contexto incompleto impiden permitir.

Cada decisión espera la bitácora confirmada. Un fallo real de INSERT convierte
la decisión en denegación sin evento confirmado. El registro de una evaluación
de lectura funciona con alcance de lectura sin conceder edición ni activación
de políticas. Cancelaciones no se convierten en permisos ni se absorben.

`0004_policy.sql` incorpora versiones canónicas inmutables por persona y un puntero
activo que solo avanza, con RLS forzada. Activación, actualización del puntero y
evento son atómicos. Repetir la misma instantánea es idempotente; reemplazar o
retroceder se rechaza. Revocar INSERT de la bitácora conserva la versión anterior.
Se probaron aislamiento, reinicio del servicio y prohibición SQL de modificación,
borrado y truncado. No se cambiaron las migraciones anteriores.

El formato v2 de bitácora agrega referencias cerradas de acción y regla. Conserva
huellas v1 y admite cadenas mixtas. Una prueba actualiza una base con un evento
v1 y agrega v2 y otro v1 de un escritor histórico; los tres enlaces se verifican.
Durante la construcción se corrigió una precedencia de operadores JSON en el CHECK
de la nueva migración, detectada al aplicarla sobre PostgreSQL real.

Las 329 pruebas del orquestador pasaron, incluidas 37 del motor y su adaptador de
latidos, 20 unitarias de bitácora y 53 de persistencia. De estas últimas, 36 usan
PostgreSQL real temporal. Lint, tipos y las seis auditorías completaron 22 tareas
correctas. Se conserva la advertencia del cliente de pruebas FastAPI/httpx.

La compilación de producción también pasó: tres tareas sin caché, con TypeScript,
compilación Next y generación de las trece páginas estáticas configuradas. No se
publicó la aplicación ni se aplicaron migraciones fuera de las bases sintéticas.

La regresión general terminó con ocho tareas correctas: 1.441 pruebas aprobadas y
una omitida por permisos de enlace simbólico en Windows. Se reutilizó caché de seis
paquetes sin cambios; orquestador y herramientas de auditoría se ejecutaron de nuevo.
Los recursos temporales de PostgreSQL se retiraron al finalizar sus pruebas.

`docs/POLITICAS.md` detalla la tabla y los supuestos. La salud de las pruebas SQL es
simulada; el transporte autenticado de latidos sigue pendiente. La etapa la fija un
llamador interno y la clasificación de primera tarea todavía es desconocida. Las
tareas persistidas siguen en N0. La decisión incluye revisión y digest, pero no
reserva ese estado: el futuro gateway deberá revalidarlo justo antes del despacho.
Faltan solicitudes exactas de aprobación, sello, consumo único, idempotencia,
delegaciones y ejecutor. No se presenta esta capa como permiso para ejecutar, ni
se cierran tareas, hitos o revisiones humanas y cruzadas. La web sigue sin estar
conectada a este motor; se preservó su diseño visual y funcional existente.

## Decimosexta iteración: aprobación exacta y despacho simulado — 19 de noviembre

Se añadió el flujo interno de T-02-011 y parte de T-02-007 y T-02-014. Cada
solicitud retiene una copia privada del contenido validado junto con resumen y
destinos. Editar invalida la solicitud anterior. El sello HMAC vincula acción,
contenido, identidad autenticada, sesión, política y revisión, sin plazo humano.
Se consume una sola vez, aun con intentos concurrentes. La emisión exige registro
confirmado. PostgreSQL conserva metadatos de la aprobación sin la vista privada,
su digest ni la firma.

El gateway comprueba el sello, espera la retención configurada por el llamador,
consulta consentimiento, registra el intento y revalida al consumir el sello.
Solo el adaptador registrado recibe la entrada aprobada y la clave de idempotencia.
Alto durante la retención cancela y revoca. La aprobación y el despacho viven en
un proceso, con adaptadores simulados y consentimiento denegado por defecto.
Faltan almacenamiento durable, delegaciones, consentimiento real, transporte,
interfaz y proveedor. PA-15 requiere elegir el primer proveedor de correo OAuth.

Verificación: 342 pruebas del orquestador con PostgreSQL temporal y 22 tareas
correctas de lint, tipos y auditorías. Se conserva la advertencia de FastAPI/httpx.
Las pruebas del gateway no envían correo ni conectan con servicios reales.

## Decimoséptima iteración: vigencia y persistencia de consentimientos — 19 de noviembre

Se añadió `ConsentService` para T-05-011. Consulta la última decisión por persona,
categoría, proveedor y versión activa del aviso, sin caché ni expiración por
tiempo. Una revocación bloquea las consultas posteriores al guardado. Un rechazo
suprime nuevas solicitudes de esa versión. La persona autenticada puede decidir
y leer su historial, y se deniega al cuidador mientras falte la delegación.

`0009_consent.sql` guarda sobres opacos con RLS y orden por persona. La aplicación
solo puede insertar y consultar, y no puede asignar el ordinal. Una prueba con
PostgreSQL y un doble de cifrado verifica aislamiento, lectura en orden y ausencia
de campos de la decisión en SQL. Falta el cifrado autenticado de producción con
la DEK por persona, el catálogo de avisos, la recepción autenticada y la pantalla.

El gateway consulta el consentimiento después de registrar el intento y
revalidar la política. Una revocación mientras el registro sigue en curso
impide el efecto simulado. Estado verificado con 347 pruebas del orquestador,
incluida la nueva migración en PostgreSQL, y 22 tareas de lint, tipos y auditorías.
