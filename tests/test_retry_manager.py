import pytest
from unittest.mock import MagicMock

from src.retry_manager import RetryManager


class TestRetryManager:
    def test_creation(self):
        """Test RetryManager initialization."""
        rm = RetryManager(max_attempts=5, multiplier=3.0, min_wait=1.0, max_wait=10.0)
        assert rm.max_attempts == 5
        assert rm.multiplier == 3.0

    def test_retry_decorator_applies(self):
        """Test that retry decorator can be applied to a function."""
        rm = RetryManager(max_attempts=2, multiplier=1.0, min_wait=0.1, max_wait=1.0)
        mock_warp = MagicMock()
        mock_warp.rotate_ip = MagicMock()

        call_count = 0

        @rm.retry_with_warp_rotation(warp=mock_warp, exceptions=(ValueError,))
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail")
            return "ok"

        result = flaky()
        assert result == "ok"
        assert call_count == 2

    def test_retry_reraises_after_exhaustion(self):
        """Test that retry re-raises after max attempts."""
        rm = RetryManager(max_attempts=2, multiplier=1.0, min_wait=0.1, max_wait=1.0)

        @rm.retry_with_warp_rotation(warp=None, exceptions=(RuntimeError,))
        def always_fail():
            raise RuntimeError("always fails")

        with pytest.raises(RuntimeError, match="always fails"):
            always_fail()

    def test_retry_with_async_warp(self):
        """Test retry manager handles async warp rotation gracefully."""
        import asyncio

        async def async_rotate():
            pass

        mock_warp = MagicMock()
        mock_warp.rotate_ip = async_rotate

        rm = RetryManager(max_attempts=2, multiplier=1.0, min_wait=0.1, max_wait=1.0)

        call_count = 0

        @rm.retry_with_warp_rotation(warp=mock_warp, exceptions=(ValueError,))
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail")
            return "ok"

        result = flaky()
        assert result == "ok"
