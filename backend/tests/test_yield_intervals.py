import math

from app.ml.intervals import conformal_quantile, log_interval
from app.ml.predict import predict_with_interval


def test_log_interval_contains_point_and_is_ordered():
    low, high = log_interval(1200.0, 0.7)
    assert low < 1200.0 < high


def test_conformal_interval_width_shrinks_with_more_representative_data():
    sparse_q = conformal_quantile([0.1, 0.2, 1.2, 1.3], 0.8)
    fuller_q = conformal_quantile([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], 0.8)
    sparse = log_interval(1000.0, sparse_q)
    fuller = log_interval(1000.0, fuller_q)
    assert (fuller[1] - fuller[0]) < (sparse[1] - sparse[0])


def test_serving_interval_contains_point_and_marks_thin_crop(monkeypatch, tmp_path):
    monkeypatch.setattr("app.ml.predict._yield_model_bundle", None)
    monkeypatch.setattr("app.ml.predict.ARTIFACTS_DIR", tmp_path)
    monkeypatch.setattr("app.ml.predict._live_yield_evidence", lambda _district, _crop: [{
        "district": "Kigali", "crop": "Maize", "season": "2026 Season A",
        "yield_kg_ha": 1000, "production_mt": 100, "harvested_area_ha": 100,
    }])
    result = predict_with_interval("Kigali", "Maize", "Season A 2026")
    assert result["low"] < result["point"] < result["high"]
    assert result["basis"] == "district_crop_baseline"
    assert result["insufficient_data"] is True
    assert math.isfinite(result["point"])
