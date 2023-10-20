"""
Description
------------------------------------------------------------------------------
Contains useful functions for commands:
 - init logging
 - organize qc metric data
 - make output dirs
------------------------------------------------------------------------------
"""

__version__ = "1.0.0"
__copyright__ = "Copyright \xa9 2023 Arthur Vargas | ahvargas92@gmail.com"
__Application__ = "market_scout"

logger_name = f"{__Application__}_{__version__}_driver"

import logging
import os
import sys
import time
import typer
import datetime
from pathlib import Path
from src.utils.logging_utils import LoggingUtils, LogFileCreationError


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


def init_logging(log_level: str) -> LoggingUtils:
    """
    Initiate app log

    :params     log_level: the log level
    :returns LoggingUtils: logging utility for consistent log formats
    """
    try:
        timestamp = time.strftime("%Y%m%d%H%M%S")
        log_dir = Path("/opt/eon/log") / __Application__ / timestamp
        log_file = f"{__Application__}_driver.log"
        log_dir.mkdir(exist_ok=True, parents=True)

        logging_utils = LoggingUtils(
            application_name=logger_name,
            log_file=log_file,
            file_level=log_level,
            console_level=logging.ERROR,
        )
        return LoggingUtils
    except LogFileCreationError as lfe:
        set_error_and_exit(f"Unable to create log file: {lfe.filespec}")
