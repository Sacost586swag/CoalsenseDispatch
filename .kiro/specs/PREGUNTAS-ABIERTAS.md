# Preguntas abiertas

Estado: fase 2 (requisitos, diseño y tareas completos). El operador respondió las preguntas de la fase 1 y aceptó mis recomendaciones. Lo que sigue abierto no bloquea la construcción del MVP.

## 1. Resueltas

| ID | Pregunta | Decisión |
| --- | --- | --- |
| PA-01 | Nombre del proyecto | **Coalsense Dispatch**. |
| PA-02 | Tres tipos de tarea del MVP | Confirmados: (1) correo o mensaje profesional, (2) notas dictadas a documento, (3) publicación para redes lista para publicar. Además, el catálogo de herramientas se amplía según la necesidad de la persona mediante servidores MCP en el gateway (spec 02). |
| PA-03 | Primer segmento | Discapacidad física; persona de ejemplo con pérdida de movilidad por lesión medular cervical. |
| PA-04 | Línea de ayuda oficial | Omitida por decisión del operador. Se trata como **dato de configuración** (sin número en el código) y como puerta de lanzamiento: ver C-06. |
| PA-05 | Piloto en Cuenca y consentimiento | Se construye primero el MVP; el piloto queda para después. Se conserva como puerta de lanzamiento (`safety.md` SF-06). |
| PA-06 | Contenido de tareas hacia el proveedor del modelo | Consentimiento explícito por categoría, minimización, y nada del perfil de capacidad ni de la condición declarada (SP-6). |
| PA-07 | Mirada y switch fuera del MVP | Aceptado: `[POST-MVP]`, con el bus y el perfil listos para sumarlos. |
| PA-08 | `help.request_human` en toda modalidad | Aceptado. |
| PA-09 | Estrategia de licencias | Aceptado: se asume producto **propietario** `[SUPUESTO]` hasta que el operador diga lo contrario; sin GPL en el artefacto distribuido; Piper aislado o alternativa MIT; n8n solo si un abogado lo avala. Ver la tabla de riesgos de `tech.md`. |
| PA-10 | Hardware real y motor de voz | Aceptado: se mide en hardware real antes de fijar el motor; el diseño de 01 incluye un motor alterno para comandos. |
| PA-11 | Actuador de escritorio en la spec 01 | Aceptado. Las peticiones de actuación solo se aceptan desde el bus (REQ-01-067). |
| PA-12 | Regulación ecuatoriana de apps de salud mental con IA | Aceptado: consultar a un abogado antes de ofrecerlo a personas reales (SF-06). |
| PA-13 | Fixtures de personas reales | Aceptado: sintéticas primero; reales solo con consentimiento registrado (REQ-01-100). |
| PA-14 | Idioma y variante | Español de Ecuador en el MVP. |

## 2. Abiertas (no bloquean el MVP)

| ID | Pregunta | Spec | Mi recomendación |
| --- | --- | --- | --- |
| PA-15 | **Proveedor de correo** para la tarea 1 (Gmail, Outlook, SMTP genérico) y **cómo conecta la persona su cuenta** (OAuth). | 04 | Empezar con un solo proveedor vía OAuth y un servidor MCP o flujo n8n detrás del gateway. Elegir el que más use la persona de ejemplo. |
| PA-16 | **Formato de salida del documento** (tarea 2): DOCX, PDF, Markdown. | 04 | Markdown como formato interno y exportación a DOCX y PDF. |
| PA-17 | **Redes sociales** (tarea 3): para qué red(es) se prepara la publicación. | 04 | En el MVP solo se deja "lista para publicar" (texto, variantes y recordatorios de formato); no hay publicación automática. |
| PA-18 | **Hosting de producción y región de los datos.** ¿Dónde viven la base de datos y los servicios? Impacta la transferencia internacional bajo LOPDP `[verificar]`. | 07, 09 | Decidir con el abogado; mientras tanto, entorno de prueba en contenedores. |
| PA-19 | **Canal de aviso al contacto de confianza** (correo, SMS, mensajería). | 05 | Correo primero; SMS cuando haya proveedor. |
| PA-20 | **Gestión de claves** (KMS administrado o propio) para el cifrado por persona. | 07 | KMS administrado del proveedor de nube elegido. |
| PA-21 | **Identidad del cuidador/a:** ¿se verifica de algún modo más allá de la invitación de la persona? | 06 | La invitación de la persona basta en el MVP; verificación fuerte en la fase 2. |
| PA-22 | **Relación persona-empresa** (laboral, servicios profesionales o por plataforma). Define impuestos, seguridad social y la cuota del 4% `[verificar con abogado]`. | 08 (fase 2) | Decidir con abogado antes de construir la fase 2. |
| PA-23 | **Proveedor de pagos** que opere en Ecuador con depósito en garantía. | 08 (fase 2) | Investigar cuando empiece la fase 2. |
| PA-24 | **Documento que acredita la discapacidad** y cómo verificarlo sin exponer datos de salud. | 08 (fase 2) | Constancia mínima firmada (REQ-08-030). |
| PA-25 | **Representación legal** de personas con incapacidad legal: quién consiente. | 05, 06, 07 | Consultar a un abogado antes de ofrecerlo a personas reales (SF-06). |

### Decisión del operador (2026-11-14)

El operador aceptó todas las recomendaciones de la tabla anterior. Quedan así:

- **PA-15:** un solo proveedor de correo vía OAuth, detrás del gateway. Falta elegir cuál; se decide antes del hito 7 de `docs/PLAN.md`.
- **PA-16:** Markdown como formato interno; exportación a DOCX y PDF.
- **PA-17:** en el MVP la publicación solo queda "lista para publicar", sin publicación automática. Falta elegir las redes; se decide antes del hito 7.
- **PA-18:** se decide con el abogado; mientras tanto, entorno de prueba en contenedores.
- **PA-19:** correo primero; SMS cuando haya proveedor.
- **PA-20:** KMS administrado del proveedor de nube que se elija.
- **PA-21:** en el MVP basta la invitación de la persona; verificación fuerte en la fase 2.
- **PA-22 a PA-25:** se consultan con un abogado antes de la fase 2 o antes de ofrecerlo a personas reales (SF-06).

## 3. Conflictos con la vertical y su resolución

Cuando algo contradice la vertical, gana la vertical.

| ID | Conflicto | Resolución |
| --- | --- | --- |
| C-01 | V-06 ("solo salen eventos e intenciones") frente a la necesidad de enviar texto de la tarea al modelo. | Video, audio y landmarks nunca salen. El texto sale solo con consentimiento explícito y mínimo necesario. |
| C-02 | V-05 ("sin límite de tiempo") frente al dwell y al escaneo. | Son tiempos que la persona ajusta y que nunca vencen una decisión. |
| C-03 | V-05 ("sin precisión fina") frente a mover el cursor con la cabeza. | Siempre existe una vía sin puntería: números, cuadrícula o imán. |
| C-04 | V-10 y licencias: Piper activo (GPL-3.0), n8n y librerías de mirada GPL frente a un producto propietario. | PA-09. |
| C-05 | V-07: detectar crisis implica analizar texto o voz sensibles. | Solo señales explícitas, reglas locales, sin inferir estado de ánimo. |
| C-06 | La vertical pide derivar a una **línea de ayuda oficial**; el operador pidió omitir la pregunta. | El protocolo la usa como dato de configuración. Sin ninguna ruta humana configurada, el sistema no se ofrece a personas reales (SF-06). El operador decide cuándo definirla. |
| C-07 | V-01 exige aprobación en el momento para toda acción externa; el aviso al contacto de confianza en una crisis es una acción externa. | Modo por defecto: el sistema **pregunta** a la persona antes de avisar. Solo si la persona eligió antes y de forma explícita "avisar automáticamente", el aviso sale sin preguntar. Es una autorización previa, revocable y visible. |
| C-08 | V-03 ("la persona fija cuánto hace la IA sola") frente a V-01 (aprobación de toda acción externa). | El dial regula los pasos internos de la IA. **Nunca elimina la aprobación de una acción con efecto externo.** Gana V-01. |
| C-09 | V-11 ("el operador no ve contenido privado") frente a un orquestador que debe leer el contenido para llamar al modelo. | El operador no tiene ninguna vía de lectura (sin pantalla, sin rol de base de datos, claves por persona). El proceso del orquestador ve el contenido de forma transitoria. Riesgo residual documentado en `07/design.md`. |

## 4. Supuestos registrados

| ID | Supuesto |
| --- | --- |
| S-01 | Windows primero. |
| S-02 | Español de Ecuador. |
| S-03 | Hardware de referencia: 4 núcleos físicos, 8 GB de RAM, sin GPU dedicada, cámara 720p a 30 fps. |
| S-04 | Presupuestos de latencia, CPU y memoria marcados `[SUPUESTO]`; se reemplazan por valores medidos. |
| S-05 | Mirada y switch son `[POST-MVP]`. |
| S-06 | Código e identificadores en inglés; documentación e interfaz en español. |
| S-07 | UI del companion como WebView que reutiliza `packages/ui`. |
| S-08 | Un "alto" dicho solo, como enunciado aislado, se trata como Alto durante el dictado. |
| S-09 | Seguimiento de varios rostros por continuidad espacial, sin reconocimiento facial. |
| S-10 | Métrica norte tomada de la propuesta de la investigación. |
| S-11 | La sincronización del perfil de capacidad entre dispositivos queda fuera del MVP; el perfil vive solo en el dispositivo. |
| S-12 | Producto propietario (PA-09). |
| S-13 | Pagos y mercado B2B solo en requisitos y diseño (fase 2). |

## 5. Verificado (2026-11-14)

| Dato | Resultado |
| --- | --- |
| `talonhub/community` | MIT (archivo LICENSE leído). |
| Project Gameface | Apache 2.0; archivado el 5 de septiembre de 2025. |
| MediaPipe Face Landmarker | 478 landmarks y 52 blendshapes. |
| Piper | Original MIT archivado en octubre de 2025; el mantenimiento activo está en un repositorio GPL-3.0 (fuentes secundarias, `[verificar]`). |
| n8n | Sustainable Use License: restringe usarlo como parte de un producto que se vende (texto de la licencia leído en resumen, `[verificar]` con abogado). |
