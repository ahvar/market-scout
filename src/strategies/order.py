"""
Defines <tbd>
"""

import logging
from ibapi.contract import Contract
from src.utils.references import MKT_SCOUT_CLI

contract_logger = logging.getLogger(MKT_SCOUT_CLI)


class ContractFactory:
    """
    Factory class for creating contracts.
    """

    def __init__(self):
        """
        Constructs the factory.
        """
        contract_logger.debug("Initializing contract factory...")
        self._contract_history = []

    def get_contract(self, ticker: str) -> Contract:
        """
        Create and return a contract object for the given ticker symbol.
        :param ticker: The ticker symbol of the stock.
        :return: Contract object.
        """
        contract_logger.debug("Creating contract for %s", ticker)
        contract = Contract()
        contract.symbol = ticker.upper()
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract_logger.debug("Contract created: %s", contract)
        # Record the contract creation in history
        self._record_contract_history(ticker, contract)
        return contract

    def _record_contract_history(self, ticker: str, contract: Contract):
        """
        Records the contract creation history.
        :param ticker: The ticker symbol of the stock.
        :param contract: The created contract object.
        """
        contract_logger.debug("Recording contract history...")
        self.contract_history.append({"ticker": ticker, "contract": contract})

    @property
    def contract_history(self) -> list:
        """
        Returns the history of all contracts created by this factory.
        :return: List of contract creation records.
        """
        return self._contract_history

    @contract_history.setter
    def contract_history(self, contract_history: list):
        """
        Sets the history of all contracts created by this factory.
        :param contract_history: List of contract creation records.
        """
        self._contract_history = contract_history
