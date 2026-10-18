alter table predictions
    drop constraint if exists predictions_priority_level_check;

alter table predictions
    add constraint predictions_priority_level_check
    check (priority_level in ('Low', 'Medium', 'High', 'Unknown'));
