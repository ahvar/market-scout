import unittest
import pytest
import pandas as pd
import numpy as np
from rich import print
from src.accounts.accounts_forecast import (
    get_normalised_forecast,
    get_average_notional_position,
    get_notional_position_for_forecast,
)
from src.models.vol import robust_daily_vol_given_price
from src.models.ewmac import calc_ewmac_forecast
from src.utils.references import (
    ARBITRARY_FORECAST_ANNUAL_RISK_TARGET_PERCENTAGE,
    ARBITRARY_FORECAST_CAPITAL,
    ROOT_BDAYS_INYEAR,
    ARBITRARY_VALUE_OF_PRICE_POINT,
)


class TestPositionSizing(unittest.TestCase):
    def setUp(self):
        # Set up common test data
        np.random.seed(42)  # For reproducibility
        n_days = 100  # Number of days for synthetic price data
        price_changes = np.random.normal(loc=0, scale=1, size=n_days)
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        self.price = pd.Series(
            np.cumsum(price_changes) + 100, name="price", index=dates
        )
        print(self.price)

        self.fast = 16
        self.slow = 64
        self.forecast = calc_ewmac_forecast(self.price, self.fast, self.slow)
        print(self.forecast)
        self.target_abs_forecast = 10.0
        self.daily_returns_volatility = robust_daily_vol_given_price(self.price)
        self.capital = ARBITRARY_FORECAST_CAPITAL
        self.risk_target = ARBITRARY_FORECAST_ANNUAL_RISK_TARGET_PERCENTAGE
        self.value_per_point = ARBITRARY_VALUE_OF_PRICE_POINT

    def test_get_normalised_forecast(self):
        normalized_forecast = get_normalised_forecast(
            self.forecast, self.target_abs_forecast
        )
        expected_normalized_forecast = self.forecast / self.target_abs_forecast
        pd.testing.assert_series_equal(
            normalized_forecast, expected_normalized_forecast
        )

    def test_get_average_notional_position(self):
        average_notional_position = get_average_notional_position(
            self.daily_returns_volatility,
            self.capital,
            self.risk_target,
            self.value_per_point,
        )
        daily_risk_target = self.risk_target / ROOT_BDAYS_INYEAR
        daily_cash_vol_target = self.capital * daily_risk_target
        instrument_currency_vol = self.daily_returns_volatility * self.value_per_point
        expected_average_notional_position = (
            daily_cash_vol_target / instrument_currency_vol
        )
        print("expected average notional position")
        print(expected_average_notional_position)
        pd.testing.assert_series_equal(
            average_notional_position, expected_average_notional_position
        )

    def test_get_notional_position_for_forecast(self):
        normalized_forecast = get_normalised_forecast(
            self.forecast, self.target_abs_forecast
        )
        average_notional_position = get_average_notional_position(
            self.daily_returns_volatility,
            self.capital,
            self.risk_target,
            self.value_per_point,
        )
        notional_position = get_notional_position_for_forecast(
            normalised_forecast=normalized_forecast,
            average_notional_position=average_notional_position,
        )
        print("notional position")
        print(notional_position)
        aligned_average = average_notional_position.reindex(
            normalized_forecast.index, method="ffill"
        )
        print("aligned average")
        print(aligned_average)
        expected_notional_position = aligned_average * normalized_forecast
        pd.testing.assert_series_equal(notional_position, expected_notional_position)
