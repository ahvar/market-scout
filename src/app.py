"""
scout app
"""

__version__ = "1.0.0"
__copyright__ = "Copyright \xa9 2023 Arthur Vargas | ahvargas92@gmail.com"
__Application__ = "MarketScout"

logger_name = f"{__Application__}_{__version__}_driver"

import typer
from src.utils.cli.callbacks import (
    validate_end_time,
    validate_start_time,
    validate_time_unit,
)
from src.utils.cli.cli import init_logging

app = typer.Typer()


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def quote(
    ctx: typer.Context,
    quote: str,
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
):
    """ """
