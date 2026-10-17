import json

import pandas as pd

from scripts import add_new_season as routine


def test_audit_failure_does_not_train_or_change_training_data(tmp_path, monkeypatch):
    table = tmp_path / "training.csv"
    table.write_text("season,district,crop\n2025 Season A,Bugesera,Maize\n", encoding="utf-8")
    pdf = tmp_path / "season.pdf"
    pdf.write_bytes(b"pdf placeholder")
    before = table.read_bytes()
    monkeypatch.setattr(routine, "_extract_pdf_season", lambda *_: [{
        "season": "2027 Season A", "season_code": "A", "year": 2027,
        "district": "Bugesera", "crop": "Maize", "crop_category": "Cereal",
        "yield_kg_ha": 1000, "cultivated_area_ha": 1, "harvested_area_ha": 1,
        "production_mt": 1,
    }])
    monkeypatch.setattr(routine, "_audit_pdf_season", lambda *_: 1)
    monkeypatch.setattr(routine.trainer, "train", lambda *_: (_ for _ in ()).throw(AssertionError("must not train")))
    try:
        routine.add_new_season(pdf, 2027, "A", table)
    except RuntimeError as exc:
        assert "audit failed" in str(exc)
    else:
        raise AssertionError("audit failure must stop the routine")
    assert table.read_bytes() == before


def test_candidate_must_improve_mae_and_not_reduce_spearman(tmp_path, monkeypatch):
    heldout = pd.DataFrame({
        "split": ["leave_one_season_out"] * 4,
        "fold": ["2027 Season A"] * 4,
        "season": ["2027 Season A"] * 4,
        "crop": ["Beans"] * 4,
        "district": ["A", "B", "C", "D"],
        "yield_kg_ha": [100, 200, 300, 400],
    })
    historical = pd.DataFrame()
    monkeypatch.setattr(
        routine, "_previous_model_predictions",
        lambda model, *_: [110, 210, 310, 410]
        if model and model.get("model_kind") == "candidate" else [150, 250, 350, 450],
    )
    better, comparison = routine._compare_candidate(
        {"model_kind": "candidate"}, {"model_kind": "deployed"}, heldout, historical, "2027 Season A"
    )
    assert better is True
    assert comparison["decision"] == "PROMOTE"


def test_drift_report_ranks_moved_features_and_reports_season_error(tmp_path):
    full = pd.DataFrame({"season": ["old"] * 4 + ["new"] * 4,
                         "farmers_using_seed_pct": [10, 11, 9, 10, 90, 91, 89, 90],
                         "yield_kg_ha": [100, 110, 90, 100, 200, 210, 190, 200]})
    oof = pd.DataFrame({"split": ["leave_one_season_out"] * 4,
                        "fold": ["old", "new", "new", "new"],
                        "yield_kg_ha": [100, 200, 200, 200], "candidate": [110, 220, 220, 220]})
    path = tmp_path / "oof.csv"
    oof.to_csv(path, index=False)
    report = routine._drift_report(full, path, "new", "candidate")
    assert report["feature_shifts"][0]["feature"] == "farmers_using_seed_pct"
    assert report["leave_one_season_out_mae_kg_ha"]["new"] == 20
