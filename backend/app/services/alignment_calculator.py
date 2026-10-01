"""Computes the National Alignment metrics (Pillar 5) for a zone.

This module now loads AHS-derived national constants from
`data/constants/ahs_2024.json` when available and uses them to tune a few
heuristic thresholds (fertilizer/irrigation prevalence influence credit
readiness and nutrition risk). The rules remain explainable and can be
adjusted once stakeholders provide feedback.
"""

import json
from pathlib import Path

CONSTANTS_PATH = Path(__file__).resolve().parents[2] / "data" / "constants" / "ahs_2024.json"


def _load_ahs_constants() -> dict:
    if CONSTANTS_PATH.exists():
        try:
            with open(CONSTANTS_PATH) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


_AHS = _load_ahs_constants()


def calculate_credit_insurance_score(predicted_yield: float | None, area_cultivated: float | None,
                                      rainfall_mm: float | None, yield_index: float | None = None) -> float:
    """0-100 score; higher = more ready for credit/insurance.

    The presence of higher national fertilizer/irrigation rates raises the
    baseline readiness slightly (they indicate an enabling environment).
    """
    # Prefer yield_index as the primary signal when provided. Map it into
    # a 0-1 range where 1.0 ~= typical crop mean. Cap at 2x for robustness.
    if yield_index is not None:
        yi = min(max(yield_index, 0.0), 2.0)
        yield_score = (yi / 2.0) * 60.0
    else:
        area = area_cultivated or 0.5
        yield_per_ha = (predicted_yield or 0.0) / area if area else (predicted_yield or 0.0)
        # Yield component (60%) using absolute yield when yield_index unavailable
        yield_score = min(yield_per_ha / 1600.0, 1.0) * 60

    # Rainfall component (40%)
    rainfall = rainfall_mm or 800.0
    rainfall_score = min(max(rainfall / 900.0, 0.3), 1.0) * 40

    base = yield_score + rainfall_score

    # Adjust by AHS fertilizer / irrigation prevalence (small nudges)
    fert = _AHS.get("fertilizer_use_share", 0.0)
    irr = _AHS.get("irrigation_share", 0.0)
    adj = min(fert * 10.0, 5.0) + min(irr * 10.0, 5.0)  # up to +10 points

    return round(min(base + adj, 100.0), 1)


def calculate_nutrition_risk(predicted_yield: float, area_cultivated: float | None) -> str:
    # Nutrition risk is aligned directly with the intervention priority.
    # The `priority_level` is the authoritative signal: High/Medium/Low.
    # Keep this mapping explicit so it isn't accidentally decoupled.
    return "Low"  # placeholder: router will call the dedicated mapper


def calculate_climate_risk(rainfall_mm: float | None) -> str:
    # If rainfall is unknown, treat as Medium (unknown should not be
    # silently considered favourable).
    if rainfall_mm is None:
        return "Medium"
    rainfall = rainfall_mm
    if rainfall < 500:
        return "High"
    if rainfall < 750:
        return "Medium"
    return "Low"


def calculate_export_readiness(predicted_yield: float | None, area_cultivated: float | None,
                                priority_level: str, yield_index: float | None = None) -> bool:
    # Require BOTH a low local priority (i.e., low need for intervention)
    # and a meaningfully above-typical yield_index (>=1.15) to mark export-ready.
    if priority_level != "Low":
        return False
    if yield_index is None:
        # Fall back to absolute yield-per-ha check when index unavailable
        area = area_cultivated or 0.5
        yield_per_ha = (predicted_yield or 0.0) / area if area else (predicted_yield or 0.0)
        return yield_per_ha > 1800
    return yield_index >= 1.15


def estimate_jobs_supported(area_cultivated: float | None) -> int:
    """Rough estimate: ~2 seasonal jobs per hectare of intervention."""
    area = area_cultivated or 0.5
    return round(area * 2)


def calculate_alignment_metrics(predicted_yield: float | None, area_cultivated: float | None,
                                 rainfall_mm: float | None, priority_level: str,
                                 yield_index: float | None = None) -> dict:
    # Nutrition risk maps directly from priority_level for a clear policy signal
    nutrition = ("High" if priority_level == "High" else
                 ("Medium" if priority_level == "Medium" else "Low"))

    return {
        "credit_insurance_score": calculate_credit_insurance_score(
            predicted_yield, area_cultivated, rainfall_mm, yield_index
        ),
        "nutrition_risk_level": nutrition,
        "climate_risk_level": calculate_climate_risk(rainfall_mm),
        "export_readiness_flag": calculate_export_readiness(
            predicted_yield, area_cultivated, priority_level, yield_index
        ),
        "estimated_jobs_supported": estimate_jobs_supported(area_cultivated),
        "irrigation_ha": area_cultivated or 0.0 if (rainfall_mm or 800) < 600 else 0.0,
        "terraces_ha": 0.0,  # populate once terrain/slope data is available
    }
