# Herramientas del pipeline de construcción

Inventario hecho el 2026-11-14 sobre lo que realmente está instalado. Los nombres y comandos son los reales, leídos de cada `SKILL.md` o archivo de comando. Si una herramienta cambia de versión, se actualiza esta tabla.

## 1. Dónde viven

| Fuente | Ruta | Nota |
| --- | --- | --- |
| Skills del repo | `.claude/skills/`, `.agents/skills/`, `.kiro/skills/` | Las tres carpetas son **idénticas** (12 skills, comprobado con `diff -rq`). `skills-lock.json` fija origen y hash. La copia que usa Claude Code es `.claude/skills/`. |
| Plugins de usuario | `~/.claude/plugins/cache/` | Instalados a nivel de usuario; aplican a este proyecto. |

## 2. Skills del repo

| Skill (nombre exacto) | Origen | Para qué sirve | Cuándo se invoca aquí | Comandos reales |
| --- | --- | --- | --- | --- |
| `ui-ux-pro-max` | nextlevelbuilder/ui-ux-pro-max-skill | Base de datos de estilos, paletas, tipografías y guías UX con buscador BM25; genera un design system. | Primera tarea `[UI]`: generar y persistir el design system. Consultas puntuales de UX y de stack (`nextjs`). | `python .claude/skills/ui-ux-pro-max/scripts/search.py "<consulta>" --design-system --persist -p "Coalsense Dispatch" --output-dir "<raíz>"` · `--domain <dominio>` · `--stack <stack>` · `--page "<pantalla>"`. Nunca `--force` sin permiso. |
| `impeccable` (v4.9.1 en el repo; plugin 4.8.0) | pbakaus/impeccable | Diseño y revisión de interfaces: contexto de producto, crítica, auditoría, pulido y robustez. Modo **Operate** para esta app. | Cada tarea `[UI]`: `init` al inicio; tras cada pantalla `critique → audit → polish → harden`. | Setup: `.claude/skills/impeccable/scripts/impeccable.cmd context` (Windows sin `sh`). Comandos vía skill: `init`, `shape`, `document`, `extract`, `critique`, `audit`, `polish`, `harden`, `clarify`, `adapt`, `distill`, `quieter`, `onboard`, `doctor`, `hooks`. |
| `design-taste-frontend` (tasteskill 2.5.1) | Leonxlnx/taste-skill | Criterio "anti-slop" para sitios web de empresa: copia, ritmo, fotos, gate en navegador. | Solo como criterio senior de base. Su plan de página (hero, fotos, shaders) es para sitios de marketing y **no** aplica a la app. Instala un hook `Stop` que corre `scripts/gate.mjs` si existe `.taste-skill/`. | `node .claude/skills/design-taste-frontend/scripts/gate.mjs <html>` · `copy-lint.mjs` · `consistency.mjs` · `perf.mjs`. |
| `frontend-design` | vercel-labs/agent-eval | Guía estética breve para interfaces distintivas. | Opcional, subordinada a `accessibility.md`. | Sin scripts. |
| `design-system` | ui-ux-pro-max-skill | Tokens en tres capas (primitivo → semántico → componente) y especificación de componentes. | Tarea de tokens de `packages/ui` (T-00-013). | `node .claude/skills/design-system/scripts/generate-tokens.cjs --config tokens.json -o tokens.css` · `validate-tokens.cjs --dir src/`. |
| `ui-styling` | ui-ux-pro-max-skill | shadcn/ui, Radix, Tailwind. | Solo si `00/design.md` elige ese stack de componentes. | `python .claude/skills/ui-styling/scripts/shadcn_add.py <componentes>` · `tailwind_config_gen.py`. |
| `design` | ui-ux-pro-max-skill | Logo, identidad corporativa, iconos, banners, fotos sociales. | **No se usa**: la regla es no inventar logo ni ilustraciones; los assets los da el operador. | `python3 scripts/logo/...` (no aplica). |
| `brand` | ui-ux-pro-max-skill | Voz de marca y sincronización de guías a tokens. | Opcional, si el operador entrega guía de marca. | `node .claude/skills/brand/scripts/sync-brand-to-tokens.cjs` · `inject-brand-context.cjs`. |
| `banner-design`, `slides` | ui-ux-pro-max-skill | Banners y presentaciones HTML. | Fuera del MVP; quizá en el guion de demo (spec 09). | Sin uso previsto. |
| `caveman` | JuliusBrussee/caveman | Voz comprimida para reportes. | Reportes operativos y reportes de una línea de los subagentes. Nunca en documentos ni código. | `/caveman`, `/caveman ultra`, "normal mode". |
| `caveman-commit` | JuliusBrussee/caveman | Mensaje Conventional Commits comprimido a la intención. | Cierre de cada tarea: un commit por tarea. Tipos en inglés (`feat`, `fix`…), resumen en español. Solo redacta el mensaje; no ejecuta `git commit`. | `/caveman-commit`. |

## 3. Plugins de usuario relevantes

| Plugin | Versión | Para qué | Comandos y agentes reales | Quién puede lanzarlo |
| --- | --- | --- | --- | --- |
| **codex** (openai-codex) | 1.0.6 | Codex como constructor paralelo y revisor cruzado. CLI `codex-cli 0.166.0`, sesión iniciada (comprobado con `setup --json`: `ready: true`). | `/codex:rescue` (encargo de construcción o diagnóstico; subagente `codex:codex-rescue`), `/codex:review` (revisión normal), `/codex:adversarial-review` (revisión adversarial), `/codex:status`, `/codex:result`, `/codex:cancel`, `/codex:setup`, `/codex:transfer`. Flags: `--wait`, `--background`, `--base <ref>`, `--scope auto\|working-tree\|branch`, `--model`, `--effort`, `--resume`, `--fresh`. | **Yo** puedo invocar `/codex:rescue` (vía agente `codex:codex-rescue`). **`/codex:review` y `/codex:adversarial-review` tienen `disable-model-invocation: true`: solo el operador puede lanzarlos.** Les entrego el comando exacto listo para pegar. Ambos requieren un repositorio git. |
| **ponytail** | 5.3.3 | Simplificación: el cambio más pequeño que resuelve todo. | `/ponytail-review` (revisión de un cambio), `/ponytail-audit` (auditoría del repo completo), `/ponytail-debt`, `/ponytail-gain`, `/ponytail-help`, `/ponytail lite\|full\|ultra`. | Yo (skills `ponytail:ponytail-review`, `ponytail:ponytail-audit`). Activo por hook al iniciar sesión. |
| **superpowers** | 7.0.2 | Disciplina de proceso. | Skills: `superpowers:brainstorming`, `superpowers:writing-plans`, `superpowers:subagent-driven-development`, `superpowers:dispatching-parallel-agents`, `superpowers:test-driven-development`, `superpowers:systematic-debugging`, `superpowers:requesting-code-review`, `superpowers:receiving-code-review`, `superpowers:verification-before-completion`, `superpowers:finishing-a-development-branch`, `superpowers:using-git-worktrees`. | Yo. |
| **caveman** (plugin) | 4.0.1 | Igual que la skill, más agentes. | Agentes `caveman:cavecrew-builder` (edición de 1–2 archivos), `caveman:cavecrew-investigator` (localizar código), `caveman:cavecrew-reviewer` (revisión de diff). Skills `caveman:caveman-review`, `caveman:verify-and-stop`, `caveman:safe-refactor`. | Yo. |
| **impeccable** (plugin) | 4.8.0 | Igual que la skill, más agentes. | `impeccable:impeccable-documenter` (escribe DESIGN.md desde lo construido), `impeccable:impeccable-finish-reviewer`. | Yo. |
| **ui-ux-pro-max** (plugin) | 2.5.0 | Igual que la skill. La copia del repo es más nueva; se usa la del repo. | — | Yo. |
| **code-review** | 1.0.1 | Revisión de PR. | `/code-review <nivel>`. | Opcional. |

## 4. Diferencias con lo que pidió el operador

| Esperado | Real | Efecto |
| --- | --- | --- |
| `design-system/MASTER.md` | UI-UX Pro Max escribe `design-system/<slug-del-proyecto>/MASTER.md` (con `pages/` para excepciones por pantalla). | Ruta real: `design-system/coalsense-dispatch/MASTER.md` `[SUPUESTO: slug generado del nombre]`. |
| "Impeccable init crea PRODUCT.md y DESIGN.md" | `init` solo crea `PRODUCT.md`. `DESIGN.md` lo crea el flujo de trabajo nuevo de Impeccable o `document` / el agente `impeccable-documenter` a partir de lo construido. | Orden: `init` → primera pantalla → `document` (DESIGN.md). Los choques con `accessibility.md` se anotan en DESIGN.md. |
| Taste Skill como criterio de base | Está orientada a sitios de marketing. | Se toma su criterio de copia, coherencia y rendimiento; se ignora su plan de página. |
| `/codex:review` y `/codex:adversarial-review` invocables por mí | Bloqueados para el modelo. | En cada hito te paso el comando exacto para que lo lances tú. |
| Repositorio git | La carpeta no era un repositorio git. | `git init -b main` hecho el 2026-11-14 con autorización del operador. Sin remoto. Las skills vendorizadas no se versionan: se reinstalan desde `skills-lock.json`. |

## 5. Entorno local comprobado

`git 2.54.0`, `node v24.19.0`, `npm 11.17.0`, `pnpm 11.21.0`, `python 3.12.10`, `uv 0.12.13`, `docker 29.9.2`, `codex-cli 0.166.0`.
