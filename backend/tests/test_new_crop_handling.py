import json

import pandas as pd
import pytest

from app.ml import predict
from scripts.ingest_new_crop_data import ingest, validate_source


def test_unknown_crop_does_not_receive_an_unverified_category_proxy(monkeypatch):
    monkeypatch.setattr(predict, "_live_yield_evidence", lambda _district, _crop: [])
    monkeypatch.setattr(predict, "_yield_model_bundle", None)

    default = predict.predict_with_interval("Kigali", "New Bean", "Season A 2026")
    assert default["point"] is None
    assert default["basis"] == "no_data"
    assert default["thin"] is True
    assert predict.predict_yield("Kigali", "New Bean", "Season A 2026")[0] is None

    proxy_opt_in = predict.predict_with_interval("Kigali", "New Bean", "Season A 2026",
                                                 allow_category_proxy=True, crop_category="Legume")
    assert proxy_opt_in["point"] is None
    assert proxy_opt_in["basis"] == "no_data"


def test_ingest_validates_then_appends_and_rebuilds_baseline(tmp_path):
    table_path = tmp_path / "training_table.csv"
    baseline_path = tmp_path / "yield_baselines.json"
    source_path = tmp_path / "extension.csv"
    pd.DataFrame([{"district": "Bugesera", "season": "2026 Season A", "yield_kg_ha": 2100}]).to_csv(source_path, index=False)
    pd.DataFrame([{"district": "Bugesera", "crop": "Maize", "crop_category": "Cereal",
                   "season": "2025 Season A", "season_code": "A", "year": 2025,
                   "yield_kg_ha": 1200, "harvested_area_ha": 1, "production_mt": 1.2}]).to_csv(table_path, index=False)
    result = ingest(source_path, "New Bean", "Legume", table_path, baseline_path)
    assert result["rows_added"] == 1
    assert result["districts_observed"] == 1 and result["thin"]
    combined = pd.read_csv(table_path)
    assert combined.iloc[-1]["data_source"] == "extension_survey"
    baseline = json.loads(baseline_path.read_text())
    assert baseline["extension_district_crop_season_averages"]["Bugesera|New Bean|A"] == 2100


@pytest.mark.parametrize("district,season,yield_value", [
    ("Atlantis", "2026 Season A", 1000),
    ("Bugesera", "rainy season", 1000),
    ("Bugesera", "2026 Season A", 0),
    ("Bugesera", "2026 Season A", 1_000_001),
])
def test_ingest_rejects_unknown_district_invalid_season_or_yield(tmp_path, district, season, yield_value):
    path = tmp_path / "input.csv"
    pd.DataFrame([{"district": district, "season": season, "yield_kg_ha": yield_value}]).to_csv(path, index=False)
    existing = pd.DataFrame([{"district": "Bugesera"}])
    with pytest.raises(ValueError):
        validate_source(path, "New Bean", "Legume", existing)
