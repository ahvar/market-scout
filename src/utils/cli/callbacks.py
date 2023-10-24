"""
Description
------------------------------------------------------------------------------
Command-line callback functions:
------------------------------------------------------------------------------
"""
import typer
from datetime import datetime, timedelta
from src.utils.cli.cli import parse_date, get_default_start_end_time
from src.utils.references import date_formats


def validate_start_time(ctx: typer.Context, start: str) -> str:
    """
    The start time
    :params  ctx: the typer context object
    :params start: the beginning of the target time period
    :return start: the beginning of the target time period
    """
    if start is None:
        # No start date provided, default to the first time unit of the current day
        start_time, _ = get_default_start_end_time(ctx.params["time_unit"])
        return start_time
    else:
        try:
            return parse_date(start, date_formats)
        except ValueError as e:
            raise typer.BadParameter(str(e))


def validate_end_time(ctx: typer.Context, end: str) -> str:
    """
    The end time
    :params  ctx: the typer context object
    :params end: the end of the target time period
    :return end: the end of the target time period
    """
    if end is None:
        # No end date provided, default to the last time unit of the current day
        _, end_time = get_default_start_end_time(ctx.params["time_unit"])
        return end_time
    else:
        try:
            return parse_date(end, date_formats)
        except ValueError as e:
            raise typer.BadParameter(str(e))


def validate_time_unit(ctx: typer.Context, unit: str) -> str:
    """
    A valid time measurement
    :params  ctx: the typer context object
    :params unit: the unit of time
    :return unit: a valid unit of time
    """
    valid_time_units = ["hour", "minute", "day", "week"]
    if unit not in valid_time_units:
        raise typer.BadParameter(
            f"Invalid time unit. Please choose from {valid_time_units}."
        )
    return unit
