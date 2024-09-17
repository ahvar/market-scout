"""
Unit tests for the callbacks module.
"""

import unittest
import pytest
from datetime import datetime, timedelta, date
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer import BadParameter, Context
from command.command_callbacks import (
    validate_duration,
    validate_end_date,
    validate_bar_size,
    validate_out_dir,
)


class TestCallbacks(unittest.TestCase):
    """
    Test the callbacks module.
    """

    @patch("src.utils.cli.callbacks.logger")
    def test_validate_duration_with_valid_input(self, mock_logger):
        """
        Test the validate_duration callback with valid input.
        """
        assert validate_duration(None, "1 D") == "1 D"

    @patch("src.utils.cli.callbacks.logger")
    def test_validate_duration_with_invalid_unit(self, mock_logger):
        """
        Test the validate_duration callback with invalid input.
        """
        with pytest.raises(BadParameter):
            validate_duration(None, "1 X")

    @patch("src.utils.cli.callbacks.logger")
    def test_validate_duration_with_zero_duration(self, mock_logger):
        """
        Test the validate_duration callback with invalid input.
        """
        with pytest.raises(BadParameter):
            validate_duration(None, "0 D")

    @patch("src.utils.cli.callbacks.logger")
    def test_validate_duration_with_no_input(self, mock_logger):
        """
        Test the validate_duration callback with no input.
        """
        assert validate_duration(None, None) == "1 D"

    @patch("src.utils.cli.callbacks.logger")
    def test_validate_bar_size_with_valid_input(self, mock_logger):
        """
        Test the validate_bar_size callback with valid input.
        """
        assert validate_bar_size(None, "1 min") == "1 min"

    @patch("src.utils.cli.callbacks.logger")
    def test_validate_bar_size_with_invalid_input(self, mock_logger):
        """
        Test the validate_bar_size callback with invalid input.
        """
        with pytest.raises(BadParameter):
            validate_bar_size(None, "invalid_size")

    @patch("src.utils.cli.callbacks.logger")
    def test_validate_bar_size_with_no_input(self, mock_logger):
        """
        Test the validate_bar_size callback with no input.
        """
        assert validate_bar_size(None, None) == "1 min"

    @patch("src.utils.cli.callbacks.logger")
    def test_validate_end_date_with_valid_input(self, mock_logger):
        """
        Test the validate_end_date callback with valid input.
        """
        assert validate_end_date(None, "2023-01-01") == date(2023, 1, 1)

    @patch("src.utils.cli.callbacks.logger")
    def test_validate_end_date_with_invalid_input(self, mock_logger):
        """
        Test the validate_end_date callback with invalid input.
        """
        with pytest.raises(BadParameter):
            validate_end_date(None, "invalid_date")

    @patch("src.utils.cli.callbacks.logger")
    def test_validate_end_date_with_no_input(self, mock_logger):
        """
        Test the validate_end_date callback with no input.
        """
        # Replace with expected default end date
        day_before = datetime.now().date() - timedelta(days=1)
        assert validate_end_date(None, None) == day_before

    @patch("src.utils.cli.callbacks.Path")
    @patch("src.utils.cli.callbacks.Context")
    @patch("src.utils.cli.callbacks.logger")
    def test_validate_out_dir_with_valid_dir(self, mock_logger, mock_ctx, mock_path):
        """
        Test the validate_out_dir function with a valid directory.
        :param mock_ctx: the typer context object
        :param mock_path: the Path object
        """
        mock_path_obj = MagicMock()
        mock_path_obj.is_dir.return_value = True
        mock_path_obj.resolve.return_value = Path("/valid/directory").resolve()
        mock_path.return_value = mock_path_obj

        result = validate_out_dir(mock_ctx, "/valid/directory")
        self.assertEqual(result, Path("/valid/directory").resolve())

    @patch("src.utils.cli.callbacks.Path")
    @patch("src.utils.cli.callbacks.Context")
    @patch("src.utils.cli.callbacks.logger")
    def test_validate_out_dir_with_none_dir(self, mock_logger, mock_ctx, mock_path):
        """
        Test the validate_out_dir function with None as directory (should use cwd).
        :param mock_ctx: the typer context object
        :param mock_path: the Path object
        """
        mock_path.cwd.return_value = Path("/current/working/directory")

        result = validate_out_dir(mock_ctx, None)
        self.assertEqual(result, Path("/current/working/directory"))

    @patch("src.utils.cli.callbacks.Path")
    @patch("src.utils.cli.callbacks.Context")
    @patch("src.utils.cli.callbacks.logger")
    def test_validate_out_dir_with_invalid_dir(self, mock_logger, mock_ctx, mock_path):
        """
        Test the validate_out_dir function with an invalid directory.
        :param mock_ctx: the typer context object
        :param mock_path: the Path object
        """
        mock_path_obj = MagicMock()
        mock_path_obj.is_dir.return_value = False
        mock_path.return_value = mock_path_obj

        with self.assertRaises(BadParameter):
            validate_out_dir(mock_ctx, "/invalid/directory")
