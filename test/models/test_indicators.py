"""
Unit tests for indicators
"""

import unittest
import pandas as pd
from src.models.indicator import MovingAverage


class TestMovingAverage(unittest.TestCase):
    """Test case for the MovingAverage class."""

    def setUp(self):
        """Set up the test case."""
        self.prices = pd.Series([10, 20, 30, 40, 50])
        self.moving_average_length = 3
        self.moving_average = MovingAverage(self.prices, self.moving_average_length)

    def test_initialization(self):
        """Test the initialization of the MovingAverage object."""
        self.assertEqual(
            self.moving_average.moving_average_length, self.moving_average_length
        )
        self.assertIsNone(self.moving_average.moving_average)

    def test_calculate(self):
        """Test the calculate method of the MovingAverage object."""
        self.moving_average.calculate()
        expected_moving_average = pd.Series(
            [None, None, 20, 30, 40], index=self.prices.index
        )
        pd.testing.assert_series_equal(
            self.moving_average.moving_average,
            expected_moving_average,
            check_names=False,
        )

    def test_moving_average_length_property(self):
        """Test the moving_average_length property of the MovingAverage object."""
        self.assertEqual(
            self.moving_average.moving_average_length, self.moving_average_length
        )

    def test_moving_average_property(self):
        """Test the moving_average property of the MovingAverage object."""
        self.moving_average.calculate()
        self.assertIsInstance(self.moving_average.moving_average, pd.Series)
        self.assertEqual(len(self.moving_average.moving_average), len(self.prices))
