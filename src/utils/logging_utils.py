"""
LoggingUtils.py

This file contains a class with utilities to facilitate consistent logging
patterns.
"""

import logging
import os
import getpass
import platform
import sys
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler


class LogFileCreationError(Exception):
    """
    Exception raised for errors when creating the log file.

    Attributes:
        filespec -- the log filespec that was requested
    """

    def __init__(self, filespec):
        self.filespec = filespec


class LoggingUtils:
    """
    A utility class to provide consistent logging for applications.

    """

    def __init__(
        self,
        application_name,
        log_file: str = None,
        file_level: int = logging.NOTSET,
        console_level: int = logging.NOTSET,
    ):
        """
        Initialize an instance of the LoggingUtils. This creates an instance of the logging class and sets
        formatting for the log.
        """
        # The name of the application
        self._app_Name = application_name
        # The filename used to write log output
        self._file_name = log_file
        # The logging level for messages written to the logging file. All messages at this
        # level and higher will be logged.
        self._file_Level = file_level
        # The level for messages to write to the console.
        self._console_Level = console_level
        # Instance of logging.Logger used for logging.
        self._logger = None
        # Handler for writing to the log file.
        self._file_handler = None
        # Handler for writing to the console.
        self._console_handler = None
        # User who initiated this program.
        self._username = getpass.getuser()
        # The system on which the program was run.
        self._hostname = platform.node()
        # The start time for this program.
        self._start_date_time = datetime.now()
        # The time this program is finished. This is set by calling log_application_finish().
        self._finish_date_time = None
        # Date and time formats
        self._full_date_time_format = "%d%b%Y %H:%M:%S"
        self._time_with_milleseconds = "%H:%M:%S.%f"
        formatter = logging.Formatter(
            "[%(asctime)s.%(msecs)03d] - %(module)s - %(levelname)s - %(message)s",
            self._full_date_time_format,
        )
        self._logger = logging.getLogger()
        self._logger.setLevel(logging.DEBUG)
        if file_level:
            if not self._file_name:
                self._file_name = os.path.join(self._app_Name + ".log")

            try:
                self._file_handler = RotatingFileHandler(
                    self._file_name, maxBytes=10240, backupCount=10
                )
            except IOError:
                raise LogFileCreationError(self._file_name)

            self._file_handler.setLevel(self._file_Level)
            self._logger.addHandler(self._file_handler)

            self._file_handler.setFormatter(formatter)
        if console_level:
            self._console_handler = logging.StreamHandler()
            self._console_handler.setLevel(self._console_Level)
            self._console_handler.setFormatter(formatter)
            self._logger.addHandler(self._console_handler)

    def __del__(self):
        """
        Destructor for LoggingUtils.
        """

        if self._file_handler:
            self._file_handler.close()
            self._logger.removeHandler(self._file_handler)
        if self._console_handler:
            self._console_handler.close()
            self._logger.removeHandler(self._console_handler)

        # Shutdown
        logging.shutdown()

    def log_application_start(self):
        """
        Log the start of an application. This inserts a standard set of information into the log file.
        """
        command = " ".join(sys.argv)
        start = self._format_date_time(self._start_date_time)
        self._logger.info(
            "**************************************************************"
        )
        self._logger.info("  User         = %s", self._username)
        self._logger.info("  Hostname     = %s", self._hostname)
        self._logger.info("  Command      = %s", command)
        self._logger.info("  Application  = %s", self._app_Name)
        self._logger.info("  Start        = %s", start)
        self._logger.info(
            "**************************************************************"
        )

    def log_application_finish(self):
        """
        Log the finish of an application. This inserts the following information:
        """
        self._finish_date_time = datetime.now()
        finish = self._format_date_time(self._finish_date_time)
        elapsed_time = self._finish_date_time - self._start_date_time
        self._logger.info(
            "**************************************************************"
        )
        self._logger.info("%s finished.", self._app_Name)
        self._logger.info("  Finish time  = %s", finish)
        self._logger.info("  Elapsed time = %s", str(elapsed_time))
        self._logger.info(
            "**************************************************************"
        )

    def update_file_handler_log_level(self, level):
        """
        Update the log level for the file handler.
        """
        for handler in self._logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.setLevel(level)

    def _format_date_time(self, raw_date_time):
        """
        Formats a time value in a human-readable format.
        """
        return raw_date_time.strftime(self._time_with_milleseconds)
