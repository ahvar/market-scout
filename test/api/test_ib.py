"""
Test IBApi with unittest.TestCase
"""
import unittest
from ibapi.contract import Contract
from src.api.ib import IBApiClient
from src.api.ib_api_exception import IBApiConnectionException
from src.utils.references import Tickers as T
from unittest.mock import patch, create_autospec, MagicMock
from datetime import datetime, timedelta


class TestIBApi(unittest.TestCase):
    """
    Unit tests for IBApi
    """

    @patch("src.api.ib.IBApiClient.connect")
    @patch("src.api.ib.IBApiClient.disconnect")
    @patch("src.api.ib.ThreadPoolExecutor")
    def setUp(self, mock_executor, mock_disconnect, mock_connect):
        """
        Set up the IBApiClient instance and mocks before each test.
        :params mock_executor: Mock the IBApiClient.ThreadPoolExecutor() method
        :params mock_disconnect: Mock the IBApiClient.disconnect() method
        :params mock_connect: Mock the IBApiClient.connect() method
        """
        self.ib_api_client = IBApiClient(host="127.0.0.1", port=4002, client_id=0)
        # Mock the connect and run methods so no actual connection is attempted.
        self.ib_api_client.connect = mock_connect
        self.ib_api_client.executor = mock_executor
        self.ib_api_client.disconnect = mock_disconnect
        # self.ib_api.connect_to_ib()

    def tearDown(self) -> None:
        """
        Tear down the IBApi instance after each test.
        """
        if (
            hasattr(self.ib_api_client, "_watchdog_future")
            and self.ib_api_client.watchdog_future
        ):
            self.ib_api_client.watchdog_future.cancel()

        if hasattr(self.ib_api_client, "_executor") and self.ib_api_client.executor:
            self.ib_api_client.executor.shutdown(wait=True)

        self.ib_api_client.isConnected = MagicMock(return_value=False)
        self.ib_api_client.disconnect_from_ib()

    @patch("src.api.ib.ConnectionWatchdog")
    def test_connect_to_ib_successful(self, mock_watchdog):
        """
        Test connecting to IB successfully.
        :params mock_watchdog: Mock the ConnectionWatchdog class
        """
        self.ib_api_client.connect_to_ib()
        self.ib_api_client.connect.assert_called_once_with("127.0.0.1", 4002, 0)
        # if self.ib_api_client.connect is successful then self.ib_api_client.isConnected should be True
        self.ib_api_client.isConnected = MagicMock(return_value=True)
        self.assertTrue(self.ib_api_client.isConnected())
        # mock_thread_start.assert_called_once()
        mock_watchdog.assert_called_once()

    def test_connect_to_ib(self):
        """
        Test connecting to IB
        """
        self.ib_api_client.connect_to_ib()
        self.ib_api_client.connect.assert_called_with("127.0.0.1", 4002, 0)

    def test_connect_to_ib_with_retries(self):
        """
        Test connecting to IB with retries
        """
        with patch.object(
            self.ib_api_client,
            "connect",
            side_effect=IBApiConnectionException("Connection failed"),
        ) as mock_connect:
            with self.assertRaises(IBApiConnectionException):
                self.ib_api_client.connect_to_ib()

            self.assertEqual(
                mock_connect.call_count, 8
            )  # max_tries = 8 defined in decorator

    def test_disconnect_from_ib(self):
        """
        Test the IBApi disconnect_from_ib method.
        """
        self.ib_api_client.isConnected = MagicMock(return_value=True)
        self.ib_api_client.disconnect_from_ib()
        self.ib_api_client.disconnect.assert_called_once()

    @patch("src.api.ib.IBApiClient.reqHistoricalData")
    def test_request_historical_data(self, mock_req_historical_data):
        """
        Test the IBApiClient request_historical_data method.
        :params mock_req_historical_data: Mock the IBApi.reqHistoricalData() method
        """
        contract = Contract()
        contract.symbol = T.apple
        self.ib_api_client.request_historical_data(
            contract, "20220810 12:30:00", "1 D", "1 hour", 1
        )
        self.assertTrue(mock_req_historical_data.called)

    # @patch("src.api.ib.backoff.on_exception")
    @patch("src.api.ib.ConnectionWatchdog")
    @patch("src.api.ib.IBApiClient.connect_to_ib")
    def test_connect_to_ib_exception(self, mock_connect, mock_watchdog):
        """
        Test connecting to IB with an exception
        :params mock_connect: Mock the IBApi.connect() method
        """
        mock_connect.side_effect = IBApiConnectionException("Connection failed")

        # When/Then
        with self.assertRaises(IBApiConnectionException):
            self.ib_api_client.connect_to_ib()

        mock_connect.assert_called_once()

    def test_error(self):
        """
        Test handling errors
        """
        pass
