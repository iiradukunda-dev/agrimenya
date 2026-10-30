from unittest.mock import MagicMock, patch

from views.segment import _load_administrative_locations


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
