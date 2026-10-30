"""Descriptive district comparisons for observed agricultural metrics with Google Earth satellite drill-down."""
from __future__ import annotations

import html
import logging
import math
from typing import Any

import pandas as pd
import requests
import streamlit as st

try:
    import folium
    from streamlit_folium import st_folium
except ImportError:  # Keep the table usable if optional map packages are missing.
    folium = None
    st_folium = None

from components.errors import error_boundary
from components.charts import render_segment_distribution_chart, render_segment_summary_chart
from components.maps import add_map_layer_control, create_rwanda_map
from utils import api_client
from utils.i18n import t
from views.data_insights import normalize_agri_metrics

logger = logging.getLogger(__name__)

DISTRICT_BOUNDARIES_URL = (
    "https://gis-server.statistics.gov.rw/server/rest/services/Hosted/"
    "District_Boundary_2022/FeatureServer/0/query"
)
CELL_BOUNDARIES_URL = (
    "https://gis-server.statistics.gov.rw/server/rest/services/Hosted/"
    "Cell_Boundary_2022__Open_Data_/FeatureServer/2/query"
)
METRIC_OPTIONS = {
    "Yield": ("Yield (kg/ha)", "kg/ha"),
    "Production": ("Production (MT)", "MT"),
    "Cultivated area": ("Cultivated area (ha)", "ha"),
}
RANGE_COLORS = {
    "Lower observed range": "#c66c55",
    "Middle observed range": "#d4a347",
    "Upper observed range": "#458b70",
    "Not comparable": "#94a3b8",
    "No recorded value": "#d1d5db",
}
SATELLITE_BOUNDARY_COLOR = "#f8fafc"
ALL_DISTRICTS = "All districts"
ALL_SECTORS = "All sectors"
ALL_CELLS = "All cells"

RWANDA_AGRO_ZONES: dict[str, dict[str, Any]] = {
    "musanze": {
        "zone": "Volcanic Highlands",
        "altitude": "1,800m – 2,500m",
        "soil": "Volcanic Andosols (High organic matter)",
        "crops": ["Irish Potato", "Maize", "Climbing Beans", "Pyrethrum", "Vegetables"],
        "advisory": "Optimal for Irish potatoes and high-elevation maize. Practice contour ridging on slopes to prevent volcanic topsoil erosion.",
    },
    "nyabihu": {
        "zone": "Volcanic Highlands",
        "altitude": "1,900m – 2,600m",
        "soil": "Volcanic Andosols",
        "crops": ["Irish Potato", "Tea", "Maize", "Wheat", "Dairy Fodder"],
        "advisory": "High potential for dairy farming and seed potato production. Monitor for late blight during rainy periods.",
    },
    "rubavu": {
        "zone": "Lake Kivu & Volcanic Belt",
        "altitude": "1,500m – 2,300m",
        "soil": "Volcanic & Alluvial Soils",
        "crops": ["Banana", "Irish Potato", "Vegetables", "Coffee", "Beans"],
        "advisory": "Favorable lake micro-climate. High potential for intensive horticulture and cross-border commercial produce.",
    },
    "burera": {
        "zone": "Northern Highlands & Lakes",
        "altitude": "1,700m – 2,300m",
        "soil": "Humic Ferralsols & Andosols",
        "crops": ["Irish Potato", "Maize", "Wheat", "Climbing Beans"],
        "advisory": "Steep lakeside terrain. Progressive terracing and agroforestry are strongly recommended.",
    },
    "gicumbi": {
        "zone": "Buberuka Highlands",
        "altitude": "1,700m – 2,200m",
        "soil": "Acidic Ferralsols",
        "crops": ["Tea", "Wheat", "Irish Potato", "Climbing Beans", "Dairy Pasture"],
        "advisory": "Acidic soils benefit significantly from agricultural lime (TRAVERTINE) application and organic manure.",
    },
    "rulindo": {
        "zone": "Buberuka & Central Plateau Transition",
        "altitude": "1,600m – 2,100m",
        "soil": "Ferralsols & Valley Alluvium",
        "crops": ["Maize", "Beans", "Coffee", "Vegetables", "Cassava"],
        "advisory": "Valley marshlands are highly productive for dry-season vegetable cultivation (Season C).",
    },
    "gakenke": {
        "zone": "Northern Hill Country",
        "altitude": "1,600m – 2,200m",
        "soil": "Ferralsols on steep hills",
        "crops": ["Specialty Arabica Coffee", "Maize", "Beans", "Banana"],
        "advisory": "World-class specialty coffee terroir. Maintain bench terraces and shade trees for erosion control.",
    },
    "bugesera": {
        "zone": "Eastern Lowlands & Lakes Basin",
        "altitude": "1,300m – 1,500m",
        "soil": "Sandy Loam & Vertisols",
        "crops": ["Cassava", "Bush Beans", "Drought-Tolerant Maize", "Sorghum", "Watermelon"],
        "advisory": "Warm climate with moderate precipitation. Early planting, mulching, and rainwater harvesting optimize yields.",
    },
    "nyagatare": {
        "zone": "Eastern Savanna & Agro-Pastoral Plain",
        "altitude": "1,250m – 1,450m",
        "soil": "Clay Loam & Sandy Clay",
        "crops": ["Maize", "Soybean", "Rice (Marshland)", "Bush Beans", "Dairy Pasture"],
        "advisory": "Rwanda's grain basket and dairy heartland. Ensure supplemental irrigation and proper post-harvest drying storage.",
    },
    "gatsibo": {
        "zone": "Eastern Plateau & Lowlands",
        "altitude": "1,350m – 1,600m",
        "soil": "Ferralsols & Lithosols",
        "crops": ["Maize", "Beans", "Banana", "Cassava", "Soybean"],
        "advisory": "Highly suitable for consolidated maize and bean farming. Timely weed management and fertilizer application drive high yields.",
    },
    "kayonza": {
        "zone": "Eastern Plateau & Savanna",
        "altitude": "1,300m – 1,550m",
        "soil": "Sandy Clay Loam",
        "crops": ["Banana", "Maize", "Cassava", "Bush Beans", "Pineapple"],
        "advisory": "Good commercial banana and cassava production zone. Protect against banana xanthomonas wilt (BXW) through sanitation.",
    },
    "kirehe": {
        "zone": "Akagera Valley Lowlands",
        "altitude": "1,250m – 1,500m",
        "soil": "Alluvial & Sandy Soils",
        "crops": ["Banana", "Maize", "Bush Beans", "Rice", "Cassava"],
        "advisory": "Major commercial cooking and dessert banana zone. Irrigation schemes near the river significantly boost dry-season output.",
    },
    "ngoma": {
        "zone": "Eastern Plateau Transition",
        "altitude": "1,400m – 1,650m",
        "soil": "Ferralsols",
        "crops": ["Banana", "Maize", "Beans", "Cassava", "Coffee"],
        "advisory": "Mixed farming zone. Intercropping bananas with shade-tolerant legumes preserves soil fertility.",
    },
    "rwamagana": {
        "zone": "Eastern Plateau",
        "altitude": "1,450m – 1,650m",
        "soil": "Sandy Loam & Ferralsols",
        "crops": ["Banana", "Maize", "Vegetables", "Beans", "Coffee"],
        "advisory": "Strategic peri-urban agricultural hub with good logistics. Ideal for high-value vegetable farming and commercial bananas.",
    },
    "huye": {
        "zone": "Central Plateau & Southern Hills",
        "altitude": "1,600m – 1,800m",
        "soil": "Humic Ferralsols & Acrisols",
        "crops": ["Coffee", "Cassava", "Beans", "Maize", "Sweet Potato"],
        "advisory": "Rich agro-research history (RAB Rubona station). Excellent for specialty coffee washing and improved cassava varieties.",
    },
    "gisagara": {
        "zone": "Southern Akanyaru Basin",
        "altitude": "1,500m – 1,750m",
        "soil": "Ferralsols & Valley Peat",
        "crops": ["Cassava", "Bush Beans", "Rice (Peat Marshlands)", "Maize"],
        "advisory": "Akanyaru marshlands produce significant rice yields. Uplands benefit from organic compost and nitrogen fertilization.",
    },
    "muhanga": {
        "zone": "Central Plateau",
        "altitude": "1,600m – 1,850m",
        "soil": "Ferralsols",
        "crops": ["Cassava", "Beans", "Maize", "Vegetables", "Coffee"],
        "advisory": "Central distribution hub. Intensify legume rotation to maintain soil organic carbon on hill slopes.",
    },
    "kamonyi": {
        "zone": "Central Plateau & Nyabarongo Basin",
        "altitude": "1,500m – 1,750m",
        "soil": "Alluvial & Ferralsols",
        "crops": ["Cassava", "Maize", "Vegetables", "Beans", "Sweet Potato"],
        "advisory": "Nyabarongo floodplains are prime for dry-season horticulture supplying the Kigali urban market.",
    },
    "nyanza": {
        "zone": "Central Plateau",
        "altitude": "1,600m – 1,800m",
        "soil": "Humic Ferralsols",
        "crops": ["Cassava", "Beans", "Maize", "Sweet Potato", "Dairy Fodder"],
        "advisory": "Historical dairy and cassava production zone. Utilize CBSD-tolerant cassava varieties for maximum root yield.",
    },
    "ruhango": {
        "zone": "Central Plateau",
        "altitude": "1,550m – 1,780m",
        "soil": "Ferralsols",
        "crops": ["Cassava", "Maize", "Beans", "Coffee", "Banana"],
        "advisory": "Major cassava processing district. Commercial cooperatives achieve high yields with certified cuttings.",
    },
    "nyamagabe": {
        "zone": "Congo-Nile Ridge & Southern Highlands",
        "altitude": "1,700m – 2,400m",
        "soil": "Acidic Ferralsols & Podzols",
        "crops": ["Tea", "Irish Potato", "Wheat", "Climbing Beans"],
        "advisory": "High altitude tea zone. Travertine lime application neutralizes soil acidity for grain and potato plots.",
    },
    "nyaruguru": {
        "zone": "Southern Highlands & Border Range",
        "altitude": "1,750m – 2,400m",
        "soil": "Acidic Acrisols",
        "crops": ["Tea", "Wheat", "Irish Potato", "Climbing Beans"],
        "advisory": "High-altitude micro-climate. Bench terracing and lime application are vital for optimal agricultural productivity.",
    },
    "karongi": {
        "zone": "Lake Kivu Escarpment",
        "altitude": "1,480m – 2,200m",
        "soil": "Ferralsols & Steep Regosols",
        "crops": ["Specialty Coffee", "Tea", "Banana", "Beans", "Cassava"],
        "advisory": "Stunning lake vistas with steep slopes. Radical terracing and agroforestry trees are essential to stabilize slopes.",
    },
    "rutsiro": {
        "zone": "Western Highlands & Kivu Basin",
        "altitude": "1,500m – 2,400m",
        "soil": "Humic Ferralsols",
        "crops": ["Coffee", "Tea", "Irish Potato", "Beans", "Maize"],
        "advisory": "Award-winning specialty coffee washing stations. Rich organic matter on middle and upper slopes.",
    },
    "nyamasheke": {
        "zone": "Southern Kivu Belt",
        "altitude": "1,470m – 2,100m",
        "soil": "Volcanic & Humic Ferralsols",
        "crops": ["Specialty Coffee", "Tea", "Banana", "Cassava", "Macadamia"],
        "advisory": "High annual rainfall and fertile lake soils. Ideal for export-grade Arabica coffee and intensive banana groves.",
    },
    "rusizi": {
        "zone": "Bugarama Basin & Southern Kivu",
        "altitude": "950m (Bugarama) – 1,900m",
        "soil": "Alluvial Vertisols & Ferralsols",
        "crops": ["Rice (Bugarama Plain)", "Cassava", "Banana", "Coffee", "Oil Palm"],
        "advisory": "Bugarama plain is Rwanda's warmest, lowest-altitude zone (950m). Prime for double-cropped irrigated paddy rice.",
    },
    "ngororero": {
        "zone": "Western Mountain Range",
        "altitude": "1,600m – 2,300m",
        "soil": "Humic Ferralsols on steep hills",
        "crops": ["Tea", "Specialty Coffee", "Maize", "Beans", "Irish Potato"],
        "advisory": "Mountainous terrain. Terrace farming combined with vetiver grass hedgerows ensures sustainable hillside cropping.",
    },
    "gasabo": {
        "zone": "Kigali Metropolitan & Valley Marshlands",
        "altitude": "1,400m – 1,750m",
        "soil": "Alluvial & Humic Ferralsols",
        "crops": ["Vegetables", "Horticulture", "Maize", "Cassava"],
        "advisory": "Intensive peri-urban horticulture and greenhouse farming. High immediate demand for fresh greens, tomatoes, and herbs.",
    },
    "kicukiro": {
        "zone": "Kigali Metropolitan Belt",
        "altitude": "1,400m – 1,650m",
        "soil": "Sandy Clay & Valley Alluvium",
        "crops": ["Vegetables", "Greenhouse Produce", "Maize", "Fruit Trees"],
        "advisory": "High-value urban farming, hydroponics, and poultry integration. Maximize output per square meter with modern irrigation.",
    },
    "nyarugenge": {
        "zone": "Nyabarongo Valley & City Slopes",
        "altitude": "1,350m – 1,600m",
        "soil": "Alluvial Valley Soils",
        "crops": ["Marshland Vegetables", "Maize", "Sweet Potato", "Sugarcane"],
        "advisory": "Nyabarongo wetlands support continuous year-round vegetable and green maize production.",
    },
}


@st.cache_data(ttl=86400, show_spinner=False)
def _load_administrative_locations() -> pd.DataFrame:
    """Load NISR's complete 2022 district-sector-cell directory without geometries."""
    locations = []
    offset = 0
    for _ in range(10):
        response = requests.get(
            CELL_BOUNDARIES_URL,
            params={
                "where": "1=1",
                "outFields": "district,sector,cell",
                "returnGeometry": "false",
                "orderByFields": "objectid",
                "resultOffset": offset,
                "resultRecordCount": 2000,
                "f": "json",
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or payload.get("error"):
            raise ValueError("NISR returned an invalid administrative-location response")
        features = payload.get("features") or []
        locations.extend(
            feature.get("attributes") or {}
            for feature in features
            if isinstance(feature, dict)
        )
        if not payload.get("exceededTransferLimit") or not features:
            break
        offset += len(features)
    else:
        raise ValueError("NISR administrative-location response exceeded the pagination limit")

    frame = pd.DataFrame(locations).rename(columns={
        "district": "District",
        "sector": "Sector",
        "cell": "Cell",
    })
    required = ["District", "Sector", "Cell"]
    if frame.empty or not all(column in frame.columns for column in required):
        raise ValueError("NISR returned no district-sector-cell records")
    for column in required:
        frame[column] = frame[column].astype("string").str.strip()
    return frame.dropna(subset=required).drop_duplicates(required).sort_values(required).reset_index(drop=True)


@st.cache_data(ttl=86400, show_spinner=False)
def _load_district_boundaries() -> dict | None:
    """Load the 2022 Rwanda district boundaries published by NISR."""
    response = requests.get(
        DISTRICT_BOUNDARIES_URL,
        params={
            "where": "1=1",
            "outFields": "district,province",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) and payload.get("type") == "FeatureCollection" else None


@st.cache_data(ttl=86400, show_spinner=False)
def _load_cell_boundaries(district: str) -> dict:
    """Load cell polygons only for the selected district to keep the map responsive."""
    locations = []
    offset = 0
    escaped_district = district.strip().replace("'", "''")
    for _ in range(10):
        response = requests.get(
            CELL_BOUNDARIES_URL,
            params={
                "where": f"district='{escaped_district}'",
                "outFields": "district,sector,cell",
                "returnGeometry": "true",
                "outSR": "4326",
                "orderByFields": "objectid",
                "resultOffset": offset,
                "resultRecordCount": 500,
                "f": "geojson",
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or payload.get("error"):
            raise ValueError("NISR returned an invalid cell-boundary response")
        features = payload.get("features") or []
        locations.extend(feature for feature in features if isinstance(feature, dict))
        if not payload.get("exceededTransferLimit") or not features:
            break
        offset += len(features)
    else:
        raise ValueError("NISR cell-boundary response exceeded the pagination limit")

    if not locations:
        raise ValueError(f"NISR returned no cell boundaries for {district}")
    return {"type": "FeatureCollection", "features": locations}


def _clean_value(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _summarize_districts(frame: pd.DataFrame, metric_column: str) -> pd.DataFrame:
    """Aggregate observed rows by district without mixing in predictions."""
    columns = ["District", "Value", "Record count", "Range"]
    if frame.empty or metric_column not in frame.columns or "District" not in frame:
        return pd.DataFrame(columns=columns)

    results = []
    for district, district_rows in frame.groupby("District", dropna=True):
        observed = district_rows[metric_column].dropna()
        if observed.empty:
            continue

        if metric_column == "Yield (kg/ha)":
            if "Cultivated area (ha)" in district_rows.columns:
                area = district_rows["Cultivated area (ha)"]
                weighted_rows = district_rows[metric_column].notna() & area.notna() & area.gt(0)
                valid_area = area[weighted_rows]
                if not valid_area.empty and valid_area.sum() > 0:
                    value = float(
                        (district_rows.loc[weighted_rows, metric_column] * valid_area).sum()
                        / valid_area.sum()
                    )
                else:
                    value = float(observed.mean())
            else:
                value = float(observed.mean())
        elif metric_column in {"Production (MT)", "Cultivated area (ha)"}:
            value = float(observed.sum())
        else:
            value = float(observed.mean())

        results.append({
            "District": str(district),
            "Value": value,
            "Record count": int(observed.count()),
            "Range": "Not comparable",
        })

    summary = pd.DataFrame(results, columns=columns)
    if summary.empty:
        return summary

    if len(summary) == 1:
        summary.loc[:, "Range"] = "Not comparable"
        return summary

    lower_cut, upper_cut = summary["Value"].quantile([1 / 3, 2 / 3]).tolist()
    summary["Range"] = summary["Value"].map(
        lambda value: (
            "Lower observed range" if value <= lower_cut else
            "Middle observed range" if value <= upper_cut else
            "Upper observed range"
        )
    )
    return summary


def _parse_map_drill_key(value: object) -> tuple[str, ...] | None:
    """Decode a controlled tooltip key returned by the interactive map."""
    if not isinstance(value, str):
        return None
    plain_text = html.unescape(value)
    plain_text = pd.Series([plain_text]).str.replace(r"<[^>]+>", "", regex=True).iloc[0].strip()
    parts = tuple(part.strip() for part in plain_text.split("|"))
    expected_sizes = {"district": 2, "sector": 3, "cell": 4}
    if len(parts) != expected_sizes.get(parts[0].casefold(), 0) or not all(parts):
        return None
    return (parts[0].casefold(), *parts[1:])


def _geometry_points(geometry: dict) -> list[tuple[float, float]]:
    """Flatten GeoJSON coordinate arrays into longitude/latitude pairs."""
    points: list[tuple[float, float]] = []

    def collect(value: object) -> None:
        if not isinstance(value, list):
            return
        if len(value) >= 2 and isinstance(value[0], (int, float)) and isinstance(value[1], (int, float)):
            points.append((float(value[0]), float(value[1])))
            return
        for item in value:
            collect(item)

    collect(geometry.get("coordinates"))
    return points


def _render_location_explorer(
    selected_district: str,
    selected_sector: tuple[str, str] | None,
    selected_cell: tuple[str, str, str] | None,
    *,
    key: str,
) -> None:
    """High-resolution Google Earth satellite viewer with hierarchical district -> sector -> cell zoom."""
    if folium is None or st_folium is None:
        st.info("The interactive satellite map is unavailable because its map components could not be loaded.")
        return

    map_view = create_rwanda_map(satellite_default=True, hybrid=True)
    current_location = (
        selected_district,
        selected_sector[1] if selected_sector else None,
        selected_cell[2] if selected_cell else None,
    )

    if selected_district == ALL_DISTRICTS:
        try:
            boundaries = _load_district_boundaries()
        except (requests.RequestException, ValueError):
            logger.exception("Unable to load official district boundaries for the location explorer")
            boundaries = None

        if boundaries:
            map_features = []
            for feature in boundaries.get("features", []):
                enriched = {**feature, "properties": dict(feature.get("properties") or {})}
                district = _clean_value(enriched["properties"].get("district"))
                if district:
                    enriched["properties"]["drill_key"] = f"district|{district}"
                    map_features.append(enriched)
                    # Add clickable district centroid marker
                    pts = _geometry_points(enriched.get("geometry") or {})
                    if pts:
                        c_lon = sum(p[0] for p in pts) / len(pts)
                        c_lat = sum(p[1] for p in pts) / len(pts)
                        label = html.escape(district)
                        folium.Marker(
                            location=[c_lat, c_lon],
                            tooltip=f"district|{district}",
                            icon=folium.DivIcon(
                                html=(
                                    "<div style='white-space:nowrap;transform:translate(-50%,-50%);"
                                    "padding:3px 8px;border-radius:12px;background:rgba(255,255,255,0.92);"
                                    "border:1.5px solid #0284c7;color:#0369a1;font-size:11px;"
                                    f"font-weight:700;box-shadow:0 2px 6px rgba(0,0,0,0.2);cursor:pointer;'>"
                                    f"📍 {label}</div>"
                                ),
                                icon_size=(1, 1),
                                icon_anchor=(0, 0),
                            ),
                        ).add_to(map_view)

            map_data = {**boundaries, "features": map_features}
            folium.GeoJson(
                map_data,
                name="Rwanda districts",
                style_function=lambda _: {
                    "color": "#f8fafc",
                    "weight": 2.2,
                    "fillColor": "#0284c7",
                    "fillOpacity": 0.22,
                },
                highlight_function=lambda _: {
                    "color": "#facc15",
                    "weight": 4,
                    "fillOpacity": 0.45,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["drill_key"], aliases=["Click district to zoom into Sectors"], labels=False, sticky=True,
                ),
                popup=folium.GeoJsonPopup(
                    fields=["district", "province"],
                    aliases=["District", "Province"],
                    labels=True,
                ),
                zoom_on_click=True,
            ).add_to(map_view)
            folium.FitBounds([[-2.85, 28.85], [-1.0, 30.9]]).add_to(map_view)
        else:
            st.warning("Official district boundaries are temporarily unavailable.")
    else:
        try:
            boundaries = _load_cell_boundaries(selected_district)
        except (requests.RequestException, ValueError):
            logger.exception("Unable to load NISR cell boundaries for %s", selected_district)
            boundaries = None

        if boundaries:
            map_features = []
            sector_points: dict[str, list[tuple[float, float]]] = {}
            for feature in boundaries.get("features", []):
                enriched = {**feature, "properties": dict(feature.get("properties") or {})}
                properties = enriched["properties"]
                district = _clean_value(properties.get("district"))
                sector = _clean_value(properties.get("sector"))
                cell = _clean_value(properties.get("cell"))
                if not district or not sector or not cell:
                    continue
                properties["drill_key"] = f"cell|{district}|{sector}|{cell}"
                if selected_sector and sector.casefold() != selected_sector[1].casefold():
                    continue
                map_features.append(enriched)
                sector_points.setdefault(sector, []).extend(
                    _geometry_points(enriched.get("geometry") or {})
                )

            if map_features:
                map_data = {"type": "FeatureCollection", "features": map_features}
                selected_cell_name = selected_cell[2].casefold() if selected_cell else None

                folium.GeoJson(
                    map_data,
                    name="Cell & Field boundaries",
                    style_function=lambda feature: {
                        "color": "#facc15" if (
                            selected_cell_name and
                            _clean_value((feature.get("properties") or {}).get("cell")).casefold() == selected_cell_name
                        ) else "#f8fafc",
                        "weight": 4 if (
                            selected_cell_name and
                            _clean_value((feature.get("properties") or {}).get("cell")).casefold() == selected_cell_name
                        ) else 2,
                        "fillColor": "#10b981" if (
                            selected_cell_name and
                            _clean_value((feature.get("properties") or {}).get("cell")).casefold() == selected_cell_name
                        ) else "#0f766e",
                        "fillOpacity": 0.35 if (
                            selected_cell_name and
                            _clean_value((feature.get("properties") or {}).get("cell")).casefold() == selected_cell_name
                        ) else 0.20,
                    },
                    highlight_function=lambda _: {
                        "color": "#facc15",
                        "weight": 4,
                        "fillOpacity": 0.48,
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=["drill_key"], aliases=["Click to zoom into field"], labels=False, sticky=True,
                    ),
                    popup=folium.GeoJsonPopup(
                        fields=["district", "sector", "cell"],
                        aliases=["District", "Sector", "Cell"],
                        labels=True,
                    ),
                    zoom_on_click=True,
                ).add_to(map_view)

                # Sector centroid markers when looking at district level
                if not selected_sector:
                    for sector, points in sector_points.items():
                        if not points:
                            continue
                        longitude = sum(point[0] for point in points) / len(points)
                        latitude = sum(point[1] for point in points) / len(points)
                        label = html.escape(sector)
                        folium.Marker(
                            location=[latitude, longitude],
                            tooltip=f"sector|{selected_district}|{sector}",
                            icon=folium.DivIcon(
                                html=(
                                    "<div style='white-space:nowrap;transform:translate(-50%,-50%);"
                                    "padding:3px 7px;border-radius:12px;background:rgba(255,255,255,0.92);"
                                    "border:1.5px solid #0f766e;color:#134e4a;font-size:11px;"
                                    f"font-weight:700;box-shadow:0 2px 6px rgba(0,0,0,0.25);cursor:pointer;'>"
                                    f"🏘️ {label}</div>"
                                ),
                                icon_size=(1, 1),
                                icon_anchor=(0, 0),
                            ),
                        ).add_to(map_view)

                # Smooth zoom bounds
                if selected_cell:
                    cell_points = [
                        point
                        for feature in map_features
                        if _clean_value((feature.get("properties") or {}).get("cell")).casefold() == selected_cell_name
                        for point in _geometry_points(feature.get("geometry") or {})
                    ]
                    if cell_points:
                        map_view.fit_bounds(
                            [[min(p[1] for p in cell_points), min(p[0] for p in cell_points)],
                             [max(p[1] for p in cell_points), max(p[0] for p in cell_points)]],
                            padding=(20, 20),
                            max_zoom=18,
                        )
                    else:
                        all_points = [point for feature in map_features for point in _geometry_points(feature.get("geometry") or {})]
                        if all_points:
                            map_view.fit_bounds([[min(p[1] for p in all_points), min(p[0] for p in all_points)], [max(p[1] for p in all_points), max(p[0] for p in all_points)]], padding=(20, 20))
                else:
                    all_points = [point for feature in map_features for point in _geometry_points(feature.get("geometry") or {})]
                    if all_points:
                        map_view.fit_bounds([[min(p[1] for p in all_points), min(p[0] for p in all_points)], [max(p[1] for p in all_points), max(p[0] for p in all_points)]], padding=(20, 20))
            else:
                st.info("No cell boundaries match this district and sector.")

    add_map_layer_control(map_view)
    map_data = st_folium(
        map_view,
        key=key,
        height=580,
        width="stretch",
        returned_objects=["last_object_clicked_tooltip"],
    )
    click = _parse_map_drill_key(
        map_data.get("last_object_clicked_tooltip") if isinstance(map_data, dict) else None
    )
    if click:
        if click[0] == "district":
            next_location = (click[1], None, None)
            next_state = {
                "seg_district": click[1],
                "seg_sector": ALL_SECTORS,
                "seg_cell": ALL_CELLS,
            }
        elif click[0] == "sector":
            next_location = (click[1], click[2], None)
            next_state = {
                "seg_district": click[1],
                "seg_sector": click[2],
                "seg_cell": ALL_CELLS,
            }
        else:
            next_location = (click[1], click[2], click[3])
            next_state = {
                "seg_district": click[1],
                "seg_sector": click[2],
                "seg_cell": click[3],
            }
        if tuple(value.casefold() if value else None for value in next_location) != tuple(
            value.casefold() if value else None for value in current_location
        ):
            st.session_state["seg_map_pending_selection"] = next_state
            st.rerun()

    st.caption(
        "🛰️ Google Earth High-Resolution Satellite: Esri World Imagery (Maxar / GIS Community). "
        "Boundaries: NISR 2022 Census Mapping. Zoom in down to Level 18 to inspect crop fields, terraces, and farm boundaries."
    )


def _render_comparison_map(
    summary: pd.DataFrame,
    metric_label: str,
    unit: str,
    *,
    key: str,
    satellite_default: bool = False,
) -> None:
    """Render a choropleth map showing observed yield/production by district."""
    if folium is None or st_folium is None:
        st.info("The map is unavailable because its optional map components could not be loaded.")
        return

    map_view = create_rwanda_map(satellite_default=satellite_default, hybrid=True)
    try:
        boundaries = _load_district_boundaries()
    except Exception:
        boundaries = None

    value_by_district = {}
    if summary is not None and not summary.empty:
        for _, row in summary.iterrows():
            d_name = _clean_value(row.get("District")).casefold()
            if d_name:
                value_by_district[d_name] = row

    if boundaries:
        features = []
        for feature in boundaries.get("features", []):
            enriched = {**feature, "properties": dict(feature.get("properties") or {})}
            district = _clean_value(enriched["properties"].get("district"))
            rec = value_by_district.get(district.casefold())
            if rec is not None:
                val = rec.get("Value")
                rng = rec.get("Range", "Not comparable")
                enriched["properties"]["obs_value"] = f"{val:,.1f} {unit}" if pd.notna(val) else "No data"
                enriched["properties"]["obs_range"] = rng
                enriched["properties"]["drill_key"] = f"district|{district}"
            else:
                enriched["properties"]["obs_value"] = "No recorded value"
                enriched["properties"]["obs_range"] = "No recorded value"
                enriched["properties"]["drill_key"] = f"district|{district}"
            features.append(enriched)

        map_data = {**boundaries, "features": features}

        def _style_fn(f):
            props = f.get("properties") or {}
            rng = props.get("obs_range", "No recorded value")
            fill = RANGE_COLORS.get(rng, "#94a3b8")
            return {
                "color": "#ffffff",
                "weight": 1.8,
                "fillColor": fill,
                "fillOpacity": 0.55,
            }

        folium.GeoJson(
            map_data,
            name="District Yield Benchmark",
            style_function=_style_fn,
            highlight_function=lambda _: {"weight": 3.5, "color": "#facc15", "fillOpacity": 0.75},
            tooltip=folium.GeoJsonTooltip(
                fields=["district", "obs_value", "obs_range"],
                aliases=["District:", f"{metric_label}:", "Range:"],
                labels=True,
                sticky=True,
            ),
            zoom_on_click=True,
        ).add_to(map_view)
        folium.FitBounds([[-2.85, 28.85], [-1.0, 30.9]]).add_to(map_view)

    add_map_layer_control(map_view)
    st_folium(map_view, key=key, height=580, width="stretch", returned_objects=[])

    legend_items = "".join(
        f"<span style='display:inline-flex;align-items:center;gap:6px;margin:0 14px 6px 0;'>"
        f"<i style='display:inline-block;width:12px;height:12px;border-radius:50%;background:{color};'></i>"
        f"{html.escape(label)}</span>"
        for label, color in RANGE_COLORS.items()
    )
    st.markdown(f"<div style='font-size:.82rem;margin-top:.35rem;'>{legend_items}</div>", unsafe_allow_html=True)


def _render_farming_zone_card(
    district: str,
    sector: str | None,
    cell: str | None,
    crop: str,
    metric_label: str,
    unit: str,
    summary_df: pd.DataFrame,
) -> None:
    """Render comprehensive agricultural farming zone intelligence for the focused location."""
    d_clean = district.strip()
    zone_info = RWANDA_AGRO_ZONES.get(d_clean.lower(), {
        "zone": "Central Plateau & Agricultural Basin",
        "altitude": "1,450m – 1,800m",
        "soil": "Ferralsols & Valley Humus",
        "crops": ["Maize", "Beans", "Cassava", "Banana"],
        "advisory": "Follow seasonal rainfall patterns and intercrop legumes for soil health.",
    })

    # Historical district metric
    hist_val = None
    if summary_df is not None and not summary_df.empty:
        matched = summary_df[summary_df["District"].astype(str).str.casefold().eq(d_clean.casefold())]
        if not matched.empty and pd.notna(matched.iloc[0]["Value"]):
            hist_val = matched.iloc[0]["Value"]

    # Live local weather
    weather = api_client.get_weather(d_clean) if d_clean and d_clean != ALL_DISTRICTS else None

    with st.container(border=True):
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;margin-bottom:0.6rem;">
                <div>
                    <span style="font-size:0.75rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:#0284c7;background:#e0f2fe;padding:3px 10px;border-radius:999px;">
                        🌾 Farming Zone Determination
                    </span>
                    <h3 style="margin:0.35rem 0 0;color:#082f49;font-size:1.35rem;font-weight:800;">
                        {html.escape(d_clean)}{f" › {html.escape(sector)}" if sector and sector != ALL_SECTORS else ""}{f" › {html.escape(cell)}" if cell and cell != ALL_CELLS else ""}
                    </h3>
                </div>
                <div style="font-size:0.85rem;color:#475569;font-weight:600;">
                    Zone: <strong style="color:#0284c7;">{html.escape(zone_info['zone'])}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Elevation Profile", zone_info["altitude"])
        c2.metric("Soil Classification", zone_info["soil"].split("(")[0].strip())
        c3.metric(
            f"Observed {metric_label}",
            f"{hist_val:,.1f} {unit}" if hist_val is not None else "Pending records",
            help=f"Observed {metric_label.casefold()} recorded in {d_clean} for {crop}.",
        )
        if weather and weather.get("temperature_c") is not None:
            c4.metric(
                "Current Weather",
                f"{weather['temperature_c']:.1f} °C",
                delta=f"Rain: {weather.get('rainfall_mm', 0):.1f}mm | Wind: {weather.get('wind_kph', 0):.0f}kph",
                delta_color="off",
            )
        else:
            c4.metric("Current Weather", "Central Africa Time", delta="CAT UTC+2", delta_color="off")

        st.markdown("##### Recommended Crops for this Farming Zone")
        crop_badges = "".join(
            f"<span style='display:inline-block;padding:4px 12px;margin:3px 6px 3px 0;border-radius:9999px;font-size:0.82rem;font-weight:700;background:{'#dcfce7;color:#166534;border:1.5px solid #86efac;' if c.casefold() == crop.casefold() else '#f1f5f9;color:#334155;border:1px solid #cbd5e1;'}'>{html.escape(c)}{' ★ Selected' if c.casefold() == crop.casefold() else ''}</span>"
            for c in zone_info["crops"]
        )
        st.markdown(f"<div style='margin-bottom:0.75rem;'>{crop_badges}</div>", unsafe_allow_html=True)

        st.info(f"**Agronomic Guidance for {d_clean}:** {zone_info['advisory']}")


@error_boundary("Segmentation")
def render_segment() -> None:
    # ── 1. Synchronize map clicks into widget state before rendering selectboxes ──
    pending = st.session_state.pop("seg_map_pending_selection", None)
    if isinstance(pending, dict):
        if "seg_district" in pending:
            st.session_state["seg_district"] = pending["seg_district"]
        if "seg_sector" in pending:
            st.session_state["seg_sector"] = pending["seg_sector"]
        if "seg_cell" in pending:
            st.session_state["seg_cell"] = pending["seg_cell"]

    st.markdown(
        """
        <style>
        .segmentation-hero {
            margin: 0.4rem 0 1.25rem;
            padding: clamp(1.25rem, 3vw, 2rem);
            border: 1px solid rgba(2, 132, 199, 0.16);
            border-radius: 20px;
            background: linear-gradient(118deg, #eff8ff 0%, #ffffff 58%, #effaf4 100%);
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.055);
        }
        .segmentation-hero__top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.65rem;
            margin-bottom: 0.8rem;
        }
        .segmentation-hero__eyebrow {
            color: #0b7657;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.11em;
            text-transform: uppercase;
        }
        .segmentation-hero__badge {
            padding: 0.3rem 0.65rem;
            border: 1px solid rgba(11, 118, 87, 0.18);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.78);
            color: #0b7657;
            font-size: 0.72rem;
            font-weight: 700;
        }
        .segmentation-hero h1 {
            margin: 0;
            color: #102a36;
            font-size: clamp(1.7rem, 3vw, 2.35rem);
            font-weight: 800;
            letter-spacing: -0.04em;
            line-height: 1.15;
        }
        .segmentation-hero__description {
            max-width: 760px;
            margin: 0.65rem 0 0;
            color: #47616b;
            font-size: 1rem;
            line-height: 1.65;
        }
        .segmentation-hero__note {
            margin-top: 1rem;
            padding-top: 0.8rem;
            border-top: 1px solid rgba(15, 54, 64, 0.1);
            color: #536b72;
            font-size: 0.84rem;
        }
        </style>
        <section class="segmentation-hero">
            <div class="segmentation-hero__top">
                <span class="segmentation-hero__eyebrow">Rwanda · District insights</span>
                <span class="segmentation-hero__badge">Observed data</span>
            </div>
            <h1>District comparison & Satellite Farming Zones</h1>
            <p class="segmentation-hero__description">
                Explore recorded yield, production, and cultivated area across crops, seasons, and districts.
                Click any district on the Google Earth satellite map to zoom directly to sectors, cells, and high-resolution farm fields.
            </p>
            <div class="segmentation-hero__note">
                Descriptive summaries and high-resolution satellite imagery — designed for extension officers and farmers.
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    try:
        official_rows = api_client.get_official_yields()
    except Exception:
        logger.exception("Unable to load bundled NISR observations for segmentation")
        official_rows = []
    official_data_available = bool(official_rows)
    if official_data_available:
        records = normalize_agri_metrics(official_rows)
        st.caption("NISR district-level observations · all seasons available in the bundled 2022–2026 evidence.")
    else:
        try:
            records = normalize_agri_metrics(api_client.get_agri_metrics())
        except Exception:
            logger.exception("Unable to load agricultural observations for segmentation")
            records = normalize_agri_metrics([])
            st.error("Agricultural observations could not be loaded. Please check the data connection and try again.")
        if not records.empty:
            st.warning("The historical NISR dataset is unavailable. Showing only operational records returned by the backend.")

    try:
        locations = _load_administrative_locations()
    except (requests.RequestException, ValueError):
        logger.exception("Unable to load the NISR 2022 administrative-location directory")
        locations = pd.DataFrame(columns=["District", "Sector", "Cell"])
        st.warning(
            "The complete NISR location directory is temporarily unavailable. "
            "Location choices are limited to places present in the available records."
        )
    if locations.empty and not records.empty:
        locations = records[["District", "Sector", "Cell"]].dropna(how="all").drop_duplicates()
    try:
        zone_locations = api_client.get_zones() or []
    except Exception:
        logger.exception("Unable to load registered zone locations")
        zone_locations = []
    if zone_locations:
        registered_locations = pd.DataFrame([{
            "District": zone.get("district"),
            "Sector": zone.get("sector"),
            "Cell": zone.get("cell"),
        } for zone in zone_locations if isinstance(zone, dict)])
        if not registered_locations.empty:
            locations = pd.concat([locations, registered_locations], ignore_index=True)
            locations = locations.dropna(subset=["District"], how="any").drop_duplicates()

    available_metrics = [
        (label, column, unit)
        for label, (column, unit) in METRIC_OPTIONS.items()
        if column in records.columns and records[column].notna().any()
    ]

    if records.empty or "Crop" not in records.columns or "Season" not in records.columns:
        st.info("No agricultural observation records are available for this view yet.")
        return
    if not available_metrics:
        st.info("The available records do not contain yield, production, or cultivated-area values to compare.")
        return

    crops = sorted(value for value in records["Crop"].dropna().astype(str).str.strip().unique() if value)
    if not crops:
        st.info("No crop labels are available in the current observations.")
        return

    with st.container(border=True):
        st.subheader("Choose what to compare")
        filter_row_one = st.columns([1.15, 1.15, 1.1])
        with filter_row_one[0]:
            selected_metric_label = st.selectbox("Measure", [item[0] for item in available_metrics], key="seg_measure")
        with filter_row_one[1]:
            selected_crop = st.selectbox("Crop", crops, key="seg_crop")

        crop_records = records[records["Crop"].astype(str).eq(selected_crop)]
        seasons = sorted(
            (value for value in crop_records["Season"].dropna().astype(str).str.strip().unique() if value),
            reverse=True,
        )
        if not seasons:
            st.info(f"No observed seasons are available for {selected_crop}.")
            return
        with filter_row_one[2]:
            selected_season = st.selectbox("Season", seasons, key="seg_season")

        crop_season_records = crop_records[crop_records["Season"].astype(str).eq(selected_season)]
        if locations.empty or "District" not in locations.columns:
            districts = sorted(
                value for value in crop_season_records["District"].dropna().astype(str).unique() if value
            )
        else:
            districts = sorted(
                value for value in locations["District"].dropna().astype(str).str.strip().unique() if value
            )
        filter_row_two = st.columns(3)
        with filter_row_two[0]:
            dist_options = [ALL_DISTRICTS, *districts]
            cur_dist = st.session_state.get("seg_district", ALL_DISTRICTS)
            dist_idx = dist_options.index(cur_dist) if cur_dist in dist_options else 0
            selected_district = st.selectbox("District", dist_options, index=dist_idx, key="seg_district")

        district_locations = locations
        if selected_district != ALL_DISTRICTS and "District" in district_locations.columns:
            district_locations = district_locations[
                district_locations["District"].astype(str).str.casefold().eq(selected_district.casefold())
            ]
        sector_records = district_locations[["District", "Sector"]].dropna().drop_duplicates()
        sector_labels = {
            (str(row["Sector"]) if selected_district != ALL_DISTRICTS
             else f"{row['District']} · {row['Sector']}"): (str(row["District"]), str(row["Sector"]))
            for _, row in sector_records.iterrows()
        }
        with filter_row_two[1]:
            sec_options = [ALL_SECTORS, *sector_labels]
            cur_sec = st.session_state.get("seg_sector", ALL_SECTORS)
            sec_idx = sec_options.index(cur_sec) if cur_sec in sec_options else 0
            selected_sector = st.selectbox("Sector", sec_options, index=sec_idx, key="seg_sector")

        selected_sector_location = sector_labels.get(selected_sector)
        cell_records = district_locations[["District", "Sector", "Cell"]].dropna().drop_duplicates()
        if selected_sector_location:
            cell_records = cell_records[
                cell_records["District"].astype(str).str.casefold().eq(selected_sector_location[0].casefold())
                & cell_records["Sector"].astype(str).str.casefold().eq(selected_sector_location[1].casefold())
            ]
        cell_labels = {
            (str(row["Cell"]) if selected_district != ALL_DISTRICTS and selected_sector_location
             else f"{row['District']} · {row['Sector']} · {row['Cell']}"):
                (str(row["District"]), str(row["Sector"]), str(row["Cell"]))
            for _, row in cell_records.iterrows()
        }
        with filter_row_two[2]:
            cell_options = [ALL_CELLS, *cell_labels]
            cur_cell = st.session_state.get("seg_cell", ALL_CELLS)
            cell_idx = cell_options.index(cur_cell) if cur_cell in cell_options else 0
            selected_cell = st.selectbox("Cell", cell_options, index=cell_idx, key="seg_cell")

    selected_cell_location = cell_labels.get(selected_cell)
    effective_district = (
        selected_district if selected_district != ALL_DISTRICTS
        else selected_cell_location[0] if selected_cell_location
        else selected_sector_location[0] if selected_sector_location
        else None
    )
    filtered = crop_season_records.copy()
    if effective_district:
        filtered = filtered[
            filtered["District"].astype(str).str.casefold().eq(effective_district.casefold())
        ]
    if not official_data_available and selected_sector_location and "Sector" in filtered.columns:
        filtered = filtered[
            filtered["Sector"].astype(str).str.casefold().eq(selected_sector_location[1].casefold())
        ]
    if not official_data_available and selected_cell_location and "Cell" in filtered.columns:
        filtered = filtered[
            filtered["Cell"].astype(str).str.casefold().eq(selected_cell_location[2].casefold())
        ]

    metric_column, metric_unit = METRIC_OPTIONS[selected_metric_label]
    summary = _summarize_districts(filtered, metric_column)
    observed_record_count = int(
        pd.to_numeric(filtered[metric_column], errors="coerce")
        .replace([float("inf"), float("-inf")], float("nan"))
        .notna()
        .sum()
    )

    coverage_columns = st.columns(3, gap="medium")
    coverage_metrics = (
        ("Matching records", f"{len(filtered):,}", "Records matching the current crop, season, and location filters."),
        ("Records with this measure", f"{observed_record_count:,}", f"Matching records with a recorded {selected_metric_label.casefold()} value."),
        ("Districts represented", f"{len(summary):,}", "Districts with at least one usable value for the selected measure."),
    )
    for column, (label, value, help_text) in zip(coverage_columns, coverage_metrics):
        with column:
            with st.container(border=True):
                st.metric(label, value, help=help_text)

    # ── Interactive Map Explorer ──────────────────────────────────────────────
    st.markdown("---")
    map_head_c1, map_head_c2 = st.columns([3, 1], vertical_alignment="center")
    with map_head_c1:
        st.subheader("🛰️ Interactive Google Earth Satellite & Zone Viewer")
        st.caption("Click any district to zoom into its sectors, click a sector to zoom into cells, and inspect clear satellite imagery to determine farming zones.")
    with map_head_c2:
        if st.button("↺ Rwanda Overview", use_container_width=True, help="Reset zoom to show all Rwanda districts"):
            st.session_state["seg_map_pending_selection"] = {
                "seg_district": ALL_DISTRICTS,
                "seg_sector": ALL_SECTORS,
                "seg_cell": ALL_CELLS,
            }
            st.rerun()

    # Active drill-down breadcrumb indicator
    cur_d = selected_district if selected_district != ALL_DISTRICTS else "All Districts"
    cur_s = selected_sector if selected_sector != ALL_SECTORS else "All Sectors"
    cur_c = selected_cell if selected_cell != ALL_CELLS else "All Cells"
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:8px;padding:6px 14px;background:#f8fafc;border-radius:10px;border:1px solid #e2e8f0;font-size:0.85rem;color:#475569;margin-bottom:0.75rem;">
            <span>📍 Active Zoom:</span>
            <strong>{html.escape(cur_d)}</strong> › 
            <span>{html.escape(cur_s)}</span> › 
            <span>{html.escape(cur_c)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    map_mode = st.radio(
        "Map visualization mode",
        ["🛰️ Satellite Farm Explorer (Google Earth Drill-down)", "📊 Observed Yield Benchmark Map"],
        horizontal=True,
        key="seg_map_mode_select",
        label_visibility="collapsed",
    )

    if map_mode.startswith("🛰️"):
        _render_location_explorer(
            selected_district,
            selected_sector_location,
            selected_cell_location,
            key="segmentation_location_explorer_map",
        )
        if selected_district != ALL_DISTRICTS:
            _render_farming_zone_card(
                selected_district,
                selected_sector,
                selected_cell,
                selected_crop,
                selected_metric_label,
                metric_unit,
                summary,
            )
    else:
        _render_comparison_map(
            summary,
            selected_metric_label,
            metric_unit,
            key="segmentation_comparison_map",
            satellite_default=False,
        )

    st.markdown("---")
    summary_col_1, summary_col_2 = st.columns([1.2, 1], gap="large")
    with summary_col_1:
        st.subheader(f"{selected_metric_label} summary across districts")
        render_segment_summary_chart(summary, selected_metric_label, metric_unit)
    with summary_col_2:
        st.subheader("Performance Highlights")
        if summary.empty:
            st.info("No matching observations include a value for this measure.")
        else:
            finite_values = summary["Value"].replace([float("inf"), float("-inf")], pd.NA).dropna()
            if not finite_values.empty:
                top = summary.loc[summary["Value"].idxmax()]
                st.metric(
                    f"Highest observed {selected_metric_label.casefold()}",
                    f"{top['Value']:,.1f} {metric_unit}",
                    help="This describes the selected records; it is not a forecast or farmer ranking.",
                )
                st.caption(f"**{top['District']}** leads with the highest recorded value in this selection.")

    st.divider()
    st.subheader("Explore matching observations")
    st.caption("Search within the current crop, season, district, sector, and cell selection.")
    search_term = st.text_input("Search records", key="seg_records_search", placeholder="Search a district, sector, cell, or crop")
    searchable_columns = [
        column for column in ["District", "Sector", "Cell", "Crop", "Season", "Soil type"]
        if column in filtered.columns
    ]
    visible_records = filtered
    if search_term.strip() and searchable_columns:
        query = search_term.strip().casefold()
        matches = filtered[searchable_columns].astype("string").fillna("").apply(
            lambda column: column.str.casefold().str.contains(query, regex=False)
        ).any(axis=1)
        visible_records = filtered[matches]

    st.caption(f"Showing {len(visible_records):,} of {len(filtered):,} matching records.")
    if visible_records.empty:
        st.info("No records match the current filters and search.")
    else:
        render_segment_distribution_chart(
            visible_records,
            metric_column,
            selected_metric_label,
            metric_unit,
        )
        records_for_inspection = visible_records.reset_index(drop=True)

        def _observation_label(index: int) -> str:
            record = records_for_inspection.iloc[index]
            location = " / ".join(
                str(record.get(column)).strip()
                for column in ("District", "Sector", "Cell")
                if record.get(column) is not None and not pd.isna(record.get(column)) and str(record.get(column)).strip()
            )
            value = record.get(metric_column)
            crop_value = record.get("Crop")
            value_label = f"{float(value):,.1f} {metric_unit}" if pd.notna(value) else "Value not recorded"
            crop_label = str(crop_value) if pd.notna(crop_value) else selected_crop
            return f"{location or 'Location not recorded'} · {crop_label} · {value_label}"

        selected_record_index = st.selectbox(
            "Inspect an observation",
            list(range(len(records_for_inspection))),
            format_func=_observation_label,
            key="seg_observation_select",
        )
        selected_record = records_for_inspection.iloc[selected_record_index]
        observation_metrics = [
            ("Yield (kg/ha)", "Yield", "kg/ha"),
            ("Production (MT)", "Production", "MT"),
            ("Cultivated area (ha)", "Cultivated area", "ha"),
            ("Rainfall (mm)", "Rainfall", "mm"),
        ]
        available_observation_metrics = [
            (column, label, unit)
            for column, label, unit in observation_metrics
            if column in records_for_inspection.columns
        ]
        if available_observation_metrics:
            metric_cols = st.columns(min(len(available_observation_metrics), 4))
            for metric_col, (column, label, unit) in zip(metric_cols, available_observation_metrics):
                value = pd.to_numeric(pd.Series([selected_record.get(column)]), errors="coerce").iloc[0]
                metric_col.metric(
                    label,
                    f"{value:,.1f} {unit}" if pd.notna(value) else "Not recorded",
                )
        def _location_value(column: str) -> str:
            value = selected_record.get(column)
            return str(value) if pd.notna(value) else "Not recorded"

        st.caption(
            f"District: {_location_value('District')}"
            f" · Sector: {_location_value('Sector')}"
            f" · Cell: {_location_value('Cell')}"
            f" · Soil: {_location_value('Soil type')}"
        )
