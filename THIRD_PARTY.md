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
| asyncpg | 0.32.0 | Apache-2.0 | PyPI: https://pypi.org/project/asyncpg/0.32.0/ | Controlador PostgreSQL asíncrono nativo, solo en persistencia; RLS y transacciones reales de T-02-002. Publicado el 2026-10-06 y comprobado con Python 3.12/Windows. No añade un cliente de BD a los agentes. |
| jsonschema | 4.26.0 | MIT | PyPI: https://pypi.org/project/jsonschema/4.26.0/ | Validación local del contrato de intenciones y del perfil (T-01-001 a T-01-003), y de esquemas de entrada/salida del gateway (T-02-006). Misma versión; dependencia directa del orquestador. |
| rfc3339-validator | 0.1.4 | MIT | PyPI: https://pypi.org/project/rfc3339-validator/0.1.4/ | Activa la comprobación real de date-time en JSON Schema; sin esta dependencia el formato quedaba sin comprobar. |
| types-jsonschema | 4.26.0.20261006 | Apache-2.0 | PyPI: https://pypi.org/project/types-jsonschema/4.26.0.20261006/ | Solo desarrollo: anotaciones para validar con mypy estricto los usos de JSON Schema. |
| hypothesis | 6.170.15 | MPL-2.0 | PyPI: https://pypi.org/project/hypothesis/6.170.15/ | Solo desarrollo y sin modificar: propiedades de orden, saturación y aprobación de baja confianza. |
| zod | 4.1.12 | MIT | npm: https://www.npmjs.com/package/zod/v/4.1.12 | Esquemas de configuración TypeScript. |
| fastapi | 0.162.2 | MIT | PyPI: https://pypi.org/project/fastapi/0.162.2/ | Servicio HTTP del orquestador (rutas de autenticación, T-00-010). Publicada el 2026-11-07, más de 7 días antes de fijarla. |
| httpx | 0.28.1 | BSD-3-Clause | PyPI: https://pypi.org/project/httpx/0.28.1/ | Solo desarrollo: lo exige `TestClient` de FastAPI para probar las rutas en `tests/`. La auditoría de importaciones lo exime fuera de `gateway/` solo en pruebas. Publicada el 2024-12-06. |
| react | 19.3.1 | MIT | npm: https://www.npmjs.com/package/react/v/19.3.1 | Componentes de `@coalsense/ui` (peer y desarrollo). Publicada el 2026-10-14. |
| react-dom | 19.3.1 | MIT | npm: https://www.npmjs.com/package/react-dom/v/19.3.1 | Render y portal del diálogo de `@coalsense/ui` (peer y desarrollo). Publicada el 2026-10-14. |
| @types/react | 19.3.0 | MIT | npm: https://www.npmjs.com/package/@types/react/v/19.3.0 | Solo desarrollo: tipos de React para `tsc` en modo `strict`. Publicada el 2026-09-09. |
| @types/react-dom | 19.3.0 | MIT | npm: https://www.npmjs.com/package/@types/react-dom/v/19.3.0 | Solo desarrollo: tipos de `react-dom`. Publicada el 2026-09-09. |
| vitest | 5.1.0 | MIT | npm: https://www.npmjs.com/package/vitest/v/5.1.0 | Solo desarrollo: ejecuta las pruebas de componentes de `@coalsense/ui` (T-00-014); las de tokens siguen en `node --test`. Publicada el 2026-11-02. |
| @testing-library/react | 16.3.3 | MIT | npm: https://www.npmjs.com/package/@testing-library/react/v/16.3.3 | Solo desarrollo: render y consultas por rol y nombre accesible. Publicada el 2026-08-27. |
| @testing-library/dom | 10.4.2 | MIT | npm: https://www.npmjs.com/package/@testing-library/dom/v/10.4.2 | Solo desarrollo: peer obligatorio de `@testing-library/react`. Publicada el 2026-09-13. |
| @testing-library/user-event | 14.6.8 | MIT | npm: https://www.npmjs.com/package/@testing-library/user-event/v/14.6.8 | Solo desarrollo: simula teclado y clic en las pruebas de componentes. Publicada el 2026-10-13. |
| jsdom | 30.1.3 | MIT | npm: https://www.npmjs.com/package/jsdom/v/30.1.3 | Solo desarrollo: DOM de las pruebas de componentes (no calcula layout; el tamaño de objetivo real se mide en T-00-017). Publicada el 2026-10-15. |
| axe-core | 4.14.0 | MPL-2.0 | npm: https://www.npmjs.com/package/axe-core/v/4.14.0 | Solo desarrollo: comprobación de accesibilidad por componente y estado (AX-11). Sin modificar. Publicada el 2026-10-05. |
| vite | 8.3.6 | MIT | npm: https://www.npmjs.com/package/vite/v/8.3.6 | Solo desarrollo: sirve y compila el catálogo de componentes (T-00-017). Versión y licencia comprobadas en el paquete instalado. |
| next | 16.4.6 | MIT | npm: https://www.npmjs.com/package/next/v/16.4.6 | App Router y puente de autenticación del lado del servidor para `apps/web` (T-00-012). Versión y licencia comprobadas en el registro y el paquete instalado. |
| caniuse-lite | 1.0.30001826 | CC-BY-4.0 | npm: https://www.npmjs.com/package/caniuse-lite/v/1.0.30001826 | Datos de compatibilidad de navegadores de caniuse.com, dependencia transitiva de Next.js. Autor del paquete: Ben Briggs; proyecto Browserslist. Sin modificaciones. Excepción limitada al paquete y versión en `approved_licenses.yaml`. Licencia completa en `docs/licenses/caniuse-lite-LICENSE.txt`. |
| @playwright/test | 1.65.0 | Apache-2.0 | npm: https://www.npmjs.com/package/@playwright/test/v/1.65.0 | Solo desarrollo: navegador real para accesibilidad, geometría y teclado del catálogo (T-00-017). Versión y licencia comprobadas en el paquete instalado. |
| Atkinson Hyperlegible (fuente) | 5.3.0 | OFL-1.1 | npm: https://www.npmjs.com/package/@fontsource/atkinson-hyperlegible/v/5.3.0 | Fuente del producto (MASTER.md). No es dependencia npm: se copian los archivos woff2 latin 400 y 700 y la licencia a `packages/ui/src/fonts/` (autoalojada, sin CDN). OFL-1.1 solo para este recurso tipográfico, registrada como fuente y no como código. Publicada el 2026-07-19. |
| Atkinson Hyperlegible Next (fuente) | 2.001 | OFL-1.1 | https://github.com/google/fonts/tree/main/ofl/atkinsonhyperlegiblenext | Tipografía exacta de Stitch UI-UX. Variable TTF original sin modificar, autoalojada en `packages/ui/src/fonts/atkinson-hyperlegible-next-variable.ttf`; licencia íntegra en `OFL-Next.txt`. SHA-256 `5a455d1cfa099b601ab70751bb9673e8fe1854dc4500c80e1a220d0d75e31745`. Sin CDN ni dependencia npm; OFL solo para este recurso tipográfico. |

## Infraestructura de prueba

`infra/compose.test.yaml` usa una imagen externa ya disponible localmente,
`pgvector/pgvector@sha256:0dd3149a06e4579a0d70d8fef9945636cd514005e7237deb27f9b67886f8dc4f`.
Se verificaron PostgreSQL 16.15 mediante su ejecutable y pgvector 0.8.7 mediante
`vector.control`. Su finalidad es la integración sintética de persistencia; la imagen
no se empaqueta en la web ni en el companion.

PostgreSQL declara licencia PostgreSQL en el archivo de copyright de su paquete.
La licencia de pgvector 0.8.7 se revisó en el
[archivo del proyecto](https://github.com/pgvector/pgvector/blob/v0.8.7/LICENSE);
es el texto permisivo PostgreSQL. El detector de GitHub devuelve `NOASSERTION`,
por lo que no se usó esa etiqueta como prueba de ausencia de licencia.

La auditoría de paquetes Python y npm no audita la imagen completa. Antes de
distribuir imágenes se debe incluir el sistema base y sus componentes en la revisión
del artefacto. Esta incorporación de prueba no cambia la lista de licencias
admitidas para los paquetes distribuidos.
