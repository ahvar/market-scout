from pathlib import Path
from abc import ABC, abstractmethod
import pandas as pd
from src.models.vol import robust_vol_calc


class TradingRule(ABC):
    @abstractmethod
    def calculate_forecast(self, price: pd.Series) -> pd.Series:
        pass


class EWMACTradingRule(TradingRule):
    def __init__(self, fast: int, slow: int):
        self.fast = fast
        self.slow = slow

    def calculate_forecast(self, price: pd.Series) -> pd.Series:
        price = price.resample("1B").last()
        if self.slow is None:
            self.slow = 4 * self.fast

        fast_ewma = price.ewm(span=self.fast).mean()
        slow_ewma = price.ewm(span=self.slow).mean()
        raw_ewmac = fast_ewma - slow_ewma
        vol = robust_vol_calc(price.diff())
        return raw_ewmac / vol
