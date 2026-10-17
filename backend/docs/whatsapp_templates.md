# WhatsApp templates

Submit these messages manually in Meta's template manager as **UTILITY**
templates. Do not mark a local template approved until Meta has approved the
matching name and language. Confirm that `rw_RW` is available in the manager.
All values substituted into `{{1}}` and later placeholders must be non-empty,
single-line text.

## `agrimenya_alert` — 4 parameters

**English (`en`):** Agri-Menya alert for {{1}} ({{2}}): {{3}} Suggested action: {{4}} Reply STOP to unsubscribe.

Parameters: district, crop, short message, action.

**Kinyarwanda (`rw_RW`; needs human review before submission):** Ubutumwa bwa Agri-Menya ku karere ka {{1}} ({{2}}): {{3}} Igikorwa gisabwa: {{4}} Andika SHIRA kugira ngo uhagarike ubutumwa.

Back-translation: Agri-Menya message for district {{1}} ({{2}}): {{3}}. Suggested action: {{4}}. Write SHIRA to stop messages.

## `agrimenya_plan_share` — 3 parameters

**English (`en`):** Agri-Menya plan for {{1}} ({{2}}): {{3}}. Reply STOP to unsubscribe.

Parameters: district, crop, plan title.

**Kinyarwanda (`rw_RW`; needs human review before submission):** Gahunda ya Agri-Menya ku karere ka {{1}} ({{2}}): {{3}}. Andika SHIRA kugira ngo uhagarike ubutumwa.

Back-translation: Agri-Menya plan for district {{1}} ({{2}}): {{3}}. Write SHIRA to stop messages.

## `agrimenya_optin_confirm` — 1 parameter

**English (`en`):** Hello {{1}}, you are subscribed to Agri-Menya WhatsApp alerts. Reply STOP to unsubscribe.

Parameter: name.

**Kinyarwanda (`rw_RW`; needs human review before submission):** Muraho {{1}}, wiyandikishije ku butumwa bwa Agri-Menya kuri WhatsApp. Andika SHIRA kugira ngo uhagarike ubutumwa.

Back-translation: Hello {{1}}, you subscribed to Agri-Menya WhatsApp messages. Write SHIRA to stop messages.

## `agrimenya_weekly_digest` — 3 parameters

**English (`en`):** Agri-Menya weekly update for {{1}}: {{2}} alerts. Top item: {{3}}. Reply STOP to unsubscribe.

Parameters: district, alert count, top item.

**Kinyarwanda (`rw_RW`; needs human review before submission):** Incamake y'icyumweru ya Agri-Menya ku karere ka {{1}}: ubutumwa {{2}}. Icy'ingenzi: {{3}}. Andika SHIRA kugira ngo uhagarike ubutumwa.

Back-translation: Agri-Menya weekly summary for district {{1}}: {{2}} messages. Main item: {{3}}. Write SHIRA to stop messages.

## Registry

From the `backend` directory, register missing templates as drafts with:

```powershell
python -m scripts.seed_whatsapp_templates
```

After approval in Meta, record the matching template status with:

```powershell
python -m scripts.seed_whatsapp_templates --mark-approved agrimenya_alert en
```

Only the approved template registry is eligible for messages outside the
24-hour customer service window. Template submission remains a manual Meta
step; the seed script never calls Meta.
