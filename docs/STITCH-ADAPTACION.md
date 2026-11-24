# Adaptación de Stitch UI-UX

Referencia: `Stitch UI-UX/stitch_accessible_hands_free_ai_operating_system`.
Se conservan los HTML y PNG originales como evidencia; no se modifican.

| Referencia española                 | Ruta implementada       |
| ----------------------------------- | ----------------------- |
| 1. Bienvenida / elección de control | `/bienvenida`           |
| 2. Calibración y malla facial       | `/calibracion`          |
| 3. Primera tarea exitosa            | `/primera-tarea`        |
| 4. Inicio / panel principal         | `/inicio`               |
| 5. Tarea en curso                   | `/tareas/[id]`          |
| 6. Aprobación                       | `/tareas/[id]/revision` |
| 7. Logros                           | `/logros`               |

La navegación también tiene `/tareas`, `/tareas/nueva`, `/autonomia`, `/cuidador`
y `/ajustes`. La autenticación existente permanece en `/`, con entrada al recorrido
de control y al espacio de trabajo. No se reemplaza el puente de sesión ni se
exponen sus credenciales a la nueva interfaz.

## Comportamiento actual

El espacio local permite elegir preferencias, practicar con una nota, crear un
borrador, editarlo, revisar contenido y destinatario, decidir después, pausar,
deshacer y aprobar una copia al portapapeles. Solo se registra un logro cuando la
copia devuelve éxito; no se presenta como correo enviado, publicación o ingreso.
La revisión queda vinculada a la versión mostrada. Alto durante una espera impide
marcarla como completada automáticamente. Copiar no es reversible y crea una
barrera en el historial de Deshacer.

Logros permite inspeccionar el identificador de la tarea, la versión y la fecha
de cada copia confirmada. La exportación descarga un archivo de texto con fechas
y títulos; excluye cuerpos y destinatarios. La interfaz pide revisar la descarga
y no la registra como un nuevo logro. Tampoco inventa una transmisión, hash,
compensación o validación externa como las que aparecen en el prototipo.

Los borradores permanecen exclusivamente en memoria de la pestaña. No hay
localStorage, sessionStorage, proveedor de IA ni telemetría de contenido. Se avisa
que recargar elimina los borradores. Este estado local no sustituye la persistencia
cifrada, ejecución de agentes y conectores del producto completo, aún pendientes.

Visitar otra sección del espacio conserva en memoria la edición todavía sin
guardar. La caché se vincula a la tarea y su versión; guardar consume esa edición
y Deshacer vuelve al contenido anterior. Ir al acceso sale de este espacio y
descarta su estado, tal como informa el aviso de memoria. No hay persistencia
entre sesiones ni aislamiento remoto de tareas asociado a la cuenta.

Cada ruta tiene un título descriptivo estático. Los metadatos de navegación no
incluyen títulos privados, contenido de borradores ni destinatarios. Una copia
que termina después de abandonar revisión no redirige a la persona a otra pantalla.

La cámara necesita una acción explícita y permiso del navegador. Solo ofrece vista
previa local; no simula malla facial ni calibración de gestos. Alto y salir detienen
las pistas; una respuesta tardía de permiso se descarta y sus pistas se cierran.
El micrófono continúa bloqueado. Voz, gestos y mirada muestran que no están
conectados y conservan una vía con teclado y mouse.

La lectura en voz alta solo selecciona voces españolas declaradas locales por el
navegador. No usa una voz remota de reemplazo. Los avisos hablados son opcionales;
Alto cancela la lectura y la interfaz conserva el aviso visual. Cuando no hay voz
local, el control explica la disponibilidad y el texto sigue visible.

## Recuperación y navegación

La carga se anuncia desde que comienza una navegación, incluso antes de recibir
su primera respuesta. La pantalla anterior y sus notas siguen disponibles mientras
tanto. Alto abandona esa navegación y conserva la ruta anterior, sin recargar.
El segmento también tiene su pantalla de carga para las respuestas en streaming.

Un fallo de renderizado de una página muestra acciones de reintento e Inicio
dentro del mismo espacio. El proveedor de tareas permanece montado; la prueba
comprueba que el borrador y su edición pendiente se recuperan. El título recibe
foco también al reintentar, aunque la URL no cambie. No se muestra ni se reenvía
el objeto de excepción desde estas pantallas.

Un fallo del contenedor tiene una recuperación independiente de su proveedor.
Conserva contraste, Alto, Deshacer deshabilitado con explicación y Ayuda humana,
con objetivos de 64 px. Explica que el estado solo en memoria puede haberse perdido.
Se comprobó el cierre de las pistas de cámara al caer el contenedor y que reintentar
no la active automáticamente. El componente también se conecta a `global-error`;
la prueba provoca un fallo del layout del espacio, no del documento raíz del servidor.

Las direcciones desconocidas devuelven 404 con texto español y controles de
seguridad. La prueba incluye su enlace de vuelta a Inicio y la ayuda con Alto
alcanzable. No se simula la existencia de una tarea que ya no está en memoria.

La barra de seguridad detecta la relación entre el ancho y el tamaño real de su
texto. Cuando tres columnas parten las etiquetas en demasiadas líneas, pasa a
dos columnas y coloca Ayuda humana en la segunda fila. La barra de entrada se
reorganiza y mantiene visible el estado de la modalidad; solo oculta una leyenda
redundante. Se conserva el texto al 200 % y los objetivos de 64 px. La prueba copia
un borrador de 50.000 caracteres sin truncarlo en ese modo.

Los controles tienen etiquetas únicas por pantalla. La pista visual «Di: …» no
duplica el nombre accesible ni la etiqueta que se publica para selección.

## Edición por bloques y versiones

El editor permite elegir un párrafo, encabezado o viñeta por su número; reemplazarlo,
insertar después o eliminarlo; y comparar Antes y Después antes de aplicar. Conserva
exactamente el texto exterior al bloque, incluidos los saltos de línea. La lista se
pagina y admite acceso directo por número. No requiere seleccionar texto con puntero.
La lectura del bloque usa una voz española local, con pausa y reanudación. Alto la
detiene. La prueba usa un motor de voz simulado; falta verificar el audio físico.

Cada cambio aplicado crea una versión inmutable con todos los campos del borrador.
Deshacer conserva las versiones aceptadas. Recuperar una anterior muestra también
destinatario, asunto, título y tipo de tarea y crea una revisión nueva para revisar.
Las ediciones pendientes se conservan al navegar dentro del espacio. La revisión
impide copiar el borrador anterior mientras hay cambios pendientes. Deshacer conserva
una edición pendiente si la operación fuera a eliminar su tarea o cambiar su revisión.

Las versiones y las ediciones continúan solo en memoria de la pestaña. Recargar o
cerrar elimina ese estado. Esto no satisface todavía REQ-04-007/063. Las variantes
generadas por IA, la conservación cifrada y el enlace con el orquestador siguen abiertos.

El orquestador tiene ahora un modelo puro de bloques con identificador, tipo, texto
y orden, y propuestas para reemplazar, insertar, borrar, abreviar y formalizar. La
aceptación comprueba que el documento base completo siga siendo el mismo. Abreviar
y formalizar requieren un puerto de reescritura; sin él se rechazan, sin inventar
una variante. Ese puerto aún no tiene implementación de gateway ni proveedor real.
Los errores y las representaciones de los objetos omiten el texto privado.

## Diferencias necesarias respecto al prototipo

- Sin nombre, contactos, ingresos ni entregas ficticias; los resúmenes empiezan vacíos.
- Sin promesas de detección, seguridad de archivos o validación que no se hayan ejecutado.
- Sin inferencia de estados personales o clínicos ni subida automática de autonomía.
- Sin CDN de fuentes, Tailwind en runtime, Material Symbols remoto ni scripts inline del prototipo.
- Las barras se miden y reservan espacio; el diseño original superponía controles al documento.
- El envío externo no conectado se explica y queda deshabilitado; la copia tiene un efecto claro.
- Español de Ecuador. Las variantes inglesas no activan una traducción incompleta del producto.

## Verificación

Las capturas de navegador se guardan en `apps/web/test-results/stitch-*.png`.
`workspace.spec.ts` comprueba las rutas, ambos contrastes, objetivos de 44/64 px,
reflujo, texto ampliado, pausa, Deshacer, copia, falta de conexión de envío y
cancelación de cámara. Los accesos de autenticación conservan su suite anterior.
También se verifica la selección/dictado mediante objetivos registrados, voces
locales, exportación, detalle, edición sin conexión y conservación del texto al
cambiar el tipo de tarea. El contraste semántico incluye `stitchTheme`.
La aceptación final requiere revisar los resultados reales y los estados aún no
conectados; esta adaptación no cierra por sí sola el MVP ni la revisión humana.
