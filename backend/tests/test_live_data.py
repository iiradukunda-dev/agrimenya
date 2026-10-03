from app.services.field_report_service import get_field_risk_summary, submit_field_report
from app.services.freshness_service import data_freshness_score
from app.services.live_data_service import build_live_context
from app.services.weather_service import fetch_weather


def test_fetch_weather_returns_fallback_snapshot_without_network():
    weather = fetch_weather(district="Gasabo")
    assert weather["district"] == "Gasabo"
    assert weather["source"] in {"fallback", "open-meteo"}
    assert isinstance(weather["rainfall_mm"], (int, float))


def test_submit_field_report_and_risk_summary():
    report = submit_field_report(
        zone_id="zone-1",
        district="Gasabo",
        crop="Maize",
        rainfall_mm=20.0,
        soil_moisture_pct=33.0,
        symptoms="yellow leaves and brown lesions",
        notes="Field appears to be drying quickly.",
    )

    assert report["zone_id"] == "zone-1"
    risk = get_field_risk_summary(crop="Maize")
    assert risk["total_reports"] >= 1
    assert risk["risk_level"] in {"Low", "Medium", "High"}


def test_live_context_has_freshness_and_weather():
    context = build_live_context(zone_id="zone-1", district="Gasabo", crop="Maize")
    assert context["source"] == "hybrid-live-baseline"
    assert context["weather"]["district"] == "Gasabo"
    assert "freshness" in context
    assert isinstance(context["freshness"]["freshness_score"], float)


def test_freshness_score_handles_missing_timestamp():
    score = data_freshness_score(None)
    assert score["status"] == "stale"
    assert score["freshness_score"] == 0.0
