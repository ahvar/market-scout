"""
Utility classes and functions for the IB API.
"""

from typing import Any, Callable
import threading
import time


class ConnectionWatchdog(threading.Thread):
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

    def run(self):
        """
        Runs the watchdog thread.
        """
        while self._running:
            if not self._is_connected_method():
                self.handle_reconnection()
            time.sleep(self._check_interval)

    def is_connection_alive(self):
        """
        Checks if the connection to the IB API is alive.
        :returns: True if the connection is alive, False otherwise.
        """
        pass

    def handle_reconnection(self):
        """
        Handles the reconnection to the IB API.
        """
        self._connect_method()

    def stop(self):
        """
        Stops the watchdog thread.
        """
        self._running = False
