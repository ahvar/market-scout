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
import pytz
from typer import Context, BadParameter
from datetime import datetime, timedelta
from pathlib import Path
from src.utils.cli.cli import (
    parse_datetime,
    convert_to_utc,
)
from src.utils.references import (
    date_formats,
    time_formats,
    bar_sizes,
    IB_API_LOGGER_NAME,
    duration_units,
    DateTimeType,
)

logger = logging.getLogger(IB_API_LOGGER_NAME)


def validate_duration(ctx: Context, duration: str) -> str:
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
            raise BadParameter("0 < duration")
        logger.debug("Parsing duration string: %s", duration)
        duration_unit = duration.split(" ")[1]
        for short, long in duration_units:
            if duration_unit in (short, long):
                return duration
        raise BadParameter(
            f"Invalid duration unit. Please choose from {', '.join(f'{short}, ({long})' for short, long in duration_units)}."
        )
    except (ValueError, IndexError, TypeError) as e:
        logger.error("Could not parse date: %s", e)
        raise BadParameter(str(e))


def validate_end_date(ctx: Context, end: str) -> datetime:
    """
    If no end date was provided the previous day is used.
    :params  ctx: the typer context object
    :params end: the end of the target time period
    :return end: the end of the target time period
    """
    try:
        logger.debug("Validate end date...")
        return parse_datetime(end, date_formats, DateTimeType.DATE)
    except (ValueError, TypeError) as e:
        logger.error("Could not parse date: %s", e)
        raise BadParameter(str(e))


def validate_bar_size(ctx: Context, bar_size: str) -> str:
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
    if bar_size.lower() not in bar_sizes:
        logger.error("Invalid time unit. Please choose from %s", ", ".join(bar_sizes))
        raise BadParameter(
            f"Invalid time unit. Please choose from {', '.join(bar_sizes)}."
        )
    return bar_size


def validate_out_dir(ctx: Context, out_dir: str) -> Path:
    """
    If no output directory is provided, the current working directory is used.
    :params    ctx: the typer context object
    :params out_dir: the output directory
    :return out_dir: the output directory
    """
    if out_dir is None:
        logger.debug(
            "No output directory provided, default to current working directory"
        )
        return Path.cwd()

    logger.debug("Validating output directory...")
    out_path = Path(out_dir)
    if not out_path.is_dir():
        logger.error("Invalid output directory. Please choose a valid directory")
        raise BadParameter("Invalid output directory. Please choose a valid directory")

    return out_path.resolve()


def validate_end_time(ctx: Context, end: str) -> str:
    """
    If no end time is provided the current end time is used.
    :params  ctx: the typer context object
    :params end: the end of the target time period
    :return end: the end of the target time period
    """
    try:
        logger.debug("Validate end time...")
        return parse_datetime(end, time_formats, DateTimeType.TIME)
    except (ValueError, TypeError) as e:
        logger.error("Could not parse date: %s", e)
        raise BadParameter(str(e))
