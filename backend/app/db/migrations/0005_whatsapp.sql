create table if not exists contacts (
    id uuid primary key default gen_random_uuid(),
    display_name text,
    role text check (role in ('planner', 'extension_officer', 'cooperative_leader', 'farmer', 'other')),
    phone_e164 text,
    bsuid text,
    language text not null default 'en' check (language in ('en', 'rw')),
    zone_id uuid references zones(id),
    crops text[] not null default '{}',
    whatsapp_opt_in boolean not null default false,
    opt_in_at timestamptz,
    opt_in_source text,
    opt_in_text_version text,
    opt_out_at timestamptz,
    last_inbound_at timestamptz,
    undeliverable_count integer not null default 0 check (undeliverable_count >= 0),
    bot_unknown_count smallint not null default 0 check (bot_unknown_count >= 0),
    last_rate_limit_notice_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz,
    constraint contacts_identity_required check (phone_e164 is not null or bsuid is not null or deleted_at is not null),
    constraint contacts_phone_e164_check check (phone_e164 is null or phone_e164 ~ '^\+[1-9][0-9]{7,14}$')
);

create unique index if not exists contacts_phone_e164_unique
    on contacts(phone_e164) where phone_e164 is not null;
create unique index if not exists contacts_bsuid_unique
    on contacts(bsuid) where bsuid is not null;
create index if not exists contacts_last_inbound_at_idx on contacts(last_inbound_at);

create table if not exists whatsapp_templates (
    name text not null,
    language text not null,
    category text not null check (category in ('utility', 'authentication', 'marketing')),
    status text not null default 'draft' check (status in ('draft', 'submitted', 'approved', 'rejected', 'paused')),
    body_preview text,
    param_count integer not null default 0 check (param_count >= 0),
    primary key (name, language)
);

create table if not exists message_log (
    id uuid primary key default gen_random_uuid(),
    direction text not null check (direction in ('outbound', 'inbound')),
    contact_id uuid references contacts(id),
    wa_message_id text unique,
    kind text not null check (kind in ('alert', 'plan_share', 'bot_reply', 'optin_confirm', 'optout_confirm', 'digest')),
    template_name text,
    status text not null check (status in ('queued', 'sent', 'delivered', 'read', 'failed', 'received')),
    error_code text,
    error_detail text,
    alert_id uuid references alerts(id),
    plan_id uuid references plans(id),
    body_hash text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create index if not exists message_log_contact_created_idx on message_log(contact_id, created_at desc);
create unique index if not exists message_log_alert_contact_unique
    on message_log(alert_id, contact_id) where alert_id is not null and contact_id is not null and direction = 'outbound';

create table if not exists webhook_events (
    event_key text primary key,
    received_at timestamptz not null default now(),
    payload_type text not null
);

create table if not exists alert_subscriptions (
    id uuid primary key default gen_random_uuid(),
    contact_id uuid not null references contacts(id) on delete cascade,
    zone_id uuid references zones(id) on delete cascade,
    crop text,
    min_severity text not null default 'warning' check (min_severity in ('info', 'warning', 'critical')),
    unique (contact_id, zone_id, crop)
);
create unique index if not exists alert_subscriptions_scope_unique
    on alert_subscriptions(contact_id, coalesce(zone_id, '00000000-0000-0000-0000-000000000000'::uuid), coalesce(crop, ''));

comment on table contacts is 'WhatsApp identity and consent records. RLS has no public policies; access is server-side only.';
comment on table whatsapp_templates is 'Approved WhatsApp template registry. RLS has no public policies; access is server-side only.';
comment on table message_log is 'Message delivery metadata and body hashes only; message bodies and credentials are never stored here.';
comment on table webhook_events is 'Webhook idempotency keys only. RLS has no public policies; access is server-side only.';
comment on table alert_subscriptions is 'Contact alert preferences. RLS has no public policies; access is server-side only.';

alter table contacts enable row level security;
alter table whatsapp_templates enable row level security;
alter table message_log enable row level security;
alter table webhook_events enable row level security;
alter table alert_subscriptions enable row level security;
