from app.services.alignment_calculator import (
    calculate_alignment_metrics,
    calculate_climate_risk,
    calculate_credit_insurance_score,
    calculate_export_readiness,
)


def test_credit_score_prefers_yield_index():
    # when yield_index provided, ensure it's used
    s_without = calculate_credit_insurance_score(2000.0, 1.0, 800.0, None)
    s_with = calculate_credit_insurance_score(None, None, None, 1.5)
    assert s_with != s_without


def test_climate_risk_none_is_medium():
    assert calculate_climate_risk(None) == "Medium"


def test_export_readiness_requires_both():
    # low priority but low index -> not ready
    assert calculate_export_readiness(2000.0, 1.0, "Low", 1.0) is False
    # low priority and index high enough -> ready
    assert calculate_export_readiness(2000.0, 1.0, "Low", 1.2) is True
    # high index but priority not Low -> not ready
    assert calculate_export_readiness(2000.0, 1.0, "High", 1.3) is False


def test_nutrition_maps_from_priority():
    # Use calculate_alignment_metrics which maps nutrition from priority
    m = calculate_alignment_metrics(2000.0, 1.0, None, "High", 1.0)
    assert m["nutrition_risk_level"] == "High"
    m2 = calculate_alignment_metrics(2000.0, 1.0, None, "Low", 1.2)
    assert m2["nutrition_risk_level"] == "Low"
