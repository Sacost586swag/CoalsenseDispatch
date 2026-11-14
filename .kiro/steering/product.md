# Producto

> Fuente de verdad de la vertical. Si una decisión de alcance, diseño o técnica la contradice, **gana la vertical** y se avisa al operador antes de seguir.

## Qué es

**Coalsense Dispatch** (nombre confirmado) es un sistema operativo de IA (AIOS) que permite a personas con discapacidad física o con depresión controlar la computadora sin las manos y producir trabajo pagado con ayuda de agentes de IA.

## Por qué existe

El acceso físico a la computadora (voz, cabeza, mirada, switches) ya existe gratis y abierto (Talon, Project Gameface, OptiKey, ACAT). Lo escaso es la capa de arriba: convertir "puedo mover el cursor" en "puedo cobrar por un trabajo". Las personas con discapacidad o con depresión no tienen acceso real a la IA y la automatización, y por eso no compiten ni ganan dinero en igualdad de condiciones. El producto nivela esas capacidades para que produzcan con libertad.

Fuente: `docs/IA contra la indefensión aprendida — Investigación base.md`.

## Enfoque psicológico

La pasividad es la respuesta por defecto ante el estrés prolongado. Lo que protege es aprender que uno tiene control (Maier y Seligman 2016; Baratta, Seligman y Maier 2023). Por eso el producto no "motiva": fabrica experiencias de control reales, pequeñas y repetidas, decididas por la persona. Si la IA hace todo sola, el control vuelve a ser de la máquina.

La activación conductual se aplica como **diseño de tareas**, no como intervención clínica (ver `safety.md`).

## Vertical innegociable

Cada regla tiene un ID para citarla en specs y tareas.

| ID | Regla |
| --- | --- |
| V-01 | **La persona decide, la IA ejecuta.** Toda acción con efecto externo (enviar, publicar, cobrar, borrar, compartir) requiere aprobación explícita de la persona, con la modalidad de entrada que ella use. Sin aprobación, la acción no ocurre. |
| V-02 | **El ciclo de control es la unidad del producto** y se repite en cada tarea (ver abajo). |
| V-03 | **Dial de autonomía.** La persona fija cuánto hace la IA sola, por tipo de tarea. Por defecto la persona aprueba todo. Subir el dial es decisión de la persona, nunca del sistema. |
| V-04 | **"Alto" y "deshacer" universales.** Existen en todas las modalidades de entrada, siempre activos, y detienen o revierten la última acción reversible. |
| V-05 | **Acceso sin manos y sin precisión motora fina.** Ninguna función depende de clic preciso, arrastre, doble clic rápido ni límite de tiempo. |
| V-06 | **Cámara y micrófono se procesan en el dispositivo.** El video nunca sale de la máquina; solo salen eventos e intenciones. Voz local por defecto; nube opcional y con consentimiento explícito. |
| V-07 | **No es terapia.** No diagnostica, no trata, no promete efectos clínicos. Ante señales de crisis deriva a una persona; la IA no maneja la crisis por su cuenta. |
| V-08 | **Ley de Arthur.** El orquestador nunca llama una API directo: usa herramientas de un gateway o delega en un agente. Ningún agente escribe directo en la base de datos de producción. Ninguna acción externa sin política. Toda ejecución deja rastro en la bitácora que la persona puede leer. |
| V-09 | **Datos sensibles.** Discapacidad y salud son categorías especiales bajo la LOPDP de Ecuador: consentimiento explícito, minimización, cifrado en reposo y en tránsito, exportación y borrado a pedido. No se guarda un diagnóstico salvo que la persona lo declare para ajustar su perfil. |
| V-10 | **Licencias.** El núcleo de Talon tiene EULA: solo inspiración de diseño, no se embebe ni se redistribuye. `talonhub/community` es MIT (verificado, 2026-11-14). Project Gameface es Apache 2.0 y está archivado desde el 5 de septiembre de 2025 (verificado): si se reutiliza código, se hace fork con atribución y no se depende del repositorio original. |
| V-11 | **El operador no ve contenido privado** de las personas. |
| V-12 | **El cuidador/a actúa con permisos delegados y revocables** y nunca decide ni aprueba por la persona sin permiso explícito vigente. |

## Ciclo de control

1. La persona elige una tarea concreta con resultado visible.
2. Los agentes ejecutan lo pesado.
3. La persona revisa y aprueba.
4. El resultado sale al mundo (entregable enviado, pago recibido).
5. Queda registrado como logro, y la siguiente tarea es un poco más grande.

## Actores

| Actor | Rol | Límite |
| --- | --- | --- |
| Persona usuaria | Discapacidad física (movilidad reducida, en cama, cuadriplejia, ELA) o depresión, o ambas. Usa voz, cabeza, gestos, mirada o un único switch. | Es quien decide siempre. |
| Cuidador/a | Configura el equipo y acompaña. | Permisos delegados y revocables (V-12). |
| Contacto de confianza | Recibe alertas. | Solo si la persona lo autorizó. |
| Empresa cliente (fase 2) | Publica trabajos, recibe entregables y paga. En Ecuador las empresas tienen una cuota laboral del 4% para personas con discapacidad. | Fuera del MVP. |
| Operador | Administra la plataforma. | No ve contenido privado (V-11). |

## Segmento inicial

Discapacidad física, con una persona de ejemplo con **pérdida de movilidad por lesión medular cervical** (confirmado). El ejemplo orienta el diseño; no es un dato que el sistema guarde ni un diagnóstico que asuma.

Consideraciones de diseño [SUPUESTO, a validar con personas reales cuando se pruebe el producto]:

- Suele conservarse el movimiento de cabeza y cuello y el habla: voz y cabeza/gestos son las modalidades principales, como en el alcance del MVP. El volumen de voz puede ser bajo o variar con la fatiga o la postura.
- Se usa en cama, silla reclinada o silla de ruedas: el ángulo de la cámara cambia, y cambiar de postura es frecuente.
- Cansancio y pausas frecuentes: todo se puede pausar y retomar sin perder avance (AX-13).
- Algunas personas conservan función parcial de las manos: teclado y mouse adaptados siguen siendo una modalidad válida.

Depresión sigue dentro de la vertical: el protocolo de crisis (`safety.md`) se construye desde el primer día para todas las personas.
## Alcance del MVP

Onboarding con calibración que termina con la primera tarea completada en la sesión 1 → control de la app y del PC por voz y por cabeza/gestos → el orquestador ejecuta tres tipos de tarea con aprobación → registro de logros → protocolo de crisis → panel básico del cuidador.

Tres tipos de tarea del MVP (confirmados):

1. Redactar y enviar un correo o mensaje profesional.
2. Convertir notas dictadas en un documento ordenado.
3. Preparar una publicación para redes sociales y dejarla lista para publicar.

**Herramientas ampliables (MCP).** El catálogo de herramientas crece según la necesidad de cada persona: se pueden conectar servidores MCP al gateway de herramientas. La persona (o su cuidador/a con delegación) habilita cada herramienta; el sistema nunca habilita una por su cuenta. Toda herramienta con efecto externo sigue sujeta a aprobación (V-01, V-08).

**Fuera del MVP:** mercado de trabajos B2B y pagos (fase 2), app Android (fase 2), habla atípica con modelos personalizados (fase 3).

## Inspiraciones

- **Talon:** control total del PC por voz, sonidos y mirada; comandos declarativos en archivos `.talon`.
- **Project Gameface (Google):** cursor con la cabeza y clics con gestos faciales con webcam común (MediaPipe Face Landmarker: 478 puntos faciales, 52 blendshapes, umbral calibrable por gesto).
- **Arthur (AIOS del operador):** el orquestador razona y delega, las herramientas ejecutan, la memoria recuerda.

## Métrica norte [SUPUESTO, propuesta de la investigación]

Tareas completadas por la persona por semana, y días hasta el primer ingreso. Mide el mecanismo (control) y el resultado (dinero). No se mide el estado de ánimo.

## Lenguaje del producto

Español claro, sin culpar y sin prometer efectos clínicos. Palabras que no se usan en la interfaz ni en el marketing: terapia, tratamiento, cura, diagnóstico, "mejora tu depresión". Ver `safety.md`.

## Convenciones de marcado en specs

| Marca | Significado |
| --- | --- |
| `[SUPUESTO]` | Decisión o cifra que el operador no dio. Se confirma o se cambia. |
| `[verificar]` | Dato externo que hay que comprobar antes de depender de él. |
| `[MVP]` / `[POST-MVP]` | Hito de la función. |
| `[CODEX]` | Tarea paralelizable que puede construir Codex. |
| `[UI]` | Tarea de interfaz, resuelta con skills de diseño subordinadas a `accessibility.md`. |

