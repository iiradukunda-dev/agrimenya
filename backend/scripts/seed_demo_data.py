"""Populate a dedicated Agri-Menya demo Supabase project with synthetic records.

This script intentionally reads only backend/.env.demo. It refuses to write
unless both APP_ENV=demo and an explicit confirmation phrase are present.
Never point these variables at production or a database containing real users.
"""
from __future__ import annotations

import hashlib
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from dotenv import load_dotenv
from supabase import create_client

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEMO_ENV = BACKEND_DIR / ".env.demo"
load_dotenv(DEMO_ENV, override=True)

DEMO_PREFIX = "DEMO — Synthetic scenario. Not real farmer, field, market, or NISR data."
DEMO_PASSWORD = "DemoOnly-Agri-Menya-2026!"
SEASONS = [
    "[DEMO] Season A 2024", "[DEMO] Season B 2024",
    "[DEMO] Season A 2025", "[DEMO] Season B 2025",
]
CROPS = ["Maize", "Beans", "Irish potato", "Cassava", "Banana"]
DISTRICTS = [
    "Musanze", "Rulindo", "Nyagatare", "Huye", "Rubavu", "Bugesera",
]
SECTORS = ["Demo Central", "Demo North", "Demo South"]


def stable_id(kind: str, key: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"agri-menya-demo-v1:{kind}:{key}"))


def password_hash(password: str) -> str:
    salt = hashlib.sha256(b"agri-menya-demo-only-salt-v1").digest()[:16]
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=64)
    return f"scrypt$16384$8$1${salt.hex()}${digest.hex()}"


def guard() -> Any:
    if not DEMO_ENV.is_file():
        raise RuntimeError(f"Missing {DEMO_ENV}. Copy backend/demo.env.example to backend/.env.demo first.")
    if os.getenv("APP_ENV", "").strip().lower() != "demo":
        raise RuntimeError("Refusing to seed: set APP_ENV=demo in backend/.env.demo.")
    if os.getenv("DEMO_SEED_CONFIRM") != "SEED_AGRI_MENYA_DEMO":
        raise RuntimeError("Refusing to seed: set DEMO_SEED_CONFIRM=SEED_AGRI_MENYA_DEMO explicitly.")

    url = os.getenv("DEMO_SUPABASE_URL", "").strip().rstrip("/")
    key = os.getenv("DEMO_SUPABASE_SERVICE_ROLE_KEY", "").strip()
    expected_ref = os.getenv("DEMO_SUPABASE_PROJECT_REF", "").strip()
    if not url.startswith("https://") or not key or not expected_ref:
        raise RuntimeError("Set DEMO_SUPABASE_URL, DEMO_SUPABASE_SERVICE_ROLE_KEY, and DEMO_SUPABASE_PROJECT_REF.")
    actual_ref = url.removeprefix("https://").split(".", 1)[0]
    if actual_ref != expected_ref:
        raise RuntimeError("The Supabase URL does not match DEMO_SUPABASE_PROJECT_REF; refusing to write.")
    print(f"Target demo Supabase project: {expected_ref}")
    if input("Type SEED_AGRI_MENYA_DEMO to continue: ").strip() != "SEED_AGRI_MENYA_DEMO":
        raise RuntimeError("Cancelled; no demo data was written.")
    return create_client(url, key)


def upsert(client: Any, table: str, rows: list[dict], conflict: str = "id") -> int:
    if not rows:
        return 0
    for start in range(0, len(rows), 200):
        client.table(table).upsert(rows[start:start + 200], on_conflict=conflict).execute()
    return len(rows)


def demo_rows() -> dict[str, tuple[list[dict], str]]:
    now = datetime.now(timezone.utc)
    zones: list[dict] = []
    zone_by_key: dict[tuple[str, str], str] = {}
    # Approximate demo map points are deliberately offset from district centroids.
    from app.db.rwanda_districts import DISTRICT_LOOKUP

    for district in DISTRICTS:
        centroid = DISTRICT_LOOKUP[district]
        for i, sector in enumerate(SECTORS):
            key = (district, sector)
            zone_id = stable_id("zone", f"{district}:{sector}")
            zone_by_key[key] = zone_id
            zones.append({
                "id": zone_id, "district": district, "sector": sector,
                "cell": f"Demo Cell {i + 1}",
                "latitude": centroid["latitude"] + (i - 1) * 0.018,
                "longitude": centroid["longitude"] + (i - 1) * 0.018,
                "crop_type": None, "season": None,
                "identity_key": f"{district.casefold()}|{sector.casefold()}|demo cell {i + 1}||",
            })

    metrics: list[dict] = []
    for zone in zones:
        for crop_index, crop in enumerate(CROPS):
            for season_index, season in enumerate(SEASONS):
                # Deterministic demonstration figures; these are not estimates from research.
                variation = (sum(map(ord, zone["district"] + zone["sector"])) % 11) * 37
                baseline = [2100, 1250, 8200, 10500, 7800][crop_index]
                yield_value = baseline + variation + (season_index - 1) * (65 + crop_index * 10)
                area = 1.5 + ((crop_index + season_index) % 5) * 0.7
                metrics.append({
                    "id": stable_id("metric", f"{zone['id']}:{crop}:{season}"),
                    "zone_id": zone["id"], "season": season, "crop": crop,
                    "yield_actual": round(yield_value, 1),
                    "production_mt": round(yield_value * area / 1000, 2),
                    "rainfall_mm": 680 + ((crop_index * 47 + season_index * 83) % 290),
                    "soil_type": "DEMO synthetic soil profile",
                    "area_cultivated": area, "household_size": 5,
                })

    alignment: list[dict] = []
    predictions: list[dict] = []
    plans: list[dict] = []
    alerts: list[dict] = []
    readiness: list[dict] = []
    work_records: list[dict] = []
    field_reports: list[dict] = []
    for index, zone in enumerate(zones):
        zone_id = zone["id"]
        predictions.append({
            "id": stable_id("prediction", zone_id), "zone_id": zone_id,
            "season": SEASONS[index % len(SEASONS)], "crop": CROPS[index % len(CROPS)],
            "predicted_yield": float(1800 + (index * 173) % 6200),
            "priority_level": ["Low", "Medium", "High"][index % 3],
            "confidence": round(0.55 + (index % 4) * 0.1, 2),
            "model_version": "DEMO synthetic scenario; not a model prediction",
        })
        for season_index, season in enumerate(SEASONS):
            alignment.append({
                "id": stable_id("alignment", f"{zone_id}:{season}"), "zone_id": zone_id,
                "season": season, "irrigation_ha": 0.4 + (index % 4) * 0.2,
                "terraces_ha": 0.8 + (index % 5) * 0.3,
                "credit_insurance_score": 35 + (index * 7 + season_index * 3) % 61,
                "nutrition_risk_level": ["Low", "Medium", "High"][index % 3],
                "climate_risk_level": ["Medium", "Low", "High"][season_index % 3],
                "female_managed_share": round(0.25 + (index % 5) * 0.1, 2),
                "export_readiness_flag": index % 4 == 0,
                "estimated_jobs_supported": 12 + (index * 3) % 80,
            })
        readiness.append({
            "zone_id": zone_id,
            "finance_evidence": {"demo": True, "records": [
                {"name": "DEMO cooperative ledger", "status": "recorded"},
                {"name": "DEMO seasonal budget", "status": "needs_review"},
            ]},
            "export_evidence": {"demo": True, "records": [
                {"name": "DEMO quality checklist", "status": "incomplete"},
            ]},
        })
        work_records.append({
            "id": stable_id("work", zone_id), "zone_id": zone_id,
            "season": SEASONS[index % len(SEASONS)], "crop": CROPS[index % len(CROPS)],
            "worker_days": 18 + index % 25,
            "notes": f"{DEMO_PREFIX} Example labor entry.",
        })
        if index < 12:
            crop = CROPS[index % len(CROPS)]
            alerts.append({
                "id": stable_id("alert", zone_id), "zone_id": zone_id,
                "message": f"{DEMO_PREFIX} Review the sample {crop} field observation with an extension officer.",
                "severity": ["Info", "Warning", "Critical"][index % 3], "crop": crop,
                "action": "DEMO ONLY: verify all local conditions before taking action.",
                "status": "draft", "allow_links": False, "created_by": "demo-seeder",
            })
        if index < 18:
            crop = CROPS[index % len(CROPS)]
            plans.append({
                "id": stable_id("plan", zone_id), "zone_id": zone_id,
                "title": f"[DEMO] {crop} seasonal support plan",
                "roadmap_json": [
                    {"step_number": 1, "title": "Review demo field notes", "description": DEMO_PREFIX,
                     "timeframe": "Week 1", "owner": "Demo extension officer", "status": "planned"},
                    {"step_number": 2, "title": "Confirm input quantities locally", "description": "Use current local supplier prices; all demo figures are illustrative.",
                     "timeframe": "Week 2", "owner": "Demo cooperative lead", "status": "in_progress"},
                    {"step_number": 3, "title": "Record follow-up observation", "description": "Add a real observation only in a real deployment.",
                     "timeframe": "After planting", "owner": "Demo farmer", "status": "planned"},
                ],
                "resources_json": {"demo": True, "area_ha": 2.2, "seeds_kg": 44,
                                   "fertilizer_kg": 110, "estimated_cost_rwf": 185000,
                                   "note": DEMO_PREFIX},
                "created_by": "demo-seeder",
            })
        if index < 30:
            field_reports.append({
                "id": stable_id("field-report", zone_id), "zone_id": zone_id,
                "district": zone["district"], "crop": CROPS[index % len(CROPS)],
                "rainfall_mm": float(18 + (index * 23) % 180),
                "soil_moisture_pct": float(24 + (index * 9) % 65),
                "symptoms": ["Leaf yellowing", "Uneven emergence", "No visible symptoms", "Wilting on a few plants"][index % 4],
                "notes": f"{DEMO_PREFIX} Do not treat this as a verified farmer report.",
                "submitted_at": (now - timedelta(days=index % 20)).isoformat(),
                "observed_on": (date.today() - timedelta(days=index % 20)).isoformat(),
            })

    users = []
    for i in range(8):
        users.append({
            "id": stable_id("community-account", str(i)),
            "email": f"demo.farmer{i + 1:02d}@example.invalid",
            "display_name": f"demo_farmer_{i + 1:02d}",
            "role": ["farmer", "cooperative_leader", "extension_officer", "planner"][i % 4],
            "password_hash": password_hash(DEMO_PASSWORD), "is_active": True,
            "email_verified_at": datetime.now(timezone.utc).isoformat(),
        })

    posts = []
    comments = []
    for i in range(16):
        post_id = stable_id("community-post", str(i))
        author_id = users[i % len(users)]["id"]
        posts.append({
            "id": post_id, "author_id": author_id,
            "title": f"[DEMO] {['Maize planting question', 'Bean leaf observation', 'Market planning discussion', 'Soil and water note'][i % 4]} #{i + 1}",
            "body": f"{DEMO_PREFIX} This fictional community post exists only to demonstrate the feed, comments, and moderation tools. Scenario: {['uneven emergence after rain', 'checking crop spacing', 'planning a cooperative meeting', 'asking an extension officer to inspect leaves'][i % 4]}.",
            "status": "published",
        })
        for j in range(2):
            comments.append({
                "id": stable_id("community-comment", f"{i}:{j}"), "post_id": post_id,
                "author_id": users[(i + j + 1) % len(users)]["id"],
                "body": f"{DEMO_PREFIX} Example reply {j + 1}: share verified local details and seek extension support where needed.",
                "status": "published",
            })

    contacts = []
    subscriptions = []
    for i in range(12):
        contact_id = stable_id("contact", str(i))
        zone_id = zones[i % len(zones)]["id"]
        contacts.append({
            "id": contact_id, "display_name": f"DEMO Contact {i + 1:02d}",
            "role": ["farmer", "extension_officer", "cooperative_leader"][i % 3],
            "phone_e164": None, "bsuid": f"demo-bsuid-{i + 1:04d}",
            "language": "rw" if i % 2 else "en", "zone_id": zone_id,
            "crops": [CROPS[i % len(CROPS)]], "whatsapp_opt_in": False,
        })
        subscriptions.append({
            "id": stable_id("subscription", str(i)), "contact_id": contact_id,
            "zone_id": zone_id, "crop": CROPS[i % len(CROPS)],
            "min_severity": ["info", "warning", "critical"][i % 3],
        })

    # Test message logs are inbound-only; no external message can be dispatched.
    messages = [{
        "id": stable_id("message", str(i)), "direction": "inbound",
        "contact_id": contacts[i % len(contacts)]["id"],
        "wa_message_id": f"wamid.demo.{i + 1:04d}", "kind": "bot_reply",
        "status": "received", "body_hash": hashlib.sha256(f"demo-message-{i}".encode()).hexdigest(),
    } for i in range(12)]
    templates = [
        {"name": "demo_alert_notice", "language": language, "category": "utility",
         "status": "draft", "body_preview": f"{DEMO_PREFIX} Example alert template.", "param_count": 1}
        for language in ("en", "rw")
    ]
    reports = [{
        "id": stable_id("community-report", "open-demo-post"),
        "reporter_id": users[0]["id"], "post_id": posts[0]["id"], "comment_id": None,
        "reason": f"{DEMO_PREFIX} Sample moderation report for training.", "status": "open",
    }]

    admin = [{
        "id": stable_id("admin-account", "demo-admin"), "email": "demo.admin@example.invalid",
        "display_name": "DEMO Administrator", "password_hash": password_hash(DEMO_PASSWORD),
        "is_active": True,
    }]

    return {
        "zones": (zones, "id"),
        "agri_metrics": (metrics, "id"),
        "predictions": (predictions, "id"),
        "alignment_metrics": (alignment, "id"),
        "zone_readiness": (readiness, "zone_id"),
        "zone_work_records": (work_records, "id"),
        "field_reports": (field_reports, "id"),
        "plans": (plans, "id"),
        "alerts": (alerts, "id"),
        "community_accounts": (users, "id"),
        "community_posts": (posts, "id"),
        "community_comments": (comments, "id"),
        "community_reports": (reports, "id"),
        "admin_accounts": (admin, "id"),
        "contacts": (contacts, "id"),
        "alert_subscriptions": (subscriptions, "id"),
        "message_log": (messages, "id"),
        "whatsapp_templates": (templates, "name,language"),
    }


def reset_demo(client: Any, payload: dict[str, tuple[list[dict], str]]) -> None:
    # Delete only deterministic IDs generated by this script, in FK-safe order.
    order = [
        "community_reports", "community_comments", "community_posts", "field_reports",
        "message_log", "alert_subscriptions", "contacts", "plans", "alerts",
        "zone_work_records", "zone_readiness", "alignment_metrics", "agri_metrics",
        "predictions",
        "community_accounts", "admin_accounts", "zones",
    ]
    for table in order:
        rows, conflict = payload[table]
        identifiers = [row.get(conflict) for row in rows if row.get(conflict)]
        for start in range(0, len(identifiers), 200):
            client.table(table).delete().in_(conflict, identifiers[start:start + 200]).execute()
        print(f"{table}: removed up to {len(identifiers)} demo rows")
    for template in payload["whatsapp_templates"][0]:
        client.table("whatsapp_templates").delete().eq("name", template["name"]).eq(
            "language", template["language"]
        ).execute()
    print("whatsapp_templates: removed demo templates")


def main() -> int:
    try:
        client = guard()
        payload = demo_rows()
        if "--reset" in sys.argv[1:]:
            reset_demo(client, payload)
            return 0
        total = 0
        for table, (rows, conflict) in payload.items():
            count = upsert(client, table, rows, conflict)
            total += count
            print(f"{table}: upserted {count}")
        print(f"Done: {total} deterministic demo rows across {len(payload)} tables.")
        print("All demo alerts are drafts; WhatsApp contacts are opted out; only inbound mock logs are seeded.")
        return 0
    except Exception as exc:
        print(f"Demo seed stopped: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
