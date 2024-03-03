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
from src.api.ib_api_exception import (
    HistoricalDataMissingException,
    UnsupportedBarSizeException,
)
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
    def verify_bar(self, bar_data) -> dict:
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
            value = getattr(bar_data, bar_data_attrs_lower[field_name], None)
            if field_name == "date":
                if value is None:
                    last_known_date = self._retrieve_last_available(
                        field_name, bar_data
                    )
                    value = (
                        self._calculate_next_date(last_known_date, bar_size)
                        if last_known_date
                        else None
                    )
                elif isinstance(value, pd.Timestamp):
                    value = value.to_pydatetime()
            else:
                if value is None:
                    value = self._retrieve_last_available(field_name, bar_data)
            verified_bar[field_name] = value
        return verified_bar

    def _retrieve_last_available(self, field_name: str, bar_data: BarData) -> Any:
        """
        Retrieve the last available data for the given field.

        :params field_name: The name of the field for which to retrieve the last available data.
        :return last_available: The last available data for the given field.
        """
        utils_logger.debug(
            "%s found missing bar data, attempting to retrieve last available data for ReqId: %s, Bar: %s, Missing: %s",
            self.__class__.__name__,
            bar_data.reqId,
            bar_data,
            field_name,
        )
        last_available = None
        for reqId, data in reversed(list(self._temp_hist_data.items())):
            for bar_data in reversed(data):
                if bar_data[field_name] is not None:
                    last_available = bar_data[field_name]
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
        if last_date is None:
            return None
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
            raise UnsupportedBarSizeException(f"Unsupported bar size unit: {unit}")

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

    def _add_to_temp_hist_cache(self, reqId: int, verified_bar: dict) -> None:
        """
        Add bar data to the temporary historical data cache.
        :params        reqId: The request ID that this bar data is associated with.
        :params verified_bar: The bar data that was received.
        """
        self._temp_hist_data[reqId].append(verified_bar)
        self._temp_hist_data[reqId] = sorted(
            self._temp_hist_data[reqId], key=lambda x: x["date"]
        )

    def add_bulk_to_hist_cache(self, reqId: int) -> None:
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
