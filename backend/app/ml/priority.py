"""Deterministic, inspectable priority components shared by serving and audits."""
from __future__ import annotations

from typing import Any


def _index_priority(yield_index: float | None) -> str:
    if yield_index is None:
        return "Unknown"
    if yield_index < 0.75:
        return "High"
    if yield_index < 0.95:
        return "Medium"
    return "Low"


def baseline_priority(yield_kg_ha: float) -> str:
    """Legacy yield thresholds retained for non-model fallback."""
    if yield_kg_ha < 900:
        return "High"
    if yield_kg_ha < 1400:
        return "Medium"
    return "Low"


def classify_components(*, observed_yield: float, expected_yield: float | None,
                        residual_se: float | None, top_quartile_yield: float | None,
                        cultivated_area_ha: float | None, area_percentile: float | None,
                        yield_index: float | None, crop_district_count: int,
                        model_available: bool) -> dict[str, Any]:
    """Combine standardized shortfall, crop gap, and exposure when supported."""
    thin = crop_district_count < 10
    if thin:
        level = _index_priority(yield_index)
        return {
            "priority_level": level,
            "underlying_priority_level": level,
            "priority_status": "low_evidence",
            "low_evidence": True,
            "reasons": [f"Thin crop evidence: {crop_district_count} districts; used crop-relative yield index "
                        f"({yield_index:.3f}) only." if yield_index is not None else
                        f"Thin crop evidence: {crop_district_count} districts; crop-relative yield index is unavailable."],
            "components": {"yield_index": yield_index, "crop_district_count": crop_district_count},
        }
    if not model_available:
        level = baseline_priority(observed_yield)
        return {
            "priority_level": level,
            "underlying_priority_level": level,
            "priority_status": "baseline_fallback",
            "low_evidence": False,
            "reasons": [f"No compatible yield model; retained baseline yield threshold for {observed_yield:.1f} kg/ha."],
            "components": {"observed_yield_kg_ha": observed_yield, "baseline_rule": "<900 High; <1400 Medium; otherwise Low"},
        }

    if expected_yield is None or residual_se is None or residual_se <= 0:
        level = baseline_priority(observed_yield)
        return {
            "priority_level": level,
            "underlying_priority_level": level,
            "priority_status": "low_evidence",
            "low_evidence": True,
            "reasons": ["Model exists, but held-out residual standard deviation is unavailable; used baseline rule."],
            "components": {"observed_yield_kg_ha": observed_yield, "expected_yield_kg_ha": expected_yield,
                           "residual_standard_deviation_kg_ha": residual_se,
                           "residual_standard_error_kg_ha": residual_se},
        }

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
