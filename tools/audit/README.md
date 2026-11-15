# audit

## Licencias (T-00-003)

Ejecutar `python tools/audit/audit_licenses.py` desde la raíz o
`uv run --locked python -m coalsense_audit.licenses`. Turbo: `pnpm turbo run audit`.
Salida vacía y código 0 significa aprobado; código 1 incluye hallazgos en español
con formato `ruta:línea: regla: mensaje`, sin reproducir entradas ni metadatos.

El inventario incluye todos los paquetes del lock de pnpm v9 y de uv v1,
incluidos opcionales de otras plataformas. Requiere metadatos instalados de la
misma versión: `node_modules/.pnpm` para npm, `importlib.metadata` para Python
(o `license` explícita en uv.lock). No consulta la red ni usa THIRD_PARTY.md
como evidencia de licencia, salvo para backends de construcción no instalados. Los backends de construcción fijados también se
verifican; su instalación aislada por uv no garantiza metadatos disponibles.
Una instalación incompleta falla de forma deliberada.

Formato del hallazgo: `ruta:línea: LICENCIA: paquete@versión: licencia "X" no
aprobada` (`X` es la licencia detectada, o `desconocida`; texto no estándar nunca
se reproduce). Miembros del workspace (pnpm `workspace:`, uv `editable`/`virtual`)
no son terceros y se excluyen. Reglas de evidencia: npm lee `license` o el
`licenses` heredado (cualquiera elegible, equivale a OR); un paquete npm con
`os`/`cpu` no instalado en esta plataforma hereda la licencia de un hermano
instalado del mismo ámbito y versión; Python lee `License-Expression`, `License`
y clasificadores, y resuelve el clasificador BSD genérico desde el texto de la
licencia instalado; un backend de construcción no instalado se evalúa con la
licencia registrada en THIRD_PARTY.md.
Si el backend está instalado pero sin licencia en sus metadatos, falla (el registro no
lo rescata). Un paquete Python con marcador de plataforma (p. ej. `colorama` solo en
win32) que no está instalado aquí requiere una entrada revisada en `uninstalled_python`
de `approved_licenses.yaml` (`name`, `version` exacta, `license`, `reason`); sin ella
falla. Igual para npm con `uninstalled_npm` (mismos campos, sin duplicados): debe listar TODAS las variantes
de plataforma del lock (`os`/`cpu`/`libc` o `optional` en `snapshots`) para que la misma política valga en
cualquier host; si el paquete está instalado se usan sus metadatos reales y la entrada se ignora; la licencia
de la entrada debe estar aprobada; una entrada cuyo nombre@versión no está en el lock falla con `POLITICA`. Varios hermanos npm instalados del mismo ámbito y versión se combinan con AND.
Ejecute siempre con `uv run --locked` tras `uv sync --locked`; un Python de sistema lee
metadatos de otro entorno.

`approved_licenses.yaml` usa el subconjunto JSON de YAML, sin dependencias nuevas.
`font_packages` contiene identificadores `npm:nombre` o `pypi:nombre` para autorizar
OFL-1.1. `exceptions` contiene objetos con `ecosystem`, `name`, `version`, `license`
y `reason` no vacío; no hay excepciones preautorizadas. MPL-2.0 cubre solo el uso
sin modificación; el script no certifica modificaciones al código de terceros.
Se aceptan expresiones SPDX con AND, OR y paréntesis; WITH y licencias desconocidas
fallan. El lector de pnpm admite el inventario de mapas de bloques generado por
pnpm v9; otros formatos requieren actualizar el lector y sus pruebas.

Auditorías de CI (licencias, esquema, importaciones, trazabilidad) y pruebas de integración del monorepo.

- `tests/test_clean_checkout.py`: clona HEAD y exige que `pnpm install --frozen-lockfile` y `uv sync --locked` terminen con código 0. Marca `integration`; necesita red. Sin red: `COALSENSE_SKIP_NETWORK_TESTS=1` la omite con motivo explícito.
- Su tarea `test` no usa caché de Turborepo (ver `turbo.json`), porque depende de HEAD y de la red.
