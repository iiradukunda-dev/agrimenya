alter table community_reports
    add column if not exists field_report_id uuid
        references field_reports(id) on delete cascade;

alter table community_reports
    drop constraint if exists community_reports_one_target;

alter table community_reports
    add constraint community_reports_one_target
    check (num_nonnulls(post_id, comment_id, field_report_id) = 1);

create unique index if not exists community_reports_once_per_field_report
    on community_reports(reporter_id, field_report_id)
    where field_report_id is not null;

create table if not exists community_notifications (
    id uuid primary key default gen_random_uuid(),
    recipient_id uuid not null references community_accounts(id) on delete cascade,
    actor_id uuid references community_accounts(id) on delete set null,
    actor_display_name text not null,
    post_id uuid not null references community_posts(id) on delete cascade,
    comment_id uuid not null references community_comments(id) on delete cascade,
    created_at timestamptz not null default now(),
    read_at timestamptz,
    unique (recipient_id, comment_id)
);

create index if not exists community_notifications_unread_idx
    on community_notifications(recipient_id, created_at desc)
    where read_at is null;

alter table community_notifications enable row level security;

create or replace function notify_community_post_author_of_reply()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    post_author_id uuid;
    actor_name text;
begin
    select author_id into post_author_id
    from community_posts
    where id = new.post_id and status = 'published';

    if post_author_id is null or post_author_id = new.author_id then
        return new;
    end if;

    select display_name into actor_name
    from community_accounts
    where id = new.author_id;

    insert into community_notifications (
        recipient_id, actor_id, actor_display_name, post_id, comment_id
    )
    values (
        post_author_id, new.author_id, coalesce(actor_name, 'Community member'),
        new.post_id, new.id
    )
    on conflict (recipient_id, comment_id) do nothing;

    return new;
end;
$$;

drop trigger if exists community_comment_reply_notification on community_comments;
create trigger community_comment_reply_notification
after insert on community_comments
for each row
when (new.status = 'published')
execute function notify_community_post_author_of_reply();
