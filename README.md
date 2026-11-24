# Coalsense Dispatch

Coalsense Dispatch es un sistema operativo de IA (AIOS) para que personas con discapacidad física o con depresión controlen la computadora sin las manos y produzcan trabajo pagado con ayuda de agentes.

El acceso físico a la computadora (voz, cabeza, mirada) ya existe gratis y abierto. Lo que falta es la capa de arriba: convertir «puedo mover el cursor» en «puedo cobrar por un trabajo». El propósito de fondo es romper la indefensión aprendida. Cada interacción le deja a la persona una experiencia real de control, decidida por ella.

> Estado: en construcción. El hito H0 (cimientos) está casi terminado y H1–H2 están en desarrollo. No está listo para personas reales: ver [Antes de ofrecerlo a personas reales](#antes-de-ofrecerlo-a-personas-reales).

## La vertical

Estas reglas no se negocian. Si una decisión de diseño, técnica o de alcance las contradice, gana la vertical. Fuente completa: [`.kiro/steering/product.md`](.kiro/steering/product.md).

| ID | Regla |
| --- | --- |
| V-01 | **La persona decide, la IA ejecuta.** Ninguna acción con efecto externo (enviar, publicar, cobrar, borrar, compartir) ocurre sin la aprobación explícita de la persona. |
| V-02 | **Ciclo de control en cada tarea:** la persona elige → los agentes ejecutan → la persona revisa y aprueba → el resultado sale al mundo → queda registrado como logro. |
| V-03 | **Dial de autonomía** por tipo de tarea. Por defecto la persona aprueba todo y solo ella lo sube. Nunca elimina la aprobación de una acción externa. |
| V-04 | **«Alto» y «Deshacer» universales,** siempre activos en todas las modalidades de entrada. |
| V-05 | **Sin manos y sin precisión motora fina.** Nada depende de clic preciso, arrastre, doble clic ni límites de tiempo. WCAG 2.2 AA como mínimo. |
| V-06 | **Cámara y micrófono se procesan en el dispositivo.** Ningún cuadro de video, audio ni landmark facial sale de la máquina. |
| V-07 | **No es terapia.** No diagnostica ni trata. Ante señales de crisis deriva a una persona, con mensajes fijos que no genera un modelo. |
| V-08 | **Ley de Arthur.** El orquestador razona y delega; las herramientas ejecutan a través de un gateway; ninguna acción externa ocurre sin política; toda ejecución queda en una bitácora que la persona puede leer. |
| V-09 | **Datos sensibles bajo la LOPDP** (Ecuador): consentimiento, minimización, cifrado, exportación y borrado. El perfil de capacidad nunca llega al proveedor del modelo. |
| V-10 | **Licencias.** Talon solo inspira el diseño, no se embebe. Project Gameface (Apache 2.0) se reutiliza con atribución. Sin GPL en el artefacto distribuido. |
| V-11 / V-12 | **El operador no ve contenido privado.** El cuidador/a actúa con permisos delegados y revocables, y nunca aprueba por la persona sin permiso vigente. |

La accesibilidad manda sobre cualquier decisión estética. Las reglas AX-01 a AX-17 de [`.kiro/steering/accessibility.md`](.kiro/steering/accessibility.md) fijan, entre otras cosas, objetivos de 44×44 px como mínimo, aprobaciones sin opción preseleccionada ni vencimiento, y estados que nunca culpan a la persona.

## Alcance del MVP

Calibración que termina con la primera tarea completada en la sesión 1. Control de la app y del PC por voz y por cabeza y gestos. Tres tipos de tarea con aprobación:

1. Redactar y enviar un correo o mensaje profesional.
2. Convertir notas dictadas en un documento ordenado.
3. Preparar una publicación para redes sociales y dejarla lista para publicar.

Además: registro de logros, protocolo de crisis con derivación a una persona y panel básico del cuidador/a. Fuera del MVP: mercado de trabajos B2B y pagos, app Android y habla atípica.

## Arquitectura

| Ruta | Qué es |
| --- | --- |
| `apps/companion` | App de escritorio en Python 3.12 (Windows primero): entrada por voz y por cabeza y gestos procesada en el dispositivo, bus de intenciones, actuador del sistema operativo y almacén de credenciales del sistema. |
| `apps/orchestrator` | FastAPI: autenticación sin contraseña, planificador, agentes, gateway de herramientas, motor de políticas, persistencia y bitácora. |
| `apps/web` | Next.js + TypeScript: espacio de trabajo, logros y panel del cuidador/a. |
| `packages/intents` | Esquema único de intenciones (JSON Schema) con tipos generados para Python y TypeScript. |
| `packages/ui` | Design system accesible: tokens, temas (alto contraste, movimiento reducido), componentes, barra de Alto y Deshacer, tarjeta de aprobación y registro de objetivos de navegación. |
| `packages/common-py`, `packages/common-ts` | Configuración validada, formato de error común, ids UUIDv7 y registros que no guardan contenido privado. |
| `tools/audit` | Auditorías de CI: licencias, importaciones prohibidas, secretos, textos de interfaz, trazabilidad y glosario, y deriva del esquema. |
| `.kiro/` | Fuente de verdad: steering (vertical, técnica, estructura, accesibilidad, seguridad) y specs por módulo. |

## Requisitos

Node 24, pnpm 11.21.0, Python 3.12 y uv 0.12.13.

```bash
pnpm install --frozen-lockfile
uv sync --locked
pnpm turbo run lint typecheck test build
pnpm turbo run audit
```

La configuración se carga desde variables de entorno validadas. Usa los `.env.example` como guía y nunca subas un `.env` con valores reales.

## Seguridad y privacidad

- Ningún secreto vive en el repositorio. La CI corre una auditoría de secretos en cada cambio, y `.env`, claves y certificados están en `.gitignore`.
- Los registros técnicos solo guardan metadatos: nunca texto dictado, cuerpos de correo, nombres de archivo ni el perfil de capacidad.
- La autenticación no usa contraseñas, CAPTCHA ni pruebas cognitivas. Los códigos no vencen por tiempo y el emparejamiento de un equipo exige que la persona lo confirme en ese mismo equipo.
- Para reportar un problema de seguridad, escribe en privado al responsable del repositorio en lugar de abrir un issue público.

## Antes de ofrecerlo a personas reales

Terminar el MVP no autoriza ofrecerlo a personas reales. Antes hace falta (ver `safety.md`, SF-06):

- Al menos una ruta humana de ayuda configurada y probada.
- Reglas y mensajes de crisis revisados por un profesional de salud mental.
- Revisión legal bajo la LOPDP y consentimiento informado por escrito.

## Documentación

- Plan de construcción: [`docs/PLAN.md`](docs/PLAN.md) y [`.kiro/specs/ORDEN-DE-CONSTRUCCION.md`](.kiro/specs/ORDEN-DE-CONSTRUCCION.md).
- Reglas para agentes: [`CLAUDE.md`](CLAUDE.md).
- Referencias de diseño (Project Gameface, Talon): [`docs/REFERENCIAS.md`](docs/REFERENCIAS.md).
- Dependencias de terceros y sus licencias: [`THIRD_PARTY.md`](THIRD_PARTY.md).

## Licencia

MIT. Ver [`LICENSE`](LICENSE).
