-- T-02-003. Bloquear escrituras antiguas durante la conversión; todo corre en una transacción.
lock table coalsense.task, coalsense.persistence_event in access exclusive mode;
set role admin;

create function coalsense.audit_refs_valid(refs jsonb) returns boolean
language sql immutable parallel safe as $$
    select jsonb_typeof(refs) = 'object' and not exists (
        select 1 from jsonb_each(refs) as item(key, value) where not (
            case
                when key in ('task_id', 'plan_id', 'step_id', 'pending_action_id',
                             'actor_id', 'device_id', 'session_id') then
                    jsonb_typeof(value) = 'string' and length(value #>> '{}') = 36
                    and (value #>> '{}') ~
                        '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                when key = 'tool_name' then
                    jsonb_typeof(value) = 'string'
                    and (value #>> '{}') ~ '^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$'
                    and (value #>> '{}') !~ '[[:space:]]'
                when key = 'effect_class' then
                    value in ('"read"'::jsonb, '"internal_write"'::jsonb, '"external_effect"'::jsonb)
                when key = 'actor_origin' then
                    value in ('"person"'::jsonb, '"caregiver"'::jsonb, '"system"'::jsonb)
                when key = 'policy_version' then
                    jsonb_typeof(value) = 'number' and (value #>> '{}') ~ '^[1-9][0-9]*$'
                else false
            end
        )
    )
$$;

-- Framing v1: orden y delimitadores compartidos con audit/chain.py. Todos los campos
-- están cerrados a valores ASCII sin saltos de línea; '-' representa una referencia ausente.
create function coalsense.audit_hash(
    event_id uuid, owner_id uuid, sequence_number bigint, event_at timestamptz,
    event_kind text, event_result text, refs jsonb, previous_hash text
) returns text language sql immutable parallel safe as $$
    select encode(sha256(convert_to(concat_ws(E'\n',
        'coalsense.audit.v1', event_id::text, owner_id::text, sequence_number::text,
        to_char(event_at at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
        event_kind, event_result,
        coalesce(refs->>'task_id', '-'), coalesce(refs->>'plan_id', '-'),
        coalesce(refs->>'step_id', '-'), coalesce(refs->>'pending_action_id', '-'),
        coalesce(refs->>'actor_id', '-'), coalesce(refs->>'device_id', '-'),
        coalesce(refs->>'session_id', '-'), coalesce(refs->>'tool_name', '-'),
        coalesce(refs->>'effect_class', '-'), coalesce(refs->>'actor_origin', '-'),
        coalesce(refs->>'policy_version', '-'), previous_hash
    ) || E'\n', 'UTF8')), 'hex')
$$;

create function coalsense.audit_lock(owner_id uuid) returns void
language sql volatile as $$
    select pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended('coalsense.audit:' || owner_id::text, 0)
    )
$$;

create table coalsense.audit_event (
    id uuid primary key,
    person_id uuid not null,
    seq bigint not null check (seq > 0),
    schema_version integer not null default 1 check (schema_version = 1),
    at timestamptz not null,
    kind text not null check (kind in (
        'task.created', 'task.paused', 'plan', 'step', 'tool', 'policy', 'approval',
        'control.stop', 'control.undo', 'derivation', 'auth'
    )),
    result text not null check (result in ('ok', 'pending', 'failed', 'denied', 'cancelled')),
    refs jsonb not null check (coalsense.audit_refs_valid(refs)),
    task_id uuid generated always as ((refs->>'task_id')::uuid) stored,
    prev_hash text not null check (length(prev_hash) = 64 and prev_hash ~ '^[0-9a-f]{64}$'),
    hash text not null check (length(hash) = 64 and hash ~ '^[0-9a-f]{64}$'),
    unique (person_id, seq),
    foreign key (person_id, task_id) references coalsense.task(person_id, id),
    constraint audit_hash_matches
        check (hash = coalsense.audit_hash(id, person_id, seq, at, kind, result, refs, prev_hash))
);

alter table coalsense.audit_event enable row level security;
alter table coalsense.audit_event force row level security;
create policy audit_person on coalsense.audit_event to app_rw, admin
    using (person_id = nullif(current_setting('coalsense.person_id', true), '')::uuid)
    with check (person_id = nullif(current_setting('coalsense.person_id', true), '')::uuid);

create function coalsense.audit_guard() returns trigger language plpgsql as $$
declare
    previous_sequence bigint;
    previous_hash text;
begin
    perform coalsense.audit_lock(new.person_id);
    select seq, hash into previous_sequence, previous_hash
        from coalsense.audit_event where person_id = new.person_id order by seq desc limit 1;
    if new.seq <> coalesce(previous_sequence, 0) + 1
       or new.prev_hash <> coalesce(previous_hash, repeat('0', 64)) then
        raise exception 'Invalid audit chain';
    end if;
    return new;
end $$;
create trigger audit_append_guard before insert on coalsense.audit_event
    for each row execute function coalsense.audit_guard();

revoke all on coalsense.audit_event from public;
grant select, insert on coalsense.audit_event to app_rw;
revoke all on function coalsense.audit_refs_valid(jsonb), coalsense.audit_lock(uuid),
    coalsense.audit_hash(uuid, uuid, bigint, timestamptz, text, text, jsonb, text),
    coalsense.audit_guard() from public;
grant execute on function coalsense.audit_refs_valid(jsonb), coalsense.audit_lock(uuid),
    coalsense.audit_hash(uuid, uuid, bigint, timestamptz, text, text, jsonb, text),
    coalsense.audit_guard() to app_rw;

-- El bloqueo exclusivo evita que una aplicación antigua escriba durante la conversión.
-- La desactivación temporal afecta solo a la tabla histórica, dentro de esta transacción.
alter table coalsense.persistence_event disable row level security;
do $$
declare
    legacy record;
    current_owner uuid;
    next_sequence bigint := 0;
    previous_hash text := repeat('0', 64);
    event_kind text;
    event_refs jsonb;
    event_hash text;
begin
    for legacy in select * from coalsense.persistence_event order by person_id, at, id loop
        if current_owner is distinct from legacy.person_id then
            current_owner := legacy.person_id;
            next_sequence := 0;
            previous_hash := repeat('0', 64);
            perform set_config('coalsense.person_id', current_owner::text, true);
        end if;
        next_sequence := next_sequence + 1;
        event_kind := case legacy.operation when 'task.create' then 'task.created' else 'task.paused' end;
        event_refs := jsonb_build_object('task_id', legacy.resource_id::text,
            'actor_id', current_owner::text, 'actor_origin', 'person');
        event_hash := coalsense.audit_hash(legacy.id, current_owner, next_sequence,
            legacy.at, event_kind, 'ok', event_refs, previous_hash);
        insert into coalsense.audit_event (id, person_id, seq, at, kind, result, refs, prev_hash, hash)
            values (legacy.id, current_owner, next_sequence, legacy.at,
                    event_kind, 'ok', event_refs, previous_hash, event_hash);
        previous_hash := event_hash;
    end loop;
    perform set_config('coalsense.person_id', '', true);
end $$;
alter table coalsense.persistence_event enable row level security;
alter table coalsense.persistence_event force row level security;
revoke insert on coalsense.persistence_event from app_rw;
reset role;
