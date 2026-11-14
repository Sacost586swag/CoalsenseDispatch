# Requisitos: 04 Espacio de trabajo

**Estado:** completo. Notación y tipos de prueba: `01-capa-de-entrada/requirements.md` sección 0.
**Cubre:** las tres herramientas de producción del MVP y sus entregables, el editor común y la pantalla de herramientas conectadas.
**Tareas del MVP (confirmadas):** (1) redactar y enviar un correo o mensaje profesional, (2) convertir notas dictadas en un documento ordenado, (3) preparar una publicación para redes sociales y dejarla lista para publicar.
**Vertical aplicable:** V-01, V-05, V-08. Reglas AX-02, AX-06, AX-09.

## 1. Alcance

Dentro: editor accesible por voz, los tres tipos de tarea y sus agentes y herramientas, entregables, versiones, pantalla de herramientas conectadas.
Fuera: publicación automática en redes (no está en el MVP), mercado de trabajos y pagos (08), adjuntos de correo `[POST-MVP]`.

## 2. Requisitos funcionales

### Grupo A. Editor común

**HU-04-A.** Como persona que no usa las manos, quiero revisar y corregir lo que preparó la IA con la voz o la cabeza, sin seleccionar texto con puntería, para tener la última palabra.

- **REQ-04-001** THE SYSTEM SHALL mostrar cada propuesta en un editor de texto cuyos bloques (párrafos, viñetas, encabezados) están numerados y se pueden seleccionar por su número, sin necesidad de seleccionar texto con el puntero. Prueba: `e2e`.
- **REQ-04-002** WHEN la persona dicta una instrucción de edición sobre un bloque (por ejemplo «más corto el 3», «más formal el 2», «borra el 4»), THE SYSTEM SHALL aplicarla solo a ese bloque y mostrar el antes y el después. Prueba: `e2e`.
- **REQ-04-003** THE SYSTEM SHALL permitir dictar texto nuevo en la posición indicada por número de bloque. Prueba: `e2e`.
- **REQ-04-004** THE SYSTEM SHALL guardar versiones de cada propuesta y permitir volver a una versión anterior con `control.undo` o por su número. Prueba: `unit`.
- **REQ-04-005** THE SYSTEM SHALL leer en voz alta la propuesta con la voz local, a petición de la persona, bloque por bloque y con pausa y reanudación. Prueba: `e2e`.
- **REQ-04-006** THE SYSTEM SHALL NOT requerir seleccionar texto con el puntero, arrastrar ni hacer doble clic en el editor (V-05). Prueba: `a11y`.
- **REQ-04-007** THE SYSTEM SHALL conservar el borrador y las versiones aunque la persona pause la tarea, cierre la aplicación o se detenga el servicio. Prueba: `integration`.

### Grupo B. Tarea 1: correo o mensaje profesional

- **REQ-04-020** WHEN la persona elige redactar un correo o mensaje, THE SYSTEM SHALL pedir destinatario, propósito y tono por dictado o selección, y producir un borrador con asunto y cuerpo. Prueba: `e2e`.
- **REQ-04-021** THE SYSTEM SHALL ofrecer variantes del borrador (más formal, más breve, más cálido) como propuestas a elegir. Prueba: `e2e`.
- **REQ-04-022** THE SYSTEM SHALL permitir a la persona conectar su cuenta de correo con una autorización de la cuenta (OAuth) completable sin manos o con ayuda del cuidador/a, y SHALL guardar las credenciales de forma cifrada y solo accesibles para el gateway. Prueba: `security`.
- **REQ-04-023** WHEN la persona pide enviar, THE SYSTEM SHALL tratarlo como una acción `external_effect` y mostrar en la tarjeta de aprobación el remitente, los destinatarios exactos, el asunto y el cuerpo completos. Prueba: `e2e`.
- **REQ-04-024** THE SYSTEM SHALL leer en voz alta los destinatarios antes de la aprobación si la persona lo eligió, y SHALL destacar los destinatarios que no estaban en la tarea original o que se añadieron después. Prueba: `e2e`.
- **REQ-04-025** THE SYSTEM SHALL NOT enviar ningún correo o mensaje sin un sello de aprobación válido sobre el contenido exacto (SP-1). Prueba: `security`.
- **REQ-04-026** WHEN el envío termina, THE SYSTEM SHALL mostrar el resultado y guardar una copia del enviado en la tarea. Prueba: `integration`.
- **REQ-04-027** THE SYSTEM SHALL ofrecer enviar primero a la propia persona como prueba, tratándolo igualmente como acción con efecto externo con aprobación. Prueba: `e2e`.
- **REQ-04-028** IF el proveedor de correo rechaza el envío o la conexión caduca, THEN THE SYSTEM SHALL decirlo en lenguaje llano, conservar el borrador y ofrecer reconectar. Prueba: `e2e`.

### Grupo C. Tarea 2: notas dictadas a documento

- **REQ-04-030** WHEN la persona dicta notas libres, THE SYSTEM SHALL producir un documento ordenado con título, secciones, listas y resumen opcional, conservando el sentido de lo dictado sin añadir hechos. Prueba: `e2e` (conjunto de dictados de muestra revisados).
- **REQ-04-031** THE SYSTEM SHALL marcar visiblemente cualquier fragmento que la IA haya reformulado de forma importante, para que la persona lo revise. Prueba: `e2e`.
- **REQ-04-032** THE SYSTEM SHALL guardar el documento en Markdown y permitir exportarlo a DOCX y PDF [SUPUESTO, PA-16]. Prueba: `integration`.
- **REQ-04-033** WHEN la persona guarda o exporta el documento en el propio dispositivo o en su espacio en la plataforma, THE SYSTEM SHALL tratarlo como acción interna (`internal_write`) sin pedir aprobación. Prueba: `unit`.
- **REQ-04-034** WHEN la persona pide compartir el documento fuera de la plataforma (por correo, enlace o servicio conectado), THE SYSTEM SHALL tratarlo como acción `external_effect` con aprobación, mostrando con quién se comparte y qué permisos tendrá. Prueba: `e2e`.
- **REQ-04-035** THE SYSTEM SHALL permitir añadir más dictado a un documento existente sin rehacerlo. Prueba: `e2e`.

### Grupo D. Tarea 3: publicación para redes sociales

- **REQ-04-040** WHEN la persona elige preparar una publicación, THE SYSTEM SHALL pedir tema, red de destino y tono, y producir el texto con variantes. Prueba: `e2e`.
- **REQ-04-041** THE SYSTEM SHALL aplicar los límites de longitud y formato de la red elegida desde una configuración por red, y avisar si el texto los supera. Prueba: `unit`.
- **REQ-04-042** THE SYSTEM SHALL sugerir texto alternativo para imágenes cuando la persona adjunte una, para que la publicación sea accesible. Prueba: `e2e`.
- **REQ-04-043** THE SYSTEM SHALL dejar la publicación en un estado «lista para publicar» (texto final, variantes, texto alternativo), guardada en la tarea, y NOT publicarla por sí misma en el MVP. Prueba: `integration`.
- **REQ-04-044** WHEN la persona pide copiar la publicación, THE SYSTEM SHALL ponerla en el portapapeles con una sola orden. Prueba: `e2e`.
- **REQ-04-045** THE SYSTEM SHALL avisar si el texto parece incluir datos personales de terceros (teléfonos, correos, direcciones) y pedir a la persona que decida si los conserva. Prueba: `unit`.
- **REQ-04-046** WHERE en el futuro se conecte una herramienta que publique, THE SYSTEM SHALL tratar la publicación como acción `external_effect` con aprobación (V-01). Prueba: `unit`.

### Grupo E. Herramientas conectadas (catálogo ampliable)

**HU-04-E.** Como persona, quiero ver qué herramientas tengo conectadas y añadir otras cuando las necesito, para que el sistema crezca con mi trabajo.

- **REQ-04-050** THE SYSTEM SHALL mostrar el catálogo de herramientas habilitadas y las disponibles para habilitar, cada una con su descripción en lenguaje llano, los datos que recibe y si puede cambiar algo fuera de la plataforma. Prueba: `e2e`.
- **REQ-04-051** WHEN la persona (o su cuidador/a con delegación) habilita o deshabilita una herramienta, THE SYSTEM SHALL pedir una aprobación explícita que describa el efecto y aplicarlo de inmediato. Prueba: `e2e`.
- **REQ-04-052** THE SYSTEM SHALL mostrar el estado de cada herramienta (conectada, desconectada, con error) con texto y ofrecer reconectar. Prueba: `a11y`.
- **REQ-04-053** THE SYSTEM SHALL NOT mostrar como disponible ninguna herramienta que no esté en el catálogo curado del MVP (REQ-02-030). Prueba: `unit`.

### Grupo F. Estados de pantalla

- **REQ-04-054** *Cargando, vacío, error y sin conexión.* THE SYSTEM SHALL cumplir en el editor y en el catálogo los estados de AX-11: mientras la IA prepara una propuesta se puede seguir editando y usar Alto; sin tareas se ofrece elegir una; ante un error se ofrece reintentar o editar a mano; sin conexión se conserva y se permite editar a mano. Prueba: `e2e`.

## 3. Requisitos no funcionales

- **REQ-04-060** THE SYSTEM SHALL cumplir WCAG 2.2 AA, y como objetivo AAA 44×44 px CSS y ausencia de límites de tiempo, en el editor y las pantallas de las tres tareas. Prueba: `a11y`.
- **REQ-04-061** THE SYSTEM SHALL mostrar el primer borrador de una tarea en un máximo de 15 s en el 95% de los casos con el proveedor principal disponible [SUPUESTO]. Prueba: `perf`.
- **REQ-04-062** THE SYSTEM SHALL NOT enviar a un proveedor de modelo contenido de la persona sin consentimiento vigente de esa categoría (spec 05). Prueba: `security`.
- **REQ-04-063** THE SYSTEM SHALL cifrar los borradores, versiones y entregables en reposo con la clave de la persona. Prueba: `security`.
- **REQ-04-064** THE SYSTEM SHALL NOT incluir en el texto de la interfaz ni en las propuestas lenguaje de consejo médico, psicológico, legal ni financiero (SF-02). Prueba: `audit`.

## 4. Dependencias

| Spec | Relación |
| --- | --- |
| 00 | Componentes (tarjeta de aprobación, pantalla de estado) |
| 01 | Dictado, comandos por número, voz local |
| 02 | Agentes, herramientas del gateway, políticas |
| 03 | Ciclo de control, aprobación, logros |
| 05 | Consentimientos |

## 5. Preguntas abiertas

PA-15 (proveedor de correo), PA-16 (formato del documento), PA-17 (red social). No bloquean: el MVP arranca con un proveedor de correo, Markdown con exportación y redes configurables.
