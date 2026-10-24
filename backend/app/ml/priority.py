"""Deterministic, inspectable priority components shared by serving and audits."""
from __future__ import annotations

from typing import Any


def _percentile_priority(yield_percentile: float | None) -> str:
    if yield_percentile is None:
        return "Unknown"
    if yield_percentile < 25:
        return "High"
    if yield_percentile < 50:
        return "Medium"
    return "Low"


def _relative_priority_result(yield_index: float | None, yield_percentile: float | None,
                              crop_district_count: int,
                              status: str) -> dict[str, Any]:
    """Rank against observed same-crop district yields, never unlike crops by kg/ha."""
    level = _percentile_priority(yield_percentile)
    if yield_percentile is None:
        reason = "No comparable same-crop district distribution is available; priority is unknown."
    else:
        reason = (
            f"Yield is at the {yield_percentile:.0f}th percentile among districts for the same crop and season. "
            "Rule: High below the 25th percentile, Medium from the 25th to below the 50th, Low at or above the 50th."
        )
    return {
        "priority_level": level,
        "underlying_priority_level": level,
        "priority_status": status if yield_percentile is not None else "no_yield_data",
        "low_evidence": crop_district_count < 10 or yield_percentile is None,
        "reasons": [reason],
        "components": {
            "district_to_crop_mean_ratio": round(yield_index, 4) if yield_index is not None else None,
            "district_yield_percentile": round(yield_percentile, 2) if yield_percentile is not None else None,
            "crop_district_count": crop_district_count,
            "rule": "High < P25; Medium P25 to < P50; Low >= P50",
        },
    }


def classify_components(*, observed_yield: float, expected_yield: float | None,
                        residual_se: float | None, top_quartile_yield: float | None,
                        cultivated_area_ha: float | None, area_percentile: float | None,
                        yield_index: float | None, yield_percentile: float | None = None,
                        crop_district_count: int,
                        model_available: bool) -> dict[str, Any]:
    """Combine standardized shortfall, crop gap, and exposure when supported."""
    thin = crop_district_count < 10
    if thin:
        result = _relative_priority_result(yield_index, yield_percentile, crop_district_count, "low_evidence")
        result["reasons"].insert(0, f"Thin evidence: only {crop_district_count} districts have observations for this crop.")
        return result
    if not model_available:
        return _relative_priority_result(yield_index, yield_percentile, crop_district_count, "nisr_percentile_baseline")

    if expected_yield is None or residual_se is None or residual_se <= 0:
        result = _relative_priority_result(yield_index, yield_percentile, crop_district_count, "low_evidence")
        result["reasons"].insert(0, "A calibrated residual scale is unavailable; used the NISR crop-relative baseline rule.")
        result["components"].update({"observed_yield_kg_ha": observed_yield,
                                     "expected_yield_kg_ha": expected_yield,
                                     "residual_standard_deviation_kg_ha": residual_se})
        return result

    # The supplied quantity is the standard deviation of held-out residuals,
    # not the standard error of a mean. Report standardized residual units.
    z_score = (observed_yield - expected_yield) / residual_se
    absolute_gap = max(0.0, (top_quartile_yield or observed_yield) - observed_yield)
    gap_ratio = absolute_gap / top_quartile_yield if top_quartile_yield and top_quartile_yield > 0 else 0.0
    under_score = 2 if z_score <= -2 else 1 if z_score <= -1 else 0
    gap_score = 2 if gap_ratio >= 0.25 else 1 if gap_ratio >= 0.10 else 0
    exposure_score = 2 if area_percentile is not None and area_percentile >= 0.75 else 1 if area_percentile is not None and area_percentile >= 0.40 else 0
    total = under_score + gap_score + exposure_score
    level = "High" if total >= 4 else "Medium" if total >= 2 else "Low"
    reasons = [f"Yield is {z_score:.2f} held-out residual standard deviations (standard errors) from model expectation ({observed_yield:.1f} vs {expected_yield:.1f} kg/ha)."]
    reasons.append(f"Gap to crop top-quartile yield is {absolute_gap:.1f} kg/ha ({gap_ratio:.0%} of the benchmark).")
    reasons.append("Cultivated area is used as a proxy for the number of farmers exposed; "
                   + (f"its district-crop percentile is {area_percentile:.0%}." if area_percentile is not None else "area percentile is unavailable."))
    return {
        "priority_level": level, "underlying_priority_level": level,
        "priority_status": "evaluated", "low_evidence": False, "reasons": reasons,
        "components": {"underperformance_residual_standard_deviations": round(z_score, 3),
                       # Keep the former key for clients while emitting the accurate unit above.
                       "underperformance_standard_errors": round(z_score, 3),
                       "observed_yield_kg_ha": round(observed_yield, 1),
                       "expected_yield_kg_ha": round(expected_yield, 1),
                       "residual_standard_deviation_kg_ha": round(residual_se, 1),
                       "absolute_gap_to_top_quartile_kg_ha": round(absolute_gap, 1),
                       "top_quartile_yield_kg_ha": top_quartile_yield,
                       "cultivated_area_ha": cultivated_area_ha,
                       "area_percentile": area_percentile,
                       "component_scores": {"underperformance": under_score, "absolute_gap": gap_score,
                                            "exposure": exposure_score}, "combined_score": total},
    }


def apply_stability(result: dict[str, Any], fold_priorities: list[str] | None) -> dict[str, Any]:
    """Mark priorities uncertain when grouped held-out folds disagree."""
    fold_labels = [label for label in (fold_priorities or []) if label in {"High", "Medium", "Low"}]
    labels = list(dict.fromkeys(fold_labels))
    result["fold_priorities"] = fold_labels
    result["priority_changes_across_folds"] = sum(a != b for a, b in zip(fold_labels, fold_labels[1:]))
    if len(labels) > 1:
        result["priority_level"] = "Uncertain"
        result["priority_status"] = "uncertain"
        result["low_evidence"] = True
        result["reasons"].append("Priority changed across grouped training folds: " + ", ".join(labels) + ".")
    return result
