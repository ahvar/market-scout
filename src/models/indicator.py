"""
Momentum or trend-following indicators are generally used to identify the direction
of the market and the strength of the trend.
"""

from abc import ABC

import pandas as pd
import numpy as np


class Indicator(ABC):
    """
    Base class for indicators.
    """

    def __init__(self, data):
        """
        Initialize the Indicator object.

        Parameters:
        - data: The data used for calculating the indicator.
        """
        self._data = data

    def calculate(self):
        """
        Calculate the indicator.

        This method should be implemented in derived classes.

        Returns:
        - The calculated indicator values.
        """
        raise NotImplementedError(
            "calculate method must be implemented in derived classes"
        )

    @property
    def data(self):
        return self._data


class Momentum(Indicator):
    """
    Base class for momentum indicators.
    """

    def __init__(self, data):
        """
        Initialize the MomentumIndicator object.

        Parameters:
        - data: The data used for calculating the indicator.
        """
        super().__init__(data)

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


class MovingAverage(Momentum):
    """
    Moving Average Crossover indicator class.
    """

    def __init__(self, data):
        """
        Initialize the MovingAverageCrossover object.

        Parameters:
        - data: The data used for calculating the indicator.
        - short_period: The period for the short-term moving average.
        - long_period: The period for the long-term moving average.
        """
        super().__init__(data)

    def calculate(self):
        """
        Calculate the moving average crossover indicator.

        Returns:
        - The trading signals based on the moving average crossover.
        """
        # Calculate the moving average
        moving_average = self._data.rolling(window=n).mean()

        # Return the trading signals based on the moving average crossover
        signals = np.where(self._data > moving_average, 1, -1)
        return signals
