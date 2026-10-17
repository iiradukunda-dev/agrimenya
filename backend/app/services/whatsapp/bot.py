from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from typing import Any

from app.core.config import settings
from app.db import crud
from app.services.ai_assistant import ask_assistant_with_source

HELP_EN = "Commands: HELP, DISTRICT <name>, CROP <name>, SUBSCRIBE <district> [crop], STATUS, RANK <crop>, ALERTS, LANG EN|RW, STOP."
HELP_RW = "Amabwiriza: HELP, DISTRICT <akarere>, CROP <igihingwa>, SUBSCRIBE <akarere> [igihingwa], STATUS, RANK <igihingwa>, ALERTS, LANG EN|RW, SHIRA."
UNKNOWN_EN = "I did not recognize that command. "
UNKNOWN_RW = "Sinumva iryo tegeko. "
SAFE_FALLBACK = "I can't answer that reliably. Send HELP for options."


def handle_inbound(contact: dict[str, Any], text: str) -> str | None:
    now = datetime.now(timezone.utc)
    one_hour_ago = (now - timedelta(hours=1)).isoformat()
    if crud.count_inbound_messages_since(contact["id"], one_hour_ago, 21) > 20:
        last_notice = _timestamp(contact.get("last_rate_limit_notice_at"))
        if not last_notice or (now - last_notice).total_seconds() >= 3600:
            crud.update_contact(contact["id"], {"last_rate_limit_notice_at": now.isoformat()})
            return _finish("Please wait before sending more messages.", "Tegereza mbere yo kohereza ubundi butumwa.", contact)
        return None

    language = contact.get("language", "en")
    normalized = _normalize(text)
    command, _, argument = normalized.partition(" ")
    if command in {"HELP", "AMABWIRIZA"}:
        _reset_unknown_count(contact)
        return _finish(HELP_EN, HELP_RW, contact)
    if command == "LANG":
        target = argument.strip().upper()
        if target not in {"EN", "RW"}:
            return _finish("Use LANG EN or LANG RW.", "Koresha LANG EN cyangwa LANG RW.", contact)
        crud.update_contact(contact["id"], {"language": target.lower(), "bot_unknown_count": 0})
        return _finish(
            "Language set to English." if target == "EN" else "Ururimi rwashyizwe mu Kinyarwanda.",
            "Language set to English." if target == "EN" else "Ururimi rwashyizwe mu Kinyarwanda.",
            {**contact, "language": target.lower()},
        )
    if command == "DISTRICT":
        return _district_reply(argument, contact)
    if command == "CROP":
        return _crop_reply(argument, contact)
    if command == "SUBSCRIBE":
        return _subscribe(argument, contact)
    if command == "STATUS":
        return _status(contact)
    if command == "RANK":
        return _rank(argument, contact)
    if command == "ALERTS":
        return _alerts(contact)
    if command in {"UNSUBSCRIBE", "STOP", "STOPPED", "HEREZA", "SHIRA"}:
        return None

    if not (settings.GROQ_API_KEY or settings.LLM_API_KEY):
        return _finish(HELP_EN, HELP_RW, contact)
    zone_id = contact.get("zone_id")
    if not zone_id:
        try:
            subscriptions = crud.list_alert_subscriptions(contact["id"])
            zone_id = next((item.get("zone_id") for item in subscriptions if item.get("zone_id")), None)
        except Exception:
            zone_id = None
    if zone_id:
        try:
            safe_question = text.strip()[:500]
            if safe_question and len(safe_question) <= 500:
                answer, _, _ = ask_assistant_with_source(
                    zone_id,
                    f"<untrusted>{safe_question}</untrusted>",
                    crop=contact.get("crop"),
                )
                answer = re.sub(r"<[^>]*>", "", str(answer or ""))
                if safe_question.casefold() in answer.casefold():
                    answer = SAFE_FALLBACK
                if answer.strip():
                    _reset_unknown_count(contact)
                    return _finish(answer, answer, contact)
        except Exception:
            pass

    _record_unknown(contact)
    unknown_count = int(contact.get("bot_unknown_count") or 0)
    menu = HELP_RW if language == "rw" else HELP_EN
    if unknown_count >= 3:
        return _finish(menu, menu, contact)
    return _finish(UNKNOWN_EN + HELP_EN, UNKNOWN_RW + HELP_RW, contact)


def _district_reply(query: str, contact: dict[str, Any]) -> str:
    zones = crud.list_zones()
    districts = sorted({str(zone.get("district")) for zone in zones if zone.get("district")})
    match = _match(query, districts)
    if isinstance(match, list):
        return _finish("Choose a district: " + ", ".join(match), "Hitamo akarere: " + ", ".join(match), contact)
    if not match:
        return _finish("I could not match that district. Send HELP for options.", "Akarere ntikabonetse. Ohereza HELP.", contact)
    metrics = crud.get_district_yield_evidence(match)
    latest = _latest_season(metrics)
    district_rows = [row for row in metrics if row.get("season") == latest and row.get("yield_kg_ha") is not None]
    if not district_rows:
        return _finish(f"{match}: no district yield data is available for the latest season.", f"{match}: nta makuru y'umusaruro y'igihembwe giheruka ahari.", contact)
    crops = sorted({str(row.get("crop")) for row in district_rows if row.get("crop")})
    answer = f"{match}, latest season {latest}: district data is available for {', '.join(crops[:4])}."
    return _finish(answer, f"{match}, igihembwe giheruka {latest}: hari amakuru y'ibihingwa {', '.join(crops[:4])}.", contact)


def _crop_reply(query: str, contact: dict[str, Any]) -> str:
    crops = crud.list_district_crops()
    match = _match(query, crops)
    if isinstance(match, list):
        return _finish("Choose a crop: " + ", ".join(match), "Hitamo igihingwa: " + ", ".join(match), contact)
    if not match:
        return _finish("I could not match that crop. Send HELP for options.", "Igihingwa ntikibonetse. Ohereza HELP.", contact)
    return _finish(f"{match} is in the recorded crop data. Send RANK {match} for district comparisons.",
                   f"{match} kiri mu makuru y'ibihingwa. Ohereza RANK {match} ugereranye uturere.", contact)


def _subscribe(argument: str, contact: dict[str, Any]) -> str:
    parts = argument.split()
    if not parts:
        return _finish("Use SUBSCRIBE <district> [crop].", "Koresha SUBSCRIBE <akarere> [igihingwa].", contact)
    zones = crud.list_zones()
    districts = sorted({str(zone.get("district")) for zone in zones if zone.get("district")})
    district_match = _match(parts[0], districts)
    if isinstance(district_match, list):
        return _finish("Choose a district: " + ", ".join(district_match), "Hitamo akarere: " + ", ".join(district_match), contact)
    if not district_match:
        return _finish("I could not match that district.", "Akarere ntikabonetse.", contact)
    crop = None
    if len(parts) > 1:
        crop_match = _match(" ".join(parts[1:]), crud.list_district_crops())
        if isinstance(crop_match, list):
            return _finish("Choose a crop: " + ", ".join(crop_match), "Hitamo igihingwa: " + ", ".join(crop_match), contact)
        if not crop_match:
            return _finish("I could not match that crop.", "Igihingwa ntikibonetse.", contact)
        crop = crop_match
    matching_zones = [zone for zone in zones if zone.get("district") == district_match]
    for zone in matching_zones:
        crud.create_alert_subscription({
            "contact_id": contact["id"],
            "zone_id": zone["id"],
            "crop": crop,
            "min_severity": "warning",
        })
    if not matching_zones:
        return _finish("That district has no zone records.", "Akarere nta zone kanditseho.", contact)
    crop_label = f" for {crop}" if crop else ""
    return _finish(
        f"Subscribed to {district_match}{crop_label} alerts.",
        f"Wiyandikishije ku butumwa bwo mu karere ka {district_match}{crop_label}.",
        contact,
    )


def _status(contact: dict[str, Any]) -> str:
    subscriptions = crud.list_alert_subscriptions(contact["id"])
    if not subscriptions:
        return _finish("You have no alert subscriptions.", "Nta butumwa bw'uturere wiyandikishijeho.", contact)
    zones = {str(zone.get("id")): zone for zone in crud.list_zones()}
    lines = []
    for subscription in subscriptions[:5]:
        zone = zones.get(str(subscription.get("zone_id")), {})
        district = zone.get("district") or "All zones"
        crop = subscription.get("crop") or "all crops"
        lines.append(f"{district} ({crop}, {subscription.get('min_severity', 'warning')}+)")
    return _finish("Your alert subscriptions: " + "; ".join(lines), "Ubutumwa wiyandikishijeho: " + "; ".join(lines), contact)


def _rank(query: str, contact: dict[str, Any]) -> str:
    match = _match(query, crud.list_district_crops())
    if isinstance(match, list):
        return _finish("Choose a crop: " + ", ".join(match), "Hitamo igihingwa: " + ", ".join(match), contact)
    if not match:
        return _finish("I could not match that crop.", "Igihingwa ntikibonetse.", contact)
    rows = crud.get_yield_evidence(None, match)
    season = _latest_season(rows)
    by_district: dict[str, list[float]] = {}
    for row in rows:
        if row.get("season") != season or row.get("yield_kg_ha") is None:
            continue
        district = row.get("district")
        if district:
            by_district.setdefault(str(district), []).append(float(row["yield_kg_ha"]))
    ranking = sorted(
        ((sum(values) / len(values), district) for district, values in by_district.items()),
        reverse=True,
    )
    if not ranking:
        return _finish(f"No district yield ranking is available for {match}.", f"Nta rutonde rw'umusaruro wa {match} ruhari.", contact)
    top = ranking[:3]
    bottom = sorted(ranking[-3:]) if len(ranking) > 3 else []
    response = f"{match}, {season}: top districts " + "; ".join(f"{district} {value:.0f} kg/ha" for value, district in top)
    if bottom:
        response += ". Lower districts " + "; ".join(f"{district} {value:.0f} kg/ha" for value, district in bottom)
    return _finish(response + ".", response + ".", contact)


def _alerts(contact: dict[str, Any]) -> str:
    zone_id = contact.get("zone_id")
    if not zone_id:
        subscriptions = crud.list_alert_subscriptions(contact["id"])
        zone_id = next((item.get("zone_id") for item in subscriptions if item.get("zone_id")), None)
    zone = crud.get_zone(zone_id) if zone_id else None
    if not zone:
        return _finish("Set a district subscription first to receive local alerts.", "Banza wiyandikishe ku karere kugira ngo ubone ubutumwa bwaho.", contact)
    alerts = crud.list_district_alerts(zone["district"])[:3]
    if not alerts:
        return _finish("There are no recent alerts for your district.", "Nta butumwa bushya buhari mu karere kawe.", contact)
    messages = [re.sub(r"\s+", " ", str(alert.get("message") or "")).strip()[:150] for alert in alerts]
    result = "Latest alerts: " + "; ".join(message for message in messages if message)
    return _finish(result, "Ubutumwa buheruka: " + "; ".join(messages), contact)


def _match(query: str, choices: list[str]) -> str | list[str] | None:
    term = _normalize(query)
    if not term:
        return None
    exact = [choice for choice in choices if _normalize(choice) == term]
    if exact:
        return exact[0]
    scored = sorted(
        ((SequenceMatcher(None, term, _normalize(choice)).ratio(), choice) for choice in choices),
        reverse=True,
    )
    viable = [(score, choice) for score, choice in scored if score >= 0.8]
    if not viable:
        return None
    if len(viable) > 1 and viable[0][0] - viable[1][0] < 0.04:
        return [choice for _, choice in viable[:3]]
    return viable[0][1]


def _latest_season(rows: list[dict]) -> str | None:
    seasons = [str(row.get("season")) for row in rows if row.get("season")]
    if not seasons:
        return None

    def season_key(season: str) -> tuple[int, int, str]:
        year_match = re.search(r"20\d{2}", season)
        year = int(year_match.group()) if year_match else 0
        term = season.lower()
        term_order = 3 if "season c" in term else 2 if "season b" in term else 1 if "season a" in term else 0
        return year, term_order, season

    return max(seasons, key=season_key)


def _record_unknown(contact: dict[str, Any]) -> None:
    count = int(contact.get("bot_unknown_count") or 0) + 1
    crud.update_contact(contact["id"], {"bot_unknown_count": count})
    contact["bot_unknown_count"] = count


def _reset_unknown_count(contact: dict[str, Any]) -> None:
    if int(contact.get("bot_unknown_count") or 0):
        crud.update_contact(contact["id"], {"bot_unknown_count": 0})
        contact["bot_unknown_count"] = 0


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold().upper()


def _finish(english: str, kinyarwanda: str, contact: dict[str, Any]) -> str:
    response = kinyarwanda if contact.get("language") == "rw" else english
    response = re.sub(r"https?://\S+|www\.\S+", "[redacted]", response, flags=re.IGNORECASE)
    response = re.sub(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)", "[redacted]", response)
    if re.search(r"\d", response) and "Source:" not in response:
        response += " Source: recorded Agri-Menya district data."
    return response[:600]


def _timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp
    except (TypeError, ValueError):
        return None
