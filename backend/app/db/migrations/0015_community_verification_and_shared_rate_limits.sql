-- Require verified email for community accounts, and share API throttles across workers.
alter table community_accounts add column if not exists email_verified_at timestamptz;

create table if not exists community_email_verification_tokens (
    token_hash text primary key,
    account_id uuid not null references community_accounts(id) on delete cascade,
    expires_at timestamptz not null,
    used_at timestamptz,
    created_at timestamptz not null default now()
);
create index if not exists community_email_verification_account_idx
    on community_email_verification_tokens(account_id, expires_at desc);
alter table community_email_verification_tokens enable row level security;

create or replace function verify_community_email(p_token_hash text) returns uuid
language plpgsql security definer set search_path = public as $$
declare v_account_id uuid;
begin
    update community_email_verification_tokens
       set used_at = now()
     where token_hash = p_token_hash and used_at is null and expires_at > now()
     returning account_id into v_account_id;
    if not found then return null; end if;
    update community_accounts set email_verified_at = coalesce(email_verified_at, now()), updated_at = now()
     where id = v_account_id and is_active = true;
    if not found then return null; end if;
    return v_account_id;
end;
$$;
revoke all on function verify_community_email(text) from public, anon, authenticated;
grant execute on function verify_community_email(text) to service_role;

create table if not exists api_rate_limit_buckets (
    scope text not null,
    bucket_start timestamptz not null,
    hits integer not null check (hits > 0),
    primary key (scope, bucket_start)
);
create index if not exists api_rate_limit_bucket_start_idx on api_rate_limit_buckets(bucket_start);
alter table api_rate_limit_buckets enable row level security;
comment on table api_rate_limit_buckets is 'Shared fixed-window API rate limits used across backend workers.';

-- Remove expired buckets opportunistically while keeping the hot path bounded.
create or replace function consume_api_rate_limit(
    p_scope text, p_max_hits integer, p_window_seconds integer
) returns boolean
language plpgsql security definer set search_path = public as $$
declare
    v_bucket timestamptz;
    v_hits integer;
begin
    if p_scope is null or length(p_scope) < 1 or length(p_scope) > 240
       or p_max_hits < 1 or p_max_hits > 10000
       or p_window_seconds < 1 or p_window_seconds > 86400 then
        raise exception 'Invalid rate limit parameters';
    end if;
    v_bucket := to_timestamp(floor(extract(epoch from now()) / p_window_seconds) * p_window_seconds);
    insert into api_rate_limit_buckets(scope, bucket_start, hits)
    values (p_scope, v_bucket, 1)
    on conflict (scope, bucket_start) do update
       set hits = api_rate_limit_buckets.hits + 1
    returning hits into v_hits;
    if v_hits = 1 then
        delete from api_rate_limit_buckets where bucket_start < now() - interval '2 days';
    end if;
    return v_hits <= p_max_hits;
end;
$$;
revoke all on function consume_api_rate_limit(text, integer, integer) from public, anon, authenticated;
grant execute on function consume_api_rate_limit(text, integer, integer) to service_role;
