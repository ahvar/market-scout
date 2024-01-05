"""
Description
------------------------------------------------------------------------------
Contains useful functions for commands:
 - init logging
 - organize qc metric data
 - make output dirs
------------------------------------------------------------------------------
"""
import sys
import time
import pytz
import logging
import typer
from datetime import datetime, timedelta
from pathlib import Path

from src.utils.logging_utils import LoggingUtils, LogFileCreationError
from src.utils.references import (
    hour,
    week,
    day,
    minute,
    IB_API_LOGGER_NAME,
    __Application__,
    __version__,
    DateTimeType,
)

__copyright__ = "Copyright \xa9 2023 Arthur Vargas | ahvargas92@gmail.com"

logger = logging.getLogger(IB_API_LOGGER_NAME)


def version_callback(value: bool) -> None:
    """
    Echo software version

    :params value: echo version if true
    """
    if value:
        typer.echo(__version__)
        raise typer.Exit()


def set_error_and_exit(error):
    """
    Reports the specified error and terminates the program..
    Parameters
    ----------
        error : str
            The error message to report.
    """
    sys.stderr.write(f"Error: {error} \n")
    sys.stderr.write("scout exiting.\n")
    sys.exit(1)


def parse_datetime(
    datetime_string: str, formats: list, datetime_type: DateTimeType
) -> datetime:
    """
    Parses a date or time from a string using specified formats.
    Defaults to the date or time one period (day or hour) prior
    to the current date/time if the input is None or empty. If
    the format doesn't match, it raises a ValueError.

    :params datetime_string: string representation of the date or time
    :params           formats: valid formats
    :params     datetime_type: specifies whether to parse a date or time
    """
    logger.debug("Parsing datetime string: %s", datetime_string)
    if not datetime_string:
        logger.debug("No datetime string provided, defaulting to previous period")
        if datetime_type == DateTimeType.DATE:
            default_value = datetime.now() - timedelta(days=1)
            return default_value.date()
        if datetime_type == DateTimeType.TIME:
            default_value = datetime.now() - timedelta(hours=1)
            return default_value.time()

    for fmt in formats:
        try:
            logger.debug("Trying format: %s", fmt)
            parsed_datetime = datetime.strptime(datetime_string, fmt)
            return (
                parsed_datetime.date()
                if datetime_type == DateTimeType.DATE
                else parsed_datetime.time()
            )
        except ValueError:
            continue  # try next format

    raise ValueError(f"Format not recognized: {datetime_string}")


def init_logging(log_level: str) -> LoggingUtils:
    """
    Initiate app log

    :params     log_level: the log level
    :returns LoggingUtils: logging utility for consistent log formats
    """
    try:
        timestamp = time.strftime("%Y%m%d%H%M%S")
        log_dir = Path("/opt/eon/log") / __Application__ / timestamp
        log_file = log_dir / "app.log"
        log_dir.mkdir(exist_ok=True, parents=True)

        logging_utils = LoggingUtils(
            application_name=IB_API_LOGGER_NAME,
            log_file=log_file,
            file_level=log_level,
            console_level=logging.ERROR,
        )
        return logging_utils
    except LogFileCreationError as lfe:
        set_error_and_exit(f"Unable to create log file: {lfe.filespec}")


def convert_to_utc(date_obj: datetime.date, time_obj: datetime.time) -> datetime:
    """
    Combines a date and time object, localizes to the US/Central timezone,
    and then converts to UTC.

    :param date_obj: The date object.
    :param time_obj: The time object.
    :return: A datetime object in UTC.
    """
    logger.debug("Converting to UTC...")
    local_datetime = datetime.combine(date_obj, time_obj)
    central = pytz.timezone("US/Central")
    localized_datetime = central.localize(local_datetime)
    utc_datetime = localized_datetime.astimezone(pytz.utc)
    logger.debug("UTC datetime: %s", utc_datetime.strftime("%Y-%m-%d %H:%M:%S"))
    return utc_datetime
