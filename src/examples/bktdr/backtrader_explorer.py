"""
Use the custom IBAsyncBroker to run a simple backtrader strategy
"""

import backtrader as bt
import asyncio
from datetime import datetime
from src.api.broker import IBAsyncBroker
from src.models.starter import Starter
from ib_async.contract import Forex, Stock


if __name__ == "__main__":
    cerebro = bt.Cerebro()

    # Use BackBroker for backtesting
    ib_async_broker = IBAsyncBroker()
    back_broker = bt.brokers.BackBroker()
    cerebro.setbroker(back_broker)

    # Fetch historical data
    contract = Forex("EURUSD")
    eurusd_data = ib_async_broker.get_historical_data(
        contract=contract,
        endDateTime="",
        durationStr="30 D",
        barSizeSetting="1 hour",
        whatToShow="MIDPOINT",
        useRTH=True,
    )

    # Add the historical data to the cerebro instance
    datafeed = bt.feeds.PandasData(dataname=eurusd_data)
    cerebro.adddata(datafeed)
    # Add strategy and pass the broker instance
    cerebro.addstrategy(Starter, broker=back_broker)

    # Run the strategy
    cerebro.run()

    # Print positions
    strategy = cerebro.runstrats[0][0]
    asyncio.run(strategy.print_positions())

    # terrible AIzaSyBnd6fL2VgJXA03ED0qhymBOFY2NuxEHu0
