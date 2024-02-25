import unittest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from src.app import app
from datetime import datetime


class TestCLI(unittest.TestCase):
    """
    Test command-line
    """

    def setUp(self):
        """
        Set up the test environment.
        """
        self.runner = CliRunner()

    @patch("src.app.logger")
    @patch("src.app.IBApiClient")
    @patch("src.app.IBMarketMemory")
    @patch("src.app.ContractFactory")
    @patch("src.app.time.sleep")
    def test_historical_quote_valid(
        self, mock_sleep, mock_contract_factory, mock_memory, mock_client, mock_logger
    ):
        """
        Test the 'quote' command.
        :param mock_sleep: mock time.sleep
        :param mock_contract_factory: mock ContractFactory
        :param mock_memory: mock IBMarketMemory
        :param mock_client: mock IBApiClient
        :param mock_logger: mock logger
        """
        result = self.runner.invoke(
            app,
            [
                "historical-quote",
                "appl",
                "-br",
                "1 hour",
                "-dr",
                "1 D",
                "-ed",
                "2023-12-12",
                "-et",
                "12:00:00",
                "-o",
                "appl.csv",
            ],
        )
        mock_contract_factory.assert_called()
        mock_memory.assert_called()
        mock_client.assert_called()
        self.assertEqual(result.exit_code, 0)
