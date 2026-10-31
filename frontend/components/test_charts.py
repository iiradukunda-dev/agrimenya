"""
Unit tests for responsive Plotly chart components.
"""
import unittest
from unittest.mock import MagicMock, patch
from components.charts import (
    build_3d_scatter,
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

    @patch("components.charts.get_current_theme", return_value="light")
    @patch("components.charts.px")
    def test_build_3d_scatter_sets_scene_axes(self, mock_px, _mock_theme):
        mock_fig = MagicMock()
        mock_px.scatter_3d.return_value = mock_fig

        build_3d_scatter(
            [],
            x="District",
            y="Crop",
            z="Production",
            labels={"Production": "Production (MT)"},
        )

        mock_px.scatter_3d.assert_called_once()
        layout = mock_fig.update_layout.call_args.kwargs
        self.assertEqual(layout["scene"]["xaxis"]["title"]["text"], "District")
        self.assertEqual(layout["scene"]["yaxis"]["title"]["text"], "Crop")
        self.assertEqual(layout["scene"]["zaxis"]["title"]["text"], "Production (MT)")

    @patch("components.charts.st")
    @patch("components.charts.px")
    def test_render_yield_chart_uses_3d_for_district_and_priority(self, mock_px, mock_st):
        source = MagicMock()
        source.empty = False
        source.columns = ["District", "Priority", "Production_MT"]
        grouped = MagicMock()
        grouped.columns = ["District", "Priority", "Production_MT"]
        source.groupby.return_value.__getitem__.return_value.mean.return_value = grouped
        mock_px.scatter_3d.return_value = MagicMock()

        render_yield_chart(source)

        mock_px.scatter_3d.assert_called_once()
        mock_px.bar.assert_not_called()
        mock_st.plotly_chart.assert_called_once()

    @patch("components.charts.get_current_theme", return_value="light")
    @patch("components.charts.st")
    @patch("components.charts.px")
    def test_render_yield_chart_keeps_2d_without_third_dimension(self, mock_px, mock_st, _mock_theme):
        source = MagicMock()
        source.empty = False
        source.columns = ["District", "Production_MT"]
        grouped = MagicMock()
        grouped.columns = ["District", "Production_MT"]
        source.groupby.return_value.__getitem__.return_value.mean.return_value = grouped
        mock_px.bar.return_value = MagicMock()

        render_yield_chart(source)

        mock_px.bar.assert_called_once()
        mock_px.scatter_3d.assert_not_called()
        mock_st.plotly_chart.assert_called_once()

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
