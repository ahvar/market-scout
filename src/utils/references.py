import backoff
import random
import os
import pandas as pd
from dataclasses import dataclass
from pathlib import Path
from enum import Enum


project_root = Path(__file__).resolve().parent.parent.parent

# IbPy2 dispatcher.py patches
original_dispatcher_file = (
    project_root / "src" / "patch" / "ibpy2_original_dispatcher.py"
)
modified_dispatcher_file = (
    project_root / "src" / "patch" / "ibpy2_modified_dispatcher.py"
)
dispatcher_patch_file = project_root / "src" / "patch" / "ibpy2_dispatcher.patch"
ibpy2_dispatcher_filepath = (
    project_root
    / "envs"
    / "lib"
    / "python3.11"
    / "site-packages"
    / "ib"
    / "opt"
    / "dispatcher.py"
)

# IbPy2 __init__.py patches
ibpy2_original_init_file = project_root / "src" / "patch" / "ibpy2_original_init.py"
ibpy2_modified_init_file = project_root / "src" / "patch" / "ibpy2_modified_init.py"
ibpy2_init_patch_file = project_root / "src" / "patch" / "fix_syntax_error.patch"
ibpy2_init_filepath = (
    project_root
    / "envs"
    / "lib"
    / "python3.11"
    / "site-packages"
    / "ib"
    / "lib"
    / "__init__.py"
)

# IbPy2 overloading.py patches
ibpy2_original_overloading_file = (
    project_root / "src" / "patch" / "ibpy2_original_overloading.py"
)
ibpy2_modified_overloading_file = (
    project_root / "src" / "patch" / "ibpy2_modified_overloading.py"
)
ibpy2_overloading_patch_file = (
    project_root / "src" / "patch" / "ibpy2_overloading.patch"
)
ibpy2_overloading_filepath = (
    project_root
    / "envs"
    / "lib"
    / "python3.11"
    / "site-packages"
    / "ib"
    / "lib"
    / "overloading.py"
)

# IbPy2 EClientSocket.py patches
ibpy2_original_eclient_socket = (
    project_root / "src" / "patch" / "ibpy2_original_eclient_socket.py"
)
ibpy2_modified_eclient_socket = (
    project_root / "src" / "patch" / "ibpy2_modified_eclient_socket.py"
)
ibpy2_eclient_socket_patch = (
    project_root / "src" / "patch" / "ibpy2_eclient_socket.patch"
)
ibpy2_eclient_socket_filepath = (
    project_root
    / "envs"
    / "lib"
    / "python3.11"
    / "site-packages"
    / "ib"
    / "ext"
    / "EClientSocket.py"
)

# IbPy2 EReader.py patches
ibpy2_original_ereader = project_root / "src" / "patch" / "ibpy2_original_ereader.py"
ibpy2_modified_ereader = project_root / "src" / "patch" / "ibpy2_modified_ereader.py"
ibpy2_ereader_patch = project_root / "src" / "patch" / "ibpy2_ereader.patch"
ibpy2_ereader_filepath = (
    project_root
    / "envs"
    / "lib"
    / "python3.11"
    / "site-packages"
    / "ib"
    / "ext"
    / "EReader.py"
)
# IbPy2 message.py patches
ibpy2_original_message = project_root / "src" / "patch" / "ibpy2_original_message.py"
ibpy2_modified_message = project_root / "src" / "patch" / "ibpy2_modified_message.py"
ibpy2_message_patch = project_root / "src" / "patch" / "ibpy2_message.patch"
ibpy2_message_filepath = (
    project_root
    / "envs"
    / "lib"
    / "python3.11"
    / "site-packages"
    / "ib"
    / "opt"
    / "message.py"
)

is_test_mode = os.getenv("TEST_MODE", "False").lower() == "true"
BUSINESS_DAYS_IN_YEAR = 256.0
backoff_params = {
    "max_tries": 1 if is_test_mode else 8,
    "max_time": 300,
    "jitter": backoff.full_jitter,
}


def resample_prices_to_business_day_index(prices: pd.Series) -> pd.Series:
    return prices.resample("1B").last()


class DateTimeType(Enum):
    """
    Enum class for date and time
    """

    DATE = 1
    TIME = 2


date_formats = [
    "%Y/%m/%d",
    "%Y-%m-%d",
]

time_formats = ["%H:%M:%S"]

hour = "hour"
day = "day"
week = "week"
minute = "minute"

bar_sizes = [
    "1 hour",
    "2 hours",
    "3 hours",
    "4 hours",
    "8 hours",
    "1 secs",
    "5 secs",
    "10 secs",
    "15 secs",
    "30 secs",
    "1 min",
    "2 mins",
    "3 mins",
    "5 mins",
    "10 mins",
    "15 mins",
    "20 mins",
    "30 mins",
    "1 day",
    "1 week",
    "1 month",
]
duration_units = [("S", "Seconds"), ("D", "Days"), ("W", "Weeks"), ("M", "Months")]
report_types = ["ReportsFinStatements", "ReportsOwnership", "ReportsFinSummary"]
default_tickers = ["AAPL", "TSLA", "MSFT"]


def get_ticker() -> str:
    """
    Get a random ticker symbol
    """
    return random.choice(default_tickers)


def get_duration_unit() -> str:
    """
    Get a random duration quantity and unit
    """
    qty = 0
    unit = random.choice(duration_units)[0]
    if unit == "S":
        qty = random.randint(1, 604800)  # seconds in 1 week
    elif unit == "D":
        qty = random.randint(1, 365)  # days in 1 year
    elif unit == "W":
        qty = random.randint(1, 104)  # weeks in 2 years
    elif unit == "M":
        qty = random.randint(1, 24)  # months in 2 years
    else:
        raise ValueError(f"Invalid duration unit: {unit}")
    return f"{qty} {unit}"


def get_bar_size() -> str:
    """
    Get a random bar size
    """
    return random.choice(bar_sizes)


@dataclass
class PriceBar:
    """
    PriceBar dataclass
    """

    date: str = ""
    open: float = 0
    high: float = 0
    low: float = 0
    close: float = 0
    volume: int = 0


@dataclass
class Tickers:
    """
    Tickers dataclass
    """

    apple: str = "AAPL"
    tesla: str = "TSLA"
    microsoft: str = "MSFT"


# IB API error codes: https://interactivebrokers.github.io/tws-api/message_codes.html

connection_lost = 1100  # Connectivity between the TWS and the server is lost.
connection_restored = (
    1101  # Connectivity between the TWS and the server is restored - data lost.
)
connection_restored_data_retained = (
    1102  # Connectivity between the TWS and the server is restored - data maintained.
)
connection_rejected = 1103  # Connectivity between the TWS and the server is inactive.
tws_socket_reset = 1300  # TWS socket port has been reset and this connection is being dropped, please reconnect on the new port.
tws_ib_gateway_config_error = 502  # Couldn't connect to TWS. Confirm that "Enable ActiveX and Socket Clients" is enabled and connection parameters are correct. TWS should be running.
tws_ib_gateway_not_running = 504  # Not connected. Please confirm that TWS is running and the "Enable ActiveX and Socket Clients" checkbox is enabled.
order_router_down = 509  # Order router is offline.
unsubscribed_api_client = (
    511  # This API client has been unsubscribed from receiving data and orders.
)
mem_error = 512  # IB Gateway or TWS is out of memory. Please restart.
api_client_not_connected = 516  # API client not connected
tws_ib_gateway_already_in_use = 517  # TWS is already in use by another API client. TWS or IB Gateway only supports one API client at a time.
tws_ib_gateway_version_outdated = 518  # TWS is out of date and must be upgraded.
api_disconnection = 519  # API is disconnected (or connection is broken)
api_client_unsubscribed_from_time_sales_data = (
    520  # This API client has been unsubscribed from receiving time sales data.
)

ignore_outside_reg_trading_hrs = 2100  # Order Event Warning: Attribute "Outside Regular Trading Hours" is ignored based on the order type and destination. PlaceOrder is now being processed.
mkt_data_farm_disconnected = 2103  # A market data farm is disconnected.
mkt_data_farm_connected = 2104  # A market data farm is connected.
hist_data_farm_disconnected = 2105  # A historical data farm is disconnected.
hist_data_farm_connected = 2106  # A historical data farm is connected.
hist_data_farm_inactive = 2107  # A historical data farm connection has become inactive but should be available upon demand.
mkt_data_farm_inactive = 2108  # A market data farm connection is inactive but should be available upon demand.
hist_data_farm_disabled = 2109  # A historical data farm is permanently disconnected.
mkt_data_farm_disabled = 2110  # A market data farm is permanently disconnected.
sec_def_data_farm_ok = (
    2158  # The security definition market data farm connection is OK.
)

socket_drop = [
    tws_socket_reset,
]

tws_ib_gate_way_errors = [
    tws_ib_gateway_config_error,
    tws_ib_gateway_not_running,
    mem_error,
]

connection_broken = [
    connection_lost,
    connection_rejected,
    api_client_not_connected,
]
mkt_data_farm_msgs = [
    mkt_data_farm_disconnected,
    mkt_data_farm_connected,
    mkt_data_farm_inactive,
    mkt_data_farm_disabled,
    sec_def_data_farm_ok,
]

hist_data_farm_msgs = [
    hist_data_farm_disconnected,
    hist_data_farm_connected,
    hist_data_farm_inactive,
    hist_data_farm_disabled,
]
# IB API historical data pacing violation
pacing_violation = [162]

__Application__ = "MarketScout"
__version__ = "1.0.0"
IB_API_LOGGER_NAME = f"{__Application__}_{__version__}_driver"
