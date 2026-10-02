import uuid
from unittest.mock import patch

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_compute_alignment_and_endpoints():
    zone_id = str(uuid.uuid4())
    payload = {
        "season": "2026-S1",
        "predicted_yield": 2000.0,
        "area_cultivated": 1.0,
        "rainfall_mm": None,
        "priority_level": "Low",
        "crop": "maize",
        "district": "Gasabo",
    }

    with patch("app.db.crud.get_zone") as mock_get_zone, \
         patch("app.db.crud.upsert_alignment_metric") as mock_upsert, \
         patch("app.db.crud.get_alignment_metric") as mock_get_metric, \
         patch("app.db.crud.list_alignment_metrics") as mock_list_metrics, \
         patch("app.ml.predict.get_yield_index") as mock_get_yi:
        mock_get_zone.return_value = {"id": zone_id}
        mock_get_yi.return_value = 1.2
        mock_upsert.return_value = {"zone_id": zone_id, "credit_insurance_score": 50}
        mock_get_metric.return_value = {"zone_id": zone_id, "credit_insurance_score": 55, "nutrition_risk_level": "Low", "climate_risk_level": "Medium", "export_readiness_flag": True}
        mock_list_metrics.return_value = [mock_get_metric.return_value]

        # Filter out None values so FastAPI doesn't receive empty query values
        params = {k: v for k, v in payload.items() if v is not None}
        r = client.post(f"/alignment/compute/{zone_id}", params=params)
        assert r.status_code == 200

        r2 = client.get(f"/alignment/finance-readiness/{zone_id}")
        assert r2.status_code == 200
        assert "credit_insurance_score" in r2.json()

        r3 = client.get(f"/alignment/nutrition-risk/{zone_id}")
        assert r3.status_code == 200
        assert "nutrition_risk_level" in r3.json()

        r4 = client.get("/alignment/export-flags")
        assert r4.status_code == 200
        assert isinstance(r4.json(), list)

        r5 = client.get("/alignment/dashboard")
        assert r5.status_code == 200
