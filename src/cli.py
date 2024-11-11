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

from dotenv import load_dotenv
import logging
import typer
from pprint import PrettyPrinter
from typing import Optional
from typing_extensions import Annotated
from rich import print
from rich.console import Console
from src.cli_app import cli_app
from src.strategies.momentum import momentum_strategy

__copyright__ = "Copyright \xa9 2023 Arthur Vargas | ahvargas92@gmail.com"

logger = logging.getLogger(IB_API_LOGGER_NAME)
load_dotenv()
