"""
Trading Rules
"""

from src.models.indicator import MovingAverage, Indicator
from abc import ABC, ABCMeta, abstractmethod
import pandas as pd
import numpy as np


class TradingRule(ABC):
    """
    Base class for trading rules.
    """

    def __init__(self, data):
        """
        Initialize the TradingRule object.

        Parameters:
        - data: The data used for calculating the trading rule.
        """
        self.data = data


class Open(TradingRule):
    """
    Base class for entry rules.
    """

    def __init__(self, data, indicator: Indicator):
        """
        Initialize the Open object.

        Parameters:
        - data: The data used for calculating the entry rule.
        """
        super().__init__(data)
        self.indicator = indicator

    @abstractmethod
    def generate_signals(self):
        """
        Calculate the moving average crossover indicator.

        Returns:
        - The trading signals based on the moving average crossover.
        """


class Close(TradingRule):
    """
    Base class for exit rules.
    """

    def __init__(self, data):
        """
        Initialize the Close object.

        Parameters:
        - data: The data used for calculating the exit rule.
        """
        super().__init__(data)

    @abstractmethod
    def generate_signals(self):
        """
        Generate exit signals based on the rule.
        """


class MovingAverageCrossover(Open):
    """
    Moving Average Crossover entry rule.
    """

    def __init__(
        self, indicator: MovingAverage, data: pd.DataFrame, short_window, long_window
    ):
        """
        Initialize the MovingAverageCrossover object.

        Parameters:
        - indicator: The moving average indicator used for generating signals.
        - data: The data used for calculating the entry rule.
        - short_window: The short moving average window.
        - long_window: The long moving average window.
        """
        super().__init__(data, indicator)
        self._short_window = short_window
        self._long_window = long_window

    def generate_signals(self):
        """
        Calculate the moving average crossover indicator.

        Returns:
        - The trading signals based on the moving average crossover.
        """
        # Calculate the short-term moving average
        self.data["short_ma"] = (
            self.data["price"].rolling(window=self._short_window).mean()
        )

        # Calculate the long-term moving average
        self.data["long_ma"] = (
            self.data["price"].rolling(window=self._long_window).mean()
        )

        # Generate the trading signals based on the moving average crossover
        self.data["signal"] = 0
        self.data["signal"][self._short_window :] = np.where(
            self.data["short_ma"][self._short_window :]
            > self.data["long_ma"][self._short_window :],
            1,
            -1,
        )

        return self.data

    @property
    def short_window(self):
        """
        Returns the value of the short window.

        Returns:
            int: The value of the short window.
        """
        return self._short_window

    @property
    def long_window(self):
        """
        Returns the long window value.

        Returns:
            int: The long window value.
        """
        return self._long_window


class PositionSize(TradingRule):
    """
    Base class for position sizing rules.
    """

    def __init__(self, data):
        """
        Initialize the PositionSize object.

        Parameters:
        - data: The data used for calculating the position size.
        """
        super().__init__(data)

    @abstractmethod
    def calculate_position_size(self):
        """
        Calculate the position size based on the rule.
        """
