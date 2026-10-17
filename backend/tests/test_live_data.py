from unittest.mock import patch

from app.services.field_report_service import get_field_risk_summary, submit_field_report
from app.services.freshness_service import data_freshness_score
from app.services.live_data_service import build_live_context
from app.services.weather_service import fetch_weather


def test_fetch_weather_unknown_district_is_unavailable_without_network():
    weather = fetch_weather(district="Not a Rwanda district")
    assert weather["district"] == "Not a Rwanda district"
    assert weather["source"] == "unavailable"
    assert weather["rainfall_mm"] is None


def test_submit_field_report_and_risk_summary():
    report = {"zone_id": "zone-1", "district": "Gasabo", "crop": "Maize",
              "rainfall_mm": 20.0, "soil_moisture_pct": 33.0,
              "symptoms": "yellow leaves and brown lesions"}
    with patch("app.services.field_report_service.crud.create_field_report", return_value=report) as create_report, \
         patch("app.services.field_report_service.crud.list_field_reports", return_value=[report]):
        result = submit_field_report(
            zone_id="zone-1", district="Gasabo", crop="Maize", rainfall_mm=20.0,
            soil_moisture_pct=33.0, symptoms="yellow leaves and brown lesions",
            notes="Field appears to be drying quickly.",
        )
        risk = get_field_risk_summary(crop="Maize", zone_id="zone-1")

    assert result["zone_id"] == "zone-1"
    create_report.assert_called_once()
    assert risk["total_reports"] == 1
    assert risk["risk_level"] == "Medium"


def test_live_context_has_freshness_and_weather():
    with patch("app.services.live_data_service.fetch_weather", return_value={
        "district": "Gasabo", "source": "unavailable", "updated_at": None,
        "rainfall_mm": None, "forecast": [],
    }), patch("app.db.crud.list_field_reports", return_value=[]):
        context = build_live_context(zone_id="zone-1", district="Gasabo", crop="Maize")
    assert context["source"] == "hybrid-live-baseline"
    assert context["weather"]["district"] == "Gasabo"
    assert context["weather"]["source"] == "unavailable"
    assert "freshness" in context
    assert isinstance(context["freshness"]["freshness_score"], float)


def test_freshness_score_handles_missing_timestamp():
    score = data_freshness_score(None)
    assert score["status"] == "stale"
    assert score["freshness_score"] == 0.0
