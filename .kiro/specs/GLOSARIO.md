# Glosario

Un concepto, un nombre. Si un documento usa un término de la columna "No usar", es un error y se corrige.

Estado: borrador de la fase 1. Se amplía en cada fase y se revisa al cerrar la fase de tareas.

## Producto y vertical

| Término | Definición | No usar |
| --- | --- | --- |
| **Persona usuaria** (en el texto: "la persona") | Quien usa el sistema para trabajar. Tiene discapacidad física, depresión, o ambas. | usuario, paciente, beneficiario, discapacitado |
| **Cuidador/a** | Quien configura el equipo y acompaña a la persona, con permisos delegados y revocables. | asistente (se confunde con la IA), tutor, sustituto |
| **Sustituto** | Figura legal ecuatoriana de la cuota del 4% (familiar que cuida a una persona con discapacidad severa). Solo se usa en la spec 08. No es sinónimo de cuidador/a. | usarlo como sinónimo de cuidador/a |
| **Contacto de confianza** | Persona que recibe alertas solo si la persona lo autorizó. | contacto de emergencia, familiar |
| **Operador** | Quien administra la plataforma. No ve contenido privado. | admin, superusuario |
| **Empresa cliente** | Empresa que publica trabajos, recibe entregables y paga (fase 2). | «cliente» a secas para una empresa, empleador |
| **Ciclo de control** | Secuencia que se repite en cada tarea: la persona elige, los agentes ejecutan, la persona revisa y aprueba, el resultado sale al mundo, queda un logro. | flujo, journey, loop |
| **Tarea** | Unidad concreta de trabajo con resultado visible, que elige la persona. | trabajo (reservado a la fase 2), misión, reto, meta |
| **Micro-paso** | Parte pequeña de una tarea que la persona puede completar y ver. | subtarea, paso |
| **Trabajo** | Oferta publicada por una empresa cliente (fase 2). | tarea (en ese contexto) |
| **Entregable** | Resultado de una tarea que sale al mundo (correo enviado, documento, publicación lista). | output, producto |
| **Logro** | Registro permanente de una tarea completada y aprobada. Solo suma. | insignia, badge, racha, puntos |
| **Siguiente tarea** | Tarea que el sistema propone, un poco más grande que la anterior. La persona la acepta o no. | meta, objetivo |
| **Dial de autonomía** | Ajuste, por tipo de tarea, de cuánto hace la IA sola. Por defecto la persona aprueba todo. Solo la persona lo sube. | nivel de automatización, modo autónomo |
| **Aprobación** | Acto explícito de la persona de aceptar o rechazar una acción con efecto externo, con la modalidad que use. | confirmación (salvo al citar la vertical original), visto bueno, OK |
| **Acción con efecto externo** | Acción que sale de la máquina o cambia algo fuera: enviar, publicar, cobrar, borrar, compartir. | acción crítica, acción sensible |
| **Alto** | Intención `control.stop`: detiene toda actuación en curso. Existe en todas las modalidades. | stop, parar, cancelar (cancelar descarta un paso o un diálogo; no detiene) |
| **Deshacer** | Intención `control.undo`: revierte la última acción reversible. | revertir, atrás |
| **Ruta de alto** | Disparador concreto de Alto en una modalidad (palabra, gesto, tecla, switch). | botón de pánico |
| **Ayuda humana** | Intención `help.request_human`: la persona pide que la atienda una persona. | SOS, pánico, emergencia (reservado a la línea de emergencias) |
| **Señal de crisis** | Señal explícita que activa la derivación humana (spec 05). | alerta de riesgo, detección de depresión |
| **Derivación** | Paso de la crisis a una persona (contacto de confianza o línea de ayuda oficial). | escalamiento |
| **Línea de ayuda oficial** | Línea pública de ayuda en crisis que se muestra a la persona (por definir, PA-04). | línea de crisis, hotline |

## Capa de entrada (spec 01)

| Término | Definición | No usar |
| --- | --- | --- |
| **Modalidad de entrada** | Canal por el que la persona actúa: voz, cabeza y gestos, mirada, switch, teclado y mouse. | método de entrada, input, dispositivo |
| **Adaptador de entrada** | Módulo que convierte las señales de una modalidad en intenciones. | driver, plugin, conector |
| **Intención** | Mensaje normalizado y tipado (esquema de `packages/intents`) que expresa lo que la persona quiere hacer, sin importar la modalidad. | evento (es más amplio), comando (es la frase hablada), acción |
| **Bus de intenciones** | Componente que recibe las intenciones de los adaptadores y las entrega a los consumidores, con prioridades. | cola de eventos, event bus |
| **Prioridad `preemptive`** | Clase de intención que se entrega antes que cualquier otra: Alto, Deshacer, Ayuda humana. | urgente |
| **Origen del actor** (`actor_origin`) | Quién actúa: `person`, `caregiver` o `system`. Lo fija la sesión autenticada. | rol del emisor |
| **Perfil de capacidad** | Configuración de la persona: modalidades habilitadas, umbrales, tiempos, vínculos y preferencias. No contiene diagnóstico. | perfil médico, perfil de discapacidad, perfil de usuario |
| **Condición declarada** | Campo opcional que la persona completa por voluntad propia para ajustar su perfil. Categoría especial. | diagnóstico |
| **Calibración** | Proceso que ajusta una modalidad al cuerpo y la voz de la persona y fija umbrales. | configuración inicial, setup |
| **Zona de práctica** | Espacio seguro de la calibración donde la persona ejecuta un vínculo y ve un efecto visible. | sandbox, tutorial |
| **Gesto** | Movimiento facial voluntario detectado desde los blendshapes. | expresión (sugiere emoción) |
| **Umbral del gesto** | Valor de blendshape, por gesto y por persona, desde el cual el gesto cuenta como activado. | sensibilidad (se reserva al puntero) |
| **Sostenimiento** | Tiempo que debe mantenerse un gesto para activarse. Lo ajusta la persona. | debounce (término de implementación) |
| **Dwell** | Permanencia de la mirada sobre un objetivo durante el tiempo que la persona fijó, que activa el objetivo. | hover, fijación |
| **Switch** | Pulsador de una sola activación (tecla, botón, dispositivo HID o gesto usado como pulsador). | botón, pulsador |
| **Escaneo** | Recorrido automático de opciones resaltadas; la persona elige activando el switch. | barrido |
| **Modo de voz** | Estado interno de la modalidad de voz: comando, dictado o sueño. | modalidad (ese es otro concepto) |
| **Comando de voz** | Frase corta que la persona dice y que se traduce en una intención. | orden, instrucción |
| **Archivo de comandos** | Archivo declarativo que define comandos de voz (frase → intención, contexto, parámetros). | script, macro |
| **Dictado** | Modo de voz que transcribe texto libre. | transcripción (es el resultado) |
| **Números en pantalla** | Superposición que numera los elementos accionables para activarlos diciendo el número. | etiquetas, hints |
| **Cuadrícula** | Superposición de celdas numeradas que se refinan para ubicar un punto sin puntería fina. | grid, malla |
| **Actuador** | Componente del companion que ejecuta intenciones en el sistema operativo. | ejecutor, driver |
| **Companion** | Aplicación de escritorio que hospeda la capa de entrada y el actuador. | app de escritorio, agente local |
| **Modo web** | Ejecución de la visión en el navegador, sin instalación. | versión web de la entrada |
| **Fixture** | Grabación reproducible (landmarks o audio) usada como entrada de prueba. | mock, sample |

## Orquestación y datos

| Término | Definición | No usar |
| --- | --- | --- |
| **Orquestador** | Componente que razona, planifica y delega. No llama APIs directo. | cerebro, controlador |
| **Cliente** | Aplicación del lado de la persona (companion o web) que se conecta al orquestador. No es una empresa. | frontend |
| **Agente** | Ejecutor de una parte de una tarea, delegado por el orquestador. Si un texto de la vertical dice "subagente", se refiere a este mismo concepto. | bot (como sinónimo de agente) |
| **Herramienta** | Capacidad con interfaz fija que ejecuta una acción, expuesta por el gateway. | plugin, skill (reservado a las skills de diseño) |
| **Gateway de herramientas** | Único punto por el que el sistema llama APIs externas. | proxy, router de APIs |
| **Motor de políticas** | Componente que decide si una acción puede ejecutarse, según aprobación, autonomía y permisos. | reglas de negocio, guardia |
| **Bitácora** | Registro legible por la persona de todo lo que se ejecutó. Almacena localmente cuando no hay conexión. | log (técnico), historial, auditoría |
| **Memoria** | Lo que el sistema recuerda para tareas futuras. | contexto (es lo que ve un modelo en una llamada) |
| **Ley de Arthur** | Conjunto de reglas V-08: sin API directa, sin escritura directa a producción, sin acción externa sin política, todo en bitácora. | reglas de seguridad |
| **LOPDP** | Ley Orgánica de Protección de Datos Personales de Ecuador. | GDPR local |

## Decisiones de nomenclatura (confirmadas por el operador el 2026-11-14)

1. **Aprobación vs. confirmación.** Tu texto usa ambas para el mismo acto. Elegí **aprobación** en todo el repositorio. El nombre de la spec 02 ("motor de políticas de confirmación") pasa a "motor de políticas".
2. **Cuidador/a vs. sustituto.** Tu lista de actores dice "cuidador/a o sustituto". La investigación usa "sustituto" con un sentido legal distinto (cuota del 4%). Elegí **cuidador/a** para el actor y reservé "sustituto" a la spec 08.
3. **Tarea vs. trabajo.** **Tarea** en el MVP; **trabajo** solo para la oferta de una empresa en la fase 2.
4. **Meta.** Tu texto dice "la siguiente meta es un poco más grande". Elegí **siguiente tarea** para no crear un concepto nuevo.

## Términos agregados en la fase 2

| Término | Definición | No usar |
| --- | --- | --- |
| **Plan** | Lista de micro-pasos que el orquestador propone para una tarea y que la persona ve y puede editar antes de ejecutar. | workflow, pipeline |
| **Propuesta** | Resultado de un agente (borrador, documento, publicación) que no tiene efecto externo hasta que se aprueba. | output final |
| **Sello de aprobación** (`ApprovalGrant`) | Prueba firmada de que la persona aprobó una acción concreta: atada al identificador de la acción y al resumen criptográfico de su contenido, de un solo uso, sin vencimiento por tiempo. | token, permiso |
| **Retención** | Pausa corta y visible entre la aprobación y el despacho de una acción externa, en la que Alto cancela. La persona la configura. | cuenta regresiva, plazo |
| **Detenido** | Estado de una tarea tras Alto. Solo la persona la reanuda. | pausada, cancelada |
| **Nivel de autonomía** | Valor del dial para un tipo de tarea: N0, N1 o N2 (spec 03). Nunca elimina la aprobación de una acción externa. | modo, nivel de IA |
| **Catálogo de herramientas** | Conjunto de herramientas que una persona tiene habilitadas, incluidas las de servidores MCP. | marketplace, plugins |
| **Servidor MCP** | Servidor del Model Context Protocol conectado al gateway de herramientas, que aporta herramientas. | conector, integración |
| **Clase de efecto** | Clasificación de cada herramienta: `read` (lee), `internal_write` (cambia datos propios del sistema) o `external_effect` (sale de la máquina o cambia algo fuera). Lo no clasificado se trata como `external_effect`. | nivel de riesgo |
| **Delegación** | Permiso concreto, revocable y visible que la persona da a un cuidador/a (spec 06). | acceso, rol |
| **Consentimiento** | Autorización explícita, por categoría y revocable, que la persona da para un uso de sus datos (spec 05 y 07). | aceptación, términos |
| **Ruta humana** | Camino de derivación a una persona: contacto de confianza o línea de ayuda oficial, definidas por configuración. | canal de escalamiento |
| **Entorno de prueba / de producción** | Los dos entornos desplegados del sistema, más el desarrollo local. | staging, QA, prod |
| **Primera tarea** | Tarea guiada que la persona completa al final de la calibración, en la sesión 1. | tutorial, demo |
| **Panel del cuidador/a** | Pantalla del cuidador/a, limitada por las delegaciones vigentes. | backoffice, admin |


