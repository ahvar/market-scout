import pandas as pd
from src.utils.references import (
    ARBITRARY_FORECAST_ANNUAL_RISK_TARGET_PERCENTAGE,
    ARBITRARY_FORECAST_CAPITAL,
    ROOT_BDAYS_INYEAR,
    ARBITRARY_VALUE_OF_PRICE_POINT,
)


def get_normalised_forecast(
    forecast: pd.Series, target_abs_forecast: float = 10.0
) -> pd.Series:
    normalised_forecast = forecast / target_abs_forecast
    return normalised_forecast


def get_average_notional_position(
    daily_returns_volatility: pd.Series,
    capital: float = ARBITRARY_FORECAST_CAPITAL,
    risk_target: float = ARBITRARY_FORECAST_ANNUAL_RISK_TARGET_PERCENTAGE,
    value_per_point=ARBITRARY_VALUE_OF_PRICE_POINT,
) -> pd.Series:
    daily_risk_target = risk_target / ROOT_BDAYS_INYEAR
    daily_cash_vol_target = capital * daily_risk_target

    instrument_currency_vol = daily_returns_volatility * value_per_point
    average_notional_position = daily_cash_vol_target / instrument_currency_vol

    return average_notional_position


def get_notional_position_for_forecast(
    normalised_forecast: pd.Series, average_notional_position: pd.Series
) -> pd.Series:
    aligned_average = average_notional_position.reindex(
        normalised_forecast.index, method="ffill"
    )

    # NOTE: only the 10 expected missing values in beginning of series observed
    # na_series = average_notional_position.isna()
    # na_count = sum(na_series)
    # print(na_count)
    # notional_position_for_forecast = aligned_average * normalised_forecast
    # notional_position_for_forecast.to_csv(Path(__file__).resolve().parent / "notional_position_for_forecast.csv")
    return aligned_average * normalised_forecast
