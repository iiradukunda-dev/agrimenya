"""Shared Google Maps components for Rwanda agricultural views."""
import math
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

try:
    import folium
except ImportError:
    folium = None


_google_map_component = components.declare_component(
    "agrimenya_google_map",
    path=str(Path(__file__).parent / "google_map_component"),
)
_google_location_map = components.declare_component(
    "agrimenya_google_location_map",
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
NISR_BOUNDARIES_URL = (
    "https://gis-server.statistics.gov.rw/server/rest/services/Hosted"
)
ESRI_SATELLITE_TILES = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/"
    "MapServer/tile/{z}/{y}/{x}"
)
ESRI_BOUNDARIES_TILES = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/"
    "World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
)
ADMIN_BOUNDARY_LEVELS = [
    {
        "name": "District",
        "min_zoom": 0,
        "service": "District_Boundary_2022",
        "layer_id": 0,
        "name_field": "district",
        "fields": ["province", "district"],
        "max_allowable_offset": 0.003,
    },
    {
        "name": "Sector",
        "min_zoom": 9,
        "service": "Sector_Boundary__Open_Data_",
        "layer_id": 1,
        "name_field": "sector",
        "fields": ["province", "district", "sector"],
        "max_allowable_offset": 0.0008,
    },
    {
        "name": "Cell",
        "min_zoom": 12,
        "service": "Cell_Boundary_2022__Open_Data_",
        "layer_id": 2,
        "name_field": "cell",
        "fields": ["province", "district", "sector", "cell"],
        "max_allowable_offset": 0.0002,
    },
    {
        "name": "Village",
        "min_zoom": 15,
        "service": "Village_Boundary_2022",
        "layer_id": 3,
        "name_field": "village",
        "fields": ["province", "district", "sector", "cell", "village"],
        "max_allowable_offset": 0.00005,
    },
]


def google_maps_configured() -> bool:
    """Return whether the optional Google Maps frontend key is configured."""
    return bool(os.getenv("GOOGLE_MAPS_API_KEY", "").strip())


def render_google_location_map(
    *,
    key: str,
    center: dict[str, float],
    zoom: int,
) -> dict | None:
    """Render the NISR boundary explorer on Google satellite imagery."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not api_key:
        return None

    return _google_location_map(
        api_key=api_key,
        center=center,
        zoom=zoom,
        map_type="satellite",
        boundary_levels=ADMIN_BOUNDARY_LEVELS,
        boundaries_url=NISR_BOUNDARIES_URL,
        height=580,
        key=key,
        default=None,
    )


def create_rwanda_map(*, satellite_default: bool = False, hybrid: bool = True):
    """Create the shared Rwanda basemap used by district and location explorers."""
    if folium is None:
        return None

    map_view = folium.Map(
        location=[-1.9403, 29.8739],
        zoom_start=8,
        max_zoom=23,
        tiles=None,
        control_scale=True,
        zoom_control=True,
        prefer_canvas=True,
    )
    folium.TileLayer(
        tiles=ESRI_SATELLITE_TILES,
        attr="Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics",
        name="Satellite (Clear Earth)",
        overlay=False,
        control=True,
        show=satellite_default,
        max_zoom=22,
        max_native_zoom=19,
    ).add_to(map_view)
    folium.TileLayer(
        "OpenStreetMap",
        name="Street Map",
        overlay=False,
        control=True,
        show=not satellite_default,
    ).add_to(map_view)
    if hybrid:
        folium.TileLayer(
            tiles=ESRI_BOUNDARIES_TILES,
            attr="Labels & Boundaries © Esri",
            name="Roads & Place Labels",
            overlay=True,
            control=True,
            show=satellite_default,
        ).add_to(map_view)
    return map_view


def add_map_layer_control(map_view) -> None:
    """Add the standard layer selector after the map layers are registered."""
    if folium is not None and map_view is not None:
        folium.LayerControl(collapsed=True, position="topright").add_to(map_view)


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
        boundary_levels=ADMIN_BOUNDARY_LEVELS,
        boundaries_url=NISR_BOUNDARIES_URL,
        boundary_attribution="Administrative boundaries © NISR, Rwanda Census Mapping 2022",
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
            priority = str(row.get("Priority", "N/A"))
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
        "Click a point to select its zone. Zoom in to explore district, sector, cell, and village boundaries."
    )
    st.caption(
        f"Use the map controls to switch between Google satellite, road, and optional RSA imagery. "
        f"{RSA_ORTHOMOSAIC_NOTE}"
    )
    selected = render_google_map(key=key, markers=markers)
    if isinstance(selected, dict) and selected.get("zone_id") is not None:
        return str(selected["zone_id"])
    return None
