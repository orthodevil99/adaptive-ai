"""In-process sliding-window rate limiter.

Per-process state: with several workers each has its own counters, so use a shared
store (e.g. Redis) or a gateway limit if you scale out.
"""

import math
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class RateDecision:
    allowed: bool
    limit: int
    remaining: int
    retry_after: int  # seconds; 0 when allowed


class SlidingWindowLimiter:
    def __init__(self, clock: Callable[[], float] = time.monotonic, sweep_every: int = 2000) -> None:
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._windows: dict[str, float] = {}
        self._sweep_every = sweep_every
        self._calls = 0

    def check(self, key: str, limit: int, window: float = 60.0) -> RateDecision:
        now = self._clock()
        self._calls += 1
        if self._calls % self._sweep_every == 0:
            self._sweep(now)
        hits = self._hits.setdefault(key, deque())
        self._windows[key] = window
        while hits and now - hits[0] >= window:
            hits.popleft()
        if len(hits) >= limit:
            retry = max(1, math.ceil(window - (now - hits[0])))
            return RateDecision(False, limit, 0, retry)
        hits.append(now)
        return RateDecision(True, limit, limit - len(hits), 0)

    def _sweep(self, now: float) -> None:
        for key in list(self._hits):
            hits = self._hits[key]
            window = self._windows.get(key, 60.0)
            while hits and now - hits[0] >= window:
                hits.popleft()
            if not hits:
                del self._hits[key]
                self._windows.pop(key, None)
