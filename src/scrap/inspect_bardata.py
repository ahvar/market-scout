from ib_async import *
from pprint import PrettyPrinter, pformat
from pydantic import BaseModel
from datetime import datetime
import inspect

# util.startLoop()  # uncomment this line when in a notebook

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


class Bar(BaseModel):
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    average: float
    barCount: int


# bars = [Bar(**bar.__dict__) for bar in bars]
pp = PrettyPrinter(indent=4)
# pp.pprint(
#    f"dir() returns list of the attributes and methods: {pp.pprint(dir(bars[0]))}"
# )
print("\n\n")
# pp.pprint(
#    f"__dict__ returns the dictionary representing the object's namespace: {pp.pprint(bars[0].__dict__)}"
# )
# pp.pprint(f"help {help(bars[0])}\n")
pp.pprint(f"{pp.pprint(bars[0].average)}")
print("\n\n")

# print(bars)

# convert to pandas dataframe (pandas needs to be installed):
# df = util.df(bars)
# print(df)
