"""
Map component for the Segmentation pillar.

Renders an interactive Folium map centered on Rwanda showing
priority zones with semantic color coding.
"""
import folium
from streamlit_folium import st_folium

# Priority zone color palette — matches the design system semantic colors
PRIORITY_COLORS = {
    "High":   "#DC2626",
    "Medium": "#D97706",
    "Low":    "#059669",
}


def render_priority_map(df) -> None:
    """
    Renders a Folium map with priority zone markers.

    Each marker shows district, crop, and yield on hover.
    Uses CartoDB Voyager tiles for a modern, clean basemap
    that complements the glassmorphic UI.
    """
    # Center on Rwanda
    m = folium.Map(
        location=[-1.9403, 29.8739],
        zoom_start=8,
        tiles="CartoDB Voyager",
        attr="&copy; CartoDB",
    )

    if not df.empty:
        for _, row in df.iterrows():
            color = PRIORITY_COLORS.get(row.get("Priority"), "#6B7280")
            popup_html = (
                f"<div style='font-family: Inter, sans-serif; font-size: 13px; line-height: 1.5;'>"
                f"<strong style='color: #1B3A2D;'>{row.get('District', 'Unknown')}</strong><br/>"
                f"Crop: {row.get('Crop', 'N/A')}<br/>"
                f"Yield: {row.get('Yield_MT_ha', 'N/A')} MT/ha<br/>"
                f"Priority: <span style='color: {color}; font-weight: 600;'>"
                f"{row.get('Priority', 'N/A')}</span>"
                f"</div>"
            )

            folium.CircleMarker(
                location=[row["Lat"], row["Lon"]],
                radius=10,
                popup=folium.Popup(popup_html, max_width=220),
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.65,
                weight=2,
                opacity=0.85,
            ).add_to(m)

    return st_folium(m, width=700, height=500, returned_objects=[])
