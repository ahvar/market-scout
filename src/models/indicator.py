"""
Momentum or trend-following indicators are generally used to identify the direction
of the market and the strength of the trend.
"""

from abc import ABC, abstractmethod

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

    @abstractmethod
    def calculate(self):
        """
        Calculate the indicator.

        This method should be implemented in derived classes.

        Returns:
        - The calculated indicator values.
        """

    @property
    def data(self):
        """
        Returns the data associated with the indicator.

        Returns:
            The data associated with the indicator.
        """
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

    @abstractmethod
    def calculate(self):
        """
        Calculate the momentum indicator.

        This method should be implemented in derived classes.

        Returns:
        - The calculated indicator values.
        """


class MovingAverage(Momentum):
    """
    Moving Average Crossover is a type of momentum indicator.
    """

    def __init__(self, prices: pd.Series, moving_average_length: int):
        """
        Initialize the MovingAverageCrossover object.

        Parameters:
        - prices: The data used for calculating the indicator.
        - moving_average_length: The length of the moving average.
        """
        super().__init__(prices)
        self._moving_average_length = moving_average_length
        self._moving_average = None

    def calculate(self):
        """
        Calculate the moving average

        Returns:
        - The trading signals based on the moving average crossover.
        """
        self._moving_average = self._data.rolling(
            window=self._moving_average_length
        ).mean()

    @property
    def moving_average_length(self):
        """
        Returns the length of the moving average.

        Returns:
        - The length of the moving average.
        """
        return self._moving_average_length

    @property
    def moving_average(self):
        """
        Returns the moving average.

        Returns:
        - The moving average.
        """
        return self._moving_average
