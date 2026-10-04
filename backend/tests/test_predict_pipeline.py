from app.ml import predict
from app.db import crud


def test_predict_returns_tuple():
    total, conf, ver = predict.predict_yield(
        district=None, crop="Maize", season=None, rainfall_mm=None, area_cultivated=0.5, household_size=4
    )
    assert isinstance(total, float)
    assert 0.0 <= conf <= 1.0
    assert isinstance(ver, str)


def test_save_prediction_filters_analysis_fields(monkeypatch):
    captured = {}

    class FakeInsert:
        def __init__(self, payload):
            captured["payload"] = payload

        def execute(self):
            return type("Resp", (), {"data": [captured["payload"]]})()

    class FakeTable:
        def __init__(self):
            self.payload = None

        def insert(self, payload):
            self.payload = payload
            return FakeInsert(payload)

    class FakeClient:
        def table(self, name):
            assert name == "predictions"
            return FakeTable()

    monkeypatch.setattr(crud, "get_supabase", lambda: FakeClient())

    payload = {
        "zone_id": "123e4567-e89b-12d3-a456-426614174000",
        "season": "Season A 2026",
        "crop": "Maize",
        "predicted_yield": 5200.0,
        "priority_level": "High",
        "confidence": 0.85,
        "model_version": "xgboost-v1-test",
        "yield_per_ha": 2500.0,
        "yield_gap_kg_ha": 300.0,
    }

    res = crud.save_prediction(payload)

    assert set(res.keys()) == {
        "zone_id",
        "season",
        "crop",
        "predicted_yield",
        "priority_level",
        "confidence",
        "model_version",
    }
    assert "yield_per_ha" not in res
    assert "yield_gap_kg_ha" not in res
