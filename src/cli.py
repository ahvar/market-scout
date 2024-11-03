"""
scout app
"""

from src.patch.patch_ibpy2 import generate_patch, apply_patch
from src.utils.references import (
    IB_API_LOGGER_NAME,
    bar_sizes,
    duration_units,
    report_types,
    get_duration_unit,
    get_bar_size,
    ARBITRARY_FORECAST_ANNUAL_RISK_TARGET_PERCENTAGE,
    ARBITRARY_VALUE_OF_PRICE_POINT,
    ARBITRARY_FORECAST_CAPITAL,
    original_dispatcher_file,
    modified_dispatcher_file,
    dispatcher_patch_file,
    ibpy2_dispatcher_filepath,
    ibpy2_init_filepath,
    ibpy2_original_init_file,
    ibpy2_modified_init_file,
    ibpy2_init_patch_file,
    ibpy2_modified_overloading_file,
    ibpy2_original_overloading_file,
    ibpy2_overloading_patch_file,
    ibpy2_overloading_filepath,
    ibpy2_eclient_socket_filepath,
    ibpy2_original_eclient_socket,
    ibpy2_modified_eclient_socket,
    ibpy2_eclient_socket_patch,
    ibpy2_ereader_filepath,
    ibpy2_original_ereader,
    ibpy2_modified_ereader,
    ibpy2_ereader_patch,
    ibpy2_original_message,
    ibpy2_modified_message,
    ibpy2_message_patch,
    ibpy2_message_filepath,
)

print("patching IbPy2 __init__.py ...")
generate_patch(
    original=ibpy2_original_init_file,
    corrected=ibpy2_modified_init_file,
    patch=ibpy2_init_patch_file,
)
apply_patch(target=ibpy2_init_filepath, patch_content=ibpy2_init_patch_file)
print("patching IbPy2 dispatcher.py ...")
generate_patch(
    original=original_dispatcher_file,
    corrected=modified_dispatcher_file,
    patch=dispatcher_patch_file,
)
apply_patch(target=ibpy2_dispatcher_filepath, patch_content=dispatcher_patch_file)
print("patching IbPy2 overloading.py ...")
generate_patch(
    original=ibpy2_original_overloading_file,
    corrected=ibpy2_modified_overloading_file,
    patch=ibpy2_overloading_patch_file,
)
apply_patch(
    target=ibpy2_overloading_filepath, patch_content=ibpy2_overloading_patch_file
)
print("patching IbPy2 EClientSocket.py ...")
generate_patch(
    original=ibpy2_original_eclient_socket,
    corrected=ibpy2_modified_eclient_socket,
    patch=ibpy2_eclient_socket_patch,
)
apply_patch(
    target=ibpy2_eclient_socket_filepath, patch_content=ibpy2_eclient_socket_patch
)

print("patching IbPy2 EReader.py ...")
generate_patch(
    original=ibpy2_original_ereader,
    corrected=ibpy2_modified_ereader,
    patch=ibpy2_ereader_patch,
)
apply_patch(target=ibpy2_ereader_filepath, patch_content=ibpy2_ereader_patch)

print("patching IbPy2 message.py ...")
generate_patch(
    original=ibpy2_original_message,
    corrected=ibpy2_modified_message,
    patch=ibpy2_message_patch,
)
apply_patch(target=ibpy2_message_filepath, patch_content=ibpy2_message_patch)

from datetime import datetime
from dotenv import load_dotenv
import logging
import time
import typer
import random
import pprint
import backtrader as bt
import pandas as pd
from pprint import PrettyPrinter
from typing import Optional
from typing_extensions import Annotated
from rich import print
from rich.console import Console
from rich.table import Table
from pathlib import Path
from ib_async import IB, client, contract, util
from ib_async.contract import Forex, Contract
from openai import OpenAI
from src.utils.command.command_callbacks import (
    validate_end_date,
    validate_duration,
    validate_bar_size,
    validate_end_time,
    validate_out_dir,
    validate_report_type,
)
from src.utils.command.command_utils import (
    init_logging,
    set_error_and_exit,
    convert_to_utc,
    make_dirs_and_write,
)
from src.broker.broker import retrieve_historical_data
from src.accounts.accounts_forecast import (
    get_normalised_forecast,
    get_average_notional_position,
    get_notional_position_for_forecast,
)
from src.accounts.curve import AccountCurve
from src.models.starter import Starter
from src.models.vol import robust_daily_vol_given_price
from src.accounts.profit_and_loss import ProfitAndLossWithSharpeRatioCosts
from trading_rule import calc_ewmac_forecast
from src.utils.references import (
    IB_API_LOGGER_NAME,
    bar_sizes,
    duration_units,
    report_types,
    get_duration_unit,
    get_bar_size,
    get_ticker,
    Frequency,
    NET_CURVE,
)

__copyright__ = "Copyright \xa9 2023 Arthur Vargas | ahvargas92@gmail.com"

logger = logging.getLogger(IB_API_LOGGER_NAME)
cli_app = typer.Typer()
load_dotenv()


@cli_app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def simple_strategy(
    ctx: typer.Context,
    ticker: Annotated[
        Optional[str],
        typer.Argument(default_factory=get_ticker, help="Ticker symbol for the stock"),
    ],
    bar_size: Annotated[
        Optional[str],
        typer.Argument(
            default_factory=get_bar_size, help="The bar size for the request"
        ),
    ],
    duration: Annotated[
        Optional[str],
        typer.Argument(
            default_factory=get_duration_unit,
            help="The duration for the request",
        ),
    ],
    end_date: Annotated[
        str,
        typer.Option(
            "-ed",
            "--end-date",
            callback=validate_end_date,
            help="The request's end date. Default is the current date. Valid formats: YYYY-MM-DD, YYYY/MM/DD",
        ),
    ] = None,
    end_time: Annotated[
        str,
        typer.Option(
            "-et",
            "--end-time",
            callback=validate_end_time,
            help="The request's end time in 24-hour clock. Default is the current time. Valid formats: HH:MM:SS",
        ),
    ] = None,
    outdir: Annotated[
        Path,
        typer.Option(
            "-o",
            "--outdir",
            callback=validate_out_dir,
            help="The name of the output file. Default is <ticker>.csv",
        ),
    ] = None,
    running_mode: Annotated[
        str,
        typer.Option(
            "-rm",
            "--running-mode",
            help="The running mode for the command. Valid modes: live, simulate",
        ),
    ] = None,
    debug: Annotated[
        bool,
        typer.Option(
            "-b",
            "--debug",
            help="Set log level to debug",
        ),
    ] = False,
):
    try:
        print("[bold red]Alert![/bold red] [green]Simple Strategy[/green]! :boom:")
        if not debug:
            for handler in logger.handlers:
                handler.setLevel(logging.INFO)
        print("[bold]Requesting price history from IB...[/bold]")
        prices = retrieve_historical_data(ticker, duration, bar_size, end_date)
        print("[bold]Calculating EWMAC Forecast...")
        forecast = calc_ewmac_forecast(prices["close"], 16, 64)
        daily_returns_volatility = robust_daily_vol_given_price(prices)
        normalized_forecast = get_normalised_forecast(
            forecast=forecast, target_abs_forecast=10
        )
        print("[bold]Calculating position size...")
        average_notional_position = get_average_notional_position(
            daily_returns_volatility=daily_returns_volatility,
            risk_target=ARBITRARY_FORECAST_ANNUAL_RISK_TARGET_PERCENTAGE,
            value_per_point=ARBITRARY_VALUE_OF_PRICE_POINT,
            capital=ARBITRARY_FORECAST_CAPITAL,
        )
        notional_position = get_notional_position_for_forecast(
            normalised_forecast=normalized_forecast,
            average_notional_position=average_notional_position,
        )
        make_dirs_and_write(
            outdir=outdir,
            ticker=ticker,
            prices=prices,
            forecast=forecast,
            notional_position=notional_position,
            duration=duration,
            bar_size=bar_size,
        )
        pandl_with_sr_costs = ProfitAndLossWithSharpeRatioCosts(
            price=prices,
            SR_cost=0.0,
            positions=notional_position,
            fx="USD",
            daily_returns_volatility=daily_returns_volatility,
            average_position=average_notional_position,
            capital=100000,
            value_per_point=1.0,
            delayfill=False,
        )
        as_pd_series = pandl_with_sr_costs.as_pd_series_for_frequency(
            frequency=Frequency.BDAY,
            percent=False,
            curve_type=NET_CURVE,
        )

        account_curve = AccountCurve(pandl_with_sr_costs)

    except Exception as e:
        logger.error("An error occurred: %s", e)
        raise Exception(e) from e
