"""
Unit tests for extended API client methods covering Decision, Planification, and Communication.
Uses standard library unittest for portability across container runtimes and test runners.
"""
import unittest
from unittest.mock import MagicMock, patch
from utils import api_client


class TestApiClientExtended(unittest.TestCase):

    @patch("utils.api_client._get_api")
    def test_get_official_yields_uses_historical_segmentation_endpoint(self, mock_get):
        rows = [{"crop": "Maize", "season": "2022 Season A", "yield_actual": "1200"}]
        mock_get.return_value = rows
        api_client.get_official_yields.clear()

        result = api_client.get_official_yields()

        self.assertEqual(result, rows)
        mock_get.assert_called_once_with("/segmentation/official-yields", timeout=20)
        api_client.get_official_yields.clear()

    @patch("utils.api_client._get_api")
    def test_get_districts_uses_canonical_backend_directory(self, mock_get):
        districts = [{"district": "Huye", "province": "Southern Province"}]
        mock_get.return_value = districts
        api_client.get_districts.clear()

        result = api_client.get_districts()

        self.assertEqual(result, districts)
        mock_get.assert_called_once_with("/segmentation/districts")
        api_client.get_districts.clear()

    def test_get_model_info_fallback(self):
        """Verify get_model_info returns structured model diagnostics with mock fallback."""
        with patch.object(api_client, "USE_MOCK_DATA", True):
            info = api_client.get_model_info()
            self.assertIsNotNone(info)
            self.assertIn("metrics", info)
            self.assertIn("features", info)
            self.assertIn("known_limitations", info)
            self.assertIn("active_basis", info)

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
