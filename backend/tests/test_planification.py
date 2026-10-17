import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.resource_estimator import estimate_resources

client = TestClient(app)


def test_estimate_resources_defaults():
    r = estimate_resources(None, None)
    assert r["status"] == "needs_inputs"
    assert r["estimated_cost_rwf"] is None
    assert r["missing_inputs"] == ["area_cultivated"]


@patch("app.db.crud.get_zone")
@patch("app.db.crud.list_plans", return_value=[])
@patch("app.db.crud.create_plan")
def test_plan_roundtrip(mock_create_plan, mock_list_plans, mock_get_zone):
    # setup
    zone_id = uuid.uuid4()
    mock_get_zone.return_value = {"id": str(zone_id), "district": "Gasabo"}
    mock_create_plan.return_value = {"id": str(uuid.uuid4()), "zone_id": str(zone_id)}

    roadmap = [
        {"step_number": 1, "title": "Test", "description": "Do X"}
    ]
    resources = {"seeds_kg": 10.0, "fertilizer_kg": 20.0, "irrigation_liters": 0.0, "estimated_cost_rwf": 1000}
    payload = {
        "zone_id": str(zone_id),
        "title": "My Plan",
        "roadmap": roadmap,
        "resources": resources,
        "created_by": "tester",
    }

    resp = client.post("/planification/roadmap", json=payload)
    assert resp.status_code == 200
    mock_create_plan.assert_called_once()

    # verify get plans forwards to crud.list_plans (we can't patch it easily here but ensure endpoint exists)
    resp2 = client.get(f"/planification/plans/{zone_id}")
    assert resp2.status_code == 200
    assert resp2.json() == []
    mock_list_plans.assert_called_once()
