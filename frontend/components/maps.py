"""
Map component for the Segmentation pillar.

Renders an interactive Folium map centered on Rwanda showing
priority zones with semantic color coding.
"""
import html
import math

import folium
import streamlit as st
from streamlit_folium import st_folium

# Priority zone color palette - matches the design system semantic colors
PRIORITY_COLORS = {
    "High":   "#DC2626",
    "Medium": "#D97706",
    "Low":    "#059669",
}


RSA_ORTHOMOSAIC_TILES = (
    "https://portal.space.gov.rw/server/rest/services/Hosted/Ortho_Orthomosaic/"
    "MapServer/tile/{z}/{y}/{x}"
)


def render_priority_map(df, *, key: str = "priority_map") -> str | None:
    """
    Renders a Folium map with priority zone markers.

    Each marker shows district, crop, and yield on hover.
    Uses the standard OpenStreetMap tile service so the map works
    without a provider-specific API key.
    """
    # Center on Rwanda
    m = folium.Map(
        location=[-1.9403, 29.8739],
        zoom_start=8,
        max_zoom=23,
        tiles="OpenStreetMap",
    )

    show_imagery = st.toggle(
        "Show Rwanda Space Agency orthomosaic imagery",
        value=False,
        key=f"{key}_rsa_imagery",
        help="Visual context only. This imagery does not affect yield estimates or priority levels.",
    )
    if show_imagery:
        folium.TileLayer(
            tiles=RSA_ORTHOMOSAIC_TILES,
            attr=("Imagery: <a href='https://portal.space.gov.rw/server/rest/services/Hosted/"
                  "Ortho_Orthomosaic/MapServer' target='_blank'>Rwanda Space Agency</a>"),
            name="RSA orthomosaic",
            overlay=True,
            control=True,
            show=True,
            max_zoom=23,
            max_native_zoom=23,
        ).add_to(m)
        folium.LayerControl(collapsed=True).add_to(m)

    if not df.empty:
        for _, row in df.iterrows():
            try:
                latitude = float(row.get("Lat"))
                longitude = float(row.get("Lon"))
            except (TypeError, ValueError):
                continue
            if not (math.isfinite(latitude) and math.isfinite(longitude)):
                continue

            color = PRIORITY_COLORS.get(row.get("Priority"), "#6B7280")
            production_value = row.get("Production_MT")
            try:
                production_number = float(production_value)
                production_text = f"{production_number:,.1f}" if math.isfinite(production_number) else "N/A"
            except (TypeError, ValueError):
                production_text = "N/A"
            district = html.escape(str(row.get("District", "Unknown")))
            crop = html.escape(str(row.get("Crop", "N/A")))
            priority = html.escape(str(row.get("Priority", "N/A")))
            popup_html = (
                f"<div style='font-family: Outfit, sans-serif; font-size: 13px; line-height: 1.5;'>"
                f"<strong style='color: #1B3A2D;'>{district}</strong><br/>"
                f"Crop: {crop}<br/>"
                f"Estimated production: {production_text} MT<br/>"
                f"Priority: <span style='color: {color}; font-weight: 600;'>"
                f"{priority}</span>"
                f"</div>"
            )

            folium.CircleMarker(
                location=[latitude, longitude],
                radius=10,
                popup=folium.Popup(popup_html, max_width=220),
                tooltip=f"{district} | {crop} | {priority}",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.65,
                weight=2,
                opacity=0.85,
            ).add_to(m)

    st.caption("Red: High priority | Amber: Medium | Green: Low | Gray: not assessed. Click a point to select its zone.")
    if show_imagery:
        st.caption(
            "The public RSA orthomosaic cache has a limited mapped footprint near Kigali; "
            "the service does not expose a capture date in its layer summary. It is visual reference only "
            "and is not evidence of crop type, field condition, or yield."
        )
    click = st_folium(
        m,
        key=key,
        height=500,
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

    # A marker click reports the marker coordinates. Ignore plain map clicks.
    return str(nearest_id) if nearest_id is not None and nearest_distance <= 0.0001 else None
