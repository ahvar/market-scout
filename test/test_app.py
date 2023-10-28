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

    def test_quote_command(self):
        """
        Test the 'quote' command.
        """
        # Assuming the quote command returns or prints something, you can check the outcome here.
        result = self.runner.invoke(
            app,
            [
                "quote",
                "appl",
                "-u",
                "minute",
                "-s",
                "2023-01-01T00:00",
                "-e",
                "2023-01-01T01:00",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    def test_quote_command_with_callbacks(self):
        """
        Test the 'quote' command with callbacks for start and end times validation.
        """
        start_time = "2023-01-01T00:00"
        end_time = "2023-01-01T01:00"
        result = self.runner.invoke(
            app,
            [
                "quote",
                "your_quote_argument",
                "-u",
                "minute",
                "-s",
                start_time,
                "-e",
                end_time,
            ],
        )

        # You should replace the following lines with checks relevant to what your callbacks do.
        # This is just an example assuming the callbacks might throw an error on invalid input.
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn(
            "Error:", result.stdout
        )  # Assuming an error would be printed with 'Error:' in the message.

        # Here you would add more test scenarios, especially edge cases, to make sure all code paths in your callbacks are being tested properly.


# The following is standard boilerplate to run the test case.
if __name__ == "__main__":
    unittest.main()
