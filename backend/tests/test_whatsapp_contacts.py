import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def _admin(monkeypatch):
    from tests.auth_helpers import admin_headers
    return admin_headers(monkeypatch)


def test_contact_creation_normalizes_and_masks_phone(monkeypatch):
    headers = _admin(monkeypatch)
    contact = {"id": str(uuid.uuid4()), "phone_e164": "+250788123456", "bsuid": "bsuid-private",
               "display_name": "Farmer", "language": "en", "crops": [], "whatsapp_opt_in": False}
    with patch("app.routers.whatsapp_admin.crud.find_contact", return_value=None), patch(
        "app.routers.whatsapp_admin.crud.create_contact", return_value=contact
    ):
        response = client.post("/communication/contacts", headers=headers, json={
            "phone": "0788123456", "bsuid": "bsuid-private", "display_name": "Farmer",
        })
    assert response.status_code == 201
    assert response.json()["phone_masked"] == "+250•••••456"
    assert "phone_e164" not in response.text
    assert "bsuid-private" not in response.text


def test_contact_creation_rejects_invalid_phone(monkeypatch):
    response = client.post("/communication/contacts", headers=_admin(monkeypatch), json={"phone": "not-a-number"})
    assert response.status_code == 422


def test_duplicate_contact_identity_returns_conflict(monkeypatch):
    headers = _admin(monkeypatch)
    with patch("app.routers.whatsapp_admin.crud.find_contact", return_value={"id": "existing"}):
        response = client.post("/communication/contacts", headers=headers, json={"phone": "+250788123456"})
    assert response.status_code == 409


def test_opt_in_requires_source_and_wording_version(monkeypatch):
    response = client.post(
        f"/communication/contacts/{uuid.uuid4()}/opt-in",
        headers=_admin(monkeypatch),
        json={},
    )
    assert response.status_code == 422


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.filters = []

    def select(self, *_):
        return self

    def eq(self, key, value):
        self.filters.append((key, "eq", value))
        return self

    def is_(self, key, value):
        self.filters.append((key, "is", value))
        return self

    def in_(self, key, values):
        self.filters.append((key, "in", values))
        return self

    def execute(self):
        rows = self.rows
        for key, operation, value in self.filters:
            if operation == "eq":
                rows = [row for row in rows if row.get(key) == value]
            elif operation == "is":
                rows = [row for row in rows if row.get(key) is None]
            else:
                rows = [row for row in rows if row.get(key) in value]
        return _FakeResult(rows)


class _FakeClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return _FakeQuery(self.tables[name])


def test_alert_audience_excludes_missing_consent_and_opted_out(monkeypatch):
    from app.db import crud

    zone_id = str(uuid.uuid4())
    allowed = {"id": "allowed", "whatsapp_opt_in": True, "opt_out_at": None, "deleted_at": None}
    opted_out = {"id": "opted-out", "whatsapp_opt_in": True, "opt_out_at": "2026-01-01", "deleted_at": None}
    no_consent = {"id": "no-consent", "whatsapp_opt_in": False, "opt_out_at": None, "deleted_at": None}
    tables = {
        "alert_subscriptions": [
            {"contact_id": contact["id"], "zone_id": zone_id, "crop": "Maize", "min_severity": "warning"}
            for contact in (allowed, opted_out, no_consent)
        ],
        "contacts": [allowed, opted_out, no_consent],
    }
    monkeypatch.setattr(crud, "get_supabase", lambda: _FakeClient(tables))
    result = crud.list_contacts_for_alert(zone_id, "Maize", "Warning")
    assert [contact["id"] for contact in result] == ["allowed"]
