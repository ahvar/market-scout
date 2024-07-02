"""
Momentum or trend-following indicators are generally used to identify the direction
of the market and the strength of the trend.
"""

from abc import ABC, abstractmethod
import logging
import pandas as pd
import numpy as np

from src.utils.references import IB_API_LOGGER_NAME

indicator_logger = logging.getLogger(IB_API_LOGGER_NAME)


class Indicator(ABC):
    """
    Base class for indicators.
    """

    def __init__(self, prices):
        """
        Initialize the Indicator object.

        Parameters:
        - prices: The price history used for calculating the indicator.
        """
        self._prices = prices

    @abstractmethod
    def calculate(self):
        """
        Calculate the indicator.

        This method should be implemented in derived classes.

        Returns:
        - The calculated indicator values.
        """

    @property
    def prices(self):
        """
        Returns the data associated with the indicator.

        Returns:
            The data associated with the indicator.
        """
        return self._prices


class Momentum(Indicator):
    """
    Base class for momentum indicators.
    """

    def __init__(self, prices):
        """
        Initialize the MomentumIndicator object.

        Parameters:
        - data: The data used for calculating the indicator.
        """
        super().__init__(prices)

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
        Initialize the MovingAverage object.

        Parameters:
        - prices: The data used for calculating the indicator.
        - moving_average_length: The length of the moving average.
        """
        super().__init__(prices)
        self._moving_average_length = moving_average_length
        self._moving_average = None
        indicator_logger.debug(
            "%s initialized with moving average length: %s. Prices: %s",
            self.__class__.__name__,
            self._moving_average_length,
            prices.to_string(index=False),
        )

    def calculate(self):
        """
        Calculate the moving average

        Returns:
        - The trading signals based on the moving average crossover.
        """
        if len(self._prices) < self._moving_average_length:
            indicator_logger.error(
                "Insufficient prices length for moving average calculation"
            )
            raise ValueError(
                "Insufficient prices length for moving average calculation"
            )
        try:
            self._moving_average = self._prices.rolling(
                window=self._moving_average_length
            ).mean()
        except AttributeError as e:
            indicator_logger.error("Attribute error in calculate method: %s", e)
            raise
        except Exception as e:
            indicator_logger.error(
                "Unexpected error occurred while calculating moving average: %s", e
            )
            raise

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
