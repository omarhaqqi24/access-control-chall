"""Small in-memory per-client request limiter."""
from collections import defaultdict, deque
import threading
import time

class RateLimiter:
    """Allow a bounded number of requests per client in a rolling window."""
    def __init__(self, limit: int = 12, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, client_id: str) -> bool:
        """Return whether a client may submit another validation request."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            requests = self._requests[client_id]
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if len(requests) >= self.limit:
                return False
            requests.append(now)
            return True
