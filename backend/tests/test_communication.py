import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.alert import Severity

client = TestClient(app)


def test_create_and_list_alerts():
    zone_id = uuid.uuid4()
    payload = {"zone_id": str(zone_id), "message": "Test alert", "severity": "Warning", "created_by": "tester"}

    with patch("app.db.crud.create_alert") as mock_create, patch("app.db.crud.list_alerts") as mock_list:
        mock_create.return_value = {"id": str(uuid.uuid4()), **payload}
        mock_list.return_value = [mock_create.return_value]

        r1 = client.post("/communication/alerts", json=payload)
        assert r1.status_code == 200
        assert r1.json()["severity"] == "Warning"

        r2 = client.get(f"/communication/alerts?zone_id={zone_id}")
        assert r2.status_code == 200
        assert isinstance(r2.json(), list)


def test_invalid_severity_rejected():
    zone_id = uuid.uuid4()
    payload = {"zone_id": str(zone_id), "message": "Bad severity", "severity": "Severe", "created_by": "tester"}
    r = client.post("/communication/alerts", json=payload)
    assert r.status_code == 422


@patch("app.db.crud.list_plans")
def test_share_plan(mock_list_plans):
    plan_id = str(uuid.uuid4())
    mock_list_plans.return_value = [{"id": plan_id, "title": "P"}]
    r = client.get(f"/communication/share/{plan_id}")
    assert r.status_code == 200
    assert r.json()["id"] == plan_id


@patch("app.routers.communication.send_notification")
def test_send_notification_route(mock_send):
    mock_send.return_value = {
        "status": "queued",
        "channels": ["sms", "whatsapp"],
        "message": "Alert queued for delivery",
        "simulated": True,
    }

    payload = {
        "phone": "+250788123456",
        "email": "farmer@example.com",
        "message": "Rain expected in 2 hours.",
        "channels": ["sms", "whatsapp", "email"],
    }

    r = client.post("/communication/notify", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] == "queued"
    assert mock_send.called


@patch("app.routers.communication.send_notification")
@patch("app.db.crud.create_alert")
def test_alert_creation_triggers_notification(mock_create_alert, mock_send):
    zone_id = uuid.uuid4()
    payload = {"zone_id": str(zone_id), "message": "Flood risk detected.", "severity": "Critical", "created_by": "tester"}
    mock_create_alert.return_value = {"id": str(uuid.uuid4()), **payload}
    mock_send.return_value = {"status": "queued", "channels": ["sms"], "simulated": True}

    r = client.post("/communication/alerts", json=payload)
    assert r.status_code == 200
    assert mock_send.called
