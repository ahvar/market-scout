"""
scout app
"""

import logging
import time
import typer
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from src.utils.cli.callbacks import (
    validate_end_date,
    validate_duration,
    validate_bar_size,
    validate_end_time,
    validate_out_dir,
    validate_report_type,
)
from src.utils.cli.cli import init_logging, set_error_and_exit, convert_to_utc
from src.api.ib import IBApiClient
from src.models.order import ContractFactory
from src.utils.references import (
    IB_API_LOGGER_NAME,
    bar_sizes,
    duration_units,
    report_types,
)

__copyright__ = "Copyright \xa9 2023 Arthur Vargas | ahvargas92@gmail.com"


logger = logging.getLogger(IB_API_LOGGER_NAME)
app = typer.Typer()
load_dotenv()


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def market_summary(
    ctx: typer.Context,
    ticker: str = typer.Argument(..., help="Ticker symbol for the stock"),
    duration: str = typer.Option(
        None,
        "-dr",
        "--duration",
        callback=validate_duration,
        help=f"The amount of time to go back from the end date and time. \
            Provide an integer and a valid duration unit. Valid units: {', '.join(f'{short} ({long})' for short, long in duration_units)}",
    ),
    end_date: str = typer.Option(
        None,
        "-ed",
        "--end-date",
        callback=validate_end_date,
        help="The request's end date. Default is the current date. Valid formats: YYYY-MM-DD, YYYY/MM/DD",
    ),
    out_dir: str = typer.Option(
        None,
        "-o",
        "--outdir",
        callback=validate_out_dir,
        help="The name of the output file. Default is <ticker>.csv",
    ),
    report_type: str = typer.Option(
        None,
        "-rt",
        "--report-type",
        callback=validate_report_type,
        help=f"The type of report to generate. Valid types: {', '.join(f'{report}' for report in report_types)}",
    ),
    debug: bool = typer.Option(
        False,
        "-b",
        "--debug",
        help="Set log level to debug",
    ),
):
    """
    This command tells Market Scout to get the market summary for a ticker within a given timeframe. The values passed to
    command options are used in requests to OpenAI API for GPT chat service.
    """
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair.",
            },
            {
                "role": "user",
                "content": "Compose a poem that explains the concept of recursion in programming.",
            },
        ],
    )

    print(completion.choices[0].message)


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def historical_quote(
    ctx: typer.Context,
    ticker: str = typer.Argument(..., help="Ticker symbol for the stock"),
    bar_size: str = typer.Option(
        None,
        "-br",
        "--bar-size",
        callback=validate_bar_size,
        help=f"Data granularity. Valid bars: {', '.join(bar_sizes)}",
    ),
    duration: str = typer.Option(
        None,
        "-dr",
        "--duration",
        callback=validate_duration,
        help=f"The amount of time to go back from the end date and time. \
            Provide an integer and a valid duration unit. Valid units: {', '.join(f'{short} ({long})' for short, long in duration_units)}",
    ),
    end_date: str = typer.Option(
        None,
        "-ed",
        "--end-date",
        callback=validate_end_date,
        help="The request's end date. Default is the current date. Valid formats: YYYY-MM-DD, YYYY/MM/DD",
    ),
    end_time: str = typer.Option(
        None,
        "-et",
        "--end-time",
        callback=validate_end_time,
        help="The request's end time in 24-hour clock. Default is the current time. Valid formats: HH:MM:SS",
    ),
    out_dir: str = typer.Option(
        None,
        "-o",
        "--outdir",
        callback=validate_out_dir,
        help="The name of the output file. Default is <ticker>.csv",
    ),
    debug: bool = typer.Option(
        False,
        "-b",
        "--debug",
        help="Set log level to debug",
    ),
):
    """
    This command tells Market Scout to get the historical data for a ticker within a given timeframe. The values passed to
    command options are used directly in a call to the Interactive Brokers method IBPI.EClient.reqHistoricalData().
    """
    try:
        if not debug:
            for handler in logger.handlers:
                handler.setLevel(logging.INFO)
        # Create the IB API client
        client = IBApiClient(host="localhost", port=4002, client_id=1)
        print("starting services...")
        client.start_services()
        time.sleep(5)
        # Create the contract
        print("creating contract...")
        contract_factory = ContractFactory()
        contract = contract_factory.get_contract(ticker)
        print("waiting for 10 seconds before making historical data request...")
        time.sleep(10)
        # Create the request
        client.request_historical_data(
            contract=contract,
            bar_size=bar_size,
            duration=duration,
            end_datetime=convert_to_utc(end_date, end_time).strftime("%Y%m%d-%H:%M:%S"),
            use_rth=1,
        )
        client.market_memory.write_to_csv(out_dir)

        client.stop_services()
        client.executor.shutdown(wait=True)
    except Exception as e:
        logger.error("An error occurred: %s", e)
        client.stop_services()
        client.executor.shutdown(wait=True)
        raise Exception(e) from e
