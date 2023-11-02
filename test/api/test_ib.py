"""
Tests for IBApi
"""

import unittest
from src.api.ib import IBApi
from datetime import datetime, timedelta
from unittest.mock import patch


class TestIBApi(unittest.TestCase):
    """
    Unit tests for IBApi
    """
    @patch("src.api.ib.IBApi.connect")
    @patch("src.api.ib.IBApi.run")
    def test_connect_to_ib(self, mock_run, mock_connect):
        """
        Test connecting to IB
        :params mock_run: Mock the IBApi.run() method
        :params mock_connect: Mock the IBApi.connect() method
        """
        # Mock the IBApi.connect() method
        mock_connect.return_value = None

        # Mock the IBApi.run() method
        mock_run.return_value = None

        # Test that the connect() and run() methods are called
        ib_api = IBApi()
        ib_api.connect_to_ib()
        mock_connect.assert_called_once()
        mock_run.assert_called_once()

    @patch("src.api.ib.IBApi.disconnect")
    def test_disconnect_from_ib(self, mock_disconnect):
        """
        Test disconnecting from IB
        :params mock_disconnect: Mock the IBApi.disconnect() method
        """
        # Mock the IBApi.disconnect() method
        mock_disconnect.return_value = None

        # Test that the disconnect() method is called
        ib_api = IBApi()
        ib_api.disconnect_from_ib()
        mock_disconnect.assert_called_once()

    def test_error(self):
        """
        Test handling errors
        """