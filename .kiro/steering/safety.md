# Seguridad y bienestar

## SF-01 No es terapia

El sistema **no diagnostica, no trata y no promete efectos clínicos**. Es una herramienta de trabajo e ingreso. La activación conductual se aplica como diseño de tareas (tareas pequeñas, concretas, elegidas por la persona, con resultado visible), no como intervención clínica.

- No se usan las palabras terapia, tratamiento, cura, diagnóstico ni "mejora tu depresión" en la interfaz, el marketing ni los mensajes de los agentes.
- No se mide ni se puntúa el estado de ánimo. No se aplican escalas clínicas [SUPUESTO].
- No se infiere salud, emociones ni estado de ánimo a partir de cámara, voz, texto ni patrones de uso. Solo se reacciona a señales explícitas de crisis (SF-03).

Por qué: vender "terapia con IA" ata el producto al regulador. Woebot cerró su app en 2025 y la ley WOPR de Illinois (agosto 2025) prohíbe que una IA diagnostique o tome decisiones terapéuticas, con multa de US$10.000 (ver la investigación base). Qué dice la regulación ecuatoriana sobre apps de salud mental con IA está sin verificar: `[verificar]` con un abogado antes del piloto (PA-12).

## SF-02 Límites de la IA

La IA:

- No da consejo médico, psicológico, legal ni financiero.
- No se hace pasar por una persona, por un terapeuta ni por la persona usuaria ante terceros.
- No decide por la persona ni sube sola el dial de autonomía (V-03).
- No manipula: sin culpa, sin urgencia artificial, sin rachas que castiguen.
- No envía, publica, cobra, borra ni comparte sin aprobación (V-01).
- Cuando no puede o no debe ayudar, lo dice, explica qué sí puede hacer y ofrece una ruta humana.

## SF-03 Protocolo de crisis

La IA no maneja la crisis por su cuenta. Deriva a una persona.

**Disparadores**

1. La persona pide ayuda humana (`help.request_human`), disponible en toda modalidad.
2. Señales explícitas de crisis detectadas con reglas definidas con asesoría de un profesional de salud mental [SUPUESTO; las reglas y los mensajes se revisan antes del piloto].

**Respuesta** [SUPUESTO en los detalles; se fijan en la spec 05]

1. Se pausan las acciones autónomas de los agentes. Las acciones con efecto externo ya estaban bajo aprobación.
2. Se muestra un mensaje **fijo y breve**, no generado por un modelo de lenguaje.
3. Se ofrecen, operables con cualquier modalidad, las **rutas humanas configuradas**: el contacto de confianza (solo si la persona lo autorizó antes) y la línea de ayuda oficial. La línea oficial es un dato de configuración, no está escrito en el código (el operador la define cuando corresponda; PA-04 queda omitida por ahora).
4. La IA no conversa sobre la crisis, no da consejos y no intenta disuadir.
5. El mensaje y los números están guardados en el dispositivo y funcionan sin conexión.
6. Se registra en la bitácora que hubo una derivación, sin el contenido. La persona puede leerlo. El operador no.
7. Después de la derivación la persona decide cuándo retomar. No hay pantalla de castigo ni de pérdida.

**Invariantes**

- Una señal de crisis siempre llega a la ruta humana (SP-5).
- La ruta humana no pasa por ningún modelo de lenguaje y no depende de la red.
- Entre un falso positivo y un falso negativo, es preferible el falso positivo.

## SF-04 Cuidador/a y contacto de confianza

- El cuidador/a actúa con permisos delegados, revocables y visibles para la persona (V-12). No aprueba por ella sin permiso explícito vigente.
- El contacto de confianza recibe alertas solo si la persona lo autorizó. El aviso lleva lo mínimo: que la persona pidió ayuda. Nunca el contenido de sus tareas.

## SF-05 Datos sensibles

Discapacidad y salud son categorías especiales bajo la LOPDP (V-09).

- Consentimiento explícito, minimización, cifrado en reposo y en tránsito, exportación y borrado a pedido.
- El perfil de capacidad y la condición declarada **nunca** se incluyen en prompts a proveedores de modelos ni en telemetría visible al operador.
- El video, el audio y los landmarks faciales no salen del dispositivo (V-06).
- El contenido de las tareas llega al proveedor del modelo solo con consentimiento explícito y mínimo necesario [SUPUESTO; ver conflicto C-01 en `PREGUNTAS-ABIERTAS.md`].

## SF-06 Condición previa para ofrecerlo a personas reales

El operador decidió construir primero el MVP y dejar el piloto para después (PA-05). Eso no cambia la vertical: V-07 y V-09 aplican desde que una persona real lo use. Antes de ofrecerlo a personas reales, como puerta de lanzamiento (no bloquea la construcción):

- Al menos una ruta humana configurada y probada (SF-03).
- Consentimiento informado por escrito y revisión legal bajo LOPDP.
- Mensajes y protocolo de crisis revisados por un profesional de salud mental.

## SF-07 Propiedades de corrección

Estas propiedades se convierten en tests en `design.md` y `tasks.md`.

| ID | Propiedad |
| --- | --- |
| SP-1 | Ninguna acción externa ocurre sin aprobación. |
| SP-2 | "Alto" siempre detiene. |
| SP-3 | Ningún frame de video sale del dispositivo. |
| SP-4 | El cuidador/a no puede aprobar en nombre de la persona sin permiso vigente. |
| SP-5 | Una señal de crisis siempre llega a la ruta humana. |
| SP-6 | El perfil de capacidad y la condición declarada nunca llegan al proveedor del modelo. |
| SP-7 | Los mensajes de crisis son fijos y no los genera un modelo. |

## SF-08 Para quien construye (agentes y personas)

- No escribas texto de interfaz con afirmaciones clínicas.
- No registres contenido privado en logs.
- Si una decisión de diseño toca crisis, datos de salud o aprobación, **consulta al operador** antes de implementarla.
- Si algo contradice la vertical, gana la vertical y se avisa.
