"""Turn saved assessment evidence into cautious, reviewable next steps."""


def get_recommendations(priority_level: str, rainfall_mm: float | None,
                         soil_type: str | None,
                         factors: list[dict] | None = None) -> list[str]:
    recs: list[str] = []

    if priority_level == "High":
        recs.append("Review this assessment with the local extension team before prioritising support.")
        recs.append("Confirm the season, cultivated area, and current field conditions before planning a response.")
    elif priority_level == "Medium":
        recs.append("Review the recorded evidence during routine seasonal follow-up.")
        recs.append("Check for newer field observations before changing the existing plan.")
    else:
        recs.append("Keep the current records under review; this assessment alone does not verify field conditions.")

    if rainfall_mm is not None:
        recs.append("Review the rainfall value and reporting period with a current local forecast before making water decisions.")

    if soil_type and soil_type.lower() in {"sandy", "poor", "degraded"}:
        recs.append(f"Verify the recorded soil description ('{soil_type}') with a field assessment before selecting soil-management actions.")

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
