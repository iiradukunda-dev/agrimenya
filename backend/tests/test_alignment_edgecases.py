from app.services.alignment_calculator import (
    calculate_credit_insurance_score,
    calculate_climate_risk,
    calculate_export_readiness,
    calculate_alignment_metrics,
)


def test_credit_score_is_unavailable_without_validated_method():
    assert calculate_credit_insurance_score(2000.0, 1.0, 800.0, 1.5) is None


def test_climate_risk_is_unavailable_without_validated_method():
    assert calculate_climate_risk(None) is None


def test_export_readiness_is_unavailable_without_compliance_evidence():
    assert calculate_export_readiness(2000.0, 1.0, "Low", 1.2) is None


def test_alignment_estimates_are_unavailable_without_validated_methods():
    m = calculate_alignment_metrics(2000.0, 1.0, None, "High", 1.0)
    assert m["nutrition_risk_level"] is None
    assert m["climate_risk_level"] is None
    assert m["export_readiness_flag"] is None
    assert m["estimated_jobs_supported"] is None
