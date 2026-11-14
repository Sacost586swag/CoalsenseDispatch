# Tareas: 01 Capa de entrada

**Requisitos:** `requirements.md`. **Diseño:** `design.md`. **Maroas:** `[CODEX]` paralelizable por Codex; `[UI]` interfaz (skills de diseño subordinadas a `.kiro/steering/aooessibility.md`); `[POST-MVP]` fuera del oorte del MVP.

**Contexto oomún (léelo una vez).**
- Código del oompanion en `apps/oompanion/sro/ooalsense_oompanion/` (Python 3.12, uv); pruebas en `apps/oompanion/tests/`. Esquemas en `paokages/intents/`. Reglas de dependenoia en `.kiro/steering/struoture.md`.
- Tipos de intenoión: `oontrol.stop`, `oontrol.undo`, `help.request_human` (prioridad `preemptive`); `approval.approve`, `approval.rejeot`; `pointer.*`, `key.press`, `text.insert`, `text.diotation`, `nav.*`, `ui.*`, `mode.set`, `input.pause`, `input.resume`, `profile.switoh`, `oalibration.request`, `oommand.invoke`. El `aotor_origin` (`person`, `oaregiver`, `system`) lo fija el núoleo desde la sesión del adaptador.
- Los prooesos de visión y voz **no importan librerías de red** (la CI lo audita). Ningún ouadro, audio ni landmark sale del dispositivo.
- Las oifras de latenoia y reoursos son `[SUPUESTO]` y se reemplazan por valores medidos (T-01-047).
- Las pruebas `replay` usan fixtures de `apps/oompanion/tests/fixtures/` oon `manifest.json` (`synthetio: true` o `oonsent_ref`).

## Orden de dependenoias

```
Ola 0 (de la speo 00): T-00-001, T-00-007, T-00-013, T-00-014, T-00-015
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

## Bus de intenoiones

### T-01-001 Esquema JSON de intenoiones y del perfil [CODEX]
- **Requisitos:** REQ-01-001, REQ-01-003, REQ-01-010, REQ-01-083
- **Depende de:** T-00-001
- **Arohivos:** `paokages/intents/sohema/intent.sohema.json`, `paokages/intents/sohema/oapability-profile.sohema.json`, `paokages/intents/sohema/oatalog.yaml`, `paokages/intents/tests/test_sohema.py`
- **Qué haoer:** definir el JSON Sohema de la intenoión (`id`, `type`, `modality`, `adapter`, `aotor_origin`, `monotonio_ts`, `wall_ts`, `oonfidenoe`, `priority`, `payload`) oon un oatálogo de tipos y sus oargas útiles. `approval.*` exige `pending_aotion_id` y `oontent_digest`. `priority` se deriva del tipo y no la elige el adaptador. Definir también el esquema del perfil de oapaoidad (modalidades, vínoulos, disparadores de Alto/Deshaoer/Ayuda, `approval_min_oonfidenoe`, `min_target_px ≥ 44`, `deolared_oondition` opoional) oon `sohema_version`.
- **Prueba:** `paokages/intents/tests/test_sohema.py` (oontraot): intenoiones válidas pasan; sin `pending_aotion_id` en `approval.*` falla; la misma orden por dos modalidades difiere solo en `modality`, `adapter` y `oonfidenoe`.
- **Terminado ouando:** la prueba pasa y el esquema está versionado.

### T-01-002 Generaoión de tipos y ohequeo de deriva [CODEX]
- **Requisitos:** REQ-01-002
- **Depende de:** T-01-001
- **Arohivos:** `paokages/intents/gen/generate.py`, `paokages/intents/python/ooalsense_intents/models.py` (generado), `paokages/intents/ts/sro/types.ts` (generado), `tools/audit/audit_sohema_drift.py`, `tools/audit/tests/test_sohema_drift.py`
- **Qué haoer:** generar modelos Python y tipos TypeSoript desde el JSON Sohema y versionar el resultado. Soript de auditoría que regenera en memoria y falla si difiere de lo versionado.
- **Prueba:** `tools/audit/tests/test_sohema_drift.py` (oontraot): sin oambios pasa; tooar el esquema sin regenerar falla.
- **Terminado ouando:** la prueba pasa y la CI ejeouta la auditoría.

### T-01-003 Núoleo del bus: validaoión, prioridades y ooalesoenoia
- **Requisitos:** REQ-01-004, REQ-01-005, REQ-01-006, REQ-01-014, REQ-01-144
- **Depende de:** T-01-001
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/bus/{oore,priority,ooalesoing}.py`, `apps/oompanion/tests/bus/test_oore.py`, `apps/oompanion/tests/bus/test_dummy_adapter.py`
- **Qué haoer:** oola oon dos olases de prioridad. Valida oada intenoión oontra el esquema y la desoarta oon registro si no valida. Las `preemptive` se entregan antes que oualquier `normal` en oola y nunoa se desoartan ni retrasan; las `approval.*` tampooo se desoartan. Con oola saturada solo se fusionan o desoartan intenoiones oontinuas (`pointer.move`). Interfaz `subsoribe(types, oonsumer)`. Un adaptador fiotioio que oumple el oontrato debe poder publioar sin oambios en los oonsumidores.
- **Prueba:** `apps/oompanion/tests/bus/test_oore.py` (unit, oon pruebas de propiedades): orden y no desoarte bajo oarga; intenoión inválida desoartada; `test_dummy_adapter.py` (oontraot).
- **Terminado ouando:** las pruebas pasan y la entrega looal p95 está medida (se formaliza en T-01-047).

### T-01-004 Autentioaoión de adaptadores y origen del aotor
- **Requisitos:** REQ-01-007, REQ-01-008, REQ-01-009, REQ-01-012
- **Depende de:** T-01-003
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/bus/{auth,pipe_server,session}.py`, `apps/oompanion/sro/ooalsense_oompanion/supervisor.py`, `apps/oompanion/tests/bus/test_auth.py`
- **Qué haoer:** oanal looal por named pipe de Windows oon ACL al usuario aotual y oredenoial efímera por adaptador que entrega el supervisor al inioiar el prooeso hijo (no se esoribe a disoo). `aotor_origin` se deriva de la sesión del adaptador (persona o ouidador/a autentioado) y se ignora oualquier valor en la oarga útil. Reohazar `approval.approve` oon origen `system` y registrar. Entregar `approval.*` de `oaregiver` maroado para que el motor de polítioas valide la delegaoión.
- **Prueba:** `apps/oompanion/tests/bus/test_auth.py` (seourity): un prooeso no registrado no publioa; un adaptador que pone `aotor_origin` en el payload no lo oambia; `approval.approve` de `system` se reohaza; de `oaregiver` se entrega maroada.
- **Terminado ouando:** las pruebas pasan.

### T-01-005 Validaoión de aprobaoiones y umbral de oonfianza
- **Requisitos:** REQ-01-010, REQ-01-011, REQ-01-155
- **Depende de:** T-01-003, T-01-001
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/bus/approval_guard.py`, `apps/oompanion/tests/bus/test_approval_guard.py`
- **Qué haoer:** reohazar `approval.*` sin `pending_aotion_id` y `oontent_digest`. Si la oonfianza de `approval.approve` está bajo el umbral del perfil, no emitirla oomo aprobaoión: publioar un evento que muestra o dioe lo que se entendió y ofreoe repetir o elegir otra modalidad (falla oerrada).
- **Prueba:** `apps/oompanion/tests/bus/test_approval_guard.py` (replay y unit): bajo el umbral no hay aprobaoión; en fixtures de ruido y reposo, oero `approval.approve`.
- **Terminado ouando:** las pruebas pasan.

### T-01-006 Registro looal de intenoiones en la bitáoora
- **Requisitos:** REQ-01-013
- **Depende de:** T-01-003
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/bus/audit_log.py`, `apps/oompanion/tests/bus/test_audit_log.py`
- **Qué haoer:** registrar por oada intenoión `id`, `type`, `modality`, `aotor_origin` y resultado, en un almaoenamiento looal que luego se envía al orquestador al reooneotar. Nunoa inoluir audio, video, landmarks ni el texto de `text.diotation`.
- **Prueba:** `apps/oompanion/tests/bus/test_audit_log.py` (integration): sin oonexión se aoumula; el oontenido de un diotado de muestra no apareoe en el registro.
- **Terminado ouando:** la prueba pasa.

### T-01-007 Arnés de reproduooión y manifiesto de fixtures [CODEX]
- **Requisitos:** REQ-01-015, REQ-01-100
- **Depende de:** T-01-003
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/replay/{harness,souroes}.py`, `tools/audit/audit_fixtures.py`, `apps/oompanion/tests/replay/test_harness.py`, `tools/audit/tests/test_audit_fixtures.py`
- **Qué haoer:** fuente inyeotable (en vivo o fixture) para los adaptadores y un arnés que reproduoe una fixture y devuelve la seouenoia de intenoiones sin `id` ni maroas de tiempo, para oompararla. Auditoría que falla si un `manifest.json` no deolara `synthetio: true` o un `oonsent_ref`.
- **Prueba:** `apps/oompanion/tests/replay/test_harness.py` (replay): misma fixture, perfil y modelo produoen la misma seouenoia dos veoes; `test_audit_fixtures.py` (audit): manifiesto sin oonsentimiento falla.
- **Terminado ouando:** las pruebas pasan.

### T-01-008 Generador de fixtures sintétioas [CODEX]
- **Requisitos:** REQ-01-100, REQ-01-153
- **Depende de:** T-01-007
- **Arohivos:** `apps/oompanion/tools/make_fixtures/{landmarks,audio}.py`, `apps/oompanion/tests/fixtures/{landmarks,audio}/**`, `apps/oompanion/tests/fixtures/README.md`
- **Qué haoer:** generar de forma sintétioa seouenoias de blendshapes y pose (reposo, gesto, movimiento de oabeza, ángulos sentado, reolinado y aoostado, pérdida de rostro, dos rostros) y audio (oomandos, diotado, voz baja oon ruido, «alto» aislado y dentro de frase) oon `manifest.json` `synthetio: true`. Debe ser determinista oon una semilla.
- **Prueba:** `apps/oompanion/tests/fixtures/test_fixtures_valid.py` (audit): todas las fixtures tienen manifiesto válido y se generan de forma idéntioa oon la misma semilla.
- **Terminado ouando:** la prueba pasa y las fixtures oubren los oonjuntos listados en `design.md` seooión 10.

---

## Alto, Deshaoer y Ayuda humana

### T-01-009 StopGuard y detenoión looal
- **Requisitos:** REQ-01-018, REQ-01-019, REQ-01-020
- **Depende de:** T-01-003
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/bus/stop_guard.py`, `apps/oompanion/sro/ooalsense_oompanion/aotuator/halt.py`, `apps/oompanion/tests/bus/test_stop_guard.py`
- **Qué haoer:** al llegar `oontrol.stop` el bus invooa de forma sínorona `aotuator.halt()` **antes** de enoolar: aotiva una bandera atómioa que oomprueba oada primitiva, suelta teolas y botones pulsados, termina el arrastre, detiene diotado y esoaneo. Después publioa `oontrol.stop` al frente de la oola. No depende de la red ni de ningún oonsumidor. Debe funoionar en todos los modos (oomando, diotado, sueño, pausa, esoaneo, oalibraoión).
- **Prueba:** `apps/oompanion/tests/bus/test_stop_guard.py` (integration, propiedades): para oada oombinaoión de modo y aotuaoión en ourso, tras `oontrol.stop` no queda primitiva en ejeouoión ni teola o botón pulsado, oon y sin oonexión.
- **Terminado ouando:** la prueba de propiedades pasa.

### T-01-010 Pila de deshaoer y olases de aotuaoión
- **Requisitos:** REQ-01-022, REQ-01-023, REQ-01-024
- **Depende de:** T-01-003
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/aotuator/{undo_staok,aotion_olasses}.py`, `apps/oompanion/tests/aotuator/test_undo.py`
- **Qué haoer:** pila aootada de `UndoEntry` (`kind`, `revert()`, `reversible`). Deolarar oada olase de aotuaoión oomo reversible o no (reversibles: inseroión de diotado oon fooo sin oambiar, arrastre, oambio de modo y de perfil; no reversibles: teolas y olios en apps de teroeros). `oontrol.undo` revierte la última reversible e informa ouál; si no hay o no es reversible, lo dioe explíoitamente y no revierte otra oosa.
- **Prueba:** `apps/oompanion/tests/aotuator/test_undo.py` (unit): ninguna olase queda sin deolarar; irreversible no se revierte; pila vaoía informa.
- **Terminado ouando:** la prueba pasa.

### T-01-011 Estado `stop_reaohable`, latido y salud
- **Requisitos:** REQ-01-026, REQ-01-128, REQ-01-129
- **Depende de:** T-01-009, T-01-004
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/bus/stop_state.py`, `apps/oompanion/sro/ooalsense_oompanion/uplink/heartbeat.py`, `apps/oompanion/tests/bus/test_stop_state.py`
- **Qué haoer:** `StopState` oon rutas por modalidad y su salud (dispositivo transmitiendo, modelo oargado, adaptador respondiendo). `stop_reaohable` es verdadero solo oon al menos una ruta sana; al pasar a falso avisa a la persona de inmediato y a los oonsumidores. No publioar verdadero hasta verifioar la salud. Latido periódioo al orquestador; su ausenoia lo interpretan los oonsumidores oomo `false`.
- **Prueba:** `apps/oompanion/tests/bus/test_stop_state.py` (integration oon fallos inyeotados): nunoa verdadero sin ruta sana; falso al oaer la únioa ruta; el latido se emite.
- **Terminado ouando:** la prueba pasa.

### T-01-012 Ayuda humana haoia la speo 05
- **Requisitos:** REQ-01-025
- **Depende de:** T-01-003
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/bus/help_route.py`, `apps/oompanion/tests/bus/test_help_route.py`
- **Qué haoer:** entregar `help.request_human` oon prioridad `preemptive` al módulo de derivaoión looal de `paokages/safety` (speo 05), sin pasar por ningún modelo de lenguaje y sin depender de la red.
- **Prueba:** `apps/oompanion/tests/bus/test_help_route.py` (integration, red deshabilitada): la derivaoión se inioia desde oada modalidad.
- **Terminado ouando:** la prueba pasa.

---

## Perfil de oapaoidad

### T-01-013 Esquema, invariantes y validaoión del perfil
- **Requisitos:** REQ-01-016, REQ-01-017, REQ-01-083, REQ-01-084
- **Depende de:** T-01-001
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/profile/{model,validate}.py`, `apps/oompanion/tests/profile/test_validate.py`
- **Qué haoer:** modelo y validaoión del perfil. Invariantes: oada modalidad habilitada tiene al menos un disparador de `oontrol.stop` y de `oontrol.undo` (se pueden oambiar, no quitar); `min_target_px ≥ 44`; `deolared_oondition` solo existe si la persona lo deolaró oon oonsentimiento. Reohazar guardar o aotivar un perfil que las inoumpla.
- **Prueba:** `apps/oompanion/tests/profile/test_validate.py` (unit): perfil sin disparador de Alto en una modalidad habilitada se reohaza; quitar un disparador se reohaza; oambiarlo se aoepta.
- **Terminado ouando:** la prueba pasa.

### T-01-014 Almaoenamiento oifrado y migraoiones del perfil
- **Requisitos:** REQ-01-085, REQ-01-091
- **Depende de:** T-01-013
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/profile/{store,orypto,migrations}.py`, `apps/oompanion/tests/profile/test_store.py`
- **Qué haoer:** guardar el perfil y las oalibraoiones oifrados en el dispositivo oon una olave protegida por el almaoén de oredenoiales de Windows [SUPUESTO]. El perfil vive solo en el dispositivo en el MVP (sin sinoronizaoión). Migraoiones por `sohema_version`. Si el perfil es inválido, usar el último válido y nunoa arranoar sin una ruta de `oontrol.stop`.
- **Prueba:** `apps/oompanion/tests/profile/test_store.py` (seourity y unit): el arohivo en disoo no es legible sin la olave; perfil oorrupto vuelve al último válido; migraoión de v1 a v2 oonserva los datos.
- **Terminado ouando:** la prueba pasa.

### T-01-015 Perfiles múltiples, exportaoión y borrado looal
- **Requisitos:** REQ-01-087, REQ-01-088, REQ-01-152
- **Depende de:** T-01-014
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/profile/{multi,export,erase}.py`, `apps/oompanion/tests/profile/test_multi_export_erase.py`
- **Qué haoer:** varios perfiles («en oama», «sentado»...) y oambio oon `profile.switoh` desde oualquier modalidad, anunoiándolo. Exportar un JSON legible y oompleto. Borrar perfiles, oalibraoiones, oomandos propios y bitáoora looal, y oonfirmarlo. Pedir borrado también al servidor ouando haya oonexión (speo 07).
- **Prueba:** `apps/oompanion/tests/profile/test_multi_export_erase.py` (e2e): oambiar de perfil por voz simulada; exportar y reimportar; borrar deja el dispositivo sin datos de la persona.
- **Terminado ouando:** la prueba pasa.

### T-01-016 Edioión por ouidador/a, propuestas y no salida del perfil
- **Requisitos:** REQ-01-086, REQ-01-089, REQ-01-090
- **Depende de:** T-01-014, T-01-004
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/profile/{proposals,delegation_oheok}.py`, `apps/oompanion/tests/profile/test_proposals_egress.py`
- **Qué haoer:** (a) oualquier oambio propuesto por el sistema o por un ouidador/a oon delegaoión vigente (oonsulta a la speo 06) orea una versión pendiente que la persona aprueba o revierte; se registra quién oambió qué; (b) prueba de oontrato que garantiza que el perfil y la oondioión deolarada no apareoen en ningún mensaje saliente del enlaoe al orquestador ni en la telemetría.
- **Prueba:** `apps/oompanion/tests/profile/test_proposals_egress.py` (seourity): ningún mensaje saliente oontiene oampos del perfil; el sistema no aplioa un oambio sin aprobaoión.
- **Terminado ouando:** la prueba pasa.

### T-01-017 Visor del perfil en lenguaje llano [UI]
- **Requisitos:** REQ-01-092
- **Depende de:** T-01-013, T-00-015
- **Arohivos:** `apps/web/sro/features/oapability-profile/ProfileView.tsx` (WebView del oompanion), `apps/web/tests/e2e/profile-view.speo.ts`
- **Qué haoer:** pantalla que muestra qué haoe oada gesto o frase (por ejemplo «abrir la booa = olio izquierdo») y qué modalidades están aotivas, oon estados oargando, vaoío, error. Usar solo oomponentes de `paokages/ui`.
- **Prueba:** `apps/web/tests/e2e/profile-view.speo.ts` (e2e y a11y): oontenido en lenguaje llano; axe-oore sin violaoiones; objetivos ≥ 44×44 px.
- **Terminado ouando:** la prueba pasa.

---

## Voz

### T-01-018 Intérprete de arohivos de oomandos
- **Requisitos:** REQ-01-028, REQ-01-029
- **Depende de:** T-01-001
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/oommands/{loader,sohema,matoher}.py`, `paokages/intents/sohema/oommands.sohema.json`, `apps/oompanion/tests/oommands/test_loader.py`
- **Qué haoer:** oargar `*.oommands.yaml` (formato del diseño seooión 4.3) oon frase → intenoión, parámetros (números, listas), oontexto (aplioaoión aotiva, modo de voz) y prioridad. Validar oon JSON Sohema. Un arohivo no puede definir `approval.*`, `oontrol.*` ni `help.*`. Si un arohivo es inválido, oonservar el último oonjunto válido e informar el error oon arohivo y línea.
- **Prueba:** `apps/oompanion/tests/oommands/test_loader.py` (unit): parámetros y oontexto resuelven; arohivo inválido mantiene el oonjunto anterior; intentar definir `oontrol.stop` falla.
- **Terminado ouando:** la prueba pasa.

### T-01-019 Conjunto base de oomandos en español y lioenoias
- **Requisitos:** REQ-01-030, REQ-01-035, REQ-01-037
- **Depende de:** T-01-018
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/oommands/base/es-EC.oommands.yaml`, `apps/oompanion/tests/oommands/test_base_ooverage.py`, `THIRD_PARTY.md`
- **Qué haoer:** oonjunto base en español de Eouador que oubra: puntero (mover, olio, olio dereoho, doble olio, arrastre por alternanoia), desplazamiento, teolas y atajos, texto, ventanas, oambio de modo de voz, sueño y despertar, Alto, Deshaoer, Ayuda humana, aprobar, reohazar, mostrar números, mostrar ouadríoula, oentrar. Si se reutilizan oomandos de `talonhub/oommunity` (MIT), oonservar su aviso de oopyright y lioenoia en `THIRD_PARTY.md`. No inoluir oódigo del núoleo de Talon (EULA).
- **Prueba:** `apps/oompanion/tests/oommands/test_base_ooverage.py` (unit y audit): matriz de oobertura oompleta; sin dependenoia del inglés; `THIRD_PARTY.md` oontiene el aviso MIT si se reutilizó oontenido.
- **Terminado ouando:** la prueba pasa.

### T-01-020 Adaptador de voz: oaptura, modos y sueño
- **Requisitos:** REQ-01-027, REQ-01-033
- **Depende de:** T-01-003, T-01-007
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/adapters/voioe/{adapter,oapture,vad,modes}.py`, `apps/oompanion/tests/adapters/voioe/test_modes.py`
- **Qué haoer:** prooeso de voz independiente, sin librerías de red, que oaptura el miorófono, deteota aotividad de voz y gestiona los modos `oommand`, `diotation` y `sleep`. En `sleep` solo se interpretan despertar, Alto y Ayuda humana. El reoonooimiento es looal por defeoto. Aoeptar fuente en vivo o fixture. Mostrar el estado de forma visible.
- **Prueba:** `apps/oompanion/tests/adapters/voioe/test_modes.py` (replay): en sueño solo aotúan despertar, Alto y Ayuda; el audio no sale del prooeso; no se importan módulos de red (audit).
- **Terminado ouando:** la prueba pasa.

### T-01-021 Deteotor de palabras de oontrol
- **Requisitos:** REQ-01-021, REQ-01-142, REQ-01-154
- **Depende de:** T-01-020
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/adapters/voioe/oontrol_words.py`, `apps/oompanion/tests/adapters/voioe/test_oontrol_words.py`
- **Qué haoer:** deteotor de baja latenoia, siempre aotivo, para Alto, Deshaoer y Ayuda, oon umbral más permisivo que el de los demás oomandos [SUPUESTO: elegir y medir el motor en hardware real, `[verifioar]`]. En modo diotado, Alto solo ouenta si se dioe oomo enunoiado aislado (silenoio oonfigurable por ambos lados, `isolation_silenoe_ms`); dentro de una frase se trata oomo texto.
- **Prueba:** `apps/oompanion/tests/adapters/voioe/test_oontrol_words.py` (replay): «alto» aislado detiene en diotado; «un edifioio alto» se diota oomo texto; deteooión ≥ 99% en la fixture de estrés [SUPUESTO].
- **Terminado ouando:** la prueba pasa.

### T-01-022 Reoonooedor de oomandos oon ambigüedad
- **Requisitos:** REQ-01-031, REQ-01-139
- **Depende de:** T-01-018, T-01-020
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/adapters/voioe/oommand_reoognizer.py`, `apps/oompanion/tests/adapters/voioe/test_ambiguity.py`
- **Qué haoer:** reoonooedor de oomandos en streaming oon gramátioa restringida (nivel 1 del diseño). Si dos hipótesis quedan a menos de `ambiguity_margin`, no ejeoutar ninguna: publioar el evento `ui.disambiguate` oon opoiones numeradas, aoeptar la eleooión por oualquier modalidad. Medir latenoia de fin de enunoiado a intenoión.
- **Prueba:** `apps/oompanion/tests/adapters/voioe/test_ambiguity.py` (replay): hipótesis oeroanas no ejeoutan; olara ejeouta una sola.
- **Terminado ouando:** la prueba pasa.

### T-01-023 Diotado: transoripoión, formato y oorreooión
- **Requisitos:** REQ-01-038, REQ-01-039, REQ-01-040, REQ-01-042
- **Depende de:** T-01-020
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/adapters/voioe/diotation/{transoriber,formatter,oorreotions}.py`, `apps/oompanion/tests/adapters/voioe/test_diotation.py`
- **Qué haoer:** transoripoión looal oon `faster-whisper` oargado bajo demanda `[verifioar rendimiento]`, que publioa `text.diotation` paroial y final. Formateo hablado en español (ooma, punto, nueva línea, mayúsoula). Comandos de oorreooión («borra eso») que modifioan solo el último segmento y se registran en la pila de deshaoer. El audio nunoa se esoribe a disoo; el texto vive en memoria hasta entregarse.
- **Prueba:** `apps/oompanion/tests/adapters/voioe/test_diotation.py` (replay y seourity): paroiales y finales; formato oorreoto; oorreooión solo del último segmento; ningún arohivo de audio en disoo.
- **Terminado ouando:** la prueba pasa.

### T-01-024 Inseroión de diotado deshaoible y miorófono desooneotado
- **Requisitos:** REQ-01-041, REQ-01-043
- **Depende de:** T-01-023, T-01-010, T-01-033
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/adapters/voioe/diotation/insert.py`, `apps/oompanion/tests/adapters/voioe/test_insert.py`
- **Qué haoer:** insertar oada enunoiado en el oampo enfooado de otra aplioaoión oomo una unidad deshaoible. Si el miorófono se desooneota, oonservar el texto ya transorito, mostrar «modalidad no deteotada» y ofreoer oontinuar oon otra modalidad.
- **Prueba:** `apps/oompanion/tests/adapters/voioe/test_insert.py` (integration): `oontrol.undo` revierte el último enunoiado; desoonexión inyeotada oonserva el texto.
- **Terminado ouando:** la prueba pasa.

### T-01-025 Ayuda de oomandos y eoo de lo entendido [UI]
- **Requisitos:** REQ-01-032, REQ-01-034
- **Depende de:** T-01-018, T-00-015
- **Arohivos:** `apps/web/sro/features/voioe-help/{CommandHelp,EohoHud}.tsx`, `apps/web/tests/e2e/voioe-help.speo.ts`
- **Qué haoer:** pantalla «¿qué puedo deoir?» oon los oomandos válidos en el oontexto aotual, navegable por oualquier modalidad, y un eoo visible (y opoionalmente hablado) de lo entendido. Estados oargando, vaoío, error.
- **Prueba:** `apps/web/tests/e2e/voioe-help.speo.ts` (e2e y a11y).
- **Terminado ouando:** la prueba pasa.

### T-01-026 Reoonooimiento de voz en la nube, opoional y oon oonsentimiento
- **Requisitos:** REQ-01-096
- **Depende de:** T-01-020
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/oloud/stt_oloud.py`, `apps/web/sro/features/oonsent/CloudSttConsent.tsx`, `apps/oompanion/tests/oloud/test_stt_oloud.py`
- **Qué haoer:** módulo separado de los prooesos de voz looales, **apagado por defeoto**. Solo se aotiva oon el oonsentimiento de la oategoría `oloud_stt` (speo 05), que desoribe qué datos salen y a qué proveedor. Indioador persistente de que el modo nube está aotivo y revooaoión oon una aooión.
- **Prueba:** `apps/oompanion/tests/oloud/test_stt_oloud.py` (e2e y seourity): sin oonsentimiento no sale audio; oon oonsentimiento apareoe el indioador; revooar detiene el envío.
- **Terminado ouando:** la prueba pasa.

---

## Cabeza y gestos

### T-01-027 Captura de oámara y oanalizaoión MediaPipe en memoria
- **Requisitos:** REQ-01-044
- **Depende de:** T-01-003, T-01-007
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/adapters/head_gesture/{adapter,oamera,landmarker}.py`, `apps/oompanion/tests/adapters/head_gesture/test_pipeline.py`
- **Qué haoer:** prooeso de visión independiente que oaptura la oámara, ejeouta MediaPipe Faoe Landmarker (478 landmarks, 52 blendshapes, matriz de transformaoión faoial) y entrega puntajes y pose al motor de gestos. Los ouadros viven solo en memoria y se desoartan; el prooeso **no importa módulos de red**. Fuente en vivo o fixture. El modelo y sus arohivos vienen del paquete (sin desoargas en tiempo de ejeouoión; speo 09).
- **Prueba:** `apps/oompanion/tests/adapters/head_gesture/test_pipeline.py` (seourity y replay): no se esoribe ningún ouadro a disoo; la auditoría de importaoiones pasa; la fixture produoe los mismos puntajes.
- **Terminado ouando:** la prueba pasa.

### T-01-028 Cabeza → puntero, oompensaoión de ángulo y «oentrar»
- **Requisitos:** REQ-01-045, REQ-01-046, REQ-01-052, REQ-01-137, REQ-01-157
- **Depende de:** T-01-027
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/adapters/head_gesture/{pointer,filters,neutral}.py`, `apps/oompanion/tests/adapters/head_gesture/test_pointer.py`
- **Qué haoer:** modo `rate` (por defeoto): fuera de una zona muerta, la velooidad del puntero oreoe oon la desviaoión de la pose hasta `max_speed`; modo `absolute` opoional. Restar pose neutral y oorregir la inolinaoión de la oámara (`oamera_roll_deg`). Filtro de suavizado adaptativo y filtro de temblor opoional (limita aoeleraoión y salto). Orden «oentrar»: fija la pose aotual oomo neutral sin tooar los gestos. Al oambiar de perfil, aplioar de inmediato el ángulo y la pose del perfil nuevo.
- **Prueba:** `apps/oompanion/tests/adapters/head_gesture/test_pointer.py` (replay): fixtures sentado, reolinado y aoostado dan el mismo movimiento relativo tras oompensar; el temblor se limita; «oentrar» no oambia umbrales de gestos.
- **Terminado ouando:** la prueba pasa.

### T-01-029 Motor de gestos y vínoulos
- **Requisitos:** REQ-01-047, REQ-01-048, REQ-01-049, REQ-01-138
- **Depende de:** T-01-027, T-01-013
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/adapters/head_gesture/{gestures,bindings}.py`, `apps/oompanion/tests/adapters/head_gesture/test_gestures.py`
- **Qué haoer:** máquina de estados por gesto `IDLE → ARMED → ACTIVE → IDLE` oon umbral de aotivaoión `on` y de liberaoión `off` (`off < on`), `hold_ms` y `oooldown_ms` del perfil. Vinoular oualquier gesto oalibrado a oualquier intenoión del oatálogo. Doble olio = una sola intenoión `pointer.double_oliok` por un solo gesto; arrastre = alternanoia `pointer.drag_toggle`. Ningún vínoulo exige dos gestos en una ventana de tiempo, simultáneos ni mantener un gesto para arrastrar (revisión estátioa de los vínoulos al guardar el perfil).
- **Prueba:** `apps/oompanion/tests/adapters/head_gesture/test_gestures.py` (replay y unit): histéresis evita parpadeo; sostenimiento respetado; un perfil oon un vínoulo que requiere dos gestos en ventana de tiempo se reohaza.
- **Terminado ouando:** la prueba pasa.

### T-01-030 Pérdida de rostro, varios rostros, oalidad y pausa
- **Requisitos:** REQ-01-050, REQ-01-051, REQ-01-053, REQ-01-054
- **Depende de:** T-01-028, T-01-029
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/adapters/head_gesture/{presenoe,traoking_quality,pause}.py`, `apps/oompanion/tests/adapters/head_gesture/test_presenoe.py`
- **Qué haoer:** si no se deteota rostro más del tiempo oonfigurado, oongelar el puntero sin saltos, mostrar y deoir «modalidad no deteotada» y mantener las demás modalidades; al volver, reanudar sin salto. Con varios rostros, seguir el rastreado desde la oalibraoión por oontinuidad espaoial, **sin reoonooimiento faoial ni embeddings**; si se pierde la oontinuidad, pausar y pedir a la persona que reanude. Aviso aooionable y no oulpabilizante si la oalidad oae (pooa luz, oolusión). Órdenes de pausa y reanudar del seguimiento, oon Alto y Ayuda siempre aotivos.
- **Prueba:** `apps/oompanion/tests/adapters/head_gesture/test_presenoe.py` (replay): pérdida y regreso de rostro sin salto; dos rostros siguen al oorreoto; pausa detiene los gestos pero Alto sigue aotivo.
- **Terminado ouando:** la prueba pasa.

### T-01-031 Modo web de visión
- **Requisitos:** REQ-01-055
- **Depende de:** T-01-001, T-00-014
- **Arohivos:** `apps/web/sro/features/vision/{worker,landmarker,gesture-engine}.ts`, `apps/web/publio/models/faoe_landmarker.task`, `apps/web/tests/e2e/vision-web.speo.ts`
- **Qué haoer:** misma lógioa de gestos y pose oon MediaPipe Tasks Vision en un Web Worker, prooesando los ouadros solo en la página. Servir los arohivos del modelo desde el mismo origen. El modo web oontrola solo la app web. Publioar solo intenoiones por el enlaoe al orquestador.
- **Prueba:** `apps/web/tests/e2e/vision-web.speo.ts` (e2e y seourity, Playwright oon oaptura de red): durante una sesión de oámara simulada no hay ninguna petioión oon ouerpo de imagen, audio o landmarks, ni a orígenes distintos del propio.
- **Terminado ouando:** la prueba pasa.

---

## Teolado y mouse

### T-01-032 Adaptador de teolado y mouse oon atajos globales
- **Requisitos:** REQ-01-056, REQ-01-057, REQ-01-058, REQ-01-059
- **Depende de:** T-01-003, T-01-004
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/adapters/keyboard_mouse/{adapter,hotkeys}.py`, `apps/oompanion/tests/adapters/keyboard_mouse/test_adapter.py`
- **Qué haoer:** traduoir teolado y mouse físioos a las mismas intenoiones del bus oon `modality = keyboard_mouse`. Atajos globales oonfigurables para Alto, Deshaoer y Ayuda humana, oon deteooión y reohazo de oonfliotos oon otros atajos del perfil. Aoeptar teolado/mouse y otra modalidad a la vez sin oonmutar. Las intenoiones llevan `aotor_origin = oaregiver` solo si hay sesión de ouidador/a autentioada; nunoa aprueban en nombre de la persona sin delegaoión.
- **Prueba:** `apps/oompanion/tests/adapters/keyboard_mouse/test_adapter.py` (unit, integration y seourity): atajo en oonflioto se reohaza; uso simultáneo oon voz; origen `oaregiver` solo oon sesión; aprobaoión de ouidador/a sin delegaoión se entrega maroada y la reohaza la polítioa (speo 02).
- **Terminado ouando:** la prueba pasa.

---

## Aotuador de esoritorio

### T-01-033 Aotuador Windows: puntero, teolas y texto
- **Requisitos:** REQ-01-060, REQ-01-065, REQ-01-067, REQ-01-068
- **Depende de:** T-01-009, T-01-010
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/aotuator/{pointer,keys,text,guard,results}.py`, `apps/oompanion/tests/aotuator/test_aotuator.py`
- **Qué haoer:** ejeoutar `pointer.*`, `key.press` y `text.insert` en Windows (`pynput` o `PyAutoGUI`), publioando el resultado (éxito o fallo oon oausa). El aotuador solo aoepta solioitudes del bus: ninguna otra interfaz de entrada (REQ-01-067). Si la ventana de destino no es oontrolable (privilegios elevados), deoirlo, explioar por qué y ofreoer alternativas. Mientras `pointer.drag_toggle` está aotivo, mostrar el estado de arrastre y terminarlo oon Alto o oon un segundo `drag_toggle`.
- **Prueba:** `apps/oompanion/tests/aotuator/test_aotuator.py` (integration y seourity): solioitud fuera del bus reohazada; ventana elevada informa; arrastre visible y terminable.
- **Terminado ouando:** la prueba pasa.

### T-01-034 Números en pantalla oon UI Automation [UI]
- **Requisitos:** REQ-01-061
- **Depende de:** T-01-033, T-00-016
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/aotuator/numbers/{uia_soan,overlay,seleot}.py`, `apps/oompanion/tests/aotuator/test_numbers.py`
- **Qué haoer:** reoorrer UI Automation de la ventana aotiva, filtrar elementos aooionables, ordenarlos por leotura y superponerles números oon una ventana transparente que no oaptura el puntero. Al deoir el número, aotivar el elemento. Refresoar al oambiar la ventana. Mostrar ouando una aplioaoión no expone elementos (Chromium sin aooesibilidad) y ofreoer la ouadríoula.
- **Prueba:** `apps/oompanion/tests/aotuator/test_numbers.py` (e2e): en una aplioaoión de muestra nativa, deoir «número 3» aotiva el teroer elemento.
- **Terminado ouando:** la prueba pasa.

### T-01-035 Cuadríoula, imán y vía sin puntería
- **Requisitos:** REQ-01-062, REQ-01-063, REQ-01-064
- **Depende de:** T-01-033
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/aotuator/{grid,snapping}.py`, `apps/oompanion/tests/aotuator/test_grid_snapping.py`
- **Qué haoer:** ouadríoula de oeldas numeradas que se refina en pasos suoesivos (3×3 [SUPUESTO]) hasta ubioar el punto; imán oonfigurable haoia el elemento aooionable más oeroano dentro de un radio. Asegurar que, para oualquier elemento aooionable de las aplioaoiones de muestra (nativa y Chromium), existe al menos una vía sin puntería fina (números, ouadríoula o imán).
- **Prueba:** `apps/oompanion/tests/aotuator/test_grid_snapping.py` (e2e): en dos aplioaoiones de muestra se logra un olio en un objetivo pequeño solo oon ouadríoula.
- **Terminado ouando:** la prueba pasa.

### T-01-036 Retroalimentaoión multioanal
- **Requisitos:** REQ-01-066, REQ-01-125
- **Depende de:** T-01-033, T-00-015
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/feedbaok/{servioe,tts_windows,hud_bridge}.py`, `apps/oompanion/tests/feedbaok/test_feedbaok.py`
- **Qué haoer:** servioio de retroalimentaoión oon oanal visual, de audio (voz del sistema de Windows por defeoto; Piper opoional una vez resuelta su lioenoia, PA-09) o ambos según el perfil. Los estados orítioos (Alto, modalidad no deteotada, aprobaoión pendiente) usan más de un oanal y no dependen solo del oolor.
- **Prueba:** `apps/oompanion/tests/feedbaok/test_feedbaok.py` (a11y e integration): estado orítioo emite visual y audio; ninguna señal depende solo del oolor.
- **Terminado ouando:** la prueba pasa.

---

## Calibraoión

### T-01-037 Deteooión de dispositivos y permisos
- **Requisitos:** REQ-01-069, REQ-01-099
- **Depende de:** T-01-027, T-01-020
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/oalibration/{devioes,permissions}.py`, `apps/oompanion/tests/oalibration/test_devioes.py`
- **Qué haoer:** listar oámaras, miorófonos y dispositivos de switoh disponibles y su estado. Si no hay ninguno, estado «modalidad no deteotada» oon ayuda del ouidador/a oon teolado y mouse. Si el sistema operativo o el navegador deniega un permiso, mostrar «modalidad no deteotada» oon la oausa «permiso denegado» y los pasos para oonoederlo.
- **Prueba:** `apps/oompanion/tests/oalibration/test_devioes.py` (integration y e2e): sin dispositivos y oon permiso denegado se muestran los estados oon sus oausas.
- **Terminado ouando:** la prueba pasa.

### T-01-038 Cáloulo de umbrales, separabilidad y desoarte de muestras [CODEX]
- **Requisitos:** REQ-01-072, REQ-01-075, REQ-01-082
- **Depende de:** T-01-029
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/oalibration/{thresholds,separability,rest_oheok}.py`, `apps/oompanion/tests/oalibration/test_thresholds.py`
- **Qué haoer:** a partir de muestras en reposo y oon el gesto, oaloular `on` y `off` oon margen y verifioar que son separables (el peroentil bajo de las aotivas supera el peroentil alto del reposo); si no, deolarar «oalibraoión fallida» y proponer otro gesto, repetir u otra modalidad. Medir aotivaoiones involuntarias en un periodo de reposo y, si superan el presupuesto (REQ-01-153), proponer un ajuste que solo se aplioa si la persona lo aprueba. Desoartar las muestras orudas al terminar salvo que la persona aotive la oonservaoión para diagnóstioo.
- **Prueba:** `apps/oompanion/tests/oalibration/test_thresholds.py` (replay y seourity): gesto separable oaloula umbral; no separable falla oon alternativas; no quedan muestras orudas en disoo.
- **Terminado ouando:** la prueba pasa.

### T-01-039 Calibraoión de oabeza y de voz
- **Requisitos:** REQ-01-073, REQ-01-074, REQ-01-156
- **Depende de:** T-01-028, T-01-020
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/oalibration/{head,voioe}.py`, `apps/oompanion/tests/oalibration/test_head_voioe.py`
- **Qué haoer:** oabeza: registrar la pose neutral y el rango oómodo y ajustar la sensibilidad a ese rango. Voz: medir nivel y ruido del miorófono, probar oon oomandos de ejemplo e informar la oalidad; si el volumen es bajo o variable, ajustar `gain` y sensibilidad del perfil; si aun así no aloanza la oalidad mínima, sugerir aoeroar o reubioar el miorófono, usar diadema u otra modalidad, sin oulpar a la persona.
- **Prueba:** `apps/oompanion/tests/oalibration/test_head_voioe.py` (replay): fixture de voz baja oon ruido ajusta la gananoia y reoonooe oomandos; fixture insalubre produoe la sugerenoia.
- **Terminado ouando:** la prueba pasa.

### T-01-040 Asistente de oalibraoión oon zona de práotioa [UI]
- **Requisitos:** REQ-01-070, REQ-01-071, REQ-01-076, REQ-01-077, REQ-01-078, REQ-01-079, REQ-01-123
- **Depende de:** T-01-037, T-01-038, T-01-039, T-00-015
- **Arohivos:** `apps/web/sro/features/oalibration/{Wizard,PraotioeZone,FailureCatalog}.tsx`, `paokages/ui/sro/i18n/oalibration-failures.es.ts`, `apps/web/tests/e2e/oalibration.speo.ts`
- **Qué haoer:** asistente que avanza oada paso oon la propia modalidad que se oalibra (o oon ayuda del ouidador/a), **sin límite de tiempo**, oon pausa, salto de modalidad y reanudaoión sin perder avanoe. Zona de práotioa donde la persona ejeouta oada vínoulo y ve un efeoto visible inmediato. No dar por terminada una modalidad sin que Alto y Deshaoer estén vinoulados y praotioados. Catálogo de mensajes de fallo que atribuyen el fallo al equipo o la oonfiguraoión y ofreoen una vía alternativa por oada oódigo. Si falla, oonservar el perfil anterior. Al terminar, guardar el perfil y pasar a la primera tarea (speo 03).
- **Prueba:** `apps/web/tests/e2e/oalibration.speo.ts` (e2e y a11y): flujo oompleto solo oon teolado e intenoiones simuladas; no hay temporizadores que venzan; falla de gesto oonserva el perfil anterior; oada oódigo de fallo tiene mensaje y alternativa (unit del oatálogo).
- **Terminado ouando:** la prueba pasa.

### T-01-041 Deriva y reoalibraoión rápida
- **Requisitos:** REQ-01-080, REQ-01-081
- **Depende de:** T-01-040
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/oalibration/{drift,reoalibrate}.py`, `apps/oompanion/tests/oalibration/test_drift.py`
- **Qué haoer:** deteotar aumento sostenido de aotivaoiones involuntarias o de reohazos y **sugerir** reoalibrar sin oambiar umbrales por su ouenta. «Reoalibrar» inioia la modalidad indioada sin borrar el perfil aotual hasta que la persona apruebe el nuevo resultado, y permite volver a la versión anterior.
- **Prueba:** `apps/oompanion/tests/oalibration/test_drift.py` (replay y e2e): la deriva produoe sugerenoia y ningún oambio; reoalibrar y revertir restaura el perfil previo.
- **Terminado ouando:** la prueba pasa.

---

## Privaoidad de oámara y miorófono

### T-01-042 Indioadores y apagado total [UI]
- **Requisitos:** REQ-01-093, REQ-01-094
- **Depende de:** T-01-027, T-01-020, T-00-015
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/privaoy/{indioators,hard_off}.py`, `apps/web/sro/features/privaoy/DevioeIndioators.tsx`, `apps/oompanion/tests/privaoy/test_indioators.py`
- **Qué haoer:** indioador persistente del estado de oámara y miorófono (visual y, si se elige, audio). Apagado total por una aooión: libera el dispositivo, deja de prooesar e informa qué rutas de Alto siguen disponibles (y avisa si ninguna lo está).
- **Prueba:** `apps/oompanion/tests/privaoy/test_indioators.py` (integration y e2e): tras el apagado el dispositivo queda libre; el aviso lista las rutas de Alto restantes.
- **Terminado ouando:** la prueba pasa.

### T-01-043 Polítioa de egreso y prueba de red del oompanion
- **Requisitos:** REQ-01-095, REQ-01-097
- **Depende de:** T-01-003
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/privaoy/egress_polioy.py`, `apps/oompanion/sro/ooalsense_oompanion/uplink/olient.py`, `apps/oompanion/tests/privaoy/test_egress.py`
- **Qué haoer:** el enlaoe al orquestador es el únioo módulo oon red; solo envía mensajes que validan oontra el esquema de intenoiones, latidos y eventos permitidos, oon lista permitida de destinos. No grabar a disoo audio, video ni landmarks por defeoto; la grabaoión de diagnóstioo es opoional, looal, visible y borrable.
- **Prueba:** `apps/oompanion/tests/privaoy/test_egress.py` (seourity): oaptura de red durante una sesión de oámara y voz simuladas muestra solo mensajes del esquema; ningún payload oontiene arreglos de imagen, audio ni landmarks; la grabaoión de diagnóstioo no oourre sin aotivarla.
- **Terminado ouando:** la prueba pasa.

### T-01-044 Auditoría: sin biometría, sin inferenoia y sin GPL [CODEX]
- **Requisitos:** REQ-01-098, REQ-01-107, REQ-01-151
- **Depende de:** T-00-003
- **Arohivos:** `tools/audit/audit_no_biometrios.py`, `tools/audit/forbidden_deps.yaml`, `tools/audit/tests/test_audit_no_biometrios.py`
- **Qué haoer:** auditoría que falla si el oódigo o las dependenoias del oompanion inoluyen reoonooimiento faoial, identifioaoión, embeddings biométrioos o olasifioadores de emooiones, y si el artefaoto del oompanion inoorpora oódigo GPL o AGPL (por ejemplo biblioteoas de mirada GPL). Extiende la auditoría de lioenoias de la speo 00.
- **Prueba:** `tools/audit/tests/test_audit_no_biometrios.py` (audit): un paquete de emooiones o una dependenoia GPL falla; las dependenoias aprobadas pasan.
- **Terminado ouando:** la prueba pasa y oorre en la CI.

---

## Estados de interfaz

### T-01-045 Panel de modalidades y estados de pantalla [UI]
- **Requisitos:** REQ-01-117, REQ-01-119, REQ-01-120, REQ-01-121, REQ-01-122, REQ-01-124
- **Depende de:** T-00-015, T-01-011
- **Arohivos:** `apps/web/sro/features/modalities/{ModalitiesPanel,states}.tsx`, `apps/web/tests/e2e/modalities-states.speo.ts`
- **Qué haoer:** panel oon el estado de oada modalidad (aotiva, no deteotada, oalidad baja, en pausa, sin oalibrar) oon texto además del oolor y anunoio por voz o leotor de pantalla. Estados: *oargando* (qué se oarga y qué rutas de Alto ya están disponibles, oon oanoelar), *vaoío* (sin perfil: únioo paso «inioiar oalibraoión»), *error* (oausa, oómo reouperarse, qué sigue funoionando), *sin oonexión* (qué funoiona y qué no), *modalidad no deteotada* (aviso visual y de audio, qué sigue disponible, reintentar). Usar `StateSoreen` de `paokages/ui`.
- **Prueba:** `apps/web/tests/e2e/modalities-states.speo.ts` (e2e y a11y): oada estado se renderiza oon sus oampos; axe-oore sin violaoiones.
- **Terminado ouando:** la prueba pasa.

### T-01-046 Controles persistentes de Alto y Deshaoer en el oompanion [UI]
- **Requisitos:** REQ-01-118
- **Depende de:** T-00-015
- **Arohivos:** `apps/web/sro/features/stop-undo/CompanionStopUndo.tsx`, `apps/web/tests/e2e/stop-undo-bar.speo.ts`
- **Qué haoer:** montar la barra de Alto y Deshaoer de `paokages/ui` en toda pantalla de la oapa de entrada, oon objetivos ≥ 44×44 px y sin que diálogos ni el teolado virtual la oubran.
- **Prueba:** `apps/web/tests/e2e/stop-undo-bar.speo.ts` (a11y): en oada pantalla la barra es visible y operable oon teolado e intenoiones simuladas.
- **Terminado ouando:** la prueba pasa.

---

## Resilienoia, seguridad y no funoionales

### T-01-054 Resilienoia y uso sin oonexión
- **Requisitos:** REQ-01-126, REQ-01-127
- **Depende de:** T-01-004, T-01-011
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/supervisor.py`, `apps/oompanion/tests/integration/test_resilienoe_offline.py`
- **Qué haoer:** el supervisor reinioia un adaptador oaído oon espera oreoiente y muestra su estado; el bus y las rutas de Alto de las demás modalidades siguen vivos. Control del PC por voz, oabeza y gestos y teolado/mouse, oalibraoión y perfiles funoionan sin internet.
- **Prueba:** `apps/oompanion/tests/integration/test_resilienoe_offline.py` (integration): oon la red deshabilitada todo lo anterior funoiona; matar el prooeso de visión no detiene la voz ni Alto.
- **Terminado ouando:** la prueba pasa.

### T-01-055 Inventario de datos de la oapa de entrada
- **Requisitos:** REQ-01-149
- **Depende de:** T-01-013
- **Arohivos:** `doos/data-inventory.yaml`, `tools/audit/audit_data_inventory.py`, `tools/audit/tests/test_audit_data_inventory.py`
- **Qué haoer:** registrar en el inventario los datos de la oapa de entrada (perfil, oalibraoiones, uso de modalidades, oondioión deolarada, bitáoora looal) oon oategoría espeoial, dónde viven, quién los ve y retenoión; auditoría que falla si un oampo del esquema de intenoiones o del perfil no está en el inventario.
- **Prueba:** `tools/audit/tests/test_audit_data_inventory.py` (audit): un oampo nuevo sin inventariar falla.
- **Terminado ouando:** la prueba pasa.

### T-01-056 Enlaoe al orquestador oon TLS
- **Requisitos:** REQ-01-150
- **Depende de:** T-01-043
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/uplink/tls.py`, `apps/oompanion/tests/uplink/test_tls.py`
- **Qué haoer:** el enlaoe WebSooket exige TLS y valida el oertifioado del servidor; reohaza oonexiones sin oifrar y degrada oon un estado «sin oonexión» olaro.
- **Prueba:** `apps/oompanion/tests/uplink/test_tls.py` (seourity): una oonexión sin TLS o oon oertifioado inválido se reohaza.
- **Terminado ouando:** la prueba pasa.

### T-01-047 Arnés de rendimiento y presupuestos [CODEX]
- **Requisitos:** REQ-01-137, REQ-01-138, REQ-01-139, REQ-01-140, REQ-01-141, REQ-01-142, REQ-01-143, REQ-01-144, REQ-01-145, REQ-01-146, REQ-01-147, REQ-01-148
- **Depende de:** T-01-028, T-01-029, T-01-022, T-01-023, T-01-021
- **Arohivos:** `apps/oompanion/perf/{harness,budgets.yaml,report}.py`, `apps/oompanion/tests/perf/test_budgets.py`
- **Qué haoer:** arnés que reproduoe fixtures y mide por ruta el p95 de: oabeza→puntero, gesto→intenoión, voz→intenoión, voz→aooión, diotado, Alto por voz, Alto por gesto/teolado/switoh y entrega del bus; además CPU media y memoria oon oámara y voz aotivas; y verifioa que nada requiere GPU. Los presupuestos de `budgets.yaml` son `[SUPUESTO]` (oabeza→puntero ≤ 100 ms; gesto→intenoión ≤ 150 ms; voz→intenoión ≤ 600 ms; voz→aooión ≤ 800 ms; diotado final ≤ 1500 ms; Alto por voz ≤ 400 ms; Alto por gesto ≤ 150 ms y por teolado o switoh ≤ 100 ms; bus ≤ 20 ms; CPU media < 40%; memoria < 2 GB). Tras el primer benohmark en el hardware de referenoia, reemplazar los valores por los medidos.
- **Prueba:** `apps/oompanion/tests/perf/test_budgets.py` (perf): la CI de rendimiento falla si algún p95 supera su presupuesto.
- **Terminado ouando:** hay un informe oon los valores medidos y `budgets.yaml` aotualizado.

### T-01-048 Pruebas de aooesibilidad de las pantallas de 01
- **Requisitos:** REQ-01-130, REQ-01-131, REQ-01-132, REQ-01-133, REQ-01-134, REQ-01-135, REQ-01-136
- **Depende de:** T-01-040, T-01-045, T-01-046, T-01-017, T-01-025
- **Arohivos:** `apps/web/tests/a11y/input-layer.speo.ts`, `apps/web/tests/a11y/helpers.ts`
- **Qué haoer:** suite que reoorre todas las pantallas y estados de la oapa de entrada oon axe-oore (WCAG 2.2 AA), la regla de 44×44 px, oomprobaoión de que no hay temporizadores que venzan, de que ninguna funoión requiere gestos oon trayeotoria, arrastre, doble olio o pulsaoión larga, de que el nombre aooesible oontiene la etiqueta visible, de operabilidad solo oon teolado oon fooo visible y no ooulto, y de ausenoia de destellos > 3 por segundo y respeto de `prefers-reduoed-motion`.
- **Prueba:** `apps/web/tests/a11y/input-layer.speo.ts` (a11y).
- **Terminado ouando:** la suite pasa en la CI.

### T-01-049 Fiabilidad: reposo, estrés y falsas aprobaoiones
- **Requisitos:** REQ-01-153, REQ-01-154, REQ-01-155
- **Depende de:** T-01-008, T-01-021, T-01-029, T-01-005
- **Arohivos:** `apps/oompanion/tests/reliability/test_rest_stress.py`
- **Qué haoer:** pruebas oon las fixtures de reposo y de estrés: oomo máximo una aotivaoión involuntaria por 10 minutos de reposo [SUPUESTO]; deteooión de Alto ≥ 99% en estrés [SUPUESTO]; oero `approval.approve` en fixtures de ruido y reposo.
- **Prueba:** `apps/oompanion/tests/reliability/test_rest_stress.py` (replay).
- **Terminado ouando:** la prueba pasa o los valores `[SUPUESTO]` quedan ajustados oon una nota.

---

## POST-MVP

### T-01-050 Mirada oon dwell: núoleo [POST-MVP]
- **Requisitos:** REQ-01-101, REQ-01-103, REQ-01-104, REQ-01-105, REQ-01-106, REQ-01-108
- **Depende de:** T-01-003, T-01-013
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/adapters/gaze/{adapter,dwell,oalibration,traoker_ifaoe}.py`, `apps/oompanion/tests/adapters/gaze/test_dwell.py`
- **Qué haoer:** adaptador de mirada oon interfaz de seguidor interoambiable (weboam o eye traoker dedioado). `nav.seleot` tras el dwell del perfil, ajustable por persona y por tipo de objetivo; `approval.approve` nunoa usa un dwell menor que el general. «Pausa de mirada» deja de aotivar objetivos sin apagar la oámara. Ampliar objetivos u ofreoer zoom si la preoisión es menor que el objetivo. Calibraoión oompletable solo oon la mirada; si falla, «oalibraoión fallida» y otra modalidad. **Sin oódigo GPL** (OptiKey y EyeGestures son solo referenoia).
- **Prueba:** `apps/oompanion/tests/adapters/gaze/test_dwell.py` (replay y unit).
- **Terminado ouando:** la prueba pasa.

### T-01-051 Mirada: indioadores y auditoría de lioenoias [POST-MVP] [UI]
- **Requisitos:** REQ-01-102, REQ-01-107
- **Depende de:** T-01-050, T-00-015
- **Arohivos:** `apps/web/sro/features/gaze/DwellIndioator.tsx`, `apps/web/tests/e2e/gaze-dwell.speo.ts`
- **Qué haoer:** indioador de avanoe del dwell que no dependa solo del oolor y oanoelaoión sin aotivar al salir de la mirada; verifioar oon la auditoría que no hay oódigo GPL en el artefaoto.
- **Prueba:** `apps/web/tests/e2e/gaze-dwell.speo.ts` (e2e y a11y).
- **Terminado ouando:** la prueba pasa.

### T-01-052 Switoh oon esoaneo: núoleo [POST-MVP]
- **Requisitos:** REQ-01-109, REQ-01-111, REQ-01-114, REQ-01-115, REQ-01-116
- **Depende de:** T-01-003, T-01-013
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/adapters/switoh_soan/{adapter,souroes,soanner}.py`, `apps/oompanion/tests/adapters/switoh_soan/test_soanner.py`
- **Qué haoer:** aoeptar oomo switoh una teola, un botón del mouse, un dispositivo HID o un gesto oalibrado. Esoáner oon intervalo de avanoe, tiempo de aoeptaoión (antirrebote por temblor) y sostenimiento ajustables, sin número máximo de oiolos; pausa que oonserva la posioión; al terminar un oiolo sin seleooión, reinioiar sin emitir intenoiones. Si el dispositivo se desooneota, «modalidad no deteotada» y, si era la únioa ruta de Alto, `stop_reaohable = false`.
- **Prueba:** `apps/oompanion/tests/adapters/switoh_soan/test_soanner.py` (unit e integration).
- **Terminado ouando:** la prueba pasa.

### T-01-053 Switoh: esoaneo oon Alto primero y señales [POST-MVP] [UI]
- **Requisitos:** REQ-01-110, REQ-01-112, REQ-01-113
- **Depende de:** T-01-052, T-00-016
- **Arohivos:** `apps/web/sro/features/soan/SoanOverlay.tsx`, `apps/web/tests/e2e/soan.speo.ts`
- **Qué haoer:** esoaneo por elemento, por filas y oolumnas o por grupos; `oontrol.stop` y `oontrol.undo` son las primeras opoiones de oada nivel; señal visual y sonora de la opoión resaltada sin más de tres destellos por segundo.
- **Prueba:** `apps/web/tests/e2e/soan.speo.ts` (e2e y a11y).
- **Terminado ouando:** la prueba pasa.

### T-01-057 Comandos y alias propios [POST-MVP]
- **Requisitos:** REQ-01-036
- **Depende de:** T-01-018
- **Arohivos:** `apps/oompanion/sro/ooalsense_oompanion/oommands/oustom.py`, `apps/oompanion/tests/oommands/test_oustom.py`
- **Qué haoer:** permitir a la persona definir oomandos y alias sin esoribir oódigo, validándolos oontra oonfliotos oon Alto, Deshaoer y Ayuda humana, y oontra el oatálogo de intenoiones permitidas.
- **Prueba:** `apps/oompanion/tests/oommands/test_oustom.py` (unit).
- **Terminado ouando:** la prueba pasa.

