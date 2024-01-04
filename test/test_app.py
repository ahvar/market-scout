import unittest
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

    def test_historical_quote_valid(self):
        """
        Test the 'quote' command.
        """
        # Assuming the quote command returns or prints something, you can check the outcome here.
        result = self.runner.invoke(
            app,
            [
                "historical-quote",
                "appl",
                "-b",
                "1 hour",
                "-d",
                "1 D",
                "-ed",
                "3 D",
                "-et",
                "12:00:00",
            ],
        )
        self.assertEqual(result.exit_code, 0)
