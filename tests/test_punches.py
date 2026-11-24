
import unittest
from datetime import datetime

from src.punches import get_night_minutes, hours_to_minutes


class TestPunchCalculations(unittest.TestCase):

    def test_full_night_shift(self):
        start = datetime(2026, 9, 1, 22, 0)
        end = datetime(2026, 9, 2, 6, 0)

        self.assertEqual(get_night_minutes(start, end), 480)

    def test_evening_shift_night_overlap(self):
        start = datetime(2026, 9, 1, 21, 0)
        end = datetime(2026, 9, 2, 7, 0)

        self.assertEqual(get_night_minutes(start, end), 480)

    def test_day_shift_has_no_night_hours(self):
        start = datetime(2026, 9, 1, 10, 0)
        end = datetime(2026, 9, 1, 18, 0)

        self.assertEqual(get_night_minutes(start, end), 0)

    def test_partial_night_hours(self):
        start = datetime(2026, 9, 1, 5, 0)
        end = datetime(2026, 9, 1, 7, 0)

        self.assertEqual(get_night_minutes(start, end), 60)

    def test_hours_to_minutes(self):
        self.assertEqual(hours_to_minutes(7.5), 450)

    def test_half_hour_conversion(self):
        self.assertEqual(hours_to_minutes(0.5), 30)


if __name__ == "__main__":
    unittest.main()
