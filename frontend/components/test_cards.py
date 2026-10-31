"""
Unit tests for executive card components and SVG sparklines in frontend.
"""
import unittest
from unittest.mock import MagicMock, patch
from components.cards import (
    generate_svg_sparkline,
    pillar_card,
    render_empty_state,
    render_kpi_card,
    render_weather_forecast_grid,
)


class TestCards(unittest.TestCase):

    def test_generate_svg_sparkline_valid(self):
        data = [10.0, 15.5, 12.0, 22.0, 18.0]
        svg = generate_svg_sparkline(data, color="#10b981", width=80, height=26)
        self.assertIn("<svg", svg)
        self.assertIn('stroke="#10b981"', svg)
        self.assertIn("<polyline", svg)
        self.assertIn("<circle", svg)

    def test_generate_svg_sparkline_edge_cases(self):
        self.assertEqual(generate_svg_sparkline([]), "")
        self.assertEqual(generate_svg_sparkline([5.0]), "")

    @patch("components.cards.st")
    def test_render_kpi_card_with_col(self, mock_st):
        mock_col = MagicMock()
        render_kpi_card(
            col=mock_col,
            title="Total Farmers",
            value="14,250",
            delta=5.4,
            sparkline_data=[10, 12, 14],
        )
        self.assertTrue(mock_st.markdown.called)

    @patch("components.cards.st")
    def test_render_kpi_card_with_subtitle_and_no_col(self, mock_st):
        render_kpi_card(
            title="National Reference",
            value="3,200 kg/ha",
            subtitle="NISR Target Benchmark",
        )
        self.assertTrue(mock_st.markdown.called)
        args, kwargs = mock_st.markdown.call_args
        html_rendered = args[0]
        self.assertIn("National Reference", html_rendered)
        self.assertIn("3,200 kg/ha", html_rendered)
        self.assertIn("NISR Target Benchmark", html_rendered)

    @patch("components.cards.st")
    def test_render_weather_forecast_grid(self, mock_st):
        forecasts = [
            {"date": "2026-10-27", "temperature_max_c": 26, "temperature_min_c": 16, "precipitation_probability_pct": 20, "precipitation_sum_mm": 1.2},
            {"date": "2026-10-28", "temperature_max_c": 24, "temperature_min_c": 15, "precipitation_probability_pct": 70, "precipitation_sum_mm": 12.4},
        ]
        render_weather_forecast_grid(forecasts)
        self.assertTrue(mock_st.markdown.called)
        rendered = mock_st.markdown.call_args[0][0]
        self.assertIn("ag-weather-row", rendered)
        self.assertIn("26° / 16°", rendered)

    @patch("components.cards.st")
    def test_render_empty_state(self, mock_st):
        render_empty_state("No Records", "No farmer records match the active filter.")
        self.assertTrue(mock_st.markdown.called)
        rendered = mock_st.markdown.call_args[0][0]
        self.assertIn("ag-empty-title", rendered)
        self.assertIn("No Records", rendered)

    @patch("components.cards.st")
    def test_pillar_card(self, mock_st):
        mock_col = MagicMock()
        mock_st.button.return_value = False
        pillar_card(
            col=mock_col,
            title="Segmentation",
            desc="Identify high-priority agricultural zones.",
            btn_text="Segment",
            page_route="pages/7_Segmentation.py",
        )
        self.assertTrue(mock_st.markdown.called)
        self.assertTrue(mock_st.button.called)


if __name__ == "__main__":
    unittest.main()
