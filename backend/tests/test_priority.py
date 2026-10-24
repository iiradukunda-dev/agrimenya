from app.ml.priority import apply_stability, classify_components


def _model_priority(*, actual, expected, se, top, area_percentile):
    return classify_components(
        observed_yield=actual, expected_yield=expected, residual_se=se,
        top_quartile_yield=top, cultivated_area_ha=100.0,
        area_percentile=area_percentile, yield_index=0.8, yield_percentile=20,
        crop_district_count=20, model_available=True,
    )


def test_underperformance_in_standard_error_units_can_raise_priority():
    result = _model_priority(actual=700, expected=1000, se=100, top=1100, area_percentile=0.2)
    assert result["priority_level"] == "High"
    assert result["components"]["underperformance_standard_errors"] == -3.0
    assert any("standard errors" in reason for reason in result["reasons"])


def test_absolute_top_quartile_gap_contributes_to_priority():
    result = _model_priority(actual=1400, expected=1400, se=300, top=2000, area_percentile=0.2)
    assert result["components"]["absolute_gap_to_top_quartile_kg_ha"] == 600
    assert result["components"]["component_scores"]["absolute_gap"] == 2
    assert result["priority_level"] == "Medium"


def test_cultivated_area_exposure_can_raise_urgency():
    low_exposure = _model_priority(actual=850, expected=1000, se=100, top=1000, area_percentile=0.5)
    high_exposure = _model_priority(actual=850, expected=1000, se=100, top=1000, area_percentile=0.8)
    assert low_exposure["priority_level"] == "Medium"
    assert high_exposure["priority_level"] == "High"
    assert any("proxy" in reason for reason in high_exposure["reasons"])


def test_thin_crop_uses_only_yield_index_and_marks_low_evidence():
    result = classify_components(
        observed_yield=2500, expected_yield=1000, residual_se=50,
        top_quartile_yield=4000, cultivated_area_ha=1000, area_percentile=1.0,
        yield_index=0.7, yield_percentile=10, crop_district_count=8, model_available=True,
    )
    assert result["priority_level"] == "High"
    assert result["low_evidence"] is True
    assert result["components"]["district_yield_percentile"] == 10
    assert result["components"]["crop_district_count"] == 8


def test_no_model_uses_same_crop_observation_percentile():
    result = classify_components(
        observed_yield=800, expected_yield=None, residual_se=None,
        top_quartile_yield=2000, cultivated_area_ha=5, area_percentile=0.5,
        yield_index=0.9, yield_percentile=20, crop_district_count=15, model_available=False,
    )
    assert result["priority_level"] == "High"
    assert result["priority_status"] == "nisr_percentile_baseline"


def test_fold_disagreement_marks_priority_uncertain():
    result = apply_stability({"priority_level": "Medium", "underlying_priority_level": "Medium",
                              "priority_status": "evaluated", "low_evidence": False,
                              "reasons": []}, ["High", "Low", "High"])
    assert result["priority_level"] == "Uncertain"
    assert result["priority_status"] == "uncertain"
    assert result["priority_changes_across_folds"] == 2
