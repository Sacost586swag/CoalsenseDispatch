-- T-00-011: sesiones por dispositivo. Esquema para PostgreSQL (H2, P-03/T-02-002).
-- Aún no se ejecuta: hoy la persistencia es la implementación en memoria de AuthRepository.
-- La sesión NO tiene vencimiento: ni por tiempo ni por inactividad (REQ-00-022). Solo se cierra
-- al revocarla (revoked_at) o si la rotación falla; el dispositivo conserva su sesión mientras
-- haya trabajo pendiente, sea cual sea el tiempo que pase sin usarla.
-- credential_hash / previous_hash: HMAC-SHA256 de la credencial vigente y de la anterior (un
-- único uso de gracia tras rotar); jamás la credencial. rotated_at: última emisión.
-- scopes: alcances del rol al emitir; en cada pedido rigen los que el rol vigente aún permite.
-- El rol `operator` nunca recibe alcances de contenido (V-11, P-00-4).

create table session (
    id              uuid primary key,
    device_id       uuid not null unique references device (id),
    scopes          text[] not null,
    credential_hash text not null unique,
    previous_hash   text unique,
    rotated_at      timestamptz not null,
    revoked_at      timestamptz
);
