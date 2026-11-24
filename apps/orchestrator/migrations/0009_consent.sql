-- Los campos de una decisión se cifran en la aplicación con la DEK de la persona.
set role admin;

create table coalsense.consent_record (
    person_id uuid not null,
    id uuid not null,
    ordinal bigint generated always as identity,
    envelope bytea not null check (octet_length(envelope) between 1 and 8192),
    primary key (person_id, id),
    unique (person_id, ordinal)
);

alter table coalsense.consent_record enable row level security;
alter table coalsense.consent_record force row level security;
create policy consent_record_person on coalsense.consent_record to app_rw, admin
    using (person_id = nullif(current_setting('coalsense.person_id', true), '')::uuid)
    with check (person_id = nullif(current_setting('coalsense.person_id', true), '')::uuid);

revoke all on coalsense.consent_record from public;
grant select on coalsense.consent_record to app_rw;
grant insert (person_id, id, envelope) on coalsense.consent_record to app_rw;
reset role;
