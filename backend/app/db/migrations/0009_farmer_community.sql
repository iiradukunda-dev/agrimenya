-- Authenticated farmer discussions with accountable authors and moderation.
create table if not exists community_accounts (
    id uuid primary key default gen_random_uuid(),
    email text not null,
    display_name text not null check (char_length(display_name) between 1 and 80),
    role text not null default 'farmer'
        check (role in ('farmer', 'cooperative_leader', 'extension_officer', 'planner')),
    password_hash text not null,
    is_active boolean not null default true,
    session_version integer not null default 1 check (session_version > 0),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create unique index if not exists community_accounts_email_unique
    on community_accounts(lower(email));

create table if not exists community_posts (
    id uuid primary key default gen_random_uuid(),
    author_id uuid not null references community_accounts(id) on delete cascade,
    title text not null check (char_length(title) between 3 and 140),
    body text not null check (char_length(body) between 1 and 5000),
    status text not null default 'published'
        check (status in ('published', 'hidden', 'deleted')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create index if not exists community_posts_feed_idx
    on community_posts(status, created_at desc);
create index if not exists community_posts_author_idx
    on community_posts(author_id, created_at desc);

create table if not exists community_comments (
    id uuid primary key default gen_random_uuid(),
    post_id uuid not null references community_posts(id) on delete cascade,
    author_id uuid not null references community_accounts(id) on delete cascade,
    body text not null check (char_length(body) between 1 and 1500),
    status text not null default 'published'
        check (status in ('published', 'hidden', 'deleted')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create index if not exists community_comments_post_idx
    on community_comments(post_id, status, created_at);

create table if not exists community_reports (
    id uuid primary key default gen_random_uuid(),
    reporter_id uuid not null references community_accounts(id) on delete cascade,
    post_id uuid references community_posts(id) on delete cascade,
    comment_id uuid references community_comments(id) on delete cascade,
    reason text not null check (char_length(reason) between 3 and 500),
    status text not null default 'open' check (status in ('open', 'resolved', 'dismissed')),
    reviewed_by uuid references admin_accounts(id) on delete set null,
    created_at timestamptz not null default now(),
    reviewed_at timestamptz,
    constraint community_reports_one_target check ((post_id is null) <> (comment_id is null))
);
create unique index if not exists community_reports_once_per_target
    on community_reports(reporter_id,
        coalesce(post_id, '00000000-0000-0000-0000-000000000000'::uuid),
        coalesce(comment_id, '00000000-0000-0000-0000-000000000000'::uuid));
create index if not exists community_reports_open_idx
    on community_reports(status, created_at desc);

alter table community_accounts enable row level security;
alter table community_posts enable row level security;
alter table community_comments enable row level security;
alter table community_reports enable row level security;

comment on table community_accounts is 'Self-registered community accounts; role is self-reported until verified. Service-role access only.';
comment on table community_posts is 'Farmer discussion posts. Service-role access only.';
comment on table community_comments is 'Comments on community posts. Service-role access only.';
comment on table community_reports is 'Abuse reports for community content. Service-role access only.';
