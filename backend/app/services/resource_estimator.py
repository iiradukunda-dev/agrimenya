"""Transparent resource arithmetic using rates and prices supplied by users.

This module does not recommend agronomic application rates. It only scales the
user-entered values to the selected area and totals supplied prices.
"""

from __future__ import annotations

from math import isfinite


_INPUTS = (
    "seed_rate_kg_ha", "seed_price_rwf_kg",
    "dap_rate_kg_ha", "dap_price_rwf_kg",
    "urea_rate_kg_ha", "urea_price_rwf_kg",
    "irrigation_liters_ha", "irrigation_price_rwf_1000_liters",
)


def estimate_resources(area_cultivated: float | None, rainfall_mm: float | None = None,
                       **inputs: float | None) -> dict:
    area = float(area_cultivated or 0)
    if not isfinite(area) or area <= 0:
        return {"status": "needs_inputs", "basis": "Enter a cultivated area greater than zero.",
                "area_ha": None, "user_inputs": {}, "quantities": {}, "costs_rwf": {},
                "estimated_cost_rwf": None, "missing_inputs": ["area_cultivated"]}

    clean = {}
    for key in _INPUTS:
        raw = inputs.get(key)
        if raw is None:
            continue
        number = float(raw)
        if not isfinite(number) or number < 0:
            raise ValueError(f"{key} must be a finite non-negative number")
        clean[key] = number

    quantities: dict[str, float] = {}
    costs: dict[str, float] = {}
    missing_prices: list[str] = []
    pairs = (
        ("seed_rate_kg_ha", "seeds_kg", "seed_price_rwf_kg", "seeds"),
        ("dap_rate_kg_ha", "dap_kg", "dap_price_rwf_kg", "dap"),
        ("urea_rate_kg_ha", "urea_kg", "urea_price_rwf_kg", "urea"),
    )
    for rate_key, quantity_key, price_key, cost_key in pairs:
        if rate_key in clean:
            quantity = round(clean[rate_key] * area, 2)
            quantities[quantity_key] = quantity
            if price_key in clean:
                costs[cost_key] = round(quantity * clean[price_key], 2)
            else:
                missing_prices.append(price_key)

    if "irrigation_liters_ha" in clean:
        quantity = round(clean["irrigation_liters_ha"] * area, 2)
        quantities["irrigation_liters"] = quantity
        if "irrigation_price_rwf_1000_liters" in clean:
            costs["irrigation"] = round(quantity / 1000 * clean["irrigation_price_rwf_1000_liters"], 2)
        else:
            missing_prices.append("irrigation_price_rwf_1000_liters")

    fertilizer_parts = [quantities[key] for key in ("dap_kg", "urea_kg") if key in quantities]
    if fertilizer_parts:
        quantities["fertilizer_kg"] = round(sum(fertilizer_parts), 2)

    if not quantities:
        status = "needs_inputs"
        total_cost = None
    else:
        status = "partial" if missing_prices else "calculated_from_user_inputs"
        total_cost = round(sum(costs.values()), 2) if not missing_prices else None

    notes = ["Arithmetic uses only the rates and prices entered here; it is not an agronomic recommendation."]
    if rainfall_mm is not None:
        notes.append("Rainfall is recorded for context and does not alter the user-entered irrigation rate.")
    if missing_prices:
        notes.append("Add prices for every entered resource to calculate a complete budget.")
    if not quantities:
        notes.append("Enter at least one resource rate per hectare.")

    return {
        "status": status,
        "area_ha": area,
        "user_inputs": clean,
        "quantities": quantities,
        "costs_rwf": costs,
        "estimated_cost_rwf": total_cost,
        "total_cost_scope": "entered_resources_only",
        "missing_inputs": missing_prices,
        "basis": " ".join(notes),
    }
