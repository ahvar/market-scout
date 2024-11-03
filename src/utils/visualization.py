import matplotlib.pyplot as plt

from rich.console import Console
from rich.table import Table
import pandas as pd


class Visualizer:
    def __init__(self):
        self.console = Console()

    def display_table(self, title: str, columns: list, data: list):
        table = Table(title=title)
        for column in columns:
            table.add_column(column, justify="right", style="cyan", no_wrap=True)

        for row in data:
            table.add_row(*row)

        self.console.print(table)

    def display_forecast(
        self, price: pd.Series, forecast: pd.Series, normalized_forecast: pd.Series
    ):
        data = [
            (str(date), f"{price:.2f}", f"{forecast:.2f}", f"{norm_forecast:.2f}")
            for date, price, forecast, norm_forecast in zip(
                price.index, price, forecast, normalized_forecast
            )
        ]
        self.display_table(
            "Instrument Price and Normalized EWMAC Forecast",
            ["Date", "Price", "Forecast", "Normalized Forecast"],
            data,
        )

    def display_notional_position(
        self, dates, normalized_forecast, average_notional_position, notional_position
    ):
        data = [
            (str(date), f"{norm_forecast:.2f}", f"{avg_pos:.2f}", f"{not_pos:.2f}")
            for date, norm_forecast, avg_pos, not_pos in zip(
                dates, normalized_forecast, average_notional_position, notional_position
            )
        ]
        self.display_table(
            "Notional Position for EWMAC Forecast",
            [
                "Date",
                "Normalized Forecast",
                "Average Notional Position",
                "Notional Position",
            ],
            data,
        )


def plot_spread(spread, title="Spread"):
    """Plot the spread with its historical mean."""
    plt.figure(figsize=(10, 7))
    spread.plot()
    plt.axhline(spread.mean(), color="red", linestyle="--")
    plt.xlabel("Time")
    plt.ylabel("Spread")
    plt.title(title)
    plt.show()


def plot_signals(spread, longs, shorts, exits, title="Trading Signals"):
    """Plot the spread and highlight trading signals."""
    plt.figure(figsize=(12, 7))
    spread.plot(label="Spread")
    plt.axhline(spread.mean(), color="grey", linestyle="--", label="Mean")
    spread[longs].plot(
        marker="^", markersize=10, color="g", linestyle="None", label="Long Signal"
    )
    spread[shorts].plot(
        marker="v", markersize=10, color="r", linestyle="None", label="Short Signal"
    )
    spread[exits].plot(
        marker="o", markersize=8, color="b", linestyle="None", label="Exit Signal"
    )
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Spread")
    plt.legend()
    plt.show()
