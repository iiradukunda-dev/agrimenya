-- Durable plan action status history and atomic status updates.
create table if not exists plan_action_history (
    id uuid primary key default gen_random_uuid(),
    plan_id uuid not null references plans(id) on delete cascade,
    step_number integer not null check (step_number > 0),
    previous_status text not null check (previous_status in ('planned', 'in_progress', 'completed', 'blocked')),
    new_status text not null check (new_status in ('planned', 'in_progress', 'completed', 'blocked')),
    change_note text not null default '',
    changed_by text not null default 'user',
    changed_at timestamptz not null default now()
);
create index if not exists plan_action_history_plan_changed_idx
    on plan_action_history(plan_id, changed_at desc, id);

alter table plan_action_history enable row level security;
comment on table plan_action_history is
    'Append-only history of plan action status changes; accessible through the trusted API service role.';

create or replace function update_plan_action_status(
    p_plan_id uuid,
    p_step_number integer,
    p_new_status text,
    p_change_note text default '',
    p_changed_by text default 'user'
) returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
    v_plan plans%rowtype;
    v_previous_status text;
    v_next_steps jsonb;
    v_note text := left(btrim(coalesce(p_change_note, '')), 1000);
begin
    if p_new_status not in ('planned', 'in_progress', 'completed', 'blocked') then
        raise exception 'Unsupported action status';
    end if;
    select * into v_plan from plans where id = p_plan_id for update;
    if not found then
        return null;
    end if;
    select coalesce(step->>'status', 'planned') into v_previous_status
      from jsonb_array_elements(coalesce(v_plan.roadmap_json, '[]'::jsonb)) as elements(step)
     where (step->>'step_number')::integer = p_step_number;
    if not found then
        raise exception 'Plan action was not found';
    end if;

    select jsonb_agg(
        case when (step->>'step_number')::integer = p_step_number
             then step || jsonb_build_object('status', p_new_status)
             else step end
        order by ordinal
    ) into v_next_steps
      from jsonb_array_elements(coalesce(v_plan.roadmap_json, '[]'::jsonb)) with ordinality as items(step, ordinal);

    if v_previous_status <> p_new_status or v_note <> '' then
        update plans set roadmap_json = coalesce(v_next_steps, '[]'::jsonb)
         where id = p_plan_id returning * into v_plan;
        insert into plan_action_history(plan_id, step_number, previous_status, new_status, change_note, changed_by)
        values (p_plan_id, p_step_number, v_previous_status, p_new_status, v_note,
                left(coalesce(nullif(btrim(p_changed_by), ''), 'user'), 120));
    end if;
    return to_jsonb(v_plan);
end;
$$;

revoke all on function update_plan_action_status(uuid, integer, text, text, text) from public, anon, authenticated;
grant execute on function update_plan_action_status(uuid, integer, text, text, text) to service_role;
