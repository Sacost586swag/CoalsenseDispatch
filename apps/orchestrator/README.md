# orchestrator

FastAPI (uv). Planificador, agentes, motor de políticas, memoria y bitácora.

`auth/` contiene acceso por código, emparejamiento, sesiones, revocación y roles.
Las rutas se prueban con puertos simulados; esto no acredita un despliegue operativo.

`agents/document/` contiene el modelo inmutable de bloques y las propuestas de
edición de T-04-001. Cada bloque tiene `id`, `kind`, `text` y `order` (desde uno).
`parse_command` reconoce órdenes completas: «más corto el 3», «más formal el 2»,
«borra el 4», «agrega después del 2: texto» y «reemplaza el 2: texto». No interpreta
órdenes incrustadas en notas ni adivina entradas ambiguas.

[SUPUESTO] El reconocimiento entrega números ASCII sin ceros iniciales. Tras los
dos puntos se consume un espacio separador; el resto del texto se conserva exacto.
Esta gramática no es un reconocedor de voz ni una autorización para ejecutar comandos.

`propose_edit` devuelve un antes y un después sin modificar el documento. Su método
`accept` rechaza una base distinta. Insertar y borrar renumeran solo los bloques que
siguen; los identificadores y el texto de los demás se conservan. El último bloque
no se elimina. Los textos se excluyen de `repr` y de los mensajes de error.

Abreviar y formalizar usan un puerto de reescritura inyectado, sin cliente de modelo
ni acceso de red en este módulo. El futuro adaptador deberá comprobar consentimiento
y pasar por el gateway. Sin adaptador no hay variante. Sigue pendiente integrar las
propuestas con el editor web, el servicio de versiones con control atómico de revisión,
el cifrado con la clave de la persona y las herramientas reales. No se cierra T-04-001
ni sus dependencias únicamente por probar este módulo.

`gateway/manifest.py` valida manifiestos contra el contrato compartido, comprueba
los esquemas de entrada y salida y clasifica una clase de efecto ausente como
`external_effect`. `registry.py` exige registro explícito y rechaza nombres repetidos.
Los contratos guardados son inmutables; exportarlos devuelve una copia. Registrar
no conecta, habilita ni ejecuta una herramienta y no concede aprobación.

Las herramientas reversibles declaran el nombre de su compensación; las demás no
pueden declararla. Las categorías de datos y el proveedor son obligatorios.
[SUPUESTO] Los nombres usan segmentos en minúsculas separados por puntos; proveedor
y categorías son identificadores en minúsculas. Los esquemas solo aceptan referencias
locales. El registro valida la forma de los esquemas; las referencias locales que no
resuelven hacen fallar la validación del valor. No se consultan esquemas externos.

Quedan pendientes el catálogo curado con implementaciones reales, la habilitación
por persona y los adaptadores de producción. El ejecutor interno exige sello,
consentimiento y registro, y usa como clave de idempotencia el ID de la acción.
La declaración de un manifiesto no acredita la seguridad de su implementación.

`agents/prompt_builder.py` admite solo instrucción del paso, texto de tarea y
preferencias de texto. La selección del rango es explícita, en puntos de código
Python; no toma offsets UTF-16 del navegador. Solo incluye las preferencias elegidas
por el llamador. El vocabulario inicial de tono, idioma y formato es cerrado y está
marcado como supuesto en el código. No admite perfiles ni objetos de contexto libres.

`gateway/consent_client.py` define la consulta asíncrona de consentimiento por persona,
categoría y proveedor. La implementación por defecto niega siempre.
El constructor consulta `llm_content` en cada preparación; errores, respuestas que
no son booleanos y ausencia de consentimiento impiden devolver el prompt. La
cancelación se propaga. Preparar no concede permiso futuro: el gateway debe consultar
de nuevo justo antes de transmitir. Todavía no hay registro real de consentimientos
ni proveedor de modelos conectado.

`persistence/` conecta a PostgreSQL con TLS verificado por defecto. La excepción sin
TLS solo permite loopback explícito de prueba. El servicio recibe un `Principal`
del servidor y obtiene de él la persona; no acepta un `person_id` del cuerpo. Guarda
metadatos de tarea, consulta y pausa con control de revisión. Conserva N0 y no ofrece
una operación que eleve autonomía. Las escrituras requieren un puerto de política
que niega si falta o falla; las pruebas conceden permiso mediante una implementación
simulada explícita. Los detalles están en `docs/PERSISTENCIA.md`.

`audit/` contiene tipos cerrados de metadatos, verificación SHA-256 por persona y
acceso transaccional a `audit_event`. Crear y pausar tareas ya escriben en esta
cadena. El rol de ejecución solo puede seleccionar e insertar filas propias;
PostgreSQL valida la huella, la secuencia y el enlace. El puerto de servidor
`append_audit` confirma la transacción antes de devolver el evento. No se expuso
una ruta de cliente para inventar eventos. Los consumidores y límites pendientes
están en `docs/BITACORA.md`.

`persistence/migrations.py` aplica SQL versionado e historial en una transacción,
rechaza deriva de archivos y excluye migradores simultáneos. La conversión conserva
los eventos provisionales. `tools/migrate.py` usa credenciales administrativas
separadas; por defecto solo informa el plan y aplica con `--apply`. La configuración
y los ejemplos están en `docs/PERSISTENCIA.md`.

`policy/` evalúa solicitudes mínimas contra manifiestos, contexto de servidor,
salud del Alto y versiones persistidas por persona. Mantiene N0 con aprobación,
exige aprobación para todo efecto externo y espera la bitácora confirmada. Fallos
de consulta o registro niegan. `0004_policy.sql` incorpora versiones inmutables,
activación auditada atómica y referencias de acción y regla en el formato v2 de la
cadena, conservando v1. `ApprovalService` vincula cada sello a la vista exacta,
la persona y su sesión. `ExternalExecutor` consume el sello una sola vez y permite
cancelar la retención con Alto. Ambos se prueban con datos y adaptadores sintéticos.
La recepción por API y la conexión a proveedores siguen pendientes.
Las guardas, supuestos y límites están en `docs/POLITICAS.md`.

`consent/` aplica una decisión vigente por persona, categoría, proveedor y
versión del aviso. El gateway consulta justo antes de consumir el sello.
`0009_consent.sql` guarda sobres opacos por persona con RLS. El registro de
producción requiere el adaptador de cifrado T-07-003 y el catálogo de avisos.
Los detalles están en `docs/PERSISTENCIA.md`.

Verificación local:

```powershell
.venv/Scripts/python.exe -m pytest apps/orchestrator/tests -q
.venv/Scripts/python.exe -m ruff check apps/orchestrator
.venv/Scripts/python.exe -m mypy apps/orchestrator/src
pnpm --filter @coalsense/orchestrator test:integration
```
