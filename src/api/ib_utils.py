"""
Utility classes and functions for the IB API.
"""

# standard
import logging
import time
from typing import Any, Callable, Tuple, Optional
from datetime import datetime, timedelta, relativedelta
from dataclasses import fields
from collections import defaultdict
from abc import ABC, abstractmethod

# third-party
import pandas as pd
import numpy as np
from ibapi.common import BarData
from src.api.ib import IBApiClient
from src.utils.references import __Application__, __version__
from src.api.ib_api_exception import HistoricalDatatMissingException
from src.utils.references import IB_API_LOGGER_NAME, PriceBar

utils_logger = logging.getLogger(IB_API_LOGGER_NAME)


class ConnectionWatchdog:
    """
    A watchdog class that monitors the connection to the IB API and
    """

    def __init__(
        self,
        check_interval: int,
        start_services: Callable[[], None],
        stop_services: Callable[[], None],
        is_connected_method: Callable[[], bool],
    ):
        """
        Constructs the watchdog class.
        :params check_interval: The interval in seconds to check the connection.
        :params connect_method: The method to call to reconnect to the IB API.
        """
        utils_logger.info("Initializing %s instance", self.__class__.__name__)
        super().__init__()
        self._check_interval = check_interval  # seconds
        self._start_services = start_services
        self._stop_services = stop_services
        self._is_connected_method = (
            is_connected_method  # method to call to check if the connection is alive
        )
        self._running = None
        utils_logger.info("%s initialized", self.__class__.__name__)

    def monitor_connection(self):
        """
        Runs the watchdog thread.
        To make ConnectionWatchdog more responsive, there are multiple
        shorter sleeps in a loop, each time checking the _running flag.
        If _is_connected_method returns False, the watchdog will stop other
        threads and then restart them.
        """
        while self._running:
            if not self._is_connected_method():
                self._stop_services()
                utils_logger.debug("Connection lost. Reconnecting...")
                self._start_services()
            for _ in range(0, self._check_interval, 1):
                if not self._running:
                    break
                time.sleep(1)

    def stop_dog(self):
        """
        Stops the watchdog thread.
        """
        utils_logger.debug("Stopping %s instance", self.__class__.__name__)
        self._running = False

    def start_dog(self):
        """
        Starts the watchdog thread.
        """
        utils_logger.debug("Starting %s instance", self.__class__.__name__)
        self._running = True

    @property
    def running(self):
        """
        Returns the state of the watchdog thread.
        """
        return self._running


class MarketMemory(ABC):
    """
    This class handles all historical data
    """

    def __init__(self):
        """
        Initialize the market memory
        """
        super().__init__()
        utils_logger.info("Calling the constructor for %s", self.__class__.__name__)

    @abstractmethod
    def verify_bar(self, bar_data) -> None:
        """
        Verify the bar data
        """


class IBMarketMemory(MarketMemory):
    """
    Market memory for Interactive Brokers
    """

    def __init__(self):
        """
        Initialize the market memory
        """
        super().__init__()
        utils_logger.info("Initializing an instance of %s", self.__class__.__name__)
        self._temp_hist_data = defaultdict(list)
        self._missing_hist_data = {}
        self._historical_data = defaultdict(pd.DataFrame)

    def verify_bar(self, bar_data: BarData, bar_size: str) -> dict:
        """
        Verify the bar data and return the verified bar data.

        :params  bar_data: The bar data that was received.
        :return       bar: The verified bar data.
        """
        verified_bar = {}
        bar_data_attrs = dir(bar_data)
        bar_data_attrs_lower = {attr.lower(): attr for attr in bar_data_attrs}
        for field in fields(PriceBar):
            field_name = field.name.lower()
            if field_name in bar_data_attrs_lower:
                value = getattr(bar_data, bar_data_attrs_lower[field_name], None)
                if value is None and field_name != "date":
                    utils_logger.debug(
                        "%s found missing bar data. ReqId: %s, Bar: %s, Missing: %s",
                        self.__class__.__name__,
                        bar_data.reqId,
                        bar_data,
                        field_name,
                    )
                    value = self._retrieve_last_available(field_name)
                elif field_name == "date" and value is None:
                    utils_logger.debug(
                        "%s found missing bar data. ReqId: %s, Bar: %s, Missing: %s",
                        self.__class__.__name__,
                        bar_data.reqId,
                        bar_data,
                        field_name,
                    )
                    _, last_date = self._retrieve_last_available(field_name)
                    value = self._calculate_next_date(last_date, bar_size)
                elif field_name == "date" and isinstance(value, pd.Timestamp):
                    value = value.to_pydatetime()
                verified_bar[field_name] = value
        return verified_bar

    def _retrieve_last_available(self, field_name: str) -> Any:
        """
        Retrieve the last available data for the given field.

        :params field_name: The name of the field for which to retrieve the last available data.
        :return last_available: The last available data for the given field.
        """
        last_available = None
        utils_logger.debug(
            "%s is retrieving the last available data for the field %s",
            self.__class__.__name__,
            field_name,
        )
        for reqId, data in reversed(list(self._temp_hist_data.items())):
            for bar in reversed(data):
                if bar[field_name] is not None:
                    last_available = bar[field_name]
                    break
            if last_available is not None:
                break
        if last_available is None:
            for reqId, df in self._historical_data.items():
                if not df.empty and field_name in df.columns:
                    last_available = df[field_name].dropna().iloc[-1]
                    break
        return last_available

    def _calculate_next_date(self, last_date: datetime, bar_size: str) -> datetime:
        """
        Calculate the date of the next bar.
        :params last_date: The date of the last bar for this request.
        :params bar_size: The size of the bar for this request.
        :return next_date: The date of the next bar.
        """
        value, unit = self._parse_bar_size(bar_size)
        if unit == "second":
            return last_date + timedelta(seconds=value)
        elif unit == "minute":
            return last_date + timedelta(minutes=value)
        elif unit == "hour":
            return last_date + timedelta(hours=value)
        elif unit == "day":
            return last_date + timedelta(days=value)
        elif unit == "week":
            return last_date + timedelta(weeks=value)
        elif unit == "month":
            return last_date + relativedelta(months=value)
        else:
            raise ValueError(f"Unsupported bar size unit: {unit}")

    def _parse_bar_size(self, bar_size: str) -> Tuple[int, Optional[str]]:
        """
        Parse the current bar size string and return the quanity and time unit.
        :params bar_size: The size of the bar for this request.
        :return: A tuple containing the quantity and time unit.
        """
        utils_logger.debug(
            "Parsing bar size string %s for quantity and time unit", bar_size
        )
        parts = bar_size.split()
        if len(parts) != 2:
            return 0, None
        try:
            value = int(parts[0])
            unit = parts[1].lower()
            if unit.endswith("s"):
                unit = unit[:-1]
            return value, unit
        except ValueError:
            return 0, None

    def _get_new_data(
        self, reqId: int, bar: object, current_ticker: str, bar_size: str
    ) -> None:
        """
        Add a record for the missing bar data.

        :params reqId: The request ID that this bar data is associated with.
        :params   bar: The bar data that was received.
        :params current_ticker: The ticker for which the bar data was received.
        :params bar_size: The size of the bar for this request.
        """
        utils_logger.debug(
            "%s received historical data with all bar data missing. ReqId: %s, Bar: %s",
            self.__class__.__name__,
            reqId,
            bar,
        )
        utils_logger.debug(
            "%s will use the date from the last available bar to determine the correct date for this missing bar.",
            self.__class__.__name__,
        )
        last_available_date = None
        if self._temp_hist_data[reqId]:
            last_available_date = self.get_last_available_date(
                reqId, use_temp_data=True
            )
        elif reqId in self._historical_data:
            last_available_date = self.get_last_available_date(
                reqId, use_temp_data=False
            )
        if not last_available_date:
            raise HistoricalDatatMissingException(
                f"{self.__class__.__name__} could not find the date for the last available bar from the temporary historical data cache or historical data cache"
            )
        return {
            PriceBar.ticker: current_ticker,
            PriceBar.date: self.compute_missing_date(
                last_available_date, reqId, bar_size
            ),
            PriceBar.open: np.NAN,
            PriceBar.high: np.NAN,
            PriceBar.low: np.NAN,
            PriceBar.close: np.NAN,
            PriceBar.volume: np.NAN,
            PriceBar.data_partially_missing: True,
        }

    def get_last_available_date(self, reqId: int, use_temp_data: bool) -> datetime:
        """
        Check temporary historical data cache and historical data cache for the last available date.

        :params                  reqId: The request ID that this bar data is associated with.
        :params          use_temp_data: A boolean flag to indicate whether to use the temporary historical data cache or the historical data cache.
        :return    last_available_date: datetime representation of the date from the last available bar in the specified cache.
        """
        data_cache = self._temp_hist_data if use_temp_data else self._historical_data
        index = len(data_cache[reqId]) - 1

        while index >= 0:
            last_available_date = data_cache[reqId][index].get(PriceBar.date)
            if last_available_date:
                utils_logger.debug(
                    "%s got the date for the last available bar from the %s data cache to be %s",
                    self.__class__.__name__,
                    "temporary historical" if use_temp_data else "historical",
                    last_available_date.strftime("%Y-%m-%d %H:%M:%S"),
                )
                return last_available_date
            index -= 1
        return None

    def compute_missing_date(
        self, last_available_date: datetime, reqId: int, bar_size: str
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
        :params                  bar_size: The size of the bar for this request.
        :return   datetime_of_missing_bar: datetime representation of the date of the next bar.
        """
        try:
            bar_size_int = int(bar_size.split()[0])
            bar_size_unit = bar_size.split()[1]
            if bar_size_unit[-1] != "s":
                bar_size_unit += "s"
            time_delta = timedelta(**{bar_size_unit.lower(): bar_size_int})
            datetime_of_missing_bar = last_available_date + time_delta
            return datetime_of_missing_bar
        except Exception as e:
            raise HistoricalDatatMissingException(
                f"{self.__class__.__name__} encountered an error while computing the date of the missing bar. ReqId: {reqId}, Error: {e}"
            ) from e

    def _add_to_temp_hist_cache(self, reqId: int, bar_data: dict) -> None:
        """
        Add bar data to the temporary historical data cache.
        :params reqId: The request ID that this bar data is associated with.
        :params bar_data: The bar data that was received.
        """
        self._temp_hist_data[reqId].append(bar_data)
        self._temp_hist_data[reqId] = sorted(
            self._temp_hist_data[reqId], key=lambda x: x["date"]
        )

    def add_bulk_to_hist_cache(self, reqId: int) -> None:
        """
        Add historical data to the historical data and clear the temp hist data.

        :params reqId: The request ID that this bar data is associated with.
        """
        print("adding bulk to hist cache...")
        new_data_df = pd.DataFrame(self._temp_hist_data[reqId])
        # self._historical_data[reqId] = self._historical_data[reqId].dropna(
        #    how="all", axis=1
        # )
        self._historical_data[reqId] = pd.concat(
            [self._historical_data[reqId], new_data_df], ignore_index=True
        )
        self._temp_hist_data[reqId] = []

    def write_to_csv(self, out_dir: str) -> None:
        """
        Write the historical data to a CSV file.

        :params out_dir: The name of the output file.
        """
        if self._historical_data:
            for reqId, data in self._historical_data.items():
                data.to_csv(out_dir, index=False)
        elif self._temp_hist_data:
            for reqId, data in self._temp_hist_data.items():
                data.to_csv(out_dir, index=False)

    @property
    def historical_data(self):
        """
        Get the historical data
        """
        return self._historical_data

    @property
    def temp_hist_data(self) -> dict:
        """
        Get the temporary historical data cache.
        :return: The temporary historical data cache.
        """
        return self._temp_hist_data

    @property
    def missing_hist_data(self) -> dict:
        """
        Get the missing historical data cache.
        :return: The missing historical data cache.
        """
        return self._missing_hist_data
