# Requisitos: 00 Fundaciones

**Estado:** completo, sin pendientes de aprobación. Notación y tipos de prueba: ver `01-capa-de-entrada/requirements.md` sección 0. Todo hito es `[MVP]` salvo que se indique.
**Cubre:** monorepo, CI, autenticación sin manos, design system accesible y convenciones comunes.
**Vertical aplicable:** V-05, V-08, V-09, V-10, V-11, V-12. Reglas AX-01 a AX-17.

## 1. Alcance

Dentro: monorepo pnpm + Turborepo y uv, CI y auditorías, configuración y secretos, errores y registros sin contenido privado, autenticación sin manos, design system (`packages/ui`).
Fuera: lógica de producto de las demás specs.

## 2. Requisitos funcionales

### Grupo A. Monorepo y CI

**HU-00-A.** Como equipo de construcción (personas y agentes), quiero un monorepo con CI que haga cumplir las reglas de la vertical, para que ninguna tarea las rompa sin que se note.

- **REQ-00-001** THE SYSTEM SHALL organizarse en un monorepo con pnpm y Turborepo para lo web y un workspace de uv para Python, con la estructura de `structure.md`, y WHEN se hace un checkout limpio, `pnpm install` y `uv sync` SHALL terminar sin errores. Prueba: `integration` (job de CI).
- **REQ-00-002** WHEN se abre un pull request, THE SYSTEM SHALL ejecutar lint, verificación de tipos y pruebas unitarias de los paquetes afectados, y SHALL bloquear la fusión si alguno falla. Prueba: `integration`.
- **REQ-00-003** THE SYSTEM SHALL ejecutar en CI las auditorías: licencias contra `THIRD_PARTY.md`, deriva del esquema de `packages/intents`, importaciones prohibidas (red en los módulos de visión y voz del companion; cliente de base de datos de producción en `agents/`; llamadas HTTP salientes fuera de `gateway/`), y detección de secretos. Prueba: `audit`.
- **REQ-00-004** IF una dependencia nueva no figura en `THIRD_PARTY.md` con licencia, versión y origen, o tiene una licencia no aprobada (GPL, AGPL o EULA en el artefacto distribuido), THEN THE SYSTEM SHALL fallar la CI. Prueba: `audit`.
- **REQ-00-005** WHEN cambia un archivo de `.kiro/specs/`, THE SYSTEM SHALL ejecutar la verificación de trazabilidad (cada requisito tiene al menos una tarea y una prueba) y la de glosario (ningún término prohibido), y fallar si no pasan. Prueba: `audit`.
- **REQ-00-006** THE SYSTEM SHALL versionar los archivos de bloqueo de dependencias y usar instalaciones congeladas en CI para builds reproducibles. Prueba: `audit`.
- **REQ-00-007** THE SYSTEM SHALL cargar la configuración de cada app desde variables de entorno validadas con un esquema, y IF falta o es inválida una variable, THEN la app SHALL fallar al arrancar con un mensaje claro y sin imprimir valores secretos. Prueba: `unit`.
- **REQ-00-008** THE SYSTEM SHALL NOT almacenar secretos en el repositorio ni en logs. Prueba: `audit` (escaneo de secretos).

### Grupo B. Errores, registros e i18n

- **REQ-00-009** THE SYSTEM SHALL usar un formato de error común (`code`, `message_es`, `recoverable`, `next_actions`) en todas las APIs y pantallas, con mensajes en español llano que no culpan a la persona (AX-12). Prueba: `unit` y `manual` (revisión del texto).
- **REQ-00-010** THE SYSTEM SHALL emitir registros técnicos estructurados con un depurador que elimina los campos de contenido (texto dictado, cuerpos de correo, nombres de archivos, perfil de capacidad), y SHALL fallar la prueba si un texto de muestra aparece en un registro. Prueba: `security`.
- **REQ-00-011** THE SYSTEM SHALL mantener todo texto de interfaz en un catálogo de español y fallar el lint si hay cadenas visibles fijas en el código. Prueba: `audit`.
- **REQ-00-012** THE SYSTEM SHALL generar identificadores únicos y marcas de tiempo monotónicas y de reloj con una biblioteca común a Python y TypeScript. Prueba: `unit`.

### Grupo C. Autenticación sin manos

**HU-00-C.** Como persona que no usa las manos, quiero crear mi cuenta, entrar y recuperar el acceso sin teclear contraseñas ni resolver pruebas de puntería, para empezar sin depender de nadie más que cuando yo lo elija.

- **REQ-00-020** THE SYSTEM SHALL autenticar sin contraseñas (código de un solo uso por correo y emparejamiento de dispositivo) y NOT usar CAPTCHA de puntería ni pruebas cognitivas (WCAG 3.3.8). Prueba: `a11y` y `e2e`.
- **REQ-00-021** THE SYSTEM SHALL permitir ingresar los códigos por voz, por cualquier modalidad o con ayuda del cuidador/a, y NOT hacer que un código venza por tiempo; los códigos se invalidan por uso, por generar otro o por exceder el número de intentos. Prueba: `e2e`.
- **REQ-00-022** THE SYSTEM SHALL mantener la sesión del dispositivo emparejado en el almacén de credenciales del sistema operativo [SUPUESTO], con rotación de credenciales, y NOT cerrar la sesión por inactividad mientras haya trabajo pendiente. Prueba: `integration`.
- **REQ-00-023** WHEN la persona revoca un dispositivo o una sesión, THE SYSTEM SHALL invalidarlos de inmediato y informarlo. Prueba: `e2e`.
- **REQ-00-024** THE SYSTEM SHALL emitir sesiones con el rol (`person`, `caregiver`, `operator`) y los permisos autorizados, y el rol `operator` SHALL NOT tener ningún permiso de lectura de contenido (V-11). Prueba: `security`.
- **REQ-00-025** WHEN hay intentos fallidos repetidos, THE SYSTEM SHALL limitar la frecuencia con espera creciente y SHALL NOT bloquear la cuenta de forma permanente; la recuperación pasa por una persona de apoyo autorizada. Prueba: `security`.
- **REQ-00-026** THE SYSTEM SHALL cifrar con TLS toda comunicación entre clientes y servicios. Prueba: `security`.
- **REQ-00-027** THE SYSTEM SHALL registrar en la bitácora los eventos de autenticación (alta, ingreso, revocación) sin secretos. Prueba: `integration`.

### Grupo D. Design system accesible (`packages/ui`)

**HU-00-D.** Como equipo y como persona usuaria, quiero componentes que ya cumplen las reglas de acceso, para que cada pantalla sea accesible por construcción.

- **REQ-00-040** THE SYSTEM SHALL definir tokens de color, espaciado, tipografía, movimiento y tamaño de objetivo, y el token de tamaño mínimo de objetivo SHALL NOT poder configurarse por debajo de 44×44 px CSS. Prueba: `unit`.
- **REQ-00-041** THE SYSTEM SHALL ofrecer los componentes base (botón, enlace, campo de texto, diálogo, lista numerada, indicador de progreso, aviso de estado, tarjeta de aprobación, pantalla de estado, paso a paso), cada uno con todos sus estados (normal, foco, activo, deshabilitado, error, cargando). Prueba: `a11y`.
- **REQ-00-042** THE SYSTEM SHALL derivar el nombre accesible de cada componente de su etiqueta visible (2.5.3). Prueba: `a11y`.
- **REQ-00-043** THE SYSTEM SHALL NOT incluir componentes que se cierren, avancen o venzan solos; los avisos permanecen hasta que la persona los descarta. Prueba: `a11y`.
- **REQ-00-044** THE SYSTEM SHALL ofrecer una barra persistente de Alto y Deshacer reutilizable (AX-05), con objetivos de al menos 44×44 px CSS, que no pueda ser cubierta por diálogos. Prueba: `a11y`.
- **REQ-00-045** THE SYSTEM SHALL ofrecer temas de alto contraste, texto ampliable y movimiento reducido, y respetar `prefers-reduced-motion`. Prueba: `a11y`.
- **REQ-00-046** THE SYSTEM SHALL ofrecer una pantalla de estado que implemente los estados obligatorios (cargando, vacío, error, sin conexión, calibración fallida, modalidad no detectada) con los campos: qué pasó, acciones posibles y qué sigue funcionando (AX-11). Prueba: `a11y`.
- **REQ-00-047** THE SYSTEM SHALL ofrecer un registro de objetivos de navegación, de modo que cada control interactivo exponga su geometría y su etiqueta a la capa de entrada (números en pantalla, dwell, escaneo). Prueba: `integration`.
- **REQ-00-048** THE SYSTEM SHALL NOT esconder información ni acciones detrás de hover, pulsación larga o gestos con trayectoria. Prueba: `a11y`.
- **REQ-00-049** THE SYSTEM SHALL ejecutar axe-core y la regla de geometría de 44×44 en CI para cada componente en cada estado. Prueba: `a11y`.
- **REQ-00-050** THE SYSTEM SHALL ofrecer la tarjeta de aprobación con: qué se aprueba, a quién llega, qué efecto tiene, aprobar, rechazar y decidir después, sin opción preseleccionada y sin vencimiento (AX-09). Prueba: `a11y`.

## 3. Requisitos no funcionales

- **REQ-00-060** THE SYSTEM SHALL cumplir WCAG 2.2 AA en `packages/ui` y como objetivo AAA el tamaño de objetivo (2.5.5) y la ausencia de límites de tiempo (2.2.3). Prueba: `a11y`.
- **REQ-00-061** THE SYSTEM SHALL completar el pipeline de CI de un pull request típico en un tiempo máximo [SUPUESTO: 15 minutos] sobre los paquetes afectados. Prueba: `perf`.
- **REQ-00-062** THE SYSTEM SHALL publicar `packages/ui` con un catálogo navegable donde cada componente muestre sus estados [SUPUESTO: Storybook u otra herramienta equivalente]. Prueba: `integration`.

## 4. Dependencias

| Spec | Qué entrega 00 |
| --- | --- |
| 01 | Esquema de intenciones (estructura), barra de Alto y Deshacer, registro de objetivos de navegación |
| 02 | Autenticación, formato de errores, registros sin contenido |
| 03 a 06 | Componentes (tarjeta de aprobación, pantalla de estado, paso a paso) |
| 09 | Pipeline de CI, entornos |

## 5. Preguntas abiertas

Ninguna que bloquee. Pendientes de configuración: proveedor de correo para los códigos (PA-15 lo cubre para el correo de tareas) y hosting (PA-18).
