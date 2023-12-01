"""
scout app
"""
import logging
import typer
from datetime import datetime
from src.utils.cli.callbacks import (
    validate_end_time,
    validate_start_time,
    validate_time_unit,
)
from src.utils.cli.cli import init_logging
from src.api.ib import IBApiClient
from src.utils.references import __Application__, __version__

__copyright__ = "Copyright \xa9 2023 Arthur Vargas | ahvargas92@gmail.com"


logger_name = f"{__Application__}_{__version__}_driver"
logger = logging.getLogger(logger_name)
app = typer.Typer()


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def quote(
    ctx: typer.Context,
    ticker: str = typer.Argument(..., help="Ticker symbol for the stock"),
    time_unit: str = typer.Option(
        "minute",
        "-u",
        "--time-unit",
        callback=validate_time_unit,
        help="Time unit for the quote -  hour, minute, day, week",
    ),
    start_time: str = typer.Option(
        None, "-s", "--start-time", callback=validate_start_time, help="The start time"
    ),
    end_time: str = typer.Option(
        None, "-e", "--end-time", callback=validate_end_time, help="The end time"
    ),
    debug: bool = typer.Option(
        False,
        "-b",
        "--debug",
        help="Set log level to debug",
    ),
):
    """
    Retrieve historical data for a given ticker
    """
    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    typer.echo(
        f"Fetching data for {ticker} from {start_time} to {end_time} in {time_unit} intervals."
    )
    # Connect to IB API and fetch data based on the above parameters
    # Handle possible errors with try-except blocks.
    try:
        # Mock the process of fetching data
        data = "Sample data for demonstration purposes."
        typer.echo(data)
    except Exception as e:
        typer.echo(f"An error occurred: {e}")
