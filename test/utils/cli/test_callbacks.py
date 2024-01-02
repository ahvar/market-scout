"""
Unit tests for the callbacks module.
"""
import unittest
import pytest
from datetime import datetime
from typer import BadParameter
from src.utils.cli.callbacks import (
    validate_duration,
    validate_end_date,
    validate_bar_size,
)


class TestCallbacks(unittest.TestCase):
    """
    Test the callbacks module.
    """

    def test_validate_duration_with_valid_input(self):
        """
        Test the validate_duration callback with valid input.
        """
        assert validate_duration(None, "1 D") == "1 D"

    def test_validate_duration_with_invalid_unit(self):
        """
        Test the validate_duration callback with invalid input.
        """
        with pytest.raises(BadParameter):
            validate_duration(None, "1 X")

    def test_validate_duration_with_zero_duration(self):
        """
        Test the validate_duration callback with invalid input.
        """
        with pytest.raises(BadParameter):
            validate_duration(None, "0 D")

    def test_validate_duration_with_no_input(self):
        """
        Test the validate_duration callback with no input.
        """
        assert validate_duration(None, None) == "1 D"

    def test_validate_bar_size_with_valid_input(self):
        """
        Test the validate_bar_size callback with valid input.
        """
        assert validate_bar_size(None, "1 min") == "1 min"

    def test_validate_bar_size_with_invalid_input(self):
        """
        Test the validate_bar_size callback with invalid input.
        """
        with pytest.raises(BadParameter):
            validate_bar_size(None, "invalid_size")

    def test_validate_bar_size_with_no_input(self):
        """
        Test the validate_bar_size callback with no input.
        """
        assert validate_bar_size(None, None) == "1 min"

    def test_validate_end_date_with_valid_input(self):
        """
        Test the validate_end_date callback with valid input.
        """
        assert validate_end_date(None, "2023-01-01") == "2023-01-01"

    def test_validate_end_date_with_invalid_input(self):
        """
        Test the validate_end_date callback with invalid input.
        """
        with pytest.raises(BadParameter):
            validate_end_date(None, "invalid_date")

    def test_validate_end_date_with_no_input(self):
        """
        Test the validate_end_date callback with no input.
        """
        # Replace with expected default end date
        assert validate_end_date(None, None) == datetime.now().strftime("%Y-%m-%d")
