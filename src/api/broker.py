"""
Classes for interacting with the IB API.
"""

# standard library
import logging

# third-party
import backtrader as bt
from ib_async.ib import IB
from ib_async.contract import Stock, Forex
from ib_async.order import LimitOrder, MarketOrder

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

from src.utils.references import IB_API_LOGGER_NAME

ib_api_logger = logging.getLogger(IB_API_LOGGER_NAME)


class IBAsyncBroker(bt.BrokerBase):
    """
    A class for interacting with the Interactive Brokers API asynchronously.
    """

    def __init__(self, host="127.0.0.1", port=4002, client_id=1):
        """
        Initialize the IBAsyncBroker instance.
        :param          host: The hostname or IP address of the machine on which the TWS or IB Gateway is running.
        :param          port: The port on which the TWS or IB Gateway is listening.
        :param     client_id: A unique identifier for the client application and used in communication with the TWS or IB Gateway.
        """
        super(IBAsyncBroker, self).__init__()
        ib_api_logger.info("Initializing %s instance", self.__class__.__name__)
        self._ib = IB()
        self._ib.connect(host=host, port=port, clientId=client_id)
        self._orders = {}
        # self._bar_size = ""
        # self._current_ticker = None
        # atexit.register(self._disconnect_from_broker_api)
        # Use % formatting instead of f-strings because f-strings are interpolated at runtime.
        # We save some performance overhead by not evaluating the f-string.
        ib_api_logger.info(
            "%s instance initialized. \nHost: %s\nPort: %s\nClient_ID: %s",
            self.__class__.__name__,
            host,
            port,
            client_id,
        )

    def start(self):
        super(IBAsyncBroker, self).start()

    def stop(self):
        self._ib.disconnect()
        super(IBAsyncBroker, self).stop()

    def getcash(self):
        pass

    def getvalue(self):
        pass

    def buy(self, owner, data, size, price=None, exectype=None, **kwargs):
        contract = Stock(data._name, "SMART", "USD")
        order = MarketOrder("BUY", size)
        self._ib.placeOrder(contract, order)
        self._orders[order.orderId] = order
        return order

    def sell(self, owner, data, size, price=None, exectype=None, **kwargs):
        contract = Stock(data._name, "SMART", "USD")
        order = MarketOrder("SELL", size)
        self._ib.placeOrder(contract, order)
        self._orders[order.orderId] = order
        return order

    def notify(self, order):
        pass

    async def get_positions(self):
        positions = await self._ib.reqPositions()
        return positions

    def add_order_history(self, order):
        # Implement the method to add order history
        pass

    def cancel(self, order):
        # Implement the method to cancel an order
        pass

    def getposition(self, data):
        # Implement the method to get the position for a given data
        pass

    def set_fund_history(self, fund):
        # Implement the method to set fund history
        pass

    def error(self, errorCode: int, errorString: str) -> None:
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
            # self.stop_services()
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
            # self.stop_services()
            # self.start_services()
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
            # ib_api_logger.error(
            #    "Error. ReqId: %s, Code: %s, Msg: %s", reqId, errorCode, errorString
            # )
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
