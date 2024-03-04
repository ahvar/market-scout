"""
Classes for interacting with the IB API.
"""

# standard library
import logging
import atexit
from datetime import datetime, timedelta
from typing import Tuple, Optional
import pandas as pd
import numpy as np
import backoff

# third-party
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import BarData
from src.utils.cli.cli import set_error_and_exit
from src.utils.references import (
    socket_drop,
    connection_broken,
    pacing_violation,
    mkt_data_farm_msgs,
    hist_data_farm_msgs,
    PriceBar,
    bar_sizes,
    backoff_params,
)
from src.api.ib_api_exception import (
    IBApiException,
    IBApiConnectionException,
    IBApiDataRequestException,
    HistoricalDataMissingException,
)
from src.api.brokerage.client import BrokerApiClient
from src.api.ib_utils import MarketMemory
from src.utils.references import IB_API_LOGGER_NAME

ib_api_logger = logging.getLogger(IB_API_LOGGER_NAME)


class IBApiClient(BrokerApiClient, EWrapper, EClient):
    """
    Concrete class for accessing Interactive Brokers API.

    Callbacks: https://interactivebrokers.github.io/tws-api/callbacks.html
    ---------------------------------------------------------------------------------------------------
    Interactive Brokers API works asynchronously, returning the requested data through a callback.
    The callback methods are defined in the EWrapper class, and the EClient class. The EClient class is
    responsible for sending requests to the TWS or IB Gateway, and the EWrapper class is responsible for
    receiving the data from the TWS or IB Gateway and processing it.
    """

    def __init__(
        self, market_memory: MarketMemory, host: str, port: int, client_id: int
    ):
        """
        Initialize the IBApiClient instance.
        :param market_memory: The market memory instance.
        :param          host: The hostname or IP address of the machine on which the TWS or IB Gateway is running.
        :param          port: The port on which the TWS or IB Gateway is listening.
        :param     client_id: A unique identifier for the client application and used in communication with the TWS or IB Gateway.
        """
        super().__init__(market_memory, host, port, client_id)
        ib_api_logger.info("Initializing %s instance", self.__class__.__name__)
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self._bar_size = ""
        self._current_ticker = None
        atexit.register(self._disconnect_from_broker_api)
        # Use % formatting instead of f-strings because f-strings are interpolated at runtime.
        # We save some performance overhead by not evaluating the f-string.
        ib_api_logger.info(
            "%s instance initialized. \nHost: %s\nPort: %s\nClient_ID: %s",
            self.__class__.__name__,
            self._host,
            self._port,
            self._client_id,
        )

    def _run_connection_thread(self) -> None:
        """
        Inherited from BrokerApiClient. For Interactive Brokers, EClient.run(), which is a blocking call,
        keeps the IB connection alive. To avoid blocking the main thread, we run it in a separate thread.
        """
        self.run()

    def _verify_connection(self) -> bool:
        """
        Inherited from BrokerApiClient.
        Verify that the connection to the IB Gateway or TWS is alive.
        """
        return self.isConnected()

    @backoff.on_exception(backoff.expo, IBApiException, **backoff_params)
    def _connect_to_broker_api(self) -> None:
        """
        Inherited from BrokerApiClient.
        Connect to the IB Gateway or TWS. We add a backoff decorator to retry connection attempts.
        It attempts to establish a connection to the IB Gateway or TWS, and if successful, starts
        the connection and watchdog threads. The connection and watchdog threads are separate to
        avoid blocking the main thread. The watchdog thread is started by calling the ConnectionWatchdog.monitor_connection()
        method, which is a non-blocking call.
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

    def _disconnect_from_broker_api(self) -> None:
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

    def historicalData(self, reqId: int, bar: BarData):
        """
        Invoked for every bar received from the IB API. The reqID is set in
        IBApiClient.request_historical_data(). To avoid overhead of adding
        each delivered bar to historical cache, data is stored in a temporary
        historical cache, and then bulk added to the historical cache when temp
        hist reaches 100 items.

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
        - To handle empty rows, the date from the last accessible bar
          in either historical, or temporary historical, data cache(s) is used
          with and specified bar size to calculate the date for the missing bar.
        - Consequently, a record is generated for this missing data, with all
          fields except for the ticker and date being N/A.
        -----------------------------------------------------------------

        :params reqId: The request ID that this bar data is associated with.
        :params   bar: The bar data that was received.
        """
        try:
            verified_bar = self._market_memory.verify_bar(bar, self._bar_size)
            verified_bar["ticker"] = self._current_ticker
            if len(self._market_memory.temp_hist_data[reqId]) == 100:
                self._market_memory.add_bulk_to_hist_cache(reqId)
            self._market_memory.add_to_temp_hist_cache(reqId, verified_bar)
        except (pd.errors.ParserError, pd.errors.EmptyDataError) as e:
            ib_api_logger.error(
                "%s encountered a Pandas error while parsing historical data. ReqId: %s, Error: %s",
                self.__class__.__name__,
                reqId,
                e,
            )

        except (KeyError, ValueError) as e:
            ib_api_logger.error(
                "%s encountered an error while processing historical data. ReqId: %s, Error: %s",
                self.__class__.__name__,
                reqId,
                e,
            )

        except HistoricalDataMissingException as e:
            ib_api_logger.error(
                "%s encountered an error while processing historical data. ReqId: %s, Error: %s",
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
        super().historicalDataEnd(reqId, start, end)
        try:
            ib_api_logger.debug(
                "%s received historical data end signal. ReqId: %s, Start: %s, End: %s",
                self.__class__.__name__,
                reqId,
                start,
                end,
            )
            if (
                reqId not in self._market_memory.historical_data
                or self._market_memory.historical_data[reqId].empty
            ):
                if (
                    reqId in self._market_memory.temp_hist_data
                    and self._market_memory.temp_hist_data[reqId]
                ):
                    new_data_frame = pd.DataFrame(
                        self._market_memory.temp_hist_data[reqId]
                    )
                    self._market_memory.historical_data[reqId] = new_data_frame
                    del self._market_memory.temp_hist_data[reqId]
            if "date" in self._market_memory.historical_data[reqId].columns:
                ib_api_logger.debug(
                    "%s is sorting historical data to by date. ReqId: %s, Data: %s",
                    self.__class__.__name__,
                    reqId,
                    self._market_memory.historical_data,
                )
                self._market_memory.historical_data[reqId].set_index(
                    "date", inplace=True
                )
                self._market_memory.historical_data[reqId].index = pd.to_datetime(
                    self._market_memory.historical_data[reqId].index, unit="s"
                )
                self._market_memory.historical_data[reqId].sort_index(inplace=True)
            else:
                ib_api_logger.error(
                    "Date column missing in historical data DataFrame for ReqId: %s",
                    reqId,
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
        self._current_ticker = contract.symbol
        self._bar_size = bar_size
        self._increment_req_id()
        ib_api_logger.debug(
            "%s is requesting historical data from IB for %s with end_datetime %s, duration %s, bar_size %s, use_rth %s",
            self.__class__.__name__,
            contract.symbol,
            end_datetime,
            duration,
            bar_size,
            use_rth,
        )
        try:
            self.reqHistoricalData(
                reqId=self._req_id,
                contract=contract,
                endDateTime=end_datetime,
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow="TRADES",
                useRTH=use_rth,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=None,
            )
            print("completed historical data request")
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
            self._market_memory.historical_data[reqId] = (
                self._market_memory.historical_data[reqId].append(
                    new_row, ignore_index=True
                )
            )

        except (pd.errors.ParserError, pd.errors.EmptyDataError) as e:
            ib_api_logger.error(
                "%s encountered a Pandas error while parsing historical data. ReqId: %s, Error: %s",
                self.__class__.__name__,
                reqId,
                e,
            )
        except (KeyError, ValueError) as e:
            ib_api_logger.error(
                "%s encountered an error while processing historical data. ReqId: %s, Error: %s",
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

    def _increment_req_id(self) -> None:
        """
        Increment the request ID.
        """
        self._req_id += 1

    @property
    def get_req_id(self) -> int:
        """
        Property getter for the current request ID.
        """
        return self._req_id

    @property
    def current_ticker(self) -> str:
        """
        Get the current ticker.
        :return: The current ticker.
        """
        return self._current_ticker
