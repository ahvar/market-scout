import unittest
from unittest.mock import MagicMock, patch
from src.api.ib_utils import ConnectionWatchdog, IBMarketMemory


class TestConnectionWatchdog(unittest.TestCase):
    """
    Test the ConnectionWatchdog class.
    """

    def setUp(self):
        self.mock_start_services = MagicMock()
        self.mock_stop_services = MagicMock()
        self.mock_is_connected_method = MagicMock(return_value=True)
        self.watchdog = ConnectionWatchdog(
            check_interval=1,
            start_services=self.mock_start_services,
            stop_services=self.mock_stop_services,
            is_connected_method=self.mock_is_connected_method,
        )

    def test_start_stop_watchdog(self):
        """
        Test the start_dog and stop_dog methods.
        """
        self.watchdog.start_dog()
        self.assertTrue(self.watchdog.running)

        self.watchdog.stop_dog()
        self.assertFalse(self.watchdog.running)

    @patch("time.sleep", MagicMock())  # To speed up the test
    def test_monitor_connection(self):
        """
        Test the monitor_connection method.
        """
        self.watchdog._running = True  # Simulate watchdog running
        self.mock_is_connected_method.side_effect = [
            False,
            True,
        ]  # First disconnect then connect

        with patch.object(
            self.watchdog, "_running", new_callable=MagicMock
        ) as mock_running:
            mock_running.side_effect = [True, False]  # Run once then stop
            self.watchdog.monitor_connection()

            self.mock_stop_services.assert_called_once()
            self.mock_start_services.assert_called_once()


class TestIBMarketMemory(unittest.TestCase):
    """
    Test the IBMarketMemory class.
    """

    def setUp(self):
        self.market_memory = IBMarketMemory()

    def test_add_to_temp_hist_cache(self):
        req_id = 1
        bar_data = {"close": 100}
        self.market_memory.add_to_temp_hist_cache(req_id, bar_data)

        self.assertIn(req_id, self.market_memory.temp_hist_data)
        self.assertEqual(len(self.market_memory.temp_hist_data[req_id]), 1)
        self.assertEqual(self.market_memory.temp_hist_data[req_id][0], bar_data)

    def test_add_bulk_to_temp_hist_cache(self):
        req_id = 1
        bar_data = [{"close": 100}, {"close": 105}]
        for bar in bar_data:
            self.market_memory.add_to_temp_hist_cache(req_id, bar)

        self.market_memory.add_bulk_to_temp_hist_cache(req_id)

        self.assertIn(req_id, self.market_memory.historical_data)
        self.assertEqual(len(self.market_memory.historical_data[req_id]), 2)
        # Further checks can be added for the content of the bulk added data

    # Additional tests can be added for testing other methods like get_new_data, compute_missing_date, etc.
