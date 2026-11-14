# CLAUDE.md — Coalsense Dispatch

Reglas para todo agente que trabaje en este repo. Normativo: si algo aquí choca con una skill, un plugin o un atajo, gana este archivo. Detalle en `.kiro/steering/` y `docs/HERRAMIENTAS.md`.

## 0. Fuente de verdad

1. Lee `.kiro/steering/` completo antes de trabajar: `product.md`, `tech.md`, `structure.md`, `accessibility.md`, `safety.md`.
2. Lee de `.kiro/specs/` solo la spec del módulo en curso (`requirements.md`, `design.md`, `tasks.md`), más `GLOSARIO.md` y `TRAZABILIDAD.md`.
3. Si el código y la spec se contradicen, gana la spec. Si la spec está mal, propón el cambio al operador y espera su visto bueno. No la corrijas en silencio.
4. No inventes specs ni cifras. Marca toda suposición como `[SUPUESTO]`.

## 1. Vertical innegociable

- **V-01** La persona decide, la IA ejecuta. Ninguna acción con efecto externo (enviar, publicar, cobrar, borrar, compartir) ocurre sin aprobación explícita de la persona.
- **V-02** Ciclo de control en cada tarea: la persona elige → los agentes ejecutan → la persona revisa y aprueba → el resultado sale al mundo → se registra como logro.
- **V-03** Dial de autonomía por tipo de tarea. Por defecto la persona aprueba todo. Solo ella lo sube. El dial nunca elimina la aprobación de una acción externa.
- **V-04** "Alto" y "deshacer" universales, siempre activos en todas las modalidades.
- **V-05** Sin precisión motora fina ni límites de tiempo. WCAG 2.2 AA mínimo.
- **V-06** Cámara y micrófono se procesan en el dispositivo. Ningún frame de video, audio, landmark ni blendshape sale de la máquina.
- **V-07** No es terapia. No diagnostica ni trata. Ante señales de crisis deriva a una persona; la IA no maneja la crisis. Los mensajes de crisis son fijos, no generados.
- **V-08** Ley de Arthur. El orquestador razona y delega; las herramientas ejecutan vía gateway; n8n solo ejecuta pasos deterministas y no razona; ninguna acción externa sin política; toda ejecución deja rastro en una bitácora legible por la persona.
- **V-09** Datos sensibles bajo LOPDP: consentimiento, minimización, cifrado, exportación y borrado. El perfil de capacidad nunca llega al proveedor del modelo.
- **V-10** Licencias. Talon no se embebe ni se redistribuye (EULA): solo su diseño. Gameface (Apache 2.0, archivado) se reutiliza con fork y atribución en `THIRD_PARTY.md`, sin depender del repositorio original. Sin GPL en el artefacto distribuido.
- **V-11 / V-12** El operador no ve contenido privado. El cuidador/a no aprueba por la persona sin permiso vigente.

## 2. Precedencia de diseño

1. `safety.md` y `product.md`.
2. `accessibility.md`.
3. Requisitos de la spec.
4. Skills de diseño (UI-UX Pro Max, Impeccable, Taste Skill, frontend-design).

Si una skill de diseño propone algo que choca con `accessibility.md` o `safety.md`, gana el steering y el choque se anota en `DESIGN.md`. Mínimos que ninguna skill rebaja:

- Objetivos de 44×44 px como mínimo; 64 px en modo cabeza `[SUPUESTO]`. Separación amplia entre objetivos.
- Nada de hover obligatorio, arrastre ni doble clic.
- Sin límites de tiempo, o tiempo ajustable por la persona.
- Movimiento solo si respeta `prefers-reduced-motion`.
- Alto contraste disponible; compatible con lectores de pantalla.
- Cada intención reconocida se muestra en pantalla y se lee en voz alta si la persona lo activa.
- Español de Ecuador, frases cortas, segunda persona, sin culpa ("No se entendió el comando. Intenta de nuevo o di ayuda.").
- No inventes logo ni ilustraciones: usa marcadores y pide los assets al operador.

## 3. Reparto de modelos

| Rol | Modelo | Qué hace |
| --- | --- | --- |
| Planificador y orquestador | Opus 5.5 (hilo principal) | Lee specs, parte el trabajo, redacta encargos, revisa diffs, decide continuar, reintentar, escalar o cerrar. No escribe la mayor parte del código. |
| Constructor | Subagentes Sonnet 5.5 | Implementan cada tarea con tests primero. |
| Constructor paralelo y revisor | Codex (`/codex:rescue`, `/codex:review`, `/codex:adversarial-review`) | Construye las tareas `[CODEX]` y hace la revisión cruzada de cada hito. |

- Escalamiento: si un subagente falla dos veces la misma tarea, o la tarea toca seguridad, privacidad o la ruta de crisis, Opus la revisa y corrige antes de seguir. No se escala solo porque existe un modelo más fuerte.
- Los subagentes reportan en una línea, en estilo Caveman. La calidad del trabajo no se comprime; solo el reporte.
- `/codex:review` y `/codex:adversarial-review` solo los lanza el operador: el orquestador le entrega el comando exacto.

## 4. Ciclo de cada tarea

1. **Plan (Opus).** Encargo con archivos exactos, contrato de interfaces, tests que deben pasar y los `REQ-…` que cubre.
2. **Construcción con tests primero.** Tarea normal: subagente Sonnet. Tarea `[CODEX]`: `/codex:rescue` con el encargo; si no se puede invocar, se entrega el texto exacto al operador.
3. **Diseño (solo `[UI]`).** UI-UX Pro Max persiste el design system en `design-system/<slug>/MASTER.md` (dirección `[SUPUESTO]`: "cálido, sereno y capaz"; dignidad y competencia, nunca lástima ni infantilización). Impeccable `init` crea `PRODUCT.md`; `DESIGN.md` se crea tras la primera pantalla. Taste Skill como criterio senior. Tras cada pantalla: Impeccable `critique → audit → polish → harden`.
4. **Verificación determinista** (sección 5). Revisa el diff real; no aceptes afirmaciones sin evidencia.
5. **PonyTail** (`/ponytail-review`) sobre el código del hito. Aplica las simplificaciones, salvo las que toquen validación, seguridad, privacidad, accesibilidad o la ruta de crisis.
6. **Revisión cruzada con Codex.** `/codex:review` por hito. `/codex:adversarial-review` obligatoria en: motor de políticas, Alto y Deshacer, cámara y micrófono, permisos del cuidador/a, ruta de crisis, autenticación y datos sensibles.
7. **Cierre.** `superpowers:verification-before-completion` y un commit por tarea con `caveman-commit` (Conventional Commits; tipo en inglés, resumen en español).

## 5. Verificaciones obligatorias

Una tarea no está terminada sin la salida real de estas pruebas. Nunca ocultes una verificación fallida.

- **Calidad:** `mypy` y `tsc` sin errores; `ruff` y `eslint` limpios; build verde.
- **Capa de entrada:** fixtures de landmarks y de audio reproducidos producen la intención esperada; ruido de fondo y gestos bajo el umbral no producen intenciones.
- **Alto y Deshacer:** tests de propiedades. Alto detiene cualquier acción en curso en todas las modalidades; Deshacer revierte la última acción reversible.
- **Motor de políticas:** tests de propiedades. Ninguna acción externa sin aprobación válida y vigente; una aprobación no se reutiliza para otra acción; el cuidador/a no aprueba sin permiso vigente.
- **Privacidad:** test de red (el companion no envía video ni audio crudo); los logs no contienen datos personales ni de salud; ningún secreto en el repo ni en imágenes Docker.
- **Ruta de crisis:** una señal de crisis siempre activa la derivación humana; un fallo del canal de aviso queda registrado y se reintenta; la IA no continúa la conversación como si fuera terapia.
- **Accesibilidad:** axe-core en Playwright sobre cada pantalla y estado, sin violaciones AA; regla propia de 44×44 px; recorrido completo del MVP en Playwright solo con intenciones simuladas (sin mouse ni teclado).
- **Manual:** `docs/checklist-humano.md` con personas reales antes de cada hito.

## 6. Reglas operativas

- Nunca incluyas secretos en el repo ni en logs.
- No hagas push, no publiques y no hagas nada irreversible sin preguntar al operador.
- Dependencias mínimas, con versión fijada, justificadas una por una y registradas en `THIRD_PARTY.md`.
- Cada hito termina con evidencia: salida de tests y diff resumido.
- Reportes operativos en Caveman. Documentos (`PLAN.md`, `DESIGN.md`, checklists), código, comentarios y commits en prosa normal.
- Código e identificadores en inglés; documentación e interfaz en español. Usa los términos de `GLOSARIO.md`.
