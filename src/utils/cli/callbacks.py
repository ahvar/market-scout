"""
Description
------------------------------------------------------------------------------
Command-line callback functions:
 - validate_start_time
 - validate_end_time
 - validate_time_unit
------------------------------------------------------------------------------
"""
import typer
import logging
from datetime import datetime, timedelta
from src.utils.cli.cli import parse_date, get_default_start_end_time
from src.utils.references import date_formats, hour, day, minute, week

__version__ = "1.0.0"
__copyright__ = "Copyright \xa9 2023 Arthur Vargas | ahvargas92@gmail.com"
__Application__ = "market_scout"

SCOUT_LOGGER_NAME = f"{__Application__}_{__version__}_scout"

logger = logging.getLogger(SCOUT_LOGGER_NAME)


def validate_start_time(ctx: typer.Context, start: str) -> str:
    """
    The start time
    :params  ctx: the typer context object
    :params start: the beginning of the target time period
    :return start: the beginning of the target time period
    """
    logger.debug("Validating start time...")
    if start is None:
        logger.debug(
            "No start date provided, default to the first time unit current day"
        )
        start_time, _ = get_default_start_end_time(ctx.params["time_unit"])
        return start_time
    else:
        try:
            logger.debug(f"Parsing start date string: {start}")
            return parse_date(start, date_formats)
        except ValueError as e:
            raise typer.BadParameter(str(e))


def validate_end_time(ctx: typer.Context, end: str) -> str:
    """
    The end time
    :params  ctx: the typer context object
    :params end: the end of the target time period
    :return end: the end of the target time period
    """
    logger.debug("Validate end time...")
    if end is None:
        logger.debug(
            "No end date provided, default to the last time unit of the current day"
        )
        _, end_time = get_default_start_end_time(ctx.params["time_unit"])
        return end_time
    else:
        try:
            logger.debug(f"Parsing end date string: {end}")
            return parse_date(end, date_formats)
        except ValueError as e:
            raise typer.BadParameter(str(e))


def validate_time_unit(ctx: typer.Context, unit: str) -> str:
    """
    A valid time measurement
    :params  ctx: the typer context object
    :params unit: the unit of time
    :return unit: a valid unit of time
    """
    logger.debug("Validating time units...")
    valid_time_units = [hour, minute, day, week]
    if unit not in valid_time_units:
        raise typer.BadParameter(
            f"Invalid time unit. Please choose from {valid_time_units}."
        )
    return unit
