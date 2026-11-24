
import unittest
from datetime import date, datetime

from src.roster import shift_interval


class TestRosterBasics(unittest.TestCase):

    def test_month_format(self):
        year, month = map(int, "2026-09".split("-"))
        self.assertEqual((year, month), (2026, 9))

    def test_week_starts_monday(self):
        d = date(2026, 9, 7)
        self.assertEqual(d.weekday(), 0)

    def test_morning_shift_interval(self):
        shift = {
            "start_time": "06:00",
            "end_time": "14:00"
        }

        start, end = shift_interval(date(2026, 9, 1), shift)

        self.assertEqual(start.hour, 6)
        self.assertEqual(end.hour, 14)
        self.assertEqual((end - start).total_seconds() / 3600, 8)

    def test_night_shift_crosses_midnight(self):
        shift = {
            "start_time": "22:00",
            "end_time": "06:00"
        }

        start, end = shift_interval(date(2026, 9, 1), shift)

        self.assertEqual(start, datetime(2026, 9, 1, 22, 0))
        self.assertEqual(end, datetime(2026, 9, 2, 6, 0))

    def test_night_shift_duration(self):
        shift = {
            "start_time": "22:00",
            "end_time": "06:00"
        }

        start, end = shift_interval(date(2026, 9, 1), shift)

        self.assertEqual((end - start).total_seconds() / 3600, 8)


if __name__ == "__main__":
    unittest.main()
