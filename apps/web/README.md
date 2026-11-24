# Aplicación web

Next.js 16.4.6 y React 19.3.1. T-00-012 construye el acceso sin contraseña y la
solicitud de vinculación del companion. Los controles proceden de `packages/ui`.

## Configuración y ejecución

Copia `.env.example` a `.env.local` y configura dos orígenes HTTPS, sin ruta,
usuario ni contraseña:

- `COALSENSE_WEB_ORIGIN`: origen público exacto; se valida contra `Origin` en las
  operaciones de autenticación.
- `COALSENSE_AUTH_ORIGIN`: origen HTTPS del servicio FastAPI de autenticación.

`pnpm --filter @coalsense/web dev --experimental-https` inicia el desarrollo con
TLS local. Usa el origen local correspondiente en la configuración. Next.js puede
necesitar preparar un certificado de desarrollo. Para producción, compila con
`pnpm --filter @coalsense/web build` y ejecuta `pnpm --filter @coalsense/web start`
detrás de un proxy TLS. Las variables se validan al arrancar; un dato faltante o
inválido termina el proceso e informa solo el nombre de la variable.

El servicio FastAPI debe tener sus dependencias reales configuradas: repositorio,
cifrado del correo y envío de códigos. Esta tarea no configura servicios externos.

## Comportamiento

La persona pide un código por correo, lo escribe, pega o dicta y entra. Los
códigos no tienen cuenta regresiva. Puede pedir uno nuevo o usar otro correo.
Tras ingresar puede escribir o dictar el código de un companion y solicitar su
vinculación. La decisión final se toma en ese companion; la web informa que sigue
pendiente y no afirma que el equipo ya esté vinculado.

Las credenciales permanecen en una cookie `__Host-` con `HttpOnly`, `Secure`,
`SameSite=Strict` y `Path=/`. No se escriben en localStorage ni se devuelven al
código del navegador. El puente del servidor persiste cada rotación, consulta la
sesión vigente y la revoca antes de cerrar el acceso. Un error de red conserva
la credencial; una respuesta 401 la elimina.

Los errores, la falta de conexión y Alto conservan los campos del paso. Alto
aborta la espera local y aclara que el servicio puede haber recibido la solicitud.
Deshacer está visible, sin acción reversible registrada en estas pantallas.
Ayuda humana muestra un mensaje fijo cuando aún no existen rutas configuradas;
su integración pertenece a la spec 05. El acceso no captura cámara ni micrófono.
El bus y los adaptadores autenticados de la spec 01 aún deben conectarse.

## Verificación

- `pnpm --filter @coalsense/web test`: diez pruebas de seguridad del puente.
- `pnpm --filter @coalsense/web test:a11y`: recorridos de acceso y espacio de
  trabajo en Chromium contra la compilación de producción. Teclado, entradas
  simuladas mediante objetivos registrados, estados de error/carga/sin conexión,
  contraste, texto al 200 %, axe-core y geometría mínima de 44/64 px.
- `pnpm --filter @coalsense/web lint` y `typecheck`: formato, lint y tipos,
  incluida la generación de tipos de rutas en un checkout limpio.

Las pruebas de navegador sustituyen explícitamente las respuestas HTTP de
autenticación. Python verifica FastAPI y Node verifica el puente; falta una
prueba de despliegue HTTPS con proveedor y persistencia reales.

## Espacio de trabajo y referencia Stitch

Las siete pantallas españolas de `Stitch UI-UX` tienen rutas implementadas:
`/bienvenida`, `/calibracion`, `/primera-tarea`, `/inicio`, `/tareas/[id]`,
`/tareas/[id]/revision` y `/logros`. La lista, el editor y los ajustes tienen
sus propias rutas. Desde el acceso se puede iniciar la configuración y, tras
entrar, abrir el espacio local. El mapa detallado está en
`docs/STITCH-ADAPTACION.md` y las decisiones visuales en `DESIGN.md`.

El espacio local permite preparar, editar, revisar, pausar, deshacer y copiar
borradores con aprobación explícita. Logros registra las copias confirmadas,
permite consultar su versión y exportar fechas y títulos. No confirma envíos,
publicaciones ni ingresos. Los borradores solo viven en memoria de la pestaña;
recargar los elimina. No hay almacenamiento web ni llamadas a proveedores de IA.
Estas pantallas no presentan una sesión de ejecución autenticada del companion.

La cámara tiene vista previa local bajo permiso explícito; Alto y salir cierran
sus pistas. El micrófono sigue bloqueado. La lectura solo usa voces españolas
que el navegador declara locales. Voz, gestos y mirada todavía necesitan
adaptadores y calibración; la interfaz conserva teclado y mouse. Tampoco están
conectados el envío de correo ni las rutas humanas del producto completo.

Las pruebas de espacio de trabajo comprueban el recorrido hasta la copia,
exportación y detalle; falta de conexión; conservación del texto al cambiar tipo;
Deshacer; Alto durante respuestas tardías; voces locales y controles accesibles.
Las capturas se guardan en `test-results/stitch-*.png` y no se versionan.

La carga de navegación se anuncia inmediatamente; Alto permite abandonarla sin
recargar el editor. Los errores de página admiten reintento dentro del espacio,
conservando el proveedor de tareas. Un fallo del contenedor muestra una recuperación
independiente y advierte que el estado solo en memoria puede haberse perdido.
La cámara cierra sus pistas al desmontarse y no vuelve a activarse al reintentar.
El 404 también tiene texto español, contraste, Alto, Deshacer y ayuda accesibles.

Al ampliar el texto, las barras cambian de distribución según el ancho disponible
y el tamaño real de las etiquetas; no reducen la fuente. La verificación incluye
un borrador de 50.000 caracteres, objetivos de 64 px y texto al 200 % en móvil.

El editor por bloques ofrece selección por número, comparación antes/después,
inserción, reemplazo y eliminación sin selección fina de texto. Cada cambio aplicado
crea una versión; recuperar otra crea una revisión nueva. Las ediciones pendientes
se conservan durante la navegación interna y evitan copiar una revisión anterior.
La lectura por bloque incorpora pausa y reanudación con voz española local.
Todo este estado sigue en memoria; aún falta persistencia cifrada y conexión con
el modelo de bloques del orquestador. No hay variantes generadas por IA disponibles.

## Dependencias

Se excluye `next>sharp` y se configura `images.unoptimized`. La aplicación sirve
la tipografía local y no necesita el optimizador nativo con binarios LGPL.
El dataset `caniuse-lite` tiene una excepción por versión en la auditoría, con
atribución y licencia completa conservadas en el repositorio.
