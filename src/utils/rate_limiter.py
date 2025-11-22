"""
Rate Limiter

Token bucket algorithm for rate limiting API calls.

This implementation follows Test-Driven Development (TDD):
- Tests written first in tests/unit/test_rate_limiter.py
- Implementation written to pass tests
- Coverage target: 100%
"""

import time
import threading
from typing import Dict


class RateLimiter:
    """
    Token bucket rate limiter

    Features:
    - Thread-safe token bucket algorithm
    - Configurable burst capacity
    - Blocking and non-blocking acquisition
    - Usage statistics tracking
    """

    def __init__(
        self,
        requests_per_second: float,
        burst_capacity: int = None
    ):
        """
        Initialize rate limiter

        Args:
            requests_per_second: Maximum sustained request rate
            burst_capacity: Maximum burst size (defaults to requests_per_second)
        """
        self.requests_per_second = requests_per_second
        self.burst_capacity = burst_capacity if burst_capacity is not None else int(requests_per_second)

        # Token bucket state
        self._tokens = float(self.burst_capacity)
        self._last_refill = time.time()
        self._lock = threading.Lock()

        # Statistics
        self._total_requests = 0
        self._total_tokens_acquired = 0
        self._total_wait_time = 0.0

    def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens, blocking if necessary

        Args:
            tokens: Number of tokens to acquire

        Returns:
            Time waited in seconds
        """
        wait_time = 0.0

        with self._lock:
            while True:
                # Refill tokens
                self._refill()

                if self._tokens >= tokens:
                    # Sufficient tokens available
                    self._tokens -= tokens
                    self._total_requests += 1
                    self._total_tokens_acquired += tokens
                    self._total_wait_time += wait_time
                    return wait_time

                # Not enough tokens, calculate wait time
                tokens_needed = tokens - self._tokens
                wait_seconds = tokens_needed / self.requests_per_second

                # Release lock while sleeping
                self._lock.release()
                time.sleep(wait_seconds)
                wait_time += wait_seconds
                self._lock.acquire()

    def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without blocking

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False otherwise
        """
        with self._lock:
            self._refill()

            if self._tokens >= tokens:
                self._tokens -= tokens
                self._total_requests += 1
                self._total_tokens_acquired += tokens
                return True

            return False

    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self._last_refill

        # Calculate tokens to add
        tokens_to_add = elapsed * self.requests_per_second

        # Update tokens (cap at burst capacity)
        self._tokens = min(self._tokens + tokens_to_add, self.burst_capacity)
        self._last_refill = now

    def get_stats(self) -> Dict:
        """
        Get usage statistics

        Returns:
            Dict with statistics
        """
        with self._lock:
            return {
                'total_requests': self._total_requests,
                'total_tokens_acquired': self._total_tokens_acquired,
                'total_wait_time': self._total_wait_time,
                'current_tokens': self._tokens,
                'burst_capacity': self.burst_capacity,
                'requests_per_second': self.requests_per_second
            }
