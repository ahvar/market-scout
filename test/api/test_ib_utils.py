import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from broker.ib_utils import ConnectionWatchdog, IBMarketMemory


class TestConnectionWatchdog(unittest.TestCase):
    """
    Test the ConnectionWatchdog class.
    """

    @patch("src.api.ib_utils.utils_logger")
    def setUp(self, mock_utils_logger):
        self.mock_utils_logger = mock_utils_logger
        self.mock_start_services = MagicMock()
        self.mock_stop_services = MagicMock()
        self.mock_is_connected_method = MagicMock(return_value=True)

        # Define a custom function to be executed when mock_stop_services is called.
        def stop_services_side_effect(*args, **kwargs):
            self.watchdog._running = False  # This will stop the watchdog loop

        self.mock_stop_services = MagicMock(side_effect=stop_services_side_effect)
        self.watchdog = ConnectionWatchdog(
            check_interval=1,
            start_services=self.mock_start_services,
            stop_services=self.mock_stop_services,
            is_connected_method=self.mock_is_connected_method,
        )
        self.mock_utils_logger.info.assert_any_call(
            "Initializing %s instance", self.watchdog.__class__.__name__
        )
        self.mock_utils_logger.info.assert_any_call(
            "%s initialized", self.watchdog.__class__.__name__
        )

    def test_start_stop_watchdog(self):
        """
        Test the start_dog and stop_dog methods.
        """
        self.watchdog.start_dog()
        self.assertTrue(self.watchdog.running)

        self.watchdog.stop_dog()
        self.assertFalse(self.watchdog.running)

    @patch("time.sleep")  # speed up the test
    def test_monitor_connection(self, mock_time_sleep):
        """
        Test the monitor_connection method.
        """
        self.watchdog._running = True
        self.mock_is_connected_method.side_effect = [True, False]
        self.watchdog.monitor_connection()

        self.mock_stop_services.assert_called_once()
        self.mock_start_services.assert_called_once()
        # Assertions for utils_logger to verify logging actions
        # Check that 'Initializing' and 'initialized' log messages were called during setup

        # Verify that 'Connection lost. Reconnecting...' was logged
        # self.mock_utils_logger.debug.assert_called_with(
        #    "Connection lost. Reconnecting..."
        # )
        # self.mock_utils_logger.debug.assert_any_call("Connection lost. Reconnecting...")

        # If you want to ensure a specific logging call count, you can do so as well
        # For example, ensure the debug log was called exactly twice
        # self.assertEqual(self.mock_utils_logger.debug.call_count, 2)


class TestIBMarketMemory(unittest.TestCase):
    """
    Test the IBMarketMemory class.
    """

    def setUp(self):
        self.market_memory = IBMarketMemory()

    def test_add_to_temp_hist_cache(self):
        """
        Test the add_to_temp_hist_cache method.
        """
        req_id = 1
        bar_data = {"close": 100}
        self.market_memory.add_to_temp_hist_cache(req_id, bar_data)

        self.assertIn(req_id, self.market_memory.temp_hist_data)
        self.assertEqual(len(self.market_memory.temp_hist_data[req_id]), 1)
        self.assertEqual(self.market_memory.temp_hist_data[req_id][0], bar_data)

    def test_add_bulk_to_hist_cache(self):
        """
        Test the add_bulk_to_temp_hist_cache method.
        """
        req_id = 1
        bar_data = [{"close": 100}, {"close": 105}]
        for bar in bar_data:
            self.market_memory.add_to_temp_hist_cache(req_id, bar)

        self.market_memory.add_bulk_to_hist_cache(req_id)

        self.assertIn(req_id, self.market_memory.historical_data)
        self.assertEqual(len(self.market_memory.historical_data[req_id]), 2)
