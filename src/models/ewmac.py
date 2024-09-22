import pandas as pd
from pathlib import Path
from src.models.vol import robust_vol_calc


def calc_ewmac_forecast(price: pd.Series, fast: int, slow: int) -> pd.Series:
    """
    Calculate the ewmac trading rule forecast, given a price and EWMA speeds
    Lfast, Lslow and vol_lookback

    """
    # price: This is the stitched price series
    # We can't use the price of the contract we're trading, or the volatility
    # will be jumpy
    # And we'll miss out on the rolldown. See
    # https://qoppac.blogspot.com/2015/05/systems-building-futures-rolling.html
    price = price.resample("1B").last()

    if slow is None:
        slow = 4 * fast

    # We don't need to calculate the decay parameter, just use the span
    # directly
    fast_ewma = price.ewm(span=fast).mean()
    fast_ewma.to_csv(Path(__file__).resolve().parent / "fast_ewma.csv")
    slow_ewma = price.ewm(span=slow).mean()
    slow_ewma.to_csv(Path(__file__).resolve().parent / "slow_ewma.csv")
    raw_ewmac = fast_ewma - slow_ewma
    raw_ewmac.to_csv(Path(__file__).resolve().parent / "raw_ewmac.csv")

    vol = robust_vol_calc(price.diff())
    return raw_ewmac / vol
