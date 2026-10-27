"""
Unit tests for responsive Plotly chart components.
"""
import unittest
from unittest.mock import MagicMock, patch
from components.charts import (
    get_plotly_layout,
    render_crop_comparison_bar,
    render_district_ranking_chart,
    render_priority_donut_chart,
    render_yield_chart,
)


class TestCharts(unittest.TestCase):

    @patch("components.charts.get_current_theme")
    def test_get_plotly_layout_light_mode(self, mock_theme):
        mock_theme.return_value = "light"
        layout = get_plotly_layout()
        self.assertIn("font", layout)
        self.assertIn("Inter", layout["font"]["family"])
        self.assertEqual(layout["font"]["color"], "#1e293b")
        self.assertEqual(layout["paper_bgcolor"], "rgba(0,0,0,0)")

    @patch("components.charts.get_current_theme")
    def test_get_plotly_layout_dark_mode(self, mock_theme):
        mock_theme.return_value = "dark"
        layout = get_plotly_layout()
        self.assertEqual(layout["font"]["color"], "#f8fafc")

    @patch("components.charts.st")
    def test_render_empty_dataframes(self, mock_st):
        mock_df = MagicMock()
        mock_df.empty = True
        mock_df.columns = []

        render_yield_chart(mock_df)
        self.assertTrue(mock_st.info.called)

        render_priority_donut_chart(mock_df)
        self.assertTrue(mock_st.info.called)

        render_crop_comparison_bar(mock_df)
        self.assertTrue(mock_st.info.called)

        render_district_ranking_chart([], crop="Maize")
        self.assertTrue(mock_st.info.called)

    @patch("components.charts.st")
    @patch("components.charts.px")
    def test_render_district_ranking_chart_valid(self, mock_px, mock_st):
        if mock_px is None:
            self.skipTest("Plotly Express not installed in host environment")

        mock_fig = MagicMock()
        mock_px.bar.return_value = mock_fig

        rankings = [
            {"district": "Musanze", "yield_per_ha": 3500.0, "rank": 1},
            {"district": "Nyagatare", "yield_per_ha": 3100.0, "rank": 2},
        ]
        render_district_ranking_chart(rankings, crop="Maize", national_ref=3200.0)

        self.assertTrue(mock_px.bar.called)
        self.assertTrue(mock_st.plotly_chart.called)
        self.assertTrue(mock_fig.add_hline.called)


if __name__ == "__main__":
    unittest.main()
