"""
Custom exceptions for the IBApi class.
"""


class IBApiException(Exception):
    """
    Thrown by the IBApi class when there is a problem:
     - connecting to IB
     - disconnecting from IB
     - receiving data from IB
    """


class IBApiConnectionException(IBApiException):
    """
    Thrown when there is a problem connecting to IB
    """


class IBApiDataRequestException(IBApiException):
    """
    Thrown when there is a problem requesting data from IB
    """


class HistoricalDataMissingException(IBApiDataRequestException):
    """
    Thrown when requested historical data is partially or entirely missing
    """


class UnsupportedBarSizeException(IBApiDataRequestException):
    """
    Thrown when the requested bar size is not supported
    """
