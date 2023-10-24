"""
Tests for command-line utility functions
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from src.utils.cli.cli import parse_date, get_default_start_end_time
from src.utils.references import date_formats, hour, day, week, minute


class TestTimes(unittest.TestCase):
    """
    Tests for handling different date formats
    """

    def test_parse_date(self):
        """
        Expects 'YYYY-MM-DD' or 'YYYY/MM/DD'
        """
        # Test with different date formats
        date_string = "2023/01/02"
        result = parse_date(date_string, date_formats)
        self.assertEqual(result, datetime(2023, 1, 2))

        # Test with non-matching format
        with self.assertRaises(ValueError):
            wrong_date_string = "01-02-2023"
            parse_date(wrong_date_string, date_formats)

        # Test with invalid date
        with self.assertRaises(ValueError):
            invalid_date_string = "not a date"
            parse_date(invalid_date_string, date_formats)

    @patch("src.utils.cli.cli.datetime")
    def test_get_default_start_end_time(self, mock_datetime):
        """
        Test setting the default start and end times if they're unavailable
        """
        # Mock datetime to control the current time
        mock_now = datetime(2023, 1, 1, 12, 0, 0)  # Arbitrary date and time
        mock_datetime.now.return_value = mock_now

        # Define what the start of the day should be
        start_of_day = mock_now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Define what the end of the day should be
        end_of_day = mock_now.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Define what the end of the current hour should be
        end_of_hour = mock_now.replace(minute=59, second=59, microsecond=999999)

        # Define what the end of the week should be
        end_of_week = (mock_now + timedelta(days=(6 - mock_now.weekday()))).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # Test for 'minute' time unit
        time_unit = minute
        start, end = get_default_start_end_time(time_unit)
        self.assertEqual(start, start_of_day)
        self.assertEqual(end, end_of_day)

        # Test for 'hour' time unit
        time_unit = hour
        start, end = get_default_start_end_time(time_unit)
        self.assertEqual(start, start_of_day)
        self.assertEqual(end, end_of_hour)  # End of the current hour

        # Test for 'day' time unit
        time_unit = day
        start, end = get_default_start_end_time(time_unit)
        self.assertEqual(start, start_of_day)
        self.assertEqual(end, end_of_day)

        # Test for 'week' time unit
        time_unit = week
        start, end = get_default_start_end_time(time_unit)
        self.assertEqual(start, start_of_day)
        self.assertEqual(end, end_of_week)
