from views.decide import _available_ranking_seasons, _format_yield, _zone_options


def test_available_ranking_seasons_uses_backend_season_values():
    options = _available_ranking_seasons({
        "available_seasons": ["2022 Season A", "2026 Season B", "2022 Season A"],
    })

    assert options == [
        "All available seasons",
        "2026 Season B",
        "2022 Season A",
    ]


def test_format_yield_displays_missing_and_non_finite_values_as_unavailable():
    assert _format_yield(1250.25) == "1,250.2 kg/ha"
    assert _format_yield(10, "kg") == "10.0 kg"
    assert _format_yield(None) == "Not available"
    assert _format_yield(float("nan")) == "Not available"


def test_zone_options_use_registered_zone_context_and_unique_labels():
    options = _zone_options([
        {"id": "12345678-a", "district": "Huye", "sector": "Ruhashya", "cell": "Gatobotobo"},
        {"id": "12345678-b", "district": "Huye", "sector": "Ruhashya", "cell": "Gatobotobo"},
        {"district": "No ID"},
    ])

    assert list(options) == [
        "Huye / Ruhashya / Gatobotobo · 123456",
        "Huye / Ruhashya / Gatobotobo · 12345678-b",
    ]
    assert len(options) == 2
