-- Community usernames are stored in display_name for compatibility with
-- existing posts, but are now validated and unique without regard to case.
do $$
begin
    if not exists (
        select 1 from pg_constraint
        where conname = 'community_accounts_username_shape'
          and conrelid = 'community_accounts'::regclass
    ) then
        alter table community_accounts
            add constraint community_accounts_username_shape
            check (display_name ~ '^[a-z0-9_]{3,30}$');
    end if;
end $$;

create unique index if not exists community_accounts_username_unique
    on community_accounts(lower(btrim(display_name)));

-- Email already has a case-insensitive unique index from migration 0009.
comment on column community_accounts.display_name is 'Unique lowercase community username shown on posts; email is also unique case-insensitively.';
