"""
Utility classes and functions for the IB API.
"""

from typing import Any, Callable
import time


class ConnectionWatchdog:
    """
    A watchdog class that monitors the connection to the IB API and
    """

    def __init__(
        self,
        check_interval: int,
        connect_method: Callable[[], None],
        is_connected_method: Callable[[], bool],
    ):
        """
        Constructs the watchdog class.
        :params check_interval: The interval in seconds to check the connection.
        :params connect_method: The method to call to reconnect to the IB API.
        """
        super().__init__()
        self._check_interval = check_interval  # seconds
        self._connect_method = (
            connect_method  # method to call to reconnect to the IB API
        )
        self._is_connected_method = (
            is_connected_method  # method to call to check if the connection is alive
        )
        self._running = True

    def monitor_connection(self):
        """
        Runs the watchdog thread.
        To make ConnectionWatchdog more responsive, there are multiple
        shorter sleeps in a loop, each time checking the _running flag.
        """
        while self._running:
            if not self._is_connected_method():
                self._connect_method()
            for _ in range(0, self._check_interval, 1):
                if not self._running:
                    break
                time.sleep(1)

    def stop(self):
        """
        Stops the watchdog thread.
        """
        self._running = False
