from __future__ import annotations

import logging
from typing import Any, Callable, Coroutine, TypeVar

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    RetryCallState,
)

T = TypeVar("T")

logger = logging.getLogger("retry-manager")


class RetryManager:
    """Wraps tenacity with optional WARP IP rotation on failure."""

    def __init__(
        self,
        max_attempts: int = 3,
        multiplier: float = 2.0,
        min_wait: float = 5.0,
        max_wait: float = 60.0,
    ) -> None:
        self.max_attempts = max_attempts
        self.multiplier = multiplier
        self.min_wait = min_wait
        self.max_wait = max_wait

    def _make_on_retry(self, warp: Any | None) -> Callable[[RetryCallState], None]:
        def on_retry(retry_state: RetryCallState) -> None:
            if warp is not None:
                try:
                    if hasattr(warp, "rotate_ip"):
                        import asyncio
                        if asyncio.iscoroutinefunction(warp.rotate_ip):
                            # Schedule async rotation if possible, else noop in sync context
                            try:
                                loop = asyncio.get_running_loop()
                                loop.create_task(warp.rotate_ip())
                            except RuntimeError:
                                pass
                        else:
                            warp.rotate_ip()
                    logger.info("Rotated WARP IP on retry attempt %s", retry_state.attempt_number)
                except Exception as exc:
                    logger.warning("WARP rotation failed on retry: %s", exc)
        return on_retry

    def retry_with_warp_rotation(
        self,
        warp: Any | None,
        exceptions: tuple[type[BaseException], ...] = (Exception,),
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Return a tenacity retry decorator that rotates WARP IP on failure.

        Args:
            warp: Optional WarpManager instance.
            exceptions: Tuple of exception types to retry on.

        Returns:
            A tenacity retry decorator.
        """
        return retry(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(multiplier=self.multiplier, min=self.min_wait, max=self.max_wait),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
            after=self._make_on_retry(warp),
        )
