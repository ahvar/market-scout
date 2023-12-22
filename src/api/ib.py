"""
Classes for interacting with the IB API.
"""
import logging
import atexit
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
import pandas as pd
import backoff
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from src.api.ib_utils import ConnectionWatchdog
from src.utils.cli.cli import set_error_and_exit
from src.utils.references import (
    socket_drop,
    connection_broken,
    pacing_violation,
    mkt_data_farm_msgs,
    hist_data_farm_msgs,
    PriceBar,
)
from src.api.ib_api_exception import (
    IBApiException,
    IBApiConnectionException,
    IBApiDataRequestException,
)
from src.utils.references import __Application__, __version__

IB_API_LOGGER_NAME = f"{__Application__}_{__version__}_driver"
ib_api_logger = logging.getLogger(IB_API_LOGGER_NAME)


class IBApiClient(EWrapper, EClient):
    """
    Serves as the intermediary between the IB API and the app logic. Handles connecting/reconnecting, errors, formatting responses.

    Callbacks: https://interactivebrokers.github.io/tws-api/callbacks.html
    ---------------------------------------------------------------------------------------------------------------------------------
    When working with Interactive Brokers, one of the main concepts to understand is that it works in an asynchronous way. This means
    that when you request data, you don't get it immediately. Instead, you get it through a callback. For example, when you request
    historical data, you get it through the historicalData() callback.
    """

    def __init__(self, host: str, port: int, client_id: int):
        """
        Initialize the IBApi instance.

        :param host: The hostname or IP address of the machine on which the TWS or IB Gateway is running.
        :param port: The port on which the TWS or IB Gateway is listening.
        :param client_id: A unique identifier for the client application.
        """
        ib_api_logger.info("Initializing %s instance", self.__class__.__name__)
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self._host = host
        self._port = port
        self._client_id = client_id
        self._connection_future = None
        self._run_connection_future = None
        self._request_counter = 0
        self._request_lock = threading.Lock()
        self._watchdog_future = None
        self._watchdog = ConnectionWatchdog(
            check_interval=10,
            start_services=self.start_services,
            stop_services=self.stop_services,
            is_connected_method=self.isConnected,
        )
        self._executor = None
        self._historical_data = pd.DataFrame(
            columns=[
                PriceBar.date,
                PriceBar.open,
                PriceBar.high,
                PriceBar.low,
                PriceBar.close,
                PriceBar.volume,
            ]
        )
        atexit.register(self.disconnect_from_ib)
        # Use % formatting instead of f-strings because f-strings are interpolated at runtime. We save some performance overhead by not evaluating the f-string.
        ib_api_logger.info(
            "%s instance initialized. \nHost: %s\nPort: %s\nClient_ID: %s",
            self.__class__.__name__,
            self._host,
            self._port,
            self._client_id,
        )

    def start_services(self) -> None:
        """
        Start the connection and watchdog threads. Creates a watchdog thread to monitor the connection to the IB API.
        """
        self._watchdog.start_dog()
        self._executor = ThreadPoolExecutor(max_workers=3)
        ib_api_logger.debug(
            "%s establishing a connection with IB API", self.__class__.__name__
        )
        self._connection_future = self.executor.submit(self.connect_to_ib)
        # Wait for connection to be established
        while not self.isConnected():
            time.sleep(1)
        ib_api_logger.debug(
            "%s is connected to IB API. Calling run() to continuously listen for messages from IB Gateway and watchdog threads.",
            self.__class__.__name__,
        )
        self._run_connection_future = self._executor.submit(self._run_connection_thread)
        self._watchdog_future = self._executor.submit(self._watchdog.monitor_connection)

    def stop_services(self) -> None:
        """
        Stop the connection and watchdog threads.
        """
        ib_api_logger.debug(
            "%s is stopping services. Disconnecting from IB and stopping watchdog thread.",
            self.__class__.__name__,
        )
        if self.isConnected():
            self.disconnect_from_ib()
            while self.isConnected():
                time.sleep(1)
        ib_api_logger.debug(
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

    def _run_connection_thread(self) -> None:
        """
        Run the connection thread to keep the IB connection alive. To do this we call the IBApi.run() method
        of the EClient class, which is a blocking call. To avoid blocking the main thread, we run it in a
        separate thread.
        """
        self.run()

    @backoff.on_exception(
        backoff.expo,
        IBApiException,
        max_tries=8,
        max_time=300,
        jitter=backoff.full_jitter,
    )
    def connect_to_ib(self) -> None:
        """
        Connect to the IB Gateway or TWS. This method is decorated with the backoff decorator to retry connection attempts.
        It attempts to establish a connection to the IB Gateway or TWS, and if successful, starts the connection and watchdog threads.
        The connection and watchdog threads are started in separate threads to avoid blocking the main thread. The connection thread
        is started by calling the IBApiClient.run() method of the EClient class, which is a blocking call. The watchdog thread is started
        by calling the ConnectionWatchdog.monitor_connection() method, which is a non-blocking call.
        """
        ib_api_logger.debug(
            "%s is connecting to IB with host %s, port %s, and client_id %s",
            self.__class__.__name__,
            self._host,
            self._port,
            self._client_id,
        )
        try:
            self.connect(self._host, self._port, self._client_id)

        except Exception as e:
            ib_api_logger.error("Error while connecting to IB: %s", e)
            raise IBApiConnectionException(
                "An error occurred while connecting to IB"
            ) from e

    def disconnect_from_ib(self) -> None:
        """
        Disconnect from the IB Gateway or TWS.
        """
        try:
            self.disconnect()
        except Exception as e:
            ib_api_logger.error("Error while disconnecting from IB: %s", e)
            raise IBApiConnectionException(
                "An error occurred while disconnecting from IB"
            ) from e

    def historicalData(self, reqId: int, bar):
        """
        This callback is invoked for every data point/bar received from the IB API.

        :params reqId: The request ID that this bar data is associated with.
        :params   bar: The bar data that was received.
        """
        try:
            new_row = {
                PriceBar.date: bar.date,
                PriceBar.open: bar.open,
                PriceBar.high: bar.high,
                PriceBar.low: bar.low,
                PriceBar.close: bar.close,
                PriceBar.volume: bar.volume,
            }
            self._historical_data = self._historical_data.append(
                new_row, ignore_index=True
            )
        except KeyError as e:
            ib_api_logger.error(
                "%s encountered a KeyError while processing historical data. ReqId: %s, Error: %s",
                self.__class__.__name__,
                reqId,
                e,
            )
        except pd.errors.ParserError as e:
            ib_api_logger.error(
                "%s encountered Pandas error while parsing historical data. ReqId: %s, Error: %s",
                self.__class__.__name__,
                reqId,
                e,
            )
        except pd.errors.EmptyDataError as e:
            ib_api_logger.error(
                "%s encountered a Pandas EmptyDataError while processing historical data. ReqId: %s, Error: %s",
                self.__class__.__name__,
                reqId,
                e,
            )
        except ValueError as e:
            ib_api_logger.error(
                "%s encountered a ValueError while processing historical data. ReqId: %s, Error: %s",
                self.__class__.__name__,
                reqId,
                e,
            )
        except Exception as e:
            ib_api_logger.error(
                "%s encountered an unexpected error while processing historical data. ReqId: %s, Error: %s",
                self.__class__.__name__,
                reqId,
                e,
            )

    def historicalDataEnd(self, reqId: int, start: str, end: str) -> None:
        """
        This callback indicates the end of the data transmission for the specific request.
        This method will be called for every data point (or bar) that is returned by the API.

        :params reqId: The request ID that this bar data is associated with.
        :params start: The start date and time for the request.
        :params   end: The end date and time for the request.
        """
        # This indicates the end of historical data transmission for the request with id `reqId`
        # You can now finalize the processing for this data set, e.g., writing to a file or sending a signal that data is ready.
        try:
            ib_api_logger.debug(
                "%s received historical data end signal. ReqId: %s, Start: %s, End: %s",
                self.__class__.__name__,
                reqId,
                start,
                end,
            )
            self._historical_data.set_index(PriceBar.date, inplace=True)
            self._historical_data.index = pd.to_datetime(
                self._historical_data.index, unit="s"
            )
            self._historical_data.sort_index(inplace=True)
            ib_api_logger.debug(
                "%s is sending historical data to the app logic. ReqId: %s, Data: %s",
                self.__class__.__name__,
                reqId,
                self._historical_data,
            )
        except Exception as e:
            ib_api_logger.error(
                "%s encountered an unexpected error while processing historical data. ReqId: %s, Error: %s",
                self.__class__.__name__,
                reqId,
                e,
            )

    def error(self, reqId: int, errorCode: int, errorString: str) -> None:
        """
        Callback for errors received from the IB API.

        :param reqId: The request ID that this error is associated with. If the error isn't associated with a request, reqId will be -1.
        :param errorCode: The error code.
        :param errorString: A description of the error.
        """
        if errorCode in socket_drop:  # Server and system messages
            ib_api_logger.critical(
                "Socket port was reset. %s will stop services and exit. Code: %s, Msg: %s",
                self.__class__.__name__,
                errorCode,
                errorString,
            )
            self.stop_services()
            set_error_and_exit(errorString)
        elif errorCode in connection_broken:  # Connection lost/restored without API
            ib_api_logger.debug(
                "Connection lost. Code: %s, Msg: %s",
                errorCode,
                errorString,
            )
            ib_api_logger.debug(
                "%s is attempting to reconnect to IB", self.__class__.__name__
            )
            # NOTE: potential for this to be an infinite loop if the connection is never restored
            self.stop_services()
            self.start_services()
        elif errorCode in pacing_violation:  # Historical data request pacing violation
            ib_api_logger.warning(
                "Historical data request pacing violation. Code: %s, Msg: %s",
                errorCode,
                errorString,
            )
            # TODO: Implement logic to slow down historical data requests.
        else:
            # General error handling
            ib_api_logger.error(
                "Error. ReqId: %s, Code: %s, Msg: %s", reqId, errorCode, errorString
            )
            # Here, you can decide whether to raise an exception or handle it differently
            # depending on the severity of the error.
            if self._is_critical_error(errorCode):
                raise IBApiConnectionException(
                    f"Critical error occurred: {errorString}"
                )

    def _is_critical_error(self, error_code: int) -> bool:
        """
        Determine if the given error code is considered critical.

        :params errorCode: The error code.
        """
        # Define your own set of critical error codes
        critical_errors = {...}  # Populate with actual critical error codes
        return error_code in critical_errors

    def request_historical_data(
        self,
        contract: Contract,
        end_datetime: str,
        duration: str,
        bar_size: str,
        use_rth: int,
    ) -> None:
        """
        Requests historical data from IB.
        :param contract: The contract for which historical data is requested.
        :param end_datetime: The end date and time for the data request.
        :param duration: The duration for which data is requested (e.g., '2 D' for 2 days).
        :param bar_size: The size of the bars in the data request (e.g., '1 hour').
        :param use_rth: Whether to use regular trading hours only (1 for Yes, 0 for No).
        """
        req_id = self._get_next_request_id()
        ib_api_logger.debug(
            "%s is requesting historical data from IB for %s with end_datetime %s, duration %s, bar_size %s, use_rth %s, and req_id %s",
            self.__class__.__name__,
            contract.symbol,
            end_datetime,
            duration,
            bar_size,
            use_rth,
            req_id,
        )
        try:
            self.reqHistoricalData(
                req_id,
                contract,
                end_datetime,
                duration,
                bar_size,
                "TRADES",
                use_rth,
                1,
                False,
                [],
            )
        except Exception as e:
            ib_api_logger.error(
                "%s encountered an error while requesting historical data from IB: %s",
                self.__class__.__name__,
                e,
            )
            raise IBApiDataRequestException(
                "An error occurred while requesting data from IB"
            ) from e

    def _get_next_request_id(self) -> int:
        """
        Get the next request ID for the IB API. The IB API requires a unique request ID for each request.
        Locks counter increment to ensure thread safety.
        """
        with self._request_lock:
            self._request_counter += 1
            return self._request_counter

    @property
    def request_counter(self) -> int:
        """
        Get the current request counter.
        """
        return self._request_counter

    @property
    def watchdog_future(self) -> Future:
        """
        Get the watchdog future.
        """
        return self._watchdog_future

    @watchdog_future.setter
    def watchdog_future(self, watchdog_future: Future) -> None:
        """
        Set the watchdog future.
        """
        self._watchdog_future = watchdog_future

    @property
    def connection_thread(self) -> threading.Thread:
        """
        Get the connection thread.
        """
        return self._run_connection_future

    @connection_thread.setter
    def connection_thread(self, connection_thread: threading.Thread) -> None:
        """
        Set the connection thread.
        """
        self._run_connection_future = connection_thread

    @property
    def executor(self) -> ThreadPoolExecutor:
        """
        Get the executor.
        """
        return self._executor

    @executor.setter
    def executor(self, executor: ThreadPoolExecutor) -> None:
        """
        Set the executor.
        """
        self._executor = executor

    @property
    def making_connection_attempt(self) -> bool:
        """
        Returns True if Watchdog is attempting a connection.
        """
        return self._making_connection_attempt

    @making_connection_attempt.setter
    def making_connection_attempt(self, value: bool) -> None:
        """
        Sets the value of making_connection_attempt.
        """
        self._making_connection_attempt = value
