# Requisitos: 08 Mercado B2B (fase 2)

**Estado:** completo. **Fase 2: solo requisitos y diseño; sin tareas del MVP.** Notación y tipos de prueba: `01-capa-de-entrada/requirements.md` sección 0. Todo hito es `[FASE-2]`.
**Cubre:** empresas clientes, trabajos, asignación y entrega, cuota laboral del 4%, cobros.
**Vertical aplicable:** V-01, V-09, V-11, V-12. La persona sigue decidiendo qué trabajo toma y qué entrega.
**Fuente:** `docs/IA contra la indefensión aprendida — Investigación base.md` (modelo en que paga la empresa; cuota del 4% en Ecuador; riesgo de pago por pieza en anotación de datos).
**Nota legal:** todo lo marcado `[verificar con abogado]` es una hipótesis sin confirmar.

## 1. Alcance

Dentro: cuentas de empresa, publicación de trabajos, asignación, revisión de entregables, certificación de cuota, cobros y facturación, protección de la persona frente a la empresa.
Fuera del MVP: todo lo anterior. En el MVP la persona completa tareas propias (spec 03).

## 2. Requisitos funcionales

### Grupo A. Empresa cliente

- **REQ-08-001** THE SYSTEM SHALL permitir a una empresa crear una cuenta y verificar su identidad legal (razón social y registro tributario) antes de publicar trabajos `[verificar con abogado los requisitos]`. Prueba: `e2e`.
- **REQ-08-002** THE SYSTEM SHALL asignar a la empresa un rol distinto (`company`) sin ningún permiso sobre datos privados de las personas. Prueba: `security`.
- **REQ-08-003** THE SYSTEM SHALL NOT mostrar a la empresa, en ninguna pantalla ni API, el perfil de capacidad, la condición declarada, el uso de modalidades, los consentimientos ni los eventos de crisis de ninguna persona. Prueba: `security`.

### Grupo B. Trabajos

- **REQ-08-010** THE SYSTEM SHALL permitir a la empresa publicar un trabajo con descripción, entregable esperado, plazo de referencia, pago ofrecido y criterios de aceptación. Prueba: `e2e`.
- **REQ-08-011** THE SYSTEM SHALL mostrar a la persona el pago ofrecido de forma transparente, indicando si es por hora o por entregable, y las comisiones. Prueba: `e2e`.
- **REQ-08-012** THE SYSTEM SHALL permitir que el plazo de referencia de un trabajo sea ajustable por acuerdo, y NOT penalizar a la persona por pausas ni por plazos (AX-03). Prueba: `e2e`.
- **REQ-08-013** THE SYSTEM SHALL describir cada trabajo en lenguaje llano y con la misma estructura accesible que una tarea (AX-12). Prueba: `a11y`.
- **REQ-08-014** THE SYSTEM SHALL NOT permitir trabajos que exijan a la persona ceder control sobre sus datos o sobre la decisión de aprobar sus entregables. Prueba: `unit`.

### Grupo C. Asignación y entrega

- **REQ-08-020** WHEN una persona acepta un trabajo, THE SYSTEM SHALL tratarlo como una tarea del ciclo de control (spec 03), con plan, aprobación y registro, y la aceptación SHALL ser una decisión explícita de la persona. Prueba: `e2e`.
- **REQ-08-021** THE SYSTEM SHALL permitir a la persona rechazar un trabajo sin consecuencias ni explicación. Prueba: `unit`.
- **REQ-08-022** WHEN la persona aprueba el entregable, THE SYSTEM SHALL enviarlo a la empresa como acción `external_effect` con aprobación (V-01), mostrando exactamente qué recibe la empresa. Prueba: `e2e`.
- **REQ-08-023** THE SYSTEM SHALL permitir a la empresa aceptar el entregable o pedir cambios con comentarios, y a la persona revisarlos y decidir cómo responder. Prueba: `e2e`.
- **REQ-08-024** THE SYSTEM SHALL mostrar a la empresa solo el nombre público que la persona eligió y el entregable, sin otros datos personales. Prueba: `security`.

### Grupo D. Cuota laboral del 4%

- **REQ-08-030** WHERE la persona consienta, THE SYSTEM SHALL emitir una constancia verificable de que cumple el criterio de la cuota del 4% sin revelar el tipo ni el grado de discapacidad ni datos de salud, con la mínima información necesaria `[verificar con abogado qué documento acredita la condición y qué se puede revelar]`. Prueba: `security`.
- **REQ-08-031** THE SYSTEM SHALL permitir a la empresa descargar un reporte de las personas y trabajos que respaldan su cumplimiento de la cuota, con datos mínimos y solo de personas que consintieron. Prueba: `e2e`.
- **REQ-08-032** THE SYSTEM SHALL permitir a la persona retirar su consentimiento para la constancia y que las constancias futuras dejen de emitirse. Prueba: `integration`.
- **REQ-08-033** THE SYSTEM SHALL NOT presentar la plataforma como una garantía de cumplimiento legal de la cuota; el cumplimiento depende de la relación contractual `[verificar con abogado]`. Prueba: `audit` (textos).

### Grupo E. Cobros y facturación

- **REQ-08-040** THE SYSTEM SHALL cobrar a la empresa por el trabajo y pagar a la persona, con una retención en depósito hasta que la empresa acepte el entregable o venza el periodo de revisión acordado `[verificar con abogado y con el proveedor de pagos]`. Prueba: `integration`.
- **REQ-08-041** THE SYSTEM SHALL integrarse con un proveedor de pagos que opere en Ecuador y NOT almacenar datos de tarjetas ni de cuentas bancarias propios `[verificar proveedor]`. Prueba: `audit`.
- **REQ-08-042** THE SYSTEM SHALL emitir la factura o el comprobante exigidos por la normativa tributaria ecuatoriana `[verificar con contador]`. Prueba: `integration`.
- **REQ-08-043** THE SYSTEM SHALL mostrar a la persona sus ingresos como un registro que solo suma, vinculado a sus logros, y permitirle exportarlo. Prueba: `e2e`.
- **REQ-08-044** THE SYSTEM SHALL tratar el cobro y el pago como acciones `external_effect` y cualquier retiro de dinero de la persona SHALL requerir su aprobación explícita (V-01). Prueba: `security`.
- **REQ-08-045** THE SYSTEM SHALL mostrar el estado de cada pago (pendiente, en depósito, pagado, en disputa) con texto y NOT depender solo del color. Prueba: `a11y`.

### Grupo F. Protección de la persona y disputas

- **REQ-08-050** THE SYSTEM SHALL ofrecer un proceso de disputa para entregables rechazados o pagos retenidos, con un plazo de respuesta y un contacto humano. Prueba: `e2e`.
- **REQ-08-051** THE SYSTEM SHALL NOT permitir calificaciones públicas de empresas hacia personas que incluyan datos personales o de salud. Prueba: `unit`.
- **REQ-08-052** THE SYSTEM SHALL NOT mostrar al operador el contenido de los entregables ni de las disputas, salvo que la persona los comparta con él en una disputa abierta por ella (V-11). Prueba: `security`.
- **REQ-08-053** THE SYSTEM SHALL permitir a la persona pausar su disponibilidad para nuevos trabajos en cualquier momento sin explicación. Prueba: `e2e`.

## 3. Requisitos no funcionales

- **REQ-08-060** THE SYSTEM SHALL cumplir WCAG 2.2 AA, y como objetivo AAA 44×44 px CSS y ausencia de límites de tiempo, en todas las pantallas que ve la persona. Las pantallas de la empresa cumplen AA. Prueba: `a11y`.
- **REQ-08-061** THE SYSTEM SHALL cifrar los datos de trabajos, entregables y pagos en reposo y en tránsito. Prueba: `security`.
- **REQ-08-062** THE SYSTEM SHALL poder auditar cada movimiento de dinero y cada entrega mediante la bitácora, sin contenido. Prueba: `integration`.

## 4. Preguntas abiertas de esta spec (fase 2)

| ID | Pregunta |
| --- | --- |
| PA-22 | ¿La relación persona-empresa es laboral, de servicios profesionales o por plataforma? Define impuestos, seguridad social y la cuota del 4% `[verificar con abogado]`. |
| PA-23 | ¿Qué proveedor de pagos opera en Ecuador con depósito en garantía? |
| PA-24 | ¿Qué documento acredita la condición de discapacidad y cómo se verifica sin exponer datos de salud? |
