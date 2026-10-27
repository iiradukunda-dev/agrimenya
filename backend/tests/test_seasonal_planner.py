from datetime import date
from unittest.mock import patch

from app.services import seasonal_planner


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_builds_upcoming_maize_plan_from_fao_and_nisr():
    zones = [{
        "zone_id": "006",
        "name": "Eastern Plateau & Eastern Savanna",
        "administratrative_units": "Nyarugenge, Nyagatare, Gasabo, Gatsibo",
    }]
    crops = [{"crop_name": "Corn", "other_name": "Corn", "crop_id": "0338"}]
    calendar = [{
        "lastUpdated": "19/08/2025",
        "crop": {"id": "0338", "name": "Corn", "cropParent": {}},
        "aez": {"id": "006", "name": "Eastern Plateau & Eastern Savanna"},
        "sessions": [
            {
                "early_sowing": {"day": 15, "month": 9},
                "later_sowing": {"day": 15, "month": 10},
                "early_harvest": {"day": 1, "month": 12},
                "late_harvest": {"day": 15, "month": 2},
                "growing_period": {"value": "100-120", "period": "Days"},
                "sowing_rate": {"value": "30-50", "unit": "kg/ha"},
            },
            {
                "early_sowing": {"day": 15, "month": 1},
                "later_sowing": {"day": 28, "month": 2},
                "early_harvest": {"day": 15, "month": 4},
                "late_harvest": {"day": 30, "month": 6},
                "growing_period": {"value": "100-120", "period": "Days"},
                "sowing_rate": {"value": "30-50", "unit": "kg/ha"},
            },
        ],
    }]
    payloads = [zones, crops, calendar]
    with patch.object(seasonal_planner, "_FAO_CACHE", None), \
         patch.object(seasonal_planner.httpx, "get", side_effect=[
             FakeResponse(payload) for payload in payloads
         ]), \
         patch.object(seasonal_planner, "known_crops", return_value=["Maize"]), \
         patch.object(seasonal_planner, "get_district_evidence_ranking", return_value={
             "national_reference_kg_ha": 2100,
             "districts_with_evidence": 25,
             "rows": [{
                 "district": "Gasabo", "yield_kg_ha": 1800, "rank": 20,
                 "observation_count": 3, "seasons": ["2026 Season A"],
                 "trend_change_pct": -5.0, "trend_season_code": "A",
                 "sources": ["Bundled official NISR SAS history"],
             }],
             "interpretation": "District comparison only.",
         }), \
         patch.object(seasonal_planner, "fetch_weather", return_value={
             "source": "unavailable", "forecast": [],
         }):
        result = seasonal_planner.build_seasonal_draft(
            district="Gasabo",
            crop="Maize",
            area_ha=2,
            today=date(2026, 10, 26),
        )

    assert result["status"] == "ready"
    assert result["calendar"]["aez"] == "Eastern Plateau & Eastern Savanna"
    assert result["calendar"]["sowing_start"] == "2027-01-15"
    assert result["calendar"]["source_is_old"]
    assert result["calendar"]["sowing_rate"]["quantity_min"] == 60
    assert result["calendar"]["sowing_rate"]["quantity_max"] == 100
    assert result["nisr_evidence"]["district_yield_kg_ha"] == 1800
    assert len(result["roadmap"]) == 4
    assert result["roadmap"][1]["due_date"] == "2027-01-15"
    progress_action = result["roadmap"][2]
    assert progress_action["title"] == "Check Maize field progress"
    assert "NISR" not in progress_action["description"]
    assert "district" not in progress_action["description"]
    assert "NISR" not in result["roadmap"][3]["description"]


def test_returns_clear_status_when_district_has_no_fao_zone():
    with patch.object(seasonal_planner, "_FAO_CACHE", (
        1e30,
        {"zones": [], "crops": [], "calendar": [], "fetched_at": "test"},
    )):
        result = seasonal_planner.build_seasonal_draft(
            district="Gicumbi", crop="Maize", today=date(2026, 10, 26),
        )

    assert result["status"] == "calendar_unavailable_for_district"
    assert result["roadmap"] == []
