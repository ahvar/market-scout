"""
Description
------------------------------------------------------------------------------
Command-line callback functions:
 - validate_start_time
 - validate_end_time
 - validate_time_unit
------------------------------------------------------------------------------
"""
import logging
import typer
from datetime import datetime, timedelta
from src.utils.cli.cli import parse_date, get_default_start_end_time
from src.utils.references import (
    date_formats,
    bar_sizes,
    IB_API_LOGGER_NAME,
    duration_units,
)

logger = logging.getLogger(IB_API_LOGGER_NAME)


def validate_duration(ctx: typer.Context, duration: str) -> str:
    """
    The duration is <int> + <valid_duration_string>
    :params      ctx: the typer context object
    :params duration: the amount of time to go back from the end date and time
    :return duration: the amount of time to go back from the end date and time
    """
    logger.debug("Validating duration...")
    if duration is None:
        logger.debug(
            "No duration provided, default to '1 D' (1 day) from the end date and time"
        )
        return "1 D"
    try:
        if int(duration.split(" ")[0]) <= 0:
            raise typer.BadParameter("Duration must be an integer > 0")
        logger.debug("Parsing duration string: %s", duration)
        duration_unit = duration.split(" ")[1]
        for short, long in duration_units:
            if duration_unit in (short, long):
                return duration
        raise typer.BadParameter(
            f"Invalid duration unit. Please choose from {', '.join(f'{short}, ({long})' for short, long in duration_units)}."
        )
    except (ValueError, IndexError, TypeError) as e:
        logger.error("Could not parse date: %s", e)
        raise typer.BadParameter(str(e))


def validate_end_date(ctx: typer.Context, end: str) -> str:
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
    try:
        logger.debug("Parsing end date string: %s", end)
        return parse_date(end, date_formats)
    except ValueError as e:
        logger.error("Could not parse date: %s", e)
        raise typer.BadParameter(str(e))


def validate_bar_size(ctx: typer.Context, bar_size: str) -> str:
    """
    A valid bar size. If none is provided, default to 1 min.
    :params       ctx: the typer context object
    :params  bar_size: the bar size
    :return  bar_size: the bar size
    """
    if bar_size is None:
        logger.debug("No bar size provided, default to 1 min")
        return "1 min"
    logger.debug("Validating bar size...")
    if bar_size not in bar_sizes:
        logger.error("Invalid time unit. Please choose from %s", ", ".join(bar_sizes))
        raise typer.BadParameter(
            f"Invalid time unit. Please choose from {', '.join(bar_sizes)}."
        )
    return bar_size


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
            "No end time provided, default to the last time unit of the current day"
        )
        _, end_time = get_default_start_end_time(ctx.params["time_unit"])
        return end_time
    try:
        logger.debug("Parsing end date string: %s", end)
        return parse_date(end, date_formats)
    except ValueError as e:
        logger.error("Could not parse date: %s", e)
        raise typer.BadParameter(str(e))
