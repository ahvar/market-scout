import matplotlib.pyplot as plt


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
