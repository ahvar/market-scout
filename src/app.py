"""
scout app
"""

__version__ = "1.0.0"
__copyright__ = "Copyright \xa9 2023 Arthur Vargas | ahvargas92@gmail.com"
__Application__ = "MarketScout"

logger_name = f"{__Application__}_{__version__}_driver"

import typer
from src.utils.cli import init_logging

app = typer.Typer
