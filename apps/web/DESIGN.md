# Interfaz web de Coalsense Dispatch

La referencia visual aprobada por el operador es `Stitch UI-UX`. La adaptación
por página está en `design-system/coalsense-dispatch/pages/stitch-workspace.md`;
esa decisión específica prevalece sobre la paleta inicial del MASTER. El mapa
de las siete pantallas y sus límites funcionales está en `docs/STITCH-ADAPTACION.md`.

El tema `stitchTheme` usa fondo #FCF9F4, verde profundo #00433F, texto #1C1C19 y
superficies blancas. Menta para selección y ámbar para decisiones con efecto.
Alto conserva su rojo y su posición estable. Atkinson Hyperlegible Next se sirve
localmente con licencia SIL OFL, base de 20 px y altura de línea 1,5.

La bienvenida tiene tres tarjetas de control y alternativa de teclado; la
preparación, cámara y gestos; la práctica, pasos y nota; Inicio, opciones de tarea
y resumen; la tarea, pasos, documento y bitácora; la aprobación, aviso ámbar, vista
previa y efecto; Logros, métricas reales y registro de copias con detalle y exportación.
La cabecera mantiene seis destinos, idioma, contraste, ayuda y acceso a la cuenta.
Las columnas se apilan en pantallas pequeñas. No se importan scripts, CDN ni datos
ficticios de los HTML.

Modo Operate: preparar, revisar y decidir. Los controles publican identificadores
que resuelven al mismo elemento del DOM para selección y dictado. Los campos solo
publican su etiqueta. Editar desde revisión abre directamente el formulario.
Cambiar el tipo de tarea conserva el texto en edición. Las barras de entrada y
seguridad se miden para reservar espacio; el foco desplaza el control hasta una
zona visible. Alto, Deshacer y Ayuda humana son alcanzables durante los diálogos.

La copia aprobada tiene un efecto local explícito. El detalle y la exportación
reflejan eventos observados, sin inventar transmisiones, hashes o ingresos. La
descarga contiene fechas y títulos; excluye cuerpos y destinatarios. El estado
permanece en memoria de la pestaña; recargar lo elimina. Todavía no sustituye la
persistencia cifrada ni el motor de tareas del producto completo.

La cámara requiere una acción y permiso explícitos y ofrece vista previa local.
Alto y salir cierran las pistas. No se afirma calibración sin un modelo real. El
micrófono sigue bloqueado. Voz, gestos y mirada son preferencias sin adaptadores
conectados; teclado y mouse siguen disponibles. La lectura solo usa voces españolas
declaradas locales por el navegador, sin sustituirlas por voces remotas.

## Recuperación

Las pantallas de carga, error y 404 conservan la composición y los controles de
seguridad. El fallo de una página permite reintentar dentro del mismo espacio;
si cae el contenedor, la recuperación independiente advierte que el estado en
memoria puede haberse perdido. La navegación lenta se anuncia desde el inicio y
Alto permite abandonarla. El título recibe foco al montar y al reintentar.

Al ampliar el texto, la barra cambia de distribución según el espacio real;
mantiene las etiquetas completas y no reduce la fuente. Se evita duplicar nombres
de controles. Las pistas «Di: …» son apoyo visual y no repiten el nombre accesible.

## Acceso y vinculación

El acceso conserva su flujo de correo, código y solicitud de vinculación.

En escritorio, el propósito ocupa una columna y el formulario la otra. Bajo
50 rem se apilan, con el contenido en el mismo orden. El formulario tiene una
acción principal y acciones secundarias explícitas. El foco pasa al título al
cambiar de paso; los avisos persistentes siguen siendo alcanzables con Tab.

Tipografía local Atkinson Hyperlegible Next, fondo cálido y tema de alto contraste
proceden del paquete compartido. Los controles y la barra de seguridad conservan
sus objetivos de 44 px y 64 px respectivamente, con separación de 16 px. Los
textos largos se dividen y el tamaño relativo admite ampliación al 200 %.

Alto y Ayuda humana quedan sobre los diálogos. Los avisos no vencen, el código
no tiene cuenta regresiva y pegar sigue permitido. AX-05 y AX-14 ganan sobre
cualquier sugerencia visual de las skills: no hay animaciones ni funciones que
dependan de hover. Deshacer permanece visible y comunica que no hay una acción
reversible registrada en el acceso.

[SUPUESTO] El cliente web usa un puente del mismo origen y una cookie HttpOnly
con prefijo `__Host-`, Secure y SameSite Strict para proteger la credencial. La
vinculación queda pendiente hasta la decisión de la persona en el companion.

La verificación incluyó captura de la pantalla, teclado, reproducción de
selección/dictado a través del registro, axe-core con contraste y medidas reales.
Las respuestas de autenticación se sustituyen en las pruebas de navegador. La
conexión real con los adaptadores de entrada, las rutas humanas, la persistencia
y el proveedor de correo siguen formando parte de la construcción pendiente.
