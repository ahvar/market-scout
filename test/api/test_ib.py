"""
Tests for IBApi
"""

import unittest
from unittest.mock import patch
from ibapi.contract import Contract
from src.api.ib import IBApi
from datetime import datetime, timedelta


class TestIBApi(unittest.TestCase):
    """
    Unit tests for IBApi
    """

    @patch("src.api.ib_api.IBApi.connect")
    @patch("src.api.ib_api.IBApi.disconnect")
    @patch("src.api.ib_api.IBApi.run")
    def setUp(self, mock_run, mock_disconnect, mock_connect):
        """
        Set up the IBApi instance and mocks before each test.
        :params mock_run: Mock the IBApi.run() method
        :params mock_disconnect: Mock the IBApi.disconnect() method
        :params mock_connect: Mock the IBApi.connect() method
        """
        self.ib_api = IBApi(host="127.0.0.1", port=4002, client_id=0)
        # Mock the connect and run methods so no actual connection is attempted.
        self.ib_api.connect = mock_connect
        self.ib_api.run = mock_run
        self.ib_api.disconnect = mock_disconnect
        self.ib_api.connect_to_ib()

    def tearDown(self) -> None:
        """
        Tear down the IBApi instance after each test.
        """
        self.ib_api._disconnect_from_ib()

    @patch("src.api.ib.IBApi.connect")
    def test_connect_to_ib(self, mock_connect):
        """
        Test connecting to IB
        :params mock_connect: Mock the IBApi.connect() method
        """
        self.ib_api.connect_to_ib()
        mock_connect.assert_called_with("127.0.0.1", 4002, 0)

    @patch("src.api.ib_api.IBApi.disconnect")
    def test_disconnect_from_ib(self, mock_disconnect):
        """
        Test the IBApi disconnect_from_ib method.
        :params mock_disconnect: Mock the IBApi.disconnect() method
        """
        self.ib_api._disconnect_from_ib()
        mock_disconnect.assert_called_once()

    @patch("src.api.ib_api.IBApi.reqHistoricalData")
    def test_request_historical_data(self, mock_req_historical_data):
        """
        Test the IBApi request_historical_data method.
        :params mock_req_historical_data: Mock the IBApi.reqHistoricalData() method
        """
        contract = Contract()
        contract.symbol = "AAPL"
        self.ib_api.request_historical_data(
            contract, "20220810 12:30:00", "1 D", "1 hour", 1
        )
        self.assertTrue(mock_req_historical_data.called)

    def test_error(self):
        """
        Test handling errors
        """
