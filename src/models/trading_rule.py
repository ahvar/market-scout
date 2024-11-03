from pathlib import Path
from abc import ABC, abstractmethod
import pandas as pd
from src.models.vol import robust_vol_calc


class TradingRule(ABC):
    """
    Abstract class for trading rules.
    """

    def __init__(
        self,
        price: pd.Series,
    ) -> None:
        """
        Initialize the trading rule.
        :params price: price series
        """
        super().__init__()
        self._price = price
        self._forecast = None
        self._normalized_forecast = None

    @abstractmethod
    def calculate_forecast(self) -> pd.Series:
        """
        Calculate the forecast.
        """

    @abstractmethod
    def normalize_forecast(self) -> pd.Series:
        """
        Normalize the forecast.
        """

    @property
    def price(self) -> pd.Series:
        """
        Return the price series.
        """
        return self._price

    @property
    def forecast(self) -> pd.Series:
        """
        Return the forecast series.
        """
        return self._forecast

    @property
    def normalized_forecast(self) -> pd.Series:
        """
        Return the normalized forecast series.
        """
        return self._normalized_forecast


class EWMACTradingRule(TradingRule):
    """
    Exponentially weighted moving average crossover.
    """

    def __init__(self, price: pd.Series, fast: int, slow: int, frequency: str = "1B"):
        super().__init__(price)
        self._original_price = price
        self._fast = fast
        self._slow = slow
        self._frequency = frequency
        self._forecast = None

    def calculate_forecast(self) -> None:
        """
        Calculate the EWMAC forecast.
        :returns: EWMAC forecast
        """
        resampled_price = self._original_price.resample(self._frequency).last()
        if self.slow is None:
            self.slow = 4 * self.fast

        fast_ewma = resampled_price.ewm(span=self.fast).mean()
        slow_ewma = resampled_price.ewm(span=self.slow).mean()
        raw_ewmac = fast_ewma - slow_ewma
        vol = robust_vol_calc(resampled_price.diff())
        self._forecast = raw_ewmac / vol
        self._price = resampled_price

    def normalize_forecast(self, target_abs_forecast: float = 10.0) -> None:
        """
        Normalize the forecast.
        :params target_abs_forecast: target absolute forecast
        :returns: normalized forecast
        """
        self._normalized_forecast = self._forecast / target_abs_forecast

    @property
    def fast(self):
        """
        Return the fast EWMAC parameter.
        """
        return self._fast

    @property
    def slow(self):
        """
        Return the slow EWMAC parameter.
        """
        return self._slow

    @property
    def frequency(self):
        """
        Return the frequency.
        """
        return self._frequency

    @property
    def original_price(self):
        """
        Return the original price series.
        """
        return self._original_price
