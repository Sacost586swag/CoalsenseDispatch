# Tareas: 09 Despliegue

**Requisitos:** `requirements.md`. **Diseño:** `design.md`. **Marcas:** `[CODEX]` paralelizable por Codex; `[UI]` interfaz.

**Contexto común (léelo una vez).**
- Empaquetado del companion en `apps/companion/packaging/`; infraestructura en `infra/` (docker-compose, proxy, base de datos, claves) y `.github/workflows/` [SUPUESTO: GitHub Actions]; PWA en `apps/web/`.
- Entornos: desarrollo local, **prueba** y **producción**. Prueba solo usa datos sintéticos y proveedores simulados. Producción se promueve a mano por el operador.
- El companion funciona sin el backend. El empaquetado no puede añadir destinos de red fuera de la lista permitida (SP-3). Las actualizaciones las aprueba la persona; nunca durante una tarea.
- Hosting y región están por decidir (PA-18): estas tareas se construyen sobre contenedores portables.

## Orden de dependencias

```
Ola 0 (specs 00, 01, 02): T-00-002, T-01-043, T-02-022
Ola 1: T-09-001, T-09-008, T-09-007
Ola 2: T-09-002, T-09-006, T-09-009, T-09-010, T-09-012
Ola 3: T-09-003, T-09-004, T-09-005, T-09-011, T-09-013, T-09-014
Ola 4: T-09-015
```

---

### T-09-001 Empaquetado e instalador firmado del companion
- **Requisitos:** REQ-09-001, REQ-09-002
- **Depende de:** T-01-054
- **Archivos:** `apps/companion/packaging/{build.py,installer.iss,signing.py}` [SUPUESTO: PyInstaller o Nuitka más Inno Setup o MSIX; se elige midiendo tamaño y arranque], `apps/companion/tests/packaging/test_installer.py`
- **Qué hacer:** generar un instalador de Windows que no requiera tener Python ni uv instalados; firmarlo con un certificado de firma de código (en CI con secreto del operador) y hacer que el companion verifique la firma antes de instalar actualizaciones. Documentar la elección de herramienta.
- **Prueba:** `apps/companion/tests/packaging/test_installer.py` (integration y security): en una máquina limpia el instalador funciona sin Python; un instalador con firma alterada se rechaza.
- **Terminado cuando:** la prueba pasa.

### T-09-002 Modelos con integridad verificada y uso sin conexión
- **Requisitos:** REQ-09-003
- **Depende de:** T-09-001
- **Archivos:** `apps/companion/packaging/models_manifest.json`, `apps/companion/src/coalsense_companion/models/verify.py`, `apps/companion/tests/packaging/test_models.py`
- **Qué hacer:** incluir en el instalador (o descargar al primer arranque) los modelos de visión y de voz con un manifiesto de hashes que se verifica; después, todo funciona sin conexión.
- **Prueba:** `apps/companion/tests/packaging/test_models.py` (security e integration): un modelo con hash distinto no se carga; tras la instalación el companion funciona con la red deshabilitada.
- **Terminado cuando:** la prueba pasa.

### T-09-003 Asistente de permisos y primer arranque [UI]
- **Requisitos:** REQ-09-004, REQ-09-063
- **Depende de:** T-09-001, T-00-015
- **Archivos:** `apps/web/src/features/install/{PermissionsWizard,FirstRun}.tsx`, `apps/web/tests/e2e/install-wizard.spec.ts`
- **Qué hacer:** asistente de instalación y de permisos de cámara y micrófono con una explicación breve y pasos operables con voz o con ayuda del cuidador/a; si se deniegan, mostrar «modalidad no detectada» con la causa. Sin límites de tiempo, objetivos ≥ 44×44 px.
- **Prueba:** `apps/web/tests/e2e/install-wizard.spec.ts` (e2e y a11y): permiso denegado muestra el estado con los pasos; sin temporizadores.
- **Terminado cuando:** la prueba pasa.

### T-09-004 Actualizaciones con aprobación y conservación de datos
- **Requisitos:** REQ-09-005, REQ-09-006
- **Depende de:** T-09-001
- **Archivos:** `apps/companion/src/coalsense_companion/update/{checker,installer,rollback}.py`, `apps/companion/tests/update/test_update.py`
- **Qué hacer:** consultar versiones nuevas firmadas y avisar; actualizar solo con la aprobación de la persona, nunca durante una tarea en ejecución, con posibilidad de posponer sin límite. Conservar la versión anterior y volver a ella si falla el arranque. Conservar perfil, calibraciones y comandos propios al actualizar y al reinstalar.
- **Prueba:** `apps/companion/tests/update/test_update.py` (e2e e integration): no actualiza sin aprobación ni durante una tarea; un arranque fallido vuelve a la versión anterior; los datos se conservan.
- **Terminado cuando:** la prueba pasa.

### T-09-005 Desinstalación e inicio con Windows
- **Requisitos:** REQ-09-007, REQ-09-008
- **Depende de:** T-09-001, T-01-042
- **Archivos:** `apps/companion/packaging/uninstall.py`, `apps/companion/src/coalsense_companion/autostart.py`, `apps/companion/tests/packaging/test_uninstall_autostart.py`
- **Qué hacer:** al desinstalar, ofrecer borrar o conservar los datos locales y no dejar procesos ni accesos directos activos de cámara o micrófono. Iniciar con Windows solo si la persona lo eligió, mostrando el indicador de cámara y micrófono desde el primer instante.
- **Prueba:** `apps/companion/tests/packaging/test_uninstall_autostart.py` (integration y e2e).
- **Terminado cuando:** la prueba pasa.

### T-09-006 Auditoría del egreso de red del artefacto [CODEX]
- **Requisitos:** REQ-09-009
- **Depende de:** T-01-043, T-09-001
- **Archivos:** `tools/audit/audit_packaged_egress.py`, `tools/audit/tests/test_packaged_egress.py`
- **Qué hacer:** analizar el artefacto empaquetado (importaciones, destinos de red declarados, cadenas de URL) y fallar el build si añade destinos fuera de la lista permitida del companion.
- **Prueba:** `tools/audit/tests/test_packaged_egress.py` (security): un artefacto con un destino nuevo falla.
- **Terminado cuando:** la prueba pasa y corre en la CI.

### T-09-007 PWA con política de contenido estricta
- **Requisitos:** REQ-09-010, REQ-09-011, REQ-09-012, REQ-09-013
- **Depende de:** T-01-031
- **Archivos:** `apps/web/next.config.js` (cabeceras de seguridad), `apps/web/public/manifest.webmanifest`, `apps/web/src/sw.ts`, `apps/web/tests/e2e/pwa-security.spec.ts`
- **Qué hacer:** PWA instalable con política de seguridad de contenido (`connect-src` solo a orígenes propios); modelos de MediaPipe servidos desde el mismo origen sin redes de entrega de terceros; abrir sin conexión las pantallas ya visitadas con los estados *sin conexión*; pedir el permiso de cámara solo cuando la persona activa el modo web de visión.
- **Prueba:** `apps/web/tests/e2e/pwa-security.spec.ts` (e2e y security): la política bloquea destinos externos; sin conexión se abren las pantallas visitadas; el permiso de cámara no se pide al cargar.
- **Terminado cuando:** la prueba pasa.

### T-09-008 Backend en contenedores, migraciones y salud
- **Requisitos:** REQ-09-020, REQ-09-021, REQ-09-022, REQ-09-023
- **Depende de:** T-00-002, T-02-002
- **Archivos:** `infra/docker-compose.yml`, `infra/Dockerfile.orchestrator`, `infra/db/migrate.py`, `infra/healthchecks/*.py`, `apps/orchestrator/tests/infra/test_compose.py`
- **Qué hacer:** definir en `infra/` PostgreSQL con pgvector, Redis, el orquestador y (opcional) n8n, reproducibles con docker-compose. Migraciones versionadas y reversibles; si una falla, el despliegue falla. Credenciales distintas por servicio; los procesos de agentes no reciben las de producción. Comprobaciones de salud por servicio y de dependencias.
- **Prueba:** `apps/orchestrator/tests/infra/test_compose.py` (integration y security): el entorno levanta; una migración fallida detiene el despliegue; el contenedor de agentes no tiene credenciales de BD.
- **Terminado cuando:** la prueba pasa.

### T-09-009 Servidores MCP en contenedores aislados
- **Requisitos:** REQ-09-024
- **Depende de:** T-09-008, T-02-023
- **Archivos:** `infra/mcp/Dockerfile.base`, `infra/mcp/network-policy.yml`, `apps/orchestrator/tests/infra/test_mcp_isolation.py`
- **Qué hacer:** ejecutar cada servidor MCP del catálogo curado en un contenedor con permisos mínimos, credenciales propias y red restringida a una lista permitida de destinos.
- **Prueba:** `apps/orchestrator/tests/infra/test_mcp_isolation.py` (security): un servidor de prueba no puede alcanzar la base de datos ni otros servicios ni destinos no permitidos.
- **Terminado cuando:** la prueba pasa.

### T-09-010 Entornos de prueba y producción
- **Requisitos:** REQ-09-030, REQ-09-031, REQ-09-032, REQ-09-033, REQ-09-034
- **Depende de:** T-09-008
- **Archivos:** `infra/envs/{test,production}/*.yml`, `infra/envs/README.md`, `tools/audit/audit_envs.py`, `apps/web/src/features/env/TestEnvBanner.tsx`, `tools/audit/tests/test_audit_envs.py`
- **Qué hacer:** tres entornos (local, prueba, producción) con configuración, secretos y datos separados y el entorno de prueba lo más parecido posible a producción (documentar diferencias). Prueba usa datos sintéticos y proveedores simulados o cuentas de prueba, de modo que ninguna prueba contacte a una persona real; una auditoría falla si hay datos reales fuera de producción. Mostrar un banner inequívoco de entorno de prueba en la interfaz y los mensajes.
- **Prueba:** `tools/audit/tests/test_audit_envs.py` (audit) y `apps/web/tests/e2e/test-env-banner.spec.ts` (e2e).
- **Terminado cuando:** ambas pasan.

### T-09-011 Pipeline de entrega, promoción y reversión
- **Requisitos:** REQ-09-040, REQ-09-041, REQ-09-042, REQ-09-044
- **Depende de:** T-09-010, T-09-006, T-00-003
- **Archivos:** `.github/workflows/{build,deploy-test,promote-prod}.yml`, `infra/scripts/rollback.sh`, `tools/audit/audit_release_gate.py`, `tools/audit/tests/test_release_gate.py`
- **Qué hacer:** construir y probar companion, web y backend desde el mismo commit; desplegar automáticamente a prueba; promover a producción solo artefactos que pasaron las pruebas de prueba, con aprobación manual del operador; permitir revertir a la versión anterior sin pérdida de datos; publicar `THIRD_PARTY.md` y el inventario de licencias con cada versión.
- **Prueba:** `tools/audit/tests/test_release_gate.py` (audit): un artefacto que no pasó en prueba no puede promoverse; reversión simulada conserva los datos.
- **Terminado cuando:** la prueba pasa.

### T-09-012 Indicadores de función [CODEX]
- **Requisitos:** REQ-09-043
- **Depende de:** T-09-010
- **Archivos:** `packages/common-py/src/coalsense_common/flags.py`, `packages/common-ts/src/flags.ts`, `infra/envs/production/flags.yml`, `packages/common-py/tests/test_flags.py`
- **Qué hacer:** indicadores de función desactivados por defecto en producción para mirada, switch y las funciones de la fase 2; el código de esas funciones no se activa sin el indicador.
- **Prueba:** `packages/common-py/tests/test_flags.py` (unit): con el indicador apagado, los adaptadores de mirada y switch no se registran.
- **Terminado cuando:** la prueba pasa.

### T-09-013 Observabilidad y alertas sin contenido
- **Requisitos:** REQ-09-050, REQ-09-052
- **Depende de:** T-09-008, T-02-027, T-01-011
- **Archivos:** `infra/observability/{metrics,alerts}.yml`, `apps/orchestrator/tests/infra/test_alerts.py`
- **Qué hacer:** recolectar métricas y registros sin contenido privado y alertar al operador de errores, degradaciones, ausencia de latido de un companion y servicio de claves caído.
- **Prueba:** `apps/orchestrator/tests/infra/test_alerts.py` (integration): apagar un latido o el servicio de claves dispara la alerta; ningún registro contiene contenido de muestra.
- **Terminado cuando:** la prueba pasa.

### T-09-014 Copias de seguridad cifradas y restauración
- **Requisitos:** REQ-09-051, REQ-09-053, REQ-09-062
- **Depende de:** T-09-008, T-07-003
- **Archivos:** `infra/backup/{backup,restore}.py`, `apps/orchestrator/tests/infra/test_backup_restore.py`
- **Qué hacer:** copias cifradas de la base de datos y del almacenamiento de archivos con frecuencia definida [SUPUESTO] y prueba periódica de restauración; el contenido de las copias está cifrado con la clave de datos de cada persona; objetivo de tiempo de restauración definido [SUPUESTO].
- **Prueba:** `apps/orchestrator/tests/infra/test_backup_restore.py` (integration y security): restaurar en el entorno de prueba recupera los datos; una copia sin la clave es ilegible.
- **Terminado cuando:** la prueba pasa.

### T-09-015 Arranque del companion y disponibilidad [CODEX]
- **Requisitos:** REQ-09-060, REQ-09-061
- **Depende de:** T-09-001, T-01-047
- **Archivos:** `apps/companion/tests/perf/test_startup.py`, `infra/observability/slo.yml`
- **Qué hacer:** medir que el companion tiene operativa al menos una ruta de Alto en ≤ 15 s en el hardware de referencia [SUPUESTO]; comprobar que sigue funcionando sin el backend; definir y medir el objetivo de disponibilidad del backend tras el primer despliegue [SUPUESTO].
- **Prueba:** `apps/companion/tests/perf/test_startup.py` (perf).
- **Terminado cuando:** la prueba pasa o los objetivos se actualizan con los valores medidos.
