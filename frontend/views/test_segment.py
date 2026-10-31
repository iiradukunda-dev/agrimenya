from unittest.mock import MagicMock, patch

from views.segment import (
    _load_administrative_locations,
    _load_cell_boundaries,
    _location_map_viewport,
    _parse_google_location_selection,
    _parse_map_drill_key,
)


def test_administrative_location_directory_pages_through_all_cells():
    page_one = MagicMock()
    page_one.json.return_value = {
        "features": [{
            "attributes": {"district": "Huye", "sector": "Ruhashya", "cell": "Gatobotobo"},
        }],
        "exceededTransferLimit": True,
    }
    page_two = MagicMock()
    page_two.json.return_value = {
        "features": [{
            "attributes": {"district": "Musanze", "sector": "Muhoza", "cell": "Mpenge"},
        }],
        "exceededTransferLimit": False,
    }
    _load_administrative_locations.clear()

    with patch("views.segment.requests.get", side_effect=[page_one, page_two]) as mock_get:
        locations = _load_administrative_locations()

    assert locations.to_dict("records") == [
        {"District": "Huye", "Sector": "Ruhashya", "Cell": "Gatobotobo"},
        {"District": "Musanze", "Sector": "Muhoza", "Cell": "Mpenge"},
    ]
    assert mock_get.call_count == 2
    assert mock_get.call_args_list[0].kwargs["params"]["resultOffset"] == 0
    assert mock_get.call_args_list[1].kwargs["params"]["resultOffset"] == 1
    assert mock_get.call_args_list[0].kwargs["params"]["returnGeometry"] == "false"
    _load_administrative_locations.clear()


def test_selected_district_cell_boundaries_include_geometry():
    response = MagicMock()
    response.json.return_value = {
        "features": [{
            "type": "Feature",
            "properties": {"district": "Bugesera", "sector": "Rweru", "cell": "Batima"},
            "geometry": {"type": "Polygon", "coordinates": [[[30.1, -2.2], [30.2, -2.2]]]},
        }],
        "exceededTransferLimit": False,
    }
    _load_cell_boundaries.clear()

    with patch("views.segment.requests.get", return_value=response) as mock_get:
        boundaries = _load_cell_boundaries("Bugesera")

    assert boundaries["features"][0]["properties"]["cell"] == "Batima"
    assert mock_get.call_args.kwargs["params"]["where"] == "district='Bugesera'"
    assert mock_get.call_args.kwargs["params"]["returnGeometry"] == "true"
    _load_cell_boundaries.clear()


def test_map_click_tooltip_decodes_location_levels():
    assert _parse_map_drill_key("district|Huye") == ("district", "Huye")
    assert _parse_map_drill_key("<div>sector|Huye|Ruhashya</div>") == (
        "sector",
        "Huye",
        "Ruhashya",
    )
    assert _parse_map_drill_key("cell|Huye|Ruhashya|Gatobotobo") == (
        "cell",
        "Huye",
        "Ruhashya",
        "Gatobotobo",
    )
    assert _parse_map_drill_key("unexpected|location") is None


def test_google_map_click_decodes_location_levels():
    assert _parse_google_location_selection({
        "admin_location": {"district": "Huye"},
    }) == ("district", "Huye")
    assert _parse_google_location_selection({
        "admin_location": {"district": "Huye", "sector": "Ruhashya"},
    }) == ("sector", "Huye", "Ruhashya")
    assert _parse_google_location_selection({
        "admin_location": {"district": "Huye", "sector": "Ruhashya", "cell": "Gatobotobo"},
    }) == ("cell", "Huye", "Ruhashya", "Gatobotobo")


def test_google_map_click_rejects_incomplete_or_unexpected_location():
    assert _parse_google_location_selection({"admin_location": {"sector": "Ruhashya"}}) is None
    assert _parse_google_location_selection({
        "admin_location": {"district": "Huye", "cell": "Gatobotobo"},
    }) is None
    assert _parse_google_location_selection("district|Huye") is None


def test_google_map_viewport_centers_on_selected_sector_or_cell():
    boundaries = {
        "features": [
            {
                "properties": {"district": "Huye", "sector": "Ruhashya", "cell": "Gatobotobo"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[29.0, -2.5], [29.2, -2.5], [29.2, -2.3], [29.0, -2.3]]],
                },
            },
            {
                "properties": {"district": "Huye", "sector": "Mukura", "cell": "Rango"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[29.4, -2.7], [29.6, -2.7], [29.6, -2.5], [29.4, -2.5]]],
                },
            },
        ],
    }
    with patch("views.segment._load_cell_boundaries", return_value=boundaries):
        assert _location_map_viewport("Huye", ("Huye", "Ruhashya"), None) == (
            {"lat": -2.4, "lng": 29.1},
            13,
        )
        assert _location_map_viewport(
            "Huye",
            ("Huye", "Ruhashya"),
            ("Huye", "Ruhashya", "Gatobotobo"),
        ) == ({"lat": -2.4, "lng": 29.1}, 16)
