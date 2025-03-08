"""
Test classes for IB Api contracts and orders with unittest.TestCase
"""
import unittest
from ibapi.contract import Contract

import unittest
from ibapi.contract import Contract
from src.strategies.order import ContractFactory


class TestContractFactory(unittest.TestCase):
    """
    Unit tests for ContractFactory
    """

    def setUp(self):
        """
        Set up the ContractFactory instance before each test.
        """
        self.contract_factory = ContractFactory()

    def test_get_contract_creates_correct_contract(self):
        """
        Test that get_contract() creates the correct contract.
        """
        ticker = "AMZN"
        contract = self.contract_factory.get_contract(ticker)

        self.assertIsInstance(contract, Contract)
        self.assertEqual(contract.symbol, ticker)
        self.assertEqual(contract.secType, "STK")
        self.assertEqual(contract.exchange, "SMART")
        self.assertEqual(contract.currency, "USD")

    def test_contract_history_is_recorded(self):
        """
        Test that contract history is recorded correctly.
        """
        tickers = ["AMZN", "AAPL"]
        for ticker in tickers:
            self.contract_factory.get_contract(ticker)

        history = self.contract_factory.contract_history

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["ticker"], "AMZN")
        self.assertIsInstance(history[0]["contract"], Contract)
        self.assertEqual(history[1]["ticker"], "AAPL")
        self.assertIsInstance(history[1]["contract"], Contract)
