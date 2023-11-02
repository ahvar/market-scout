#!/usr/bin/env python3

"""
Classes for interacting with the IB API.
"""

import pandas as pd
import threading
import atexit
import logging
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from src.utils.logging_utils import LoggingUtils
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
    """

    def __init__(self, host: str, port: int, client_id: int):
        """
        Initialize the IBApi instance.
        :param host: The hostname or IP address of the machine on which the TWS or IB Gateway is running.
        :param port: The port on which the TWS or IB Gateway is listening.
        :param client_id: A unique identifier for the client application.
        """
        ib_api_logger.debug(f"Initializing {self.__class__.__name__} instance")
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self._host = host
        self._port = port
        self._client_id = client_id
        self._connection_thread = None
        self._request_counter = 0
        self._request_lock = threading.Lock()
        atexit.register(self._disconnect_from_ib)
        ib_api_logger.debug(
            f"{self.__class__.__name__} instance initialized.\nHost: {self._host}\nPort: {self._port}\nClient_Id: {self._client_id}"
        )

    def _run_connection_thread(self) -> None:
        """
        Run the connection thread to keep the IB connection alive. To do this we call the IBApi.run() method
        of the EClient class, which is a blocking call. To avoid blocking the main thread, we run it in a
        separate thread. To manage the thread, we use the threading module.
        """
        self.run()

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
                f"{self.__class__.__name__} is connecting to IB with host {self._host}, port {self._port}, and client_id {self._client_id}"
            )
            try:
                self.connect(self._host, self._port, self._client_id)
                self._connection_thread = threading.Thread(
                    target=self._run_connection_thread
                )
                self._connection_thread.start()
            except Exception as e:
                ib_api_logger.error(
                    f"{self.__class__.__name__} encountered an error while connecting to IB: {e}"
                )
                raise IBApiConnectionException(
                    f"An error occurred while connecting to IB"
                ) from e
        else:
            ib_api_logger.debug(
                f"{self.__class__.__name__} is already connected to IB"
            )

    def _disconnect_from_ib(self) -> None:
        """
        Disconnect from the IB Gateway or TWS.
        """
        if self.isConnected():
            try:
                self.disconnect()
                if self._connection_thread:
                    self._connection_thread.join()  # Wait for the thread to complete
                    self._connection_thread = None
            except Exception as e:
                ib_api_logger.error(
                    f"{self.__class__.__name__} encountered an error while disconnecting from IB: {e}"
                )
                raise IBApiConnectionException(
                    f"An error occurred while disconnecting from IB"
                ) from e
        else:
            ib_api_logger.debug(
                f"{self.__class__.__name__} is already disconnected from IB"
            )
        
    def historicalData(self, reqId: int, bar):
        # `bar` contains the historical data information for that bar.
        # You can access bar's attributes to get the data:
        date = bar.date
        open_ = bar.open
        high = bar.high
        low = bar.low
        close = bar.close
        volume = bar.volume
    
        # You can now process/store this data as needed.
        # For example, you could append it to a list or store it in a database.

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        # This indicates the end of historical data transmission for the request with id `reqId`
        # You can now finalize the processing for this data set, e.g., writing to a file or sending a signal that data is ready.
        pass

    def error(self, reqId: int, errorCode: int, errorString: str):
        """
        This method is called when an error occurs.
        
        :param reqId: The request ID that this error is associated with. If the error isn't associated with a request, reqId will be -1.
        :param errorCode: The error code.
        :param errorString: A description of the error.
        """
        # Log or print the error
        ib_api_logger.error(f"Error. ReqId: {reqId}, Code: {errorCode}, Msg: {errorString}")
        
        # Depending on the nature of your application, you might also:
        # - Raise exceptions for certain error codes.
        # - Attempt to retry the request for certain


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
            f"{self.__class__.__name__} is requesting historical data from IB for {contract.symbol} with end_datetime {end_datetime}, duration {duration}, bar_size {bar_size}, use_rth {use_rth}, and req_id {req_id}"
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
                f"{self.__class__.__name__} encountered an error while requesting historical data from IB: {e}"
            )
            raise IBApiDataRequestException(
                f"An error occurred while requesting data from IB"
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
        

