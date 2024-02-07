"""
Classes for establishing and maintaining a connection with the broker's API.
"""

import logging
import time
import threading
import pandas as pd
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from src.api.ib_utils import ConnectionWatchdog
from src.utils.references import IB_API_LOGGER_NAME

broker_logger = logging.getLogger(IB_API_LOGGER_NAME)


class BrokerApiClient(ABC):
    """
    Abstract base class for brokerage API clients.
    """

    def __init__(self, host: str, port: int, client_id: int):
        """
        Constructs the BrokerApiClient.
        :param host: The hostname of the brokerage API.
        :param port: The port number of the brokerage API.
        :param client_id: The client ID to use when connecting to the brokerage API.
        """
        self._host = host
        self._port = port
        self._client_id = client_id
        self._connection_future = None
        self._run_connection_future = None
        self._executor = None
        self._request_lock = threading.Lock()
        self._watchdog = ConnectionWatchdog(
            check_interval=10,
            start_services=self.start_services,
            stop_services=self.stop_services,
            is_connected_method=self._verify_connection,
        )
        broker_logger.info(
            "Initializing %s instance", ConnectionWatchdog.__class__.__name__
        )

    def start_services(self) -> None:
        """
        Start the connection and watchdog threads. Creates a watchdog thread to monitor the API connection.
        """
        self._watchdog.start_dog()
        self._executor = ThreadPoolExecutor(max_workers=3)
        broker_logger.debug("%s establishing a connection", self.__class__.__name__)
        self._connection_future = self._executor.submit(self._connect_to_broker_api)
        # Wait for connection to be established
        while not self._verify_connection():
            time.sleep(1)
        broker_logger.debug(
            "%s is connected to the API. Assigning self._run_connection_future...",
            self.__class__.__name__,
        )
        self._run_connection_future = self._executor.submit(self._run_connection_thread)
        self._watchdog_future = self._executor.submit(self._watchdog.monitor_connection)

    def stop_services(self) -> None:
        """
        Stop the connection and watchdog threads.
        """
        broker_logger.debug(
            "%s is stopping services. Disconnecting from API and stopping watchdog thread.",
            self.__class__.__name__,
        )
        if self._verify_connection():
            self._disconnect_from_broker_api()
            while self._verify_connection():
                time.sleep(1)
        broker_logger.debug(
            "%s is disconnected from IB. Stopping watchdog thread.",
            self.__class__.__name__,
        )
        if self._watchdog_future:
            self._watchdog_future.cancel()
        if self._connection_future:
            self._connection_future.cancel()
        if self._run_connection_future:
            self._run_connection_future.cancel()
        self._watchdog.stop_dog()
        # self._executor.shutdown(wait=True)

    @abstractmethod
    def _run_connection_thread(self) -> None:
        """
        Run the connection thread to keep the connection alive. To avoid blocking the main thread,
        we run it in a separate thread.
        """

    @abstractmethod
    def _connect_to_broker_api(self) -> None:
        """
        Connect to the brokerage API.
        """

    @abstractmethod
    def _verify_connection(self) -> bool:
        """
        Verify there is an active connection to the brokerage API.
        """

    @abstractmethod
    def _disconnect_from_broker_api(self) -> None:
        """
        Disconnect from the brokerage API.
        """

    @abstractmethod
    def request_historical_data(self, **kwargs):
        """
        Request historical data.
        """
        pass

    @abstractmethod
    def error(self, reqId: int, errorCode: int, errorString: str):
        """
        Handle errors received from the brokerage API.
        """
        pass
