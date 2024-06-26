from ib_async import *

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

# convert to pandas dataframe (pandas needs to be installed):
df = util.df(bars)
print(df)
