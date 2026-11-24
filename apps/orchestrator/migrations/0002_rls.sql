-- T-02-002: base de persistencia por persona. Ejecutar como migrador administrativo.
-- Los roles son grupos sin LOGIN; las credenciales de ejecución se provisionan aparte.
-- No se cambian las tablas históricas de autenticación: su repositorio aún es en memoria.
do $$
begin
    if not exists (select 1 from pg_roles where rolname = 'admin') then
        create role admin nologin nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'app_rw') then
        create role app_rw nologin nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'app_ro_audit') then
        create role app_ro_audit nologin nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
    end if;
    if exists (
        select 1 from pg_roles where rolname in ('admin', 'app_rw', 'app_ro_audit')
        and (rolcanlogin or rolsuper or rolbypassrls or rolcreatedb or rolcreaterole or rolreplication)
    ) then
        raise exception 'Unsafe persistence role';
    end if;
end $$;

create schema coalsense authorization admin;
revoke all on schema coalsense from public;
grant usage on schema coalsense to app_rw, app_ro_audit;

set role admin;

create table coalsense.task (
    id uuid primary key,
    person_id uuid not null,
    kind text not null check (kind in ('email', 'document', 'social')),
    state text not null default 'draft' check (state in ('draft', 'paused')),
    autonomy_level text not null default 'N0' check (autonomy_level = 'N0'),
    revision bigint not null default 1 check (revision > 0),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (person_id, id)
);
create index task_person_order_idx on coalsense.task (person_id, id);

-- Registro transaccional de escrituras de persistencia. La bitácora encadenada
-- de T-02-003 es una pieza posterior, no se acredita mediante esta tabla.
create table coalsense.persistence_event (
    id uuid primary key,
    person_id uuid not null,
    operation text not null check (operation in ('task.create', 'task.pause')),
    resource_id uuid not null,
    at timestamptz not null default now(),
    foreign key (person_id, resource_id) references coalsense.task(person_id, id)
);
create index persistence_event_person_idx on coalsense.persistence_event (person_id, id);

alter table coalsense.task enable row level security;
alter table coalsense.task force row level security;
alter table coalsense.persistence_event enable row level security;
alter table coalsense.persistence_event force row level security;

create policy task_person on coalsense.task to app_rw, admin
    using (person_id = nullif(current_setting('coalsense.person_id', true), '')::uuid)
    with check (person_id = nullif(current_setting('coalsense.person_id', true), '')::uuid);
create policy persistence_event_person on coalsense.persistence_event to app_rw, admin
    using (person_id = nullif(current_setting('coalsense.person_id', true), '')::uuid)
    with check (person_id = nullif(current_setting('coalsense.person_id', true), '')::uuid);

revoke all on coalsense.task, coalsense.persistence_event from public;
grant select, insert on coalsense.task to app_rw;
grant update (state, revision, updated_at) on coalsense.task to app_rw;
grant select, insert on coalsense.persistence_event to app_rw;
-- Ningún UPDATE/DELETE/TRUNCATE sobre el registro. app_ro_audit no recibe acceso
-- a tareas ni a eventos individuales; las métricas agregadas se implementan aparte.

reset role;
