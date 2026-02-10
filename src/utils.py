from __future__ import annotations

import time
from typing import Callable, TypeVar


T = TypeVar("T")


def backoff_retry(action: Callable[[], T], attempts: int = 3, base_delay: float = 1.0) -> T:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return action()
        except Exception as exc:  # pragma: no cover - convenience wrapper
            last_error = exc
            time.sleep(base_delay * (2**attempt))
    if last_error:
        raise last_error
    raise RuntimeError("retry failed")
