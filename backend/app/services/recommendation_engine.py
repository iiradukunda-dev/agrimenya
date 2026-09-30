"""
Turns a priority level + zone metrics into concrete recommendations.
Rule-based today; can be extended to pull from an LLM or a richer
rules table without changing the calling code in routers/decision.py.
"""


def get_recommendations(priority_level: str, rainfall_mm: float | None,
                         soil_type: str | None) -> list[str]:
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

    return recs
