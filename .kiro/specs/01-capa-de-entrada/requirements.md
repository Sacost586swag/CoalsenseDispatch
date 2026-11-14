# Requisitos: 01 Capa de entrada

**Estado:** aprobado por el operador (fase 1). Se agregaron REQ-01-156 y REQ-01-157 por el segmento inicial.
**Producto:** Coalsense Dispatch. **Idioma del producto:** español de Ecuador [SUPUESTO].
**Vertical aplicable:** V-01, V-04, V-05, V-06, V-08, V-09, V-12 (ver `.kiro/steering/product.md`). Reglas de accesibilidad: AX-01 a AX-17.

## 0. Cómo leer este documento

- **EARS.** Las palabras clave van en inglés: `WHEN`, `WHILE`, `IF … THEN`, `WHERE`, `THE SYSTEM SHALL`. El resto va en español. "THE SYSTEM" es la capa de entrada (companion y modo web) salvo que se nombre otro componente.
- **IDs.** `REQ-01-NNN`, únicos y estables. Un ID retirado no se reutiliza.
- **Prueba.** Cada criterio termina con el tipo de prueba que lo verifica:

| Tipo | Qué es |
| --- | --- |
| `unit` | Prueba unitaria (pytest o Vitest). |
| `contract` | Validación contra JSON Schema y tipos generados. |
| `replay` | Reproduce una fixture (landmarks o audio) y compara la secuencia de intenciones. |
| `integration` | Varios componentes reales, red controlada. |
| `e2e` | Playwright o prueba de extremo a extremo del companion. |
| `a11y` | axe-core, reglas propias de geometría y revisión de criterios WCAG. |
| `perf` | Benchmark reproducible en el hardware de referencia. |
| `security` | Prueba negativa: captura de red, inyección, permisos. |
| `audit` | Chequeo automático en CI (licencias, dependencias, manifiestos). |
| `manual` | Con persona y hardware reales. Se usa solo donde no hay alternativa. |

- **Hitos.** Cada grupo lleva `[MVP]` o `[POST-MVP]` [SUPUESTO, PA-07]. Un criterio con otro hito lo indica.
- **Cifras.** Todo número que no vino de ti está marcado `[SUPUESTO]` y se reemplaza por un valor medido (REQ-01-145).

## 1. Propósito y alcance

La capa de entrada convierte lo que la persona hace con su voz, su cabeza, su cara, su mirada o un switch en **intenciones** normalizadas, y ejecuta en el PC las que son de control local. Es donde empieza la experiencia de control que sostiene todo el producto: si la entrada falla, la persona no siente que decide.

**Dentro de la spec**

- Adaptadores de entrada: voz (comandos y dictado), cabeza y gestos, mirada con dwell, switch con escaneo, teclado y mouse.
- Bus de intenciones y esquema en `packages/intents`.
- Alto, Deshacer y Ayuda humana en todas las modalidades.
- Calibración y perfil de capacidad.
- Actuador de escritorio del companion (PC sin puntería fina). Ubicación a confirmar, PA-11.
- Privacidad de cámara y micrófono.
- Estados de interfaz propios de esta capa.

**Fuera de la spec**

| Tema | Spec dueña |
| --- | --- |
| Qué hace la IA con la intención, políticas y aprobación válida | 02 |
| Ciclo de control, dial de autonomía, logros | 03 |
| Detección de señales de crisis y derivación | 05 (aquí solo se emite `help.request_human`) |
| Delegaciones del cuidador/a | 06 |
| Retención, exportación y borrado a nivel plataforma | 07 |
| Empaquetado e instalación del companion | 09 |
| Habla atípica, Android | Fases 3 y 2 |

## 2. Modalidades

| Modalidad | Quién la usa (ejemplos) | Hito |
| --- | --- | --- |
| Voz (comandos y dictado) | Quien puede hablar con claridad: cama, cuadriplejia, movilidad reducida. | MVP |
| Cabeza y gestos | Quien mueve la cabeza o la cara. | MVP |
| Teclado y mouse | Cuidador/a, y la persona en días de mejor movilidad. | MVP |
| Mirada con dwell | Quien controla solo los ojos. | POST-MVP |
| Switch con escaneo | Quien solo puede activar un pulsador. | POST-MVP |

## 3. Catálogo inicial de intenciones [SUPUESTO; se fija en `design.md`]

| Tipo | Uso | Prioridad |
| --- | --- | --- |
| `control.stop` | Alto | `preemptive` |
| `control.undo` | Deshacer | `preemptive` |
| `help.request_human` | Ayuda humana | `preemptive` |
| `approval.approve`, `approval.reject` | Aprobación de una acción pendiente | `normal` (nunca se descarta) |
| `pointer.move`, `pointer.click`, `pointer.double_click`, `pointer.drag_toggle`, `pointer.scroll` | Control del puntero | `normal` |
| `key.press`, `text.insert`, `text.dictation` | Teclas y texto | `normal` |
| `nav.next`, `nav.previous`, `nav.select`, `nav.back` | Navegación y escaneo | `normal` |
| `ui.show_numbers`, `ui.show_grid`, `ui.select_target` | Números y cuadrícula | `normal` |
| `mode.set`, `input.pause`, `input.resume` | Modo de voz y pausa | `normal` |
| `profile.switch`, `calibration.request` | Perfiles y calibración | `normal` |
| `command.invoke` | Comando de voz con nombre y parámetros | `normal` |

## 4. Requisitos funcionales

### Grupo A. Bus de intenciones [MVP]

**HU-01-A.** Como persona usuaria, quiero que lo que hago con mi voz, mi cabeza o mi gesto se convierta en la misma orden para el sistema, para poder cambiar de modalidad el día que me canse sin perder nada de lo que sé hacer.

- **REQ-01-001** WHEN un adaptador de entrada detecta una acción de la persona, THE SYSTEM SHALL publicar en el bus una intención que valide contra el JSON Schema de `packages/intents`, con los campos obligatorios `id` (único), `type`, `modality`, `adapter`, `actor_origin`, `monotonic_ts`, `wall_ts`, `payload` y, cuando aplique, `confidence`. Prueba: `contract`.
- **REQ-01-002** THE SYSTEM SHALL generar los tipos de Python y de TypeScript desde el mismo JSON Schema y fallar el pipeline de CI si los tipos versionados difieren de los generados. Prueba: `contract`.
- **REQ-01-003** WHEN la misma orden se produce por dos modalidades distintas (por ejemplo «clic» por voz y por gesto), THE SYSTEM SHALL publicar intenciones del mismo `type` y `payload`, que difieren solo en `modality`, `adapter` y `confidence`. Prueba: `unit`.
- **REQ-01-004** IF una intención no valida contra el esquema, THEN THE SYSTEM SHALL descartarla, registrar el rechazo en la bitácora y no entregarla a ningún consumidor. Prueba: `unit`.
- **REQ-01-005** THE SYSTEM SHALL asignar a cada tipo de intención una clase de prioridad fija (`preemptive` para `control.stop`, `control.undo` y `help.request_human`; `normal` para el resto) y entregar las `preemptive` antes que cualquier `normal` en cola. Prueba: `unit`.
- **REQ-01-006** WHILE la cola del bus está saturada, THE SYSTEM SHALL fusionar o descartar solo intenciones `normal` de tipo continuo (por ejemplo `pointer.move`), y THE SYSTEM SHALL NOT descartar ni retrasar una intención `preemptive` ni una `approval.*`. Prueba: `unit`.
- **REQ-01-007** THE SYSTEM SHALL derivar `actor_origin` (`person`, `caregiver` o `system`) de la sesión autenticada del adaptador y NOT tomarlo de la carga útil. Prueba: `security`.
- **REQ-01-008** IF una intención `approval.approve` llega con `actor_origin = system`, THEN THE SYSTEM SHALL rechazarla en el bus y registrar el intento. Prueba: `security`.
- **REQ-01-009** WHEN una intención `approval.*` llega con `actor_origin = caregiver`, THE SYSTEM SHALL entregarla marcada con ese origen para que el motor de políticas (spec 02) valide la delegación vigente. El bus no decide si la delegación es válida. Prueba: `contract`.
- **REQ-01-010** THE SYSTEM SHALL exigir que toda intención `approval.*` incluya `pending_action_id` y `content_digest` de la acción sobre la que se decide, y rechazar las que no los incluyan. Prueba: `contract`.
- **REQ-01-011** IF la confianza de una intención `approval.approve` es menor que el umbral de aprobación del perfil de capacidad, THEN THE SYSTEM SHALL NOT emitirla como aprobación, SHALL mostrar o decir lo que entendió y SHALL ofrecer repetir o elegir otra modalidad. Prueba: `replay`.
- **REQ-01-012** THE SYSTEM SHALL aceptar publicaciones solo de adaptadores registrados que se autentican con una credencial local efímera, y IF un proceso no registrado intenta publicar, THEN rechazarlo y registrar el intento. Prueba: `security`.
- **REQ-01-013** THE SYSTEM SHALL registrar cada intención publicada (`id`, `type`, `modality`, `actor_origin`, resultado) en la bitácora, guardándola localmente mientras no haya conexión, y NOT incluir audio, video, landmarks ni texto dictado. Prueba: `integration`.
- **REQ-01-014** WHERE se agrega un adaptador nuevo que cumple el contrato del bus, THE SYSTEM SHALL entregar sus intenciones a los consumidores existentes sin cambios en ellos. Prueba: `contract` (con un adaptador ficticio).
- **REQ-01-015** WHEN se reproduce la misma fixture con el mismo perfil de capacidad y la misma versión de modelo, THE SYSTEM SHALL producir la misma secuencia de intenciones, ignorando `id`, `wall_ts` y `monotonic_ts`. Prueba: `replay`.

### Grupo B. Alto, Deshacer y Ayuda humana universales [MVP]

**HU-01-B.** Como persona usuaria, quiero poder decir o hacer «alto» y «deshacer» en cualquier momento, con la modalidad que uso, para saber que siempre puedo parar y corregir.

- **REQ-01-016** THE SYSTEM SHALL asociar `control.stop` y `control.undo` a al menos un disparador en cada modalidad habilitada, y SHALL rechazar guardar o activar un perfil de capacidad en el que alguna modalidad habilitada carezca de disparador para cualquiera de los dos. Prueba: `unit`.
- **REQ-01-017** THE SYSTEM SHALL permitir cambiar el disparador de `control.stop` y `control.undo` y NOT permitir quitarlos. Prueba: `unit`.
- **REQ-01-018** WHEN se recibe `control.stop` por cualquier modalidad, THE SYSTEM SHALL detener de inmediato toda actuación local en curso (puntero, pulsaciones, inserción de texto, dictado, escaneo) y publicar `control.stop` con prioridad `preemptive` sin esperar respuesta de ningún consumidor. Prueba: `integration`.
- **REQ-01-019** WHILE no hay conexión con el orquestador, THE SYSTEM SHALL detener la actuación local al recibir `control.stop`. Prueba: `integration`.
- **REQ-01-020** WHILE el sistema está en cualquier modo (comando, dictado, sueño de voz, pausa de seguimiento, escaneo, calibración), THE SYSTEM SHALL mantener activas las rutas de `control.stop`, `control.undo` y `help.request_human`. Prueba: `replay` (una por modo).
- **REQ-01-021** WHILE el modo de voz es dictado, WHEN la palabra de Alto se pronuncia como enunciado aislado (delimitado por silencio) [SUPUESTO regla de aislamiento, S-09], THE SYSTEM SHALL tratarla como `control.stop`, y WHEN forma parte de un enunciado más largo, THE SYSTEM SHALL tratarla como texto dictado. Prueba: `replay`.
- **REQ-01-022** WHEN se recibe `control.undo`, THE SYSTEM SHALL revertir la última actuación local reversible de la pila de deshacer e informar a la persona cuál revirtió. Prueba: `unit`.
- **REQ-01-023** IF la pila de deshacer está vacía o la última actuación no es reversible, THEN THE SYSTEM SHALL decirlo explícitamente y NOT fallar en silencio ni revertir otra cosa. Prueba: `unit`.
- **REQ-01-024** THE SYSTEM SHALL declarar para cada clase de actuación local si es reversible o no, y revertir solo las declaradas reversibles. Prueba: `unit` (ninguna clase queda sin declarar).
- **REQ-01-025** WHEN la persona emite `help.request_human` por cualquier modalidad, THE SYSTEM SHALL publicarla con prioridad `preemptive` hacia la ruta de derivación humana de la spec 05, sin pasarla por ningún modelo de lenguaje [SUPUESTO, PA-08]. Prueba: `integration`.
- **REQ-01-026** THE SYSTEM SHALL publicar el estado `stop_reachable`, verdadero solo si al menos una ruta de `control.stop` está activa y sana, y WHEN pasa a falso, THE SYSTEM SHALL avisar de inmediato a la persona y a los consumidores. La spec 02 usa este estado para no ejecutar acciones de agentes. Prueba: `integration`.

### Grupo C. Voz: comandos [MVP]

**HU-01-C.** Como persona sin uso de manos, quiero controlar mi computadora y la app diciendo órdenes cortas en español, para trabajar sin tocar nada.

- **REQ-01-027** THE SYSTEM SHALL reconocer voz en el dispositivo por defecto y NOT enviar audio fuera de él salvo que la persona haya activado el reconocimiento en la nube (REQ-01-096). Prueba: `security`.
- **REQ-01-028** THE SYSTEM SHALL cargar los comandos de voz desde archivos declarativos (formato propio inspirado en `.talon`) que relacionan una frase con una intención, con soporte para parámetros (números, listas de palabras), alcance por contexto (aplicación activa, modo de voz) y prioridad. Prueba: `unit`.
- **REQ-01-029** IF un archivo de comandos no es válido, THEN THE SYSTEM SHALL conservar el último conjunto válido, informar el error con archivo y línea y NOT dejar a la persona sin comandos. Prueba: `unit`.
- **REQ-01-030** THE SYSTEM SHALL incluir un conjunto base de comandos en español que cubra: puntero (mover, clic, clic derecho, doble clic, arrastre por alternancia), desplazamiento, teclas y atajos, texto, ventanas, cambio de modo de voz, sueño y despertar, Alto, Deshacer, Ayuda humana, aprobar, rechazar, mostrar números y mostrar cuadrícula. Prueba: `unit` (matriz de cobertura).
- **REQ-01-031** WHEN el reconocimiento produce dos o más hipótesis cuya diferencia de confianza es menor que el margen del perfil [SUPUESTO; valor en `design.md`], THE SYSTEM SHALL NOT ejecutar ninguna, SHALL mostrar las opciones numeradas y SHALL aceptar la elección por cualquier modalidad. Prueba: `replay`.
- **REQ-01-032** WHEN se reconoce un comando, THE SYSTEM SHALL mostrar lo que entendió y, si la persona lo eligió, decirlo. Prueba: `e2e`.
- **REQ-01-033** WHEN la persona dice la frase de sueño, THE SYSTEM SHALL dejar de interpretar comandos salvo despertar, `control.stop` y `help.request_human`, y mostrar el estado de forma visible. WHEN dice la frase de despertar, THE SYSTEM SHALL volver al modo comando. Prueba: `replay`.
- **REQ-01-034** WHEN la persona pide la ayuda de comandos («¿qué puedo decir?»), THE SYSTEM SHALL mostrar los comandos válidos en el contexto actual, navegables por cualquier modalidad. Prueba: `e2e`.
- **REQ-01-035** WHERE el conjunto base reutilice comandos de `talonhub/community`, THE SYSTEM SHALL conservar el aviso de copyright y la licencia MIT en `THIRD_PARTY.md` y NOT incluir código del núcleo de Talon. Prueba: `audit`.
- **REQ-01-036** WHERE la persona define comandos propios o alias, THE SYSTEM SHALL permitirlo sin escribir código y validarlos contra conflictos con `control.stop`, `control.undo` y `help.request_human`. Hito: `[POST-MVP]`. Prueba: `unit`.
- **REQ-01-037** THE SYSTEM SHALL ofrecer los comandos base en español de Ecuador [SUPUESTO, PA-14] y NOT depender del inglés para ninguna función. Prueba: `replay`.

### Grupo D. Voz: dictado libre [MVP]

**HU-01-D.** Como persona que dicta, quiero hablar con naturalidad y que mi texto aparezca ordenado, para producir documentos sin teclear.

- **REQ-01-038** WHEN la persona entra en modo dictado, THE SYSTEM SHALL transcribir en el dispositivo y publicar `text.dictation` con segmentos parciales y finales. Prueba: `replay`.
- **REQ-01-039** THE SYSTEM SHALL interpretar los comandos de formato dictados en español (coma, punto, nueva línea, mayúscula) como formato y no como texto literal. Prueba: `replay`.
- **REQ-01-040** WHEN la persona dice un comando de corrección (por ejemplo «borra eso»), THE SYSTEM SHALL modificar solo el último segmento dictado y registrar el cambio en la pila de deshacer. Prueba: `unit`.
- **REQ-01-041** WHEN el dictado se inserta en un campo de otra aplicación, THE SYSTEM SHALL insertar cada enunciado como una unidad deshacible. Prueba: `integration`.
- **REQ-01-042** THE SYSTEM SHALL NOT escribir audio a disco y SHALL conservar el texto transcrito solo en memoria hasta entregarlo a su consumidor. Prueba: `security`.
- **REQ-01-043** IF el micrófono se desconecta durante el dictado, THEN THE SYSTEM SHALL conservar el texto ya transcrito, mostrar el estado «modalidad no detectada» y ofrecer continuar con otra modalidad. Prueba: `integration`.

### Grupo E. Cabeza y gestos (patrón Gameface) [MVP]

**HU-01-E.** Como persona que mueve la cabeza o la cara pero no las manos, quiero mover el cursor y hacer clic con gestos que yo elijo y calibro, para usar la computadora sin ayuda.

- **REQ-01-044** THE SYSTEM SHALL procesar los cuadros de la cámara en memoria, en el dispositivo, con MediaPipe Face Landmarker (478 landmarks y 52 blendshapes), y NOT escribirlos a disco ni pasarlos a ningún componente con acceso a la red. Prueba: `security`.
- **REQ-01-045** WHEN la cámara está activa y hay un rostro detectado, THE SYSTEM SHALL mover el puntero según la pose de la cabeza, con sensibilidad, zona muerta, suavizado y velocidad máxima configurables en el perfil. Prueba: `replay`.
- **REQ-01-046** THE SYSTEM SHALL compensar la inclinación y la posición de la cámara registradas en la calibración, incluida una postura reclinada o acostada, sin recalibrar en cada sesión. Prueba: `replay` (fixtures con ángulos distintos).
- **REQ-01-047** THE SYSTEM SHALL detectar gestos faciales a partir de los blendshapes con un umbral calibrable por gesto y por persona, con histéresis (umbral de activación distinto del de liberación) y un sostenimiento configurable. Prueba: `replay`.
- **REQ-01-048** THE SYSTEM SHALL permitir vincular cualquier gesto calibrado a cualquier intención del catálogo y mostrar cada vínculo gesto→intención en el perfil. Prueba: `unit`.
- **REQ-01-049** THE SYSTEM SHALL implementar el doble clic como una única intención (`pointer.double_click`) disparada por un solo gesto o un solo comando, y el arrastre como alternancia (`pointer.drag_toggle`), y NOT requerir dos gestos dentro de una ventana de tiempo, gestos simultáneos ni mantener un gesto para arrastrar. Prueba: `unit` (revisión estática del catálogo y de los vínculos).
- **REQ-01-050** WHEN no se detecta rostro durante más del tiempo configurado, THE SYSTEM SHALL congelar el puntero sin saltos, mostrar y decir «modalidad no detectada» y mantener las demás modalidades. WHEN el rostro vuelve, THE SYSTEM SHALL reanudar sin salto del puntero. Prueba: `replay`.
- **REQ-01-051** WHEN hay más de un rostro en cuadro, THE SYSTEM SHALL seguir el rostro rastreado desde la calibración por continuidad espacial, sin reconocimiento facial ni embeddings biométricos [SUPUESTO, S-10]. IF la continuidad se pierde, THEN THE SYSTEM SHALL pausar el seguimiento y pedir a la persona que lo reanude. Prueba: `replay`.
- **REQ-01-052** WHERE la persona activa el filtro de temblor o espasmo, THE SYSTEM SHALL limitar la aceleración y el salto del puntero según los parámetros del perfil. Prueba: `replay`.
- **REQ-01-053** WHEN la persona da la orden de pausa, THE SYSTEM SHALL detener el seguimiento y la emisión de gestos, y WHEN da la orden de reanudar, THE SYSTEM SHALL reanudarlos. `control.stop` y `help.request_human` siguen activos durante la pausa. Prueba: `replay`.
- **REQ-01-054** WHEN la calidad del seguimiento cae por debajo del umbral (poca luz, rostro parcial, oclusión), THE SYSTEM SHALL avisar con una sugerencia accionable y sin culpar a la persona. Prueba: `replay`.
- **REQ-01-055** WHERE se use el modo web (sin instalación), THE SYSTEM SHALL ejecutar el mismo flujo con MediaPipe Tasks Vision en el navegador, procesar los cuadros solo en la página o en un worker, servir los archivos del modelo desde el propio origen y NOT enviar cuadros ni landmarks por la red. Prueba: `e2e` y `security` (Playwright con captura de red).

### Grupo F. Teclado y mouse [MVP]

**HU-01-F.** Como cuidador/a, o como persona con movilidad parcial, quiero usar teclado y mouse físicos junto con las demás modalidades, para configurar el equipo y para los días de mejor movilidad.

- **REQ-01-056** THE SYSTEM SHALL traducir la entrada de teclado y mouse físicos a las mismas intenciones del bus, con `modality = keyboard_mouse`. Prueba: `unit`.
- **REQ-01-057** THE SYSTEM SHALL ofrecer atajos globales configurables para `control.stop`, `control.undo` y `help.request_human`, y detectar y rechazar conflictos con otros atajos del perfil. Prueba: `unit`.
- **REQ-01-058** WHILE teclado/mouse y otra modalidad están activos a la vez, THE SYSTEM SHALL aceptar ambos sin que la persona tenga que conmutar entre ellos (WCAG 2.5.6). Prueba: `integration`.
- **REQ-01-059** WHEN el cuidador/a usa teclado y mouse, THE SYSTEM SHALL publicar las intenciones con `actor_origin = caregiver` solo si hay una sesión de cuidador/a autenticada, y SHALL NOT emitir aprobaciones en nombre de la persona sin una delegación vigente (spec 06). Prueba: `security`.

### Grupo G. Actuador de escritorio [MVP]

**HU-01-G.** Como persona sin uso de manos, quiero que mis órdenes se conviertan en acciones precisas en cualquier aplicación sin necesitar puntería fina, para trabajar con las mismas herramientas que todos.

- **REQ-01-060** WHEN llega una intención de puntero (`pointer.*`), de tecla (`key.press`) o de texto (`text.insert`), THE SYSTEM SHALL ejecutarla en el sistema operativo (Windows primero [SUPUESTO, S-02]) y publicar el resultado, éxito o fallo con su causa. Prueba: `integration`.
- **REQ-01-061** WHEN la persona pide «mostrar números», THE SYSTEM SHALL superponer una etiqueta numerada a cada elemento accionable de la ventana activa que el sistema operativo exponga como accesible, y WHEN la persona dice el número, THE SYSTEM SHALL activar ese elemento. Prueba: `e2e`.
- **REQ-01-062** WHEN la persona pide «mostrar cuadrícula», THE SYSTEM SHALL dividir la pantalla en celdas numeradas y permitir refinar la celda en pasos sucesivos hasta ubicar el objetivo, para los elementos que el sistema operativo no expone. Prueba: `e2e`.
- **REQ-01-063** WHERE el puntero se acerque a un elemento accionable, THE SYSTEM SHALL ofrecer un imán hacia ese elemento, configurable en el perfil. Prueba: `unit`.
- **REQ-01-064** THE SYSTEM SHALL ofrecer, para cualquier elemento accionable de cualquier aplicación, al menos una vía que no requiera puntería fina (números, cuadrícula o imán). Prueba: `e2e` (aplicaciones de muestra).
- **REQ-01-065** IF la ventana de destino no es controlable (por ejemplo un proceso con privilegios elevados), THEN THE SYSTEM SHALL decirlo, explicar por qué y ofrecer alternativas. Prueba: `integration`.
- **REQ-01-066** WHEN se ejecuta una actuación, THE SYSTEM SHALL dar a la persona retroalimentación por el canal que eligió (visual, audio o ambos) y NOT depender solo del color. Prueba: `e2e`.
- **REQ-01-067** THE SYSTEM SHALL aceptar solicitudes de actuación únicamente desde el bus de intenciones y rechazar las que lleguen de agentes o del orquestador por otra vía [SUPUESTO, PA-11]. Prueba: `security`.
- **REQ-01-068** WHILE un `pointer.drag_toggle` está activo, THE SYSTEM SHALL mostrar el estado de arrastre de forma visible, y SHALL terminarlo con `control.stop` o con un segundo `pointer.drag_toggle`. Prueba: `e2e`.

### Grupo H. Calibración [MVP]

**HU-01-H.** Como persona usuaria (o cuidador/a que me ayuda), quiero calibrar la entrada a mi cuerpo y mi voz, sin prisa y sin sentir que fallo, para controlar el equipo desde la primera sesión.

- **REQ-01-069** WHEN se inicia la calibración, THE SYSTEM SHALL detectar las cámaras, micrófonos y dispositivos de switch disponibles y mostrar cuáles están listos. IF no hay ninguno, THEN THE SYSTEM SHALL mostrar «modalidad no detectada» y ofrecer continuar con teclado y mouse con ayuda del cuidador/a. Prueba: `integration`.
- **REQ-01-070** THE SYSTEM SHALL permitir iniciar y avanzar cada paso de la calibración con la propia modalidad que se calibra, o con la ayuda del cuidador/a por teclado y mouse. Prueba: `e2e`.
- **REQ-01-071** THE SYSTEM SHALL NOT imponer un límite de tiempo a ningún paso de la calibración, y SHALL permitir pausar, saltar una modalidad y reanudar más tarde sin perder el avance. Prueba: `e2e`.
- **REQ-01-072** WHEN se calibra un gesto, THE SYSTEM SHALL capturar muestras en reposo y con el gesto activo, calcular el umbral con un margen respecto del reposo y verificar que ambas distribuciones se pueden separar. IF no se pueden separar, THEN THE SYSTEM SHALL declarar «calibración fallida» para ese gesto y proponer otro gesto, repetir o usar otra modalidad. Prueba: `replay`.
- **REQ-01-073** WHEN se calibra la cabeza, THE SYSTEM SHALL registrar la pose neutral y el rango de movimiento cómodo de la persona y ajustar la sensibilidad a ese rango. Prueba: `replay`.
- **REQ-01-074** WHEN se calibra la voz, THE SYSTEM SHALL medir el nivel y el ruido del micrófono, probar el reconocimiento con comandos de ejemplo e informar la calidad. Prueba: `replay`.
- **REQ-01-075** WHEN termina la calibración de un gesto o comando, THE SYSTEM SHALL medir las activaciones involuntarias durante un periodo de reposo. IF superan el presupuesto (REQ-01-153), THEN THE SYSTEM SHALL proponer un ajuste del umbral y aplicarlo solo si la persona lo aprueba. Prueba: `replay`.
- **REQ-01-076** WHEN se calibra cada vínculo, THE SYSTEM SHALL ofrecer una zona de práctica donde la persona lo ejecute y vea un efecto visible e inmediato (experiencia de control). Prueba: `e2e`.
- **REQ-01-077** THE SYSTEM SHALL NOT dar por terminada la calibración de una modalidad sin que `control.stop` y `control.undo` estén vinculados y practicados con éxito en ella. Prueba: `e2e`.
- **REQ-01-078** IF una calibración falla, THEN THE SYSTEM SHALL mostrar un mensaje de un catálogo de mensajes de fallo que atribuye el fallo al equipo o a la configuración y no a la persona, e incluir al menos una vía alternativa. Cada código de fallo tiene su mensaje. Prueba: `unit` (cobertura del catálogo) y `manual` (revisión del texto).
- **REQ-01-079** WHEN termina la calibración, THE SYSTEM SHALL guardar el perfil de capacidad y pasar el control a la selección de la primera tarea (spec 03) dentro de la misma sesión. Prueba: `integration`.
- **REQ-01-080** WHEN la persona pide «recalibrar» en cualquier momento, THE SYSTEM SHALL iniciar la calibración de la modalidad indicada sin borrar el perfil actual hasta que la persona apruebe el nuevo resultado, y SHALL permitir volver a la versión anterior. Prueba: `e2e`.
- **REQ-01-081** WHEN el sistema detecta deriva (aumento sostenido de activaciones involuntarias o de rechazos), THE SYSTEM SHALL sugerir recalibrar y NOT cambiar umbrales por su cuenta. Prueba: `replay`.
- **REQ-01-082** THE SYSTEM SHALL descartar las muestras crudas de calibración (valores de blendshapes y audio) una vez calculados los umbrales, salvo que la persona active la conservación para diagnóstico. Prueba: `security`.

### Grupo I. Perfil de capacidad [MVP]

**HU-01-I.** Como persona usuaria, quiero que el sistema recuerde cómo me muevo y qué uso, y que esos datos sean míos: que los vea quien yo diga, y que se exporten o se borren cuando lo pida.

- **REQ-01-083** THE SYSTEM SHALL representar el perfil de capacidad con: modalidades habilitadas, parámetros por modalidad, vínculos gesto o frase → intención, disparadores de Alto, Deshacer y Ayuda humana, preferencias de retroalimentación, idioma, umbral de aprobación y tamaño mínimo de objetivo, validable contra un JSON Schema versionado. Prueba: `contract`.
- **REQ-01-084** THE SYSTEM SHALL NOT incluir diagnóstico ni campos clínicos en el perfil, salvo un campo opcional de condición declarada que la persona completa voluntariamente, con consentimiento explícito, marcado como categoría especial. Prueba: `unit`.
- **REQ-01-085** THE SYSTEM SHALL almacenar el perfil cifrado en reposo en el dispositivo, y WHERE la persona active la sincronización, SHALL cifrarlo en tránsito y en reposo en el servidor [SUPUESTO: cifrado de extremo a extremo con clave de la persona; se decide en `design.md` y en la spec 07]. Prueba: `security`.
- **REQ-01-086** THE SYSTEM SHALL NOT incluir el perfil de capacidad ni la condición declarada en prompts a proveedores de modelos ni en telemetría visible al operador (SP-6). Prueba: `security` (prueba de contrato sobre el constructor de prompts y la telemetría).
- **REQ-01-087** THE SYSTEM SHALL permitir varios perfiles de capacidad (por ejemplo «en cama», «sentado», «cansado») y cambiar entre ellos con `profile.switch` desde cualquier modalidad, anunciando el cambio. Prueba: `e2e`.
- **REQ-01-088** WHEN la persona pide exportar su perfil, THE SYSTEM SHALL entregar un archivo legible y completo (JSON), y WHEN pide borrarlo, THE SYSTEM SHALL borrarlo del dispositivo y del servidor y confirmarlo. Prueba: `e2e`.
- **REQ-01-089** WHERE un cuidador/a edita el perfil, THE SYSTEM SHALL requerir una delegación vigente (spec 06), registrar quién cambió qué y cuándo en la bitácora, y mostrar el cambio a la persona con la opción de revertirlo. Prueba: `integration`.
- **REQ-01-090** WHEN el sistema propone un cambio al perfil (umbral, sensibilidad, vínculo), THE SYSTEM SHALL aplicarlo solo después de la aprobación explícita de la persona. Prueba: `unit`.
- **REQ-01-091** THE SYSTEM SHALL versionar el esquema del perfil con migraciones, y IF un perfil no es válido, THEN THE SYSTEM SHALL usar el último válido y NOT arrancar sin una ruta de `control.stop`. Prueba: `unit`.
- **REQ-01-092** THE SYSTEM SHALL mostrar el perfil en lenguaje llano (qué hace cada gesto o frase), no solo valores. Prueba: `e2e`.

### Grupo J. Privacidad de cámara y micrófono [MVP]

**HU-01-J.** Como persona usuaria, quiero tener la certeza de que mi cara y mi voz no salen de mi computadora, para usar el sistema sin miedo.

- **REQ-01-093** WHILE la cámara o el micrófono están activos, THE SYSTEM SHALL mostrar un indicador persistente del estado de cada uno, por canal visual y, si la persona lo elige, por audio. Prueba: `e2e`.
- **REQ-01-094** WHEN la persona pide apagar la cámara o el micrófono (apagado total), THE SYSTEM SHALL liberar el dispositivo, dejar de procesar e informar qué rutas de `control.stop` siguen disponibles. Prueba: `integration`.
- **REQ-01-095** THE SYSTEM SHALL NOT transmitir por la red cuadros de video, audio, landmarks ni blendshapes; solo salen intenciones y eventos del esquema (SP-3). Prueba: `security` (captura de red y lista permitida de egreso).
- **REQ-01-096** WHERE la persona active el reconocimiento de voz en la nube, THE SYSTEM SHALL requerir un consentimiento explícito que describa qué datos salen y a qué proveedor, mostrar de forma persistente que el modo nube está activo y permitir revocarlo con una sola acción. Por defecto está apagado. Prueba: `e2e`.
- **REQ-01-097** THE SYSTEM SHALL NOT grabar a disco audio, video ni landmarks por defecto, y WHERE la persona active la grabación de diagnóstico, THE SYSTEM SHALL guardarla solo en el dispositivo, mostrar su estado y permitir borrarla. Prueba: `security`.
- **REQ-01-098** THE SYSTEM SHALL NOT usar reconocimiento facial, identificación, embeddings biométricos ni inferencia de emociones, salud o estado de ánimo a partir de la cámara o la voz. Prueba: `audit` (dependencias y código).
- **REQ-01-099** WHEN el sistema operativo o el navegador deniega el permiso de cámara o micrófono, THE SYSTEM SHALL mostrar «modalidad no detectada» con la causa «permiso denegado» y los pasos para concederlo, operables con otra modalidad o con ayuda del cuidador/a. Prueba: `e2e`.
- **REQ-01-100** THE SYSTEM SHALL admitir en el repositorio solo fixtures de landmarks y audio que sean sintéticas o de personas con consentimiento registrado, y fallar la CI si el `manifest.json` de una fixture no declara `synthetic: true` o un `consent_ref`. Prueba: `audit`.

### Grupo K. Mirada con dwell [POST-MVP]

**HU-01-K.** Como persona que solo controla los ojos, quiero seleccionar mirando un objetivo el tiempo que yo elija, para usar la app sin cabeza ni manos.

- **REQ-01-101** WHEN la mirada permanece sobre un objetivo activable durante el tiempo de dwell del perfil, THE SYSTEM SHALL emitir `nav.select` sobre ese objetivo. Prueba: `replay`.
- **REQ-01-102** WHILE la mirada permanece sobre un objetivo, THE SYSTEM SHALL mostrar el avance del dwell con un indicador que no dependa solo del color, y WHEN la mirada sale del objetivo, THE SYSTEM SHALL cancelar sin activar. Prueba: `e2e`.
- **REQ-01-103** THE SYSTEM SHALL permitir ajustar el tiempo de dwell por persona y por tipo de objetivo, y NOT usar para `approval.approve` un dwell menor que el general. Prueba: `unit`.
- **REQ-01-104** WHEN la persona activa «pausa de mirada», THE SYSTEM SHALL dejar de activar objetivos por dwell sin apagar la cámara (evita activar sin querer todo lo que se mira). `control.stop` sigue activo. Prueba: `replay`.
- **REQ-01-105** WHERE la precisión estimada de la mirada es menor que el tamaño de los objetivos, THE SYSTEM SHALL ampliar los objetivos u ofrecer zoom antes de la selección. Prueba: `replay`.
- **REQ-01-106** THE SYSTEM SHALL calibrar la mirada con un procedimiento que la persona pueda completar solo con la mirada, y IF la precisión es insuficiente, THEN THE SYSTEM SHALL declarar «calibración fallida» y ofrecer otra modalidad. Prueba: `replay`.
- **REQ-01-107** THE SYSTEM SHALL implementar el seguimiento de mirada sin incorporar código GPL en el artefacto distribuido [SUPUESTO: OptiKey y EyeGestures son solo referencia de diseño, PA-09]. Prueba: `audit`.
- **REQ-01-108** WHERE existe un eye tracker dedicado compatible, THE SYSTEM SHALL aceptarlo como fuente alternativa mediante el mismo adaptador [SUPUESTO]. Prueba: `contract`.

### Grupo L. Switch con escaneo [POST-MVP]

**HU-01-L.** Como persona que solo puede activar un switch, quiero que el sistema recorra las opciones y yo elija con una sola activación, para hacer todo lo que harían las demás modalidades.

- **REQ-01-109** THE SYSTEM SHALL aceptar como switch cualquier fuente configurada (una tecla, un botón del mouse, un dispositivo HID o un gesto calibrado) y publicar la activación como evento de switch. Prueba: `unit`.
- **REQ-01-110** WHILE el escaneo está activo, THE SYSTEM SHALL resaltar las opciones en secuencia (por elemento, por filas y columnas o por grupos, según el perfil), y WHEN la persona activa el switch, THE SYSTEM SHALL emitir `nav.select` sobre la opción resaltada. Prueba: `e2e`.
- **REQ-01-111** THE SYSTEM SHALL permitir ajustar el intervalo de avance, el tiempo de aceptación (ignorar activaciones repetidas por temblor) y el sostenimiento, y NOT imponer un número máximo de ciclos tras el cual se pierda la selección. Prueba: `unit`.
- **REQ-01-112** THE SYSTEM SHALL incluir `control.stop` y `control.undo` como las primeras opciones de cada nivel de escaneo. Prueba: `e2e`.
- **REQ-01-113** WHILE el escaneo está activo, THE SYSTEM SHALL señalar la opción resaltada de forma visual y sonora, sin destellos de más de tres por segundo. Prueba: `a11y`.
- **REQ-01-114** WHEN la persona activa «pausar escaneo», THE SYSTEM SHALL detener el avance hasta que la persona lo reanude, sin perder la posición. Prueba: `unit`.
- **REQ-01-115** WHEN el escaneo llega al final de un ciclo sin selección, THE SYSTEM SHALL reiniciar el ciclo sin emitir ninguna intención. Prueba: `unit`.
- **REQ-01-116** IF el dispositivo de switch se desconecta, THEN THE SYSTEM SHALL mostrar «modalidad no detectada» y, si era la única ruta de Alto, publicar `stop_reachable = false`. Prueba: `integration`.

### Grupo M. Estados y retroalimentación de la interfaz [MVP]

Pantallas de esta spec: panel de modalidades, asistente de calibración, visor y editor del perfil, ayuda de comandos, panel de dictado y controles persistentes de Alto y Deshacer. Los requisitos describen estados y comportamiento, no estilo.

- **REQ-01-117** THE SYSTEM SHALL mostrar en un panel el estado de cada modalidad (activa, no detectada, calidad baja, en pausa, sin calibrar) con texto además del color, y anunciarlo por voz o lector de pantalla. Prueba: `a11y`.
- **REQ-01-118** THE SYSTEM SHALL mantener visibles y operables los controles de Alto y Deshacer en toda pantalla de esta capa, con un tamaño de objetivo de al menos 44×44 px CSS. Prueba: `a11y`.
- **REQ-01-119** *Estado cargando.* WHILE la capa de entrada inicia (modelos, dispositivos), THE SYSTEM SHALL mostrar qué se está cargando y qué rutas de Alto ya están disponibles, y SHALL permitir cancelar. Prueba: `e2e`.
- **REQ-01-120** *Estado vacío.* WHEN no existe un perfil de capacidad, THE SYSTEM SHALL mostrar un único siguiente paso (iniciar la calibración) y no una pantalla en blanco. Prueba: `e2e`.
- **REQ-01-121** *Estado error.* IF falla un adaptador o el bus, THEN THE SYSTEM SHALL mostrar la causa en lenguaje llano, la acción para recuperarse y qué modalidades siguen funcionando. Prueba: `e2e`.
- **REQ-01-122** *Estado sin conexión.* WHILE no hay red, THE SYSTEM SHALL indicar qué funciones siguen disponibles (entrada y control del PC) y cuáles no (orquestador, nube). Prueba: `e2e`.
- **REQ-01-123** *Estado calibración fallida.* IF una calibración falla, THEN THE SYSTEM SHALL conservar el perfil anterior y ofrecer reintentar, elegir otro gesto o usar otra modalidad. Prueba: `e2e`.
- **REQ-01-124** *Estado modalidad no detectada.* WHEN una modalidad habilitada deja de detectarse, THE SYSTEM SHALL avisarlo por canal visual y de audio en un tiempo máximo [SUPUESTO; valor en `design.md`], indicar qué modalidades siguen disponibles y ofrecer reintentar. Prueba: `e2e`.
- **REQ-01-125** THE SYSTEM SHALL ofrecer la retroalimentación por canal visual, de audio o ambos, según el perfil, y NOT depender de un solo canal para comunicar un estado crítico (Alto, modalidad no detectada, aprobación pendiente). Prueba: `a11y`.

### Grupo N. Resiliencia y uso sin conexión [MVP]

- **REQ-01-126** THE SYSTEM SHALL ofrecer control del PC por voz, cabeza y gestos y teclado y mouse, calibración y perfiles sin conexión a internet. Prueba: `integration` (red deshabilitada).
- **REQ-01-127** IF un adaptador (visión o voz) falla, THEN THE SYSTEM SHALL mantener vivos el bus y las rutas de Alto de las demás modalidades, reiniciar el adaptador con espera creciente y mostrar su estado. Prueba: `integration`.
- **REQ-01-128** THE SYSTEM SHALL emitir un latido periódico al orquestador, y los consumidores SHALL interpretar su ausencia como `stop_reachable = false`. Prueba: `integration`.
- **REQ-01-129** THE SYSTEM SHALL NOT publicar `stop_reachable = true` hasta verificar la salud de al menos una ruta de Alto (dispositivo transmitiendo, modelo cargado y adaptador respondiendo). Prueba: `integration`.

## 5. Requisitos no funcionales

### 5.1 Accesibilidad [MVP]

Base: WCAG 2.2 AA. Objetivos AAA en tamaño de objetivo y tiempo ajustable (AX-03, AX-04).

- **REQ-01-130** THE SYSTEM SHALL cumplir WCAG 2.2 nivel AA en todas las pantallas de la capa de entrada (web y companion), verificado con axe-core en cada pantalla y en cada estado del grupo M, más revisión manual de los criterios que no se automatizan. Prueba: `a11y`.
- **REQ-01-131** THE SYSTEM SHALL cumplir como objetivo AAA el criterio 2.5.5 (tamaño de objetivo): todo control interactivo mide al menos 44×44 px CSS. El mínimo AA 2.5.8 es 24×24. Prueba: `a11y` (regla de geometría propia en Playwright).
- **REQ-01-132** THE SYSTEM SHALL NOT tener límites de tiempo en ninguna función (2.2.3). Toda temporización de interacción (dwell, intervalo de escaneo, sostenimiento) es ajustable por la persona, y ninguna decisión pendiente expira. Prueba: `e2e`.
- **REQ-01-133** THE SYSTEM SHALL NOT requerir gestos de puntero con trayectoria, arrastre, doble clic ni pulsación larga para ninguna función (2.5.1, 2.5.7), ni movimiento del dispositivo (2.5.4). Prueba: `a11y`.
- **REQ-01-134** THE SYSTEM SHALL garantizar que el nombre accesible de cada control contiene su etiqueta visible (2.5.3), para que la persona lo active diciendo lo que ve. Prueba: `a11y` (regla `label-content-name-mismatch` de axe-core).
- **REQ-01-135** THE SYSTEM SHALL permitir operar toda función de la capa de entrada solo con teclado (2.1.1), sin atajos de una sola tecla activos por defecto (2.1.4), con foco visible y no oculto (2.4.7, 2.4.11). Prueba: `a11y`.
- **REQ-01-136** THE SYSTEM SHALL NOT usar destellos de más de tres por segundo (2.3.1) y SHALL respetar `prefers-reduced-motion`. Prueba: `a11y`.

### 5.2 Latencia de entrada [SUPUESTO: todas las cifras se miden y se reemplazan, REQ-01-145]

Se mide en el hardware de referencia (`tech.md`), con cámara y voz activas, percentil 95.

| ID | Ruta | Desde → hasta | Presupuesto p95 [SUPUESTO] | Prueba |
| --- | --- | --- | --- | --- |
| REQ-01-137 | Cabeza → puntero | cuadro capturado → puntero movido | ≤ 100 ms | `perf` |
| REQ-01-138 | Gesto → intención | cuadro en que se cumple el umbral y el sostenimiento → intención en el bus | ≤ 150 ms | `perf` |
| REQ-01-139 | Voz (comando) → intención | fin del enunciado → intención publicada | ≤ 600 ms | `perf` |
| REQ-01-140 | Voz (comando) → acción | fin del enunciado → efecto visible en pantalla | ≤ 800 ms | `perf` |
| REQ-01-141 | Dictado | fin del enunciado → texto final disponible | ≤ 1500 ms | `perf` |
| REQ-01-142 | Alto por voz | fin de la palabra → actuación local detenida | ≤ 400 ms | `perf` |
| REQ-01-143 | Alto por gesto / teclado o switch | evento → actuación local detenida | ≤ 150 ms / ≤ 100 ms | `perf` |
| REQ-01-144 | Bus | publicación → entrega a un consumidor local | ≤ 20 ms | `perf` |

Prueba de cada fila: `perf`.

- **REQ-01-145** THE SYSTEM SHALL incluir un arnés de medición reproducible, basado en fixtures, que mida cada ruta de la tabla en el hardware de referencia y falle la CI de rendimiento cuando un p95 supere su presupuesto. Tras el primer benchmark, los valores `[SUPUESTO]` se sustituyen por los medidos. Prueba: `perf`.

### 5.3 Recursos [SUPUESTO]

- **REQ-01-146** WHILE la cámara y la voz están activas en el hardware de referencia, THE SYSTEM SHALL mantener el uso medio de CPU del companion por debajo del 40% del total [SUPUESTO]. Prueba: `perf`.
- **REQ-01-147** THE SYSTEM SHALL mantener la memoria residente del companion por debajo de 2 GB [SUPUESTO]. Prueba: `perf`.
- **REQ-01-148** THE SYSTEM SHALL funcionar sin GPU dedicada y SHALL aprovecharla solo si existe, sin que ninguna función la requiera. Prueba: `perf`.

### 5.4 Privacidad y seguridad

- **REQ-01-149** THE SYSTEM SHALL tratar el perfil de capacidad, la condición declarada y el uso de modalidades como datos de categoría especial (LOPDP), con inventario de datos revisado en `design.md`. Prueba: `audit`.
- **REQ-01-150** THE SYSTEM SHALL cifrar con TLS toda comunicación del companion y del modo web con el orquestador. Prueba: `security`.
- **REQ-01-151** THE SYSTEM SHALL mantener en `THIRD_PARTY.md` la licencia, versión y origen de cada dependencia, y fallar la CI si aparece una licencia no aprobada en el artefacto distribuido (por ejemplo GPL o AGPL, o un EULA). Prueba: `audit`.
- **REQ-01-152** WHEN la persona pide borrar sus datos de la capa de entrada, THE SYSTEM SHALL borrar en el dispositivo los perfiles, calibraciones, comandos propios y la bitácora local, y confirmarlo. Prueba: `e2e`.

### 5.5 Fiabilidad del reconocimiento [SUPUESTO]

- **REQ-01-153** WHILE la persona está en reposo y sin intención de actuar, THE SYSTEM SHALL producir como máximo una activación involuntaria por cada 10 minutos de reposo en la fixture de reposo [SUPUESTO; valor inicial, se ajusta con datos del piloto]. Prueba: `replay`.
- **REQ-01-154** THE SYSTEM SHALL dar a la detección de `control.stop` un umbral más permisivo que al resto de intenciones, y detectarlo en al menos el 99% de las repeticiones de la fixture de estrés (ruido y variación de postura) [SUPUESTO]. Prueba: `replay`.
- **REQ-01-155** THE SYSTEM SHALL NOT emitir ninguna `approval.approve` durante las fixtures de ruido y de reposo, donde no hay un acto deliberado de la persona (cero falsas aprobaciones). Prueba: `replay`.

### 5.6 Segmento inicial: lesión medular cervical [SUPUESTO, a validar con personas reales]

- **REQ-01-156** WHEN la calibración de voz mide un volumen de voz bajo o variable, THE SYSTEM SHALL ajustar la ganancia y la sensibilidad del micrófono del perfil para reconocer comandos a ese volumen, y IF aun así no alcanza la calidad mínima de reconocimiento, THEN THE SYSTEM SHALL sugerir una alternativa (acercar o reubicar el micrófono, usar diadema u otra modalidad) sin culpar a la persona. Prueba: `replay` (fixtures de voz baja con ruido).
- **REQ-01-157** WHEN la persona dice o hace la orden «centrar», THE SYSTEM SHALL tomar la pose actual de la cabeza como neutral sin repetir la calibración de los gestos, y WHEN cambia de perfil de capacidad por un cambio de postura, THE SYSTEM SHALL aplicar de inmediato el ángulo de cámara y la pose neutral de ese perfil. Prueba: `replay`.
## 6. Estrategia de pruebas y fixtures

- **Fixtures de landmarks:** secuencias de blendshapes, pose de cabeza y marcas de tiempo, con metadatos (fps, versión del modelo). **Fixtures de audio:** WAV mono con transcripción esperada y metadatos (frecuencia, ruido).
- **`manifest.json` obligatorio** en cada directorio de fixtures: `synthetic: true` o `consent_ref` (REQ-01-100).
- **Arnés de reproducción:** los adaptadores aceptan una fuente inyectable (en vivo o fixture). Con la misma fixture, perfil y versión de modelo, la secuencia de intenciones es idéntica (REQ-01-015).
- **Conjuntos mínimos:** reposo, estrés (ruido y postura), por gesto, por ángulo de cámara (sentado, reclinado, acostado), por comando y por modo de voz.
- **Hardware real:** las pruebas `manual` con personas y equipos reales ocurren en el piloto y solo con consentimiento (PA-05).

## 7. Riesgos

| ID | Riesgo | Mitigación prevista |
| --- | --- | --- |
| R-01 | `faster-whisper` en CPU puede no cumplir el presupuesto de latencia para comandos cortos `[verificar]`. | Benchmark temprano (REQ-01-145) y motor alterno para comandos en `design.md` (PA-10). |
| R-02 | El seguimiento de mirada con webcam es poco preciso. | Objetivos grandes, zoom, eye tracker dedicado (REQ-01-105, REQ-01-108). Hito POST-MVP. |
| R-03 | Muchas aplicaciones no exponen todos sus elementos al sistema operativo. | Cuadrícula como respaldo (REQ-01-062, REQ-01-064). |
| R-04 | Ventanas con privilegios elevados no se pueden controlar. | Aviso explícito (REQ-01-065). |
| R-05 | Postura acostada o reclinada: ángulos de cámara poco comunes. | Compensación en la calibración y fixtures por ángulo (REQ-01-046). |
| R-06 | Los landmarks faciales pueden ser datos biométricos. | No salen del dispositivo, fixtures con consentimiento, sin reconocimiento facial (REQ-01-095, 098, 100). |
| R-07 | Licencias: Piper, n8n, GPL en la mirada. | PA-09; auditoría de licencias en la CI (REQ-01-151). |
| R-08 | Gameface está archivado. | Fork con atribución si se reutiliza código; nunca depender del repositorio original (V-10). |
| R-09 | Un "alto" dicho dentro de una frase dictada. | Regla de enunciado aislado (REQ-01-021) `[SUPUESTO]`. |

## 8. Dependencias con otras specs

| Spec | Qué necesita 01 | Qué entrega 01 |
| --- | --- | --- |
| 00 | Monorepo, CI, `packages/ui`, autenticación sin manos | Esquema `packages/intents` |
| 02 | Motor de políticas que valida aprobaciones y delegaciones | Intenciones, `actor_origin`, `stop_reachable`, latido |
| 03 | Selección de la primera tarea al terminar la calibración | Intenciones `approval.*`, perfil guardado |
| 05 | Ruta de derivación humana | `help.request_human` |
| 06 | Delegaciones del cuidador/a | Origen `caregiver` en el bus |
| 07 | Políticas de retención, exportación y borrado | Datos locales borrables (REQ-01-088, REQ-01-152) |
| 09 | Empaquetado, permisos de cámara y micrófono, archivos de modelo | Companion funcional sin conexión |

## 9. Preguntas abiertas

Las cinco mínimas (PA-01 a PA-05) y el resto están en `.kiro/specs/PREGUNTAS-ABIERTAS.md`. Las que afectan directamente a esta spec:

| ID | Pregunta | Afecta a |
| --- | --- | --- |
| PA-03 | Resuelta: discapacidad física, ejemplo lesión medular cervical. | REQ-01-156, REQ-01-157. |
| PA-05 | ¿Piloto en Cuenca y con qué consentimiento? | Fixtures reales y pruebas `manual`. |
| PA-07 | ¿Se acepta que el MVP deje fuera mirada y switch? | Grupos K y L. |
| PA-08 | ¿Se mantiene `help.request_human` en toda modalidad? | REQ-01-025. |
| PA-09 | Licencias: Piper, n8n, librerías GPL. | REQ-01-107, REQ-01-151. |
| PA-10 | Hardware real y motor de voz para comandos. | REQ-01-137 a REQ-01-148. |
| PA-11 | ¿El actuador de escritorio vive en 01? | Grupo G. |
| PA-13 | Fixtures de personas reales. | REQ-01-100. |
| PA-14 | Idioma y variante. | REQ-01-037. |

