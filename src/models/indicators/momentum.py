"""
Momentum or trend-following indicators are generally used to identify the direction of the market and the strength of the trend.
Moving average crossover, for example, is commonly used by many people. It is easy to calculate
"""


class MomentumIndicator:
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

    def __init__(self, data, short_period, long_period):
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
        short_ma = self.data.rolling(window=self.short_period).mean()

        # Calculate the long-term moving average
        long_ma = self.data.rolling(window=self.long_period).mean()

        # Generate the trading signals based on the moving average crossover
        signals = []
        for i in range(len(self.data)):
            if short_ma[i] > long_ma[i]:
                signals.append(1)  # Buy signal
            else:
                signals.append(-1)  # Sell signal

        return signals
