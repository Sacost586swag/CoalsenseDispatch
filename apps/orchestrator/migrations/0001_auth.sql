-- T-00-010: autenticación sin contraseña. Esquema para PostgreSQL (H2, P-03/T-02-002).
-- Aún no se ejecuta: hoy la persistencia es la implementación en memoria de AuthRepository.
-- [SUPUESTO] El correo nunca se guarda en claro (spec 07): se cifra y se busca por HMAC.
-- Ningún código tiene fecha de caducidad por tiempo (REQ-00-021, P-00-3): se invalida por uso,
-- por generar otro o por exceder los intentos.

create table account (
    id               uuid primary key,
    role             text not null check (role in ('person', 'caregiver', 'operator', 'company')),
    email_ciphertext bytea not null,
    email_lookup     text not null unique,
    -- Pista del correo (p***@e***). Dato derivado del correo: se borra con la cuenta (spec 07).
    email_hint       text not null,
    language         text not null default 'es',
    created_at       timestamptz not null
);

create table device (
    id         uuid primary key,
    account_id uuid not null references account (id),
    label      text not null,
    paired_at  timestamptz not null,
    revoked_at timestamptz
);

create index device_account_idx on device (account_id);

-- Códigos de correo (kind = 'email') y de emparejamiento (kind = 'device').
-- code_hash es el HMAC-SHA256 del código con la clave de configuración; nunca el código.
-- subject_lookup: HMAC del correo (email) o del identificador del companion (device).
-- account_id: en kind = 'email' se llena al usar el código; en kind = 'device' lo llena el
-- reclamo (claim) y el dispositivo solo se crea cuando el companion confirma.
-- claims: reclamos recibidos del código de emparejamiento (tope en la aplicación).
-- claim_id: identifica el reclamo pendiente; el companion debe enviarlo para confirmar o rechazar.
create table pairing_code (
    id             uuid primary key,
    kind           text not null check (kind in ('email', 'device')),
    subject_lookup text not null,
    account_id     uuid references account (id),
    code_hash      text not null,
    attempts       integer not null default 0,
    claims         integer not null default 0,
    claim_id       uuid,
    device_label   text,
    created_at     timestamptz not null,
    used_at        timestamptz,
    invalidated_at timestamptz
);

-- Un solo código activo por (kind, subject_lookup): generar otro invalida el anterior.
create unique index pairing_code_active_subject_idx
    on pairing_code (kind, subject_lookup)
    where used_at is null and invalidated_at is null;

create index pairing_code_active_hash_idx
    on pairing_code (kind, code_hash)
    where used_at is null and invalidated_at is null;
