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
