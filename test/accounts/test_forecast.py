import unittest
import pytest
import pandas as pd
import numpy as np
from src.strategies.vol import robust_daily_vol_given_price
from src.strategies.trading_rule import EWMACTradingRule
from src.accounts.profit_and_loss import (
    get_average_notional_position,
    get_notional_position_for_forecast,
)
from src.utils.tabulation import ConsoleTabulator
from src.utils.references import (
    ARBITRARY_FORECAST_ANNUAL_RISK_TARGET_PERCENTAGE,
    ARBITRARY_FORECAST_CAPITAL,
    ROOT_BDAYS_INYEAR,
    ARBITRARY_VALUE_OF_PRICE_POINT,
)


class TestPositionSizing(unittest.TestCase):
    """
    Test the position sizing functions
    """

    def setUp(self):
        # Set up common test data
        np.random.seed(42)  # For reproducibility
        n_days = 100  # Number of days for synthetic price data
        price_changes = np.random.normal(loc=0, scale=1, size=n_days)
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        price = pd.Series(np.cumsum(price_changes) + 100, name="price", index=dates)
        self.target_abs_forecast = 10.0
        self.ewmac_trading_rule = EWMACTradingRule(price, fast=16, slow=64)
        self.ewmac_trading_rule.calculate_forecast()
        self.ewmac_trading_rule.normalize_forecast(self.target_abs_forecast)
        self.daily_returns_volatility = robust_daily_vol_given_price(price)
        self.capital = ARBITRARY_FORECAST_CAPITAL
        self.risk_target = ARBITRARY_FORECAST_ANNUAL_RISK_TARGET_PERCENTAGE
        self.value_per_point = ARBITRARY_VALUE_OF_PRICE_POINT
        self.console_tabulator = ConsoleTabulator()

    def test_get_normalised_forecast(self):
        """
        Test the get_normalised_forecast function
        """
        expected_normalized_forecast = (
            self.ewmac_trading_rule.forecast / self.target_abs_forecast
        )
        pd.testing.assert_series_equal(
            self.ewmac_trading_rule.normalized_forecast, expected_normalized_forecast
        )
        data = []
        for date, price, forecast, norm_forecast in zip(
            self.ewmac_trading_rule.price.index,
            self.ewmac_trading_rule.price,
            self.ewmac_trading_rule.forecast,
            self.ewmac_trading_rule.normalized_forecast,
        ):
            data.append(
                (str(date), f"{price:.2f}", f"{forecast:.2f}", f"{norm_forecast:.2f}")
            )
        self.console_tabulator.display_table(
            title="Instrument Price and Normalized EWMAC Forecast",
            columns=["Date", "Price", "Forecast", "Normalized Forecast"],
            data=data,
        )

    def test_get_average_notional_position(self):
        """
        Test the get_average_notional_position function
        """
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

        pd.testing.assert_series_equal(
            average_notional_position, expected_average_notional_position
        )
        self.console_tabulator.display_forecast(
            price=self.ewmac_trading_rule.price,
            forecast=self.ewmac_trading_rule.forecast,
            normalized_forecast=self.ewmac_trading_rule.normalized_forecast,
        )

    def test_get_notional_position_for_forecast(self):
        """
        Test the get_notional_position_for_forecast function
        """
        average_notional_position = get_average_notional_position(
            self.daily_returns_volatility,
            self.capital,
            self.risk_target,
            self.value_per_point,
        )
        notional_position = get_notional_position_for_forecast(
            normalised_forecast=self.ewmac_trading_rule.normalized_forecast,
            average_notional_position=average_notional_position,
        )

        aligned_average = average_notional_position.reindex(
            self.ewmac_trading_rule.normalized_forecast.index, method="ffill"
        )

        expected_notional_position = (
            aligned_average * self.ewmac_trading_rule.normalized_forecast
        )
        pd.testing.assert_series_equal(notional_position, expected_notional_position)
        self.console_tabulator.display_notional_position(
            price=self.ewmac_trading_rule.price,
            normalized_forecast=self.ewmac_trading_rule.normalized_forecast,
            average_notional_position=aligned_average,
            notional_position=notional_position,
        )
