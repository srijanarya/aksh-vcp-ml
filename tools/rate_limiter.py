"""
Rate Limiter - Token bucket algorithm for API rate limiting

Prevents overwhelming external APIs (BSE, NSE, yfinance) with too many requests.
Uses token bucket algorithm with configurable refill rate.

Author: VCP Financial Research Team
Version: 1.0.0
"""

import time
import logging
from typing import Optional
from threading import Lock

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for controlling request rates.

    Attributes:
        max_tokens: Maximum number of tokens in bucket
        refill_rate: Tokens added per second
        current_tokens: Current available tokens
        last_refill: Timestamp of last refill
    """

    def __init__(self, max_requests_per_second: float = 2.0, burst_size: Optional[int] = None):
        """
        Initialize rate limiter with token bucket algorithm.

        Args:
            max_requests_per_second: Maximum sustained request rate (default: 2.0)
            burst_size: Maximum burst requests allowed (default: 2x max_requests_per_second)

        Example:
            # Allow 2 requests/second with burst of 5
            limiter = RateLimiter(max_requests_per_second=2.0, burst_size=5)
        """
        self.refill_rate = max_requests_per_second  # tokens per second
        self.max_tokens = burst_size if burst_size else int(max_requests_per_second * 2)
        self.current_tokens = float(self.max_tokens)
        self.last_refill = time.time()
        self._lock = Lock()

        logger.info(
            f"RateLimiter initialized: {max_requests_per_second} req/s, "
            f"burst={self.max_tokens}"
        )

    def _refill(self):
        """Refill tokens based on elapsed time since last refill."""
        now = time.time()
        elapsed = now - self.last_refill

        # Calculate tokens to add
        tokens_to_add = elapsed * self.refill_rate
        self.current_tokens = min(self.max_tokens, self.current_tokens + tokens_to_add)
        self.last_refill = now

    def acquire(self, tokens: int = 1, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire (default: 1)
            blocking: If True, wait until tokens available; if False, return immediately
            timeout: Maximum seconds to wait (None = wait forever)

        Returns:
            True if tokens acquired, False if not available (non-blocking mode)

        Raises:
            TimeoutError: If timeout exceeded while waiting for tokens

        Example:
            limiter = RateLimiter(max_requests_per_second=2.0)

            # Blocking mode (wait for token)
            limiter.acquire()
            make_api_request()

            # Non-blocking mode (check availability)
            if limiter.acquire(blocking=False):
                make_api_request()
            else:
                logger.warning("Rate limit exceeded, skipping request")
        """
        start_time = time.time()

        while True:
            with self._lock:
                self._refill()

                if self.current_tokens >= tokens:
                    self.current_tokens -= tokens
                    logger.debug(f"Acquired {tokens} tokens ({self.current_tokens:.2f} remaining)")
                    return True

                if not blocking:
                    logger.debug(f"Token acquisition failed (non-blocking)")
                    return False

                # Calculate wait time
                tokens_needed = tokens - self.current_tokens
                wait_time = tokens_needed / self.refill_rate

            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed + wait_time > timeout:
                    raise TimeoutError(
                        f"Rate limiter timeout after {elapsed:.2f}s "
                        f"(needed {wait_time:.2f}s more)"
                    )

            logger.debug(f"Waiting {wait_time:.2f}s for tokens to refill")
            time.sleep(wait_time)

    def get_available_tokens(self) -> float:
        """
        Get current number of available tokens (non-blocking).

        Returns:
            Current token count

        Example:
            limiter = RateLimiter(max_requests_per_second=2.0)
            tokens = limiter.get_available_tokens()
            print(f"Available: {tokens:.2f} tokens")
        """
        with self._lock:
            self._refill()
            return self.current_tokens

    def reset(self):
        """
        Reset rate limiter to full token count.

        Example:
            limiter = RateLimiter(max_requests_per_second=2.0)
            # ... make many requests ...
            limiter.reset()  # Reset for new batch
        """
        with self._lock:
            self.current_tokens = float(self.max_tokens)
            self.last_refill = time.time()
            logger.info("Rate limiter reset to full capacity")


def respect_rate_limit(
    limiter: RateLimiter,
    tokens: int = 1,
    operation_name: str = "operation"
) -> None:
    """
    Convenience function to acquire tokens with logging.

    Args:
        limiter: RateLimiter instance
        tokens: Number of tokens to acquire
        operation_name: Human-readable operation name for logging

    Example:
        limiter = RateLimiter(max_requests_per_second=2.0)

        for company in companies:
            respect_rate_limit(limiter, operation_name=f"Fetch {company}")
            data = fetch_data(company)
    """
    logger.debug(f"Requesting rate limit token for: {operation_name}")
    limiter.acquire(tokens=tokens, blocking=True)
    logger.debug(f"Rate limit token acquired for: {operation_name}")


# Pre-configured rate limiters for common APIs
BSE_RATE_LIMITER = RateLimiter(max_requests_per_second=1.0, burst_size=3)  # Conservative
NSE_RATE_LIMITER = RateLimiter(max_requests_per_second=2.0, burst_size=5)  # Moderate
YFINANCE_RATE_LIMITER = RateLimiter(max_requests_per_second=5.0, burst_size=10)  # Generous


if __name__ == "__main__":
    # Demo: Test rate limiter
    logging.basicConfig(level=logging.DEBUG)

    print("Testing RateLimiter (2 req/s, burst=5)...")
    limiter = RateLimiter(max_requests_per_second=2.0, burst_size=5)

    print("\n1. Burst test (should be instant):")
    for i in range(5):
        limiter.acquire()
        print(f"  Request {i + 1} at {time.time():.2f}s")

    print("\n2. Sustained rate test (should wait ~0.5s between requests):")
    for i in range(3):
        limiter.acquire()
        print(f"  Request {i + 1} at {time.time():.2f}s")

    print("\n3. Non-blocking test:")
    if limiter.acquire(blocking=False):
        print("  ✅ Token available")
    else:
        print("  ❌ No tokens available (expected)")

    print("\n4. Reset test:")
    limiter.reset()
    print(f"  Available tokens after reset: {limiter.get_available_tokens()}")
