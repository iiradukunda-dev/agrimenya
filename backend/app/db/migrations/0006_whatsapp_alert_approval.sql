alter table alerts add column if not exists crop text;
alter table alerts add column if not exists action text;
alter table alerts add column if not exists status text not null default 'draft';
alter table alerts add column if not exists approved_by text;
alter table alerts add column if not exists approved_at timestamptz;
alter table alerts add column if not exists allow_links boolean not null default false;

do $$
begin
    if not exists (
        select 1 from pg_constraint
        where conname = 'alerts_status_check'
          and conrelid = 'alerts'::regclass
    ) then
        alter table alerts add constraint alerts_status_check
            check (status in ('draft', 'approved'));
    end if;
end
$$;

create index if not exists alerts_status_created_idx on alerts(status, created_at desc);
