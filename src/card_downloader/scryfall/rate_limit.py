import time
from typing import Callable


class RateLimiter:
    def __init__(
        self,
        min_interval: float = 0.5,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        self._min_interval = min_interval
        self._sleep = sleep_fn or time.sleep
        self._last_at = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_at
        if elapsed < self._min_interval:
            self._sleep(self._min_interval - elapsed)
        self._last_at = time.monotonic()
