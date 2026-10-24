-- Named administrator identities and one-time password recovery tokens.
create table if not exists admin_accounts (
    id uuid primary key default gen_random_uuid(),
    email text not null unique,
    display_name text not null,
    password_hash text not null,
    is_active boolean not null default true,
    session_version integer not null default 1 check (session_version > 0),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    last_login_at timestamptz
);

create table if not exists admin_password_reset_tokens (
    id uuid primary key default gen_random_uuid(),
    admin_id uuid not null references admin_accounts(id) on delete cascade,
    token_hash text not null unique,
    expires_at timestamptz not null,
    used_at timestamptz,
    created_at timestamptz not null default now()
);
create index if not exists admin_password_reset_tokens_admin_idx
    on admin_password_reset_tokens(admin_id, expires_at desc);

alter table admin_accounts enable row level security;
alter table admin_password_reset_tokens enable row level security;
comment on table admin_accounts is 'Named administrator accounts. Service-role access only.';
comment on table admin_password_reset_tokens is 'Hashed, expiring, single-use administrator recovery tokens. Service-role access only.';
