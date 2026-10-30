"""
Integration and rendering tests for core views (Dashboard, Decisions, Planning, Communication, Segmentation, Zones).
Ensures every view executes safely within error boundaries without raising unhandled exceptions.
"""
import unittest
from unittest.mock import MagicMock, patch
from views.communicate import render_communicate
from views.dashboard import render_dashboard
from views.decide import render_decide
from views.plan import render_plan
from views.segment import render_segment
from views.zones import render_zones


class TestViews(unittest.TestCase):

    @patch("views.dashboard.st")
    @patch("views.dashboard.api_client")
    def test_render_dashboard_executes_safely(self, mock_api, mock_st):
        mock_api.get_kpis.return_value = {
            "total_zones": 30,
            "baseline_yield_kg_ha": 3200,
            "active_alerts": 3,
        }
        mock_df = MagicMock()
        mock_df.empty = True
        mock_df.columns = []
        mock_api.get_priority_data.return_value = mock_df
        mock_api.get_agri_metrics.return_value = []
        mock_api.get_zones.return_value = [
            {"id": "z1", "district": "Gasabo", "crop": "Maize", "priority": "High", "risk_status": "At Risk", "area_ha": 40.0, "latitude": -1.9, "longitude": 30.1}
        ]
        mock_api.get_alerts.return_value = []
        mock_api.get_weather.return_value = {"temperature_c": 24, "humidity_pct": 65, "condition": "Clear"}

        mock_st.session_state = {}
        mock_st.sidebar = MagicMock()
        mock_st.sidebar.radio.return_value = "Dashboard"
        mock_st.sidebar.selectbox.return_value = "All"
        mock_st.sidebar.multiselect.return_value = []
        mock_st.columns.side_effect = lambda n, **kwargs: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        mock_st.container.return_value.__enter__.return_value = MagicMock()

        render_dashboard()
        self.assertTrue(mock_st.columns.called)

    @patch("views.decide.st")
    @patch("views.decide.api_client")
    def test_render_decide_executes_safely(self, mock_api, mock_st):
        mock_api.get_recommendations.return_value = [
            {
                "zone_id": "zone-1",
                "area": "Musanze",
                "crop": "Irish Potatoes",
                "season": "2026 Season A",
                "priority": "High",
                "text": "Apply fertilizer",
                "status": "Pending",
            }
        ]
        mock_api.get_crops.return_value = ["Maize", "Irish Potatoes"]
        mock_api.get_district_ranking.return_value = [
            {
                "district": "Musanze",
                "yield_per_ha": 3500.0,
                "benchmark_yield_per_ha": 3200.0,
                "yield_gap_kg_ha": 0.0,
                "observation_count": 12,
                "rank": 1,
            }
        ]
        mock_api.get_evidence_ranking.return_value = {
            "national_reference_kg_ha": 3200.0,
            "available_seasons": ["2026 Season A"],
            "interpretation": "District evidence only.",
        }
        mock_api.get_zones.return_value = [
            {"id": "zone-1", "district": "Musanze", "crop": "Irish Potatoes", "area_cultivated": 2.0}
        ]
        mock_api.predict_yield.return_value = {
            "yield_per_ha": 2400.0,
            "predicted_yield": 4800.0,
            "priority_level": "Medium",
            "district_observations": 12,
            "priority_reasons": ["Historical observations support this assessment."],
            "yield_data_status": "available",
        }
        mock_api.get_zone_recommendations.return_value = {
            "recommendations": ["Review soil moisture before planting."]
        }
        mock_st.selectbox.side_effect = lambda label, options, **kwargs: options[0]
        mock_st.button.return_value = False
        mock_st.checkbox.return_value = False
        mock_st.form_submit_button.return_value = True
        mock_st.chat_input.return_value = None
        mock_api.get_field_risk.return_value = None

        mock_st.session_state = {}
        mock_st.tabs.return_value = [MagicMock() for _ in range(4)]
        mock_st.columns.side_effect = lambda n, **kwargs: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        mock_st.form.return_value.__enter__.return_value = MagicMock()

        render_decide()
        self.assertTrue(mock_st.tabs.called)
        self.assertTrue(mock_api.get_evidence_ranking.called)
        mock_api.predict_yield.assert_called_once_with({
            "zone_id": "zone-1",
            "crop": "Maize",
            "season": "2026 Season A",
        })
        mock_api.get_zone_recommendations.assert_called_once_with("zone-1")

    @patch("views.plan.st")
    @patch("views.plan.api_client")
    def test_render_plan_executes_safely(self, mock_api, mock_st):
        mock_api.get_zones.return_value = [
            {"id": "zone-1", "district": "Musanze", "crop": "Irish Potatoes", "area_cultivated": 12.5}
        ]
        mock_api.get_zone_plans.return_value = [
            {
                "id": "plan-1",
                "title": "Season A Sowing Plan",
                "roadmap_json": [
                    {"step_number": 1, "title": "Field preparation", "status": "completed", "timeframe": "Week 1"},
                    {"step_number": 2, "title": "Sowing", "status": "in_progress", "timeframe": "Week 2"},
                ],
                "resources_json": {},
            }
        ]
        mock_api.get_plan_action_history.return_value = []
        mock_api.get_crops.return_value = ["Maize", "Beans"]

        mock_st.session_state = {"planning_pending_zone_id": "zone-1"}
        mock_st.button.return_value = False
        mock_st.tabs.return_value = [MagicMock() for _ in range(3)]
        mock_st.columns.side_effect = lambda n, **kwargs: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        mock_st.expander.return_value.__enter__.return_value = MagicMock()
        mock_st.popover.return_value.__enter__.return_value = MagicMock()
        mock_st.form.return_value.__enter__.return_value = MagicMock()

        render_plan()
        self.assertTrue(mock_api.get_zones.called)
        self.assertTrue(mock_api.get_zone_plans.called)
        self.assertEqual(mock_st.session_state["planning_zone_select"], "Musanze / Irish Potatoes")

    @patch("views.communicate.st")
    @patch("views.communicate.api_client")
    def test_render_communicate_executes_safely(self, mock_api, mock_st):
        mock_api.get_alerts.return_value = [
            {"type": "Warning", "message": "Heavy rain forecast", "timestamp": "1h ago"}
        ]
        mock_api.get_email_status.return_value = {"ready": True, "port": 587, "transport": "TLS"}
        mock_api.get_whatsapp_status_info.return_value = {"ready": True, "mode": "live"}
        mock_api.get_email_status.return_value = {"ready": True, "provider": "smtp"}
        mock_api.get_zones.return_value = [
            {"id": "zone-1", "district": "Rubavu"}
        ]
        mock_api.get_crops.return_value = ["Maize"]
        mock_api.render_admin_login.return_value = False

        mock_st.session_state = {}
        mock_st.button.return_value = False
        mock_st.tabs.return_value = [MagicMock() for _ in range(3)]
        mock_st.columns.side_effect = lambda n, **kwargs: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        mock_st.form.return_value.__enter__.return_value = MagicMock()

        render_communicate()
        self.assertTrue(mock_st.tabs.called)

    @patch("views.segment.st")
    @patch("views.segment.api_client")
    def test_render_segment_executes_safely(self, mock_api, mock_st):
        mock_df = MagicMock()
        mock_df.empty = True
        mock_df.columns = []
        mock_api.get_priority_data.return_value = mock_df

        mock_st.session_state = {}
        mock_st.columns.side_effect = lambda n, **kwargs: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        mock_st.container.return_value.__enter__.return_value = MagicMock()

        render_segment()
        self.assertTrue(mock_st.info.called)

    @patch("views.zones.st")
    @patch("views.zones.api_client")
    def test_render_zones_executes_safely(self, mock_api, mock_st):
        mock_api.get_zones.return_value = [
            {"id": "zone-1", "district": "Musanze", "sector": "Muhoza", "crop": "Irish Potatoes", "priority": "High", "risk_status": "Stable"}
        ]
        mock_api.get_zone_detail.return_value = {
            "id": "zone-1", "district": "Musanze", "sector": "Muhoza", "crop": "Irish Potatoes", "priority": "High"
        }

        mock_st.session_state = {}
        mock_st.columns.side_effect = lambda n, **kwargs: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        mock_st.container.return_value.__enter__.return_value = MagicMock()
        mock_st.expander.return_value.__enter__.return_value = MagicMock()

        render_zones()
        self.assertTrue(mock_st.columns.called)


if __name__ == "__main__":
    unittest.main()
