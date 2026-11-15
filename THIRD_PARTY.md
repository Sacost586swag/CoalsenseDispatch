# Dependencias de terceros

Registro de cada dependencia **directa** del monorepo: versión fijada, licencia y origen. Solo se admiten licencias MIT, BSD, Apache-2.0, ISC y MPL-2.0. Las dependencias transitivas las cubre la auditoría de licencias de CI (T-00-003).

Versiones fijadas exactas (sin `^` ni `~`) en `package.json` y `pyproject.toml`.

| Paquete | Versión | Licencia | Origen | Por qué |
| --- | --- | --- | --- | --- |
| turbo | 2.11.11 | MIT | npm: https://www.npmjs.com/package/turbo | Orquesta `lint`, `typecheck`, `test` y `build` en todo el monorepo (TypeScript y Python). |
| typescript | 6.0.3 | Apache-2.0 | npm: https://www.npmjs.com/package/typescript | Compilador y verificación de tipos en modo `strict`. Se queda en 6.x porque `typescript-eslint` 8.72.2 exige `<6.1.0`. |
| eslint | 10.14.0 | MIT | npm: https://www.npmjs.com/package/eslint | Lint de TypeScript. |
| @eslint/js | 10.0.1 | MIT | npm: https://www.npmjs.com/package/@eslint/js | Reglas recomendadas de ESLint. |
| typescript-eslint | 8.72.2 | MIT | npm: https://www.npmjs.com/package/typescript-eslint | Reglas de ESLint para TypeScript. |
| prettier | 3.10.1 | MIT | npm: https://www.npmjs.com/package/prettier | Formato de TypeScript, JSON y Markdown. |
| @types/node | 24.19.2 | MIT | npm: https://www.npmjs.com/package/@types/node | Tipos de Node 24 (`node:test`, `node:assert`). |
| ruff | 0.17.5 | MIT | PyPI: https://pypi.org/project/ruff/ | Lint y orden de imports de Python. |
| mypy | 2.4.1 | MIT | PyPI: https://pypi.org/project/mypy/ | Verificación de tipos de Python en modo `strict`. |
| pytest | 9.2.0 | MIT | PyPI: https://pypi.org/project/pytest/ | Pruebas de Python. |
| pyyaml | 6.0.3 | MIT | PyPI: https://pypi.org/project/pyyaml/6.0.3/ | Solo desarrollo: la prueba de CI (`test_ci_config.py`) analiza `ci.yml` con un parser YAML real. Publicada el 2025-09-25. |
| uv_build | 0.12.13 | MIT OR Apache-2.0 | PyPI: https://pypi.org/project/uv-build/ | Backend de construcción de los paquetes Python del workspace de uv. |
| pydantic | 2.12.3 | MIT | PyPI: https://pypi.org/project/pydantic/2.12.3/ | Esquemas de configuración y protección de secretos con SecretStr. |
| zod | 4.1.12 | MIT | npm: https://www.npmjs.com/package/zod/v/4.1.12 | Esquemas de configuración TypeScript. |
| fastapi | 0.162.2 | MIT | PyPI: https://pypi.org/project/fastapi/0.162.2/ | Servicio HTTP del orquestador (rutas de autenticación, T-00-010). Publicada el 2026-11-07, más de 7 días antes de fijarla. |
| httpx | 0.28.1 | BSD-3-Clause | PyPI: https://pypi.org/project/httpx/0.28.1/ | Solo desarrollo: lo exige `TestClient` de FastAPI para probar las rutas en `tests/`. La auditoría de importaciones lo exime fuera de `gateway/` solo en pruebas. Publicada el 2024-12-06. |
