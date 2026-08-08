from ib_async.ib import IB
from ib_async.contract import Contract

# Create an instance of the IB class
ib = IB()

# Connect to the Interactive Brokers API synchronously
ib.connect("127.0.0.1", 4002, clientId=1)

# Create a contract object for a specific stock
contract = Contract(symbol="AAPL", secType="STK", exchange="SMART", currency="USD")

# Request current positions synchronously
positions = ib.reqPositions()

# Print the positions
for position in positions:
    print(position)

# Disconnect from the API
ib.disconnect()
