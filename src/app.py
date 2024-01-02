"""
scout app
"""
import logging
import time
import typer
from datetime import datetime
from src.utils.cli.callbacks import (
    validate_end_date,
    validate_duration,
    validate_bar_size,
)
from src.utils.cli.cli import init_logging, set_error_and_exit
from src.api.ib import IBApiClient
from src.models.order import ContractFactory
from src.utils.references import IB_API_LOGGER_NAME, bar_sizes, duration_units

__copyright__ = "Copyright \xa9 2023 Arthur Vargas | ahvargas92@gmail.com"


logger = logging.getLogger(IB_API_LOGGER_NAME)
app = typer.Typer()


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def historical_quote(
    ctx: typer.Context,
    ticker: str = typer.Argument(..., help="Ticker symbol for the stock"),
    bar_size: str = typer.Option(
        None,
        "-b",
        "--bar-size",
        callback=validate_bar_size,
        help=f"Data granularity. Valid bars: {', '.join(bar_sizes)}",
    ),
    duration: str = typer.Option(
        None,
        "-d",
        "--duration",
        callback=validate_duration,
        help=f"The amount of time to go back from the end date and time. \
            Provide an integer and a valid duration string unit. Valid units: {', '.join(f'{short} ({long})' for short, long in duration_units)}",
    ),
    end_date: str = typer.Option(
        None,
        "-ed",
        "--end-date",
        callback=validate_end_date,
        help="The end time. Valid formats: YYYY-MM-DD, YYYY/MM/DD",
    ),
    end_time: str = typer.Option(
        None,
        "-et",
        "--end-time",
        callback=validate_end_date,
        help="The end time in 24-hour clock format. Valid formats: HH:MM:SS",
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
    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    try:
        # Initialize logging
        app_log = init_logging(log_level)
        app_log.log_application_start()
        # Create the IB API client
        client = IBApiClient(host="localhost", port=4002, client_id=1)
        client.start_services()
        # Create the contract
        contract_factory = ContractFactory()
        contract = contract_factory.get_contract(ticker)

        client.stop_services()
        client.executor.shutdown(wait=True)

    except Exception as e:
        logger.error("An error occurred: %s", e)
        set_error_and_exit(e)
    finally:
        app_log.log_application_finish()
