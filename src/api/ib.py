"""
Classes for interacting with the IB API.
"""

import logging
import atexit
import threading
from datetime import datetime, timedelta
import time
from concurrent.futures import Future, ThreadPoolExecutor
import pandas as pd
import numpy as np
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
    bar_sizes,
)
from src.api.ib_api_exception import (
    IBApiException,
    IBApiConnectionException,
    IBApiDataRequestException,
    HistoricalDatatMissingException,
)
from src.utils.references import IB_API_LOGGER_NAME

ib_api_logger = logging.getLogger(IB_API_LOGGER_NAME)


class IBApiClient(EWrapper, EClient):
    """
    Interface for other system components to access IB API.
     - Handles connection
     - data requests

    Callbacks: https://interactivebrokers.github.io/tws-api/callbacks.html
    ---------------------------------------------------------------------------------------------------------------------------------
    Interactive Brokers API works in an asynchronously, returning the requested data through a callback.
    The callback methods are defined in the EWrapper class, and the EClient class. The EClient class is
    responsible for sending requests to the TWS or IB Gateway, and the EWrapper class is responsible for
    receiving the data from the TWS or IB Gateway and processing it.
    """

    def __init__(self, host: str, port: int, client_id: int):
        """
        Initialize the IBApiClient instance.

        :param      host: The hostname or IP address of the machine on which the TWS or IB Gateway is running.
        :param      port: The port on which the TWS or IB Gateway is listening.
        :param client_id: A unique identifier for the client application and used in communication with the TWS or IB Gateway.
        """
        ib_api_logger.info("Initializing %s instance", self.__class__.__name__)
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self._host = host
        self._port = port
        self._client_id = client_id
        self._bar_size = ""
        self._connection_future = None
        self._run_connection_future = None
        self._ticker_id = 0
        self._current_ticker = None
        self._temp_hist_data = {}
        self._missing_hist_data = {}
        self._request_lock = threading.Lock()
        self._watchdog_future = None
        self._watchdog = ConnectionWatchdog(
            check_interval=10,
            start_services=self.start_services,
            stop_services=self.stop_services,
            is_connected_method=self.isConnected,
        )
        self._executor = None
        self._historical_data = {}
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
        The connection and watchdog threads are separate to avoid blocking the main thread. The connection thread is started by calling
        the IBApiClient.run() method of the EClient class, which is a blocking call. The watchdog thread is started by calling the
        ConnectionWatchdog.monitor_connection() method, which is a non-blocking call.
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

    def historicalData(self, reqId: int, bar: object):
        """
        Invoked for every data point/bar received from the IB API. The reqID
        is set in IBApiClient.request_historical_data(). To avoid overhead of
        adding each delivered bar to historical cache, data is stored in a
        temporary historical cache, and then bulk added to the historical cache
        when temp hist reaches 100 items.

        NOTE: Expected Bar Data Structure
        -----------------------------------------------------------------
        - The bar data received from the IB API is expected to be in the
            following format:
            BarData(date, open, high, low, close, volume, barCount, average, hasGaps, WAP, hasGaps)
        - The bar data is converted to a dictionary with the following keys:
            {
                "ticker": ticker,
                "date": date,
                "open": open,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "data_partially_missing": True/False
            }
        - The dictionary is added to the temp hist data cache.
        -----------------------------------------------------------------

        NOTE: Handling Missing Bar Data
        -----------------------------------------------------------------
        - Pandas may error if attempts are made to concatenate multiple
          empty rows, which occurs if all bar data is unavailable.
        - This is handled by utilizing the date from the last accessible bar
          in either historical, or temporary historical, data cache(s) and the
          specified bar size to calculate the anticipated date for the missing bar.
        - Consequently, a record is generated for this missing data, with all
          fields except for the ticker and date being marked as N/A.
        -----------------------------------------------------------------

        :params reqId: The request ID that this bar data is associated with.
        :params   bar: The bar data that was received.
        """
        if self._all_bar_data_missing(bar):
            try:
                new_row = self._get_new_row_for_missing_bar(reqId, bar)
                self._add_bar_data_to_temp_hist_cache(reqId, new_row)
            except HistoricalDatatMissingException as e:
                ib_api_logger.error(
                    "%s encountered an error while processing historical data. ReqId: %s, Error: %s",
                    self.__class__.__name__,
                    reqId,
                    e,
                )
            return

        new_row = {
            # NOTE: letting Pandas handle the conversion to datetime rather than applying the conversion here
            # IB API says bar date format="%Y%m%d %H:%M:%S" but found this not to work consistently
            PriceBar.ticker: self._current_ticker,
            PriceBar.date: pd.to_datetime(bar.date),
            PriceBar.open: bar.open,
            PriceBar.high: bar.high,
            PriceBar.low: bar.low,
            PriceBar.close: bar.close,
            PriceBar.volume: bar.volume,
            PriceBar.data_partially_missing: self._data_partially_missing(bar),
        }

        self._add_bar_data_to_temp_hist_cache(reqId, new_row)
        try:
            # If the temp hist data list has 100 items, add it to the historical data list and clear the temp hist data list
            if len(self._temp_hist_data[reqId]) == 100:
                self._add_bulk_temp_hist_data(reqId)

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

    def _get_new_row_for_missing_bar(self, reqId: int, bar: object) -> None:
        """
        Add a record for the missing bar data.

        :params reqId: The request ID that this bar data is associated with.
        :params   bar: The bar data that was received.
        """
        ib_api_logger.debug(
            "%s received historical data with all bar data missing. ReqId: %s, Bar: %s",
            self.__class__.__name__,
            reqId,
            bar,
        )
        ib_api_logger.debug(
            "%s will use the date from the last available bar to determine the correct date for this missing bar.",
            self.__class__.__name__,
        )
        last_available_date = None
        if self._temp_hist_data[reqId]:
            last_available_date = self._get_last_available_bar_date(
                reqId, use_temp_data=True
            )
        elif reqId in self._historical_data:
            last_available_date = self._get_last_available_bar_date(
                reqId, use_temp_data=False
            )
        if not last_available_date:
            raise HistoricalDatatMissingException(
                f"{self.__class__.__name__} could not find the date for the last available bar from the temporary historical data cache or historical data cache"
            )
        return {
            PriceBar.ticker: self._current_ticker,
            PriceBar.date: self._compute_missing_bar_date_from_last_available(
                last_available_date, reqId
            ),
            PriceBar.open: np.NAN,
            PriceBar.high: np.NAN,
            PriceBar.low: np.NAN,
            PriceBar.close: np.NAN,
            PriceBar.volume: np.NAN,
            PriceBar.data_partially_missing: True,
        }

    def _get_last_available_bar_date(self, reqId: int, use_temp_data: bool) -> datetime:
        """
        Get the date of the last available bar from the specified data cache.

        :params               reqId: The request ID that this bar data is associated with.
        :params         use_temp_data: Boolean flag to determine which data structure to access.
        :return last_available_date: datetime representation of the date from the last available bar in the specified cache.
        """
        data_cache = self._temp_hist_data if use_temp_data else self._historical_data
        index = len(data_cache[reqId]) - 1

        while index >= 0:
            last_available_date = data_cache[reqId][index].get(PriceBar.date)
            if last_available_date:
                ib_api_logger.debug(
                    "%s got the date for the last available bar from the %s data cache to be %s",
                    self.__class__.__name__,
                    "temporary historical" if use_temp_data else "historical",
                    last_available_date.strftime("%Y-%m-%d %H:%M:%S"),
                )
                return last_available_date
            index -= 1
        return None

    def _compute_missing_bar_date_from_last_available(
        self, last_available_date: datetime, reqId: int
    ) -> datetime:
        """
        The date for the current bar is computed by first parsing the bar size (e.g. '1 hour')
        for this request for the bar size time unit and the number of units, and then using these
        values to calculate what the date of the next bar would have been. This is done by adding
        the bar size time unit to the date of the previous bar.

        Notes:
        - time period unit of measurement passed to timedelta must be plural

        :params        last_availale_date: The bar data pulled from temporary historical cache or historical data cache.
        :params                     reqId: The request ID that this bar data is associated with.
        :return   datetime_of_missing_bar: datetime representation of the date of the next bar.
        """
        try:
            bar_size_int = int(self._bar_size.split()[0])
            bar_size_unit = self._bar_size.split()[1]
            if bar_size_unit[-1] != "s":
                bar_size_unit += "s"
            time_delta = timedelta(**{bar_size_unit.lower(): bar_size_int})
            datetime_of_missing_bar = last_available_date + time_delta
            return datetime_of_missing_bar
        except Exception as e:
            raise HistoricalDatatMissingException(
                f"{self.__class__.__name__} encountered an error while computing the date of the missing bar. ReqId: {reqId}, Error: {e}"
            ) from e

    def _data_partially_missing(self, bar_data: object) -> bool:
        """
        Determine if the given bar has any missing data.

        :params bar_data: The bar data that was received.
        """
        return (
            bar_data.date is None
            or bar_data.open is None
            or bar_data.high is None
            or bar_data.low is None
            or bar_data.close is None
            or bar_data.volume is None
        )

    def _all_bar_data_missing(self, bar_data: object) -> bool:
        """
        Determine if all bar data is missing.

        :params bar_data: The bar data that was received.
        """
        return (
            bar_data.date is None
            and bar_data.open is None
            and bar_data.high is None
            and bar_data.low is None
            and bar_data.close is None
            and bar_data.volume is None
        )

    def _add_bar_data_to_temp_hist_cache(self, reqId: int, bar_data: {}) -> None:
        """
        Add bar data to the temp historical data cache.

        :params                 reqId: The request ID that this bar data is associated with.
        :params              bar_data: The bar data that was received.
        """
        if reqId not in self._temp_hist_data:
            self._temp_hist_data[reqId] = []
        self._temp_hist_data[reqId].append(bar_data)

    def _add_bulk_temp_hist_data(self, reqId: int) -> None:
        """
        Add historical data to the historical data and clear the temp hist data.

        :params reqId: The request ID that this bar data is associated with.
        """
        new_data_df = pd.DataFrame(self._temp_hist_data[reqId])
        # self._historical_data[reqId] = self._historical_data[reqId].dropna(
        #    how="all", axis=1
        # )
        self._historical_data[reqId] = pd.concat(
            [self._historical_data[reqId], new_data_df], ignore_index=True
        )
        self._temp_hist_data[reqId] = []

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
        elif errorCode in mkt_data_farm_msgs:  # Market data farm messages
            ib_api_logger.warning(
                "Market data farm message. Code: %s, Msg: %s",
                errorCode,
                errorString,
            )
        elif errorCode in hist_data_farm_msgs:  # Historical data farm messages
            ib_api_logger.warning(
                "Historical data farm message. Code: %s, Msg: %s",
                errorCode,
                errorString,
            )
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
        :param end_datetime: The end date and time for the data request.
        :param duration: The duration for which data is requested (e.g., '2 D' for 2 days).
        :param bar_size: The size of the bars in the data request (e.g., '1 hour').
        :param use_rth: Whether to use regular trading hours only (1 for Yes, 0 for No).
        """
        ticker_id = self._get_next_ticker_id()
        if ticker_id in self._historical_data:
            ib_api_logger.debug(
                "%s is clearing historical data for ticker ID %s",
                self.__class__.__name__,
                ticker_id,
            )
            self._historical_data[ticker_id].drop(
                self._historical_data[ticker_id].index, inplace=True
            )
        self._historical_data[ticker_id] = pd.DataFrame(
            columns=[
                PriceBar.ticker,
                PriceBar.date,
                PriceBar.open,
                PriceBar.high,
                PriceBar.low,
                PriceBar.close,
                PriceBar.volume,
            ]
        )
        self._current_ticker = contract.symbol
        self._bar_size = bar_size
        ib_api_logger.debug(
            "%s is requesting historical data from IB for %s with end_datetime %s, duration %s, bar_size %s, use_rth %s, and req_id %s",
            self.__class__.__name__,
            contract.symbol,
            end_datetime,
            duration,
            bar_size,
            use_rth,
            ticker_id,
        )
        try:
            self.reqHistoricalData(
                ticker_id,
                contract,
                end_datetime,
                duration,
                bar_size,
                "TRADES",
                use_rth,
                1,
                False,
                None,
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

    def historicalDataUpdate(self, reqId: int, bar):
        """
        This callback is invoked for every data point/bar received from the IB API.
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

    def _get_next_ticker_id(self) -> int:
        """
        Get the next ticker ID for an IB API request. The IB API requires a unique ticker ID which will identify incoming data.
        Locks ticker increment to ensure thread safety.
        """
        ib_api_logger.debug(
            "%s is getting the next ticker ID for the IB API", self.__class__.__name__
        )
        with self._request_lock:
            self._ticker_id += 1
            ib_api_logger.debug(
                "%s is returning the next ticker ID for the IB API: %s",
                self.__class__.__name__,
                self._ticker_id,
            )
            return self._ticker_id

    @property
    def ticker_id(self) -> int:
        """
        Get the current request counter.
        """
        return self._ticker_id

    @property
    def current_ticker(self) -> str:
        """
        Get the current ticker.
        """
        return self._current_ticker

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

    @property
    def historical_data(self) -> pd.DataFrame:
        """
        Returns the historical data.
        """
        return self._historical_data
