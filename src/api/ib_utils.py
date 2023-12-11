"""
Utility classes and functions for the IB API.
"""
import logging
import time
from typing import Any, Callable

from src.utils.references import __Application__, __version__

logger_name = f"{__Application__}_{__version__}_driver"
watchdog_logger = logging.getLogger(logger_name)


class ConnectionWatchdog:
    """
    A watchdog class that monitors the connection to the IB API and
    """

    def __init__(
        self,
        check_interval: int,
        start_services: Callable[[], None],
        stop_services: Callable[[], None],
        is_connected_method: Callable[[], bool],
    ):
        """
        Constructs the watchdog class.
        :params check_interval: The interval in seconds to check the connection.
        :params connect_method: The method to call to reconnect to the IB API.
        """
        watchdog_logger.info("Initializing %s instance", self.__class__.__name__)
        super().__init__()
        self._check_interval = check_interval  # seconds
        self._start_services = start_services
        self._stop_services = stop_services
        self._is_connected_method = (
            is_connected_method  # method to call to check if the connection is alive
        )
        self._running = None
        watchdog_logger.info("%s initialized", self.__class__.__name__)

    def monitor_connection(self):
        """
        Runs the watchdog thread.
        To make ConnectionWatchdog more responsive, there are multiple
        shorter sleeps in a loop, each time checking the _running flag.
        """
        while self._running:
            if not self._is_connected_method():
                self._stop_services()
                watchdog_logger.debug("Connection lost. Reconnecting...")
                self._start_services()
            for _ in range(0, self._check_interval, 1):
                if not self._running:
                    break
                time.sleep(1)

    def stop_dog(self):
        """
        Stops the watchdog thread.
        """
        watchdog_logger.debug("Stopping %s instance", self.__class__.__name__)
        self._running = False

    def start_dog(self):
        """
        Starts the watchdog thread.
        """
        watchdog_logger.debug("Starting %s instance", self.__class__.__name__)
        self._running = True
