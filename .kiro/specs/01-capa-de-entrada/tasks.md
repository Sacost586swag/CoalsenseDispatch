# Tareas: 01 Capa de entrada

**Requisitos:** `requirements.md`. **Diseño:** `design.md`. **Marcas:** `[CODEX]` paralelizable por Codex; `[UI]` interfaz (skills de diseño subordinadas a `.kiro/steering/accessibility.md`); `[POST-MVP]` fuera del corte del MVP.

**Contexto común (léelo una vez).**
- Código del companion en `apps/companion/src/coalsense_companion/` (Python 3.12, uv); pruebas en `apps/companion/tests/`. Esquemas en `packages/intents/`. Reglas de dependencia en `.kiro/steering/structure.md`.
- Tipos de intención: `control.stop`, `control.undo`, `help.request_human` (prioridad `preemptive`); `approval.approve`, `approval.reject`; `pointer.*`, `key.press`, `text.insert`, `text.dictation`, `nav.*`, `ui.*`, `mode.set`, `input.pause`, `input.resume`, `profile.switch`, `calibration.request`, `command.invoke`. El `actor_origin` (`person`, `caregiver`, `system`) lo fija el núcleo desde la sesión del adaptador.
- Los procesos de visión y voz **no importan librerías de red** (la CI lo audita). Ningún cuadro, audio ni landmark sale del dispositivo.
- Las cifras de latencia y recursos son `[SUPUESTO]` y se reemplazan por valores medidos (T-01-047).
- Las pruebas `replay` usan fixtures de `apps/companion/tests/fixtures/` con `manifest.json` (`synthetic: true` o `consent_ref`).

## Orden de dependencias

```
Ola 0 (de la spec 00): T-00-001, T-00-007, T-00-013, T-00-014, T-00-015
Ola 1: T-01-001
Ola 2: T-01-002, T-01-003, T-01-007, T-01-008, T-01-013, T-01-018
Ola 3: T-01-004, T-01-005, T-01-006, T-01-009, T-01-010, T-01-014, T-01-019, T-01-020, T-01-027, T-01-032
Ola 4: T-01-011, T-01-012, T-01-015, T-01-016, T-01-021, T-01-022, T-01-023, T-01-028, T-01-029, T-01-033, T-01-037, T-01-043, T-01-044
Ola 5: T-01-017, T-01-024, T-01-025, T-01-026, T-01-030, T-01-031, T-01-034, T-01-035, T-01-036, T-01-038, T-01-039, T-01-042
Ola 6: T-01-040, T-01-041, T-01-045, T-01-046, T-01-054, T-01-055, T-01-056
Ola 7: T-01-047, T-01-048, T-01-049
POST-MVP: T-01-050, T-01-051, T-01-052, T-01-053, T-01-057
```

---

## Bus de intenciones

### T-01-001 Esquema JSON de intenciones y del perfil [CODEX]
- **Requisitos:** REQ-01-001, REQ-01-003, REQ-01-010, REQ-01-083
- **Depende de:** T-00-001
- **Archivos:** `packages/intents/schema/intent.schema.json`, `packages/intents/schema/capability-profile.schema.json`, `packages/intents/schema/catalog.yaml`, `packages/intents/tests/test_schema.py`
- **Qué hacer:** definir el JSON Schema de la intención (`id`, `type`, `modality`, `adapter`, `actor_origin`, `monotonic_ts`, `wall_ts`, `confidence`, `priority`, `payload`) con un catálogo de tipos y sus cargas útiles. `approval.*` exige `pending_action_id` y `content_digest`. `priority` se deriva del tipo y no la elige el adaptador. Definir también el esquema del perfil de capacidad (modalidades, vínculos, disparadores de Alto/Deshacer/Ayuda, `approval_min_confidence`, `min_target_px ≥ 44`, `declared_condition` opcional) con `schema_version`.
- **Prueba:** `packages/intents/tests/test_schema.py` (contract): intenciones válidas pasan; sin `pending_action_id` en `approval.*` falla; la misma orden por dos modalidades difiere solo en `modality`, `adapter` y `confidence`.
- **Terminado cuando:** la prueba pasa y el esquema está versionado.

### T-01-002 Generación de tipos y chequeo de deriva [CODEX]
- **Requisitos:** REQ-01-002
- **Depende de:** T-01-001
- **Archivos:** `packages/intents/gen/generate.py`, `packages/intents/python/coalsense_intents/models.py` (generado), `packages/intents/ts/src/types.ts` (generado), `tools/audit/audit_schema_drift.py`, `tools/audit/tests/test_schema_drift.py`
- **Qué hacer:** generar modelos Python y tipos TypeScript desde el JSON Schema y versionar el resultado. Script de auditoría que regenera en memoria y falla si difiere de lo versionado.
- **Prueba:** `tools/audit/tests/test_schema_drift.py` (contract): sin cambios pasa; tocar el esquema sin regenerar falla.
- **Terminado cuando:** la prueba pasa y la CI ejecuta la auditoría.

### T-01-003 Núcleo del bus: validación, prioridades y coalescencia
- **Requisitos:** REQ-01-004, REQ-01-005, REQ-01-006, REQ-01-014, REQ-01-144
- **Depende de:** T-01-001
- **Archivos:** `apps/companion/src/coalsense_companion/bus/{core,priority,coalescing}.py`, `apps/companion/tests/bus/test_core.py`, `apps/companion/tests/bus/test_dummy_adapter.py`
- **Qué hacer:** cola con dos clases de prioridad. Valida cada intención contra el esquema y la descarta con registro si no valida. Las `preemptive` se entregan antes que cualquier `normal` en cola y nunca se descartan ni retrasan; las `approval.*` tampoco se descartan. Con cola saturada solo se fusionan o descartan intenciones continuas (`pointer.move`). Interfaz `subscribe(types, consumer)`. Un adaptador ficticio que cumple el contrato debe poder publicar sin cambios en los consumidores.
- **Prueba:** `apps/companion/tests/bus/test_core.py` (unit, con pruebas de propiedades): orden y no descarte bajo carga; intención inválida descartada; `test_dummy_adapter.py` (contract).
- **Terminado cuando:** las pruebas pasan y la entrega local p95 está medida (se formaliza en T-01-047).

### T-01-004 Autenticación de adaptadores y origen del actor
- **Requisitos:** REQ-01-007, REQ-01-008, REQ-01-009, REQ-01-012
- **Depende de:** T-01-003
- **Archivos:** `apps/companion/src/coalsense_companion/bus/{auth,pipe_server,session}.py`, `apps/companion/src/coalsense_companion/supervisor.py`, `apps/companion/tests/bus/test_auth.py`
- **Qué hacer:** canal local por named pipe de Windows con ACL al usuario actual y credencial efímera por adaptador que entrega el supervisor al iniciar el proceso hijo (no se escribe a disco). `actor_origin` se deriva de la sesión del adaptador (persona o cuidador/a autenticado) y se ignora cualquier valor en la carga útil. Rechazar `approval.approve` con origen `system` y registrar. Entregar `approval.*` de `caregiver` marcado para que el motor de políticas valide la delegación.
- **Prueba:** `apps/companion/tests/bus/test_auth.py` (security): un proceso no registrado no publica; un adaptador que pone `actor_origin` en el payload no lo cambia; `approval.approve` de `system` se rechaza; de `caregiver` se entrega marcada.
- **Terminado cuando:** las pruebas pasan.

### T-01-005 Validación de aprobaciones y umbral de confianza
- **Requisitos:** REQ-01-010, REQ-01-011, REQ-01-155
- **Depende de:** T-01-003, T-01-001
- **Archivos:** `apps/companion/src/coalsense_companion/bus/approval_guard.py`, `apps/companion/tests/bus/test_approval_guard.py`
- **Qué hacer:** rechazar `approval.*` sin `pending_action_id` y `content_digest`. Si la confianza de `approval.approve` está bajo el umbral del perfil, no emitirla como aprobación: publicar un evento que muestra o dice lo que se entendió y ofrece repetir o elegir otra modalidad (falla cerrada).
- **Prueba:** `apps/companion/tests/bus/test_approval_guard.py` (replay y unit): bajo el umbral no hay aprobación; en fixtures de ruido y reposo, cero `approval.approve`.
- **Terminado cuando:** las pruebas pasan.

### T-01-006 Registro local de intenciones en la bitácora
- **Requisitos:** REQ-01-013
- **Depende de:** T-01-003
- **Archivos:** `apps/companion/src/coalsense_companion/bus/audit_log.py`, `apps/companion/tests/bus/test_audit_log.py`
- **Qué hacer:** registrar por cada intención `id`, `type`, `modality`, `actor_origin` y resultado, en un almacenamiento local que luego se envía al orquestador al reconectar. Nunca incluir audio, video, landmarks ni el texto de `text.dictation`.
- **Prueba:** `apps/companion/tests/bus/test_audit_log.py` (integration): sin conexión se acumula; el contenido de un dictado de muestra no aparece en el registro.
- **Terminado cuando:** la prueba pasa.

### T-01-007 Arnés de reproducción y manifiesto de fixtures [CODEX]
- **Requisitos:** REQ-01-015, REQ-01-100
- **Depende de:** T-01-003
- **Archivos:** `apps/companion/src/coalsense_companion/replay/{harness,sources}.py`, `tools/audit/audit_fixtures.py`, `apps/companion/tests/replay/test_harness.py`, `tools/audit/tests/test_audit_fixtures.py`
- **Qué hacer:** fuente inyectable (en vivo o fixture) para los adaptadores y un arnés que reproduce una fixture y devuelve la secuencia de intenciones sin `id` ni marcas de tiempo, para compararla. Auditoría que falla si un `manifest.json` no declara `synthetic: true` o un `consent_ref`.
- **Prueba:** `apps/companion/tests/replay/test_harness.py` (replay): misma fixture, perfil y modelo producen la misma secuencia dos veces; `test_audit_fixtures.py` (audit): manifiesto sin consentimiento falla.
- **Terminado cuando:** las pruebas pasan.

### T-01-008 Generador de fixtures sintéticas [CODEX]
- **Requisitos:** REQ-01-100, REQ-01-153
- **Depende de:** T-01-007
- **Archivos:** `apps/companion/tools/make_fixtures/{landmarks,audio}.py`, `apps/companion/tests/fixtures/{landmarks,audio}/**`, `apps/companion/tests/fixtures/README.md`
- **Qué hacer:** generar de forma sintética secuencias de blendshapes y pose (reposo, gesto, movimiento de cabeza, ángulos sentado, reclinado y acostado, pérdida de rostro, dos rostros) y audio (comandos, dictado, voz baja con ruido, «alto» aislado y dentro de frase) con `manifest.json` `synthetic: true`. Debe ser determinista con una semilla.
- **Prueba:** `apps/companion/tests/fixtures/test_fixtures_valid.py` (audit): todas las fixtures tienen manifiesto válido y se generan de forma idéntica con la misma semilla.
- **Terminado cuando:** la prueba pasa y las fixtures cubren los conjuntos listados en `design.md` sección 10.

---

## Alto, Deshacer y Ayuda humana

### T-01-009 StopGuard y detención local
- **Requisitos:** REQ-01-018, REQ-01-019, REQ-01-020
- **Depende de:** T-01-003
- **Archivos:** `apps/companion/src/coalsense_companion/bus/stop_guard.py`, `apps/companion/src/coalsense_companion/actuator/halt.py`, `apps/companion/tests/bus/test_stop_guard.py`
- **Qué hacer:** al llegar `control.stop` el bus invoca de forma síncrona `actuator.halt()` **antes** de encolar: activa una bandera atómica que comprueba cada primitiva, suelta teclas y botones pulsados, termina el arrastre, detiene dictado y escaneo. Después publica `control.stop` al frente de la cola. No depende de la red ni de ningún consumidor. Debe funcionar en todos los modos (comando, dictado, sueño, pausa, escaneo, calibración).
- **Prueba:** `apps/companion/tests/bus/test_stop_guard.py` (integration, propiedades): para cada combinación de modo y actuación en curso, tras `control.stop` no queda primitiva en ejecución ni tecla o botón pulsado, con y sin conexión.
- **Terminado cuando:** la prueba de propiedades pasa.

### T-01-010 Pila de deshacer y clases de actuación
- **Requisitos:** REQ-01-022, REQ-01-023, REQ-01-024
- **Depende de:** T-01-003
- **Archivos:** `apps/companion/src/coalsense_companion/actuator/{undo_stack,action_classes}.py`, `apps/companion/tests/actuator/test_undo.py`
- **Qué hacer:** pila acotada de `UndoEntry` (`kind`, `revert()`, `reversible`). Declarar cada clase de actuación como reversible o no (reversibles: inserción de dictado con foco sin cambiar, arrastre, cambio de modo y de perfil; no reversibles: teclas y clics en apps de terceros). `control.undo` revierte la última reversible e informa cuál; si no hay o no es reversible, lo dice explícitamente y no revierte otra cosa.
- **Prueba:** `apps/companion/tests/actuator/test_undo.py` (unit): ninguna clase queda sin declarar; irreversible no se revierte; pila vacía informa.
- **Terminado cuando:** la prueba pasa.

### T-01-011 Estado `stop_reachable`, latido y salud
- **Requisitos:** REQ-01-026, REQ-01-128, REQ-01-129
- **Depende de:** T-01-009, T-01-004
- **Archivos:** `apps/companion/src/coalsense_companion/bus/stop_state.py`, `apps/companion/src/coalsense_companion/uplink/heartbeat.py`, `apps/companion/tests/bus/test_stop_state.py`
- **Qué hacer:** `StopState` con rutas por modalidad y su salud (dispositivo transmitiendo, modelo cargado, adaptador respondiendo). `stop_reachable` es verdadero solo con al menos una ruta sana; al pasar a falso avisa a la persona de inmediato y a los consumidores. No publicar verdadero hasta verificar la salud. Latido periódico al orquestador; su ausencia lo interpretan los consumidores como `false`.
- **Prueba:** `apps/companion/tests/bus/test_stop_state.py` (integration con fallos inyectados): nunca verdadero sin ruta sana; falso al caer la única ruta; el latido se emite.
- **Terminado cuando:** la prueba pasa.

### T-01-012 Ayuda humana hacia la spec 05
- **Requisitos:** REQ-01-025
- **Depende de:** T-01-003
- **Archivos:** `apps/companion/src/coalsense_companion/bus/help_route.py`, `apps/companion/tests/bus/test_help_route.py`
- **Qué hacer:** entregar `help.request_human` con prioridad `preemptive` al módulo de derivación local de `packages/safety` (spec 05) mediante la interfaz `DerivationReceiver`, sin pasar por ningún modelo de lenguaje y sin depender de la red. Hasta que exista T-05-004, usar un receptor simulado que registra la llamada; T-05-004 aporta el real.
- **Prueba:** `apps/companion/tests/bus/test_help_route.py` (integration, red deshabilitada): la derivación se inicia desde cada modalidad.
- **Terminado cuando:** la prueba pasa.

---

## Perfil de capacidad

### T-01-013 Esquema, invariantes y validación del perfil
- **Requisitos:** REQ-01-016, REQ-01-017, REQ-01-083, REQ-01-084
- **Depende de:** T-01-001
- **Archivos:** `apps/companion/src/coalsense_companion/profile/{model,validate}.py`, `apps/companion/tests/profile/test_validate.py`
- **Qué hacer:** modelo y validación del perfil. Invariantes: cada modalidad habilitada tiene al menos un disparador de `control.stop` y de `control.undo` (se pueden cambiar, no quitar); `min_target_px ≥ 44`; `declared_condition` solo existe si la persona lo declaró con consentimiento. Rechazar guardar o activar un perfil que las incumpla.
- **Prueba:** `apps/companion/tests/profile/test_validate.py` (unit): perfil sin disparador de Alto en una modalidad habilitada se rechaza; quitar un disparador se rechaza; cambiarlo se acepta.
- **Terminado cuando:** la prueba pasa.

### T-01-014 Almacenamiento cifrado y migraciones del perfil
- **Requisitos:** REQ-01-085, REQ-01-091
- **Depende de:** T-01-013
- **Archivos:** `apps/companion/src/coalsense_companion/profile/{store,crypto,migrations}.py`, `apps/companion/tests/profile/test_store.py`
- **Qué hacer:** guardar el perfil y las calibraciones cifrados en el dispositivo con una clave protegida por el almacén de credenciales de Windows [SUPUESTO]. El perfil vive solo en el dispositivo en el MVP (sin sincronización). Migraciones por `schema_version`. Si el perfil es inválido, usar el último válido y nunca arrancar sin una ruta de `control.stop`.
- **Prueba:** `apps/companion/tests/profile/test_store.py` (security y unit): el archivo en disco no es legible sin la clave; perfil corrupto vuelve al último válido; migración de v1 a v2 conserva los datos.
- **Terminado cuando:** la prueba pasa.

### T-01-015 Perfiles múltiples, exportación y borrado local
- **Requisitos:** REQ-01-087, REQ-01-088, REQ-01-152
- **Depende de:** T-01-014
- **Archivos:** `apps/companion/src/coalsense_companion/profile/{multi,export,erase}.py`, `apps/companion/tests/profile/test_multi_export_erase.py`
- **Qué hacer:** varios perfiles («en cama», «sentado»...) y cambio con `profile.switch` desde cualquier modalidad, anunciándolo. Exportar un JSON legible y completo. Borrar perfiles, calibraciones, comandos propios y bitácora local, y confirmarlo. Pedir borrado también al servidor cuando haya conexión (spec 07).
- **Prueba:** `apps/companion/tests/profile/test_multi_export_erase.py` (e2e): cambiar de perfil por voz simulada; exportar y reimportar; borrar deja el dispositivo sin datos de la persona.
- **Terminado cuando:** la prueba pasa.

### T-01-016 Edición por cuidador/a, propuestas y no salida del perfil
- **Requisitos:** REQ-01-086, REQ-01-089, REQ-01-090
- **Depende de:** T-01-014, T-01-004
- **Archivos:** `apps/companion/src/coalsense_companion/profile/{proposals,delegation_check}.py`, `apps/companion/tests/profile/test_proposals_egress.py`
- **Qué hacer:** (a) cualquier cambio propuesto por el sistema o por un cuidador/a con delegación vigente (consulta a la spec 06 mediante la interfaz `DelegationLookup`, simulada y negada por defecto hasta T-06-003) crea una versión pendiente que la persona aprueba o revierte; se registra quién cambió qué; (b) prueba de contrato que garantiza que el perfil y la condición declarada no aparecen en ningún mensaje saliente del enlace al orquestador ni en la telemetría.
- **Prueba:** `apps/companion/tests/profile/test_proposals_egress.py` (security): ningún mensaje saliente contiene campos del perfil; el sistema no aplica un cambio sin aprobación.
- **Terminado cuando:** la prueba pasa.

### T-01-017 Visor del perfil en lenguaje llano [UI]
- **Requisitos:** REQ-01-092
- **Depende de:** T-01-013, T-00-015
- **Archivos:** `apps/web/src/features/capability-profile/ProfileView.tsx` (WebView del companion), `apps/web/tests/e2e/profile-view.spec.ts`
- **Qué hacer:** pantalla que muestra qué hace cada gesto o frase (por ejemplo «abrir la boca = clic izquierdo») y qué modalidades están activas, con estados cargando, vacío, error. Usar solo componentes de `packages/ui`.
- **Prueba:** `apps/web/tests/e2e/profile-view.spec.ts` (e2e y a11y): contenido en lenguaje llano; axe-core sin violaciones; objetivos ≥ 44×44 px.
- **Terminado cuando:** la prueba pasa.

---

## Voz

### T-01-018 Intérprete de archivos de comandos
- **Requisitos:** REQ-01-028, REQ-01-029
- **Depende de:** T-01-001
- **Archivos:** `apps/companion/src/coalsense_companion/commands/{loader,schema,matcher}.py`, `packages/intents/schema/commands.schema.json`, `apps/companion/tests/commands/test_loader.py`
- **Qué hacer:** cargar `*.commands.yaml` (formato del diseño sección 4.3) con frase → intención, parámetros (números, listas), contexto (aplicación activa, modo de voz) y prioridad. Validar con JSON Schema. Un archivo no puede definir `approval.*`, `control.*` ni `help.*`. Si un archivo es inválido, conservar el último conjunto válido e informar el error con archivo y línea.
- **Prueba:** `apps/companion/tests/commands/test_loader.py` (unit): parámetros y contexto resuelven; archivo inválido mantiene el conjunto anterior; intentar definir `control.stop` falla.
- **Terminado cuando:** la prueba pasa.

### T-01-019 Conjunto base de comandos en español y licencias
- **Requisitos:** REQ-01-030, REQ-01-035, REQ-01-037
- **Depende de:** T-01-018
- **Archivos:** `apps/companion/src/coalsense_companion/commands/base/es-EC.commands.yaml`, `apps/companion/tests/commands/test_base_coverage.py`, `THIRD_PARTY.md`
- **Qué hacer:** conjunto base en español de Ecuador que cubra: puntero (mover, clic, clic derecho, doble clic, arrastre por alternancia), desplazamiento, teclas y atajos, texto, ventanas, cambio de modo de voz, sueño y despertar, Alto, Deshacer, Ayuda humana, aprobar, rechazar, mostrar números, mostrar cuadrícula, centrar. Si se reutilizan comandos de `talonhub/community` (MIT), conservar su aviso de copyright y licencia en `THIRD_PARTY.md`. No incluir código del núcleo de Talon (EULA).
- **Prueba:** `apps/companion/tests/commands/test_base_coverage.py` (unit y audit): matriz de cobertura completa; sin dependencia del inglés; `THIRD_PARTY.md` contiene el aviso MIT si se reutilizó contenido.
- **Terminado cuando:** la prueba pasa.

### T-01-020 Adaptador de voz: captura, modos y sueño
- **Requisitos:** REQ-01-027, REQ-01-033
- **Depende de:** T-01-003, T-01-007
- **Archivos:** `apps/companion/src/coalsense_companion/adapters/voice/{adapter,capture,vad,modes}.py`, `apps/companion/tests/adapters/voice/test_modes.py`
- **Qué hacer:** proceso de voz independiente, sin librerías de red, que captura el micrófono, detecta actividad de voz y gestiona los modos `command`, `dictation` y `sleep`. En `sleep` solo se interpretan despertar, Alto y Ayuda humana. El reconocimiento es local por defecto. Aceptar fuente en vivo o fixture. Mostrar el estado de forma visible.
- **Prueba:** `apps/companion/tests/adapters/voice/test_modes.py` (replay): en sueño solo actúan despertar, Alto y Ayuda; el audio no sale del proceso; no se importan módulos de red (audit).
- **Terminado cuando:** la prueba pasa.

### T-01-021 Detector de palabras de control
- **Requisitos:** REQ-01-021, REQ-01-142, REQ-01-154
- **Depende de:** T-01-020
- **Archivos:** `apps/companion/src/coalsense_companion/adapters/voice/control_words.py`, `apps/companion/tests/adapters/voice/test_control_words.py`
- **Qué hacer:** detector de baja latencia, siempre activo, para Alto, Deshacer y Ayuda, con umbral más permisivo que el de los demás comandos [SUPUESTO: elegir y medir el motor en hardware real, `[verificar]`]. En modo dictado, Alto solo cuenta si se dice como enunciado aislado (silencio configurable por ambos lados, `isolation_silence_ms`); dentro de una frase se trata como texto.
- **Prueba:** `apps/companion/tests/adapters/voice/test_control_words.py` (replay): «alto» aislado detiene en dictado; «un edificio alto» se dicta como texto; detección ≥ 99% en la fixture de estrés [SUPUESTO].
- **Terminado cuando:** la prueba pasa.

### T-01-022 Reconocedor de comandos con ambigüedad
- **Requisitos:** REQ-01-031, REQ-01-139
- **Depende de:** T-01-018, T-01-020
- **Archivos:** `apps/companion/src/coalsense_companion/adapters/voice/command_recognizer.py`, `apps/companion/tests/adapters/voice/test_ambiguity.py`
- **Qué hacer:** reconocedor de comandos en streaming con gramática restringida (nivel 1 del diseño). Si dos hipótesis quedan a menos de `ambiguity_margin`, no ejecutar ninguna: publicar el evento `ui.disambiguate` con opciones numeradas, aceptar la elección por cualquier modalidad. Medir latencia de fin de enunciado a intención.
- **Prueba:** `apps/companion/tests/adapters/voice/test_ambiguity.py` (replay): hipótesis cercanas no ejecutan; clara ejecuta una sola.
- **Terminado cuando:** la prueba pasa.

### T-01-023 Dictado: transcripción, formato y corrección
- **Requisitos:** REQ-01-038, REQ-01-039, REQ-01-040, REQ-01-042
- **Depende de:** T-01-020
- **Archivos:** `apps/companion/src/coalsense_companion/adapters/voice/dictation/{transcriber,formatter,corrections}.py`, `apps/companion/tests/adapters/voice/test_dictation.py`
- **Qué hacer:** transcripción local con `faster-whisper` cargado bajo demanda `[verificar rendimiento]`, que publica `text.dictation` parcial y final. Formateo hablado en español (coma, punto, nueva línea, mayúscula). Comandos de corrección («borra eso») que modifican solo el último segmento y se registran en la pila de deshacer. El audio nunca se escribe a disco; el texto vive en memoria hasta entregarse.
- **Prueba:** `apps/companion/tests/adapters/voice/test_dictation.py` (replay y security): parciales y finales; formato correcto; corrección solo del último segmento; ningún archivo de audio en disco.
- **Terminado cuando:** la prueba pasa.

### T-01-024 Inserción de dictado deshacible y micrófono desconectado
- **Requisitos:** REQ-01-041, REQ-01-043
- **Depende de:** T-01-023, T-01-010, T-01-033
- **Archivos:** `apps/companion/src/coalsense_companion/adapters/voice/dictation/insert.py`, `apps/companion/tests/adapters/voice/test_insert.py`
- **Qué hacer:** insertar cada enunciado en el campo enfocado de otra aplicación como una unidad deshacible. Si el micrófono se desconecta, conservar el texto ya transcrito, mostrar «modalidad no detectada» y ofrecer continuar con otra modalidad.
- **Prueba:** `apps/companion/tests/adapters/voice/test_insert.py` (integration): `control.undo` revierte el último enunciado; desconexión inyectada conserva el texto.
- **Terminado cuando:** la prueba pasa.

### T-01-025 Ayuda de comandos y eco de lo entendido [UI]
- **Requisitos:** REQ-01-032, REQ-01-034
- **Depende de:** T-01-018, T-00-015
- **Archivos:** `apps/web/src/features/voice-help/{CommandHelp,EchoHud}.tsx`, `apps/web/tests/e2e/voice-help.spec.ts`
- **Qué hacer:** pantalla «¿qué puedo decir?» con los comandos válidos en el contexto actual, navegable por cualquier modalidad, y un eco visible (y opcionalmente hablado) de lo entendido. Estados cargando, vacío, error.
- **Prueba:** `apps/web/tests/e2e/voice-help.spec.ts` (e2e y a11y).
- **Terminado cuando:** la prueba pasa.

### T-01-026 Reconocimiento de voz en la nube, opcional y con consentimiento
- **Requisitos:** REQ-01-096
- **Depende de:** T-01-020
- **Archivos:** `apps/companion/src/coalsense_companion/cloud/stt_cloud.py`, `apps/web/src/features/consent/CloudSttConsent.tsx`, `apps/companion/tests/cloud/test_stt_cloud.py`
- **Qué hacer:** módulo separado de los procesos de voz locales, **apagado por defecto**. Solo se activa con el consentimiento de la categoría `cloud_stt` (spec 05), que describe qué datos salen y a qué proveedor. Indicador persistente de que el modo nube está activo y revocación con una acción.
- **Prueba:** `apps/companion/tests/cloud/test_stt_cloud.py` (e2e y security): sin consentimiento no sale audio; con consentimiento aparece el indicador; revocar detiene el envío.
- **Terminado cuando:** la prueba pasa.

---

## Cabeza y gestos

### T-01-027 Captura de cámara y canalización MediaPipe en memoria
- **Requisitos:** REQ-01-044
- **Depende de:** T-01-003, T-01-007
- **Archivos:** `apps/companion/src/coalsense_companion/adapters/head_gesture/{adapter,camera,landmarker}.py`, `apps/companion/tests/adapters/head_gesture/test_pipeline.py`
- **Qué hacer:** proceso de visión independiente que captura la cámara, ejecuta MediaPipe Face Landmarker (478 landmarks, 52 blendshapes, matriz de transformación facial) y entrega puntajes y pose al motor de gestos. Los cuadros viven solo en memoria y se descartan; el proceso **no importa módulos de red**. Fuente en vivo o fixture. El modelo y sus archivos vienen del paquete (sin descargas en tiempo de ejecución; spec 09).
- **Prueba:** `apps/companion/tests/adapters/head_gesture/test_pipeline.py` (security y replay): no se escribe ningún cuadro a disco; la auditoría de importaciones pasa; la fixture produce los mismos puntajes.
- **Terminado cuando:** la prueba pasa.

### T-01-028 Cabeza → puntero, compensación de ángulo y «centrar»
- **Requisitos:** REQ-01-045, REQ-01-046, REQ-01-052, REQ-01-137, REQ-01-157
- **Depende de:** T-01-027
- **Archivos:** `apps/companion/src/coalsense_companion/adapters/head_gesture/{pointer,filters,neutral}.py`, `apps/companion/tests/adapters/head_gesture/test_pointer.py`
- **Qué hacer:** modo `rate` (por defecto): fuera de una zona muerta, la velocidad del puntero crece con la desviación de la pose hasta `max_speed`; modo `absolute` opcional. Restar pose neutral y corregir la inclinación de la cámara (`camera_roll_deg`). Filtro de suavizado adaptativo y filtro de temblor opcional (limita aceleración y salto). Orden «centrar»: fija la pose actual como neutral sin tocar los gestos. Al cambiar de perfil, aplicar de inmediato el ángulo y la pose del perfil nuevo.
- **Prueba:** `apps/companion/tests/adapters/head_gesture/test_pointer.py` (replay): fixtures sentado, reclinado y acostado dan el mismo movimiento relativo tras compensar; el temblor se limita; «centrar» no cambia umbrales de gestos.
- **Terminado cuando:** la prueba pasa.

### T-01-029 Motor de gestos y vínculos
- **Requisitos:** REQ-01-047, REQ-01-048, REQ-01-049, REQ-01-138
- **Depende de:** T-01-027, T-01-013
- **Archivos:** `apps/companion/src/coalsense_companion/adapters/head_gesture/{gestures,bindings}.py`, `apps/companion/tests/adapters/head_gesture/test_gestures.py`
- **Qué hacer:** máquina de estados por gesto `IDLE → ARMED → ACTIVE → IDLE` con umbral de activación `on` y de liberación `off` (`off < on`), `hold_ms` y `cooldown_ms` del perfil. Vincular cualquier gesto calibrado a cualquier intención del catálogo. Doble clic = una sola intención `pointer.double_click` por un solo gesto; arrastre = alternancia `pointer.drag_toggle`. Ningún vínculo exige dos gestos en una ventana de tiempo, simultáneos ni mantener un gesto para arrastrar (revisión estática de los vínculos al guardar el perfil).
- **Prueba:** `apps/companion/tests/adapters/head_gesture/test_gestures.py` (replay y unit): histéresis evita parpadeo; sostenimiento respetado; un perfil con un vínculo que requiere dos gestos en ventana de tiempo se rechaza.
- **Terminado cuando:** la prueba pasa.

### T-01-030 Pérdida de rostro, varios rostros, calidad y pausa
- **Requisitos:** REQ-01-050, REQ-01-051, REQ-01-053, REQ-01-054
- **Depende de:** T-01-028, T-01-029
- **Archivos:** `apps/companion/src/coalsense_companion/adapters/head_gesture/{presence,tracking_quality,pause}.py`, `apps/companion/tests/adapters/head_gesture/test_presence.py`
- **Qué hacer:** si no se detecta rostro más del tiempo configurado, congelar el puntero sin saltos, mostrar y decir «modalidad no detectada» y mantener las demás modalidades; al volver, reanudar sin salto. Con varios rostros, seguir el rastreado desde la calibración por continuidad espacial, **sin reconocimiento facial ni embeddings**; si se pierde la continuidad, pausar y pedir a la persona que reanude. Aviso accionable y no culpabilizante si la calidad cae (poca luz, oclusión). Órdenes de pausa y reanudar del seguimiento, con Alto y Ayuda siempre activos.
- **Prueba:** `apps/companion/tests/adapters/head_gesture/test_presence.py` (replay): pérdida y regreso de rostro sin salto; dos rostros siguen al correcto; pausa detiene los gestos pero Alto sigue activo.
- **Terminado cuando:** la prueba pasa.

### T-01-031 Modo web de visión
- **Requisitos:** REQ-01-055
- **Depende de:** T-01-001, T-00-014
- **Archivos:** `apps/web/src/features/vision/{worker,landmarker,gesture-engine}.ts`, `apps/web/public/models/face_landmarker.task`, `apps/web/tests/e2e/vision-web.spec.ts`
- **Qué hacer:** misma lógica de gestos y pose con MediaPipe Tasks Vision en un Web Worker, procesando los cuadros solo en la página. Servir los archivos del modelo desde el mismo origen. El modo web controla solo la app web. Publicar solo intenciones por el enlace al orquestador.
- **Prueba:** `apps/web/tests/e2e/vision-web.spec.ts` (e2e y security, Playwright con captura de red): durante una sesión de cámara simulada no hay ninguna petición con cuerpo de imagen, audio o landmarks, ni a orígenes distintos del propio.
- **Terminado cuando:** la prueba pasa.

---

## Teclado y mouse

### T-01-032 Adaptador de teclado y mouse con atajos globales
- **Requisitos:** REQ-01-056, REQ-01-057, REQ-01-058, REQ-01-059
- **Depende de:** T-01-003, T-01-004
- **Archivos:** `apps/companion/src/coalsense_companion/adapters/keyboard_mouse/{adapter,hotkeys}.py`, `apps/companion/tests/adapters/keyboard_mouse/test_adapter.py`
- **Qué hacer:** traducir teclado y mouse físicos a las mismas intenciones del bus con `modality = keyboard_mouse`. Atajos globales configurables para Alto, Deshacer y Ayuda humana, con detección y rechazo de conflictos con otros atajos del perfil. Aceptar teclado/mouse y otra modalidad a la vez sin conmutar. Las intenciones llevan `actor_origin = caregiver` solo si hay sesión de cuidador/a autenticada; nunca aprueban en nombre de la persona sin delegación.
- **Prueba:** `apps/companion/tests/adapters/keyboard_mouse/test_adapter.py` (unit, integration y security): atajo en conflicto se rechaza; uso simultáneo con voz; origen `caregiver` solo con sesión; aprobación de cuidador/a sin delegación se entrega marcada y la rechaza la política (spec 02).
- **Terminado cuando:** la prueba pasa.

---

## Actuador de escritorio

### T-01-033 Actuador Windows: puntero, teclas y texto
- **Requisitos:** REQ-01-060, REQ-01-065, REQ-01-067, REQ-01-068
- **Depende de:** T-01-009, T-01-010
- **Archivos:** `apps/companion/src/coalsense_companion/actuator/{pointer,keys,text,guard,results}.py`, `apps/companion/tests/actuator/test_actuator.py`
- **Qué hacer:** ejecutar `pointer.*`, `key.press` y `text.insert` en Windows (`pynput` o `PyAutoGUI`), publicando el resultado (éxito o fallo con causa). El actuador solo acepta solicitudes del bus: ninguna otra interfaz de entrada (REQ-01-067). Si la ventana de destino no es controlable (privilegios elevados), decirlo, explicar por qué y ofrecer alternativas. Mientras `pointer.drag_toggle` está activo, mostrar el estado de arrastre y terminarlo con Alto o con un segundo `drag_toggle`.
- **Prueba:** `apps/companion/tests/actuator/test_actuator.py` (integration y security): solicitud fuera del bus rechazada; ventana elevada informa; arrastre visible y terminable.
- **Terminado cuando:** la prueba pasa.

### T-01-034 Números en pantalla con UI Automation [UI]
- **Requisitos:** REQ-01-061
- **Depende de:** T-01-033, T-00-016
- **Archivos:** `apps/companion/src/coalsense_companion/actuator/numbers/{uia_scan,overlay,select}.py`, `apps/companion/tests/actuator/test_numbers.py`
- **Qué hacer:** recorrer UI Automation de la ventana activa, filtrar elementos accionables, ordenarlos por lectura y superponerles números con una ventana transparente que no captura el puntero. Al decir el número, activar el elemento. Refrescar al cambiar la ventana. Mostrar cuando una aplicación no expone elementos (Chromium sin accesibilidad) y ofrecer la cuadrícula.
- **Prueba:** `apps/companion/tests/actuator/test_numbers.py` (e2e): en una aplicación de muestra nativa, decir «número 3» activa el tercer elemento.
- **Terminado cuando:** la prueba pasa.

### T-01-035 Cuadrícula, imán y vía sin puntería
- **Requisitos:** REQ-01-062, REQ-01-063, REQ-01-064
- **Depende de:** T-01-033
- **Archivos:** `apps/companion/src/coalsense_companion/actuator/{grid,snapping}.py`, `apps/companion/tests/actuator/test_grid_snapping.py`
- **Qué hacer:** cuadrícula de celdas numeradas que se refina en pasos sucesivos (3×3 [SUPUESTO]) hasta ubicar el punto; imán configurable hacia el elemento accionable más cercano dentro de un radio. Asegurar que, para cualquier elemento accionable de las aplicaciones de muestra (nativa y Chromium), existe al menos una vía sin puntería fina (números, cuadrícula o imán).
- **Prueba:** `apps/companion/tests/actuator/test_grid_snapping.py` (e2e): en dos aplicaciones de muestra se logra un clic en un objetivo pequeño solo con cuadrícula.
- **Terminado cuando:** la prueba pasa.

### T-01-036 Retroalimentación multicanal
- **Requisitos:** REQ-01-066, REQ-01-125
- **Depende de:** T-01-033, T-00-015
- **Archivos:** `apps/companion/src/coalsense_companion/feedback/{service,tts_windows,hud_bridge}.py`, `apps/companion/tests/feedback/test_feedback.py`
- **Qué hacer:** servicio de retroalimentación con canal visual, de audio (voz del sistema de Windows por defecto; Piper opcional una vez resuelta su licencia, PA-09) o ambos según el perfil. Los estados críticos (Alto, modalidad no detectada, aprobación pendiente) usan más de un canal y no dependen solo del color.
- **Prueba:** `apps/companion/tests/feedback/test_feedback.py` (a11y e integration): estado crítico emite visual y audio; ninguna señal depende solo del color.
- **Terminado cuando:** la prueba pasa.

---

## Calibración

### T-01-037 Detección de dispositivos y permisos
- **Requisitos:** REQ-01-069, REQ-01-099
- **Depende de:** T-01-027, T-01-020
- **Archivos:** `apps/companion/src/coalsense_companion/calibration/{devices,permissions}.py`, `apps/companion/tests/calibration/test_devices.py`
- **Qué hacer:** listar cámaras, micrófonos y dispositivos de switch disponibles y su estado. Si no hay ninguno, estado «modalidad no detectada» con ayuda del cuidador/a con teclado y mouse. Si el sistema operativo o el navegador deniega un permiso, mostrar «modalidad no detectada» con la causa «permiso denegado» y los pasos para concederlo.
- **Prueba:** `apps/companion/tests/calibration/test_devices.py` (integration y e2e): sin dispositivos y con permiso denegado se muestran los estados con sus causas.
- **Terminado cuando:** la prueba pasa.

### T-01-038 Cálculo de umbrales, separabilidad y descarte de muestras [CODEX]
- **Requisitos:** REQ-01-072, REQ-01-075, REQ-01-082
- **Depende de:** T-01-029
- **Archivos:** `apps/companion/src/coalsense_companion/calibration/{thresholds,separability,rest_check}.py`, `apps/companion/tests/calibration/test_thresholds.py`
- **Qué hacer:** a partir de muestras en reposo y con el gesto, calcular `on` y `off` con margen y verificar que son separables (el percentil bajo de las activas supera el percentil alto del reposo); si no, declarar «calibración fallida» y proponer otro gesto, repetir u otra modalidad. Medir activaciones involuntarias en un periodo de reposo y, si superan el presupuesto (REQ-01-153), proponer un ajuste que solo se aplica si la persona lo aprueba. Descartar las muestras crudas al terminar salvo que la persona active la conservación para diagnóstico.
- **Prueba:** `apps/companion/tests/calibration/test_thresholds.py` (replay y security): gesto separable calcula umbral; no separable falla con alternativas; no quedan muestras crudas en disco.
- **Terminado cuando:** la prueba pasa.

### T-01-039 Calibración de cabeza y de voz
- **Requisitos:** REQ-01-073, REQ-01-074, REQ-01-156
- **Depende de:** T-01-028, T-01-020
- **Archivos:** `apps/companion/src/coalsense_companion/calibration/{head,voice}.py`, `apps/companion/tests/calibration/test_head_voice.py`
- **Qué hacer:** cabeza: registrar la pose neutral y el rango cómodo y ajustar la sensibilidad a ese rango. Voz: medir nivel y ruido del micrófono, probar con comandos de ejemplo e informar la calidad; si el volumen es bajo o variable, ajustar `gain` y sensibilidad del perfil; si aun así no alcanza la calidad mínima, sugerir acercar o reubicar el micrófono, usar diadema u otra modalidad, sin culpar a la persona.
- **Prueba:** `apps/companion/tests/calibration/test_head_voice.py` (replay): fixture de voz baja con ruido ajusta la ganancia y reconoce comandos; fixture de baja calidad produce la sugerencia.
- **Terminado cuando:** la prueba pasa.

### T-01-040 Asistente de calibración con zona de práctica [UI]
- **Requisitos:** REQ-01-070, REQ-01-071, REQ-01-076, REQ-01-077, REQ-01-078, REQ-01-079, REQ-01-123
- **Depende de:** T-01-037, T-01-038, T-01-039, T-00-015
- **Archivos:** `apps/web/src/features/calibration/{Wizard,PracticeZone,FailureCatalog}.tsx`, `packages/ui/src/i18n/calibration-failures.es.ts`, `apps/web/tests/e2e/calibration.spec.ts`
- **Qué hacer:** asistente que avanza cada paso con la propia modalidad que se calibra (o con ayuda del cuidador/a), **sin límite de tiempo**, con pausa, salto de modalidad y reanudación sin perder avance. Zona de práctica donde la persona ejecuta cada vínculo y ve un efecto visible inmediato. No dar por terminada una modalidad sin que Alto y Deshacer estén vinculados y practicados. Catálogo de mensajes de fallo que atribuyen el fallo al equipo o la configuración y ofrecen una vía alternativa por cada código. Si falla, conservar el perfil anterior. Al terminar, guardar el perfil y pasar a la primera tarea (spec 03).
- **Prueba:** `apps/web/tests/e2e/calibration.spec.ts` (e2e y a11y): flujo completo solo con teclado e intenciones simuladas; no hay temporizadores que venzan; falla de gesto conserva el perfil anterior; cada código de fallo tiene mensaje y alternativa (unit del catálogo).
- **Terminado cuando:** la prueba pasa.

### T-01-041 Deriva y recalibración rápida
- **Requisitos:** REQ-01-080, REQ-01-081
- **Depende de:** T-01-040
- **Archivos:** `apps/companion/src/coalsense_companion/calibration/{drift,recalibrate}.py`, `apps/companion/tests/calibration/test_drift.py`
- **Qué hacer:** detectar aumento sostenido de activaciones involuntarias o de rechazos y **sugerir** recalibrar sin cambiar umbrales por su cuenta. «Recalibrar» inicia la modalidad indicada sin borrar el perfil actual hasta que la persona apruebe el nuevo resultado, y permite volver a la versión anterior.
- **Prueba:** `apps/companion/tests/calibration/test_drift.py` (replay y e2e): la deriva produce sugerencia y ningún cambio; recalibrar y revertir restaura el perfil previo.
- **Terminado cuando:** la prueba pasa.

---

## Privacidad de cámara y micrófono

### T-01-042 Indicadores y apagado total [UI]
- **Requisitos:** REQ-01-093, REQ-01-094
- **Depende de:** T-01-027, T-01-020, T-00-015
- **Archivos:** `apps/companion/src/coalsense_companion/privacy/{indicators,hard_off}.py`, `apps/web/src/features/privacy/DeviceIndicators.tsx`, `apps/companion/tests/privacy/test_indicators.py`
- **Qué hacer:** indicador persistente del estado de cámara y micrófono (visual y, si se elige, audio). Apagado total por una acción: libera el dispositivo, deja de procesar e informa qué rutas de Alto siguen disponibles (y avisa si ninguna lo está).
- **Prueba:** `apps/companion/tests/privacy/test_indicators.py` (integration y e2e): tras el apagado el dispositivo queda libre; el aviso lista las rutas de Alto restantes.
- **Terminado cuando:** la prueba pasa.

### T-01-043 Política de egreso y prueba de red del companion
- **Requisitos:** REQ-01-095, REQ-01-097
- **Depende de:** T-01-003
- **Archivos:** `apps/companion/src/coalsense_companion/privacy/egress_policy.py`, `apps/companion/src/coalsense_companion/uplink/client.py`, `apps/companion/tests/privacy/test_egress.py`
- **Qué hacer:** el enlace al orquestador es el único módulo con red; solo envía mensajes que validan contra el esquema de intenciones, latidos y eventos permitidos, con lista permitida de destinos. No grabar a disco audio, video ni landmarks por defecto; la grabación de diagnóstico es opcional, local, visible y borrable.
- **Prueba:** `apps/companion/tests/privacy/test_egress.py` (security): captura de red durante una sesión de cámara y voz simuladas muestra solo mensajes del esquema; ningún payload contiene arreglos de imagen, audio ni landmarks; la grabación de diagnóstico no ocurre sin activarla.
- **Terminado cuando:** la prueba pasa.

### T-01-044 Auditoría: sin biometría, sin inferencia y sin GPL [CODEX]
- **Requisitos:** REQ-01-098, REQ-01-107, REQ-01-151
- **Depende de:** T-00-003
- **Archivos:** `tools/audit/audit_no_biometrics.py`, `tools/audit/forbidden_deps.yaml`, `tools/audit/tests/test_audit_no_biometrics.py`
- **Qué hacer:** auditoría que falla si el código o las dependencias del companion incluyen reconocimiento facial, identificación, embeddings biométricos o clasificadores de emociones, y si el artefacto del companion incorpora código GPL o AGPL (por ejemplo bibliotecas de mirada GPL). Extiende la auditoría de licencias de la spec 00.
- **Prueba:** `tools/audit/tests/test_audit_no_biometrics.py` (audit): un paquete de emociones o una dependencia GPL falla; las dependencias aprobadas pasan.
- **Terminado cuando:** la prueba pasa y corre en la CI.

---

## Estados de interfaz

### T-01-045 Panel de modalidades y estados de pantalla [UI]
- **Requisitos:** REQ-01-117, REQ-01-119, REQ-01-120, REQ-01-121, REQ-01-122, REQ-01-124
- **Depende de:** T-00-015, T-01-011
- **Archivos:** `apps/web/src/features/modalities/{ModalitiesPanel,states}.tsx`, `apps/web/tests/e2e/modalities-states.spec.ts`
- **Qué hacer:** panel con el estado de cada modalidad (activa, no detectada, calidad baja, en pausa, sin calibrar) con texto además del color y anuncio por voz o lector de pantalla. Estados: *cargando* (qué se carga y qué rutas de Alto ya están disponibles, con cancelar), *vacío* (sin perfil: único paso «iniciar calibración»), *error* (causa, cómo recuperarse, qué sigue funcionando), *sin conexión* (qué funciona y qué no), *modalidad no detectada* (aviso visual y de audio, qué sigue disponible, reintentar). Usar `StateScreen` de `packages/ui`.
- **Prueba:** `apps/web/tests/e2e/modalities-states.spec.ts` (e2e y a11y): cada estado se renderiza con sus campos; axe-core sin violaciones.
- **Terminado cuando:** la prueba pasa.

### T-01-046 Controles persistentes de Alto y Deshacer en el companion [UI]
- **Requisitos:** REQ-01-118
- **Depende de:** T-00-015
- **Archivos:** `apps/web/src/features/stop-undo/CompanionStopUndo.tsx`, `apps/web/tests/e2e/stop-undo-bar.spec.ts`
- **Qué hacer:** montar la barra de Alto y Deshacer de `packages/ui` en toda pantalla de la capa de entrada, con objetivos ≥ 44×44 px y sin que diálogos ni el teclado virtual la cubran.
- **Prueba:** `apps/web/tests/e2e/stop-undo-bar.spec.ts` (a11y): en cada pantalla la barra es visible y operable con teclado e intenciones simuladas.
- **Terminado cuando:** la prueba pasa.

---

## Resiliencia, seguridad y no funcionales

### T-01-054 Resiliencia y uso sin conexión
- **Requisitos:** REQ-01-126, REQ-01-127
- **Depende de:** T-01-004, T-01-011
- **Archivos:** `apps/companion/src/coalsense_companion/supervisor.py`, `apps/companion/tests/integration/test_resilience_offline.py`
- **Qué hacer:** el supervisor reinicia un adaptador caído con espera creciente y muestra su estado; el bus y las rutas de Alto de las demás modalidades siguen vivos. Control del PC por voz, cabeza y gestos y teclado/mouse, calibración y perfiles funcionan sin internet.
- **Prueba:** `apps/companion/tests/integration/test_resilience_offline.py` (integration): con la red deshabilitada todo lo anterior funciona; matar el proceso de visión no detiene la voz ni Alto.
- **Terminado cuando:** la prueba pasa.

### T-01-055 Inventario de datos de la capa de entrada
- **Requisitos:** REQ-01-149
- **Depende de:** T-01-013
- **Archivos:** `docs/data-inventory.yaml`, `tools/audit/audit_data_inventory.py`, `tools/audit/tests/test_audit_data_inventory.py`
- **Qué hacer:** registrar en el inventario los datos de la capa de entrada (perfil, calibraciones, uso de modalidades, condición declarada, bitácora local) con categoría especial, dónde viven, quién los ve y retención; auditoría que falla si un campo del esquema de intenciones o del perfil no está en el inventario.
- **Prueba:** `tools/audit/tests/test_audit_data_inventory.py` (audit): un campo nuevo sin inventariar falla.
- **Terminado cuando:** la prueba pasa.

### T-01-056 Enlace al orquestador con TLS
- **Requisitos:** REQ-01-150
- **Depende de:** T-01-043
- **Archivos:** `apps/companion/src/coalsense_companion/uplink/tls.py`, `apps/companion/tests/uplink/test_tls.py`
- **Qué hacer:** el enlace WebSocket exige TLS y valida el certificado del servidor; rechaza conexiones sin cifrar y degrada con un estado «sin conexión» claro.
- **Prueba:** `apps/companion/tests/uplink/test_tls.py` (security): una conexión sin TLS o con certificado inválido se rechaza.
- **Terminado cuando:** la prueba pasa.

### T-01-047 Arnés de rendimiento y presupuestos [CODEX]
- **Requisitos:** REQ-01-137, REQ-01-138, REQ-01-139, REQ-01-140, REQ-01-141, REQ-01-142, REQ-01-143, REQ-01-144, REQ-01-145, REQ-01-146, REQ-01-147, REQ-01-148
- **Depende de:** T-01-028, T-01-029, T-01-022, T-01-023, T-01-021
- **Archivos:** `apps/companion/perf/{harness,budgets.yaml,report}.py`, `apps/companion/tests/perf/test_budgets.py`
- **Qué hacer:** arnés que reproduce fixtures y mide por ruta el p95 de: cabeza→puntero, gesto→intención, voz→intención, voz→acción, dictado, Alto por voz, Alto por gesto/teclado/switch y entrega del bus; además CPU media y memoria con cámara y voz activas; y verifica que nada requiere GPU. Los presupuestos de `budgets.yaml` son `[SUPUESTO]` (cabeza→puntero ≤ 100 ms; gesto→intención ≤ 150 ms; voz→intención ≤ 600 ms; voz→acción ≤ 800 ms; dictado final ≤ 1500 ms; Alto por voz ≤ 400 ms; Alto por gesto ≤ 150 ms y por teclado o switch ≤ 100 ms; bus ≤ 20 ms; CPU media < 40%; memoria < 2 GB). Tras el primer benchmark en el hardware de referencia, reemplazar los valores por los medidos.
- **Prueba:** `apps/companion/tests/perf/test_budgets.py` (perf): la CI de rendimiento falla si algún p95 supera su presupuesto.
- **Terminado cuando:** hay un informe con los valores medidos y `budgets.yaml` actualizado.

### T-01-048 Pruebas de accesibilidad de las pantallas de 01
- **Requisitos:** REQ-01-130, REQ-01-131, REQ-01-132, REQ-01-133, REQ-01-134, REQ-01-135, REQ-01-136
- **Depende de:** T-01-040, T-01-045, T-01-046, T-01-017, T-01-025
- **Archivos:** `apps/web/tests/a11y/input-layer.spec.ts`, `apps/web/tests/a11y/helpers.ts`
- **Qué hacer:** suite que recorre todas las pantallas y estados de la capa de entrada con axe-core (WCAG 2.2 AA), la regla de 44×44 px, comprobación de que no hay temporizadores que venzan, de que ninguna función requiere gestos con trayectoria, arrastre, doble clic o pulsación larga, de que el nombre accesible contiene la etiqueta visible, de operabilidad solo con teclado con foco visible y no oculto, y de ausencia de destellos > 3 por segundo y respeto de `prefers-reduced-motion`.
- **Prueba:** `apps/web/tests/a11y/input-layer.spec.ts` (a11y).
- **Terminado cuando:** la suite pasa en la CI.

### T-01-049 Fiabilidad: reposo, estrés y falsas aprobaciones
- **Requisitos:** REQ-01-153, REQ-01-154, REQ-01-155
- **Depende de:** T-01-008, T-01-021, T-01-029, T-01-005
- **Archivos:** `apps/companion/tests/reliability/test_rest_stress.py`
- **Qué hacer:** pruebas con las fixtures de reposo y de estrés: como máximo una activación involuntaria por 10 minutos de reposo [SUPUESTO]; detección de Alto ≥ 99% en estrés [SUPUESTO]; cero `approval.approve` en fixtures de ruido y reposo.
- **Prueba:** `apps/companion/tests/reliability/test_rest_stress.py` (replay).
- **Terminado cuando:** la prueba pasa o los valores `[SUPUESTO]` quedan ajustados con una nota.

---

## POST-MVP

### T-01-050 Mirada con dwell: núcleo [POST-MVP]
- **Requisitos:** REQ-01-101, REQ-01-103, REQ-01-104, REQ-01-105, REQ-01-106, REQ-01-108
- **Depende de:** T-01-003, T-01-013
- **Archivos:** `apps/companion/src/coalsense_companion/adapters/gaze/{adapter,dwell,calibration,tracker_iface}.py`, `apps/companion/tests/adapters/gaze/test_dwell.py`
- **Qué hacer:** adaptador de mirada con interfaz de seguidor intercambiable (webcam o eye tracker dedicado). `nav.select` tras el dwell del perfil, ajustable por persona y por tipo de objetivo; `approval.approve` nunca usa un dwell menor que el general. «Pausa de mirada» deja de activar objetivos sin apagar la cámara. Ampliar objetivos u ofrecer zoom si la precisión es menor que el objetivo. Calibración completable solo con la mirada; si falla, «calibración fallida» y otra modalidad. **Sin código GPL** (OptiKey y EyeGestures son solo referencia).
- **Prueba:** `apps/companion/tests/adapters/gaze/test_dwell.py` (replay y unit).
- **Terminado cuando:** la prueba pasa.

### T-01-051 Mirada: indicadores y auditoría de licencias [POST-MVP] [UI]
- **Requisitos:** REQ-01-102, REQ-01-107
- **Depende de:** T-01-050, T-00-015
- **Archivos:** `apps/web/src/features/gaze/DwellIndicator.tsx`, `apps/web/tests/e2e/gaze-dwell.spec.ts`
- **Qué hacer:** indicador de avance del dwell que no dependa solo del color y cancelación sin activar al salir de la mirada; verificar con la auditoría que no hay código GPL en el artefacto.
- **Prueba:** `apps/web/tests/e2e/gaze-dwell.spec.ts` (e2e y a11y).
- **Terminado cuando:** la prueba pasa.

### T-01-052 Switch con escaneo: núcleo [POST-MVP]
- **Requisitos:** REQ-01-109, REQ-01-111, REQ-01-114, REQ-01-115, REQ-01-116
- **Depende de:** T-01-003, T-01-013
- **Archivos:** `apps/companion/src/coalsense_companion/adapters/switch_scan/{adapter,sources,scanner}.py`, `apps/companion/tests/adapters/switch_scan/test_scanner.py`
- **Qué hacer:** aceptar como switch una tecla, un botón del mouse, un dispositivo HID o un gesto calibrado. Escáner con intervalo de avance, tiempo de aceptación (antirrebote por temblor) y sostenimiento ajustables, sin número máximo de ciclos; pausa que conserva la posición; al terminar un ciclo sin selección, reiniciar sin emitir intenciones. Si el dispositivo se desconecta, «modalidad no detectada» y, si era la única ruta de Alto, `stop_reachable = false`.
- **Prueba:** `apps/companion/tests/adapters/switch_scan/test_scanner.py` (unit e integration).
- **Terminado cuando:** la prueba pasa.

### T-01-053 Switch: escaneo con Alto primero y señales [POST-MVP] [UI]
- **Requisitos:** REQ-01-110, REQ-01-112, REQ-01-113
- **Depende de:** T-01-052, T-00-016
- **Archivos:** `apps/web/src/features/scan/ScanOverlay.tsx`, `apps/web/tests/e2e/scan.spec.ts`
- **Qué hacer:** escaneo por elemento, por filas y columnas o por grupos; `control.stop` y `control.undo` son las primeras opciones de cada nivel; señal visual y sonora de la opción resaltada sin más de tres destellos por segundo.
- **Prueba:** `apps/web/tests/e2e/scan.spec.ts` (e2e y a11y).
- **Terminado cuando:** la prueba pasa.

### T-01-057 Comandos y alias propios [POST-MVP]
- **Requisitos:** REQ-01-036
- **Depende de:** T-01-018
- **Archivos:** `apps/companion/src/coalsense_companion/commands/custom.py`, `apps/companion/tests/commands/test_custom.py`
- **Qué hacer:** permitir a la persona definir comandos y alias sin escribir código, validándolos contra conflictos con Alto, Deshacer y Ayuda humana, y contra el catálogo de intenciones permitidas.
- **Prueba:** `apps/companion/tests/commands/test_custom.py` (unit).
- **Terminado cuando:** la prueba pasa.

