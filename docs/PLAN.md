# Plan de construcción de Coalsense Dispatch

> **Para agentes ejecutores:** usa `superpowers:subagent-driven-development` tarea por tarea. El detalle de cada tarea (archivos, qué hacer, prueba y "terminado cuando") está en el `tasks.md` de su spec; este plan fija el orden, quién la construye, cómo se acepta y qué riesgo vigilar.

**Objetivo:** el MVP de Coalsense Dispatch, en el que una persona controla la computadora sin manos y completa con agentes tres tipos de tarea con aprobación, desde su primera sesión.

**Arquitectura:** un companion local en Python (entrada por voz y cabeza, bus de intenciones, actuador de Windows), un orquestador FastAPI (planificador, agentes, gateway de herramientas, motor de políticas, bitácora) y una app web Next.js (espacio de trabajo, logros, panel del cuidador/a). Se comunican solo con los tipos de `packages/intents`.

**Stack:** pnpm + Turborepo, uv, Python 3.12, FastAPI, Next.js + TypeScript, MediaPipe Face Landmarker, faster-whisper, PostgreSQL + pgvector, Redis, pytest, Vitest, Playwright, axe-core. Todo `[SUPUESTO]` según `tech.md`.

**Spec:** `.kiro/steering/` (cinco archivos), `.kiro/specs/ORDEN-DE-CONSTRUCCION.md` y los `requirements.md`, `design.md` y `tasks.md` de cada spec. Reglas de trabajo: `CLAUDE.md`.

**Estado:** aprobado por el operador el 2026-11-14. Sigue los hitos H0 a H6 de `.kiro/specs/ORDEN-DE-CONSTRUCCION.md` (versión de Kiro); si este plan y ese archivo chocan, gana el archivo de la spec.

## Restricciones globales

Toda tarea las cumple aunque su encargo no las repita.

- La persona decide, la IA ejecuta: ninguna acción con efecto externo sin aprobación explícita y vigente (V-01, SP-1).
- Alto, Deshacer y Ayuda humana activos en toda modalidad y en toda pantalla (V-04, AX-05, SP-2).
- Ningún frame de video, audio, landmark ni blendshape cruza la red; los módulos de visión y voz no importan librerías de red (V-06, SP-3).
- El perfil de capacidad y la condición declarada nunca llegan al proveedor del modelo (SP-6). Los mensajes de crisis son fijos (SP-7).
- Solo `apps/orchestrator/.../gateway/` hace llamadas salientes; los agentes no tienen credenciales de la base de datos (V-08).
- Sin GPL en el artefacto distribuido; toda dependencia en `THIRD_PARTY.md` con licencia, versión fijada y origen (V-10).
- Objetivos interactivos de 44×44 px como mínimo, 64 px en modo cabeza `[SUPUESTO]`; nada de hover obligatorio, arrastre, doble clic ni límite de tiempo (AX-02 a AX-04).
- Interfaz en español de Ecuador, frases cortas, sin culpa y sin palabras clínicas; identificadores en inglés (AX-12, SF-01).
- Logs sin contenido: solo id, tipo y resultado (`tech.md` regla 9).
- Ningún secreto en el repo, en logs ni en imágenes Docker.

## Riesgos que ninguna prueba cubre todavía (Review Focus)

Cinco situaciones que las specs implican y que ninguna prueba ejercita de forma explícita. La prueba nueva se suma a la tarea indicada.

1. **El eco de la voz sintética.** Cuando el sistema lee en voz alta, su propio audio no debe disparar comandos ni tapar un Alto dicho en voz baja. Prueba en T-01-021: fixture con la voz sintética de fondo y un "alto" a volumen bajo; se espera `control.stop` y ningún otro comando.
2. **Modalidades contradictorias a la vez.** Un gesto de aprobar y un "alto" de voz en la misma ventana de tiempo: gana Alto, y la aprobación no se emite. Prueba de propiedades en T-01-049.
3. **Caída del companion o del navegador durante la retención.** Si el cliente cae entre la aprobación y el despacho, la acción no se despacha sin que la persona pueda ver la retención; al volver, sigue pendiente o detenida, nunca enviada a ciegas. Prueba en T-02-014.
4. **Contenido en excepciones.** Una excepción con texto dictado o un borrador en su mensaje no debe llegar a los logs. Prueba en T-00-008: se lanza un error con contenido marcado y el log solo muestra el id.
5. **El actuador no puede actuar** (pantalla de bloqueo, ventana elevada de Windows). La persona recibe aviso por más de un canal, y Alto y Ayuda humana siguen funcionando. Prueba en T-01-033.

## Ciclo de cada tarea

Es el ciclo de `CLAUDE.md`, sección 4. En resumen:

1. Opus redacta el encargo: archivos, contrato de interfaces, prueba que debe pasar y REQ que cubre.
2. Construye la columna "Ejecuta": un subagente Sonnet o Codex (`/codex:rescue`), con la prueba primero.
3. Tareas `[UI]`: UI-UX Pro Max (design system persistido), Impeccable `init` (solo la primera vez) y, por pantalla, `critique → audit → polish → harden`.
4. Verificación: tipos, lint, pruebas, build y accesibilidad, con la salida real.
5. "+ revisión Opus": Opus revisa el diff línea por línea antes de aceptar. Si el subagente falla dos veces, Opus corrige.
6. Cierre: un commit por tarea con `caveman-commit`.

Al cierre de cada hito: `/ponytail-review` sobre el código del hito, `/codex:review` y, si el hito tiene tareas marcadas "Adversarial", `/codex:adversarial-review`. **Esos dos comandos de Codex solo los puedes lanzar tú**: te paso la línea exacta.

## H0 — Cimientos (spec 00)

Objetivo: que ninguna tarea posterior pueda romper la vertical sin que la CI lo note.

| Tarea | Título | Ejecuta | Aceptación | Riesgos |
| --- | --- | --- | --- | --- |
| T-00-001 | Esqueleto del monorepo | Sonnet | `tools/audit/tests/test_clean_checkout.py` pasa (integration) | — |
| T-00-002 | Pipeline de CI `[CODEX]` | Codex | `tools/audit/tests/test_ci_config.py` pasa (integration) | GitHub Actions es [SUPUESTO]; sin remoto la CI no corre en servidor: se ejecuta local con `turbo` hasta que haya remoto. |
| T-00-003 | Auditoría de licencias `[CODEX]` | Codex | `tools/audit/tests/test_audit_licenses.py` pasa (audit) | Piper (GPL) y n8n (Sustainable Use) deben quedar marcados (PA-09). |
| T-00-004 | Auditoría de importaciones prohibidas `[CODEX]` | Codex | `tools/audit/tests/test_audit_imports.py` pasa (audit) | — |
| T-00-005 | Auditoría de secretos `[CODEX]` | Codex + revisión Opus | `tools/audit/tests/test_audit_secrets.py` pasa (audit) | Adversarial Codex: Autenticación y datos sensibles. |
| T-00-006 | Auditoría de trazabilidad y glosario `[CODEX]` | Codex | `tools/audit/tests/test_audit_traceability.py` pasa (audit) | — |
| T-00-007 | Configuración, errores e identificadores comunes `[CODEX]` | Codex | `packages/common-py/tests/test_config_errors_ids.py` pasa (unit) | — |
| T-00-009 | Catálogo de textos en español y lint de cadenas `[CODEX]` | Codex | `tools/audit/tests/test_audit_copy.py` pasa (audit) | — |
| T-00-013 | Tokens y temas del design system `[CODEX]` | Codex | `packages/ui/tests/tokens.test.ts` pasa (unit) | Objetivos 44 px y 64 px en modo cabeza [SUPUESTO]; dirección "cálido, sereno y capaz" [SUPUESTO]. |
| T-00-008 | Registros estructurados con depurador de contenido `[CODEX]` | Codex + revisión Opus | `packages/common-py/tests/test_logging_scrub.py` pasa (security) | Adversarial Codex: Autenticación y datos sensibles. Incluir excepciones y trazas con contenido dictado (ver Review Focus 4). |
| T-00-010 | Servicio de autenticación sin contraseña | Sonnet + revisión Opus | `apps/orchestrator/tests/auth/test_codes_pairing.py` pasa (unit y security) | Adversarial Codex: Autenticación y datos sensibles. Sin contraseña y sin CAPTCHA (AX-16). |
| T-00-014 | Componentes base accesibles `[UI]` | Sonnet | `packages/ui/tests/components.test.tsx` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |
| T-00-011 | Sesiones, roles y revocación | Sonnet + revisión Opus | `apps/orchestrator/tests/auth/test_sessions_roles.py` pasa (security e integration) | Adversarial Codex: Autenticación y datos sensibles. |
| T-00-012 | Pantallas de autenticación accesibles `[UI]` | Sonnet | `apps/web/tests/e2e/auth.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |
| T-00-015 | Pantalla de estado, tarjeta de aprobación y barra de Alto y Deshacer `[UI]` | Sonnet | `packages/ui/tests/state-approval-stopbar.test.tsx` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |
| T-00-016 | Registro de objetivos de navegación `[CODEX]` | Codex | `packages/ui/tests/nav-registry.test.tsx` pasa (integration) | — |
| T-00-017 | Catálogo de componentes y control de accesibilidad en CI `[CODEX]` | Codex | `packages/ui/tests/a11y-ci.test.ts` pasa | — |

**Puerta de salida:** CI en verde con todas las auditorías; autenticación sin contraseña funcionando; componentes base con axe-core y la regla de 44×44 px. Además: existen `design-system/coalsense-dispatch/MASTER.md` y `PRODUCT.md`. Revisión adversarial: autenticación, sesiones y logs.

## H1 — Control sin manos (spec 01)

Objetivo: que una persona controle el PC con voz y con cabeza y gestos, y que Alto y Deshacer siempre funcionen. Patrones de Gameface y Talon en `docs/REFERENCIAS.md`.

Riesgo a resolver primero: la latencia de la voz en hardware real. T-01-021 y T-01-022 van antes que el resto de la voz, con un benchmark temprano de T-01-047, y el motor se decide con datos (PA-10).

| Tarea | Sub-hito | Título | Ejecuta | Aceptación | Riesgos |
| --- | --- | --- | --- | --- | --- |
| T-01-001 | H1a | Esquema JSON de intenciones y del perfil `[CODEX]` | Codex | `packages/intents/tests/test_schema.py` pasa (contract) | — |
| T-01-002 | H1a | Generación de tipos y chequeo de deriva `[CODEX]` | Codex | `tools/audit/tests/test_schema_drift.py` pasa (contract) | — |
| T-01-003 | H1a | Núcleo del bus: validación, prioridades y coalescencia | Sonnet | `apps/companion/tests/bus/test_core.py` pasa (unit, con pruebas de propiedades) | — |
| T-01-013 | H1a | Esquema, invariantes y validación del perfil | Sonnet | `apps/companion/tests/profile/test_validate.py` pasa (unit) | — |
| T-01-018 | H1b | Intérprete de archivos de comandos | Sonnet | `apps/companion/tests/commands/test_loader.py` pasa (unit) | — |
| T-01-044 | H1e | Auditoría: sin biometría, sin inferencia y sin GPL `[CODEX]` | Codex | `tools/audit/tests/test_audit_no_biometrics.py` pasa (audit) | — |
| T-01-004 | H1a | Autenticación de adaptadores y origen del actor | Sonnet + revisión Opus | `apps/companion/tests/bus/test_auth.py` pasa (security) | Adversarial Codex: Autenticación y datos sensibles. |
| T-01-005 | H1a | Validación de aprobaciones y umbral de confianza | Sonnet + revisión Opus | `apps/companion/tests/bus/test_approval_guard.py` pasa (replay y unit) | Adversarial Codex: Motor de políticas. |
| T-01-006 | H1a | Registro local de intenciones en la bitácora | Sonnet | `apps/companion/tests/bus/test_audit_log.py` pasa (integration) | — |
| T-01-007 | H1a | Arnés de reproducción y manifiesto de fixtures `[CODEX]` | Codex | `apps/companion/tests/replay/test_harness.py` pasa (replay) | — |
| T-01-009 | H1a | StopGuard y detención local | Sonnet + revisión Opus | `apps/companion/tests/bus/test_stop_guard.py` pasa (integration, propiedades) | Adversarial Codex: Alto y Deshacer. |
| T-01-010 | H1a | Pila de deshacer y clases de actuación | Sonnet + revisión Opus | `apps/companion/tests/actuator/test_undo.py` pasa (unit) | Adversarial Codex: Alto y Deshacer. |
| T-01-012 | H1a | Ayuda humana hacia la spec 05 | Sonnet + revisión Opus | `apps/companion/tests/bus/test_help_route.py` pasa (integration, red deshabilitada) | Adversarial Codex: Ruta de crisis. |
| T-01-014 | H1a | Almacenamiento cifrado y migraciones del perfil | Sonnet + revisión Opus | `apps/companion/tests/profile/test_store.py` pasa (security y unit) | Adversarial Codex: Autenticación y datos sensibles. |
| T-01-019 | H1b | Conjunto base de comandos en español y licencias | Sonnet | `apps/companion/tests/commands/test_base_coverage.py` pasa (unit y audit) | — |
| T-01-031 | H1c | Modo web de visión | Sonnet | `apps/web/tests/e2e/vision-web.spec.ts` pasa | — |
| T-01-043 | H1e | Política de egreso y prueba de red del companion | Sonnet + revisión Opus | `apps/companion/tests/privacy/test_egress.py` pasa (security) | Adversarial Codex: Cámara y micrófono. |
| T-01-055 | H1f | Inventario de datos de la capa de entrada | Sonnet | `tools/audit/tests/test_audit_data_inventory.py` pasa (audit) | — |
| T-01-008 | H1a | Generador de fixtures sintéticas `[CODEX]` | Codex | `apps/companion/tests/fixtures/test_fixtures_valid.py` pasa (audit) | Fixtures sintéticas primero; reales solo con consentimiento (REQ-01-100). |
| T-01-011 | H1a | Estado `stop_reachable`, latido y salud | Sonnet + revisión Opus | `apps/companion/tests/bus/test_stop_state.py` pasa (integration con fallos inyectados) | Adversarial Codex: Alto y Deshacer. |
| T-01-015 | H1f | Perfiles múltiples, exportación y borrado local | Sonnet + revisión Opus | `apps/companion/tests/profile/test_multi_export_erase.py` pasa | Adversarial Codex: Autenticación y datos sensibles. |
| T-01-016 | H1f | Edición por cuidador/a, propuestas y no salida del perfil | Sonnet + revisión Opus | `apps/companion/tests/profile/test_proposals_egress.py` pasa (security) | Adversarial Codex: Permisos del cuidador/a. |
| T-01-017 | H1f | Visor del perfil en lenguaje llano `[UI]` | Sonnet | `apps/web/tests/e2e/profile-view.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |
| T-01-020 | H1b | Adaptador de voz: captura, modos y sueño | Sonnet + revisión Opus | `apps/companion/tests/adapters/voice/test_modes.py` pasa (replay) | Adversarial Codex: Cámara y micrófono. Motor de voz sin medir en hardware real (PA-10). |
| T-01-025 | H1b | Ayuda de comandos y eco de lo entendido `[UI]` | Sonnet | `apps/web/tests/e2e/voice-help.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |
| T-01-027 | H1c | Captura de cámara y canalización MediaPipe en memoria | Sonnet + revisión Opus | `apps/companion/tests/adapters/head_gesture/test_pipeline.py` pasa (security y replay) | Adversarial Codex: Cámara y micrófono. Licencia y peso del modelo MediaPipe [verificar]; ningún frame a disco ni red. |
| T-01-032 | H1d | Adaptador de teclado y mouse con atajos globales | Sonnet | `apps/companion/tests/adapters/keyboard_mouse/test_adapter.py` pasa (unit, integration y security) | — |
| T-01-033 | H1d | Actuador Windows: puntero, teclas y texto | Sonnet | `apps/companion/tests/actuator/test_actuator.py` pasa (integration y security) | Windows bloquea la inyección en apps elevadas (UIPI) [verificar]. Ver Review Focus 5. |
| T-01-046 | H1e | Controles persistentes de Alto y Deshacer en el companion `[UI]` | Sonnet + revisión Opus | `apps/web/tests/e2e/stop-undo-bar.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Adversarial Codex: Alto y Deshacer. Skill de diseño contra `accessibility.md`. |
| T-01-056 | H1f | Enlace al orquestador con TLS | Sonnet + revisión Opus | `apps/companion/tests/uplink/test_tls.py` pasa (security) | Adversarial Codex: Cámara y micrófono. |
| T-01-021 | H1b | Detector de palabras de control | Sonnet | `apps/companion/tests/adapters/voice/test_control_words.py` pasa (replay) | Un Alto perdido es inaceptable; un falso Alto es aceptable (D-13). Ver Review Focus 1. |
| T-01-022 | H1b | Reconocedor de comandos con ambigüedad | Sonnet | `apps/companion/tests/adapters/voice/test_ambiguity.py` pasa (replay) | — |
| T-01-023 | H1b | Dictado: transcripción, formato y corrección | Sonnet | `apps/companion/tests/adapters/voice/test_dictation.py` pasa (replay y security) | Rendimiento de faster-whisper en CPU de 8 GB [verificar]. |
| T-01-026 | H1b | Reconocimiento de voz en la nube, opcional y con consentimiento | Sonnet + revisión Opus | `apps/companion/tests/cloud/test_stt_cloud.py` pasa | Adversarial Codex: Cámara y micrófono. |
| T-01-028 | H1c | Cabeza → puntero, compensación de ángulo y «centrar» | Sonnet | `apps/companion/tests/adapters/head_gesture/test_pointer.py` pasa (replay) | Patrón Gameface: fork propio con atribución en THIRD_PARTY.md. |
| T-01-029 | H1c | Motor de gestos y vínculos | Sonnet | `apps/companion/tests/adapters/head_gesture/test_gestures.py` pasa (replay y unit) | — |
| T-01-034 | H1d | Números en pantalla con UI Automation `[UI]` | Sonnet | `apps/companion/tests/actuator/test_numbers.py` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. La cobertura de UI Automation varía por aplicación. |
| T-01-035 | H1d | Cuadrícula, imán y vía sin puntería | Sonnet | `apps/companion/tests/actuator/test_grid_snapping.py` pasa | — |
| T-01-036 | H1d | Retroalimentación multicanal | Sonnet | `apps/companion/tests/feedback/test_feedback.py` pasa | — |
| T-01-037 | H1e | Detección de dispositivos y permisos | Sonnet + revisión Opus | `apps/companion/tests/calibration/test_devices.py` pasa | Adversarial Codex: Cámara y micrófono. |
| T-01-042 | H1e | Indicadores y apagado total `[UI]` | Sonnet + revisión Opus | `apps/companion/tests/privacy/test_indicators.py` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Adversarial Codex: Cámara y micrófono. Skill de diseño contra `accessibility.md`. |
| T-01-045 | H1e | Panel de modalidades y estados de pantalla `[UI]` | Sonnet | `apps/web/tests/e2e/modalities-states.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |
| T-01-054 | H1f | Resiliencia y uso sin conexión | Sonnet | `apps/companion/tests/integration/test_resilience_offline.py` pasa (integration) | — |
| T-01-024 | H1b | Inserción de dictado deshacible y micrófono desconectado | Sonnet | `apps/companion/tests/adapters/voice/test_insert.py` pasa (integration) | — |
| T-01-030 | H1c | Pérdida de rostro, varios rostros, calidad y pausa | Sonnet | `apps/companion/tests/adapters/head_gesture/test_presence.py` pasa (replay) | — |
| T-01-038 | H1e | Cálculo de umbrales, separabilidad y descarte de muestras `[CODEX]` | Codex | `apps/companion/tests/calibration/test_thresholds.py` pasa (replay y security) | — |
| T-01-039 | H1e | Calibración de cabeza y de voz | Sonnet | `apps/companion/tests/calibration/test_head_voice.py` pasa (replay) | — |
| T-01-047 | H1g | Arnés de rendimiento y presupuestos `[CODEX]` | Codex | `apps/companion/tests/perf/test_budgets.py` pasa (perf) | Presupuestos [SUPUESTO] hasta medir en hardware real. |
| T-01-049 | H1g | Fiabilidad: reposo, estrés y falsas aprobaciones | Sonnet | `apps/companion/tests/reliability/test_rest_stress.py` pasa (replay) | Ver Review Focus 2 (modalidades contradictorias). |
| T-01-040 | H1e | Asistente de calibración con zona de práctica `[UI]` | Sonnet | `apps/web/tests/e2e/calibration.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |
| T-01-041 | H1e | Deriva y recalibración rápida | Sonnet | `apps/companion/tests/calibration/test_drift.py` pasa | — |
| T-01-048 | H1g | Pruebas de accesibilidad de las pantallas de 01 | Sonnet | `apps/web/tests/a11y/input-layer.spec.ts` pasa | — |

**Puerta de salida:** con fixtures, la propiedad «Alto siempre detiene» pasa; ningún cuadro, audio ni landmark sale del dispositivo (captura de red); una calibración completa produce un perfil guardado con Alto y Deshacer practicados. Revisión adversarial: Alto y Deshacer, cámara y micrófono, perfil cifrado.

## H2 — Orquestador seguro (spec 02 y núcleo de la spec 05)

Objetivo: que ninguna acción con efecto externo ocurra sin aprobación, y que la crisis llegue siempre a una persona.

Antes de T-02-002 va **P-03**: `infra/docker-compose.dev.yml` con PostgreSQL + pgvector y Redis, solo para desarrollo y pruebas (la prueba de seguridad por filas lo necesita y ninguna tarea lo crea antes de T-09-008). Sonnet. Aceptación: `docker compose -f infra/docker-compose.dev.yml up -d` levanta ambos con su comprobación de salud; credenciales desde `.env`, con `.env.example` sin secretos; imágenes con versión fijada.

| Tarea | Título | Ejecuta | Aceptación | Riesgos |
| --- | --- | --- | --- | --- |
| T-05-001 | Paquete de seguridad: formato de reglas y control de revisión `[CODEX]` | Codex + revisión Opus | `tools/audit/tests/test_audit_safety_review.py` pasa (audit) | Adversarial Codex: Ruta de crisis. |
| T-02-002 | Servicio de persistencia y aislamiento por persona | Sonnet + revisión Opus | `apps/orchestrator/tests/persistence/test_rls.py` pasa (security) | Adversarial Codex: Autenticación y datos sensibles. La prueba RLS necesita PostgreSQL local: P-03 va justo antes. |
| T-02-006 | Manifiesto de herramientas y registro `[CODEX]` | Codex | `apps/orchestrator/tests/gateway/test_manifest.py` pasa (contract y unit) | — |
| T-02-017 | Auditoría de límites del gateway y de credenciales `[CODEX]` | Codex + revisión Opus | `tools/audit/tests/test_gateway_boundaries.py` pasa (audit) | Adversarial Codex: Autenticación y datos sensibles. |
| T-05-002 | Reglas de crisis en español de Ecuador y corpus sintético | Sonnet + revisión Opus | `packages/safety/python/tests/test_rules_corpus.py` pasa (replay) | Adversarial Codex: Ruta de crisis. Reglas y mensajes requieren revisión de un profesional antes del piloto (SF-06). |
| T-05-006 | Configuración de rutas humanas y aviso sin rutas | Sonnet + revisión Opus | `packages/safety/python/tests/test_routes.py` pasa (unit y audit) | Adversarial Codex: Ruta de crisis. La línea oficial es dato de configuración (C-06). |
| T-05-010 | Filtro de salida, suplantación y palabras prohibidas | Sonnet + revisión Opus | `packages/safety/python/tests/test_output_filter.py` pasa (security) | Adversarial Codex: Ruta de crisis. |
| T-02-003 | Bitácora de solo agregado con cadena de hash | Sonnet + revisión Opus | `apps/orchestrator/tests/audit/test_chain.py` pasa (unit y security) | Adversarial Codex: Autenticación y datos sensibles. |
| T-02-008 | Constructor de prompts con lista permitida y consentimiento | Sonnet + revisión Opus | `apps/orchestrator/tests/agents/test_prompt_builder.py` pasa (security) | Adversarial Codex: Autenticación y datos sensibles. |
| T-02-001 | API base, contrato versionado y límites | Sonnet | `apps/orchestrator/tests/api/test_api_base.py` pasa (contract y unit) | — |
| T-02-004 | Fusión de la bitácora local y permisos de lectura | Sonnet | `apps/orchestrator/tests/audit/test_merge_read.py` pasa (integration y security) | — |
| T-02-007 | Gateway: ejecución con verificación de sello e idempotencia | Sonnet | `apps/orchestrator/tests/gateway/test_executor.py` pasa (security) | — |
| T-02-010 | Motor de políticas núcleo | Sonnet + revisión Opus | `apps/orchestrator/tests/policy/test_engine.py` pasa (unit y security) | Adversarial Codex: Motor de políticas. |
| T-05-003 | Reglas antes de modelos y memoria; sin inferencia de ánimo | Sonnet + revisión Opus | `apps/orchestrator/tests/safety/test_crisis_gate.py` pasa (security) | Adversarial Codex: Ruta de crisis. |
| T-05-011 | Registro de consentimientos y consulta `consent.check` | Sonnet + revisión Opus | `apps/orchestrator/tests/consent/test_consent.py` pasa (unit y security) | Adversarial Codex: Ruta de crisis. |
| T-02-009 | Herramienta `llm.complete`, enrutador y presupuesto | Sonnet | `apps/orchestrator/tests/agents/test_router.py` pasa (unit e integration con proveedores simulados) | Contenido al proveedor solo con consentimiento (C-01); nunca el perfil (SP-6). |
| T-02-011 | Solicitud de aprobación y sello | Sonnet + revisión Opus | `apps/orchestrator/tests/policy/test_grant.py` pasa (unit y security) | Adversarial Codex: Motor de políticas. |
| T-02-013 | Niveles de autonomía en las políticas | Sonnet + revisión Opus | `apps/orchestrator/tests/policy/test_autonomy.py` pasa (unit y propiedades) | Adversarial Codex: Motor de políticas. |
| T-02-016 | Agentes: base, lista permitida, aislamiento, propuestas y puntos de control | Sonnet | `apps/orchestrator/tests/agents/test_agents.py` pasa (unit e integration) | — |
| T-02-019 | Deshacer con compensación | Sonnet + revisión Opus | `apps/orchestrator/tests/gateway/test_undo.py` pasa (unit) | Adversarial Codex: Alto y Deshacer. |
| T-02-020 | Bloqueo por `stop_reachable` | Sonnet + revisión Opus | `apps/orchestrator/tests/policy/test_stop_gate.py` pasa (integration) | Adversarial Codex: Alto y Deshacer. |
| T-05-012 | Pantalla de consentimientos `[UI]` | Sonnet + revisión Opus | `apps/web/tests/e2e/consent.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Adversarial Codex: Ruta de crisis. Skill de diseño contra `accessibility.md`. |
| T-02-012 | Origen y delegaciones en las aprobaciones | Sonnet + revisión Opus | `apps/orchestrator/tests/policy/test_origin.py` pasa (security) | Adversarial Codex: Permisos del cuidador/a. |
| T-02-014 | Retención y despacho | Sonnet + revisión Opus | `apps/orchestrator/tests/policy/test_hold.py` pasa (integration) | Adversarial Codex: Motor de políticas. Ver Review Focus 3 (caída durante la retención). |
| T-02-015 | Planificador con plan editable | Sonnet | `apps/orchestrator/tests/agents/test_planner.py` pasa (integration y unit) | — |
| T-02-018 | Alto en el orquestador | Sonnet + revisión Opus | `apps/orchestrator/tests/agents/test_halt.py` pasa (integration y perf) | Adversarial Codex: Alto y Deshacer. |
| T-05-009 | Límites de la IA: peticiones de consejo | Sonnet + revisión Opus | `packages/safety/python/tests/test_advice_gate.py` pasa | Adversarial Codex: Ruta de crisis. |
| T-05-004 | Orquestador de derivación en el cliente | Sonnet + revisión Opus | `packages/safety/python/tests/test_derivation.py` pasa (integration, red deshabilitada) | Adversarial Codex: Ruta de crisis. |
| T-05-007 | Contacto de confianza: alta, prueba, modos y aviso mínimo | Sonnet + revisión Opus | `apps/orchestrator/tests/safety/test_trusted_contact.py` pasa | Adversarial Codex: Ruta de crisis. Canal: correo primero (PA-19). |

**Puerta de salida:** sin sello válido la herramienta externa se rechaza; un sello solo sirve para su contenido y una vez; Alto cancela durante la retención; un corpus de crisis llega al 100% a la ruta humana sin red y sin modelo; el constructor de prompts rechaza el perfil y la condición declarada. Revisión adversarial obligatoria: motor de políticas, Alto en el orquestador, persistencia, prompts y ruta de crisis.

## H3 — Primera tarea de la sesión 1 (spec 03 y correo de la spec 04)

Antes de empezar: elegir el proveedor de correo (PA-15).

| Tarea | Título | Ejecuta | Aceptación | Riesgos |
| --- | --- | --- | --- | --- |
| T-04-005 | Conexión de la cuenta de correo (OAuth) y fallos de conexión | Sonnet + revisión Opus | `apps/orchestrator/tests/workspace/test_connection.py` pasa | Adversarial Codex: Autenticación y datos sensibles. Proveedor de correo por elegir antes de este hito (PA-15). |
| T-03-001 | Modelo de tareas, micro-pasos y máquina de estados | Sonnet | `apps/orchestrator/tests/tasks/test_state_machine.py` pasa (unit y propiedades) | — |
| T-04-001 | Modelo de bloques y edición por número | Sonnet | `apps/orchestrator/tests/workspace/test_blocks_edit.py` pasa (unit) | — |
| T-03-002 | API de tareas y catálogo de tipos | Sonnet | `apps/orchestrator/tests/tasks/test_api.py` pasa (integration) | — |
| T-03-004 | Plan, estado y control de la tarea `[UI]` | Sonnet | `apps/web/tests/e2e/task-flow.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |
| T-03-005 | Servicio de aprobación en el ciclo | Sonnet + revisión Opus | `apps/orchestrator/tests/tasks/test_approvals.py` pasa (unit e integration) | Adversarial Codex: Motor de políticas. |
| T-03-011 | Logros: registro, ocultar, exportar y borrar | Sonnet | `apps/orchestrator/tests/achievements/test_achievements.py` pasa (integration y security) | — |
| T-04-002 | Editor accesible de bloques numerados `[UI]` | Sonnet | `apps/web/tests/e2e/block-editor.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |
| T-04-003 | Versiones y conservación de borradores | Sonnet | `apps/orchestrator/tests/workspace/test_versions.py` pasa (unit e integration) | — |
| T-03-003 | Pantalla para elegir tarea `[UI]` | Sonnet | `apps/web/tests/e2e/choose-task.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |
| T-03-006 | Tarjeta de aprobación integrada y lista de pendientes `[UI]` | Sonnet | `apps/web/tests/e2e/approval-card.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |
| T-04-004 | Agente de correo y borradores | Sonnet | `apps/orchestrator/tests/workspace/test_email_agent.py` pasa (unit e integration con modelo simulado) | — |
| T-05-005 | Pantalla de derivación `[UI]` | Sonnet + revisión Opus | `apps/web/tests/e2e/derivation.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Adversarial Codex: Ruta de crisis. Skill de diseño contra `accessibility.md`. |
| T-05-008 | Registro de derivaciones y cuidado de datos | Sonnet + revisión Opus | `apps/orchestrator/tests/safety/test_events.py` pasa (security) | Adversarial Codex: Ruta de crisis. |
| T-03-007 | Retención visible y resultado del despacho `[UI]` | Sonnet + revisión Opus | `apps/web/tests/e2e/hold-dispatch.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Adversarial Codex: Alto y Deshacer. Skill de diseño contra `accessibility.md`. |
| T-03-015 | Primera tarea de la sesión 1 | Sonnet | `apps/web/tests/e2e/first-task.spec.ts` pasa | — |
| T-04-006 | Envío de correo con aprobación | Sonnet | `apps/orchestrator/tests/workspace/test_email_send.py` pasa | — |

**Puerta de salida:** una persona de ejemplo con voz y cabeza completa la calibración y la primera tarea (correo a sí misma con aprobación) y ve su primer logro (REQ-03-040 a REQ-03-044), verificado con Playwright solo con intenciones simuladas. Revisión adversarial: aprobación en el ciclo y OAuth del correo.

## H4 — Las tres tareas y herramientas ampliables

Antes de empezar: elegir las redes para la publicación (PA-17).

| Tarea | Título | Ejecuta | Aceptación | Riesgos |
| --- | --- | --- | --- | --- |
| T-02-025 | Memoria por persona | Sonnet | `apps/orchestrator/tests/memory/test_memory.py` pasa | — |
| T-02-021 | n8n opcional detrás del gateway `[CODEX]` | Codex | `apps/orchestrator/tests/gateway/test_n8n.py` pasa (audit y integration) | n8n no se activa en producción sin aval de abogado (PA-09). |
| T-02-022 | MCP: registro, catálogo curado y habilitación por la persona | Sonnet | `apps/orchestrator/tests/gateway/test_mcp_enablement.py` pasa | Salidas de servidores MCP de terceros son no confiables. |
| T-02-023 | MCP: aislamiento y salidas no confiables | Sonnet + revisión Opus | `apps/orchestrator/tests/gateway/test_mcp_security.py` pasa (security) | Adversarial Codex: Autenticación y datos sensibles. |
| T-03-009 | Dial de autonomía: configuración y reglas | Sonnet + revisión Opus | `apps/orchestrator/tests/tasks/test_autonomy_settings.py` pasa (unit) | Adversarial Codex: Motor de políticas. |
| T-04-007 | Agente de documento: notas dictadas a documento | Sonnet | `apps/orchestrator/tests/workspace/test_document_agent.py` pasa | — |
| T-04-009 | Agente de publicación: texto, límites y texto alternativo | Sonnet | `apps/orchestrator/tests/workspace/test_social_agent.py` pasa (unit) | Redes concretas por elegir (PA-17); sin publicación automática. |
| T-04-011 | Catálogo de herramientas conectadas `[UI]` | Sonnet | `apps/web/tests/e2e/tool-catalog.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |
| T-02-024 | Conjunto de pruebas de inyección de prompts `[CODEX]` | Codex + revisión Opus | `apps/orchestrator/tests/security/test_prompt_injection.py` pasa (security) | Adversarial Codex: Autenticación y datos sensibles. |
| T-03-010 | Pantalla del dial de autonomía `[UI]` | Sonnet | `apps/web/tests/e2e/autonomy-dial.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |
| T-03-012 | Logros y progreso sin rachas `[UI]` | Sonnet | `apps/web/tests/e2e/achievements.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |
| T-03-013 | Siguiente tarea propuesta | Sonnet | `apps/orchestrator/tests/tasks/test_next_task.py` pasa (unit) | — |
| T-03-014 | Métrica norte agregada con consentimiento | Sonnet | `apps/orchestrator/tests/achievements/test_metrics.py` pasa (security) | — |
| T-04-008 | Guardar, exportar y compartir documentos | Sonnet | `apps/orchestrator/tests/workspace/test_doc_tools.py` pasa (unit y security) | — |
| T-04-010 | Publicación: datos de terceros, copiar y regla de publicar | Sonnet | `apps/orchestrator/tests/workspace/test_social_extras.py` pasa (unit) | — |
| T-04-012 | Estados de pantalla del editor y del catálogo `[UI]` | Sonnet | `apps/web/tests/e2e/workspace-states.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |

**Puerta de salida:** las tres tareas funcionan de punta a punta con aprobación; habilitar una herramienta MCP exige la aprobación de la persona; el conjunto de inyección de prompts pasa. Revisión adversarial: MCP e inyección.

## H5 — Cuidador/a, privacidad y despliegue

| Tarea | Título | Ejecuta | Aceptación | Riesgos |
| --- | --- | --- | --- | --- |
| T-04-016 | Auditoría de lenguaje de consejo `[CODEX]` | Codex | `tools/audit/tests/test_copy_workspace.py` pasa (audit) | — |
| T-07-001 | Inventario de datos, clasificación y registro de tratamiento | Sonnet + revisión Opus | `tools/audit/tests/test_audit_data_inventory_full.py` pasa (audit) | Adversarial Codex: Autenticación y datos sensibles. |
| T-07-006 | TLS entre clientes y servicios `[CODEX]` | Codex + revisión Opus | `apps/orchestrator/tests/privacy/test_tls_everywhere.py` pasa (security) | Adversarial Codex: Autenticación y datos sensibles. |
| T-07-002 | Sin diagnóstico y retención cero | Sonnet + revisión Opus | `apps/orchestrator/tests/privacy/test_zero_retention.py` pasa (security) | Adversarial Codex: Autenticación y datos sensibles. |
| T-07-003 | Servicio de claves y cifrado de aplicación | Sonnet + revisión Opus | `apps/orchestrator/tests/privacy/test_crypto.py` pasa (security e integration) | Adversarial Codex: Autenticación y datos sensibles. KMS administrado (PA-20); hosting sin decidir (PA-18). |
| T-07-013 | Retención por categoría | Sonnet + revisión Opus | `apps/orchestrator/tests/privacy/test_retention.py` pasa | Adversarial Codex: Autenticación y datos sensibles. |
| T-09-008 | Backend en contenedores, migraciones y salud | Sonnet | `apps/orchestrator/tests/infra/test_compose.py` pasa (integration y security) | — |
| T-06-001 | Modelo de datos de cuidadores, invitaciones y delegaciones | Sonnet + revisión Opus | `apps/orchestrator/tests/caregivers/test_models_signing.py` pasa (contract y security) | Adversarial Codex: Permisos del cuidador/a. |
| T-07-004 | Registro y alertas del uso de claves | Sonnet + revisión Opus | `apps/orchestrator/tests/privacy/test_key_audit.py` pasa (integration) | Adversarial Codex: Autenticación y datos sensibles. |
| T-07-005 | Cifrado local del companion | Sonnet + revisión Opus | `apps/companion/tests/profile/test_local_encryption_audit.py` pasa (security) | Adversarial Codex: Autenticación y datos sensibles. |
| T-07-014 | Acceso del operador y roles de base de datos | Sonnet + revisión Opus | `apps/orchestrator/tests/privacy/test_operator_access.py` pasa (security) | Adversarial Codex: Autenticación y datos sensibles. |
| T-07-015 | Incidentes de seguridad e identificación de afectados | Sonnet + revisión Opus | `apps/orchestrator/tests/privacy/test_incident_scope.py` pasa (integration) | Adversarial Codex: Autenticación y datos sensibles. |
| T-09-007 | PWA con política de contenido estricta | Sonnet | `apps/web/tests/e2e/pwa-security.spec.ts` pasa | — |
| T-09-010 | Entornos de prueba y producción | Sonnet | `tools/audit/tests/test_audit_envs.py` pasa (audit) | Hosting y región sin decidir (PA-18). |
| T-09-014 | Copias de seguridad cifradas y restauración | Sonnet + revisión Opus | `apps/orchestrator/tests/infra/test_backup_restore.py` pasa (integration y security) | Adversarial Codex: Autenticación y datos sensibles. |
| T-02-005 | Pantalla de la bitácora en lenguaje llano `[UI]` | Sonnet | `apps/web/tests/e2e/audit-log.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |
| T-06-002 | Invitación, cuenta del cuidador/a y reglas de invitación | Sonnet + revisión Opus | `apps/orchestrator/tests/caregivers/test_invitations.py` pasa (unit y security) | Adversarial Codex: Permisos del cuidador/a. |
| T-06-003 | Creación y consulta de delegaciones | Sonnet + revisión Opus | `apps/orchestrator/tests/caregivers/test_delegations.py` pasa (security y contract) | Adversarial Codex: Permisos del cuidador/a. |
| T-06-005 | Registro de actividad de acompañantes | Sonnet + revisión Opus | `apps/orchestrator/tests/caregivers/test_activity.py` pasa (security) | Adversarial Codex: Permisos del cuidador/a. |
| T-07-007 | Capa de salida a terceros con campos prohibidos | Sonnet + revisión Opus | `apps/orchestrator/tests/privacy/test_egress_layer.py` pasa (security) | Adversarial Codex: Autenticación y datos sensibles. |
| T-09-012 | Indicadores de función `[CODEX]` | Codex | `packages/common-py/tests/test_flags.py` pasa (unit) | — |
| T-02-026 | Modos degradados | Sonnet | `apps/orchestrator/tests/api/test_degraded.py` pasa | — |
| T-02-027 | Métricas operativas sin contenido y retención cero de prompts | Sonnet + revisión Opus | `apps/orchestrator/tests/observability/test_metrics.py` pasa (security e integration) | Adversarial Codex: Autenticación y datos sensibles. |
| T-06-006 | Control por alcance en la API | Sonnet + revisión Opus | `apps/orchestrator/tests/caregivers/test_scope_guard.py` pasa (security) | Adversarial Codex: Permisos del cuidador/a. |
| T-06-010 | Versiones de perfil pendientes y cuenta de la persona | Sonnet + revisión Opus | `apps/orchestrator/tests/caregivers/test_profile_versions.py` pasa (unit y security) | Adversarial Codex: Permisos del cuidador/a. |
| T-07-008 | Registro de terceros y política con proveedores | Sonnet + revisión Opus | `apps/orchestrator/tests/privacy/test_third_parties.py` pasa (unit y audit) | Adversarial Codex: Autenticación y datos sensibles. |
| T-09-001 | Empaquetado e instalador firmado del companion | Sonnet | `apps/companion/tests/packaging/test_installer.py` pasa (integration y security) | Certificado de firma de código: costo y trámite [verificar]. |
| T-03-017 | Recuperación tras una caída del servicio `[CODEX]` | Codex | `apps/orchestrator/tests/tasks/test_recovery.py` pasa (integration) | — |
| T-06-004 | Revocación inmediata y rechazo sin delegación | Sonnet + revisión Opus | `apps/orchestrator/tests/caregivers/test_revocation.py` pasa (integration, security y perf) | Adversarial Codex: Permisos del cuidador/a. |
| T-06-011 | Vista de perfiles y versión pendiente `[UI]` | Sonnet + revisión Opus | `apps/web/tests/e2e/pending-profile-version.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Adversarial Codex: Permisos del cuidador/a. Skill de diseño contra `accessibility.md`. |
| T-07-011 | Oposición, suspensión y derechos por cuidador/a | Sonnet + revisión Opus | `apps/orchestrator/tests/privacy/test_objection.py` pasa (integration y security) | Adversarial Codex: Autenticación y datos sensibles. |
| T-09-002 | Modelos con integridad verificada y uso sin conexión | Sonnet | `apps/companion/tests/packaging/test_models.py` pasa (security e integration) | — |
| T-09-003 | Asistente de permisos y primer arranque `[UI]` | Sonnet | `apps/web/tests/e2e/install-wizard.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Skill de diseño contra `accessibility.md`. |
| T-09-004 | Actualizaciones con aprobación y conservación de datos | Sonnet | `apps/companion/tests/update/test_update.py` pasa | — |
| T-09-005 | Desinstalación e inicio con Windows | Sonnet | `apps/companion/tests/packaging/test_uninstall_autostart.py` pasa | — |
| T-09-006 | Auditoría del egreso de red del artefacto `[CODEX]` | Codex + revisión Opus | `tools/audit/tests/test_packaged_egress.py` pasa (security) | Adversarial Codex: Cámara y micrófono. |
| T-09-013 | Observabilidad y alertas sin contenido | Sonnet | `apps/orchestrator/tests/infra/test_alerts.py` pasa (integration) | — |
| T-09-015 | Arranque del companion y disponibilidad `[CODEX]` | Codex | `apps/companion/tests/perf/test_startup.py` pasa (perf) | — |
| T-03-008 | Aprobación de cuidador/a visible a la persona | Sonnet + revisión Opus | `apps/web/tests/e2e/caregiver-notice.spec.ts` pasa | Adversarial Codex: Permisos del cuidador/a. |
| T-04-015 | Consentimiento y cifrado de entregables `[CODEX]` | Codex + revisión Opus | `apps/orchestrator/tests/workspace/test_consent_encryption.py` pasa (security) | Adversarial Codex: Autenticación y datos sensibles. |
| T-06-007 | Pantallas de la persona sobre sus cuidadores/as `[UI]` | Sonnet + revisión Opus | `apps/web/tests/e2e/my-caregivers.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Adversarial Codex: Permisos del cuidador/a. Skill de diseño contra `accessibility.md`. |
| T-06-009 | Calibración asistida con origen de cuidador/a | Sonnet + revisión Opus | `apps/companion/tests/calibration/test_assisted.py` pasa (integration) | Adversarial Codex: Permisos del cuidador/a. |
| T-07-009 | Acceso, exportación y rectificación | Sonnet + revisión Opus | `apps/orchestrator/tests/privacy/test_export.py` pasa | Adversarial Codex: Autenticación y datos sensibles. |
| T-07-010 | Borrado criptográfico reanudable | Sonnet + revisión Opus | `apps/orchestrator/tests/privacy/test_erase.py` pasa | Adversarial Codex: Autenticación y datos sensibles. |
| T-09-009 | Servidores MCP en contenedores aislados | Sonnet | `apps/orchestrator/tests/infra/test_mcp_isolation.py` pasa (security) | — |
| T-09-011 | Pipeline de entrega, promoción y reversión | Sonnet | `tools/audit/tests/test_release_gate.py` pasa (audit) | — |
| T-04-014 | Rendimiento del primer borrador `[CODEX]` | Codex | `apps/orchestrator/tests/perf/test_first_draft.py` pasa (perf) | — |
| T-05-013 | Prueba de extremo a extremo de la derivación y rendimiento `[CODEX]` | Codex + revisión Opus | `apps/web/tests/e2e/crisis-end-to-end.spec.ts` pasa (perf) | Adversarial Codex: Ruta de crisis. |
| T-06-008 | Panel del cuidador/a `[UI]` | Sonnet + revisión Opus | `apps/web/tests/e2e/caregiver-panel.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Adversarial Codex: Permisos del cuidador/a. Skill de diseño contra `accessibility.md`. |
| T-07-012 | Pantalla de privacidad `[UI]` | Sonnet + revisión Opus | `apps/web/tests/e2e/privacy.spec.ts` pasa; axe-core sin violaciones AA y objetivos ≥ 44 px; Impeccable critique → audit → polish → harden | Adversarial Codex: Autenticación y datos sensibles. Skill de diseño contra `accessibility.md`. |
| T-04-013 | Accesibilidad de las pantallas de 04 `[CODEX]` | Codex | `apps/web/tests/a11y/workspace.spec.ts` pasa | — |
| T-06-012 | Accesibilidad y cifrado de 06 `[CODEX]` | Codex + revisión Opus | `apps/web/tests/a11y/caregivers.spec.ts` pasa (security) | Adversarial Codex: Permisos del cuidador/a. |

**Puerta de salida:** una persona borra todos sus datos y el contenido queda ilegible incluso en una copia restaurada; el cuidador/a no aprueba sin delegación vigente; el instalador firmado y el entorno de prueba funcionan; el empaquetado no abre destinos de red nuevos. Revisión adversarial obligatoria: permisos del cuidador/a, claves, borrado y acceso del operador. Además: `docs/guion-demo.md` y `docs/checklist-humano.md`.

## H6 — Cierre del MVP

Además de estas dos tareas, se vuelven a correr en el hardware real T-01-047, T-01-049, T-04-014, T-05-013 y T-09-015, y las suites de accesibilidad T-01-048, T-04-013 y T-06-012; T-00-006 en verde sobre todo `.kiro/specs/`.

| Tarea | Título | Ejecuta | Aceptación | Riesgos |
| --- | --- | --- | --- | --- |
| T-02-028 | Pruebas de rendimiento de plan y aprobación `[CODEX]` | Codex | `apps/orchestrator/tests/perf/test_latency.py` pasa (perf) | — |
| T-03-016 | Accesibilidad y textos de 03 `[CODEX]` | Codex | `apps/web/tests/a11y/control-cycle.spec.ts` pasa (audit) | — |

**Puerta de salida:** la definición de MVP terminado de `ORDEN-DE-CONSTRUCCION.md`, sección 3.

## Fuera del MVP

Spec 08 (mercado B2B, fase 2) y estas tareas `[POST-MVP]` de la spec 01:

| Tarea | Título |
| --- | --- |
| T-01-050 | Mirada con dwell: núcleo |
| T-01-051 | Mirada: indicadores y auditoría de licencias |
| T-01-052 | Switch con escaneo: núcleo |
| T-01-053 | Switch: escaneo con Alto primero y señales |
| T-01-057 | Comandos y alias propios |

## Lo que decides tú antes de cada hito

| Antes de | Decisión |
| --- | --- |
| H0 | Remoto de git (sin remoto, la CI de T-00-002 solo corre en local). |
| H3 | Proveedor de correo (PA-15). |
| H4 | Redes para la publicación (PA-17). |
| H2 | Canal de aviso al contacto de confianza (por defecto correo, PA-19). |
| H5 | Hosting y región (PA-18) y servicio de claves (PA-20), con el abogado. |
| Personas reales | Puerta SF-06: ruta humana probada, consentimiento revisado bajo LOPDP y mensajes de crisis revisados por un profesional. |
