date_formats = [
    "%Y/%m/%d",
    "%Y-%m-%d",
]

hour = "hour"
day = "day"
week = "week"
minute = "minute"

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

server_and_system_msgs = [
    tws_ib_gateway_config_error,
    tws_ib_gateway_not_running,
    order_router_down,
    mem_error,
    tws_ib_gateway_already_in_use,
    tws_ib_gateway_version_outdated,
    api_disconnection,
]
connection_disruptions = [
    connection_lost,
    connection_restored,
    connection_restored_data_retained,
    connection_rejected,
    tws_socket_reset,
]
mkt_data_farm_msgs = [
    mkt_data_farm_disconnected,
    mkt_data_farm_connected,
    mkt_data_farm_inactive,
    mkt_data_farm_disabled,
]

hist_data_farm_msgs = [
    hist_data_farm_disconnected,
    hist_data_farm_connected,
    hist_data_farm_inactive,
    hist_data_farm_disabled,
]
# IB API historical data pacing violation
pacing_violation = [162]
