# Stack técnico

> Todo el stack es **[SUPUESTO]** y editable. Cualquier cambio se justifica en el `design.md` de la spec afectada.

## Stack

| Ruta | Decisión |
| --- | --- |
| Monorepo | pnpm + Turborepo para lo web; uv para Python. |
| `apps/companion` | Python 3.12. Control del sistema operativo, Windows primero. MediaPipe Face Landmarker (patrón Gameface). `pynput` o `PyAutoGUI`. Reconocimiento de voz local con `faster-whisper` o `whisper.cpp` `[verificar rendimiento en el hardware objetivo]`. Gramática de comandos declarativa inspirada en `.talon`. |
| `apps/web` | Next.js + TypeScript, PWA. Espacio de trabajo, logros, panel del cuidador. MediaPipe Tasks Vision en el navegador como modo sin instalación. |
| `apps/orchestrator` | FastAPI. Planificador, agentes, motor de políticas, bitácora. |
| `packages/intents` | Esquema compartido de intenciones: JSON Schema → tipos Python y TypeScript. |
| `packages/ui` | Design system accesible (tokens y componentes base). |
| `infra/` | docker-compose: PostgreSQL + pgvector, Redis. n8n para acciones externas deterministas. |
| Modelos | Claude por API; OpenRouter como respaldo; enrutamiento por tipo de tarea. |
| Voz sintética | Piper local; ElevenLabs opcional (nube, con consentimiento). |
| Pruebas | pytest, Vitest, Playwright, axe-core, y tests de entrada reproducibles: grabaciones de landmarks faciales y de audio que se reproducen como fixtures. |
| Calidad [SUPUESTO] | Python: ruff + mypy. TypeScript: `strict`, ESLint, Prettier. |
| UI del companion [SUPUESTO] | Ventana con WebView que reutiliza `packages/ui`, para poder verificar con axe-core las mismas pantallas. Se decide en `01/design.md`. |

## Hechos verificados (2026-11-14)

| Tema | Resultado |
| --- | --- |
| `talonhub/community` | Licencia MIT. Se puede reutilizar con aviso de copyright. |
| Project Gameface | Apache 2.0. Repositorio archivado el 5 de septiembre de 2025 (solo lectura). |
| MediaPipe Face Landmarker | 478 landmarks 3D y 52 puntajes de blendshapes por rostro (documentación de Google). |

## Riesgos de licencia por resolver

| Componente | Riesgo | Estado |
| --- | --- | --- |
| Núcleo de Talon | Tiene EULA, no es open source. | Solo inspiración de diseño. |
| OptiKey, EyeGestures | GPL-3.0 según la investigación base. Embeberlos obligaría a publicar bajo GPL. | Solo referencia de diseño. |
| Piper | El repositorio original `rhasspy/piper` (MIT) se archivó en octubre de 2025. El mantenimiento activo está en `OHF-Voice/piper1-gpl` bajo GPL-3.0, según fuentes secundarias. | `[verificar]` antes de distribuirlo (PA-09). |
| n8n | Sustainable Use License: uso para fines internos de negocio o no comerciales; restringe revender o embeber como producto. | `[verificar]` con un abogado si encaja con una plataforma comercial (PA-09). |
| faster-whisper, modelos Whisper | Se esperan licencias permisivas. | `[verificar]` y registrar en `THIRD_PARTY.md`. |

## Reglas técnicas obligatorias

1. **Ley de Arthur.** El orquestador no llama APIs directo: solo vía herramientas del gateway o un agente. Los agentes no tienen credenciales de la base de datos de producción: escriben a través de un servicio de persistencia con política.
2. **Egreso de red del companion con lista permitida.** Ningún frame de video, audio, landmark ni blendshape cruza la red. Los módulos de visión y de voz no importan librerías de red (regla de lint).
3. **Bus de intenciones autenticado.** Solo adaptadores registrados publican. El origen del actor (`person`, `caregiver`, `system`) sale de la sesión autenticada, no del contenido del mensaje.
4. **Fuente única del esquema de intenciones.** `packages/intents` genera los tipos de Python y TypeScript. La CI falla si los tipos versionados difieren de los generados.
5. **Secretos** en variables de entorno o en un vault. Nunca en código ni en logs.
6. **Cifrado.** TLS en tránsito. En reposo: base de datos cifrada y almacenamiento local cifrado [SUPUESTO: protegido con la API de credenciales del sistema operativo].
7. **Minimización con los modelos.** El proveedor del LLM nunca recibe el perfil de capacidad ni la condición declarada. Los mensajes de crisis no los genera un modelo.
8. **Acciones externas deterministas.** Pasan por n8n o una herramienta del gateway, siempre detrás del motor de políticas y de la aprobación de la persona.
9. **Logs sin contenido privado.** Se registran metadatos (id, tipo, resultado), no audio, video, landmarks ni texto dictado.
10. **Dependencias.** Toda dependencia nueva se registra en `THIRD_PARTY.md` con licencia, versión y origen. La CI falla ante una licencia no aprobada.

## Rendimiento

Hardware de referencia **[SUPUESTO]**: portátil de gama media, 4 núcleos físicos, 8 GB de RAM, sin GPU dedicada, Windows 11, cámara web 720p a 30 fps. Los presupuestos de latencia y de CPU están en cada spec y se reemplazan por valores medidos tras el primer benchmark.

## Pruebas

- **Entrada reproducible:** las grabaciones de landmarks y de audio son fixtures. Con el mismo perfil y la misma versión de modelo, la secuencia de intenciones es la misma.
- **Fixtures con personas reales** solo con consentimiento registrado; si no, sintéticas (landmarks faciales pueden identificar a una persona).
- **Pirámide:** unit y contract (pytest, Vitest) → replay y integration → e2e (Playwright) → a11y (axe-core) → perf (benchmark en el hardware de referencia).
- **Auditorías en CI:** licencias, deriva del esquema, importaciones de red en los módulos de visión y voz.

## Pipeline de construcción

Las specs las consume Claude Code: un agente Opus 5.5 planifica; Sonnet 5.5 construye junto a Codex. Cada tarea debe entenderse sin contexto externo y caber en una sesión de un agente. `[CODEX]` marca tareas paralelizables; `[UI]` marca tareas de interfaz.
