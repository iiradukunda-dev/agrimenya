from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

folium = pytest.importorskip("folium")

from components import maps


def _tile_layer_names(map_view):
    return {
        child.layer_name
        for child in map_view._children.values()
        if isinstance(child, folium.raster_layers.TileLayer)
    }


def test_priority_map_uses_shared_layers_and_keeps_marker_selection():
    points = pd.DataFrame([{
        "id": "zone-1",
        "Lat": -1.94,
        "Lon": 29.87,
        "District": "Kigali",
        "Crop": "Maize",
        "Priority": "High",
        "Production_MT": 12.5,
    }])
    streamlit_mock = MagicMock()

    with patch.object(maps, "st", streamlit_mock), \
         patch.object(maps, "st_folium", return_value={"last_object_clicked": {"lat": -1.94, "lng": 29.87}}) as render_map:
        selected_id = maps.render_priority_map(points, key="test_priority_map")

    assert selected_id == "zone-1"
    map_view = render_map.call_args.args[0]
    assert _tile_layer_names(map_view) == {"Street", "Satellite", "RSA orthomosaic"}
    assert any(isinstance(child, folium.map.LayerControl) for child in map_view._children.values())
    assert any(isinstance(child, folium.CircleMarker) for child in map_view._children.values())
    assert render_map.call_args.kwargs["height"] == 540


def test_segmentation_map_uses_shared_layers_and_district_interactions():
    from views import segment

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
         patch.object(segment, "st_folium") as render_map:
        segment._render_comparison_map(
            summary,
            "Yield",
            "kg/ha",
            key="test_segmentation_map",
            satellite_default=False,
        )

    map_view = render_map.call_args.args[0]
    assert _tile_layer_names(map_view) == {"Street", "Satellite", "RSA orthomosaic"}
    assert any(isinstance(child, folium.map.LayerControl) for child in map_view._children.values())
    assert any(isinstance(child, folium.features.GeoJson) for child in map_view._children.values())
    assert render_map.call_args.kwargs["returned_objects"] == []
