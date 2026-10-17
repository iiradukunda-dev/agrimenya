import pandas as pd

from app.ml.explain import ExplanationService
from app.services.recommendation_engine import get_recommendations


def test_low_improved_seed_use_recommends_seed_access(tmp_path):
    rows = []
    for index in range(30):
        rows.append({
            "season": "2026 Season A", "season_code": "A", "year": 2026,
            "district": f"District {index:02d}", "crop": "Maize", "crop_category": "Cereal",
            "yield_kg_ha": 500 + index * 75, "cultivated_area_ha": 10,
            "harvested_area_ha": 8, "production_mt": (500 + index * 75) * 8 / 1000,
            "farmers_using_improved_seeds_pct": 10 + index * 2.5,
        })
    rows.append({
        "season": "2026 Season A", "season_code": "A", "year": 2026,
        "district": "Target District", "crop": "Maize", "crop_category": "Cereal",
        "yield_kg_ha": 700, "cultivated_area_ha": 10,
        "harvested_area_ha": 8, "production_mt": 5.6,
        "farmers_using_improved_seeds_pct": 2,
    })
    data_path = tmp_path / "training_table.csv"
    pd.DataFrame(rows).to_csv(data_path, index=False)

    explanation = ExplanationService(data_path).explain(
        "Target District", "Maize", "Season A 2026"
    )
    assert explanation["data_status"] == "sourced"
    seed_factor = next(f for f in explanation["factors"]
                       if f["feature"] == "farmers_using_improved_seeds_pct")
    assert seed_factor["peer_direction"] == "below_peers"

    recommendations = get_recommendations("High", None, None, explanation["factors"])
    assert any("seed access" in recommendation.lower() for recommendation in recommendations)
    assert "not proven causes" in explanation["interpretation_note"]
