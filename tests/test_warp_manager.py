import pytest
from unittest.mock import Mock, patch, MagicMock

from src.warp_manager import WarpManager, WarpStatus


class TestWarpStatus:
    def test_warp_status_creation(self):
        """Test WarpStatus dataclass creation."""
        status = WarpStatus(connected=True, ip="1.2.3.4")
        assert status.connected is True
        assert status.ip == "1.2.3.4"

    def test_warp_status_disconnected(self):
        """Test WarpStatus for disconnected state."""
        status = WarpStatus(connected=False, ip=None)
        assert status.connected is False
        assert status.ip is None


class TestWarpManager:
    def test_warp_manager_creation(self):
        """Test WarpManager initialization."""
        manager = WarpManager(connect_timeout_sec=30)
        assert manager.connect_timeout_sec == 30

    @patch("src.warp_manager.subprocess.run")
    def test_connect_runs_warp_cli(self, mock_run):
        """Test that connect runs warp-cli connect."""
        mock_run.return_value = Mock()

        with patch.object(WarpManager, "_wait_for_connection"):
            manager = WarpManager()
            manager.connect()

        mock_run.assert_called_with(["warp-cli", "connect"], check=True)

    @patch("src.warp_manager.subprocess.run")
    def test_disconnect_runs_warp_cli(self, mock_run):
        """Test that disconnect runs warp-cli disconnect."""
        mock_run.return_value = Mock()

        manager = WarpManager()
        manager.disconnect()

        mock_run.assert_called_with(["warp-cli", "disconnect"], check=True)

    @patch("src.warp_manager.subprocess.run")
    @patch("src.warp_manager.time.sleep")
    def test_rotate_ip_disconnects_and_connects(self, mock_sleep, mock_run):
        """Test that rotate_ip disconnects then connects."""
        mock_run.return_value = Mock()

        with patch.object(WarpManager, "_wait_for_connection"):
            manager = WarpManager()
            manager.rotate_ip()

        # Should call disconnect then connect
        calls = mock_run.call_args_list
        assert any("disconnect" in str(c) for c in calls)
        assert any("connect" in str(c) for c in calls)
        mock_sleep.assert_called_once_with(2)

    @patch("src.warp_manager.subprocess.run")
    def test_status_parses_connected_output(self, mock_run):
        """Test parsing connected status output."""
        mock_result = Mock()
        mock_result.stdout = "Status: Connected\nIP: 1.2.3.4"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        manager = WarpManager()
        status = manager.status()

        assert status.connected is True
        assert status.ip == "1.2.3.4"

    @patch("src.warp_manager.subprocess.run")
    def test_status_parses_disconnected_output(self, mock_run):
        """Test parsing disconnected status output."""
        mock_result = Mock()
        mock_result.stdout = "Status: Disconnected"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        manager = WarpManager()
        status = manager.status()

        assert status.connected is False
        assert status.ip is None

    @patch("src.warp_manager.subprocess.run")
    def test_status_handles_missing_ip(self, mock_run):
        """Test handling status output without IP."""
        mock_result = Mock()
        mock_result.stdout = "Status: Connected"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        manager = WarpManager()
        status = manager.status()

        assert status.connected is True
        assert status.ip is None

    @patch("src.warp_manager.subprocess.run")
    @patch("src.warp_manager.time.time")
    @patch("src.warp_manager.time.sleep")
    def test_wait_for_connection_succeeds(self, mock_sleep, mock_time, mock_run):
        """Test successful connection wait."""
        # Mock time to return increasing values
        mock_time.side_effect = [0, 1, 2]

        # Mock status to return connected on second call
        mock_result = Mock()
        mock_result.stdout = "Status: Connected"
        mock_run.return_value = mock_result

        manager = WarpManager(connect_timeout_sec=30)
        manager._wait_for_connection()  # Should not raise

    @patch("src.warp_manager.subprocess.run")
    @patch("src.warp_manager.time.time")
    @patch("src.warp_manager.time.sleep")
    def test_wait_for_connection_times_out(self, mock_sleep, mock_time, mock_run):
        """Test connection wait timeout."""
        # Mock time to exceed timeout
        mock_time.side_effect = [0, 35, 70]

        # Mock status to always return disconnected
        mock_result = Mock()
        mock_result.stdout = "Status: Disconnected"
        mock_run.return_value = mock_result

        manager = WarpManager(connect_timeout_sec=30)
        with pytest.raises(TimeoutError):
            manager._wait_for_connection()

    @patch("src.warp_manager.subprocess.run")
    def test_connect_retries_on_failure(self, mock_run):
        """Test that connect retries on failure."""
        from tenacity import RetryError

        # Make subprocess.run always fail
        mock_run.side_effect = Exception("Command failed")

        manager = WarpManager(connect_timeout_sec=30)
        with pytest.raises(RetryError):
            manager.connect()

        # Should have been called multiple times due to retry
        assert mock_run.call_count > 1
