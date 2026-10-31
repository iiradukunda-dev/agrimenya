"""Shared interactive Folium map components for Rwanda agricultural views."""
import html
import math
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
try:
    import folium
    from streamlit_folium import st_folium
except ImportError:
    folium = None
    st_folium = None

# Priority zone color palette - matches the design system semantic colors
PRIORITY_COLORS = {
    "High": "#DC2626",
    "Medium": "#D97706",
    "Low": "#059669",
}

RSA_ORTHOMOSAIC_TILES = (
    "https://portal.space.gov.rw/server/rest/services/Hosted/Ortho_Orthomosaic/"
    "MapServer/tile/{z}/{y}/{x}"
)
NISR_BOUNDARIES_URL = "https://gis-server.statistics.gov.rw/server/rest/services/Hosted"
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

_google_location_map = components.declare_component(
    "agrimenya_google_location_map",
    path=str(Path(__file__).parent / "google_map_component"),
)
RSA_ORTHOMOSAIC_NOTE = (
    "The public RSA orthomosaic cache has a limited mapped footprint near Kigali, and its capture date is not "
    "available. It is visual reference only, not evidence of crop type, field condition, or yield."
)
ESRI_SATELLITE_TILES = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/"
    "MapServer/tile/{z}/{y}/{x}"
)
ESRI_BOUNDARIES_TILES = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/"
    "World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
)


def google_maps_configured() -> bool:
    """Return whether the optional Google Maps frontend key is configured."""
    return bool(os.getenv("GOOGLE_MAPS_API_KEY", "").strip())


def render_google_location_map(
    *,
    key: str,
    center: dict[str, float],
    zoom: int,
    markers: list[dict] | None = None,
    height: int = 580,
) -> dict | None:
    """Render NISR boundaries and optional markers on Google satellite imagery."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not api_key:
        return None

    return _google_location_map(
        api_key=api_key,
        center=center,
        zoom=zoom,
        map_type="satellite",
        markers=markers or [],
        geojson=None,
        fit_bounds=False,
        rsa_tiles=RSA_ORTHOMOSAIC_TILES,
        boundary_levels=ADMIN_BOUNDARY_LEVELS,
        boundaries_url=NISR_BOUNDARIES_URL,
        boundary_attribution="Administrative boundaries © NISR, Rwanda Census Mapping 2022",
        height=height,
        key=key,
        default=None,
    )


def render_google_map(*, key: str, markers: list[dict], height: int = 540):
    """Render priority markers with NISR boundaries on the shared Google map."""
    return render_google_location_map(
        key=key,
        center={"lat": -1.9403, "lng": 29.8739},
        zoom=8,
        markers=markers,
        height=height,
    )


def create_rwanda_map(*, satellite_default: bool = False, hybrid: bool = True):
    """Create a Rwanda map with Esri satellite imagery and optional labels overlay."""
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
        "OpenStreetMap", name="Street Map", overlay=False, control=True,
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
    """Add the standard compact layer selector after all map layers are registered."""
    if folium is not None and map_view is not None:
        folium.LayerControl(collapsed=True, position="topright").add_to(map_view)


def add_rsa_orthomosaic_layer(map_view) -> None:
    """Add the Rwanda Space Agency imagery as an optional overlay."""
    if folium is None or map_view is None:
        return
    folium.TileLayer(
        tiles=RSA_ORTHOMOSAIC_TILES,
        attr=("Imagery: <a href='https://portal.space.gov.rw/server/rest/services/Hosted/"
              "Ortho_Orthomosaic/MapServer' target='_self'>Rwanda Space Agency</a>"),
        name="RSA orthomosaic",
        overlay=True,
        control=True,
        show=False,
        max_zoom=23,
        max_native_zoom=23,
    ).add_to(map_view)


def render_priority_map(df, *, key: str = "priority_map") -> str | None:
    """Render priority markers and return the selected zone ID."""
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

    st.caption("Red: High priority | Amber: Medium | Green: Low | Gray: not assessed. Click a point to select its zone.")
    if google_maps_configured():
        st.caption(
            "Use the map controls to switch between Google satellite, road, and optional RSA imagery. "
            f"{RSA_ORTHOMOSAIC_NOTE}"
        )
        selected = render_google_map(key=key, markers=markers)
        if isinstance(selected, dict) and selected.get("zone_id") is not None:
            return str(selected["zone_id"])
        return None

    if folium is None or st_folium is None:
        st.info("The interactive map is unavailable because its optional map components could not be loaded.")
        return None

    m = create_rwanda_map()
    add_rsa_orthomosaic_layer(m)
    for marker in markers:
        district = html.escape(marker["details"][0]["value"])
        crop = html.escape(marker["details"][1]["value"])
        production = html.escape(marker["details"][2]["value"])
        priority = html.escape(marker["details"][3]["value"])
        color = PRIORITY_COLORS.get(priority, "#6B7280")
        popup_html = (
            f"<div style='font-family: Outfit, sans-serif; font-size: 13px; line-height: 1.5;'>"
            f"<strong style='color: #1B3A2D;'>{district}</strong><br/>"
            f"Crop: {crop}<br/>"
            f"Estimated production: {production}<br/>"
            f"Priority: <span style='color: {color}; font-weight: 600;'>"
            f"{priority}</span>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[marker["lat"], marker["lng"]],
            radius=10,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=marker["title"],
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.65,
            weight=2,
            opacity=0.85,
        ).add_to(m)

    add_map_layer_control(m)
    st.caption(
        f"Use the layer control to switch between street, satellite, and RSA imagery. {RSA_ORTHOMOSAIC_NOTE}"
    )
    click = st_folium(
        m,
        key=key,
        height=540,
        width="stretch",
        returned_objects=["last_object_clicked"],
    )
    clicked = click.get("last_object_clicked") if isinstance(click, dict) else None
    if not isinstance(clicked, dict) or clicked.get("lat") is None or clicked.get("lng") is None:
        return None

    clicked_lat = float(clicked["lat"])
    clicked_lon = float(clicked["lng"])
    nearest_id = None
    nearest_distance = float("inf")
    for _, row in df.iterrows():
        try:
            latitude = float(row.get("Lat"))
            longitude = float(row.get("Lon"))
        except (TypeError, ValueError):
            continue
        if not (math.isfinite(latitude) and math.isfinite(longitude)):
            continue
        distance = (latitude - clicked_lat) ** 2 + (longitude - clicked_lon) ** 2
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_id = row.get("id")

    return str(nearest_id) if nearest_id is not None and nearest_distance <= 0.0001 else None
