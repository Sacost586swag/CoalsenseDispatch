# Requisitos: 05 Seguridad y bienestar

**Estado:** completo. Notación y tipos de prueba: `01-capa-de-entrada/requirements.md` sección 0.
**Cubre:** detección de señales de crisis, derivación a una ruta humana, límites de la IA y consentimientos.
**Vertical aplicable:** V-01, V-06, V-07, V-09, V-12. Propiedades: SP-5, SP-6, SP-7. Detalle de producto en `.kiro/steering/safety.md`.

## 1. Alcance

Dentro: reglas de señales explícitas de crisis, flujo de derivación, mensajes fijos, rutas humanas por configuración, límites de contenido de la IA, registro y captura de consentimientos.
Fuera: terapia, diagnóstico, seguimiento clínico, evaluación del estado de ánimo (V-07). Almacenamiento, cifrado, exportación y borrado (07).

## 2. Requisitos funcionales

### Grupo A. Señales de crisis y derivación

**HU-05-A.** Como persona, quiero que si estoy en crisis el sistema me conecte con una persona real y no intente manejarlo solo, para estar acompañada.

- **REQ-05-001** THE SYSTEM SHALL detectar señales explícitas de crisis mediante reglas versionadas (frases y patrones en español de Ecuador) aplicadas en el dispositivo al texto dictado, escrito y a los comandos, antes de que ese texto se envíe a ningún proveedor de modelo. Prueba: `replay` (corpus sintético).
- **REQ-05-002** WHEN una regla detecta una señal de crisis, THE SYSTEM SHALL NOT enviar ese texto a ningún proveedor de modelo ni guardarlo en la memoria (SP-6). Prueba: `security`.
- **REQ-05-003** WHEN una regla detecta una señal de crisis o la persona emite `help.request_human`, THE SYSTEM SHALL iniciar la derivación humana, y la señal SHALL llegar siempre a la ruta humana (SP-5). Prueba: `integration` (prueba de propiedad sobre el corpus).
- **REQ-05-004** WHEN se inicia la derivación, THE SYSTEM SHALL pausar las acciones autónomas de los agentes de esa persona, dejando las tareas en estado detenido [SUPUESTO]. Prueba: `integration`.
- **REQ-05-005** WHEN se inicia la derivación, THE SYSTEM SHALL mostrar un **mensaje fijo y breve**, no generado por un modelo (SP-7), con las rutas humanas configuradas, operables con cualquier modalidad y con objetivos de al menos 44×44 px CSS. Prueba: `e2e`.
- **REQ-05-006** THE SYSTEM SHALL guardar en el dispositivo los mensajes fijos y la configuración de las rutas humanas, de modo que la derivación funcione sin conexión y sin modelo. Prueba: `integration` (red deshabilitada).
- **REQ-05-007** THE SYSTEM SHALL NOT conversar sobre la crisis, dar consejos ni intentar disuadir a la persona durante la derivación. Prueba: `unit`.
- **REQ-05-008** THE SYSTEM SHALL tomar las rutas humanas de una configuración (contacto de confianza y línea de ayuda oficial, más el número de emergencias) y NOT tener números ni destinatarios escritos en el código. Prueba: `audit`.
- **REQ-05-009** IF no hay ninguna ruta humana configurada, THEN THE SYSTEM SHALL mostrar un aviso persistente en la configuración y en el arranque, indicando que el sistema no debe ofrecerse a personas reales hasta configurarla (SF-06), y la pantalla de crisis SHALL mostrar el número de emergencias por defecto [verificar]. Prueba: `e2e`.
- **REQ-05-010** WHERE el contacto de confianza está autorizado, THE SYSTEM SHALL preguntar a la persona antes de avisarle, con opciones «avisar» y «no avisar» con el mismo tamaño y sin opción preseleccionada; y WHERE la persona eligió antes y de forma explícita «avisar automáticamente», THE SYSTEM SHALL avisar sin preguntar (C-07). Prueba: `e2e`.
- **REQ-05-011** THE SYSTEM SHALL limitar el aviso al contacto de confianza al hecho de que la persona pidió ayuda, sin incluir contenido de tareas ni de la señal. Prueba: `unit`.
- **REQ-05-012** WHEN la persona termina la derivación, THE SYSTEM SHALL dejarla decidir cuándo retomar y NOT mostrar pantallas de castigo, pérdida ni reproche. Prueba: `e2e`.
- **REQ-05-013** THE SYSTEM SHALL registrar en la bitácora que hubo una derivación (fecha, ruta usada) sin el contenido que la originó, visible para la persona y no para el operador. Prueba: `security`.
- **REQ-05-014** THE SYSTEM SHALL permitir configurar y probar el contacto de confianza, enviando un mensaje de prueba con aprobación de la persona, y revocarlo con una acción. Prueba: `e2e`.
- **REQ-05-015** THE SYSTEM SHALL NOT inferir ni puntuar el estado de ánimo, depresión o riesgo a partir de la cámara, la voz, el texto o los patrones de uso; solo reaccionar a las señales explícitas de las reglas (SF-01). Prueba: `audit`.
- **REQ-05-016** THE SYSTEM SHALL mantener las reglas de señales y los mensajes fijos en archivos versionados con su revisión (quién y cuándo) y fallar la CI si cambian sin una nota de revisión. Prueba: `audit`.
- **REQ-05-017** THE SYSTEM SHALL preferir el falso positivo al falso negativo: las reglas se prueban con un corpus donde el 100% de las frases marcadas como señal explícita debe activar la derivación, y se miden los falsos positivos sin bloquear la CI. Prueba: `replay`.

### Grupo B. Límites de la IA

- **REQ-05-020** WHEN la persona pide consejo médico, psicológico, legal o financiero, THE SYSTEM SHALL responder con el mensaje fijo de límites, explicar qué sí puede hacer y ofrecer una ruta humana, sin dar el consejo. Prueba: `e2e` (conjunto de peticiones de muestra).
- **REQ-05-021** THE SYSTEM SHALL revisar las propuestas y los textos generados con una lista de expresiones prohibidas (afirmaciones clínicas, promesas de efectos, suplantación de terapeuta) y reemplazar o marcar los que coincidan antes de mostrarlos. Prueba: `security`.
- **REQ-05-022** THE SYSTEM SHALL NOT hacerse pasar por una persona, por un terapeuta ni por la persona usuaria ante terceros, y SHALL identificar como generados por IA los mensajes que la IA propone cuando el destinatario podría confundirse [SUPUESTO: opción configurable por la persona]. Prueba: `unit`.
- **REQ-05-023** THE SYSTEM SHALL NOT usar mecanismos de manipulación (culpa, urgencia artificial, rachas que castigan) en ningún texto ni flujo. Prueba: `audit` y `manual`.
- **REQ-05-024** THE SYSTEM SHALL mantener la lista de palabras prohibidas de la interfaz (terapia, tratamiento, cura, diagnóstico, «mejora tu depresión») y fallar la CI si aparecen en el catálogo de textos. Prueba: `audit`.

### Grupo C. Consentimientos

**HU-05-C.** Como persona, quiero decidir con claridad qué datos usa el sistema y para qué, y poder cambiar de opinión, para confiar en él.

- **REQ-05-030** THE SYSTEM SHALL pedir un consentimiento explícito, separado y revocable por cada categoría de uso de datos: (1) enviar contenido de tareas a un proveedor de modelo (por proveedor), (2) reconocimiento de voz en la nube, (3) voz sintética en la nube, (4) aviso al contacto de confianza y su modo, (5) condición declarada, (6) contadores agregados de la métrica norte, (7) grabación de diagnóstico, (8) sincronización del perfil `[POST-MVP]`. Prueba: `e2e`.
- **REQ-05-031** THE SYSTEM SHALL tener todos los consentimientos desactivados por defecto. Prueba: `unit`.
- **REQ-05-032** THE SYSTEM SHALL presentar cada consentimiento con un resumen en lenguaje llano (qué datos, quién los recibe, para qué, qué pasa si no los da) y ofrecer leerlo en voz alta, con el texto completo disponible. Prueba: `a11y`.
- **REQ-05-033** THE SYSTEM SHALL poder usarse sin dar los consentimientos opcionales, con las funciones que dependan de ellos claramente deshabilitadas y explicadas. Prueba: `e2e`.
- **REQ-05-034** WHEN la persona revoca un consentimiento, THE SYSTEM SHALL dejar de usar los datos para esa categoría de inmediato. Prueba: `integration`.
- **REQ-05-035** THE SYSTEM SHALL guardar un registro de consentimientos con la categoría, la versión del texto, la decisión, la fecha y la modalidad usada, y permitir a la persona verlo y exportarlo. Prueba: `unit`.
- **REQ-05-036** THE SYSTEM SHALL ofrecer una consulta de consentimiento que el gateway, el constructor de prompts y el reconocimiento en la nube usen antes de enviar datos, y NOT enviar si no hay consentimiento vigente. Prueba: `security`.
- **REQ-05-037** WHEN cambia de forma importante el texto de un consentimiento, THE SYSTEM SHALL pedir una nueva decisión y mientras tanto tratarlo como no dado. Prueba: `unit`.
- **REQ-05-038** THE SYSTEM SHALL NOT hacer que un consentimiento venza por tiempo, y SHALL NOT pedirlo repetidamente cuando la persona lo rechazó. Prueba: `unit`.
- **REQ-05-039** WHERE el cuidador/a ayuda con los consentimientos, THE SYSTEM SHALL requerir que la decisión final la confirme la persona con su propia modalidad, salvo una delegación explícita y vigente para ello (spec 06) `[verificar con abogado si hay representante legal]`. Prueba: `security`.

### Grupo D. Estados de pantalla

- **REQ-05-045** THE SYSTEM SHALL cumplir los estados de AX-11 en las pantallas de esta spec: *cargando* (se muestra qué se prepara y la derivación sigue disponible), *vacío* (sin rutas humanas: se ofrece configurarlas), *error* (si falla un aviso, se informa y se ofrecen las demás rutas), *sin conexión* (la derivación local sigue disponible y se indica qué no lo está). Prueba: `e2e`.

## 3. Requisitos no funcionales

- **REQ-05-050** THE SYSTEM SHALL mostrar el mensaje fijo de derivación en un máximo de 1 s tras la detección o la solicitud, incluso sin conexión [SUPUESTO]. Prueba: `perf`.
- **REQ-05-051** THE SYSTEM SHALL NOT depender de la red, de un modelo de lenguaje ni del orquestador para la ruta humana local. Prueba: `integration`.
- **REQ-05-052** THE SYSTEM SHALL cumplir WCAG 2.2 AA y, como objetivo AAA, 44×44 px CSS y ausencia de límites de tiempo en las pantallas de crisis y de consentimientos. Prueba: `a11y`.
- **REQ-05-053** THE SYSTEM SHALL tratar los eventos de crisis y los consentimientos como datos de categoría especial: cifrados en reposo y fuera del alcance del operador. Prueba: `security`.
- **REQ-05-054** THE SYSTEM SHALL poder probar toda la ruta de derivación de extremo a extremo en el entorno de prueba con destinatarios ficticios, sin contactar a nadie real. Prueba: `e2e`.

## 4. Dependencias

| Spec | Relación |
| --- | --- |
| 01 | Emite `help.request_human`; aplica reglas locales al dictado |
| 02 | Consulta consentimientos; detiene agentes en la derivación |
| 03 | Tareas en estado detenido; reanudación por la persona |
| 06 | Delegaciones para ayuda con consentimientos |
| 07 | Cifrado, retención y borrado de eventos de crisis y consentimientos |

## 5. Preguntas abiertas

PA-19 (canal de aviso al contacto de confianza). La línea de ayuda oficial es un dato de configuración (C-06). Revisión de reglas y mensajes por un profesional de salud mental: puerta de lanzamiento (SF-06).
