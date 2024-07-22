from ib_async.ib import IB
from ib_async.contract import Contract
import asyncio


async def main():
    # Other setup code...
    ib = IB()
    contract = Contract(symbol="AAPL", secType="STK", exchange="SMART", currency="USD")

    # Create a task for requesting tickers but don't wait for it yet
    ticker_task = asyncio.create_task(ib.reqTickersAsync(contract))

    # Execute other code that doesn't depend on the tickers
    print("Doing other work that doesn't require tickers...")

    # Now, wait for the ticker task to complete when you need the result
    tickers = await ticker_task

    # Continue with operations that depend on tickers
    for ticker in tickers:
        print(ticker)


# Run the asynchronous main function
asyncio.run(main())
