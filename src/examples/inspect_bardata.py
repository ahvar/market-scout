import ib_async
from ib_async.ib import IB
from ib_async.contract import Forex
from pprint import PrettyPrinter, pformat
from datetime import datetime
import inspect
import rich

# util.startLoop()  # uncomment this line when in a notebook
pp = PrettyPrinter(indent=4)
"""
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
"""


# bars = [Bar(**bar.__dict__) for bar in bars]
pp.pprint(f"IB ASYNC: {pp.pprint(ib_async.__dict__)}")
print("\n\n")
pp.pprint(f"IB: {pp.pprint(IB.__dict__)}")
# pp.pprint(
#    f"__dict__ returns the dictionary representing the object's namespace: {pp.pprint(bars[0].__dict__)}"
# )
# pp.pprint(f"help {help(bars[0])}\n")
# pp.pprint(f"{pp.pprint(bars[0].average)}")
# print("\n\n")

# print(bars)

# convert to pandas dataframe (pandas needs to be installed):
# df = util.df(bars)
# print(df)
