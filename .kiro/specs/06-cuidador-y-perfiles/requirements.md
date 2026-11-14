# Requisitos: 06 Cuidador y perfiles

**Estado:** completo. Notación y tipos de prueba: `01-capa-de-entrada/requirements.md` sección 0.
**Cubre:** panel básico del cuidador/a, delegaciones (permisos delegados y revocables) y gestión de perfiles de capacidad desde la cuenta.
**Vertical aplicable:** V-01, V-09, V-11, V-12. Propiedad: SP-4. Regla AX-17.

## 1. Principios

- La persona decide quién la acompaña y qué puede hacer cada cuidador/a.
- Un cuidador/a **nunca** decide ni aprueba por la persona sin una delegación explícita y vigente.
- Todo lo que hace un cuidador/a es visible para la persona y queda en la bitácora.
- La persona puede usar el sistema sin ningún cuidador/a.

## 2. Alcances de delegación (catálogo del MVP) [SUPUESTO]

| Alcance | Permite |
| --- | --- |
| `devices.configure` | Configurar dispositivos y ayudar con la calibración. |
| `profile.edit` | Editar perfiles de capacidad. |
| `progress.view` | Ver contadores de progreso (sin contenido). |
| `content.view` | Ver el contenido de tareas y propuestas. |
| `tasks.start` | Iniciar tareas en nombre de la persona. |
| `tools.manage` | Habilitar o deshabilitar herramientas conectadas. |
| `autonomy.set` | Cambiar el nivel de autonomía. |
| `consents.assist` | Ayudar a la persona con los consentimientos. |
| `approval.grant` | Aprobar acciones, limitado a los tipos de tarea que la persona indique. |

## 3. Requisitos funcionales

### Grupo A. Cuenta del cuidador/a e invitación

**HU-06-A.** Como persona, quiero invitar a quien me ayuda y decidir qué puede hacer, para recibir apoyo sin perder el control.

- **REQ-06-001** THE SYSTEM SHALL permitir a la persona invitar a un cuidador/a (por correo o código) y definir, en la misma invitación, los alcances que le delega. Prueba: `e2e`.
- **REQ-06-002** THE SYSTEM SHALL crear para el cuidador/a una cuenta y una sesión propias, con rol `caregiver`, distintas de las de la persona. Prueba: `security`.
- **REQ-06-003** THE SYSTEM SHALL dar a un cuidador/a recién invitado **ningún alcance** salvo los que la persona haya marcado explícitamente. Prueba: `unit`.
- **REQ-06-004** THE SYSTEM SHALL permitir más de un cuidador/a por persona y ninguno, con delegaciones independientes. Prueba: `unit`.
- **REQ-06-005** WHEN un cuidador/a acepta una invitación, THE SYSTEM SHALL mostrar a la persona quién aceptó y qué puede hacer, y registrarlo en la bitácora. Prueba: `e2e`.
- **REQ-06-006** THE SYSTEM SHALL NOT permitir que un cuidador/a invite a otro cuidador/a ni se otorgue alcances a sí mismo. Prueba: `security`.

### Grupo B. Delegaciones

- **REQ-06-010** THE SYSTEM SHALL representar cada delegación con: cuidador/a, alcances, tipos de tarea cuando aplique, fecha de inicio, fecha de fin opcional elegida por la persona y estado (vigente, revocada, vencida). Prueba: `contract`.
- **REQ-06-011** THE SYSTEM SHALL crear, ampliar o cambiar una delegación solo por una intención de la persona con su propia modalidad (`actor_origin = person`) y NOT por una solicitud del cuidador/a, que solo puede pedirla. Prueba: `security`.
- **REQ-06-012** WHEN la persona revoca una delegación, por cualquier modalidad (incluida una orden de voz), THE SYSTEM SHALL aplicarlo de inmediato, invalidar las sesiones de acción del cuidador/a para ese alcance y cancelar sus acciones pendientes de despacho. Prueba: `integration`.
- **REQ-06-013** WHEN una delegación llega a su fecha de fin, THE SYSTEM SHALL dejarla vencida y NOT permitir su uso, avisando a la persona y al cuidador/a. Prueba: `unit`.
- **REQ-06-014** THE SYSTEM SHALL exponer al motor de políticas (spec 02) una consulta de delegación vigente por cuidador/a, alcance, persona y tipo de tarea, que responda con el estado en el momento de decidir. Prueba: `contract`.
- **REQ-06-015** IF un cuidador/a intenta una acción sin una delegación vigente que la cubra, THEN THE SYSTEM SHALL rechazarla, registrar el intento y mostrar al cuidador/a un mensaje claro (SP-4). Prueba: `security`.
- **REQ-06-016** THE SYSTEM SHALL tratar el alcance `approval.grant` como el más sensible: requiere indicar tipos de tarea, se confirma con una aprobación explícita de la persona que describa su efecto y se muestra siempre destacado. Prueba: `e2e`.
- **REQ-06-017** WHEN un cuidador/a usa una delegación, THE SYSTEM SHALL registrar quién, qué alcance, qué acción y cuándo, y mostrárselo a la persona en su vista de actividad de acompañantes. Prueba: `integration`.
- **REQ-06-018** THE SYSTEM SHALL NOT permitir que un cuidador/a oculte, borre o altere el registro de sus propias acciones (AX-17). Prueba: `security`.
- **REQ-06-019** THE SYSTEM SHALL permitir a la persona ver en cualquier momento, en lenguaje llano, todas sus delegaciones vigentes y revocarlas. Prueba: `e2e`.

### Grupo C. Panel del cuidador/a

- **REQ-06-030** THE SYSTEM SHALL ofrecer al cuidador/a un panel con: estado de los dispositivos y modalidades, ayuda con la calibración, perfiles de capacidad, contadores de progreso, y su propia actividad, todo limitado por sus alcances. Prueba: `e2e`.
- **REQ-06-031** THE SYSTEM SHALL ocultar al cuidador/a el contenido de tareas, propuestas, memoria, bitácora de contenido y condición declarada salvo que tenga el alcance `content.view`, y la condición declarada SHALL NOT ser visible en ningún caso para el cuidador/a. Prueba: `security`.
- **REQ-06-032** WHERE el cuidador/a tiene `progress.view`, THE SYSTEM SHALL mostrarle contadores (tareas completadas por semana) sin contenido ni títulos. Prueba: `e2e`.
- **REQ-06-033** WHERE el cuidador/a tiene `devices.configure`, THE SYSTEM SHALL permitirle iniciar la calibración asistida del companion y probar dispositivos, publicando sus intenciones con `actor_origin = caregiver`. Prueba: `integration`.
- **REQ-06-034** THE SYSTEM SHALL mostrar al cuidador/a, en cada acción que realiza, que actúa por delegación de la persona y bajo qué alcance. Prueba: `e2e`.
- **REQ-06-035** THE SYSTEM SHALL NOT permitir al cuidador/a exportar ni borrar datos de la persona; esas acciones son solo de la persona. Prueba: `security`.
- **REQ-06-036** THE SYSTEM SHALL NOT enviar al cuidador/a alertas de crisis, salvo que sea además el contacto de confianza que la persona autorizó (spec 05). Prueba: `unit`.

### Grupo D. Perfiles de capacidad y cuenta

- **REQ-06-040** THE SYSTEM SHALL mostrar a la persona, y a un cuidador/a con `profile.edit`, la lista de perfiles de capacidad del dispositivo (por ejemplo «en cama», «sentado») con su historial de versiones. Prueba: `e2e`.
- **REQ-06-041** WHEN un cuidador/a con `profile.edit` cambia un perfil, THE SYSTEM SHALL aplicarlo como una nueva versión pendiente que la persona vea y apruebe o revierta, y NOT sustituir la versión en uso sin su aprobación. Prueba: `e2e`.
- **REQ-06-042** THE SYSTEM SHALL validar los cambios de perfil con las invariantes de la spec 01 (ruta de Alto y Deshacer en cada modalidad habilitada) también cuando los hace un cuidador/a. Prueba: `unit`.
- **REQ-06-043** THE SYSTEM SHALL mantener los datos de la cuenta de la persona (nombre, idioma, preferencias de retroalimentación, condición declarada opcional) separados del perfil de capacidad. Prueba: `unit`.
- **REQ-06-044** THE SYSTEM SHALL permitir a la persona exportar y borrar sus perfiles y su cuenta (spec 07). Prueba: `e2e`.

### Grupo E. Estados de pantalla

- **REQ-06-050** THE SYSTEM SHALL cumplir los estados de AX-11 en el panel y en la vista de delegaciones: *cargando*, *vacío* (sin cuidadores: se ofrece invitar sin presionar), *error*, *sin conexión* (el panel indica qué no está disponible) y *modalidad no detectada* (en la vista de dispositivos). Prueba: `e2e`.

## 4. Requisitos no funcionales

- **REQ-06-060** THE SYSTEM SHALL cumplir WCAG 2.2 AA, y como objetivo AAA 44×44 px CSS y ausencia de límites de tiempo, en el panel del cuidador/a y en la vista de delegaciones de la persona (AX-17). Prueba: `a11y`.
- **REQ-06-061** THE SYSTEM SHALL aplicar una revocación en un máximo de 2 s en el 95% de los casos [SUPUESTO]. Prueba: `perf`.
- **REQ-06-062** THE SYSTEM SHALL firmar las delegaciones y rechazar las alteradas. Prueba: `security`.
- **REQ-06-063** THE SYSTEM SHALL tratar las delegaciones y la actividad de acompañantes como datos personales protegidos, cifrados en reposo. Prueba: `security`.

## 5. Dependencias

| Spec | Relación |
| --- | --- |
| 00 | Autenticación, roles y componentes |
| 01 | Origen `caregiver`, calibración asistida, invariantes del perfil |
| 02 | Motor de políticas consulta delegaciones |
| 03 | Aprobación y registro de actividad |
| 05 | Consentimientos asistidos |
| 07 | Exportación y borrado |

## 6. Preguntas abiertas

PA-21 (verificación de identidad del cuidador/a). Representación legal de personas con incapacidad `[verificar con abogado]`, relevante antes de ofrecerlo a personas reales.
