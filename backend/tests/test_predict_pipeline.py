from app.ml import predict
from app.db import crud


def test_predict_returns_tuple():
    total, conf, ver = predict.predict_yield(
        district=None, crop="Maize", season=None, rainfall_mm=None, area_cultivated=0.5, household_size=4
    )
    assert isinstance(total, float)
    assert 0.0 <= conf <= 1.0
    assert isinstance(ver, str)


def test_season_specific_baselines_differ(monkeypatch):
    monkeypatch.setattr(predict, "_baselines", {
        "schema_version": 2,
        "district_crop_season_weighted_averages": {"Kigali|Maize|A": 1000.0, "Kigali|Maize|B": 9000.0},
        "district_crop_weighted_averages": {"Kigali|Maize": 5000.0},
        "crop_season_weighted_averages": {"Maize|A": 1000.0, "Maize|B": 9000.0},
        "crop_weighted_averages": {"Maize": 5000.0},
    })
    monkeypatch.setattr(predict, "_yield_model_bundle", None)
    assert predict.get_yield_per_hectare("Kigali", "Maize", "Season A 2026") == 1000.0
    assert predict.get_yield_per_hectare("Kigali", "Maize", "Season B 2026") == 9000.0
    season_a_total, _, _ = predict.predict_yield("Kigali", "Maize", "Season A 2026", None, 1.0, None)
    season_b_total, _, _ = predict.predict_yield("Kigali", "Maize", "Season B 2026", None, 1.0, None)
    assert season_a_total == 1000.0
    assert season_b_total == 9000.0


def test_season_none_uses_area_weighted_combination(monkeypatch):
    # Hand calculation: (100 kg + 8,100 kg) / (1 ha + 9 ha) = 820 kg/ha.
    from scripts.build_yield_baseline import build

    payload = build([
        {"district": "Kigali", "crop": "Maize", "season_code": "A", "yield_kg_ha": "100",
         "harvested_area_ha": "1", "production_mt": "0.1"},
        {"district": "Kigali", "crop": "Maize", "season_code": "B", "yield_kg_ha": "900",
         "harvested_area_ha": "9", "production_mt": "8.1"},
    ])
    monkeypatch.setattr(predict, "_baselines", payload)
    monkeypatch.setattr(predict, "_yield_model_bundle", None)
    assert payload["legacy_simple_mean_district_crop_averages"]["Kigali|Maize"] == 500.0
    assert predict.get_yield_per_hectare("Kigali", "Maize") == 820.0
    assert predict.predict_yield("Kigali", "Maize", area_cultivated=1.0)[0] == 820.0


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
