"""
This module is an attempt at the Starter System from Robert Carver's book Leveraged Trader.
The system is explained in chapters 5-6 of the book.
"""

import numpy as np
import backtrader as bt
from backtrader.strategy import Strategy
from pandas import DataFrame
from abc import ABC, abstractmethod
from typing import Union
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


class Starter(Strategy):
    """Starter System from Robert Carver's book Leveraged Trader"""

    params = (
        ("short_moving_average_length", 16),
        ("long_moving_average_length", 64),
        ("expected_sharpe_ratio", 0.24),
        ("speed_limit", 0.08),
    )

    def __init__(self):
        """
        Initialize the model
        """
        super().__init__()
        # Initialize moving averages using the built-in indicators
        self.short_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.short_moving_average_length
        )
        self.long_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.long_moving_average_length
        )
        # Initialize the actual sharpe ratio using backtrader indicators for sharpe ratio
        self._actual_sharpe_ratio = bt.indicators.SharpeRatio(self.data.close)

    def next(self):
        """
        Define the moving average crossover strategy
        """
        # Check if short MA is above the long MA and we're not already in the market
        if self.short_ma > self.long_ma and not self.position:
            self.buy()
        # Check if short MA is below the long MA and we're in the market
        elif self.short_ma < self.long_ma and self.position:
            self.sell()

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
        """
        This model uses a moving average crossover strategy to generate signals.

        NOTE:
        -------------------------------------------------------------------------
        A vectorized dataset in algorithmic trading refers to historical data structured
        in such a way that operations on the data can be performed using vectorized computations,
        typically leveraging libraries like NumPy or pandas. This approach is efficient for certain
        types of analysis but may not accurately capture the realities of trading, such as transaction costs,
        market impact, or the sequential nature of receiving market data.
        -------------------------------------------------------------------------

        -------------------------------------------------------------------------
        While we use pandas here for backtesting, this simulation assumes all data is available for vectorized
        operations at once, rather than accounting for the time-ordered sequence of market events. Does the
        sequential nature of trading data matter for this strategy? If so, how would you modify the code to
        account for this?
        """
        params = (
            ("short_moving_average_length", 16),
            ("long_moving_average_length", 64),
            ("expected_sharpe_ratio", 0.24),
            ("speed_limit", 0.08),
        )

        # Default values for the moving averages come from ch. 5, pp. 109 of Leveraged Trader
        short_ma = kwargs.get("short_moving_average_length", 16)
        long_ma = kwargs.get("long_moving_average_length", 64)
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
