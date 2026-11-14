# Requisitos: 07 Privacidad y datos

**Estado:** completo. Notación y tipos de prueba: `01-capa-de-entrada/requirements.md` sección 0.
**Cubre:** LOPDP de Ecuador, cifrado, claves, exportación, borrado, retención y límites de acceso.
**Vertical aplicable:** V-06, V-09, V-11. Propiedades: SP-3, SP-6.
**Nota legal:** todo lo marcado `[verificar con abogado]` es una interpretación de la LOPDP que no está confirmada. Esta spec no es asesoría legal.

## 1. Alcance

Dentro: inventario y clasificación de datos, cifrado en reposo y en tránsito, gestión de claves por persona, minimización hacia terceros, derechos de la persona (acceso, exportación, rectificación, borrado, oposición), retención, acceso del operador, incidentes.
Fuera: captura de consentimientos (05), delegaciones (06).

## 2. Requisitos funcionales

### Grupo A. Inventario y clasificación

- **REQ-07-001** THE SYSTEM SHALL mantener un inventario de datos versionado en el repositorio, con cada dato personal que el sistema trata: categoría, finalidad, dónde vive, quién lo ve, cuánto se conserva y si es categoría especial (discapacidad y salud). Prueba: `audit`.
- **REQ-07-002** THE SYSTEM SHALL fallar la CI si un campo nuevo de la base de datos o del esquema de intenciones no está en el inventario. Prueba: `audit`.
- **REQ-07-003** THE SYSTEM SHALL clasificar como categoría especial el perfil de capacidad, la condición declarada, el uso de modalidades, los eventos de crisis, los consentimientos y el contenido de las tareas. Prueba: `unit`.
- **REQ-07-004** THE SYSTEM SHALL NOT guardar ningún diagnóstico salvo que la persona lo declare para ajustar su perfil (V-09). Prueba: `unit`.
- **REQ-07-005** THE SYSTEM SHALL mantener un registro de las actividades de tratamiento a partir del inventario `[verificar con abogado si la LOPDP lo exige]`. Prueba: `audit`.

### Grupo B. Cifrado y claves

- **REQ-07-010** THE SYSTEM SHALL cifrar con TLS todo el tráfico entre clientes y servicios y entre servicios. Prueba: `security`.
- **REQ-07-011** THE SYSTEM SHALL cifrar en reposo la base de datos, las copias de seguridad y el almacenamiento de archivos. Prueba: `security`.
- **REQ-07-012** THE SYSTEM SHALL cifrar el contenido de la persona (tareas, propuestas, memoria, credenciales de herramientas) a nivel de aplicación con una clave de datos por persona, protegida por una clave maestra del servicio de claves (PA-20). Prueba: `security`.
- **REQ-07-013** THE SYSTEM SHALL cifrar en reposo los datos locales del companion (perfil, calibraciones, bitácora local) con una clave protegida por el almacén de credenciales del sistema operativo [SUPUESTO]. Prueba: `security`.
- **REQ-07-014** THE SYSTEM SHALL registrar cada uso de claves maestras y de claves de persona fuera del flujo normal de la aplicación y alertar al operador. Prueba: `integration`.
- **REQ-07-015** THE SYSTEM SHALL permitir rotar las claves sin pérdida de datos. Prueba: `integration`.
- **REQ-07-016** THE SYSTEM SHALL NOT guardar secretos, claves ni contenido de personas en archivos de configuración ni en variables de entorno de los agentes. Prueba: `audit`.

### Grupo C. Minimización y flujo a terceros

- **REQ-07-020** THE SYSTEM SHALL pasar todo envío de datos a un tercero (proveedor de modelo, voz en la nube, correo, servidores MCP) por una capa de salida que verifique el consentimiento vigente y aplique la minimización de campos. Prueba: `security`.
- **REQ-07-021** THE SYSTEM SHALL NOT enviar a ningún tercero el perfil de capacidad, la condición declarada, los eventos de crisis ni datos de calibración (SP-6). Prueba: `security`.
- **REQ-07-022** THE SYSTEM SHALL NOT enviar a ningún tercero cuadros de video, audio, landmarks ni blendshapes (SP-3). Prueba: `security`.
- **REQ-07-023** THE SYSTEM SHALL mantener un registro de encargados y terceros (proveedores) con su finalidad, país y categorías de datos que reciben, visible para la persona. Prueba: `unit`.
- **REQ-07-024** THE SYSTEM SHALL marcar en el registro de terceros cuáles reciben datos fuera de Ecuador para evaluar la transferencia internacional `[verificar con abogado]`. Prueba: `unit`.
- **REQ-07-025** THE SYSTEM SHALL NOT usar los datos de las personas para entrenar modelos, y SHALL exigir a los proveedores de modelos configuraciones sin retención ni entrenamiento cuando existan `[verificar contrato]`. Prueba: `audit`.

### Grupo D. Derechos de la persona

**HU-07-D.** Como persona, quiero ver, llevarme y borrar mis datos cuando yo lo pida, para saber que son míos.

- **REQ-07-030** WHEN la persona pide acceder a sus datos, THE SYSTEM SHALL mostrar en lenguaje llano qué datos tiene, para qué y con quién se comparten. Prueba: `e2e`.
- **REQ-07-031** WHEN la persona pide exportar sus datos, THE SYSTEM SHALL entregar un archivo completo en formatos abiertos (JSON y los entregables en su formato) que incluya tareas, propuestas, logros, memoria, bitácora, consentimientos, perfiles y delegaciones. Prueba: `e2e`.
- **REQ-07-032** WHEN la persona corrige un dato, THE SYSTEM SHALL actualizarlo en todas las copias vivas. Prueba: `integration`.
- **REQ-07-033** WHEN la persona pide borrar sus datos, THE SYSTEM SHALL borrarlos de la base de datos, de la memoria vectorial, de la caché, del almacenamiento de archivos y de las credenciales de herramientas, destruir su clave de datos (borrado criptográfico) y revocar los accesos de cuidadores/as y de dispositivos. Prueba: `e2e`.
- **REQ-07-034** WHEN termina un borrado, THE SYSTEM SHALL entregar a la persona una constancia con la fecha y qué se borró, sin conservar el contenido. Prueba: `e2e`.
- **REQ-07-035** THE SYSTEM SHALL cumplir los borrados también en las copias de seguridad, mediante el borrado criptográfico, a más tardar al vencer su retención [SUPUESTO: plazo máximo a definir]. Prueba: `integration`.
- **REQ-07-036** WHEN la persona pide dejar de usar sus datos para una finalidad (oposición o suspensión), THE SYSTEM SHALL aplicarlo de inmediato mediante la revocación del consentimiento correspondiente `[verificar con abogado los derechos exactos de la LOPDP]`. Prueba: `integration`.
- **REQ-07-037** THE SYSTEM SHALL permitir ejercer estos derechos con cualquier modalidad y sin plazos de interacción. Prueba: `a11y`.
- **REQ-07-038** THE SYSTEM SHALL NOT permitir que un cuidador/a ejerza estos derechos en nombre de la persona sin una delegación específica para ello `[verificar con abogado si hay representante legal]`. Prueba: `security`.

### Grupo E. Retención

- **REQ-07-045** THE SYSTEM SHALL tener una política de retención por categoría de datos y permitir a la persona ajustarla dentro de límites. Prueba: `unit`.
- **REQ-07-046** THE SYSTEM SHALL NOT almacenar nunca audio, video, landmarks, prompts ni respuestas de modelos más allá de lo que la persona vea en sus propuestas (retención cero). Prueba: `security`.
- **REQ-07-047** THE SYSTEM SHALL conservar por defecto el contenido de las tareas hasta que la persona lo borre [SUPUESTO] y ofrecer borrar en cualquier momento tareas individuales. Prueba: `e2e`.
- **REQ-07-048** THE SYSTEM SHALL aplicar una retención limitada a los registros técnicos (sin contenido) y a los datos operativos [SUPUESTO: valores a definir]. Prueba: `unit`.

### Grupo F. Acceso del operador

- **REQ-07-055** THE SYSTEM SHALL NOT ofrecer al operador ninguna pantalla, API ni rol de base de datos que permita leer contenido de personas (V-11). Prueba: `security`.
- **REQ-07-056** THE SYSTEM SHALL dar al operador solo métricas agregadas y registros técnicos sin contenido, con campos de contenido eliminados. Prueba: `security`.
- **REQ-07-057** THE SYSTEM SHALL NOT dar a un operador un acceso de emergencia a contenido; si hace falta soporte, la persona exporta y comparte lo necesario por su decisión. Prueba: `security`.
- **REQ-07-058** THE SYSTEM SHALL registrar y alertar todo acceso a la base de datos con un rol de administración. Prueba: `integration`.

### Grupo G. Incidentes

- **REQ-07-065** THE SYSTEM SHALL tener un procedimiento documentado de incidentes de seguridad con detección, contención, aviso a las personas afectadas y a la autoridad competente en los plazos de la ley `[verificar con abogado los plazos]`. Prueba: `manual`.
- **REQ-07-066** THE SYSTEM SHALL poder identificar, a partir de la bitácora y del inventario, qué personas y qué datos afectó un incidente. Prueba: `integration`.

## 3. Requisitos no funcionales

- **REQ-07-070** THE SYSTEM SHALL completar una exportación de datos de una persona típica en un máximo de 5 minutos [SUPUESTO] y notificarlo cuando termine, sin que la persona tenga que esperar en pantalla. Prueba: `perf`.
- **REQ-07-071** THE SYSTEM SHALL completar un borrado en un máximo de 24 horas, salvo copias de seguridad (REQ-07-035) [SUPUESTO]. Prueba: `perf`.
- **REQ-07-072** THE SYSTEM SHALL cumplir WCAG 2.2 AA y, como objetivo AAA, 44×44 px CSS y ausencia de límites de tiempo en las pantallas de privacidad. Prueba: `a11y`.
- **REQ-07-073** THE SYSTEM SHALL evitar que un fallo del borrado deje datos a medio borrar: la operación es reanudable y verificable. Prueba: `integration`.

## 4. Dependencias

| Spec | Relación |
| --- | --- |
| 00 | Registros sin contenido, roles |
| 01 | Datos locales del companion |
| 02 | Capa de salida, memoria, bitácora |
| 05 | Consentimientos |
| 06 | Delegaciones |
| 09 | Servicio de claves, copias de seguridad, entornos |

## 5. Preguntas abiertas

PA-18 (hosting y región de los datos), PA-20 (gestión de claves). Revisión legal de LOPDP antes de ofrecerlo a personas reales (SF-06).
