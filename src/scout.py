#!/usr/bin/env python3
"""
Script file intended for executable invocation

scout (main)
"""

import typer
from rich import print as rprint
from src.utils.cli import version_callback, __version__, __Application__
from src.app import app


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show software version",
    ),
):
    message = f"""
    [bold]------------------------------------------------------------------------------------------------[\bold]
    [bold blue]{__Application__.replace("_", " ").upper()} {__version__} [\bold blue]
    [bold yellow]A query tool for equity market data [\bold yellow]
    [bold]------------------------------------------------------------------------------------------------[\bold]

    [green]
    A comprehensive command-line companion for navigating the financial markets. Interact with your brokerage account, 
    access real-time and historical market data, analyze trends, and manage your investment portfolio.

    For more detailed guidance on a command, you can type 'scout COMMAND --help'. For example, 'scout analyze --help' will display detailed information about the analyze command.
    """
    if ctx.invoked_subcommand is None:
        rprint(message)
        raise typer.Exit()


if __name__ == "__main__":
    app()
