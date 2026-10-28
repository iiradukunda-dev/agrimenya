"""Transparent resource arithmetic using rates and prices supplied by users.

This module does not recommend agronomic application rates. It only scales the
user-entered values to the selected area and totals supplied prices.
"""

from __future__ import annotations

from math import isfinite


RESOURCE_INPUT_KEYS = (
    "seed_rate_kg_ha", "seed_price_rwf_kg",
    "dap_rate_kg_ha", "dap_price_rwf_kg",
    "urea_rate_kg_ha", "urea_price_rwf_kg",
    "irrigation_liters_ha", "irrigation_price_rwf_1000_liters",
    "labor_days_ha", "labor_price_rwf_day",
    "land_preparation_cost_rwf_ha", "crop_protection_cost_rwf_ha",
    "equipment_hire_cost_rwf_ha", "transport_cost_rwf_ha",
    "postharvest_cost_rwf_ha", "storage_packaging_cost_rwf_ha", "other_cost_rwf_ha",
    "contingency_pct",
)


def estimate_resources(area_cultivated: float | None, rainfall_mm: float | None = None,
                       fertilizer_items: list[dict] | None = None,
                       **inputs: float | None) -> dict:
    area = float(area_cultivated or 0)
    if not isfinite(area) or area <= 0:
        return {"status": "needs_inputs", "basis": "Enter a cultivated area greater than zero.",
                "area_ha": None, "user_inputs": {}, "quantities": {}, "costs_rwf": {},
                "estimated_cost_rwf": None, "missing_inputs": ["area_cultivated"],
                "fertilizer_items": []}

    clean = {}
    for key in RESOURCE_INPUT_KEYS:
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
    calculated_fertilizers: list[dict] = []
    fertilizer_items = fertilizer_items or []
    for index, item in enumerate(fertilizer_items, start=1):
        name = str(item.get("name") or "").strip()
        unit = str(item.get("unit") or "").strip().casefold()
        if not name or len(name) > 60:
            raise ValueError("Each fertilizer product must have a name of at most 60 characters")
        if unit not in {"kg", "litres", "tonnes"}:
            raise ValueError("Fertilizer units must be kg, litres, or tonnes")
        rate = float(item.get("rate_per_ha"))
        price = item.get("price_per_unit")
        if not isfinite(rate) or rate < 0:
            raise ValueError(f"{name} rate must be a finite non-negative number")
        if price is not None:
            price = float(price)
            if not isfinite(price) or price < 0:
                raise ValueError(f"{name} price must be a finite non-negative number")
        quantity = round(rate * area, 2)
        cost = round(quantity * price, 2) if price is not None else None
        calculated_fertilizers.append({
            "name": name,
            "rate_per_ha": rate,
            "unit": unit,
            "price_per_unit": price,
            "quantity": quantity,
            "estimated_cost_rwf": cost,
            "missing_price": price is None,
        })
        quantities[f"fertilizer_{index}_{unit}"] = quantity
        if cost is not None:
            costs[f"fertilizer_{index}"] = cost
        else:
            missing_prices.append(f"fertilizer price ({name})")

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

    if "labor_days_ha" in clean:
        quantities["labor_days"] = round(clean["labor_days_ha"] * area, 2)
        if "labor_price_rwf_day" in clean:
            costs["labor"] = round(quantities["labor_days"] * clean["labor_price_rwf_day"], 2)
        else:
            missing_prices.append("labor_price_rwf_day")

    per_hectare_costs = (
        ("land_preparation_cost_rwf_ha", "land_preparation"),
        ("crop_protection_cost_rwf_ha", "crop_protection"),
        ("equipment_hire_cost_rwf_ha", "equipment_hire"),
        ("transport_cost_rwf_ha", "transport"),
        ("postharvest_cost_rwf_ha", "postharvest_handling"),
        ("storage_packaging_cost_rwf_ha", "storage_packaging"),
        ("other_cost_rwf_ha", "other_costs"),
    )
    for input_key, cost_key in per_hectare_costs:
        if input_key in clean:
            costs[cost_key] = round(clean[input_key] * area, 2)

    subtotal = round(sum(costs.values()), 2)
    if "contingency_pct" in clean and subtotal:
        costs["contingency"] = round(subtotal * clean["contingency_pct"] / 100, 2)

    fertilizer_parts = [quantities[key] for key in ("dap_kg", "urea_kg") if key in quantities]
    fertilizer_parts.extend(
        item["quantity"] * (1000 if item["unit"] == "tonnes" else 1)
        for item in calculated_fertilizers
        if item["unit"] in {"kg", "tonnes"}
    )
    if fertilizer_parts:
        quantities["fertilizer_kg"] = round(sum(fertilizer_parts), 2)

    if not quantities and not costs:
        status = "needs_inputs"
        total_cost = None
    else:
        status = "partial" if missing_prices else "calculated_from_user_inputs"
        total_cost = round(sum(costs.values()), 2) if costs and not missing_prices else None

    notes = ["Arithmetic uses only the rates and costs entered here; it is not an agronomic recommendation."]
    if rainfall_mm is not None:
        notes.append("Rainfall is recorded for context and does not alter the user-entered irrigation rate.")
    if missing_prices:
        notes.append("Add prices for each quantity-based item to calculate a complete entered-item budget.")
    if not quantities and not costs:
        notes.append("Enter at least one resource rate or cost per hectare.")

    return {
        "status": status,
        "area_ha": area,
        "user_inputs": clean,
        "quantities": quantities,
        "costs_rwf": costs,
        "estimated_cost_rwf": total_cost,
        "total_cost_scope": "entered_resources_only",
        "missing_inputs": missing_prices,
        "fertilizer_items": calculated_fertilizers,
        "cost_coverage": "incomplete" if missing_prices else ("entered_items_only" if costs else "not_estimated"),
        "basis": " ".join(notes),
    }
