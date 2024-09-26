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

from datetime import datetime
from dotenv import load_dotenv
import logging
import time
import typer
import random
import pprint
import backtrader as bt
from pprint import PrettyPrinter
from typing import Optional
from typing_extensions import Annotated
from rich import print
from rich.console import Console
from rich.table import Table
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
)
from src.broker.broker import IBAsyncBroker
from src.broker.ib_utils import IBMarketMemory
from src.models.starter import Starter
from src.models.ewmac import calc_ewmac_forecast
from src.utils.references import (
    IB_API_LOGGER_NAME,
    bar_sizes,
    duration_units,
    report_types,
    get_duration_unit,
    get_bar_size,
)

__copyright__ = "Copyright \xa9 2023 Arthur Vargas | ahvargas92@gmail.com"


logger = logging.getLogger(IB_API_LOGGER_NAME)
cli_app = typer.Typer()
load_dotenv()


@cli_app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def market_summary(
    ctx: typer.Context,
    ticker: str = typer.Argument(..., help="Ticker symbol for the stock"),
    duration: str = typer.Option(
        None,
        "-dr",
        "--duration",
        callback=validate_duration,
        help=f"The amount of time to go back from the end date and time. \
            Provide an integer and a valid duration unit. Valid units: {', '.join(f'{short} ({long})' for short, long in duration_units)}",
    ),
    end_date: str = typer.Option(
        None,
        "-ed",
        "--end-date",
        callback=validate_end_date,
        help="The request's end date. Default is the current date. Valid formats: YYYY-MM-DD, YYYY/MM/DD",
    ),
    out_dir: str = typer.Option(
        None,
        "-o",
        "--outdir",
        callback=validate_out_dir,
        help="The name of the output file. Default is <ticker>.csv",
    ),
    report_type: str = typer.Option(
        None,
        "-rt",
        "--report-type",
        callback=validate_report_type,
        help=f"The type of report to generate. Valid types: {', '.join(f'{report}' for report in report_types)}",
    ),
    debug: bool = typer.Option(
        False,
        "-b",
        "--debug",
        help="Set log level to debug",
    ),
):
    """
    This command tells Market Scout to get the market summary for a ticker within a given timeframe. The values passed to
    command options are used in requests to OpenAI API for GPT chat service.
    """
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair.",
            },
            {
                "role": "user",
                "content": "Compose a poem that explains the concept of recursion in programming.",
            },
        ],
    )

    print(completion.choices[0].message)


@cli_app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def trade(
    ctx: typer.Context,
    ticker: str = typer.Argument(..., help="Ticker symbol for the stock"),
    bar_size: str = typer.Option(
        None,
        "-br",
        "--bar-size",
        callback=validate_bar_size,
        help=f"Data granularity. Valid bars: {', '.join(bar_sizes)}",
    ),
    duration: str = typer.Option(
        None,
        "-dr",
        "--duration",
        callback=validate_duration,
        help=f"The amount of time to go back from the end date and time. \
            Provide an integer and a valid duration unit. Valid units: {', '.join(f'{short} ({long})' for short, long in duration_units)}",
    ),
    end_date: str = typer.Option(
        None,
        "-ed",
        "--end-date",
        callback=validate_end_date,
        help="The request's end date. Default is the current date. Valid formats: YYYY-MM-DD, YYYY/MM/DD",
    ),
    end_time: str = typer.Option(
        None,
        "-et",
        "--end-time",
        callback=validate_end_time,
        help="The request's end time in 24-hour clock. Default is the current time. Valid formats: HH:MM:SS",
    ),
    out_dir: str = typer.Option(
        None,
        "-o",
        "--outdir",
        callback=validate_out_dir,
        help="The name of the output file. Default is <ticker>.csv",
    ),
    running_mode: str = typer.Option(
        None,
        "-rm",
        "--running-mode",
        help="The running mode for the command. Valid modes: live, simulate",
    ),
    debug: bool = typer.Option(
        False,
        "-b",
        "--debug",
        help="Set log level to debug",
    ),
):
    """
    This command tells Market Scout to get the historical data for a ticker within a given timeframe.
    The values passed to command options are used directly in a call to the Interactive Brokers
    method IBPI.EClient.reqHistoricalData().
    """
    try:
        if not debug:
            for handler in logger.handlers:
                handler.setLevel(logging.INFO)
        ib = IB()
        cerebro = bt.Cerebro()
        ib.connect(host="127.0.0.1", port=4002, clientId=1, timeout=30)
        eurusd_contract = Forex("EURUSD")
        bars = ib.reqHistoricalData(
            eurusd_contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow="MIDPOINT",
            useRTH=True,
        )
        eurusd_data = util.df(bars)
        starter = Starter()
        cerebro.addstrategy(starter)
        data = bt.feeds.PandasData(dataname=eurusd_data)
        cerebro.adddata(data)
        ib.disconnect()

    except Exception as e:
        logger.error("An error occurred: %s", e)
        raise Exception(e) from e
    finally:
        logger.info("Market Scout has stopped.")


@cli_app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def simple_strategy(
    ctx: typer.Context,
    ticker: Annotated[str, typer.Argument(..., help="Ticker symbol for the stock")],
    bar_size: Annotated[Optional[str], typer.Argument(default_factory=get_bar_size)],
    duration: Annotated[
        Optional[str], typer.Argument(default_factory=get_duration_unit)
    ],
    end_date: Annotated[
        str,
        typer.Option(
            None,
            "-ed",
            "--end-date",
            callback=validate_end_date,
            help="The request's end date. Default is the current date. Valid formats: YYYY-MM-DD, YYYY/MM/DD",
        ),
    ],
    end_time: Annotated[
        str,
        typer.Option(
            None,
            "-et",
            "--end-time",
            callback=validate_end_time,
            help="The request's end time in 24-hour clock. Default is the current time. Valid formats: HH:MM:SS",
        ),
    ],
    out_dir: Annotated[
        str,
        typer.Option(
            None,
            "-o",
            "--outdir",
            callback=validate_out_dir,
            help="The name of the output file. Default is <ticker>.csv",
        ),
    ],
    running_mode: Annotated[
        str,
        typer.Option(
            None,
            "-rm",
            "--running-mode",
            help="The running mode for the command. Valid modes: live, simulate",
        ),
    ],
    debug: Annotated[
        bool,
        typer.Option(
            False,
            "-b",
            "--debug",
            help="Set log level to debug",
        ),
    ],
):
    """
    This command tells Market Scout to get the historical data for a ticker within a given timeframe.
    The values passed to command options are used directly in a call to the Interactive Brokers
    method IBPI.EClient.reqHistoricalData().
    """
    try:
        print("[bold red]Alert![/bold red] [green]Simple Strategy[/green]! :boom:")
        if not debug:
            for handler in logger.handlers:
                handler.setLevel(logging.INFO)
        print("[bold]Market Scout is starting...[/bold]")
        ib = IB()
        ib.connect(host="127.0.0.1", port=4002, clientId=1, timeout=30)
        eurusd_contract = Forex("EURUSD")
        bars = ib.reqHistoricalData(
            eurusd_contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow="MIDPOINT",
            useRTH=True,
        )
        eurusd_data = util.df(bars)
        table = Table(title="EURUSD Data")
        table.add_column("Date", style="cyan", no_wrap=True)
        table.add_column("Open", style="magenta")
        table.add_column("High", style="green")
        table.add_column("Low", style="red")
        table.add_column("Close", style="blue")
        table.add_column("Volume", style="yellow")
        for index, row in eurusd_data.iterrows():
            table.add_row(
                str(index),
                str(row["open"]),
                str(row["high"]),
                str(row["low"]),
                str(row["close"]),
                str(row["volume"]),
            )
        print(table)
        close_prices = eurusd_data["close"]
        forecast = calc_ewmac_forecast(close_prices, 16, 64)

    except Exception as e:
        logger.error("An error occurred: %s", e)
        raise Exception(e) from e
