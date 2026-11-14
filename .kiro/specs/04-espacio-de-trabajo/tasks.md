# Tareas: 04 Espacio de trabajo

**Requisitos:** `requirements.md`. **Diseño:** `design.md`. **Marcas:** `[CODEX]` paralelizable por Codex; `[UI]` interfaz.

**Contexto común (léelo una vez).**
- Interfaz en `apps/web/src/features/workspace/` (Next.js + `packages/ui`); agentes y herramientas en `apps/orchestrator/src/coalsense_orchestrator/agents/{email,document,social}/` y `.../gateway/tools/`; pruebas en `apps/orchestrator/tests/workspace/` y `apps/web/tests/`.
- Tareas del MVP: (1) correo o mensaje profesional, (2) notas dictadas a documento, (3) publicación para redes **lista para publicar** (no se publica en el MVP).
- Clases de efecto: `email.send` y `doc.share` son `external_effect` (exigen sello sobre el contenido exacto); `email.draft`, `doc.save`, `doc.export`, `social.prepare` son `internal_write`; `llm.complete` y `doc.structure` son `read`.
- Los documentos se editan por **número de bloque**, sin selección con puntero, arrastre ni doble clic.
- La tarjeta de aprobación muestra el contenido exacto, no un resumen generado por el modelo.

## Orden de dependencias

```
Ola 0 (specs 00, 02, 03): T-00-014, T-00-015, T-02-007, T-02-009, T-02-016, T-03-005, T-03-006
Ola 1: T-04-001, T-04-003
Ola 2: T-04-002, T-04-004, T-04-005, T-04-007, T-04-009
Ola 3: T-04-006, T-04-008, T-04-010, T-04-011
Ola 4: T-04-012, T-04-013, T-04-014, T-04-015, T-04-016
```

---

### T-04-001 Modelo de bloques y edición por número
- **Requisitos:** REQ-04-001, REQ-04-002, REQ-04-003, REQ-04-006
- **Depende de:** T-02-016
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/agents/document/{blocks,edit_commands}.py`, `apps/orchestrator/tests/workspace/test_blocks_edit.py`
- **Qué hacer:** documento como lista de bloques (`id`, `kind`, `text`, `order`). Interpretar instrucciones dictadas como `{verbo, bloque, parámetros}` («más corto el 3», «más formal el 2», «borra el 4», «agrega después del 2») y aplicarlas solo al bloque indicado devolviendo el antes y el después. Permitir dictar texto nuevo en la posición de un bloque.
- **Prueba:** `apps/orchestrator/tests/workspace/test_blocks_edit.py` (unit): cada verbo afecta solo su bloque; devuelve antes y después.
- **Terminado cuando:** la prueba pasa.

### T-04-002 Editor accesible de bloques numerados [UI]
- **Requisitos:** REQ-04-001, REQ-04-005, REQ-04-006
- **Depende de:** T-04-001, T-00-014
- **Archivos:** `apps/web/src/features/workspace/{BlockEditor,BeforeAfter,ReadAloud}.tsx`, `apps/web/tests/e2e/block-editor.spec.ts`
- **Qué hacer:** editor con el número de cada bloque visible, selección por número con cualquier modalidad, vista del antes y el después de cada edición, y lectura en voz alta con voz local bloque por bloque con pausa y reanudación. Nada requiere seleccionar texto con puntero, arrastrar ni doble clic.
- **Prueba:** `apps/web/tests/e2e/block-editor.spec.ts` (e2e y a11y): editar solo con teclado e intenciones simuladas; leer en voz alta y pausar.
- **Terminado cuando:** la prueba pasa.

### T-04-003 Versiones y conservación de borradores
- **Requisitos:** REQ-04-004, REQ-04-007
- **Depende de:** T-04-001, T-02-002
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/agents/document/versions.py`, `apps/orchestrator/migrations/0007_deliverables.sql`, `apps/orchestrator/tests/workspace/test_versions.py`
- **Qué hacer:** `deliverable` y `version` (con `parent_id`, `author`, bloques cifrados con la clave de la persona). Cada cambio aceptado crea una versión; `control.undo` o un número vuelven a una versión anterior. Los borradores se conservan si la persona pausa, cierra la aplicación o cae el servicio.
- **Prueba:** `apps/orchestrator/tests/workspace/test_versions.py` (unit e integration): volver a una versión previa; reiniciar el servicio conserva el borrador.
- **Terminado cuando:** la prueba pasa.

### T-04-004 Agente de correo y borradores
- **Requisitos:** REQ-04-020, REQ-04-021
- **Depende de:** T-02-009, T-02-016, T-04-003
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/agents/email/{agent,prompts}.py`, `apps/orchestrator/src/coalsense_orchestrator/gateway/tools/email_draft.py`, `apps/orchestrator/tests/workspace/test_email_agent.py`
- **Qué hacer:** a partir de destinatario, propósito y tono (por dictado o selección) producir borrador con asunto y cuerpo y variantes (más formal, más breve, más cálido) como propuestas. Herramienta `email.draft` (`internal_write`, reversible).
- **Prueba:** `apps/orchestrator/tests/workspace/test_email_agent.py` (unit e integration con modelo simulado): produce asunto, cuerpo y tres variantes; el borrador no tiene efecto externo.
- **Terminado cuando:** la prueba pasa.

### T-04-005 Conexión de la cuenta de correo (OAuth) y fallos de conexión
- **Requisitos:** REQ-04-022, REQ-04-028
- **Depende de:** T-02-007, T-00-011
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/gateway/connections/{oauth,store}.py`, `apps/web/src/features/workspace/ConnectMail.tsx`, `apps/orchestrator/tests/workspace/test_connection.py`
- **Qué hacer:** autorizar la cuenta de correo de la persona por OAuth (completable sin manos o con ayuda del cuidador/a) para un proveedor [SUPUESTO, PA-15]. Credenciales cifradas con la clave de la persona y legibles solo por el gateway. Si el proveedor rechaza el envío o la conexión caduca, decirlo en lenguaje llano, conservar el borrador y ofrecer reconectar.
- **Prueba:** `apps/orchestrator/tests/workspace/test_connection.py` (security y e2e): los agentes no pueden leer las credenciales; la conexión caducada conserva el borrador y ofrece reconectar.
- **Terminado cuando:** la prueba pasa.

### T-04-006 Envío de correo con aprobación
- **Requisitos:** REQ-04-023, REQ-04-024, REQ-04-025, REQ-04-026, REQ-04-027
- **Depende de:** T-04-004, T-04-005, T-02-011, T-03-006
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/gateway/tools/email_send.py`, `apps/web/src/features/workspace/EmailApproval.tsx`, `apps/orchestrator/tests/workspace/test_email_send.py`
- **Qué hacer:** `email.send` como `external_effect` nativo. La tarjeta muestra remitente, destinatarios, asunto y cuerpo exactos, destaca los destinatarios que no estaban en la tarea original o se añadieron después y puede leerlos en voz alta. Sin sello válido sobre el contenido exacto no se envía. Al terminar, mostrar el resultado y guardar copia del enviado en la tarea. Ofrecer «enviar primero a mí» como prueba, también con aprobación.
- **Prueba:** `apps/orchestrator/tests/workspace/test_email_send.py` (security y e2e): sin sello no sale; cambiar un destinatario tras aprobar invalida el sello; destinatario nuevo se resalta.
- **Terminado cuando:** la prueba pasa.

### T-04-007 Agente de documento: notas dictadas a documento
- **Requisitos:** REQ-04-030, REQ-04-031, REQ-04-035
- **Depende de:** T-02-009, T-02-016, T-04-001
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/agents/document/{agent,structure}.py`, `apps/orchestrator/tests/workspace/test_document_agent.py`, `apps/orchestrator/tests/workspace/fixtures/dictations/*.yaml`
- **Qué hacer:** `doc.structure` (`read`) propone título, secciones, listas y resumen opcional sin añadir hechos, y **marca** los fragmentos reformulados de forma importante. Permitir añadir más dictado a un documento existente sin rehacerlo. Conjunto de dictados de muestra con resultados revisados.
- **Prueba:** `apps/orchestrator/tests/workspace/test_document_agent.py` (e2e con modelo simulado): conserva el contenido, marca reformulaciones, añadir dictado no rehace lo anterior.
- **Terminado cuando:** la prueba pasa.

### T-04-008 Guardar, exportar y compartir documentos
- **Requisitos:** REQ-04-032, REQ-04-033, REQ-04-034
- **Depende de:** T-04-007, T-02-011
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/gateway/tools/{doc_save,doc_export,doc_share}.py`, `apps/orchestrator/tests/workspace/test_doc_tools.py`
- **Qué hacer:** guardar en Markdown y exportar a DOCX y PDF [SUPUESTO, PA-16] como acciones `internal_write` sin aprobación. `doc.share` (enlace, correo o servicio conectado) es `external_effect`: requiere sello y la tarjeta muestra con quién se comparte y con qué permisos.
- **Prueba:** `apps/orchestrator/tests/workspace/test_doc_tools.py` (unit y security): guardar y exportar no piden aprobación; compartir sin sello se rechaza.
- **Terminado cuando:** la prueba pasa.

### T-04-009 Agente de publicación: texto, límites y texto alternativo
- **Requisitos:** REQ-04-040, REQ-04-041, REQ-04-042, REQ-04-043
- **Depende de:** T-02-009, T-02-016, T-04-001
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/agents/social/{agent,networks}.py`, `apps/orchestrator/config/social_networks.yaml`, `apps/orchestrator/src/coalsense_orchestrator/gateway/tools/social_prepare.py`, `apps/orchestrator/tests/workspace/test_social_agent.py`
- **Qué hacer:** a partir de tema, red y tono, producir texto y variantes aplicando límites de longitud y formato de la red desde configuración y avisando si se superan; sugerir texto alternativo para imágenes adjuntas. Estado final «lista para publicar» guardado en la tarea. **No publica por sí misma** en el MVP.
- **Prueba:** `apps/orchestrator/tests/workspace/test_social_agent.py` (unit): el límite de una red se respeta y avisa; no existe ninguna ruta de código que publique.
- **Terminado cuando:** la prueba pasa.

### T-04-010 Publicación: datos de terceros, copiar y regla de publicar
- **Requisitos:** REQ-04-044, REQ-04-045, REQ-04-046
- **Depende de:** T-04-009
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/agents/social/{pii_notice,publish_rule}.py`, `apps/web/src/features/workspace/CopyToClipboard.tsx`, `apps/orchestrator/tests/workspace/test_social_extras.py`
- **Qué hacer:** avisar si el texto parece incluir datos personales de terceros (teléfonos, correos, direcciones) y pedir a la persona que decida; copiar al portapapeles con una sola orden (`clipboard.copy`, local); dejar definido que cualquier herramienta futura que publique es `external_effect` con aprobación.
- **Prueba:** `apps/orchestrator/tests/workspace/test_social_extras.py` (unit): detecta datos de terceros de muestra; una herramienta de publicación de ejemplo sin clase queda como `external_effect`.
- **Terminado cuando:** la prueba pasa.

### T-04-011 Catálogo de herramientas conectadas [UI]
- **Requisitos:** REQ-04-050, REQ-04-051, REQ-04-052, REQ-04-053
- **Depende de:** T-02-022, T-00-015
- **Archivos:** `apps/web/src/features/workspace/ToolCatalog.tsx`, `apps/web/tests/e2e/tool-catalog.spec.ts`
- **Qué hacer:** pantalla con las herramientas habilitadas y las disponibles del catálogo curado: qué hace cada una, qué datos recibe y si puede cambiar algo fuera de la plataforma. Habilitar o deshabilitar pide una aprobación que describe el efecto y se aplica de inmediato. Estado de cada herramienta con texto (conectada, desconectada, con error) y reconectar. No muestra nada fuera del catálogo curado del MVP.
- **Prueba:** `apps/web/tests/e2e/tool-catalog.spec.ts` (e2e y a11y).
- **Terminado cuando:** la prueba pasa.

### T-04-012 Estados de pantalla del editor y del catálogo [UI]
- **Requisitos:** REQ-04-054
- **Depende de:** T-04-002, T-04-011
- **Archivos:** `apps/web/src/features/workspace/states.tsx`, `apps/web/tests/e2e/workspace-states.spec.ts`
- **Qué hacer:** *cargando* (se puede seguir editando y usar Alto), *vacío* (ofrecer elegir una tarea), *error* (reintentar o editar a mano) y *sin conexión* (conservar y editar a mano) en el editor y el catálogo, con `StateScreen`.
- **Prueba:** `apps/web/tests/e2e/workspace-states.spec.ts` (e2e y a11y).
- **Terminado cuando:** la prueba pasa.

### T-04-013 Accesibilidad de las pantallas de 04 [CODEX]
- **Requisitos:** REQ-04-060
- **Depende de:** T-04-002, T-04-006, T-04-011, T-04-012
- **Archivos:** `apps/web/tests/a11y/workspace.spec.ts`
- **Qué hacer:** suite con axe-core (WCAG 2.2 AA), 44×44 px, ausencia de límites de tiempo y operabilidad solo con teclado para el editor, las tres tareas y el catálogo.
- **Prueba:** `apps/web/tests/a11y/workspace.spec.ts` (a11y).
- **Terminado cuando:** pasa en la CI.

### T-04-014 Rendimiento del primer borrador [CODEX]
- **Requisitos:** REQ-04-061
- **Depende de:** T-04-004, T-04-007, T-04-009
- **Archivos:** `apps/orchestrator/tests/perf/test_first_draft.py`
- **Qué hacer:** medir con proveedor simulado el tiempo al primer borrador (p95 ≤ 15 s) [SUPUESTO] y ajustar con datos reales.
- **Prueba:** `apps/orchestrator/tests/perf/test_first_draft.py` (perf).
- **Terminado cuando:** pasa o el presupuesto se actualiza con una nota.

### T-04-015 Consentimiento y cifrado de entregables [CODEX]
- **Requisitos:** REQ-04-062, REQ-04-063
- **Depende de:** T-04-003, T-02-008
- **Archivos:** `apps/orchestrator/tests/workspace/test_consent_encryption.py`
- **Qué hacer:** pruebas de que ningún contenido llega a un proveedor de modelo sin consentimiento vigente de esa categoría y de que borradores, versiones y entregables se guardan cifrados con la clave de la persona.
- **Prueba:** `apps/orchestrator/tests/workspace/test_consent_encryption.py` (security).
- **Terminado cuando:** la prueba pasa.

### T-04-016 Auditoría de lenguaje de consejo [CODEX]
- **Requisitos:** REQ-04-064
- **Depende de:** T-00-009
- **Archivos:** `tools/audit/tests/test_copy_workspace.py`
- **Qué hacer:** extender la auditoría de textos para que falle si la interfaz o las plantillas de propuestas de 04 contienen consejo médico, psicológico, legal o financiero.
- **Prueba:** `tools/audit/tests/test_copy_workspace.py` (audit).
- **Terminado cuando:** la prueba pasa.
