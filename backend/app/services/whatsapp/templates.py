from __future__ import annotations

import re

from app.db import crud


TEMPLATES = {
    ("agrimenya_alert", "en"): {
        "category": "utility",
        "param_count": 4,
        "body_preview": "Agri-Menya alert for {{1}} ({{2}}): {{3}} Suggested action: {{4}} Reply STOP to unsubscribe.",
    },
    ("agrimenya_alert", "rw_RW"): {
        "category": "utility",
        "param_count": 4,
        "body_preview": "Ubutumwa bwa Agri-Menya ku karere ka {{1}} ({{2}}): {{3}} Igikorwa gisabwa: {{4}} Andika SHIRA kugira ngo uhagarike ubutumwa.",
    },
    ("agrimenya_plan_share", "en"): {
        "category": "utility",
        "param_count": 3,
        "body_preview": "Agri-Menya plan for {{1}} ({{2}}): {{3}}. Reply STOP to unsubscribe.",
    },
    ("agrimenya_plan_share", "rw_RW"): {
        "category": "utility",
        "param_count": 3,
        "body_preview": "Gahunda ya Agri-Menya ku karere ka {{1}} ({{2}}): {{3}}. Andika SHIRA kugira ngo uhagarike ubutumwa.",
    },
    ("agrimenya_optin_confirm", "en"): {
        "category": "utility",
        "param_count": 1,
        "body_preview": "Hello {{1}}, you are subscribed to Agri-Menya WhatsApp alerts. Reply STOP to unsubscribe.",
    },
    ("agrimenya_optin_confirm", "rw_RW"): {
        "category": "utility",
        "param_count": 1,
        "body_preview": "Muraho {{1}}, wiyandikishije ku butumwa bwa Agri-Menya kuri WhatsApp. Andika SHIRA kugira ngo uhagarike ubutumwa.",
    },
    ("agrimenya_weekly_digest", "en"): {
        "category": "utility",
        "param_count": 3,
        "body_preview": "Agri-Menya weekly update for {{1}}: {{2}} alerts. Top item: {{3}}. Reply STOP to unsubscribe.",
    },
    ("agrimenya_weekly_digest", "rw_RW"): {
        "category": "utility",
        "param_count": 3,
        "body_preview": "Incamake y'icyumweru ya Agri-Menya ku karere ka {{1}}: ubutumwa {{2}}. Icy'ingenzi: {{3}}. Andika SHIRA kugira ngo uhagarike ubutumwa.",
    },
}


def validate_params(name: str, params: list[str]) -> list[str]:
    candidates = [template for (template_name, _), template in TEMPLATES.items() if template_name == name]
    if not candidates:
        raise ValueError("Unknown WhatsApp template")
    if len(params) != candidates[0]["param_count"]:
        raise ValueError("Wrong number of WhatsApp template parameters")
    values = [str(value) for value in params]
    if any(not value.strip() or "\n" in value or "\r" in value or len(value) > 500 for value in values):
        raise ValueError("WhatsApp template parameters must be non-empty single-line text up to 500 characters")
    return [re.sub(r" {5,}", "    ", value).strip() for value in values]


def render_preview(name: str, language: str, params: list[str]) -> str:
    values = validate_params(name, params)
    template = TEMPLATES.get((name, language))
    if not template:
        raise ValueError("Unknown WhatsApp template language")
    result = template["body_preview"]
    for index, value in enumerate(values, start=1):
        result = result.replace("{{" + str(index) + "}}", value)
    return result


def approved_template(name: str, language: str) -> dict | None:
    requested_language = "rw_RW" if language in {"rw", "rw_RW"} else "en"
    record = crud.get_whatsapp_template(name, requested_language)
    if record and record.get("status") == "approved":
        return record
    if requested_language != "en":
        fallback = crud.get_whatsapp_template(name, "en")
        if fallback and fallback.get("status") == "approved":
            return fallback
    return None
