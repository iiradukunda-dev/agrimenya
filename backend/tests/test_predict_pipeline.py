from app.ml import predict
from app.db import crud
from app.routers import segmentation


def test_predict_returns_tuple():
    total, conf, ver = predict.predict_yield(
        district=None, crop="Maize", season=None, rainfall_mm=None, area_cultivated=0.5, household_size=4
    )
    assert isinstance(total, float)
    assert conf is None or 0.0 <= conf <= 1.0
    assert isinstance(ver, str)


def test_official_yield_observations_include_historical_seasons_and_filter(monkeypatch):
    rows = [
        {
            "district": "Huye",
            "crop": "Maize",
            "season": "2022 Season A",
            "yield_kg_ha": "1200",
            "production_mt": "45",
            "cultivated_area_ha": "37.5",
            "harvested_area_ha": "36.0",
        },
        {
            "district": "Huye",
            "crop": "Maize",
            "season": "2022 Season B",
            "yield_kg_ha": "1400",
            "production_mt": "50",
            "cultivated_area_ha": "40",
            "harvested_area_ha": "39",
        },
        {
            "district": "Rubavu",
            "crop": "Beans",
            "season": "2022 Season A",
            "yield_kg_ha": "900",
            "production_mt": "20",
            "cultivated_area_ha": "22",
            "harvested_area_ha": "21",
        },
    ]
    monkeypatch.setattr(predict, "_load_official_evidence", lambda: rows)

    observations = predict.official_yield_observations(crop="maize", season="2022 season a")

    assert len(observations) == 1
    assert observations[0]["id"] == "Huye|Maize|2022 Season A"
    assert observations[0]["zones"] == {"district": "Huye"}
    assert observations[0]["yield_actual"] == "1200"
    assert observations[0]["data_source"] == "official_nisr_sas"


def test_official_yield_observations_cover_bundled_seasons():
    observations = predict.official_yield_observations()

    seasons = {row["season"] for row in observations}
    assert "2022 Season A" in seasons
    assert "2026 Season B" in seasons
    assert len(seasons) == 14


def test_official_yields_route_passes_optional_filters(monkeypatch):
    captured = {}

    def fake_observations(**filters):
        captured.update(filters)
        return [{"district": "Huye", "season": "2022 Season A"}]

    monkeypatch.setattr(segmentation, "official_yield_observations", fake_observations)

    result = segmentation.browse_official_yields(
        district="Huye", crop="Maize", season="2022 Season A",
    )

    assert captured == {
        "district": "Huye",
        "crop": "Maize",
        "season": "2022 Season A",
    }
    assert result == [{"district": "Huye", "season": "2022 Season A"}]


def test_season_specific_baselines_differ(monkeypatch):
    rows = [
        {"district": "Kigali", "crop": "Maize", "season": "2026 Season A", "yield_kg_ha": 1000,
         "production_mt": 100, "harvested_area_ha": 100},
        {"district": "Kigali", "crop": "Maize", "season": "2026 Season B", "yield_kg_ha": 9000,
         "production_mt": 900, "harvested_area_ha": 100},
    ]
    monkeypatch.setattr(predict, "_live_yield_evidence", lambda _district, _crop: rows)
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
    rows = [
        {"district": "Kigali", "crop": "Maize", "season": "2026 Season A", "yield_kg_ha": 100,
         "production_mt": 0.1, "harvested_area_ha": 1},
        {"district": "Kigali", "crop": "Maize", "season": "2026 Season B", "yield_kg_ha": 900,
         "production_mt": 8.1, "harvested_area_ha": 9},
    ]
    monkeypatch.setattr(predict, "_live_yield_evidence", lambda _district, _crop: rows)
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
