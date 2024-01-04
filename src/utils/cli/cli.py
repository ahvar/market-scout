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
from src.utils.references import hour, week, day, minute, __Application__, __version__

__copyright__ = "Copyright \xa9 2023 Arthur Vargas | ahvargas92@gmail.com"

SCOUT_LOGGER_NAME = f"{__Application__}_{__version__}_driver"

logger = logging.getLogger(SCOUT_LOGGER_NAME)


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


def parse_date(date_string: str, formats: list) -> datetime:
    """
    Parses a date from a string using the 'YYYY-MM-DD' or
    'YYYY/MM/DD' format.
    If the format doesn't match, it raises a ValueError.

    :params date_string: string representation of the date
    :params     formats: valid formats
    """
    for fmt in formats:
        try:
            logger.debug("Trying to parse date string: %s", date_string)
            central = pytz.timezone("US/Central")
            local_datetime = central.localize(datetime.now())
            utc_datetime = local_datetime.astimezone(pytz.utc)
            return utc_datetime.strptime(date_string, fmt)
        except ValueError as ve:
            logger.debug("Could not parse date: %s", ve)
    raise ValueError(f"Could not parse date: {date_string}")


def parse_time(time_string: str, formats: list) -> datetime:
    """
    Parses a time from a string using the 'HH:MM:SS' format.
    If the format doesn't match, it raises a ValueError.

    :params time_string: string representation of the time
    :params     formats: valid formats
    """
    for fmt in formats:
        try:
            logger.debug("Trying to parse time string: %s", time_string)
            central = pytz.timezone("US/Central")
            local_datetime = central.localize(datetime.now())
            utc_datetime = local_datetime.astimezone(pytz.utc)
            return utc_datetime.strptime(time_string, fmt)
        except ValueError as ve:
            logger.debug("Could not parse time: %s", ve)
    raise ValueError(f"Could not parse time: {time_string}")


def get_default_end_date(time_unit: str, time_length: int) -> (datetime, datetime):
    """
    Calculates a default end date based on the current day
    and the specified time unit.

    :params time_unit: time unit
    :params time_length: time length
    :return datetime: the time unit as datetime
    """
    # Assuming the smallest time unit is a minute
    now = datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    if time_unit == hour:
        # If the time unit is an hour, set the default end time to the next hour
        end_of_day = now.replace(minute=59, second=59, microsecond=999999)
    elif time_unit == day:
        # If the time unit is a day, the default times are already set to the start and end of the day
        pass
    elif time_unit == week:
        # If the time unit is a week, set the default end time to the end of the week
        end_of_day += timedelta(days=(6 - end_of_day.weekday()))

    return start_of_day, end_of_day


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
            application_name=SCOUT_LOGGER_NAME,
            log_file=log_file,
            file_level=log_level,
            console_level=logging.ERROR,
        )
        return logging_utils
    except LogFileCreationError as lfe:
        set_error_and_exit(f"Unable to create log file: {lfe.filespec}")
