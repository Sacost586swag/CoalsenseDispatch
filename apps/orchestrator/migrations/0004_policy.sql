-- Bitácora v2: vincula la acción y la regla sin reescribir eventos v1.
lock table coalsense.audit_event in access exclusive mode;
set role admin;

create function coalsense.audit_refs_valid_v2(refs jsonb) returns boolean
language sql immutable parallel safe as $$
    select coalsense.audit_refs_valid(refs - array['action_id', 'rule_id'])
        and (not refs ? 'action_id' or (
            jsonb_typeof(refs->'action_id') = 'string' and length(refs->>'action_id') = 36
            and (refs->>'action_id') collate "C" ~
                '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        ))
        and (not refs ? 'rule_id' or (
            jsonb_typeof(refs->'rule_id') = 'string'
            and (refs->>'rule_id') collate "C" ~ '^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$'
            and (refs->>'rule_id') !~ '[[:space:]]'
        ))
$$;

create function coalsense.audit_hash_v2(
    event_id uuid, owner_id uuid, sequence_number bigint, event_at timestamptz,
    event_kind text, event_result text, refs jsonb, previous_hash text
) returns text language sql immutable parallel safe as $$
    select encode(sha256(convert_to(concat_ws(E'\n',
        'coalsense.audit.v2', event_id::text, owner_id::text, sequence_number::text,
        to_char(event_at at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
        event_kind, event_result,
        coalesce(refs->>'task_id', '-'), coalesce(refs->>'plan_id', '-'),
        coalesce(refs->>'step_id', '-'), coalesce(refs->>'pending_action_id', '-'),
        coalesce(refs->>'actor_id', '-'), coalesce(refs->>'device_id', '-'),
        coalesce(refs->>'session_id', '-'), coalesce(refs->>'tool_name', '-'),
        coalesce(refs->>'effect_class', '-'), coalesce(refs->>'actor_origin', '-'),
        coalesce(refs->>'policy_version', '-'), coalesce(refs->>'action_id', '-'),
        coalesce(refs->>'rule_id', '-'), previous_hash
    ) || E'\n', 'UTF8')), 'hex')
$$;
revoke all on function coalsense.audit_refs_valid_v2(jsonb),
    coalsense.audit_hash_v2(uuid, uuid, bigint, timestamptz, text, text, jsonb, text) from public;
grant execute on function coalsense.audit_refs_valid_v2(jsonb),
    coalsense.audit_hash_v2(uuid, uuid, bigint, timestamptz, text, text, jsonb, text) to app_rw;

alter table coalsense.audit_event drop constraint audit_event_schema_version_check;
alter table coalsense.audit_event drop constraint audit_event_refs_check;
alter table coalsense.audit_event drop constraint audit_hash_matches;
alter table coalsense.audit_event add constraint audit_event_schema_version_check
    check (schema_version in (1, 2));
alter table coalsense.audit_event add constraint audit_event_refs_check
    check (case schema_version when 1 then coalsense.audit_refs_valid(refs)
                               else coalsense.audit_refs_valid_v2(refs) end);
alter table coalsense.audit_event add constraint audit_hash_matches check (
    hash = case schema_version
        when 1 then coalsense.audit_hash(id, person_id, seq, at, kind, result, refs, prev_hash)
        else coalsense.audit_hash_v2(id, person_id, seq, at, kind, result, refs, prev_hash)
    end
);
-- DEFAULT 1 se conserva para escritores históricos. Los nuevos escriben la versión explícita.

create function coalsense.policy_config_valid(doc jsonb, revision bigint) returns boolean
language sql immutable parallel safe as $$
    select coalesce(
        jsonb_typeof(doc) = 'object' and doc ?& array['version','rules']
        and doc - array['version','rules'] = '{}'::jsonb
        and jsonb_typeof(doc->'version') = 'number' and doc->>'version' = revision::text
        and jsonb_typeof(doc->'rules') = 'object'
        and (doc->'rules') - array['read','internal_write','external_effect'] = '{}'::jsonb
        and not exists (
            select 1 from unnest(array['read','internal_write','external_effect']) e(effect)
            where not coalesce(
                jsonb_typeof(doc->'rules'->effect) = 'object'
                and (doc->'rules'->effect) ?& array['id','decision']
                and (doc->'rules'->effect) - array['id','decision'] = '{}'::jsonb
                and jsonb_typeof(doc->'rules'->effect->'id') = 'string'
                and (doc->'rules'->effect->>'id') collate "C" ~
                    '^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$'
                and (doc->'rules'->effect->>'id') !~ '[[:space:]]'
                and (doc->'rules'->effect->>'id') !~ '^(guard|policy)\.'
                and doc->'rules'->effect->>'decision' in ('allow','require_approval','deny')
                and (effect <> 'external_effect'
                     or doc->'rules'->effect->>'decision' <> 'allow'), false
            )
        )
        and (select count(distinct doc->'rules'->effect->>'id')
             from unnest(array['read','internal_write','external_effect']) e(effect)) = 3,
        false
    )
$$;

create table coalsense.policy_version (
    person_id uuid not null,
    version bigint not null check (version between 1 and 9007199254740991),
    canonical text not null,
    digest text not null check (length(digest) = 64),
    created_at timestamptz not null default now(),
    primary key (person_id, version),
    check (coalsense.policy_config_valid(canonical::jsonb, version)),
    check (digest = encode(sha256(convert_to(canonical, 'UTF8')), 'hex'))
);
create table coalsense.policy_active (
    person_id uuid primary key,
    version bigint not null,
    foreign key (person_id, version) references coalsense.policy_version(person_id, version)
);

alter table coalsense.policy_version enable row level security;
alter table coalsense.policy_version force row level security;
alter table coalsense.policy_active enable row level security;
alter table coalsense.policy_active force row level security;
create policy policy_version_person on coalsense.policy_version to app_rw, admin
    using (person_id = nullif(current_setting('coalsense.person_id', true), '')::uuid)
    with check (person_id = nullif(current_setting('coalsense.person_id', true), '')::uuid);
create policy policy_active_person on coalsense.policy_active to app_rw, admin
    using (person_id = nullif(current_setting('coalsense.person_id', true), '')::uuid)
    with check (person_id = nullif(current_setting('coalsense.person_id', true), '')::uuid);

create function coalsense.policy_activation_guard() returns trigger language plpgsql as $$
begin
    if tg_op = 'UPDATE' and (new.person_id <> old.person_id or new.version <= old.version) then
        raise exception 'Invalid policy activation';
    end if;
    return new;
end $$;
create trigger policy_activation_monotonic before update on coalsense.policy_active
    for each row execute function coalsense.policy_activation_guard();

revoke all on coalsense.policy_version, coalsense.policy_active from public;
grant select, insert on coalsense.policy_version, coalsense.policy_active to app_rw;
grant update(version) on coalsense.policy_active to app_rw;
revoke all on function coalsense.policy_config_valid(jsonb,bigint),
    coalsense.policy_activation_guard() from public;
grant execute on function coalsense.policy_config_valid(jsonb,bigint),
    coalsense.policy_activation_guard() to app_rw;
reset role;
