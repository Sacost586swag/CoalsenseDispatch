# Estructura del monorepo

> Disposición **[SUPUESTO]**. El interior de cada app se refina en el `design.md` de su spec.

## Árbol

```
.
├─ .kiro/
│  ├─ steering/                 product, tech, structure, accessibility, safety
│  └─ specs/
│     ├─ 00-fundaciones/        requirements.md, design.md, tasks.md
│     ├─ 01-capa-de-entrada/
│     ├─ 02-orquestador-y-agentes/
│     ├─ 03-ciclo-de-control/
│     ├─ 04-espacio-de-trabajo/
│     ├─ 05-seguridad-y-bienestar/
│     ├─ 06-cuidador-y-perfiles/
│     ├─ 07-privacidad-y-datos/
│     ├─ 08-mercado-b2b/        fase 2: solo requisitos y diseño
│     ├─ 09-despliegue/
│     ├─ ORDEN-DE-CONSTRUCCION.md
│     ├─ GLOSARIO.md
│     ├─ TRAZABILIDAD.md
│     └─ PREGUNTAS-ABIERTAS.md
├─ apps/
│  ├─ companion/                Python 3.12 (uv)
│  ├─ web/                      Next.js + TypeScript (pnpm)
│  └─ orchestrator/             FastAPI (uv)
├─ packages/
│  ├─ intents/                  JSON Schema + tipos generados (Python y TypeScript)
│  ├─ safety/                   reglas de crisis, mensajes fijos y límites (Python y TypeScript)
│  ├─ common-py/                configuración, errores, ids, registros e indicadores de función (Python)
│  ├─ common-ts/                lo mismo para TypeScript
│  └─ ui/                       design system accesible
├─ tools/audit/                 auditorías de CI (licencias, esquema, importaciones, trazabilidad)
├─ infra/                       docker-compose: PostgreSQL + pgvector, Redis, n8n (opcional)
├─ docs/                        investigación base; data-inventory.yaml (inventario de datos)
├─ THIRD_PARTY.md               licencias, versiones y origen de cada dependencia
├─ pnpm-workspace.yaml
├─ turbo.json
└─ pyproject.toml               workspace de uv
```

## Interior orientativo de cada app [SUPUESTO]

```
apps/companion/src/coalsense_companion/
  adapters/    voice/, head_gesture/, gaze/, switch_scan/, keyboard_mouse/
  bus/         bus de intenciones, prioridades, autenticación de adaptadores
  calibration/ asistente y cálculo de umbrales
  profile/     perfil de capacidad: esquema, almacenamiento, migraciones
  actuator/    ejecución en el sistema operativo, números en pantalla, cuadrícula
  commands/    archivos de comandos de voz y su intérprete
  privacy/     indicadores, apagado total, política de egreso
apps/companion/tests/fixtures/{landmarks,audio}/   con manifest.json

apps/orchestrator/src/coalsense_orchestrator/
  gateway/     ÚNICO lugar con llamadas salientes a APIs externas
  policy/      motor de políticas (aprobaciones, autonomía)
  agents/      planificador, enrutador, agentes de trabajo
  memory/      memoria (pgvector)
  audit/       bitácora

apps/web/src/
  app/         rutas (Next.js)
  features/    espacio de trabajo, logros, panel del cuidador, modo web de visión
```

## Reglas de dependencia

1. `apps/*` pueden depender de `packages/*`. `packages/*` nunca dependen de `apps/*`.
2. Las apps no se importan entre sí. Se comunican por red o por el bus, usando solo tipos de `packages/intents`.
3. Solo `apps/orchestrator/.../gateway/` hace llamadas salientes a APIs externas (V-08).
4. Ningún módulo de `agents/` importa el cliente de base de datos de producción.
5. En `apps/companion`, los módulos de visión y de voz no importan librerías de red.

## Mapa spec → rutas

| Spec | Rutas principales |
| --- | --- |
| 00-fundaciones | raíz del monorepo, CI, `packages/ui`, autenticación |
| 01-capa-de-entrada | `apps/companion`, `packages/intents`, modo web de visión en `apps/web` |
| 02-orquestador-y-agentes | `apps/orchestrator` |
| 03-ciclo-de-control | `apps/web`, `apps/orchestrator` |
| 04-espacio-de-trabajo | `apps/web`, `apps/orchestrator` |
| 05-seguridad-y-bienestar | `apps/orchestrator`, copia local de mensajes y números en `apps/companion` |
| 06-cuidador-y-perfiles | `apps/web`, `apps/orchestrator` |
| 07-privacidad-y-datos | `apps/orchestrator`, `infra/`, almacenamiento local del companion |
| 08-mercado-b2b | `apps/web`, `apps/orchestrator` (fase 2) |
| 09-despliegue | `infra/`, empaquetado de `apps/companion` |

## Convenciones [SUPUESTO]

- Identificadores de código, tipos de intención y nombres de archivo en **inglés**. Documentación y texto de interfaz en **español**.
- Python: `snake_case`. TypeScript: `kebab-case` en archivos, `camelCase` en variables.
- IDs de requisitos `REQ-<spec>-<nnn>`; propiedades `SP-n` (ver `safety.md`); reglas de la vertical `V-nn`; reglas de accesibilidad `AX-nn`.
- Cada tarea cita los IDs de requisito que cubre y la ruta exacta de sus archivos.
