import backtrader as bt
from datetime import datetime
from pprint import PrettyPrinter
from src.models.starter import Starter
from ib_async.ib import IB
from ib_async import util
from ib_async.contract import Forex


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
df = util.df(bars)
cerebro = bt.Cerebro()
pp = PrettyPrinter(indent=4)
# pp.pprint(f"Backtrader: {pp.pprint(bt.__dict__)}")
# print("\n\n")
# pp.pprint(f"Cerebro: {pp.pprint(dir(cerebro))}")
# print("\n\n")
# pp.pprint(f"Feeds: {pp.pprint(dir(bt.feeds.PandasData))}")
cerebro.addstrategy(Starter)
data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)
strategies = cerebro.run()
starter_strategy = strategies[0]
pp.pprint(dir(starter_strategy))
ib.disconnect()
