"""
Momentum or trend-following indicators are generally used to identify the direction
of the market and the strength of the trend.
"""

from abc import ABC

import pandas as pd
import numpy as np


class MomentumIndicator(ABC):
    """
    Base class for momentum indicators.
    """

    def __init__(self, data):
        """
        Initialize the MomentumIndicator object.

        Parameters:
        - data: The data used for calculating the indicator.
        """
        self.data = data

    def calculate(self):
        """
        Calculate the momentum indicator.

        This method should be implemented in derived classes.

        Returns:
        - The calculated indicator values.
        """
        raise NotImplementedError(
            "calculate method must be implemented in derived classes"
        )


class MovingAverageCrossover(MomentumIndicator):
    """
    Moving Average Crossover indicator class.
    """

    def __init__(self, data, short_period=16, long_period=64):
        """
        Initialize the MovingAverageCrossover object.

        Parameters:
        - data: The data used for calculating the indicator.
        - short_period: The period for the short-term moving average.
        - long_period: The period for the long-term moving average.
        """
        super().__init__(data)
        self.short_period = short_period
        self.long_period = long_period

    def calculate(self):
        """
        Calculate the moving average crossover indicator.

        Returns:
        - The trading signals based on the moving average crossover.
        """
        # Calculate the short-term moving average
        self.data["short_ma"] = (
            self.data["price"].rolling(window=self.short_period).mean()
        )

        # Calculate the long-term moving average
        self.data["long_ma"] = (
            self.data["price"].rolling(window=self.long_period).mean()
        )

        # Generate the trading signals based on the moving average crossover
        self.data["signal"] = 0
        self.data["signal"][self.short_period :] = np.where(
            self.data["short_ma"][self.short_period :]
            > self.data["long_ma"][self.short_period :],
            1,
            -1,
        )

        return self.data
