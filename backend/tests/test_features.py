import pandas as pd

from app.ml.features import build_features, build_previous_season_yield_lag, build_serving_features


def sample_frame():
    return pd.DataFrame([
        {"district": "Kigali", "crop": "Maize", "crop_category": "Cereal", "season_code": "A",
         "year": 2025, "cultivated_area_ha": 10.0, "yield_kg_ha": 1000.0,
         "production_mt": 10.0, "harvested_area_ha": 10.0, "farmers_using_improved_seeds_pct": 35.0},
        {"district": "Kigali", "crop": "Beans", "crop_category": "Legume", "season_code": "A",
         "year": 2025, "cultivated_area_ha": 30.0, "yield_kg_ha": 500.0,
         "production_mt": 15.0, "harvested_area_ha": 20.0, "farmers_using_improved_seeds_pct": 35.0},
    ])


def test_feature_values_do_not_change_when_targets_change():
    frame = sample_frame()
    changed = frame.copy()
    changed["yield_kg_ha"] = [999999, 0]
    changed["production_mt"] = [0, 999999]
    pd.testing.assert_frame_equal(build_features(frame), build_features(changed))


def test_production_yield_and_harvested_area_are_not_features():
    features = build_features(sample_frame())
    assert not any(any(token in column for token in ("yield", "production", "harvested_area")) for column in features)


def test_previous_season_lag_requires_previous_season_in_training_frame():
    train = pd.DataFrame([{
        "district": "Kigali", "crop": "Maize", "season_code": "A", "year": 2025, "yield_kg_ha": 1200.0,
    }])
    request = pd.DataFrame([{
        "district": "Kigali", "crop": "Maize", "season_code": "B", "year": 2025, "yield_kg_ha": 9999.0,
    }])
    assert build_previous_season_yield_lag(train, request).iloc[0] == 1200.0
    assert pd.isna(build_previous_season_yield_lag(request, request).iloc[0])


def test_unseen_categories_become_nan():
    features = build_features(
        pd.DataFrame([{"district": "New District", "crop": "New Crop", "season_code": "B", "year": 2026}]),
        known_categories={"district": ["Kigali"], "crop": ["Maize"], "season_code": ["A"]},
    )
    assert pd.isna(features.loc[0, "district"])
    assert pd.isna(features.loc[0, "crop"])
    assert pd.isna(features.loc[0, "season_code"])


def test_area_aggregates_use_only_cultivated_area():
    frame = sample_frame()
    baseline = build_features(frame)
    frame["yield_kg_ha"] *= 50
    frame["production_mt"] = 0
    changed = build_features(frame)
    assert baseline["district_total_cultivated_area_ha"].tolist() == [40.0, 40.0]
    assert baseline["district_cultivated_area_share"].tolist() == [0.25, 0.75]
    pd.testing.assert_series_equal(baseline["district_cultivated_area_share"], changed["district_cultivated_area_share"])


def test_training_and_serving_use_same_feature_builder(tmp_path):
    table = sample_frame()
    path = tmp_path / "training_table.csv"
    table.to_csv(path, index=False)
    categories = {"district": ["Kigali"], "crop": ["Maize", "Beans"],
                  "crop_category": ["Cereal", "Legume"], "season_code": ["A"]}
    served = build_serving_features("Kigali", "Maize", "Season A 2025", 10.0, categories, path)
    trained = build_features(table.iloc[[0]], categories, table)
    assert served.columns.tolist() == trained.columns.tolist()
    assert served.loc[0, "district_cultivated_area_share"] == trained.loc[0, "district_cultivated_area_share"] == 0.25


def test_serving_feature_values_equal_features_for_same_training_row(tmp_path):
    table = sample_frame()
    path = tmp_path / "training_table.csv"
    table.to_csv(path, index=False)
    categories = {"district": ["Kigali", "Huye"], "crop": ["Maize", "Beans"],
                  "crop_category": ["Cereal", "Legume"], "season_code": ["A"]}
    row = table.iloc[0]
    served = build_serving_features(row.district, row.crop, "Season A 2025",
                                    float(row.cultivated_area_ha), categories, path)
    trained = build_features(table.iloc[[0]], categories, table)
    pd.testing.assert_frame_equal(served.reset_index(drop=True), trained.reset_index(drop=True))
