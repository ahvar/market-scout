"""
This module is an attempt at the Starter System from Robert Carver's book Leveraged Trader.
The system is explained in chapters 5-6 of the book.
"""

from src.models.strategies.base_strategy import BaseStrategy


class StarterStrategy(BaseStrategy):
    """Starter System from Robert Carver's book Leveraged Trader"""

    def __init__(self, data):
        super().__init__(data)
        self._expected_sharpe_ratio = 0.24  # default from ch. 5 of Leveraged Trader
        self._speed_limit = 0.08  # default from ch. 5 of Leveraged Trader
        self._actual_sharpe_ratio = None
        self._actual_speed = None

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

    def calculate_metrics(self):
        """Additional metrics calculation specific to pairs trading could be added here."""

    def execute_trades(self):
        """Execution logic based on generated signals."""

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
