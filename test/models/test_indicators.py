"""
Unit tests for indicators
"""

import unittest
from unittest.mock import patch
import pandas as pd
from src.models.indicator import MovingAverage


class TestMovingAverage(unittest.TestCase):
    """
    Unit tests for the MovingAverage class.
    """

    @patch("src.models.indicator.indicator_logger")
    def setUp(self, mock_logger):
        """
        Set up the test case by initializing the MovingAverage object.
        """
        self.prices = pd.Series([10, 20, 30, 40, 50])
        self.moving_average_length = 3
        self.moving_average = MovingAverage(self.prices, self.moving_average_length)
        mock_logger.debug.assert_called_with(
            "%s initialized with moving average length: %s. Prices: %s",
            self.moving_average.__class__.__name__,
            self.moving_average_length,
            self.prices.to_string(index=False),
        )

    def test_initialization(self):
        """Test initialization of MovingAverage object."""
        self.assertEqual(
            self.moving_average.moving_average_length, self.moving_average_length
        )
        self.assertIsNone(self.moving_average.moving_average)

    @patch("src.models.indicator.indicator_logger")
    def test_calculate(self, mock_logger):
        """Test the calculation of the moving average."""
        self.moving_average.calculate()
        expected_values = [None, None, 20.0, 30.0, 40.0]
        pd.testing.assert_series_equal(
            self.moving_average.moving_average,
            pd.Series(expected_values),
            check_names=False,
        )
        mock_logger.error.assert_not_called()

    @patch("src.models.indicator.indicator_logger")
    def test_calculate_error(self, mock_logger):
        """Test the calculation of the moving average with an error due to insufficient prices length."""
        # Set prices to a length less than the moving average length to trigger the error condition
        self.moving_average._prices = pd.Series([10, 20])
        with self.assertRaises(ValueError):
            self.moving_average.calculate()
        mock_logger.error.assert_called()

    def test_moving_average_length_property(self):
        """Test the moving_average_length property."""
        self.assertEqual(
            self.moving_average.moving_average_length, self.moving_average_length
        )

    def test_moving_average_property(self):
        """Test the moving_average property after calculation."""
        self.moving_average.calculate()
        self.assertIsInstance(self.moving_average.moving_average, pd.Series)
        self.assertEqual(len(self.moving_average.moving_average), len(self.prices))
