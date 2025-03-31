import backtrader as bt
from datetime import datetime
from pprint import PrettyPrinter
from src.strategies.starter import Starter
from src.broker.broker import IBAsyncBroker
from ib_async.ib import IB
from ib_async import util
from ib_async.contract import Forex

pp = PrettyPrinter(indent=4)


def get_ib_and_price_data():
    ib = IB()
    ib.connect(host="127.0.0.1", port=4002, clientId=1, timeout=30)

    contract = Forex("EURUSD")
    bars = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr="30 D",
        barSizeSetting="1 hour",
        whatToShow="MIDPOINT",
        useRTH=True,
    )
    return ib, bars


def print_some_stuff():
    # pp.pprint(f"Backtrader: {pp.pprint(bt.__dict__)}")
    # print("\n\n")
    # pp.pprint(f"Cerebro: {pp.pprint(dir(cerebro))}")
    # print("\n\n")
    # pp.pprint(f"Feeds: {pp.pprint(dir(bt.feeds.PandasData))}")
    print("\n\n")
    pp.pprint(f"Indicators: {pp.pprint(dir(bt.indicators))}")
    pp.pprint("\n\n")


if __name__ == "__main__":
    ib, bars = get_ib_and_price_data()
    df = util.df(bars)
    df.set_index("date", inplace=True)
    cerebro = bt.Cerebro()
    pp.pprint(f"Data: {pp.pprint(df)}")
    cerebro.addstrategy(Starter)
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name="sharpe_a")
    # run the backtest
    strategies = cerebro.run()
    # get the starter strategy
    if not strategies:
        raise ValueError("No strategies were returned")
    starter_strategy = strategies[0]
    if hasattr(starter_strategy.analyzers, "sharpe_a"):
        sharpe_ratio = starter_strategy.analyzers.sharpe_a.get_analysis()
        pp.pprint(f"Sharpe Ratio: {sharpe_ratio}")
    else:
        raise ValueError("Sharpe Ratio Analyzer not found")
    # get the sharpe ratio
    # sharpe_ratio = starter_strategy.analyzers.sharpe_a.get_analysis()
    # pp.pprint(f"Sharpe Ratio: {sharpe_ratio}")
    # compute the speed
    # speed = sharpe_ratio / 3
    # if speed <= starter_strategy.expected_sharpe_ratio / 3:
    #    print("This product meets the speed limit requirements")
    ib.disconnect()
