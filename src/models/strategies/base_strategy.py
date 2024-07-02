""" Base class for trading strategies. """

from abc import ABC, abstractmethod
from models.indicator import MovingAverage


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.
    """

    def __init__(self, data):
        """
        Initialize the trading strategy with the necessary data.

        :param data: Historical market data
        """
        self.data = data

    @abstractmethod
    def generate_signals(self):
        """
        Generate trading signals based on the strategy.
        """

    @abstractmethod
    def calculate_metrics(self):
        """
        Calculate and return strategy-specific metrics.
        """

    @abstractmethod
    def execute_trades(self):
        """
        Execute trades based on the generated signals.
        """
