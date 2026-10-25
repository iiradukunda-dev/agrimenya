-- Support optional Google OAuth sign-in for farmer community accounts.
alter table community_accounts
    alter column password_hash drop not null,
    add column if not exists google_subject text;

create unique index if not exists community_accounts_google_subject_unique
    on community_accounts(google_subject)
    where google_subject is not null;

create table if not exists community_oauth_login_codes (
    code_hash text primary key,
    account_id uuid not null references community_accounts(id) on delete cascade,
    expires_at timestamptz not null,
    consumed_at timestamptz,
    created_at timestamptz not null default now()
);
create index if not exists community_oauth_login_codes_expiry_idx
    on community_oauth_login_codes(expires_at);
alter table community_oauth_login_codes enable row level security;

comment on column community_accounts.google_subject is
    'Stable Google OpenID subject used to link an optional Community sign-in method.';
comment on table community_oauth_login_codes is
    'Short-lived, one-time browser handoff codes for completing Google Community sign-in.';
