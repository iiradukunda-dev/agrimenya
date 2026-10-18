"""
Turns a priority level + zone metrics into concrete recommendations.
Rule-based today; can be extended to pull from an LLM or a richer
rules table without changing the calling code in routers/decision.py.
"""


def get_recommendations(priority_level: str, rainfall_mm: float | None,
                         soil_type: str | None,
                         factors: list[dict] | None = None) -> list[str]:
    recs: list[str] = []

    if priority_level == "High":
        recs.append("Prioritize this zone for immediate extension officer visit and resource allocation.")
        recs.append("Assess irrigation feasibility given current yield gap.")
    elif priority_level == "Medium":
        recs.append("Schedule a routine extension visit within the season.")
        recs.append("Monitor rainfall trends; flag for re-assessment if conditions worsen.")
    else:
        recs.append("Maintain current practices; zone is performing within expected range.")

    if rainfall_mm is not None and rainfall_mm < 600:
        recs.append("Low rainfall detected - consider drought-resistant crop varieties or supplemental irrigation.")

    if soil_type and soil_type.lower() in {"sandy", "poor", "degraded"}:
        recs.append(f"Soil type '{soil_type}' may limit yield - recommend soil improvement (compost, terracing).")

    for factor in factors or []:
        name = factor.get("feature")
        if factor.get("peer_direction") != "below_peers":
            continue
        if name == "farmers_using_improved_seeds_pct":
            recs.append(
                f"Improved seed use is {factor.get('district_value')}% here versus "
                f"{factor.get('peer_value')}% in higher-yield peers; review improved seed access."
            )
        elif name in {"farmers_using_organic_fertilizer_pct", "agricultural_area_organic_fertilizer_share"}:
            recs.append("Review access to organic fertilizer and locally suitable soil fertility support; reported use is below higher-yield peer districts.")
        elif name in {"farmers_using_inorganic_fertilizer_pct", "agricultural_area_inorganic_fertilizer_share"}:
            recs.append("Review access to appropriate fertilizer and extension guidance; reported use is below higher-yield peer districts.")
        elif name in {"farmers_practicing_irrigation_pct", "modern_irrigated_area_share"}:
            recs.append("Assess practical access to irrigation; reported use is below higher-yield peer districts.")

    # Preserve order while avoiding duplicate advice from overlapping features.
    return list(dict.fromkeys(recs))
