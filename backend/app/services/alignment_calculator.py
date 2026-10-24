"""Return unavailable alignment estimates until validated data and methods exist."""

def calculate_credit_insurance_score(predicted_yield: float | None, area_cultivated: float | None,
                                      rainfall_mm: float | None, yield_index: float | None = None) -> None:
    """No validated credit or insurance scoring method is configured."""
    return None


def calculate_nutrition_risk(predicted_yield: float, area_cultivated: float | None) -> None:
    """Yield alone is insufficient to determine household nutrition risk."""
    return None


def calculate_climate_risk(rainfall_mm: float | None) -> None:
    """A point rainfall observation is not a validated climate-risk measure."""
    return None


def calculate_export_readiness(predicted_yield: float | None, area_cultivated: float | None,
                                priority_level: str, yield_index: float | None = None) -> None:
    """Export compliance requires commodity and regulatory data not present here."""
    return None


def estimate_jobs_supported(area_cultivated: float | None) -> None:
    """No sourced jobs-per-hectare coefficient is configured."""
    return None


def calculate_alignment_metrics(predicted_yield: float | None, area_cultivated: float | None,
                                 rainfall_mm: float | None, priority_level: str,
                                 yield_index: float | None = None) -> dict:
    return {
        "credit_insurance_score": calculate_credit_insurance_score(
            predicted_yield, area_cultivated, rainfall_mm, yield_index
        ),
        "nutrition_risk_level": None,
        "climate_risk_level": calculate_climate_risk(rainfall_mm),
        "export_readiness_flag": calculate_export_readiness(
            predicted_yield, area_cultivated, priority_level, yield_index
        ),
        "estimated_jobs_supported": estimate_jobs_supported(area_cultivated),
        "irrigation_ha": None,
        "terraces_ha": None,
    }
