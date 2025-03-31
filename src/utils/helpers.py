"""
Description
------------------------------------------------------------------------------
Contains useful functions for commands:
 - init logging
 - organize qc metric data
 - make output dirs
------------------------------------------------------------------------------
"""

# standard library
import sys
import time
import logging
import pytz
from datetime import datetime, timedelta
from pathlib import Path

# third-party
import typer
import yaml
import pandas as pd
from src.utils.logging_utils import LoggingUtils, LogFileCreationError
from src.utils.references import (
    hour,
    week,
    day,
    minute,
    MKT_SCOUT_CLI,
    MKT_SCOUT_FRONTEND,
    __Application__,
    __version__,
    DateTimeType,
)

__copyright__ = "Copyright \xa9 2025 Arthur Vargas | arthurvargasdev@gmail.com"

logger = logging.getLogger(MKT_SCOUT_CLI)


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
    if datetime_type not in (DateTimeType.DATE, DateTimeType.TIME):
        raise ValueError(
            f"Invalid datetime type: {datetime_type}. Must be {DateTimeType.DATE} or {DateTimeType.TIME}."
        )
    if not formats:
        raise ValueError("No formats provided.")
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
        except (ValueError, TypeError, IndexError, AttributeError):
            logger.debug("Format not recognized: %s", fmt)
            continue
        except Exception as e:
            logger.error("Error parsing datetime: %s", e)
            continue

    raise ValueError(f"Format not recognized: {datetime_string}")

def _make_logfile_parent_dir_and_get_path() -> Path:
    try:
        logfile_parent = Path("/opt/eon/log") / __Application__ / __version__.replace('.','_') / time.strftime("%Y%m%d%H%M%S")
        logfile_parent.mkdir(exist_ok=True, parents=True)
        return logfile_parent
    except LogFileCreationError as lfe:
        set_error_and_exit(f"Unable to create logfile parent dir: {lfe.filespec}")

def init_cli_logger(log_level: str) -> LoggingUtils:
    """
    Initiate app log

    :params     log_level: the log level
    :returns LoggingUtils: logging utility for consistent log formats
    """
    try:
        logfile_parent = _make_logfile_parent_dir_and_get_path()
        log_file = logfile_parent / f"{MKT_SCOUT_CLI}.log"

        logging_utils = LoggingUtils(
            application_name=MKT_SCOUT_CLI,
            log_file=log_file,
            file_level=log_level,
            console_level=logging.ERROR,
        )
        return logging_utils
    except LogFileCreationError as lfe:
        set_error_and_exit(f"Unable to create log file: {lfe.filespec}")

def init_frontend_logger(log_level: str) -> LoggingUtils:
    try:
        logfile_parent = _make_logfile_parent_dir_and_get_path()
        log_file = logfile_parent / f"{MKT_SCOUT_FRONTEND}.log"

        logging_utils = LoggingUtils(
            application_name=MKT_SCOUT_FRONTEND,
            log_file=log_file,
            file_level=log_level,
            console_level=logging.ERROR,
        )
        return logging_utils
    except LogFileCreationError as lfe:
        set_error_and_exit(f"Unable to create log file: {lfe.filespec}")

def load_config(config_path: str):
    """Load and return configuration from a YAML file."""
    with open(config_path) as file:
        return yaml.safe_load(file)

def make_dirs_and_write(
    outdir: Path,
    ticker: str,
    prices: pd.Series,
    forecast: pd.Series,
    notional_position: pd.Series,
    duration: str,
    bar_size: str,
) -> None:
    price_and_analysis_dir = outdir / "prices_and_analysis"
    price_history_dir = price_and_analysis_dir / ticker / "price_history"
    forecast_dir = price_and_analysis_dir / ticker / "forecast" / "trend_following"
    price_history_dir.mkdir(parents=True, exist_ok=True)
    forecast_dir.mkdir(parents=True, exist_ok=True)

    prices.to_csv(
        price_history_dir
        / f"{ticker}_{duration}_{bar_size}_{datetime.today().strftime('%Y_%m_%d')}_prices.csv"
    )
    forecast.to_csv(
        forecast_dir
        / f"{ticker}_{duration}_{bar_size}_{datetime.today().strftime('%Y_%m_%d')}_forecast.csv"
    )
    notional_position.to_csv(
        forecast_dir
        / f"{ticker}_{duration}_{bar_size}_{datetime.today().strftime('%Y_%m_%d')}_notional_position.csv"
    )


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
