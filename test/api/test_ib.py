"""
Test IBApi with unittest.TestCase
"""

import os
import unittest
from ibapi.contract import Contract
from src.api.ib_api_exception import (
    IBApiConnectionException,
    HistoricalDatatMissingException,
)
from src.utils.references import Tickers as T
from unittest.mock import patch, create_autospec, MagicMock, call
from datetime import datetime, timedelta


class TestIBApiClient(unittest.TestCase):
    """
    Unit tests for IBApi
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Set up the IBApiClient instance before each test.
        """
        os.environ["TEST_MODE"] = "True"
        from src.api.ib import IBApiClient

        cls.IBApiClient = IBApiClient

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Tear down the IBApi instance after each test.
        """
        if "TEST_MODE" in os.environ:
            del os.environ["TEST_MODE"]

    @patch("src.api.ib.ib_api_logger")
    @patch("src.api.brokerage.client.ConnectionWatchdog")
    def setUp(self, mock_watchdog, mock_logger):
        """
        Set up the IBApiClient instance and mocks before each test.
        """
        self.mock_logger = mock_logger
        self.mock_watchdog = mock_watchdog
        self.ib_api_client = self.IBApiClient(host="127.0.0.1", port=4002, client_id=0)
        self.ib_api_client._verify_connection = MagicMock(return_value=True)
        self.mock_watchdog.return_value.monitor_connection = MagicMock()

    def tearDown(self) -> None:
        """
        Tear down the IBApi instance after each test.
        """
        # self.ib_api_client.stop_services()

    @patch("src.api.ib.IBApiClient._run_connection_thread")
    @patch("src.api.ib.IBApiClient._connect_to_broker_api")
    @patch("src.api.brokerage.client.ThreadPoolExecutor", autospec=True)
    def test_start_services_schedules_connection(
        self,
        mock_thread_pool_executor,
        mock_connect_to_broker_api,
        mock_run_connection_thread,
    ):
        """
        Test that start_services schedules the connection and watchdog threads.
        :param mock_thread_pool_executor:  Mock the ThreadPoolExecutor class
        :param mock_connect_to_broker_api: Mock the IBApiClient._connect_to_broker_api() method
        :param mock_run_connection_thread: Mock the IBApiClient._run_connection_thread() method
        """
        mock_executor_instance = mock_thread_pool_executor.return_value
        mock_executor_instance.submit.return_value = MagicMock()
        self.ib_api_client.start_services()

        mock_thread_pool_executor.assert_called_once()
        calls = [
            call(mock_connect_to_broker_api),
            call(mock_run_connection_thread),
            call(self.mock_watchdog.return_value.monitor_connection),
        ]
        mock_executor_instance.submit.assert_has_calls(calls)
        assert mock_executor_instance.submit.call_count == 3

    @patch("src.api.ib.IBApiClient._connect_to_broker_api")
    def test_start_services_eventual_connection_success(
        self, mock_connect_to_broker_api
    ):
        """
        Test that start_services eventually connects to the broker API.
        :param mock_connect_to_broker_api: Mock the IBApiClient._connect_to_broker_api() method
        """
        self.ib_api_client._verify_connection.side_effect = [False, False, True]
        self.ib_api_client.start_services()
        mock_connect_to_broker_api.assert_called()
        self.assertEqual(self.ib_api_client._verify_connection.call_count, 3)
        self.assertEqual(self.ib_api_client._count_attempts_to_verify, 0)

    @patch("src.api.ib.IBApiClient._connect_to_broker_api")
    def test_start_services_continuous_connection_failure(
        self, mock_connect_to_broker_api
    ):
        """
        Test that start_services attempts to connect but ultimately raises an exception
        after failing to verify the connection continuously up to the maximum retry limit.
        :param mock_connect_to_broker_api: Mock the IBApiClient._connect_to_broker_api() method
        """
        self.ib_api_client._verify_connection.return_value = False
        self.ib_api_client._max_attempts_to_verify = 3
        with self.assertRaises(IBApiConnectionException) as context:
            self.ib_api_client.start_services()
        self.assertIn(
            "Failed to establish a connection to the broker's API after 3 attempts",
            str(context.exception),
        )
        mock_connect_to_broker_api.assert_called_once()
        self.assertEqual(self.ib_api_client._verify_connection.call_count, 4)

    @patch("src.api.ib.IBApiClient._disconnect_from_broker_api")
    def test_stop_services_disconnection_failure(self, mock_disconnect_from_broker_api):
        """
        Test that stop_services attempts to disconnect but ultimately raises an exception
        :param mock_disconnect_from_broker_api: Mock the IBApiClient._disconnect_from_broker_api() method
        """
        self.ib_api_client._verify_connection.return_value = True
        self.ib_api_client._connection_future = MagicMock()
        self.ib_api_client._run_connection_future = MagicMock()
        self.mock_watchdog.return_value.stop_dog = MagicMock()
        self.ib_api_client._watchdog_future = MagicMock()
        self.ib_api_client._max_attempts_to_verify = 3
        with self.assertRaises(IBApiConnectionException) as context:
            self.ib_api_client.stop_services()
        self.ib_api_client._watchdog_future.cancel.assert_not_called()
        self.ib_api_client._connection_future.cancel.assert_not_called()
        self.ib_api_client._run_connection_future.cancel.assert_not_called()
        self.mock_watchdog.return_value.stop_dog.assert_not_called()

    @patch("src.api.ib.IBApiClient._disconnect_from_broker_api")
    def test_stop_services_eventual_disconnection_success(
        self, mock_disconnect_from_broker_api
    ):
        """
        Test that stop_services makes more than one attempt and successfully disconnects from the broker API.
        :param mock_disconnect_from_broker_api: Mock the IBApiClient._disconnect_from_broker_api() method
        """
        # Simulate a successful disconnection after 3 attempts
        self.ib_api_client._verify_connection.side_effect = [True, True, False]
        # We expect calls to cancel the futures and stop the watchdog
        self.ib_api_client._connection_future = MagicMock()
        self.ib_api_client._run_connection_future = MagicMock()
        self.mock_watchdog.return_value.stop_dog = MagicMock()
        self.ib_api_client._watchdog_future = MagicMock()
        self.ib_api_client._max_attempts_to_verify = 3
        # Call the method and assert
        self.ib_api_client.stop_services()
        self.ib_api_client._watchdog_future.cancel.assert_called()
        self.ib_api_client._connection_future.cancel.assert_called()
        self.ib_api_client._run_connection_future.cancel.assert_called()
        self.mock_watchdog.return_value.stop_dog.assert_called()

    @patch("src.api.ib.IBApiClient._connect_to_broker_api")
    def test_connect_to_ib_successful(self, mock_connect_to_broker_api):
        """
        Test connecting to IB successfully.
        :params mock_connect_to_broker_api: Mock the IBApiClient._connect_to_broker_api() method
        """
        self.ib_api_client.start_services()
        mock_connect_to_broker_api.assert_called()

    @patch("src.api.ib.IBApiClient.request_historical_data")
    def test_request_historical_data(self, mock_request_historical_data):
        """
        Test connecting to IB successfully.
        :params mock_request_historical_data: Mock the IBApiClient.request_historical_data() method
        """
        contract = Contract()
        contract.symbol = "AAPL"
        self.ib_api_client.request_historical_data(
            contract, "20220810 12:30:00", "1 D", "1 hour", 1
        )
        mock_request_historical_data.assert_called_with(
            contract, "20220810 12:30:00", "1 D", "1 hour", 1
        )

    def test_connect_to_ib_with_retries(self):
        """
        Test connecting to IB with retries
        """
        pass

    @patch("src.api.ib.IBApiClient._connect_to_broker_api")
    def test_connect_to_ib_exception(self, mock_connect_to_broker_api):
        """
        Test connecting to IB with an exception
        :params mock_connect: Mock the IBApi.connect() method
        """
        mock_connect_to_broker_api.side_effect = IBApiConnectionException(
            "Connection failed"
        )

        # When/Then
        with self.assertRaises(IBApiConnectionException):
            self.ib_api_client.start_services()

        mock_connect_to_broker_api.assert_called_once()

    def test_error(self):
        """
        Test handling errors
        """
        pass
