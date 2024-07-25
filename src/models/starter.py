"""
The Starter System from Robert Carver's book Leveraged Trader.
The system is explained in chapters 5-6 of the book.

NOTE | Vectorized Data:
    -------------------------------------------------------------------------
    A vectorized dataset in algorithmic trading refers to historical data
    structured in such a way that operations on the data can be performed
    using vectorized computations, typically leveraging libraries like NumPy
    or pandas. This approach is efficient for certain types of analysis but
    may not accurately capture the realities of trading, such as transaction
    costs, market impact, or the sequential nature of receiving market data.
    This simulation assumes all data is available for vectorized operations
    at once, rather than accounting for the time-ordered sequence of market
    events. Although the sequential nature of trading may not matter for some
    strategies.
    -------------------------------------------------------------------------
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
        self._order = None
        self.returns = []

    def next(self):
        """
        Define the moving average crossover strategy
        """
        # Check if short MA is above the long MA and we're not already in the market
        if self.short_ma > self.long_ma and not self.position:
            self._order = self.buy(size=10)
        # Check if short MA is below the long MA and we're in the market
        elif self.short_ma < self.long_ma and self.position:
            self._order = self.sell(size=10)

    def stop(self):
        """
        Calculate the returns of the strategy
        """
        self.returns = np.diff(self.strategy.equity) / self.strategy.equity[:-1]

    @property
    def expected_sharpe_ratio(self):
        """
        The expected sharpe ratio for the model
        """
        return self.params.expected_sharpe_ratio

    @property
    def order(self):
        """
        The order placed by the model
        """
        return self._order
