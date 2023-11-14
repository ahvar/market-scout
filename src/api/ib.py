"""
Classes for interacting with the IB API.
"""
import logging
import atexit
import threading
import pandas as pd
import backoff as backoff
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from concurrent.futures import ThreadPoolExecutor, Future
from src.api.ib_utils import ConnectionWatchdog
from src.utils.references import (
    server_and_system_msgs,
    connection_disruptions,
    pacing_violation,
    mkt_data_farm_msgs,
    hist_data_farm_msgs,
)
from src.api.ib_api_exception import (
    IBApiException,
    IBApiConnectionException,
    IBApiDataRequestException,
)
from src.utils.cli.cli import __Application__, __version__

IB_API_LOGGER_NAME = __Application__ + "__" + __version__

ib_api_logger = logging.getLogger(IB_API_LOGGER_NAME)


class IBApi(EWrapper, EClient):
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
        ib_api_logger.debug("Initializing %s instance", self.__class__.__name__)
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self._host = host
        self._port = port
        self._client_id = client_id
        self._connection_future = None
        self._request_counter = 0
        self._request_lock = threading.Lock()
        self._watchdog_future = None
        self._executor = ThreadPoolExecutor(max_workers=2)
        atexit.register(self._disconnect_from_ib)
        # Use % formatting instead of f-strings because f-strings are evaluated at runtime, and we want to log the exception as it was at the time of the error.
        # We save some performance overhead by not evaluating the f-string.
        ib_api_logger.debug(
            "%s instance initialized. \nHost: %s\nPort: %s\nClient_ID: %s",
            self.__class__.__name__,
            self._host,
            self._port,
            self._client_id,
        )

    def _start_services(self) -> None:
        """
        Start the connection and watchdog threads.
        """
        self._connection_future = self._executor.submit(self._run_connection_thread)
        watchdog = ConnectionWatchdog(
            check_interval=10,
            connect_method=self.connect_to_ib,
            is_connected_method=self.isConnected,
        )
        self._watchdog_future = self._executor.submit(watchdog.monitor_connection)

    def _stop_services(self) -> None:
        """
        Stop the connection and watchdog threads.
        """
        if self._watchdog_future:
            self._watchdog_future.cancel()
        self._executor.shutdown(wait=True)

    def _run_connection_thread(self) -> None:
        """
        Run the connection thread to keep the IB connection alive. To do this we call the IBApi.run() method
        of the EClient class, which is a blocking call. To avoid blocking the main thread, we run it in a
        separate thread. To manage the thread, we use the threading module.
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
        Connect to the IB Gateway or TWS. This method is called from the main thread. We want to ensure that
        the connection thread always finishes its tasks and closes the connection gracefully, therefore, we
        choose not to set the daemon flag of the thread to True, so that the thread is kept alive even if the
        main thread terminates. This is important because the IBApi.run() method is blocking, and we want to
        keep the connection alive until we explicitly disconnect. It also ensures that the connection is not
        terminated when the main thread terminates, which can happen if the user presses Ctrl+C.
        """
        if not self.isConnected():
            ib_api_logger.debug(
                "%s is connecting to IB with host %s, port %s, and client_id %s",
                self.__class__.__name__,
                self._host,
                self._port,
                self._client_id,
            )
            try:
                self.connect(self._host, self._port, self._client_id)
                self._start_services()
            except Exception as e:
                ib_api_logger.error("Error while connecting to IB: %s", e)
                raise IBApiConnectionException(
                    "An error occurred while connecting to IB"
                ) from e
        else:
            ib_api_logger.debug("%s already connected to IB", self.__class__.__name__)

    def _disconnect_from_ib(self) -> None:
        """
        Disconnect from the IB Gateway or TWS.
        """
        if self.isConnected():
            try:
                self.disconnect()
                if self._connection_future:
                    self._connection_future.join()  # Wait for the thread to complete
                    self._connection_future = None
                    self._stop_services()
            except Exception as e:
                ib_api_logger.error("Error while disconnecting from IB: %s", e)
                raise IBApiConnectionException(
                    "An error occurred while disconnecting from IB"
                ) from e

        else:
            ib_api_logger.debug(
                "%s is already disconnected from IB", self.__class__.__name__
            )

    def historicalData(self, reqId: int, bar):
        """
        This callback is invoked for every data point/bar received from the IB API.

        :params reqId: The request ID that this bar data is associated with.
        :params   bar: The bar data that was received.
        """
        try:
            date = bar.date
            open_ = bar.open
            high = bar.high
            low = bar.low
            close = bar.close
            volume = bar.volume
            # You can now process/store this data as needed.
            # For example, you could append it to a list or store it in a database.
        except Exception as e:
            ib_api_logger.error(
                "Error while processing historical data. ReqId: %s, Error: %s", reqId, e
            )
            # Here you can add logic to handle the error, such as retrying the request,
            # notifying the user, or storing the error in a log or database.

    def historicalDataEnd(self, reqId: int, start: str, end: str):
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
            pass
        except Exception as e:
            ib_api_logger.error(
                "Error at the end of historical data transmission. ReqId: %s, Error: %s",
                reqId,
                e,
            )

    def error(self, reqId: int, errorCode: int, errorString: str):
        """
        Callback for errors received from the IB API.

        :param reqId: The request ID that this error is associated with. If the error isn't associated with a request, reqId will be -1.
        :param errorCode: The error code.
        :param errorString: A description of the error.
        """
        if errorCode in server_and_system_msgs:  # Server and system messages
            ib_api_logger.critical(
                "Server or system message. Code: %s, Msg: %s", errorCode, errorString
            )
            # TODO: Implement connection retry logic here if necessary.
        elif (
            errorCode in connection_disruptions
        ):  # Connection lost/restored without API
            ib_api_logger.warning(
                "Connection lost/restored without API. Code: %s, Msg: %s",
                errorCode,
                errorString,
            )
            # TODO: Decide whether to pause operations or wait for reconnection.
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
    def watchdog(self) -> ConnectionWatchdog:
        """
        Get the watchdog thread.
        """
        return self._watchdog_future

    @watchdog.setter
    def watchdog(self, watchdog: ConnectionWatchdog) -> None:
        """
        Set the watchdog thread.
        """
        self._watchdog_future = watchdog

    @property
    def connection_thread(self) -> threading.Thread:
        """
        Get the connection thread.
        """
        return self._connection_future

    @connection_thread.setter
    def connection_thread(self, connection_thread: threading.Thread) -> None:
        """
        Set the connection thread.
        """
        self._connection_future = connection_thread

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
