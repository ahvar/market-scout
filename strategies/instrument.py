"""
Types of financial products
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class FinancialInstrument(ABC):
    """Abstract base class for financial instruments."""

    name: str

    @abstractmethod
    def calculate_value(self):
        """Calculate the value of the financial instrument."""
        pass


@dataclass
class FuturesContract(FinancialInstrument):
    """Class representing a futures contract."""

    symbol: str
    expiration_date: str
    contract_size: int
    price: float

    def calculate_value(self):
        """Calculate the value of the futures contract."""
        return self.price * self.contract_size


@dataclass
class Index(FinancialInstrument):
    """Class representing an index."""

    constituents: list

    def calculate_value(self):
        """Calculate the value of the index."""
        total_value = 0
        for instrument in self.constituents:
            total_value += instrument.calculate_value()
        return total_value


@dataclass
class Asset(FinancialInstrument):
    """Class representing an asset."""

    symbol: str
    quantity: int
    price: float

    def calculate_value(self):
        """Calculate the value of the asset."""
        return self.quantity * self.price
