import uuid
from unittest.mock import patch

from app.main import app
from fastapi.testclient import TestClient

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
