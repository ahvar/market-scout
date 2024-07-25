"""
Use the custom IBAsyncBroker to run a simple backtrader strategy
"""

import backtrader as bt
import asyncio
from datetime import datetime
from src.api.broker import IBAsyncBroker
from src.models.starter import Starter


if __name__ == "__main__":
    cerebro = bt.Cerebro()

    # Use the custom IBAsyncBroker
    broker = IBAsyncBroker()
    cerebro.setbroker(broker)

    # Add strategy and pass the broker instance
    cerebro.addstrategy(Starter, broker)

    # Add data feed
    data = bt.feeds.YahooFinanceData(
        dataname="AAPL",
        fromdate=datetime.datetime(2020, 1, 1),
        todate=datetime.datetime(2021, 1, 1),
    )
    cerebro.adddata(data)

    # Run the strategy
    cerebro.run()

    # Print positions
    strategy = cerebro.runstrats[0][0]
    asyncio.run(strategy.print_positions())
