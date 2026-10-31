"""
Unit tests for extended API client methods covering Decision, Planification, and Communication.
Uses standard library unittest for portability across container runtimes and test runners.
"""
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
import requests
from utils import api_client


class TestApiClientExtended(unittest.TestCase):

    def test_zone_api_failure_is_not_cached_as_empty_data(self):
        zone = {"id": "zone-1", "district": "Huye"}
        api_client.clear_zones_cache()
        with patch.object(api_client.st, "session_state", {}) as session_state, patch.object(
            api_client, "USE_MOCK_DATA", False
        ), patch.object(api_client, "_get_api", side_effect=[None, [zone], []]) as get_api:
            try:
                self.assertEqual(api_client.get_zones(), [])
                self.assertTrue(session_state["zones_api_unavailable"])

                zones = api_client.get_zones()
                self.assertEqual(zones[0]["name"], "Huye")
                self.assertNotIn("zones_api_unavailable", session_state)
                self.assertEqual(get_api.call_count, 3)
            finally:
                api_client.clear_zones_cache()

    @patch("utils.api_client.requests.get")
    @patch("utils.api_client._get_api")
    def test_weather_falls_back_to_district_weather_and_requests_kmh(self, mock_api, mock_get):
        mock_api.return_value = {"district": "Bugesera", "temperature_c": None}
        response = MagicMock()
        response.json.return_value = {
            "current": {
                "temperature_2m": 22.0,
                "relative_humidity_2m": 65,
                "precipitation": 0.0,
                "wind_speed_10m": 12.5,
                "weather_code": 1,
                "time": "2026-10-30T12:00",
            },
            "daily": {
                "time": ["2026-10-30"],
                "temperature_2m_max": [25.0],
                "temperature_2m_min": [17.0],
                "precipitation_probability_max": [50],
                "precipitation_sum": [2.0],
            },
        }
        response.raise_for_status = MagicMock()
        mock_get.return_value = response
        api_client.get_weather.clear()

        try:
            weather = api_client.get_weather("Bugesera")
            self.assertEqual(weather["wind_kph"], 12.5)
            self.assertEqual(weather["source"], "Open-Meteo Live API")
            self.assertEqual(mock_get.call_args.kwargs["params"]["wind_speed_unit"], "kmh")
        finally:
            api_client.get_weather.clear()

    @patch("utils.api_client.requests.get")
    def test_direct_weather_does_not_use_kigali_for_unknown_district(self, mock_get):
        self.assertIsNone(api_client._fetch_direct_open_meteo("Unknown district"))
        mock_get.assert_not_called()

    @patch("utils.api_client._get_api")
    def test_get_official_yields_uses_api_when_bundled_copy_is_unavailable(self, mock_get):
        rows = [{"crop": "Maize", "season": "2022 Season A", "yield_actual": "1200"}]
        mock_get.return_value = rows
        with patch.object(api_client, "_get_bundled_official_yields", return_value=[]):
            api_client.get_official_yields.clear()
            result = api_client.get_official_yields()

        api_client.get_official_yields.clear()

        self.assertEqual(result, rows)
        mock_get.assert_called_once_with(
            "/segmentation/official-yields", timeout=2, retry_on_transient=False
        )

    def test_bundled_nisr_yields_are_available_without_api(self):
        source = (
            Path(__file__).resolve().parents[2]
            / "backend"
            / "data"
            / "nisr_official_yields_2022_2026.csv"
        )
        frontend_copy = api_client._BUNDLED_NISR_PATH
        self.assertEqual(source.read_bytes(), frontend_copy.read_bytes())

        api_client._get_bundled_official_yields.clear()
        rows = api_client.get_official_yields()
        self.assertGreater(len(rows), 6000)
        self.assertIn("Musanze", {row["district"] for row in rows})
        self.assertIn("Maize", {row["crop"] for row in rows})
        self.assertEqual(rows[0]["data_source"], "official_nisr_sas")
        api_client._get_bundled_official_yields.clear()

    @patch("utils.api_client._get_api")
    def test_get_districts_uses_canonical_backend_directory(self, mock_get):
        districts = [{"district": "Huye", "province": "Southern Province"}]
        mock_get.return_value = districts
        api_client.get_districts.clear()

        result = api_client.get_districts()

        self.assertEqual(result, districts)
        mock_get.assert_called_once_with(
            "/segmentation/districts", timeout=2, retry_on_transient=False
        )
        api_client.get_districts.clear()

    def test_decision_crops_do_not_show_mock_choices_when_backend_is_unavailable(self):
        with patch.object(api_client, "USE_MOCK_DATA", False), patch.object(
            api_client, "_get_api", return_value=None
        ):
            api_client.get_crops.clear()
            try:
                crops = api_client.get_crops()
                self.assertIn("Maize", crops)
                self.assertGreater(len(crops), 0)
            finally:
                api_client.get_crops.clear()

    def test_nisr_evidence_ranking_remains_available_when_api_is_unavailable(self):
        with patch.object(api_client, "USE_MOCK_DATA", False), patch.object(
            api_client, "_get_api", return_value=None
        ):
            api_client.get_evidence_ranking.clear()
            api_client.get_district_ranking.clear()
            try:
                evidence = api_client.get_evidence_ranking("Maize")
                rankings = api_client.get_district_ranking("Maize")
                self.assertTrue(evidence["offline_fallback"])
                self.assertGreater(evidence["districts_with_evidence"], 0)
                self.assertEqual(rankings[0]["rank"], 1)
                self.assertEqual(
                    rankings[0]["data_source"],
                    "Bundled official NISR SAS history",
                )
            finally:
                api_client.get_evidence_ranking.clear()
                api_client.get_district_ranking.clear()

    def test_offline_nisr_advisor_returns_historical_district_evidence(self):
        rows = [
            {
                "crop": "Maize",
                "district": "Huye",
                "season": "2024 Season A",
                "production_mt": "1.2",
                "harvested_area_ha": "1",
                "yield_actual": "1200",
            },
            {
                "crop": "Maize",
                "district": "Musanze",
                "season": "2024 Season A",
                "production_mt": "2",
                "harvested_area_ha": "1",
                "yield_actual": "2000",
            },
        ]
        with patch.object(api_client, "_get_bundled_official_yields", return_value=rows):
            response = api_client.get_offline_nisr_advisor_response(
                "What is the historical yield?",
                "Maize",
                district="Huye",
                season="2024 Season A",
            )

        self.assertIn("1,200.0 kg/ha", response["answer"])
        self.assertIn("ranks 2 of 2 districts", response["answer"])
        self.assertEqual(response["source"], "offline_nisr")
        self.assertTrue(response["offline_fallback"])
        self.assertIn("a farm or zone assessment", response["answer"])

    def test_offline_nisr_advisor_has_no_answer_for_unavailable_crop(self):
        with patch.object(api_client, "_get_bundled_official_yields", return_value=[]):
            self.assertIsNone(
                api_client.get_offline_nisr_advisor_response(
                    "What should I do?", "Unknown crop"
                )
            )

    def test_ai_zone_lookup_can_return_without_cold_start_retry(self):
        api_client.clear_zones_cache()
        with patch.object(api_client, "USE_MOCK_DATA", False), patch.object(
            api_client, "_get_api", return_value=None
        ) as get_api:
            try:
                zones = api_client.get_zones(
                    timeout=3,
                    retry_on_transient=False,
                    include_map=False,
                )
                self.assertEqual(zones, [])
                get_api.assert_called_once_with(
                    "/segmentation/zones",
                    timeout=3,
                    retry_on_transient=False,
                )
            finally:
                api_client.clear_zones_cache()

    def test_ai_zone_lookup_skips_map_data(self):
        zone = {"id": "zone-1", "district": "Huye"}
        api_client.clear_zones_cache()
        with patch.object(api_client, "USE_MOCK_DATA", False), patch.object(
            api_client, "_get_api", return_value=[zone]
        ) as get_api:
            try:
                zones = api_client.get_zones(
                    timeout=3,
                    retry_on_transient=False,
                    include_map=False,
                )
                self.assertEqual(zones[0]["name"], "Huye")
                get_api.assert_called_once_with(
                    "/segmentation/zones",
                    timeout=3,
                    retry_on_transient=False,
                )
            finally:
                api_client.clear_zones_cache()

    @patch("utils.api_client._get_api")
    def test_api_liveness_check_does_not_retry(self, mock_get):
        mock_get.return_value = {"status": "alive"}

        self.assertTrue(api_client.is_api_available(timeout=2))
        mock_get.assert_called_once_with(
            "/health/live",
            timeout=2,
            retry_on_transient=False,
        )

    @patch("utils.api_client.time.sleep")
    @patch("utils.api_client.requests.get")
    def test_transient_api_failure_retries_with_cold_start_timeout(
        self, mock_get, _mock_sleep
    ):
        response = MagicMock()
        response.json.return_value = {"status": "ok"}
        response.raise_for_status = MagicMock()
        mock_get.side_effect = [requests.Timeout("Render cold start"), response]

        self.assertEqual(api_client._get_api("/health", timeout=10), {"status": "ok"})
        self.assertEqual(
            [call.kwargs["timeout"] for call in mock_get.call_args_list],
            [10, 60],
        )

    def test_recommendations_use_backend_saved_assessments_and_action_guidance(self):
        rows = [{
            "zone_id": "zone-123",
            "crop": "Maize",
            "season": "2026 Season A",
            "priority_level": "High",
            "zones": {"district": "Huye"},
            "recommendations": ["Review drainage", "Check soil moisture"],
        }]
        with patch.object(api_client, "USE_MOCK_DATA", False), patch.object(
            api_client, "_get_api", return_value=rows
        ) as get_api:
            api_client.get_recommendations.clear()
            try:
                result = api_client.get_recommendations()
            finally:
                api_client.get_recommendations.clear()

        get_api.assert_called_once_with(
            "/decision/priority-ranking",
            params={"include_recommendations": "true", "limit": 20},
        )
        self.assertEqual(result, [{
            "zone_id": "zone-123",
            "area": "Huye",
            "crop": "Maize",
            "season": "2026 Season A",
            "priority": "High",
            "text": "Review drainage Check soil moisture",
            "recommendations": ["Review drainage", "Check soil moisture"],
            "status": "Pending",
        }])

    def test_get_district_ranking_mock(self):
        """Verify get_district_ranking returns district list with benchmarks and yield gaps."""
        with patch.object(api_client, "USE_MOCK_DATA", True):
            rankings = api_client.get_district_ranking(crop="Maize")
            self.assertIsInstance(rankings, list)
            self.assertGreater(len(rankings), 0)
            first = rankings[0]
            self.assertIn("district", first)
            self.assertIn("yield_per_ha", first)
            self.assertIn("benchmark_yield_per_ha", first)
            self.assertIn("yield_gap_kg_ha", first)

    @patch("requests.get")
    def test_get_district_ranking_api(self, mock_get):
        """Verify get_district_ranking queries backend with query parameters."""
        with patch.object(api_client, "USE_MOCK_DATA", False):
            mock_resp = MagicMock()
            mock_resp.json.return_value = [
                {"district": "Musanze", "yield_per_ha": 3500.0, "rank": 1}
            ]
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            result = api_client.get_district_ranking(crop="Irish Potatoes", season="Season A")
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["district"], "Musanze")
            self.assertTrue(mock_get.called)
            call_url = mock_get.call_args[0][0]
            self.assertIn("/decision/district-ranking", call_url)

    @patch("requests.post")
    def test_get_disease_risk(self, mock_post):
        """Verify get_disease_risk POSTs symptoms and returns assessment."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "crop": "Maize",
            "predicted_disease": "Maize Lethal Necrosis",
            "confidence": 0.92,
            "risk_level": "High",
            "recommended_actions": ["Rogue infected plants"],
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = api_client.get_disease_risk(
            zone_id="12345",
            crop="Maize",
            symptoms="Yellow mottling and stunted growth",
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["predicted_disease"], "Maize Lethal Necrosis")
        self.assertEqual(result["risk_level"], "High")
        self.assertTrue(mock_post.called)

    @patch("utils.api_client.requests.post")
    def test_chat_sends_recent_zone_context_to_backend(self, mock_post):
        response = MagicMock()
        response.json.return_value = {"answer": "Use the zone's seasonal rainfall context."}
        response.raise_for_status = MagicMock()
        mock_post.return_value = response

        result = api_client.chat(
            "How should I prepare?",
            zone_id="zone-123",
            history=[{"role": "user", "content": "I grow maize."}],
            crop="Maize",
            season="2026 Season A",
        )

        self.assertEqual(result["answer"], "Use the zone's seasonal rainfall context.")
        self.assertEqual(mock_post.call_args.kwargs["json"], {
            "question": "How should I prepare?",
            "zone_id": "zone-123",
            "history": [{"role": "user", "content": "I grow maize."}],
            "crop": "Maize",
            "season": "2026 Season A",
        })

    @patch("utils.api_client.requests.post")
    def test_disease_upload_rewinds_image_before_multipart_request(self, mock_post):
        response = MagicMock()
        response.json.return_value = {"predicted_disease": "Unconfirmed"}
        response.raise_for_status = MagicMock()
        mock_post.return_value = response
        image_file = MagicMock()
        image_file.name = "leaf.png"
        image_file.type = "image/png"

        result = api_client.disease_detect_upload(
            "Maize",
            "Yellowing leaves",
            "zone-123",
            image_file,
        )

        self.assertEqual(result["predicted_disease"], "Unconfirmed")
        image_file.seek.assert_called_once_with(0)
        self.assertEqual(mock_post.call_args.kwargs["files"]["image"], (
            "leaf.png",
            image_file,
            "image/png",
        ))

    @patch("requests.patch")
    def test_update_plan_action_status(self, mock_patch):
        """Verify update_plan_action_status sends PATCH to plan action endpoint."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "plan-1", "status": "in_progress"}
        mock_resp.raise_for_status = MagicMock()
        mock_patch.return_value = mock_resp

        result = api_client.update_plan_action_status(
            plan_id="plan-1",
            step_number=2,
            status="in_progress",
            change_note="Tractor arrived on field",
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "in_progress")
        self.assertTrue(mock_patch.called)
        call_url = mock_patch.call_args[0][0]
        self.assertIn("/planification/plans/plan-1/actions/2", call_url)

    @patch("requests.post")
    def test_send_shared_plan(self, mock_post):
        """Verify send_shared_plan posts recipient email."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "sent", "recipient": "officer@test.rw"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = api_client.send_shared_plan(
            plan_id="plan-99",
            email="officer@test.rw",
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "sent")
        self.assertTrue(mock_post.called)
        call_url = mock_post.call_args[0][0]
        self.assertIn("/communication/share/plan-99/send", call_url)

    @patch("requests.get")
    def test_get_email_status(self, mock_get):
        """Verify get_email_status queries /communication/email-status."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ready": True, "port": 587, "transport": "STARTTLS"}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = api_client.get_email_status()
        self.assertIsNotNone(result)
        self.assertTrue(result["ready"])
        self.assertEqual(result["port"], 587)


if __name__ == "__main__":
    unittest.main()
