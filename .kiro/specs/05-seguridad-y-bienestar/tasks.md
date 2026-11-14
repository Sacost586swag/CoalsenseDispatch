# Tareas: 05 Seguridad y bienestar

**Requisitos:** `requirements.md`. **Diseño:** `design.md`. **Producto:** `.kiro/steering/safety.md`. **Marcas:** `[CODEX]` paralelizable por Codex; `[UI]` interfaz.

**Contexto común (léelo una vez).**
- Paquete compartido `packages/safety/` (reglas, mensajes fijos, límites) con implementaciones en Python (`packages/safety/python/`) y TypeScript (`packages/safety/ts/`) que leen los mismos archivos versionados en `packages/safety/rules/`.
- La IA **no maneja la crisis**: la entrega a una persona. Mensajes **fijos**, no generados. Sin conversación, sin consejos. Funciona sin red y sin modelo.
- No se inventa ningún número de teléfono: las rutas humanas (contacto de confianza, línea de ayuda oficial, número de emergencias) son **datos de configuración**. Sin ninguna ruta configurada, el sistema muestra un aviso persistente y no debe ofrecerse a personas reales (SF-06).
- El texto que activa una señal de crisis **no se envía a ningún proveedor de modelo ni se guarda en la memoria**.
- Todos los consentimientos nacen **apagados**.

## Orden de dependencias

```
Ola 0 (spec 00, 02): T-00-009, T-00-015, T-02-003, T-02-008
Ola 1: T-05-001
Ola 2: T-05-002, T-05-006, T-05-009, T-05-011
Ola 3: T-05-003, T-05-004, T-05-007, T-05-010, T-05-012
Ola 4: T-05-005, T-05-008
Ola 5: T-05-013
```

---

### T-05-001 Paquete de seguridad: formato de reglas y control de revisión [CODEX]
- **Requisitos:** REQ-05-016
- **Depende de:** T-00-001
- **Archivos:** `packages/safety/python/coalsense_safety/{loader,model}.py`, `packages/safety/ts/src/{loader,model}.ts`, `packages/safety/rules/crisis.es-EC.yaml`, `packages/safety/messages/es-EC.yaml`, `tools/audit/audit_safety_review.py`, `tools/audit/tests/test_audit_safety_review.py`
- **Qué hacer:** formato versionado de reglas y mensajes con `version`, `reviewed_by` y `reviewed_at` obligatorios; cargadores en Python y TypeScript; auditoría de CI que falla si un archivo cambia sin actualizar la nota de revisión. Un valor `reviewed_by: pendiente` está permitido en desarrollo y el lanzamiento a personas reales lo exige completo (SF-06).
- **Prueba:** `tools/audit/tests/test_audit_safety_review.py` (audit): cambio sin nota falla; con nota pasa.
- **Terminado cuando:** la prueba pasa y ambos cargadores leen el mismo archivo.

### T-05-002 Reglas de crisis en español de Ecuador y corpus sintético
- **Requisitos:** REQ-05-001, REQ-05-017
- **Depende de:** T-05-001
- **Archivos:** `packages/safety/rules/crisis.es-EC.yaml`, `packages/safety/tests/corpus/crisis_explicit.yaml`, `packages/safety/tests/corpus/benign.yaml`, `packages/safety/python/tests/test_rules_corpus.py`, `packages/safety/ts/tests/rules-corpus.test.ts`
- **Qué hacer:** motor de reglas (frases y patrones explícitos, normalización de acentos y variantes de escritura) que evalúa un texto y devuelve si hay señal. Corpus sintético de frases explícitas y de frases benignas. Prueba de paridad: Python y TypeScript dan el mismo resultado sobre el corpus. Las reglas iniciales las redacta el desarrollador como borrador y quedan marcadas `reviewed_by: pendiente` hasta que las revise un profesional de salud mental.
- **Prueba:** `packages/safety/python/tests/test_rules_corpus.py` (replay): el 100% de las frases del corpus explícito activa; se miden los falsos positivos sin bloquear la CI; paridad con TypeScript.
- **Terminado cuando:** la prueba pasa en ambos lenguajes.

### T-05-003 Reglas antes de modelos y memoria; sin inferencia de ánimo
- **Requisitos:** REQ-05-002, REQ-05-015
- **Depende de:** T-05-002, T-02-008
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/agents/crisis_gate.py`, `apps/companion/src/coalsense_companion/safety/crisis_gate.py`, `apps/orchestrator/tests/safety/test_crisis_gate.py`, `tools/audit/tests/test_no_mood_inference.py`
- **Qué hacer:** puerta de crisis antes del constructor de prompts y de la memoria: si hay señal, descartar el texto (no va a ningún modelo ni a memoria) e iniciar la derivación. Auditoría que falla si el código contiene puntuación o clasificación de ánimo, depresión o riesgo a partir de cámara, voz, texto o patrones de uso.
- **Prueba:** `apps/orchestrator/tests/safety/test_crisis_gate.py` (security): un texto con señal no llega al proveedor simulado ni a la memoria; `tools/audit/tests/test_no_mood_inference.py` (audit).
- **Terminado cuando:** ambas pruebas pasan.

### T-05-004 Orquestador de derivación en el cliente
- **Requisitos:** REQ-05-003, REQ-05-004, REQ-05-006, REQ-05-007, REQ-05-051
- **Depende de:** T-05-002, T-01-012, T-02-018
- **Archivos:** `packages/safety/python/coalsense_safety/derivation.py`, `packages/safety/ts/src/derivation.ts`, `apps/orchestrator/src/coalsense_orchestrator/tasks/crisis_pause.py`, `packages/safety/python/tests/test_derivation.py`
- **Qué hacer:** al detectar una señal o recibir `help.request_human`, iniciar la derivación: pausar las acciones autónomas de la persona (tareas en estado detenido) [SUPUESTO], mostrar el mensaje fijo con las rutas configuradas desde el almacén local, y no conversar ni dar consejos. Funciona sin conexión, sin orquestador y sin modelo. Si hay red, avisar al orquestador para pausar.
- **Prueba:** `packages/safety/python/tests/test_derivation.py` (integration, red deshabilitada): cada elemento del corpus llega a la ruta humana; no se llama a ningún modelo; las tareas quedan detenidas cuando hay conexión.
- **Terminado cuando:** la prueba pasa.

### T-05-005 Pantalla de derivación [UI]
- **Requisitos:** REQ-05-005, REQ-05-012, REQ-05-045, REQ-05-052
- **Depende de:** T-05-004, T-00-015
- **Archivos:** `apps/web/src/features/safety/{DerivationScreen,RouteList}.tsx`, `apps/web/tests/e2e/derivation.spec.ts`
- **Qué hacer:** pantalla con el mensaje fijo y las rutas humanas, operable con cualquier modalidad, objetivos ≥ 44×44 px y sin límite de tiempo. Tras la derivación, la persona decide cuándo retomar; sin pantallas de castigo, pérdida ni reproche. Estados cargando (derivación sigue disponible), vacío (sin rutas: ofrecer configurarlas), error (si falla un aviso, ofrecer las demás rutas) y sin conexión (la derivación local sigue disponible).
- **Prueba:** `apps/web/tests/e2e/derivation.spec.ts` (e2e y a11y): flujo completo solo con intenciones simuladas; no hay temporizadores; axe-core sin violaciones.
- **Terminado cuando:** la prueba pasa.

### T-05-006 Configuración de rutas humanas y aviso sin rutas
- **Requisitos:** REQ-05-008, REQ-05-009
- **Depende de:** T-05-001, T-00-007
- **Archivos:** `packages/safety/python/coalsense_safety/routes.py`, `packages/safety/config/routes.example.yaml`, `apps/web/src/features/safety/NoRoutesNotice.tsx`, `tools/audit/audit_no_hardcoded_routes.py`, `packages/safety/python/tests/test_routes.py`
- **Qué hacer:** leer las rutas humanas de una configuración (contacto de confianza por persona; línea de ayuda oficial y número de emergencias del operador), sin ningún valor escrito en el código (auditoría que lo verifica). Si no hay ninguna ruta, mostrar un aviso persistente en la configuración y en el arranque indicando que el sistema no debe ofrecerse a personas reales hasta configurarla, y mostrar el número de emergencias por defecto [verificar] en la pantalla de crisis.
- **Prueba:** `packages/safety/python/tests/test_routes.py` (unit y audit): sin rutas aparece el aviso; ningún número aparece en el código.
- **Terminado cuando:** la prueba pasa.

### T-05-007 Contacto de confianza: alta, prueba, modos y aviso mínimo
- **Requisitos:** REQ-05-010, REQ-05-011, REQ-05-014
- **Depende de:** T-05-004, T-02-011
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/gateway/tools/notify_trusted_contact.py`, `apps/orchestrator/src/coalsense_orchestrator/policy/standing_authorization.py`, `apps/web/src/features/safety/TrustedContact.tsx`, `apps/orchestrator/tests/safety/test_trusted_contact.py`
- **Qué hacer:** la persona da de alta, prueba y revoca un contacto de confianza (la prueba se aprueba como acción externa). `notify.trusted_contact` es `external_effect`. Modo **preguntar** (por defecto): antes de avisar, mostrar «avisar» y «no avisar» del mismo tamaño y sin opción preseleccionada. Modo **automático**: solo si la persona lo eligió antes de forma explícita, con un sello de **autorización previa** atado a esa herramienta y a ese contacto, revocable y visible. El aviso usa una plantilla fija sin contenido de tareas. Sin red, el aviso queda en cola y se envía al volver solo si la persona lo pidió o lo había autorizado de forma automática.
- **Prueba:** `apps/orchestrator/tests/safety/test_trusted_contact.py` (security y e2e): sin autorización ni pregunta aprobada no se envía; en automático se envía con la plantilla mínima; revocar detiene los avisos.
- **Terminado cuando:** la prueba pasa.

### T-05-008 Registro de derivaciones y cuidado de datos
- **Requisitos:** REQ-05-013, REQ-05-053
- **Depende de:** T-05-004, T-02-003
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/safety/events.py`, `apps/orchestrator/migrations/0008_crisis_events.sql`, `apps/orchestrator/tests/safety/test_events.py`
- **Qué hacer:** registrar en la bitácora que hubo una derivación (fecha y ruta usada) **sin el contenido**, legible por la persona y no por el operador. Eventos de crisis y consentimientos cifrados con la clave de la persona y fuera del alcance del operador.
- **Prueba:** `apps/orchestrator/tests/safety/test_events.py` (security): el evento no contiene texto de la señal; el rol `operator` no puede leerlo.
- **Terminado cuando:** la prueba pasa.

### T-05-009 Límites de la IA: peticiones de consejo
- **Requisitos:** REQ-05-020
- **Depende de:** T-05-001, T-02-016
- **Archivos:** `packages/safety/python/coalsense_safety/advice_gate.py`, `packages/safety/rules/advice.es-EC.yaml`, `packages/safety/messages/limits.es-EC.yaml`, `packages/safety/python/tests/test_advice_gate.py`
- **Qué hacer:** clasificador por reglas de peticiones de consejo médico, psicológico, legal o financiero, aplicado antes de pasar la petición al agente. Si coincide, responde con el mensaje fijo de límites, explica qué sí puede hacer y ofrece una ruta humana, sin pasar la petición al agente.
- **Prueba:** `packages/safety/python/tests/test_advice_gate.py` (e2e): un conjunto de peticiones de muestra produce el mensaje fijo y ninguna llega al agente.
- **Terminado cuando:** la prueba pasa.

### T-05-010 Filtro de salida, suplantación y palabras prohibidas
- **Requisitos:** REQ-05-021, REQ-05-022, REQ-05-023, REQ-05-024
- **Depende de:** T-05-001, T-00-009
- **Archivos:** `packages/safety/python/coalsense_safety/output_filter.py`, `packages/safety/rules/forbidden_output.es-EC.yaml`, `packages/safety/python/tests/test_output_filter.py`, `tools/audit/tests/test_forbidden_words_ci.py`
- **Qué hacer:** filtro que revisa propuestas y textos generados con una lista de expresiones prohibidas (afirmaciones clínicas, promesas de efecto, suplantación de terapeuta) y las reemplaza o marca antes de mostrarlas. Los mensajes que la IA propone a terceros pueden identificarse como generados por IA con una opción configurable por la persona [SUPUESTO]. La CI rechaza palabras prohibidas en el catálogo de textos y mecanismos de manipulación (culpa, urgencia artificial, rachas que castigan).
- **Prueba:** `packages/safety/python/tests/test_output_filter.py` (security): una salida con afirmaciones clínicas se reemplaza o marca; `tools/audit/tests/test_forbidden_words_ci.py` (audit).
- **Terminado cuando:** ambas pruebas pasan.

### T-05-011 Registro de consentimientos y consulta `consent.check`
- **Requisitos:** REQ-05-031, REQ-05-034, REQ-05-035, REQ-05-036, REQ-05-037, REQ-05-038, REQ-05-039
- **Depende de:** T-02-002, T-02-003
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/consent/{models,service,check}.py`, `apps/orchestrator/migrations/0009_consent.sql`, `apps/orchestrator/tests/consent/test_consent.py`
- **Qué hacer:** `consent_record` (categoría, proveedor, versión del texto, decisión, modalidad, fecha) y la vista vigente. Todos los consentimientos arrancan apagados. `consent.check(persona, categoría, proveedor)` lo usan el gateway, el constructor de prompts y la voz en la nube: sin consentimiento vigente no se envía. Revocar deja de usar los datos de esa categoría de inmediato. Un cambio importante del texto invalida la decisión previa hasta una nueva. Los consentimientos no vencen por tiempo y no se vuelven a pedir tras un rechazo. Si un cuidador/a ayuda, la decisión final la confirma la persona con su modalidad, salvo una delegación específica (spec 06).
- **Prueba:** `apps/orchestrator/tests/consent/test_consent.py` (unit y security): nacen apagados; sin consentimiento no se envía; revocar es inmediato; un rechazo no se vuelve a pedir; el cuidador/a sin delegación no puede consentir por la persona.
- **Terminado cuando:** la prueba pasa.

### T-05-012 Pantalla de consentimientos [UI]
- **Requisitos:** REQ-05-030, REQ-05-032, REQ-05-033
- **Depende de:** T-05-011, T-00-015
- **Archivos:** `apps/web/src/features/consent/{ConsentCenter,ConsentCard}.tsx`, `apps/web/tests/e2e/consent.spec.ts`
- **Qué hacer:** centro de consentimientos con las categorías: contenido de tareas a un proveedor de modelo (por proveedor), voz en la nube, voz sintética en la nube, aviso al contacto de confianza y su modo, condición declarada, contadores agregados, grabación de diagnóstico y, `[POST-MVP]`, sincronización del perfil. Cada tarjeta con resumen en lenguaje llano (qué datos, quién los recibe, para qué, qué pasa si no los da), lectura en voz alta y texto completo. El sistema se puede usar sin los opcionales, con las funciones afectadas explicadas.
- **Prueba:** `apps/web/tests/e2e/consent.spec.ts` (e2e y a11y): todos arrancan apagados; usar el sistema sin ellos funciona; lectura en voz alta disponible.
- **Terminado cuando:** la prueba pasa.

### T-05-013 Prueba de extremo a extremo de la derivación y rendimiento [CODEX]
- **Requisitos:** REQ-05-050, REQ-05-054
- **Depende de:** T-05-005, T-05-007, T-05-008
- **Archivos:** `apps/web/tests/e2e/crisis-end-to-end.spec.ts`, `packages/safety/python/tests/test_derivation_perf.py`
- **Qué hacer:** en el entorno de prueba con destinatarios ficticios, ejercer toda la ruta (señal → pausa de agentes → mensaje fijo → pregunta o aviso → registro) sin contactar a nadie real; medir que el mensaje fijo aparece en ≤ 1 s también sin red [SUPUESTO].
- **Prueba:** `apps/web/tests/e2e/crisis-end-to-end.spec.ts` (e2e) y `packages/safety/python/tests/test_derivation_perf.py` (perf).
- **Terminado cuando:** ambas pruebas pasan.
