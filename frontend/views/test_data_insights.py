"""Tests for the real-data analytics processing layer."""
import unittest

import pandas as pd

from views.data_insights import (
    build_insights,
    crop_key,
    filter_dashboard_metrics,
    normalize_agri_metrics,
    seasons_match,
)


class TestDataInsights(unittest.TestCase):
    def setUp(self):
        self.frame = normalize_agri_metrics([
            {
                "id": "r1", "zone_id": "z1", "season": "2026 Season A", "crop": "Maize",
                "yield_actual": "1200", "production_mt": "3.2", "area_cultivated": "2",
                "rainfall_mm": "not recorded", "zones": {"district": "Huye", "sector": "Ruhashya"},
            },
            {
                "id": "r2", "zone_id": "z2", "season": "2026 Season A", "crop": "Beans",
                "yield_actual": 800, "production_mt": 1.1, "zones": {"district": "Huye"},
            },
            {
                "id": "r3", "zone_id": "z3", "season": "2026 Season B", "crop": "Maize",
                "yield_actual": 1500, "production_mt": 4.0, "zones": {"district": "Kigali"},
            },
        ])

    def test_normalization_flattens_and_safely_coerces_values(self):
        self.assertEqual(self.frame.loc[0, "District"], "Huye")
        self.assertEqual(self.frame.loc[0, "Yield (kg/ha)"], 1200)
        self.assertTrue(pd.isna(self.frame.loc[0, "Rainfall (mm)"]))
        self.assertEqual(crop_key("maizes"), crop_key("Maize"))
        self.assertEqual(crop_key("Irish potatoes"), crop_key("Irish potato"))

    def test_filters_share_season_crop_and_district_selections(self):
        filtered = filter_dashboard_metrics(
            self.frame,
            season="2026 Season A",
            all_seasons_label="All seasons",
            crops=["Maize"],
            district="Huye",
            all_districts_label="All Districts",
        )
        self.assertEqual(filtered["Record ID"].tolist(), ["r1"])
        self.assertTrue(seasons_match("Season A 2026", "2026 Season A"))

    def test_insights_are_calculated_from_the_selected_rows(self):
        insights = build_insights(self.frame)
        messages = [message for _, _, message in insights]
        self.assertTrue(any("Maize averages 1,350 kg/ha" in message for message in messages))
        self.assertTrue(any("Huye" in message or "Kigali" in message for message in messages))
        self.assertTrue(any("unadjusted for crop mix" in message for message in messages))

    def test_empty_and_missing_data_produce_no_broken_insights(self):
        empty = normalize_agri_metrics([])
        self.assertTrue(empty.empty)
        self.assertEqual(build_insights(empty), [])
        missing = normalize_agri_metrics([{"id": "r", "zones": None}])
        self.assertEqual(build_insights(missing), [])


if __name__ == "__main__":
    unittest.main()
