# Requisitos: 09 Despliegue

**Estado:** completo. Notación y tipos de prueba: `01-capa-de-entrada/requirements.md` sección 0.
**Cubre:** companion de escritorio, web, backend, entornos de prueba y producción, CI/CD, observabilidad y copias de seguridad.
**Vertical aplicable:** V-04, V-06, V-09, V-10, V-11. Propiedad: SP-3.

## 1. Alcance

Dentro: empaquetado e instalación del companion en Windows, publicación de la web (PWA) y del backend, entornos, pipelines de entrega, observabilidad sin contenido, copias de seguridad, pruebas de entorno.
Fuera: hosting definitivo y región (PA-18, a definir con asesoría legal), mercado y pagos (08).

## 2. Requisitos funcionales

### Grupo A. Companion de escritorio

- **REQ-09-001** THE SYSTEM SHALL empaquetar el companion para Windows como un instalador que no requiera tener Python ni uv instalados [SUPUESTO: herramienta de empaquetado a decidir en el diseño]. Prueba: `integration`.
- **REQ-09-002** THE SYSTEM SHALL firmar digitalmente los instaladores y las actualizaciones, y el companion SHALL verificar la firma antes de instalar. Prueba: `security`.
- **REQ-09-003** THE SYSTEM SHALL incluir con el instalador, o descargar al primer arranque con verificación de integridad (hash), los modelos de visión y de voz necesarios, de modo que después funcione sin conexión (REQ-01-126). Prueba: `integration`.
- **REQ-09-004** THE SYSTEM SHALL solicitar los permisos de cámara y micrófono con una explicación clara y un paso operable con voz o ayuda del cuidador/a, y mostrar «modalidad no detectada» con la causa si se deniegan (REQ-01-099). Prueba: `e2e`.
- **REQ-09-005** THE SYSTEM SHALL actualizar el companion solo con la aprobación de la persona, nunca durante una tarea en ejecución ni sin poder posponerla sin límite, y conservar la versión anterior para volver atrás. Prueba: `e2e`.
- **REQ-09-006** THE SYSTEM SHALL conservar el perfil de capacidad, las calibraciones y los comandos propios al actualizar y al reinstalar. Prueba: `integration`.
- **REQ-09-007** WHEN la persona desinstala el companion, THE SYSTEM SHALL ofrecer borrar o conservar los datos locales, y NOT dejar procesos ni accesos directos activos de cámara o micrófono. Prueba: `integration`.
- **REQ-09-008** THE SYSTEM SHALL iniciar el companion con el sistema operativo solo si la persona lo eligió, y mostrar el indicador de cámara y micrófono desde el primer instante (REQ-01-093). Prueba: `e2e`.
- **REQ-09-009** THE SYSTEM SHALL aplicar la lista permitida de egreso de red del companion en el artefacto empaquetado y fallar el build si el empaquetado añade destinos de red no previstos (SP-3). Prueba: `security`.

### Grupo B. Web (PWA)

- **REQ-09-010** THE SYSTEM SHALL publicar `apps/web` como PWA instalable, con una política de seguridad de contenido estricta que restrinja los destinos de conexión a los orígenes propios. Prueba: `security`.
- **REQ-09-011** THE SYSTEM SHALL servir los archivos de los modelos de MediaPipe desde el propio origen de la web, sin redes de entrega de terceros, para el modo web de visión (REQ-01-055). Prueba: `security`.
- **REQ-09-012** THE SYSTEM SHALL permitir que la PWA abra sin conexión con las pantallas ya visitadas y con los estados *sin conexión* de AX-11. Prueba: `e2e`.
- **REQ-09-013** THE SYSTEM SHALL pedir el permiso de cámara en el navegador solo cuando la persona activa el modo web de visión. Prueba: `e2e`.

### Grupo C. Backend

- **REQ-09-020** THE SYSTEM SHALL empaquetar el orquestador, el gateway, n8n (si procede, PA-09), PostgreSQL con pgvector y Redis como contenedores definidos en `infra/` y reproducibles localmente con docker-compose. Prueba: `integration`.
- **REQ-09-021** THE SYSTEM SHALL aplicar migraciones de base de datos versionadas y reversibles, y fallar el despliegue si una migración falla. Prueba: `integration`.
- **REQ-09-022** THE SYSTEM SHALL separar las credenciales de cada servicio y NOT dar credenciales de la base de datos de producción a los procesos de los agentes (V-08). Prueba: `security`.
- **REQ-09-023** THE SYSTEM SHALL exponer comprobaciones de salud de cada servicio y el estado de las dependencias (modelo, base de datos, gateway). Prueba: `integration`.
- **REQ-09-024** THE SYSTEM SHALL ejecutar los servidores MCP del catálogo curado en procesos o contenedores aislados con permisos mínimos (REQ-02-029). Prueba: `security`.

### Grupo D. Entornos

- **REQ-09-030** THE SYSTEM SHALL ofrecer tres entornos: desarrollo local, **prueba** y **producción**, con configuración, secretos y datos separados. Prueba: `audit`.
- **REQ-09-031** THE SYSTEM SHALL NOT usar datos reales de personas fuera de producción; el entorno de prueba usa datos sintéticos. Prueba: `audit`.
- **REQ-09-032** THE SYSTEM SHALL mantener el entorno de prueba lo más parecido posible a producción (mismas versiones de servicios y mismo empaquetado) y documentar las diferencias. Prueba: `audit`.
- **REQ-09-033** THE SYSTEM SHALL usar en prueba proveedores simulados o cuentas de prueba para modelos, correo, avisos y pagos, de modo que ninguna prueba contacte a una persona real. Prueba: `e2e`.
- **REQ-09-034** THE SYSTEM SHALL mostrar de forma inequívoca en la interfaz y en los mensajes cuando se está en el entorno de prueba. Prueba: `e2e`.

### Grupo E. CI/CD y publicaciones

- **REQ-09-040** THE SYSTEM SHALL construir y probar artefactos del companion, la web y el backend en CI desde el mismo commit, y publicarlos en el entorno de prueba de forma automática. Prueba: `integration`.
- **REQ-09-041** THE SYSTEM SHALL promover a producción solo artefactos que pasaron las pruebas del entorno de prueba, con una aprobación manual del operador. Prueba: `audit`.
- **REQ-09-042** THE SYSTEM SHALL permitir revertir una publicación a la versión anterior sin pérdida de datos. Prueba: `integration`.
- **REQ-09-043** THE SYSTEM SHALL gobernar las modalidades `[POST-MVP]` (mirada, switch) y las funciones de la fase 2 con indicadores de función desactivados por defecto en producción. Prueba: `unit`.
- **REQ-09-044** THE SYSTEM SHALL generar y publicar `THIRD_PARTY.md` y el inventario de licencias con cada versión. Prueba: `audit`.

### Grupo F. Observabilidad y copias de seguridad

- **REQ-09-050** THE SYSTEM SHALL recolectar métricas y registros sin contenido privado (REQ-00-010) y alertar al operador de errores y degradaciones. Prueba: `integration`.
- **REQ-09-051** THE SYSTEM SHALL hacer copias de seguridad cifradas de la base de datos y del almacenamiento de archivos con una frecuencia definida [SUPUESTO] y probar la restauración periódicamente. Prueba: `integration`.
- **REQ-09-052** THE SYSTEM SHALL alertar si falta el latido de un companion o si el servicio de claves no responde. Prueba: `integration`.
- **REQ-09-053** THE SYSTEM SHALL NOT incluir contenido de personas en las copias de seguridad sin cifrar con la clave de la persona (REQ-07-012). Prueba: `security`.

## 3. Requisitos no funcionales [SUPUESTO en las cifras]

- **REQ-09-060** THE SYSTEM SHALL arrancar el companion hasta tener operativa al menos una ruta de Alto en un máximo de 15 s en el hardware de referencia [SUPUESTO]. Prueba: `perf`.
- **REQ-09-061** THE SYSTEM SHALL tener una disponibilidad objetivo del backend definida y medida [SUPUESTO: valor a fijar tras el primer despliegue], y el companion SHALL seguir funcionando sin el backend (REQ-01-126). Prueba: `perf`.
- **REQ-09-062** THE SYSTEM SHALL permitir restaurar el servicio desde copia de seguridad en un tiempo objetivo definido [SUPUESTO]. Prueba: `integration`.
- **REQ-09-063** THE SYSTEM SHALL cumplir WCAG 2.2 AA en los asistentes de instalación, actualización y permisos, y como objetivo AAA 44×44 px CSS y ausencia de límites de tiempo. Prueba: `a11y`.

## 4. Preguntas abiertas

PA-18 (hosting y región), PA-20 (gestión de claves), PA-09 (n8n, Piper). El entorno de prueba en contenedores no bloquea ninguna construcción.
