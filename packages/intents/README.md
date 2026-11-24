# Contrato de intenciones

Fuente única: `schema/intent.schema.json` y `schema/capability-profile.schema.json`
(JSON Schema 2020-12). Los 26 tipos del catálogo de Kiro tienen cargas útiles
cerradas. Los datos crudos de cámara y audio no son campos de una intención.

`gen/generate.py` genera modelos `TypedDict` de Python, tipos discriminados de
TypeScript, esquemas embebidos para la distribución Python y `schema/catalog.yaml`.
Los archivos generados se versionan y no se editan a mano. Los tipos describen
formas; la validación JSON Schema aplica límites de valores e invariantes.

## Uso y verificación

- `pnpm --filter @coalsense/intents generate`: regenerar con Ruff fijado en el
  workspace para obtener el mismo formato en Windows y Linux.
- `uv run --locked python packages/intents/gen/generate.py --check`: detectar deriva.
- `pnpm --filter @coalsense/intents test`: contratos independientes y pruebas de
  los validadores distribuidos.
- `pnpm --filter @coalsense/intents typecheck`: mypy y contratos de compilación
  de TypeScript, incluidos casos negativos con `@ts-expect-error`.
- `pnpm exec turbo run audit`: incluye la nueva auditoría `audit:schema`, que
  vuelve a generar en memoria y falla si falta o cambia cualquier salida.

Python exporta `Intent`, `CapabilityProfile`, `validate_intent`, `validate_profile`,
`priority_for` e `intent_types`. `ContractError` no contiene la entrada ni los
detalles privados del validador. Las entradas se copian y se rechazan NaN, infinito,
ciclos y objetos que no puedan representarse como JSON. Los formatos de fecha
se comprueban con RFC 3339; no quedan como anotaciones sin validar.

TypeScript importa los tipos desde `@coalsense/intents`. Este paquete no contiene
un bus web ni un validador de ejecución en el navegador; eso se conecta en la
tarea correspondiente de la spec 01.

## Decisiones de representación [SUPUESTO]

- `monotonic_ts`: microsegundos del reloj monotónico local (`monotonic_ns() // 1000`
  en Python). Su máximo es el entero seguro de JavaScript para que el transporte
  JSON conserve la precisión. La biblioteca común sigue midiendo intervalos en
  nanosegundos. La marca no se compara entre procesos ni se conserva entre arranques.
- Identificadores: UUIDv7 de la biblioteca común. `content_digest`: SHA-256
  hexadecimal de 64 caracteres, ligado a `pending_action_id` en ambas decisiones.
- Movimiento: `payload.mode` relativo o absoluto y `x`, `y` en coordenadas del
  actuador. El movimiento relativo acumulado se suma al coalescer; el absoluto
  conserva la posición más reciente. No se fusiona a través de un clic u otra acción.
- Cada vínculo del perfil declara su modalidad, disparador e intención. Toda
  modalidad habilitada necesita Alto, Deshacer y Ayuda humana. Los disparadores
  deben corresponder a esa modalidad.
- La condición declarada es opcional: texto, `consent_ref` y categoría `special`.
  El esquema comprueba la forma; el companion debe confirmar ese consentimiento
  con `validate_for_activation` antes de guardar o activar el perfil.

El núcleo del bus fija actor, modalidad, adaptador y prioridad desde su registro
confiable; esos campos de una publicación no acreditan por sí mismos a su emisor.

## Latido y salud de Alto

`schema/heartbeat.schema.json` versiona el evento `heartbeat`, separado del catálogo
de intenciones. Incluye instancia UUIDv7, secuencia, fechas y un estado con rutas
por modalidad. No contiene órdenes ni datos de sensores o del perfil. Los tipos
Python/TypeScript y el esquema embebido se regeneran con el mismo generador; la
auditoría de deriva cubre también restricciones que no cambian la forma del tipo.

`validate_heartbeat` exige correspondencia entre el motivo de cada ruta y su salud,
entre rutas y `stop_reachable`, y rechaza identificadores duplicados. Los objetos
son cerrados y los errores no reproducen la entrada.

`heartbeat.HeartbeatReceiver` es el contrato de vigencia para consumidores: exige
una instancia enlazada por una conexión autenticada, conserva el contador al
reconectar la misma instancia y no refresca salud con mensajes repetidos, de otra
instancia o con revisión anterior. Su tiempo se mide desde la recepción local.
Un paquete inválido o desconexión hace falso el estado; desconectar exige nuevo
enlace. La ausencia durante tres segundos `[SUPUESTO]`, configurable, también lo
hace falso. El consumidor debe consultar antes de actuar y en su monitor. La
integración con el WebSocket y los consumidores reales de políticas queda pendiente.

## Manifiestos de herramientas

`schema/tool-manifest.schema.json` versiona el contrato de T-02-006. Se generan
`ToolManifest`, `ToolEffectClass`, `ToolSchema` y sus tipos JSON en Python y
TypeScript; el esquema también se embebe y queda cubierto por la auditoría de deriva.
`validate_tool_manifest` verifica JSON real, campos obligatorios y coherencia entre
reversibilidad y compensación. Devuelve una copia y no refleja entradas en los errores.

La clase de efecto puede faltar por compatibilidad con REQ-02-022. El validador del
contrato no inventa el campo: el gateway debe convertir esa ausencia en
`external_effect`. No equivale a `read`. El registro del orquestador aplica ese valor
antes de guardar y exportar el manifiesto. Un manifiesto no autoriza ejecutar nada.

Los esquemas de entrada y salida se transportan como objetos JSON; el gateway
comprueba además su validez como JSON Schema y solo permite referencias locales.
No hay validación de ejecución en el navegador ni herramientas conectadas por
agregar este contrato compartido.
