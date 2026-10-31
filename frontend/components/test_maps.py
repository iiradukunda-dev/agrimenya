from unittest.mock import MagicMock, patch

import pandas as pd

from components import maps


def _priority_data():
    return pd.DataFrame([{
        "id": "zone-1",
        "Lat": -1.94,
        "Lon": 29.87,
        "District": "Kigali",
        "Crop": "Maize",
        "Priority": "High",
        "Production_MT": 12.5,
    }])


def test_priority_map_uses_google_component_and_keeps_marker_selection(monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test-google-maps-key")
    component = MagicMock(return_value={"zone_id": "zone-1"})

    with patch.object(maps, "_google_map_component", component), \
         patch.object(maps, "st", MagicMock()):
        selected_id = maps.render_priority_map(_priority_data(), key="test_priority_map")

    assert selected_id == "zone-1"
    args = component.call_args.kwargs
    assert args["map_type"] == "satellite"
    assert args["key"] == "test_priority_map"
    assert args["markers"][0]["id"] == "zone-1"
    assert args["markers"][0]["color"] == maps.PRIORITY_COLORS["High"]
    assert args["rsa_tiles"] == maps.RSA_ORTHOMOSAIC_TILES


def test_google_map_reports_missing_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)
    streamlit_mock = MagicMock()

    with patch.object(maps, "st", streamlit_mock), \
         patch.object(maps, "_google_map_component") as component:
        result = maps.render_priority_map(_priority_data(), key="missing_key_map")

    assert result is None
    component.assert_not_called()
    streamlit_mock.warning.assert_called_once()
    assert "GOOGLE_MAPS_API_KEY" in streamlit_mock.warning.call_args.args[0]


def test_segmentation_map_passes_enriched_boundaries_to_google_component(monkeypatch):
    from views import segment

    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test-google-maps-key")
    summary = pd.DataFrame([{
        "District": "Kigali",
        "Value": 3200,
        "Record count": 4,
        "Range": "Upper observed range",
    }])
    boundaries = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"district": "Kigali", "province": "Kigali City"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [29.8, -1.9],
                    [29.9, -1.9],
                    [29.9, -2.0],
                    [29.8, -2.0],
                    [29.8, -1.9],
                ]],
            },
        }],
    }

    with patch.object(segment, "_load_district_boundaries", return_value=boundaries), \
         patch.object(segment, "st", MagicMock()), \
         patch.object(segment, "render_google_map") as render_map:
        segment._render_comparison_map(
            summary,
            "Yield",
            "kg/ha",
            key="test_segmentation_map",
            satellite_default=True,
        )

    args = render_map.call_args.kwargs
    feature = args["geojson"]["features"][0]
    assert args["key"] == "test_segmentation_map"
    assert args["satellite_default"] is True
    assert args["fit_bounds"] is True
    assert args["markers"] is None
    assert feature["properties"]["metric_value"] == "3,200.0 kg/ha"
    assert feature["properties"]["style_color"] == segment.RANGE_COLORS["Upper observed range"]
    assert feature["properties"]["has_observations"] is True


def test_google_map_component_uses_maps_javascript_api_and_click_events():
    component_path = maps.Path(__file__).parent / "google_map_component"
    html = (component_path / "index.html").read_text(encoding="utf-8")
    script = (component_path / "google_map.js").read_text(encoding="utf-8")

    assert 'type: "streamlit:componentReady"' in script
    assert 'type: "streamlit:setComponentValue"' in script
    assert "maps.googleapis.com/maps/api/js" in script
    assert 'mapTypeIds: ["roadmap", "satellite"]' in script
    assert 'name: "Rwanda Space Agency orthomosaic"' in script
    assert 'aria-label="Interactive Google map"' in html


def test_google_map_loads_official_admin_levels_as_zoom_increases():
    assert [
        (level["name"], level["min_zoom"], level["layer_id"])
        for level in maps.ADMIN_BOUNDARY_LEVELS
    ] == [
        ("District", 0, 0),
        ("Sector", 9, 1),
        ("Cell", 12, 2),
        ("Village", 15, 3),
    ]

    component_path = maps.Path(__file__).parent / "google_map_component"
    script = (component_path / "google_map.js").read_text(encoding="utf-8")
    assert "map.addListener(\"idle\", scheduleBoundaryRefresh)" in script
    assert "geometryType: \"esriGeometryEnvelope\"" in script
    assert "spatialRel: \"esriSpatialRelIntersects\"" in script
    assert "resultRecordCount: \"1000\"" in script
    assert 'level.name_field' in script
