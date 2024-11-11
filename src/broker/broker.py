"""
Classes for interacting with the IB API.
"""

# standard library
import logging
import collections
import asyncio
from datetime import datetime
from enum import Enum

# third-party
import backtrader as bt
import pandas as pd
from backtrader.brokers.ibbroker import IBBroker
from ib_async.ib import IB, util
from ib_async.contract import Stock, Forex
from ib_async.order import LimitOrder, MarketOrder

from src.utils.command.command_utils import set_error_and_exit
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
from src.broker.ib_api_exception import (
    IBApiException,
    IBApiConnectionException,
    IBApiDataRequestException,
    HistoricalDataMissingException,
)

from src.utils.references import IB_API_LOGGER_NAME

ib_api_logger = logging.getLogger(IB_API_LOGGER_NAME)


def connect_ib(host: str, port: int, client_id: int) -> IB:
    """
    Connect to the Interactive Brokers API.
    :param host: The hostname or IP address of the machine on which the TWS or IB Gateway is running.
    :param port: The port on which the TWS or IB Gateway is listening.
    :param client_id: A unique identifier for the client application and used in communication with the TWS or IB Gateway.
    """
    ib_api_logger.info("Connecting to the Interactive Brokers API...")
    ib = IB()
    ib.connect(host=host, port=port, clientId=client_id)
    ib_api_logger.info(
        "Connected to the Interactive Brokers API. \nHost: %s\nPort: %s\nClient_ID: %s",
        host,
        port,
        client_id,
    )
    return ib


def retrieve_historical_data(
    symbol: str, duration: str, bar_size: str, end_date: datetime
) -> pd.DataFrame:
    """
    Retrieve historical data from the Interactive Brokers API.
    :param symbol: The symbol of the asset for which to retrieve historical data.
    :param duration: The duration of the historical data.
    :param bar_size: The size of the bars in the historical data.
    :param end_date: The end date of the historical data
    """
    ib = connect_ib(host="127.0.0.1", port=4002, client_id=1)
    stock_contract = Stock(symbol=symbol, exchange="SMART", currency="USD")
    bars = ib.reqHistoricalData(
        stock_contract,
        endDateTime=end_date,
        durationStr=duration,
        barSizeSetting=bar_size,
        whatToShow="MIDPOINT",
        useRTH=True,
    )
    stock_data = util.df(bars)
    stock_data["date"] = pd.to_datetime(stock_data["date"])
    stock_data.set_index("date", inplace=True)
    ib.disconnect()
    return stock_data


class IBAsyncBroker(IBBroker):
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
        super().__init__()
        ib_api_logger.info("Initializing %s instance", self.__class__.__name__)
        self._ib = IB()
        self._ib.connect(host=host, port=port, clientId=client_id)
        self._orders = {}
        self.notifs = collections.deque()  # Initialize the notifications deque
        ib_api_logger.info(
            "%s instance initialized. \nHost: %s\nPort: %s\nClient_ID: %s",
            self.__class__.__name__,
            host,
            port,
            client_id,
        )

    def start(self):
        super().start()

    def stop(self):
        self._ib.disconnect()
        super().stop()

    def get_notification(self):
        try:
            return self.notifs.popleft()
        except IndexError:
            pass

        return None

    """
    NOTE: Asynchronous vs. Synchronous
    -----------------------------------------
    Commenting buy() and sell() out for now because
    the IBBroker methods use _makeorder and submit,
    which might be synchronous and specific to the
    backtrader framework. In contrast, IBAsyncBroker
    directly interacts with the Interactive Brokers
    API asynchronously by calling _ib.placeOrder()
    directly.
    -----------------------------------------
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

    """

    def notify(self, order):
        pass

    def get_historical_data(
        self, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH
    ):
        bars = self._ib.reqHistoricalData(
            contract,
            endDateTime=endDateTime,
            durationStr=durationStr,
            barSizeSetting=barSizeSetting,
            whatToShow=whatToShow,
            useRTH=useRTH,
        )
        # Convert bars to a pandas DataFrame
        dataframe = pd.DataFrame([bar_data.__dict__ for bar_data in bars])
        dataframe.set_index("date", inplace=True)
        return dataframe

    async def get_positions(self):
        positions = await self._ib.reqPositions()
        return positions

    def add_order_history(self, order):
        # Implement the method to add order history
        pass

    def cancel(self, order):
        # Implement the method to cancel an order
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

    @property
    def ib(self):
        return self._ib


class OrderType(Enum):
    MARKET = "MKT"
    LIMIT = "LMT"
    STOP = "STP"


class OrderStatus(Enum):
    PENDING = "Pending"
    FILLED = "Filled"
    CANCELLED = "Cancelled"


class Order:
    def __init__(
        self,
        instrument: str,
        quantity: float,
        order_type: OrderType,
        price: float = None,
        timestamp: pd.Timestamp = None,
    ):
        self.instrument = instrument
        self.quantity = quantity
        self.order_type = order_type
        self.price = price  # Relevant for limit and stop orders
        self.status = OrderStatus.PENDING
        self.timestamp = timestamp if timestamp else pd.Timestamp.now()
        self.ib_order = None  # Will hold the IB API order object

    def __repr__(self):
        return (
            f"Order({self.instrument}, {self.quantity}, {self.order_type}, "
            f"Price={self.price}, Status={self.status}, Time={self.timestamp})"
        )


class ExecutionEngine:
    def __init__(self, ib_broker: IBAsyncBroker):
        self.ib_broker = ib_broker

    async def execute_order(self, order: Order):
        # Create IB contract
        contract = Stock(symbol=order.instrument, exchange="SMART", currency="USD")

        # Qualify the contract
        await self.ib_broker.ib.qualify_contract(contract)

        # Create IB order based on order type
        if order.order_type == OrderType.MARKET:
            ib_order = MarketOrder(
                action="BUY" if order.quantity > 0 else "SELL",
                total_quantity=abs(order.quantity),
            )
        elif order.order_type == OrderType.LIMIT:
            ib_order = LimitOrder(
                action="BUY" if order.quantity > 0 else "SELL",
                total_quantity=abs(order.quantity),
                limit_price=order.price,
            )
        elif order.order_type == OrderType.STOP:
            ib_order = StopOrder(
                action="BUY" if order.quantity > 0 else "SELL",
                total_quantity=abs(order.quantity),
                stop_price=order.price,
            )
        else:
            raise ValueError(f"Unsupported order type: {order.order_type}")

        # Place the order using IBAsyncBroker
        trade = await self.ib_broker.ib.place_order(contract, ib_order)
        order.ib_order = trade

        # Monitor the order status
        while True:
            await asyncio.sleep(1)  # Adjust as needed
            order_status = trade.order_status.status
            if order_status == IBOrderStatus.FILLED:
                order.status = OrderStatus.FILLED
                break
            elif order_status in [IBOrderStatus.CANCELLED, IBOrderStatus.INACTIVE]:
                order.status = OrderStatus.CANCELLED
                break
            # Continue waiting if order is still pending
        return order


class OrderManagementSystem:
    def __init__(self, execution_engine: ExecutionEngine):
        self.execution_engine = execution_engine
        self.orders = []
        self.positions = {}

    async def generate_order(
        self, signal: float, instrument: str, timestamp: pd.Timestamp
    ):
        # Determine desired position based on the signal
        desired_position = int(signal)  # Adjust as per your position sizing logic

        # Calculate the required order size
        current_position = self.positions.get(instrument, 0)
        order_size = desired_position - current_position

        if order_size == 0:
            return None

        order_type = OrderType.MARKET  # Using market orders
        order = Order(
            instrument=instrument,
            quantity=order_size,
            order_type=order_type,
            timestamp=timestamp,
        )
        self.orders.append(order)
        return order

    async def process_orders(self):
        pending_orders = [
            order for order in self.orders if order.status == OrderStatus.PENDING
        ]
        execution_tasks = [
            self.execution_engine.execute_order(order) for order in pending_orders
        ]
        if execution_tasks:
            await asyncio.gather(*execution_tasks)
            # Update positions after orders are filled
            for order in pending_orders:
                if order.status == OrderStatus.FILLED:
                    self.update_positions(order)

    def update_positions(self, order: Order):
        instrument = order.instrument
        self.positions[instrument] = self.positions.get(instrument, 0) + order.quantity

    def get_positions(self):
        return self.positions

    def get_open_orders(self):
        return [order for order in self.orders if order.status == OrderStatus.PENDING]

    def get_order_history(self):
        return self.orders
