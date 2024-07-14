import asyncio
from ib_async.ib import IB
from ib_async.contract import Contract


async def main():
    # Create an instance of the IB class
    ib = IB()

    # Connect to the Interactive Brokers API asynchronously
    await ib.connectAsync("127.0.0.1", 7497, clientId=1)

    # Create a contract object for a specific stock
    contract = Contract(symbol="AAPL", secType="STK", exchange="SMART", currency="USD")

    # Request tickers asynchronously
    tickers = await ib.reqTickersAsync(contract)

    # Print the tickers
    for ticker in tickers:
        print(ticker)

    # Disconnect from the API
    ib.disconnect()


# Run the asynchronous main function
asyncio.run(main())
