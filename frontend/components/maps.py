"""Interactive priority map with transparent, clearly labeled map layers."""
import html
import json
import math
import copy
from pathlib import Path

import folium
import streamlit as st
from folium import Element
from folium.plugins import Fullscreen, MarkerCluster, MeasureControl
from streamlit_folium import st_folium

PRIORITY_COLORS = {
    "High": "#B5473C",
    "Medium": "#B7791F",
    "Low": "#34745A",
    "Unassessed": "#718096",
}

DISTRICT_BOUNDARIES_PATH = Path(__file__).resolve().parents[1] / "data" / "rwanda_district_boundaries.geojson"
DISTRICT_BOUNDARIES_SOURCE = "https://gis-server.statistics.gov.rw/server/rest/services/Hosted/District_Boundary_2022/FeatureServer/0"
PRIORITY_RANK = {"Unassessed": 0, "Low": 1, "Medium": 2, "High": 3}
YIELD_SEGMENT_COLORS = {
    "Lower observed range": "#B5473C",
    "Middle observed range": "#B7791F",
    "Upper observed range": "#34745A",
    "No observations": "#D7DFD9",
}


def _priority_label(value) -> str:
    text = str(value or "Unassessed").strip().casefold()
    return {"high": "High", "medium": "Medium", "low": "Low"}.get(text, "Unassessed")


def _number(value) -> float | None:
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


@st.cache_data(show_spinner=False)
def _district_boundaries() -> dict | None:
    """Load the bundled NISR 2022 district boundary snapshot."""
    try:
        with DISTRICT_BOUNDARIES_PATH.open(encoding="utf-8") as source:
            return json.load(source)
    except (OSError, json.JSONDecodeError):
        return None


def _district_key(value) -> str:
    return "".join(character for character in str(value or "").casefold() if character.isalnum())


def render_priority_map(df, *, key: str = "priority_map") -> str | None:
    """Render district priority shading and saved zone points."""
    m = folium.Map(
        location=[-1.9403, 29.8739],
        zoom_start=7,
        min_zoom=6,
        max_zoom=19,
        # CartoDB's built-in Folium tiles now require an API key. OSM keeps
        # the ordinary street layer visible without a project credential.
        tiles="OpenStreetMap",
        control_scale=True,
        prefer_canvas=True,
    )
    Fullscreen(position="topleft", title="Expand map", title_cancel="Close map").add_to(m)
    MeasureControl(position="topleft", primary_length_unit="kilometers").add_to(m)

    district_summary: dict[str, dict] = {}
    if not df.empty and "District" in df.columns:
        for _, row in df.iterrows():
            district_name = str(row.get("District") or "").strip()
            if not district_name:
                continue
            summary = district_summary.setdefault(
                _district_key(district_name),
                {"name": district_name, "priority": "Unassessed", "zones": set()},
            )
            priority = _priority_label(row.get("Priority"))
            if PRIORITY_RANK[priority] > PRIORITY_RANK[summary["priority"]]:
                summary["priority"] = priority
            zone_id = row.get("id")
            summary["zones"].add(str(zone_id) if zone_id else f"row-{len(summary['zones'])}")

    cached_boundaries = _district_boundaries()
    boundaries = copy.deepcopy(cached_boundaries) if cached_boundaries else None
    if boundaries and boundaries.get("features"):
        for feature in boundaries["features"]:
            properties = feature.setdefault("properties", {})
            summary = district_summary.get(_district_key(properties.get("district")))
            properties["agri_priority"] = summary["priority"] if summary else "No matching records"
            properties["agri_zone_records"] = len(summary["zones"]) if summary else 0

        def district_style(feature):
            district = _district_key(feature.get("properties", {}).get("district"))
            summary = district_summary.get(district)
            color = PRIORITY_COLORS[summary["priority"]] if summary else "#aab7b0"
            return {
                "fillColor": color,
                "color": "#ffffff",
                "weight": 1.5,
                "fillOpacity": 0.34 if summary else 0.08,
            }

        folium.GeoJson(
            boundaries,
            name="District priority areas",
            style_function=district_style,
            highlight_function=lambda _: {"weight": 3, "color": "#263b32", "fillOpacity": 0.48},
            tooltip=folium.GeoJsonTooltip(
                fields=["district", "agri_priority"], aliases=["District", "Highest priority"], sticky=True
            ),
            popup=folium.GeoJsonPopup(
                fields=["district", "agri_priority", "agri_zone_records"],
                aliases=["District", "Highest filtered priority", "Zone records"], labels=True,
            ),
            control=True,
            show=True,
        ).add_to(m)

    cluster = MarkerCluster(
        name="Priority zones",
        overlay=True,
        control=True,
        disableClusteringAtZoom=13,
        showCoverageOnHover=False,
        spiderfyOnMaxZoom=True,
    ).add_to(m)

    valid_points: list[tuple[float, float]] = []
    district_reference_count = 0
    if not df.empty:
        for _, row in df.iterrows():
            if row.get("location_scope") == "district_reference":
                district_reference_count += 1
                continue
            latitude = _number(row.get("Lat"))
            longitude = _number(row.get("Lon"))
            # Protect the national map extent from bad or non-Rwanda coordinates.
            if latitude is None or longitude is None or not (-5 <= latitude <= 1 and 28 <= longitude <= 32):
                continue

            priority = _priority_label(row.get("Priority"))
            color = PRIORITY_COLORS[priority]
            production = _number(row.get("Production_MT"))
            production_text = f"{production:,.2f} MT" if production is not None else "Not available"
            district = html.escape(str(row.get("District") or "Unknown district"))
            crop = html.escape(str(row.get("Crop") or "Unspecified"))
            season = html.escape(str(row.get("season") or "Not specified"))
            zone_id = html.escape(str(row.get("id") or ""))
            zone_line = f"<br><span style='color:#75837b;font-size:11px'>Zone {zone_id[:8]}</span>" if zone_id else ""
            popup_html = (
                "<div style='min-width:190px;font:13px/1.55 Inter,Arial,sans-serif;color:#263b32'>"
                f"<strong style='font-size:15px'>{district}</strong><br>"
                f"{crop} · {season}<hr style='margin:7px 0;border-color:#e4ebe6'>"
                f"<span style='color:{color};font-weight:700'>{priority} priority</span><br>"
                f"Estimated total output: {production_text}"
                f"{zone_line}"
                "</div>"
            )
            folium.CircleMarker(
                location=[latitude, longitude],
                radius=8 if priority != "Unassessed" else 7,
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"{district} · {crop} · {priority}",
                color="#ffffff",
                fill=True,
                fill_color=color,
                fill_opacity=0.92,
                weight=2.5,
            ).add_to(cluster)
            valid_points.append((latitude, longitude))

    if valid_points:
        if len(valid_points) == 1:
            m.location = valid_points[0]
            m.zoom_start = 11
        else:
            m.fit_bounds(valid_points, padding=(24, 24), max_zoom=10)

    legend_rows = "".join(
        f"<div style='display:flex;align-items:center;gap:8px;margin:5px 0'>"
        f"<span style='width:10px;height:10px;border-radius:50%;background:{color};display:inline-block'></span>{label}</div>"
        for label, color in PRIORITY_COLORS.items()
    )
    legend_html = (
        "<div style='position:fixed;bottom:24px;left:14px;z-index:9999;background:#fff;"
        "padding:10px 13px;border:1px solid #dce5df;border-radius:10px;"
        "box-shadow:0 3px 14px rgba(24,45,34,.13);font:12px/1.3 Inter,Arial,sans-serif;color:#34473d'>"
        f"<strong>Priority key · district fill / zone point</strong>{legend_rows}</div>"
    )
    m.get_root().html.add_child(Element(legend_html))
    folium.LayerControl(collapsed=True, position="topright").add_to(m)

    st.caption(
        "District shading shows the highest priority among records that match the filters. "
        "It summarizes whole districts and does not imply every farm in a shaded district has that priority. "
        f"Boundaries: NISR 2022 · [source]({DISTRICT_BOUNDARIES_SOURCE}). Base map: OpenStreetMap."
    )

    missing_points = max(0, len(df) - len(valid_points))
    st.caption(
        f"{len(valid_points)} mapped zone point{'s' if len(valid_points) != 1 else ''}. "
        "Points use submitted coordinates that have not been independently verified. District polygons are administrative summaries, not farm or field outlines. "
        "Select a point for its saved record details."
    )
    if district_reference_count:
        st.caption(f"{district_reference_count} district-level records use approximate district reference coordinates and are not drawn as field points.")
    if not boundaries:
        st.caption("District boundary file is unavailable; showing saved zone points only.")
    if missing_points:
        st.caption(f"{missing_points} filtered row{'s' if missing_points != 1 else ''} omitted because valid Rwanda coordinates are unavailable.")

    result = st_folium(
        m,
        key=key,
        height=480,
        width="stretch",
        returned_objects=["last_object_clicked"],
    )
    click = result.get("last_object_clicked") if isinstance(result, dict) else None
    if not isinstance(click, dict) or click.get("lat") is None or click.get("lng") is None:
        return None

    clicked_lat = float(click["lat"])
    clicked_lon = float(click["lng"])
    nearest_id = None
    nearest_distance = float("inf")
    for _, row in df.iterrows():
        latitude = _number(row.get("Lat"))
        longitude = _number(row.get("Lon"))
        if latitude is None or longitude is None:
            continue
        distance = (latitude - clicked_lat) ** 2 + (longitude - clicked_lon) ** 2
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_id = row.get("id")
    return str(nearest_id) if nearest_id is not None and nearest_distance <= 0.0001 else None


def render_yield_segmentation_map(rows: list[dict], *, metric_label: str, key: str = "yield_segmentation_map") -> None:
    """Map observed district segments without depending on zone points or predictions."""
    m = folium.Map(
        location=[-1.9403, 29.8739], zoom_start=7, min_zoom=6,
        tiles="OpenStreetMap", control_scale=True, prefer_canvas=True,
    )
    Fullscreen(position="topleft", title="Expand map", title_cancel="Close map").add_to(m)
    by_district = {_district_key(row.get("district")): row for row in rows if row.get("district")}
    boundaries = copy.deepcopy(_district_boundaries())
    if boundaries and boundaries.get("features"):
        for feature in boundaries["features"]:
            properties = feature.setdefault("properties", {})
            row = by_district.get(_district_key(properties.get("district")))
            properties["segment"] = row.get("segment") if row else "No observations"
            properties["metric_value"] = row.get("value_display") if row else "—"
            properties["record_count"] = row.get("record_count") if row else 0

        folium.GeoJson(
            boundaries,
            name="Observed district segments",
            style_function=lambda feature: {
                "fillColor": YIELD_SEGMENT_COLORS.get(
                    feature.get("properties", {}).get("segment"), YIELD_SEGMENT_COLORS["No observations"]
                ),
                "color": "#ffffff",
                "weight": 1.4,
                "fillOpacity": 0.58 if feature.get("properties", {}).get("segment") != "No observations" else 0.12,
            },
            highlight_function=lambda _: {"weight": 2.5, "color": "#263b32", "fillOpacity": 0.72},
            tooltip=folium.GeoJsonTooltip(
                fields=["district", "segment", "metric_value", "record_count"],
                aliases=["District", "Observed segment", metric_label, "Records"], sticky=True,
            ),
            show=True,
        ).add_to(m)

    legend_items = "".join(
        f"<div style='display:flex;align-items:center;gap:8px;margin:5px 0'>"
        f"<span style='width:10px;height:10px;border-radius:50%;background:{color};display:inline-block'></span>{label}</div>"
        for label, color in YIELD_SEGMENT_COLORS.items()
    )
    m.get_root().html.add_child(Element(
        "<div style='position:fixed;bottom:22px;left:14px;z-index:9999;background:#fff;"
        "padding:10px 13px;border:1px solid #dce5df;border-radius:10px;"
        "box-shadow:0 3px 14px rgba(24,45,34,.13);font:12px/1.3 Inter,Arial,sans-serif;color:#34473d'>"
        f"<strong>Relative {html.escape(metric_label)} segments</strong>{legend_items}</div>"
    ))
    folium.LayerControl(collapsed=True, position="topright").add_to(m)
    st.caption(
        "Each color is a quartile segment of observed district values for the selected crop and season. "
        "It is a relative comparison, not a risk score, farm-level estimate, or administrative boundary claim. "
        f"Boundaries: NISR 2022 · [source]({DISTRICT_BOUNDARIES_SOURCE})."
    )
    st_folium(m, key=key, height=500, width="stretch", returned_objects=[])
