"""
Tests for command-line utility functions
"""

import unittest
import pytz
from datetime import datetime, timedelta
from unittest.mock import patch
from src.utils.cli.cli import parse_datetime, convert_to_utc
from src.utils.references import date_formats, hour, day, week, minute


class TestTimes(unittest.TestCase):
    """
    Tests for handling different date formats
    """

    def test_parse_datetime(self):
        """
        Expects 'YYYY-MM-DD' or 'YYYY/MM/DD'
        """
        pass

    def test_convert_to_utc(self):
        """
        Expects a datetime object
        """
        # Input date and time
        input_date = datetime.date(2024, 1, 4)  # Example date
        input_time = datetime.time(12, 30)  # Example time

        # Expected output
        expected_utc_datetime = datetime(2024, 1, 4, 18, 30, tzinfo=pytz.utc)

        # Run the function
        result_utc_datetime = convert_to_utc(input_date, input_time)

        # Check if the result matches the expected output
        self.assertEqual(result_utc_datetime, expected_utc_datetime)
