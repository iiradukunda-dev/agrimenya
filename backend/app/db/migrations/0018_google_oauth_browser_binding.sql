-- Bind Google sign-in handoff codes to the browser that initiated OAuth.
alter table community_oauth_login_codes
    add column if not exists browser_binding_hash text;

-- Invalidate codes issued before browser binding was required.
update community_oauth_login_codes
set browser_binding_hash = '',
    consumed_at = coalesce(consumed_at, now())
where browser_binding_hash is null;

alter table community_oauth_login_codes
    alter column browser_binding_hash set not null;

comment on column community_oauth_login_codes.browser_binding_hash is
    'SHA-256 hash of the initiating browser handoff cookie; required to redeem the one-time code.';
