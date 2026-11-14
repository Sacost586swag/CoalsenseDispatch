# audit

Auditorías de CI (licencias, esquema, importaciones, trazabilidad) y pruebas de integración del monorepo.

- `tests/test_clean_checkout.py`: clona HEAD y exige que `pnpm install --frozen-lockfile` y `uv sync --frozen` terminen con código 0. Marca `integration`; necesita red. Sin red: `COALSENSE_SKIP_NETWORK_TESTS=1` la omite con motivo explícito.
- Su tarea `test` no usa caché de Turborepo (ver `turbo.json`), porque depende de HEAD y de la red.
