# Tareas: 00 Fundaciones

**Requisitos:** `requirements.md`. **Diseño:** `design.md`. **Marcas:** `[CODEX]` paralelizable por Codex; `[UI]` interfaz (se resuelve con skills de diseño subordinadas a `.kiro/steering/accessibility.md`).

**Contexto común (léelo una vez).** Monorepo pnpm + Turborepo (web) y uv (Python 3.12). Árbol y reglas de dependencia en `.kiro/steering/structure.md`. Reglas de la vertical: `.kiro/steering/product.md`. Cada tarea cita los REQ que cubre y la prueba que la verifica. Una tarea termina solo cuando su prueba pasa y la CI de la spec 00 está en verde (cuando exista).

## Orden de dependencias

```
Ola 1: T-00-001
Ola 2: T-00-002, T-00-003, T-00-004, T-00-005, T-00-006, T-00-007, T-00-009, T-00-013   (paralelas, dependen solo de T-00-001)
Ola 3: T-00-008 (←T-00-007), T-00-010 (←T-00-007), T-00-014 (←T-00-013), T-00-016 (←T-00-014)
Ola 4: T-00-011 (←T-00-010), T-00-012 (←T-00-010, T-00-014), T-00-015 (←T-00-014), T-00-017 (←T-00-014)
```

---

### T-00-001 Esqueleto del monorepo
- **Requisitos:** REQ-00-001, REQ-00-006
- **Depende de:** ninguna
- **Archivos:** `pnpm-workspace.yaml`, `turbo.json`, `package.json`, `pyproject.toml` (workspace de uv), `uv.lock`, `pnpm-lock.yaml`, `.gitignore`, `THIRD_PARTY.md`, carpetas vacías con README en `apps/companion`, `apps/web`, `apps/orchestrator`, `packages/intents`, `packages/ui`, `packages/safety`, `tools/audit`, `infra`
- **Qué hacer:** crear el monorepo con la estructura de `structure.md`, workspace de pnpm y de uv, Turborepo con tareas `lint`, `typecheck`, `test`, `build`. Commitear los archivos de bloqueo. `THIRD_PARTY.md` con tabla vacía (licencia, versión, origen).
- **Prueba:** `tools/audit/tests/test_clean_checkout.py` (integration): en un checkout limpio, `pnpm install --frozen-lockfile` y `uv sync --frozen` terminan con código 0.
- **Terminado cuando:** la prueba pasa y `turbo run lint typecheck test` corre sin errores sobre los paquetes vacíos.

### T-00-002 Pipeline de CI [CODEX]
- **Requisitos:** REQ-00-002, REQ-00-061
- **Depende de:** T-00-001
- **Archivos:** `.github/workflows/ci.yml` [SUPUESTO: GitHub Actions], `turbo.json`
- **Qué hacer:** pipeline que en cada pull request instala con bloqueo, ejecuta lint, tipos y pruebas unitarias solo de los paquetes afectados (`turbo --filter=...[origin/main]`), y marca los pasos de auditoría, accesibilidad e integración como etapas requeridas para fusionar. Medir y registrar el tiempo del pipeline.
- **Prueba:** `tools/audit/tests/test_ci_config.py` (integration): valida que el flujo define las etapas requeridas y que `turbo` filtra por paquetes afectados.
- **Terminado cuando:** un pull request de prueba que rompe una prueba unitaria queda bloqueado, y el pipeline típico termina en el tiempo objetivo [SUPUESTO: 15 minutos].

### T-00-003 Auditoría de licencias [CODEX]
- **Requisitos:** REQ-00-004
- **Depende de:** T-00-001
- **Archivos:** `tools/audit/audit_licenses.py`, `tools/audit/approved_licenses.yaml`, `tools/audit/tests/test_audit_licenses.py`
- **Qué hacer:** script que lee las dependencias de pnpm y uv, obtiene su licencia y compara con `THIRD_PARTY.md` y con la lista aprobada (MIT, BSD, Apache-2.0, ISC, MPL-2.0 sin modificar). Falla si una dependencia no está registrada o tiene GPL, AGPL, LGPL sin revisión o EULA.
- **Prueba:** `tools/audit/tests/test_audit_licenses.py` (audit) con paquetes ficticios: aprobado pasa; GPL falla; no registrado falla.
- **Terminado cuando:** la prueba pasa y el script corre en la CI.

### T-00-004 Auditoría de importaciones prohibidas [CODEX]
- **Requisitos:** REQ-00-003
- **Depende de:** T-00-001
- **Archivos:** `tools/audit/audit_imports.py`, `tools/audit/forbidden_imports.yaml`, `tools/audit/tests/test_audit_imports.py`
- **Qué hacer:** análisis estático de Python que falla si (a) `apps/companion/**/adapters/{voice,head_gesture,gaze}` o `**/vision` importan módulos de red (`socket`, `http`, `urllib`, `requests`, `httpx`, `aiohttp`, `websockets`); (b) `apps/orchestrator/**/agents/` importa el cliente de base de datos de producción; (c) cualquier módulo fuera de `apps/orchestrator/**/gateway/` importa un cliente HTTP saliente. Las reglas viven en `forbidden_imports.yaml`.
- **Prueba:** `tools/audit/tests/test_audit_imports.py` (audit) con árboles de ejemplo que cumplen y que violan.
- **Terminado cuando:** la prueba pasa y la auditoría corre en la CI.

### T-00-005 Auditoría de secretos [CODEX]
- **Requisitos:** REQ-00-003, REQ-00-008
- **Depende de:** T-00-001
- **Archivos:** `tools/audit/audit_secrets.py`, `tools/audit/tests/test_audit_secrets.py`
- **Qué hacer:** escaneo del repositorio (patrones de claves, tokens, cadenas de conexión) que falla ante coincidencias; lista de excepciones explícita y revisable.
- **Prueba:** `tools/audit/tests/test_audit_secrets.py` (audit): un archivo con una clave de muestra falla; un archivo limpio pasa.
- **Terminado cuando:** la prueba pasa y corre en la CI.

### T-00-006 Auditoría de trazabilidad y glosario [CODEX]
- **Requisitos:** REQ-00-005
- **Depende de:** T-00-001
- **Archivos:** `tools/audit/audit_traceability.py`, `tools/audit/tests/test_audit_traceability.py`, `.kiro/specs/TRAZABILIDAD.md` (salida generada)
- **Qué hacer:** leer `requirements.md` y `tasks.md` de cada spec; extraer cada `REQ-xx-nnn` con su tipo de `Prueba:`, y de cada tarea sus `Requisitos:` y `Prueba:`; generar `TRAZABILIDAD.md` (requisito → tareas → prueba) y fallar si un requisito (salvo los de la spec 08, fase 2) no tiene tarea o prueba. Además leer los términos de la columna «No usar» de `GLOSARIO.md` y fallar si aparecen fuera de los glosarios y de comillas de cita.
- **Prueba:** `tools/audit/tests/test_audit_traceability.py` (audit) con specs de ejemplo: completa pasa; con un requisito huérfano falla; con un término prohibido falla.
- **Terminado cuando:** la prueba pasa y el script corre sobre `.kiro/specs/` real sin huérfanos.

### T-00-007 Configuración, errores e identificadores comunes [CODEX]
- **Requisitos:** REQ-00-007, REQ-00-009, REQ-00-012
- **Depende de:** T-00-001
- **Archivos:** `packages/common-py/src/coalsense_common/{config,errors,ids}.py`, `packages/common-ts/src/{config,errors,ids}.ts`, pruebas en `packages/common-py/tests/` y `packages/common-ts/tests/`
- **Qué hacer:** (a) carga de configuración desde variables de entorno con esquema validado que falla al arrancar con mensaje claro sin imprimir secretos; (b) tipo de error común `{code, message_es, recoverable, next_actions[]}`; (c) generación de ids únicos (UUIDv7 [SUPUESTO]) y marcas de tiempo monotónica y de reloj, en Python y TypeScript con la misma semántica.
- **Prueba:** `packages/common-py/tests/test_config_errors_ids.py` y `packages/common-ts/tests/common.test.ts` (unit).
- **Terminado cuando:** las pruebas pasan: variable faltante falla sin imprimir su valor; errores serializan igual en ambos lenguajes; los ids son únicos y ordenables por tiempo.

### T-00-008 Registros estructurados con depurador de contenido [CODEX]
- **Requisitos:** REQ-00-010
- **Depende de:** T-00-007
- **Archivos:** `packages/common-py/src/coalsense_common/logging.py`, `packages/common-ts/src/logging.ts`, `packages/common-py/tests/test_logging_scrub.py`
- **Qué hacer:** registro estructurado con un depurador que elimina campos de contenido (`text`, `body`, `dictation`, `profile`, `filename`, `recipient`, `prompt`, `completion`) antes de emitir. La lista es configurable y se prueba con textos de muestra.
- **Prueba:** `packages/common-py/tests/test_logging_scrub.py` (security): emitir un registro con texto de muestra y exigir que no aparezca en la salida.
- **Terminado cuando:** la prueba pasa en Python y hay una prueba equivalente en TypeScript.

### T-00-009 Catálogo de textos en español y lint de cadenas [CODEX]
- **Requisitos:** REQ-00-011
- **Depende de:** T-00-001
- **Archivos:** `packages/ui/src/i18n/es.ts`, `packages/common-py/src/coalsense_common/i18n_es.py`, `tools/audit/audit_copy.py`, `tools/audit/forbidden_words.yaml`, `tools/audit/tests/test_audit_copy.py`
- **Qué hacer:** catálogo único de textos de interfaz en español; script que falla si hay cadenas visibles fijas en componentes y si el catálogo contiene palabras prohibidas (terapia, tratamiento, cura, diagnóstico, «mejora tu depresión», lenguaje de reproche como «fallaste»).
- **Prueba:** `tools/audit/tests/test_audit_copy.py` (audit).
- **Terminado cuando:** la prueba pasa y corre en la CI.

### T-00-010 Servicio de autenticación sin contraseña
- **Requisitos:** REQ-00-020, REQ-00-021, REQ-00-025, REQ-00-026, REQ-00-027
- **Depende de:** T-00-007
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/auth/{codes,pairing,rate_limit,routes}.py`, migración `apps/orchestrator/migrations/0001_auth.sql`, `apps/orchestrator/tests/auth/test_codes_pairing.py`
- **Qué hacer:** endpoints para solicitar y verificar un código de un solo uso por correo y para emparejar un dispositivo con un código corto. Los códigos **no tienen `expires_at`**: se invalidan por uso, por generar otro o por exceder el número de intentos. Limitación de frecuencia con espera creciente y sin bloqueo permanente. Registrar eventos de autenticación (alta, ingreso, revocación) en la bitácora sin secretos. TLS obligatorio (rechazar HTTP). Tablas de `account`, `device`, `pairing_code`.
- **Prueba:** `apps/orchestrator/tests/auth/test_codes_pairing.py` (unit y security): un código no vence por tiempo; intentos excedidos lo invalidan; nunca hay bloqueo permanente; la bitácora no contiene el código.
- **Terminado cuando:** las pruebas pasan.

### T-00-011 Sesiones, roles y revocación
- **Requisitos:** REQ-00-022, REQ-00-023, REQ-00-024
- **Depende de:** T-00-010
- **Archivos:** `apps/orchestrator/src/coalsense_orchestrator/auth/{sessions,roles,revocation}.py`, `apps/companion/src/coalsense_companion/auth/credential_store.py`, `apps/orchestrator/tests/auth/test_sessions_roles.py`
- **Qué hacer:** credencial por dispositivo con rotación, guardada en el almacén de credenciales de Windows en el companion [SUPUESTO] y sin cierre por inactividad con trabajo pendiente. Roles `person`, `caregiver`, `operator`, `company` (fase 2) con alcances. El rol `operator` no tiene ningún alcance de lectura de contenido. Revocación inmediata de dispositivos y sesiones.
- **Prueba:** `apps/orchestrator/tests/auth/test_sessions_roles.py` (security e integration): `operator` recibe 403 en todo recurso de contenido; la revocación invalida de inmediato; la sesión sobrevive a la inactividad mientras haya trabajo pendiente.
- **Terminado cuando:** las pruebas pasan.

### T-00-012 Pantallas de autenticación accesibles [UI]
- **Requisitos:** REQ-00-020, REQ-00-021
- **Depende de:** T-00-010, T-00-014
- **Archivos:** `apps/web/src/features/auth/*`, `apps/web/tests/e2e/auth.spec.ts`
- **Qué hacer:** pantallas para pedir código, ingresarlo (por voz, por cualquier modalidad o con ayuda del cuidador/a) y emparejar el companion. Sin CAPTCHA ni pruebas cognitivas (WCAG 3.3.8). Estados cargando, error, sin conexión (AX-11). Usar solo componentes de `packages/ui`.
- **Prueba:** `apps/web/tests/e2e/auth.spec.ts` (e2e y a11y): flujo completo solo con teclado y con intenciones simuladas; axe-core sin violaciones; objetivos ≥ 44×44 px.
- **Terminado cuando:** la prueba pasa.

### T-00-013 Tokens y temas del design system [CODEX]
- **Requisitos:** REQ-00-040, REQ-00-045, REQ-00-060
- **Depende de:** T-00-001
- **Archivos:** `packages/ui/src/tokens/*.ts`, `packages/ui/src/themes/{default,high-contrast,reduced-motion}.ts`, `packages/ui/tests/tokens.test.ts`
- **Qué hacer:** tokens de color, espaciado, tipografía, movimiento y tamaño de objetivo. `target.min = 44` (px CSS) es un piso: un tema que lo reduzca falla en tiempo de construcción. Temas de alto contraste, texto ampliable y movimiento reducido (`prefers-reduced-motion`). Contrastes 4.5:1 texto y 3:1 componentes verificados por prueba.
- **Prueba:** `packages/ui/tests/tokens.test.ts` (unit): tema con objetivo < 44 falla; los contrastes cumplen.
- **Terminado cuando:** la prueba pasa.

### T-00-014 Componentes base accesibles [UI]
- **Requisitos:** REQ-00-041, REQ-00-042, REQ-00-043, REQ-00-048
- **Depende de:** T-00-013
- **Archivos:** `packages/ui/src/components/{Button,Link,TextField,Dialog,NumberedList,Progress,StatusBanner,Stepper}.tsx`, `packages/ui/tests/components.test.tsx`
- **Qué hacer:** componentes con todos los estados (normal, foco, activo, deshabilitado, error, cargando). Nombre accesible derivado de la etiqueta visible (WCAG 2.5.3). Los avisos no se cierran solos. Nada oculto tras hover, pulsación larga ni gestos con trayectoria. Diálogos que no cubren la barra de Alto y Deshacer.
- **Prueba:** `packages/ui/tests/components.test.tsx` (a11y): axe-core por componente y estado; el nombre accesible contiene la etiqueta visible; ningún aviso desaparece sin acción.
- **Terminado cuando:** la prueba pasa.

### T-00-015 Pantalla de estado, tarjeta de aprobación y barra de Alto y Deshacer [UI]
- **Requisitos:** REQ-00-044, REQ-00-046, REQ-00-050
- **Depende de:** T-00-014
- **Archivos:** `packages/ui/src/components/{StateScreen,ApprovalCard,StopUndoBar}.tsx`, `packages/ui/tests/state-approval-stopbar.test.tsx`
- **Qué hacer:** (a) `StateScreen` recibe `{estado, queOcurrio, acciones[], queSigueFuncionando[]}` para cargando, vacío, error, sin conexión, calibración fallida y modalidad no detectada; (b) `ApprovalCard` muestra qué se aprueba, a quién llega y qué efecto tiene, con aprobar, rechazar y decidir después, sin opción preseleccionada y sin vencimiento; (c) `StopUndoBar` fija y siempre visible con objetivos ≥ 44×44 px, no cubrible por diálogos.
- **Prueba:** `packages/ui/tests/state-approval-stopbar.test.tsx` (a11y): estados completos; sin preselección; la barra no queda tapada por un diálogo.
- **Terminado cuando:** la prueba pasa.

### T-00-016 Registro de objetivos de navegación [CODEX]
- **Requisitos:** REQ-00-047
- **Depende de:** T-00-014
- **Archivos:** `packages/ui/src/nav/NavTargetRegistry.ts`, `packages/ui/src/nav/useNavTarget.ts`, `packages/ui/tests/nav-registry.test.tsx`
- **Qué hacer:** registro donde cada control interactivo publica `{id, label, bounds}` y se actualiza al cambiar el layout. La capa de entrada lo consulta para números en pantalla, dwell y escaneo. Exponer la lista en un canal que el puente del companion pueda leer.
- **Prueba:** `packages/ui/tests/nav-registry.test.tsx` (integration): al montar y mover un control, el registro refleja su geometría y etiqueta.
- **Terminado cuando:** la prueba pasa.

### T-00-017 Catálogo de componentes y control de accesibilidad en CI [CODEX]
- **Requisitos:** REQ-00-049, REQ-00-062
- **Depende de:** T-00-014
- **Archivos:** `packages/ui/.catalog/*` [SUPUESTO: Storybook o equivalente], `tools/audit/a11y_target_size.ts`, `packages/ui/tests/a11y-ci.test.ts`
- **Qué hacer:** catálogo navegable donde cada componente muestra todos sus estados. Regla propia en Playwright que mide cada objetivo interactivo y falla si es < 44×44 px CSS (axe cubre solo 24×24). Integrar axe-core y la regla en la CI para cada componente y estado.
- **Prueba:** `packages/ui/tests/a11y-ci.test.ts` (a11y): un componente de ejemplo con 40 px falla; con 44 px pasa.
- **Terminado cuando:** la prueba pasa y el catálogo corre en la CI.
