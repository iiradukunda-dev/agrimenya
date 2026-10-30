"""Shared Google Maps components for Rwanda agricultural views."""
import math
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


_google_map_component = components.declare_component(
    "agrimenya_google_map",
    path=str(Path(__file__).parent / "google_map_component"),
)

PRIORITY_COLORS = {
    "High": "#DC2626",
    "Medium": "#D97706",
    "Low": "#059669",
}

RSA_ORTHOMOSAIC_TILES = (
    "https://portal.space.gov.rw/server/rest/services/Hosted/Ortho_Orthomosaic/"
    "MapServer/tile/{z}/{y}/{x}"
)
RSA_ORTHOMOSAIC_NOTE = (
    "The public RSA orthomosaic cache has a limited mapped footprint near Kigali, and its capture date is not "
    "available. It is visual reference only, not evidence of crop type, field condition, or yield."
)


def render_google_map(
    *,
    key: str,
    satellite_default: bool = True,
    markers: list[dict] | None = None,
    geojson: dict | None = None,
    fit_bounds: bool = False,
    height: int = 540,
    center: dict | None = None,
    zoom: int = 8,
):
    """Render an interactive Google satellite map with optional markers and boundaries."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not api_key:
        st.warning(
            "Google Maps is not configured. Set GOOGLE_MAPS_API_KEY in the frontend environment "
            "to enable interactive maps."
        )
        return None

    return _google_map_component(
        api_key=api_key,
        center=center or {"lat": -1.9403, "lng": 29.8739},
        zoom=zoom,
        map_type="satellite" if satellite_default else "roadmap",
        markers=markers or [],
        geojson=geojson,
        fit_bounds=fit_bounds,
        rsa_tiles=RSA_ORTHOMOSAIC_TILES,
        height=height,
        key=key,
        default=None,
    )


def render_priority_map(df, *, key: str = "priority_map") -> str | None:
    """Render clickable priority markers and return the selected zone ID."""
    if df is None or not hasattr(df, "empty") or not hasattr(df, "iterrows"):
        st.info("Map data is not available in a usable format.")
        return None

    markers = []
    if not df.empty:
        for _, row in df.iterrows():
            try:
                latitude = float(row.get("Lat"))
                longitude = float(row.get("Lon"))
            except (TypeError, ValueError):
                continue
            if not (math.isfinite(latitude) and math.isfinite(longitude)):
                continue

            priority = str(row.get("Priority", "N/A"))
            production_value = row.get("Production_MT")
            try:
                production_number = float(production_value)
                production_text = f"{production_number:,.1f}" if math.isfinite(production_number) else "N/A"
            except (TypeError, ValueError):
                production_text = "N/A"

            district = str(row.get("District", "Unknown"))
            crop = str(row.get("Crop", "N/A"))
            markers.append({
                "id": str(row.get("id", "")),
                "lat": latitude,
                "lng": longitude,
                "title": f"{district} | {crop} | {priority}",
                "color": PRIORITY_COLORS.get(priority, "#6B7280"),
                "details": [
                    {"label": "District", "value": district},
                    {"label": "Crop", "value": crop},
                    {"label": "Estimated production", "value": f"{production_text} MT"},
                    {"label": "Priority", "value": priority},
                ],
            })

    st.caption(
        "Red: High priority | Amber: Medium | Green: Low | Gray: not assessed. "
        "Click a point to select its zone."
    )
    st.caption(
        f"Use the map controls to switch between Google satellite, road, and optional RSA imagery. "
        f"{RSA_ORTHOMOSAIC_NOTE}"
    )
    selected = render_google_map(key=key, markers=markers)
    if isinstance(selected, dict) and selected.get("zone_id") is not None:
        return str(selected["zone_id"])
    return None
