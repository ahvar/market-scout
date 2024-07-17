"""
This module is an attempt at the Starter System from Robert Carver's book Leveraged Trader.
The system is explained in chapters 5-6 of the book.
"""

import numpy as np
from pandas import DataFrame
from abc import ABC, abstractmethod
from typing import Union
from src.models.indicator import MovingAverage
from ib_async.contract import (
    Forex,
    Stock,
    Option,
    Future,
    ContFuture,
    FuturesOption,
    Index,
    CFD,
    Commodity,
    Bond,
    Warrant,
    Contract,
    ContractDetails,
)


class BaseModel(ABC):
    """
    Abstract base class for trading models.
    """

    def __init__(self, price_data: Union[np.ndarray, list, dict, DataFrame]):
        """
        Initialize the model with price data.

        :param data: price data
        """
        self._price_data = price_data

    @abstractmethod
    def generate_signals(self, *args, **kwargs):
        """
        Generate trading signals based on the strategy.
        """

    @property
    def price_data(self):
        """
        Returns the data associated with the model.

        Returns:
            The data associated with the model.
        """
        return self._price_data


class Starter(BaseModel):
    """Starter System from Robert Carver's book Leveraged Trader"""

    def __init__(self, price_data, financial_instrument: Contract):
        """
        Initialize the model with price data and a financial product.
        :param                 data: price data
        :param financial_instrument: financial instrument to trade
        """
        super().__init__(price_data)
        self._expected_sharpe_ratio = 0.24  # default from ch. 5 of Leveraged Trader
        self._speed_limit = 0.08  # default from ch. 5 of Leveraged Trader
        self._actual_sharpe_ratio = None
        self._actual_speed = None
        self.signals = None

    def _compute_speed_limit(self):
        """
        Computes the speed limit for the strategy based on the actual Sharpe ratio.

        Raises:
            ValueError: If the actual Sharpe ratio is not available.

        Notes:
            According to LT (ch5), the speed limit should be limited to one-third of the expected Sharpe ratio.
            Risk-adjusted costs should be 0.08 or less, ideally around 0.05.
        """
        if self._actual_sharpe_ratio is None:
            raise ValueError("Actual Sharpe ratio is not available.")
        self._actual_speed = self._actual_sharpe_ratio / 3

    def generate_signals(self, *args, **kwargs):
        """This model uses a moving average crossover strategy to generate signals."""

        short_ma = kwargs.get("short_moving_average_length", 10)
        long_ma = kwargs.get("long_moving_average_length", 40)
        # Calculate the short (fast) and long (slow) moving averages
        self._price_data["short_ma"] = (
            self._price_data["close"].rolling(window=short_ma).mean()
        )
        self._price_data["long_ma"] = (
            self._price_data["close"].rolling(window=long_ma).mean()
        )
        # Generate signals: 1 for buy, -1 for sell, 0 for hold
        self._price_data["signal"] = 0
        self._price_data["signal"][short_ma:] = np.where(
            self._price_data["short_ma"][short_ma:]
            > self._price_data["long_ma"][short_ma:],
            1,
            -1,
        )
        # Optionally, clean up by dropping the MA columns if they are not needed further
        # self._price_data.drop(['short_ma', 'long_ma'], axis=1, inplace=True)

        # Assuming you want to store the signals for further use
        self.signals = self._price_data["signal"]

    @property
    def expected_sharpe_ratio(self):
        """
        Returns the expected Sharpe ratio of the strategy.

        The Sharpe ratio is a measure of risk-adjusted return. It calculates the excess return of an investment
        per unit of volatility or risk. A higher Sharpe ratio indicates a better risk-adjusted performance.

        Returns:
            float: The expected Sharpe ratio of the strategy (.24 for StarterStrategy by default)
        """
        return self._expected_sharpe_ratio

    @property
    def actual_sharpe_ratio(self):
        """
        Returns the actual Sharpe ratio of the strategy (see above for definition).

        Returns:
            float: The actual Sharpe ratio of the strategy.
        """
        return self._actual_sharpe_ratio

    @property
    def actual_speed(self):
        """
        Returns the speed limit of the system.

        Returns:
            int: The speed limit of the system.
        """
        return self._actual_speed
