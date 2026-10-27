"""
Unit tests for system Central Africa Time (CAT) UTC+2 timezone utilities.
"""
import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from utils.timezone import (
    CAT_TIMEZONE,
    CAT_TZ,
    get_current_time,
    setup_system_timezone,
    to_cat,
)


class TestTimezone(unittest.TestCase):

    def test_cat_timezone_constant(self):
        self.assertEqual(CAT_TIMEZONE, "Africa/Kigali")
        self.assertEqual(str(CAT_TZ), "Africa/Kigali")

    def test_setup_system_timezone(self):
        setup_system_timezone()
        import os
        self.assertEqual(os.environ.get("TZ"), "Africa/Kigali")

    def test_get_current_time_returns_cat(self):
        now = get_current_time()
        self.assertIsNotNone(now.tzinfo)
        # UTC offset for CAT (Africa/Kigali) is +02:00
        offset = now.utcoffset()
        self.assertIsNotNone(offset)
        self.assertEqual(offset.total_seconds(), 7200)

    def test_to_cat_conversion(self):
        # 10:00 UTC should be 12:00 CAT
        utc_dt = datetime(2026, 10, 27, 10, 0, 0, tzinfo=timezone.utc)
        cat_dt = to_cat(utc_dt)
        self.assertEqual(cat_dt.hour, 12)
        self.assertEqual(cat_dt.minute, 0)
        self.assertEqual(cat_dt.utcoffset().total_seconds(), 7200)

    def test_to_cat_naive_datetime(self):
        # Naive datetime assumes UTC and converts to CAT
        naive_dt = datetime(2026, 10, 27, 8, 30, 0)
        cat_dt = to_cat(naive_dt)
        self.assertEqual(cat_dt.hour, 10)
        self.assertEqual(cat_dt.minute, 30)


if __name__ == "__main__":
    unittest.main()

