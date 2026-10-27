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


def test_estimate_resources_reports_priced_items_when_other_prices_are_missing():
    result = estimate_resources(
        2.0,
        seed_rate_kg_ha=10.0,
        seed_price_rwf_kg=500.0,
        dap_rate_kg_ha=5.0,
        land_preparation_cost_rwf_ha=1000.0,
    )

    assert result["status"] == "partial"
    assert result["quantities"]["seeds_kg"] == 20.0
    assert result["quantities"]["dap_kg"] == 10.0
    assert result["costs_rwf"]["seeds"] == 10000.0
    assert result["costs_rwf"]["land_preparation"] == 2000.0
    assert result["estimated_cost_rwf"] is None
    assert result["missing_inputs"] == ["dap_price_rwf_kg"]


def test_estimate_resources_accepts_multiple_named_fertilizers_and_units():
    result = estimate_resources(
        1.5,
        fertilizer_items=[
            {"name": "NPK 17-17-17", "rate_per_ha": 200, "unit": "kg", "price_per_unit": 900},
            {"name": "Compost", "rate_per_ha": 2, "unit": "tonnes", "price_per_unit": None},
        ],
    )

    assert result["status"] == "partial"
    assert result["fertilizer_items"][0]["quantity"] == 300
    assert result["fertilizer_items"][0]["estimated_cost_rwf"] == 270000
    assert result["fertilizer_items"][1]["quantity"] == 3
    assert result["fertilizer_items"][1]["missing_price"] is True
    assert result["quantities"]["fertilizer_kg"] == 3300
    assert result["missing_inputs"] == ["fertilizer price (Compost)"]


@patch("app.db.crud.get_zone")
@patch("app.db.crud.list_plans", return_value=[])
@patch("app.db.crud.create_plan")
def test_plan_roundtrip(mock_create_plan, mock_list_plans, mock_get_zone):
    # setup
    zone_id = uuid.uuid4()
    mock_get_zone.return_value = {"id": str(zone_id), "district": "Gasabo"}
    mock_create_plan.return_value = {"id": str(uuid.uuid4()), "zone_id": str(zone_id)}

    roadmap = [
        {"step_number": 1, "title": "Test", "description": "Do X", "due_date": "2026-11-01"}
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
    saved_step = mock_create_plan.call_args.args[0]["roadmap_json"][0]
    assert saved_step["status"] == "planned"
    assert saved_step["due_date"] == "2026-11-01"

    # verify get plans forwards to crud.list_plans (we can't patch it easily here but ensure endpoint exists)
    resp2 = client.get(f"/planification/plans/{zone_id}")
    assert resp2.status_code == 200
    assert resp2.json() == []
    mock_list_plans.assert_called_once()


@patch("app.routers.planification.build_seasonal_draft")
@patch("app.routers.planification.crud.get_zone")
def test_seasonal_draft_uses_saved_zone_context(mock_get_zone, mock_build_draft):
    zone_id = uuid.uuid4()
    mock_get_zone.return_value = {
        "id": str(zone_id), "district": "Gasabo", "area_cultivated": 2.5,
    }
    mock_build_draft.return_value = {"status": "ready", "roadmap": []}

    response = client.get(
        f"/planification/draft?zone_id={zone_id}&crop=Maize"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    mock_build_draft.assert_called_once_with(
        district="Gasabo", crop="Maize", area_ha=2.5,
    )


@patch("app.routers.planification.crud.get_zone", return_value=None)
def test_seasonal_draft_rejects_unknown_zone(mock_get_zone):
    response = client.get(
        f"/planification/draft?zone_id={uuid.uuid4()}&crop=Maize"
    )

    assert response.status_code == 404


@patch("app.routers.planification.crud.get_zone")
def test_resource_estimate_accepts_named_fertilizer_products(mock_get_zone):
    zone_id = uuid.uuid4()
    mock_get_zone.return_value = {"id": str(zone_id)}
    response = client.post(
        f"/planification/resources/{zone_id}/estimate",
        json={
            "area_cultivated": 2,
            "inputs": {},
            "fertilizer_items": [
                {"name": "NPK", "rate_per_ha": 100, "unit": "kg", "price_per_unit": 800},
                {"name": "Liquid feed", "rate_per_ha": 10, "unit": "litres"},
            ],
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["fertilizer_items"][0]["quantity"] == 200
    assert result["fertilizer_items"][0]["estimated_cost_rwf"] == 160000
    assert result["fertilizer_items"][1]["quantity"] == 20
    assert result["fertilizer_items"][1]["missing_price"] is True
    assert result["status"] == "partial"


@patch("app.routers.planification.crud.get_zone")
def test_resource_estimate_rejects_unknown_input_keys(mock_get_zone):
    zone_id = uuid.uuid4()
    mock_get_zone.return_value = {"id": str(zone_id)}
    response = client.post(
        f"/planification/resources/{zone_id}/estimate",
        json={"area_cultivated": 1, "inputs": {"unknown_cost": 50}},
    )

    assert response.status_code == 422
