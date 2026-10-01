"""
Estimates seeds/fertilizer/irrigation resources needed to close the
yield gap for a zone. Rough per-hectare rates below are reasonable
starting assumptions for Rwanda smallholder maize/bean production -
refine with real agronomic data/NISR figures as they become available.
"""

SEEDS_KG_PER_HA = 25.0
FERTILIZER_KG_PER_HA = 150.0
IRRIGATION_LITERS_PER_HA_LOW_RAINFALL = 5000.0
COST_PER_KG_SEEDS_RWF = 1200.0
COST_PER_KG_FERTILIZER_RWF = 800.0


def estimate_resources(area_cultivated: float | None, rainfall_mm: float | None) -> dict:
    area = area_cultivated or 0.5

    seeds_kg = round(SEEDS_KG_PER_HA * area, 1)
    fertilizer_kg = round(FERTILIZER_KG_PER_HA * area, 1)
    irrigation_liters = (
        round(IRRIGATION_LITERS_PER_HA_LOW_RAINFALL * area, 1)
        if (rainfall_mm is not None and rainfall_mm < 600)
        else 0.0
    )
    estimated_cost = round(
        seeds_kg * COST_PER_KG_SEEDS_RWF + fertilizer_kg * COST_PER_KG_FERTILIZER_RWF, 0
    )

    return {
        "seeds_kg": seeds_kg,
        "fertilizer_kg": fertilizer_kg,
        "irrigation_liters": irrigation_liters,
        "estimated_cost_rwf": estimated_cost,
    }
