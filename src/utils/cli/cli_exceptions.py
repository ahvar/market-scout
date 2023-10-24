"""
Custom exceptions for SCOUT command-line
"""


class SomeGeneralCLIException(Exception):
    """
    docstring here
    """


class SomeMoreSpecificCLIException(SomeGeneralCLIException):
    """
    docstring here
    """


class AnotherSpecificCLIException(SomeGeneralCLIException):
    """
    docstring here
    """
