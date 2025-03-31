"""
Custom exceptions for SCOUT command-line
"""


class SomeGeneralCLIException(Exception):
    """
    docstring here
    """


class MissingData(Exception):
    pass


class SomeMoreSpecificCLIException(SomeGeneralCLIException):
    """
    docstring here
    """


class AnotherSpecificCLIException(SomeGeneralCLIException):
    """
    docstring here
    """


class missingData(Exception):
    pass
