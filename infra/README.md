# infra

docker-compose: PostgreSQL + pgvector, Redis y n8n (opcional).

`compose.test.yaml` permite probar la persistencia en PostgreSQL real con datos
sintéticos. La imagen de pgvector se fija por digest; la copia local examinada
incluye PostgreSQL 16.15. No es la configuración de despliegue de la plataforma.

Preparación, desde la raíz del repositorio:

```powershell
docker pull pgvector/pgvector@sha256:0dd3149a06e4579a0d70d8fef9945636cd514005e7237deb27f9b67886f8dc4f
pnpm --filter @coalsense/orchestrator test:integration
```

El comando de integración exige Docker operativo y la imagen disponible. Si faltan,
falla; no convierte la ausencia de infraestructura en una prueba aprobada. Crea un
proyecto Compose con nombre aleatorio propio, contraseña aleatoria efímera y puerto
automático enlazado a `127.0.0.1`. No toca bases de otros proyectos. Los datos viven
en `tmpfs`; al terminar se eliminan sus contenedores y recursos de prueba. No se
crean archivos de contraseñas en el repositorio ni volúmenes con contenido de personas.
Docker recibe la contraseña por el entorno del proceso y del contenedor de prueba;
su configuración interna puede contenerla hasta que se elimina el contenedor.

La fixture aplica el conjunto versionado de `apps/orchestrator/migrations/` en una
transacción, incluidas RLS y la bitácora encadenada, y provisiona un usuario de
ejecución sin privilegios administrativos. Desactiva el registro de sentencias y
parámetros del servidor de prueba. La misma etapa está configurada en CI de Linux,
que descarga primero la imagen fijada. Esto no acredita una ejecución remota de CI.

Las pruebas ordinarias omiten los casos PostgreSQL si no se activa la infraestructura.
Para ejecutar **todos** los paquetes con esos casos incluidos en PowerShell:

```powershell
$env:COALSENSE_TEST_POSTGRES = '1'
pnpm test
```

Turborepo incluye esa opción en la clave de caché; no reutiliza una ejecución con
pruebas omitidas para una ejecución que pide PostgreSQL. `test:integration` activa
la opción por sí mismo y nunca depende de recordarla manualmente.

Faltan los contenedores de aplicación, Redis, proxy TLS, almacenamiento cifrado
persistente, gestión de claves, copias y restauración del entorno desplegable. No
usar esta configuración efímera para conservar borradores ni para producción.

El comando administrativo de migraciones y sus límites están en
`docs/PERSISTENCIA.md`; usa credenciales separadas y consulta el plan por defecto.
Las pruebas de actualización crean y eliminan bases con nombres aleatorios dentro
de su contenedor propio. No modifican bases ajenas al proyecto de prueba.
