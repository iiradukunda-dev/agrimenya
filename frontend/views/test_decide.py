from views.decide import _available_ranking_seasons, _evaluation_rows


def test_available_ranking_seasons_uses_backend_season_values():
    options = _available_ranking_seasons({
        "available_seasons": ["2022 Season A", "2026 Season B", "2022 Season A"],
    })

    assert options == [
        "All available seasons",
        "2026 Season B",
        "2022 Season A",
    ]


def test_evaluation_rows_uses_reported_metrics_without_fabricated_scores():
    rows = _evaluation_rows({
        "metrics": {
            "leave_one_season_out": {
                "crop_mean": {
                    "n": 20,
                    "coverage": 0.9,
                    "mae_kg_ha": 120.5,
                    "rmse_kg_ha": 220.0,
                    "r2": 0.75,
                },
                "not_evaluated": {"n": 0, "coverage": 0, "mae_kg_ha": None},
            },
        },
    })

    assert rows == [{
        "Evaluation split": "Leave One Season Out",
        "Candidate": "Crop Mean",
        "Observations": 20,
        "Coverage": 0.9,
        "MAE (kg/ha)": 120.5,
        "RMSE (kg/ha)": 220.0,
        "R²": 0.75,
    }]
