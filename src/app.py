"""
scout app
"""
import logging
import time
import typer
from datetime import datetime
from src.utils.cli.callbacks import (
    validate_end_time,
    validate_start_time,
    validate_time_unit,
)
from src.utils.cli.cli import init_logging, set_error_and_exit
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
        help="Time unit for the quote. Valid units: hour, minute, day, week",
    ),
    start_time: str = typer.Option(
        None,
        "-s",
        "--start-time",
        callback=validate_start_time,
        help="The start time. Valid formats: YYYY-MM-DD, YYYY/MM/DD",
    ),
    end_time: str = typer.Option(
        None,
        "-e",
        "--end-time",
        callback=validate_end_time,
        help="The end time. Valid formats: YYYY-MM-DD, YYYY/MM/DD",
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
    try:
        app_log = init_logging(log_level)
        app_log.log_application_start()
        client = IBApiClient(host="localhost", port=4002, client_id=1)
        client.start_services()
        time.sleep(120)
        client.stop_services()
        time.sleep(30)
        client.start_services()
        time.sleep(120)
        client.stop_services()
        client.executor.shutdown(wait=True)

    except Exception as e:
        logger.error("An error occurred: %s", e)
        set_error_and_exit(e)
    finally:
        app_log.log_application_finish()
