# Tareas: 07 Privacidad y datos

**Requisitos:** `requirements.md`. **Diseño:** `design.md`. **Marcas:** `[CODEX]` paralelizable por Codex; `[UI]` interfaz.

**Contexto común (léelo una vez).**
- Código en `apps/orchestrator/src/coalsense_orchestrator/privacy/` y `.../crypto/`; datos locales en `apps/companion/src/coalsense_companion/profile/`; inventario en `docs/data-inventory.yaml`; pruebas en `apps/orchestrator/tests/privacy/`.
- Lo marcado `[verificar con abogado]` es una hipótesis legal sin confirmar; estas tareas implementan el comportamiento, no dan asesoría legal.
- Jerarquía de claves: clave maestra (servicio de claves, PA-20) → clave de cifrado de claves por entorno → **clave de datos por persona** que cifra el contenido. Destruir la clave de datos de una persona borra su contenido en base, memoria vectorial y copias de seguridad (borrado criptográfico).
- **Retención cero:** audio, video, landmarks, prompts y respuestas de modelos no se guardan nunca más allá de lo que la persona ve en sus propuestas.
- El operador no tiene ninguna vía de lectura de contenido.

## Orden de dependencias

```
Ola 0 (specs 00, 02): T-00-007, T-00-008, T-00-011, T-02-002, T-02-003, T-02-007
Ola 1: T-07-001, T-07-003, T-07-006
Ola 2: T-07-002, T-07-004, T-07-005, T-07-007, T-07-013, T-07-014
Ola 3: T-07-008, T-07-009, T-07-010, T-07-015
Ola 4: T-07-011, T-07-012
```

---

### T-07-001 Inventario de datos, clasificación y registro de tratamiento
- **Requisitos:** REQ-07-001, REQ-07-002, REQ-07-003, REQ-07-005
- **Depende de:** T-00-006
- **Archivos:** `docs/data-inventory.yaml`, `tools/audit/audit_data_inventory.py`, `tools/audit/tests/test_audit_data_inventory_full.py`, `docs/processing-register.md` (generado)
- **Qué hacer:** inventario versionado con cada dato personal (categoría, finalidad, dónde vive, quién lo ve, retención, si es categoría especial). Clasificar como categoría especial: perfil de capacidad, condición declarada, uso de modalidades, eventos de crisis, consentimientos y contenido de tareas. Auditoría que falla si un campo nuevo de la base de datos o del esquema de intenciones no figura en el inventario. Generar un registro de actividades de tratamiento a partir del inventario `[verificar con abogado si la LOPDP lo exige]`.
- **Prueba:** `tools/audit/tests/test_audit_data_inventory_full.py` (audit): un campo nuevo sin inventariar falla; las categorías especiales están clasificadas.
- **Terminado cuando:** la prueba pasa y el registro de tratamiento se genera.

### T-07-002 Sin diagnóstico y retención cero
- **Requisitos:** REQ-07-004, REQ-07-046
- **Depende de:** T-07-001
- **Archivos:** `apps/orchestrator/tests/privacy/test_zero_retention.py`, `apps/orchestrator/tests/privacy/test_no_diagnosis.py`
- **Qué hacer:** pruebas que recorren el sistema con datos de muestra y verifican que no se guarda ningún diagnóstico salvo la condición declarada voluntariamente, y que audio, video, landmarks, prompts y respuestas de modelos no quedan almacenados en base, disco, caché, registros ni métricas.
- **Prueba:** `apps/orchestrator/tests/privacy/test_zero_retention.py` (security).
- **Terminado cuando:** las pruebas pasan.

### T-07-003 Servicio de claves y cifrado de aplicación
- **Requisitos:** REQ-07-011, REQ-07-012, REQ-07-015, REQ-07-016
- **Depende de:** T-00-007, T-02-002
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/crypto/{kms_client,dek,envelope,rotation}.py`, `apps/orchestrator/tests/privacy/test_crypto.py`
- **Qué hacer:** cliente del servicio de claves (PA-20) con jerarquía clave maestra → KEK por entorno → DEK por persona; cifrado de aplicación de contenido, memoria, credenciales de herramientas, eventos de crisis y consentimientos; cifrado en reposo de base y copias; rotación de KEK y DEK sin pérdida de datos. Los agentes no reciben claves ni secretos por configuración (auditoría).
- **Prueba:** `apps/orchestrator/tests/privacy/test_crypto.py` (security e integration): un volcado de la base es ilegible sin la DEK; rotar conserva los datos; ningún agente accede a una clave.
- **Terminado cuando:** la prueba pasa.

### T-07-004 Registro y alertas del uso de claves
- **Requisitos:** REQ-07-014
- **Depende de:** T-07-003
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/crypto/key_audit.py`, `apps/orchestrator/tests/privacy/test_key_audit.py`
- **Qué hacer:** registrar todo uso de claves maestras y de DEK fuera del flujo normal de la aplicación y alertar al operador.
- **Prueba:** `apps/orchestrator/tests/privacy/test_key_audit.py` (integration): un acceso fuera del flujo normal genera registro y alerta.
- **Terminado cuando:** la prueba pasa.

### T-07-005 Cifrado local del companion
- **Requisitos:** REQ-07-013
- **Depende de:** T-01-014
- **Archivos:** `apps/companion/tests/profile/test_local_encryption_audit.py`
- **Qué hacer:** prueba y verificación de que perfil, calibraciones y bitácora local se cifran en reposo con una clave protegida por el almacén de credenciales de Windows [SUPUESTO].
- **Prueba:** `apps/companion/tests/profile/test_local_encryption_audit.py` (security): los archivos locales no son legibles sin la clave del sistema operativo.
- **Terminado cuando:** la prueba pasa.

### T-07-006 TLS entre clientes y servicios [CODEX]
- **Requisitos:** REQ-07-010
- **Depende de:** T-00-007
- **Archivos:** `apps/orchestrator/tests/privacy/test_tls_everywhere.py`, `infra/proxy/tls.conf`
- **Qué hacer:** exigir TLS entre clientes y servicios y entre servicios internos; pruebas que rechazan tráfico sin cifrar.
- **Prueba:** `apps/orchestrator/tests/privacy/test_tls_everywhere.py` (security).
- **Terminado cuando:** la prueba pasa.

### T-07-007 Capa de salida a terceros con campos prohibidos
- **Requisitos:** REQ-07-020, REQ-07-021, REQ-07-022
- **Depende de:** T-02-007, T-05-011
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/privacy/egress_layer.py`, `apps/orchestrator/config/forbidden_fields.yaml`, `apps/orchestrator/tests/privacy/test_egress_layer.py`
- **Qué hacer:** todo envío a un tercero (modelo, voz en la nube, correo, servidores MCP) pasa por una capa que verifica el consentimiento vigente y minimiza campos. Bloquea por esquema el perfil de capacidad, la condición declarada, los eventos de crisis, los datos de calibración, cuadros, audio, landmarks y blendshapes.
- **Prueba:** `apps/orchestrator/tests/privacy/test_egress_layer.py` (security): un payload con cada campo prohibido se bloquea; sin consentimiento no sale nada.
- **Terminado cuando:** la prueba pasa.

### T-07-008 Registro de terceros y política con proveedores
- **Requisitos:** REQ-07-023, REQ-07-024, REQ-07-025
- **Depende de:** T-07-007
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/privacy/third_parties.py`, `docs/third-parties.yaml`, `apps/orchestrator/tests/privacy/test_third_parties.py`, `tools/audit/audit_provider_settings.py`
- **Qué hacer:** registro visible para la persona de cada proveedor (finalidad, país, categorías de datos); marcar los que reciben datos fuera de Ecuador para revisión legal `[verificar con abogado]`; documentar y verificar las configuraciones de no retención ni entrenamiento de los proveedores de modelos cuando existan `[verificar contrato]`; los datos de las personas no se usan para entrenar modelos.
- **Prueba:** `apps/orchestrator/tests/privacy/test_third_parties.py` (unit y audit): todo proveedor usado figura en el registro con país; uno nuevo sin registrar falla.
- **Terminado cuando:** la prueba pasa.

### T-07-009 Acceso, exportación y rectificación
- **Requisitos:** REQ-07-030, REQ-07-031, REQ-07-032, REQ-07-070
- **Depende de:** T-07-003, T-02-025, T-03-011
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/privacy/{access,export,rectify}.py`, `apps/orchestrator/tests/privacy/test_export.py`
- **Qué hacer:** vista de acceso en lenguaje llano (qué datos, para qué, con quién); exportación completa en formatos abiertos (JSON y entregables en su formato) con tareas, propuestas, logros, memoria, bitácora, consentimientos, perfiles y delegaciones, generada en segundo plano con aviso al terminar (≤ 5 min [SUPUESTO] para una persona típica); rectificación aplicada a todas las copias vivas.
- **Prueba:** `apps/orchestrator/tests/privacy/test_export.py` (e2e y perf): la exportación incluye todas las categorías; una corrección se refleja en todas las copias.
- **Terminado cuando:** la prueba pasa.

### T-07-010 Borrado criptográfico reanudable
- **Requisitos:** REQ-07-033, REQ-07-034, REQ-07-035, REQ-07-071, REQ-07-073
- **Depende de:** T-07-003, T-06-004
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/privacy/erase.py`, `apps/orchestrator/tests/privacy/test_erase.py`
- **Qué hacer:** al pedir el borrado: revocar sesiones, dispositivos, delegaciones y herramientas; borrar base, memoria vectorial, caché y archivos; destruir la DEK de la persona; verificar que nada queda legible; entregar una constancia con fecha y qué se borró, sin contenido. El proceso deja un registro por paso para ser **reanudable** si falla. Las copias de seguridad quedan ilegibles por el borrado criptográfico a más tardar al vencer su retención [SUPUESTO]. Objetivo de ≤ 24 h salvo copias [SUPUESTO].
- **Prueba:** `apps/orchestrator/tests/privacy/test_erase.py` (e2e e integration con fallos inyectados): tras el borrado, el contenido es ilegible incluso en una copia restaurada; un fallo a mitad se reanuda sin dejar datos legibles.
- **Terminado cuando:** la prueba pasa.

### T-07-011 Oposición, suspensión y derechos por cuidador/a
- **Requisitos:** REQ-07-036, REQ-07-038
- **Depende de:** T-05-011, T-06-006
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/privacy/objection.py`, `apps/orchestrator/tests/privacy/test_objection.py`
- **Qué hacer:** materializar la oposición o suspensión de una finalidad como la revocación inmediata del consentimiento correspondiente `[verificar con abogado los derechos exactos de la LOPDP]`. Un cuidador/a no ejerce estos derechos sin una delegación específica para ello `[verificar con abogado si hay representante legal]`.
- **Prueba:** `apps/orchestrator/tests/privacy/test_objection.py` (integration y security).
- **Terminado cuando:** la prueba pasa.

### T-07-012 Pantalla de privacidad [UI]
- **Requisitos:** REQ-07-030, REQ-07-037, REQ-07-072
- **Depende de:** T-07-009, T-07-010, T-00-015
- **Archivos:** `apps/web/src/features/privacy/{PrivacyCenter,ExportData,EraseData}.tsx`, `apps/web/tests/e2e/privacy.spec.ts`
- **Qué hacer:** pantalla para ver los datos, exportarlos y borrarlos con cualquier modalidad y sin plazos para la persona: el borrado explica qué se borra y pide una aprobación; la exportación avisa al terminar sin obligar a esperar en pantalla. Estados cargando, error, sin conexión.
- **Prueba:** `apps/web/tests/e2e/privacy.spec.ts` (e2e y a11y): flujo solo con intenciones simuladas; sin temporizadores; axe-core sin violaciones.
- **Terminado cuando:** la prueba pasa.

### T-07-013 Retención por categoría
- **Requisitos:** REQ-07-045, REQ-07-047, REQ-07-048
- **Depende de:** T-07-001
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/privacy/retention.py`, `apps/orchestrator/config/retention.yaml`, `apps/orchestrator/tests/privacy/test_retention.py`
- **Qué hacer:** política de retención por categoría con límites que la persona puede ajustar; por defecto el contenido de tareas se conserva hasta que la persona lo borre [SUPUESTO] y puede borrar tareas individuales; registros técnicos y datos operativos con retención limitada [SUPUESTO: valores a definir].
- **Prueba:** `apps/orchestrator/tests/privacy/test_retention.py` (unit y e2e).
- **Terminado cuando:** la prueba pasa.

### T-07-014 Acceso del operador y roles de base de datos
- **Requisitos:** REQ-07-055, REQ-07-056, REQ-07-057, REQ-07-058
- **Depende de:** T-02-002, T-00-011
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/privacy/operator_access.py`, `infra/db/roles.sql`, `apps/orchestrator/tests/privacy/test_operator_access.py`
- **Qué hacer:** el operador no tiene pantalla, API ni rol de base de datos para leer contenido; solo métricas agregadas y registros técnicos sin contenido. Sin acceso de emergencia al contenido. Registrar y alertar todo acceso con el rol de administración.
- **Prueba:** `apps/orchestrator/tests/privacy/test_operator_access.py` (security): enumerar roles y rutas del operador y comprobar que ninguno devuelve contenido; un acceso con rol admin genera alerta.
- **Terminado cuando:** la prueba pasa.

### T-07-015 Incidentes de seguridad e identificación de afectados
- **Requisitos:** REQ-07-065, REQ-07-066
- **Depende de:** T-07-001, T-02-003
- **Archivos:** `docs/security-incident-procedure.md`, `apps/orchestrator/src/coalsense_orchestrator/privacy/incident_scope.py`, `apps/orchestrator/tests/privacy/test_incident_scope.py`
- **Qué hacer:** procedimiento documentado de incidentes (detección, contención, aviso a las personas afectadas y a la autoridad en los plazos de la ley `[verificar con abogado]`). Herramienta que, a partir de la bitácora y del inventario, lista qué personas y qué categorías de datos afectó un incidente simulado.
- **Prueba:** `apps/orchestrator/tests/privacy/test_incident_scope.py` (integration); la parte documental se revisa de forma manual (`manual`).
- **Terminado cuando:** la prueba pasa y el procedimiento está revisado por el operador.
