"""
Tests for Rate Limiter

TDD Approach: RED Phase - All tests will fail initially
"""

import pytest
import time
from src.utils.rate_limiter import RateLimiter


class TestRateLimiterInitialization:
    """Test rate limiter initialization"""

    def test_rate_limiter_initialization(self):
        """Test rate limiter with default parameters"""
        limiter = RateLimiter(requests_per_second=10)
        assert limiter.requests_per_second == 10
        assert limiter.burst_capacity == 10  # Default equals rate

    def test_rate_limiter_with_burst_capacity(self):
        """Test rate limiter with custom burst capacity"""
        limiter = RateLimiter(requests_per_second=5, burst_capacity=20)
        assert limiter.requests_per_second == 5
        assert limiter.burst_capacity == 20


class TestTokenAcquisition:
    """Test token acquisition"""

    def test_acquire_single_token(self):
        """Test acquiring single token"""
        limiter = RateLimiter(requests_per_second=10)
        wait_time = limiter.acquire(1)
        assert wait_time >= 0

    def test_acquire_multiple_tokens(self):
        """Test acquiring multiple tokens at once"""
        limiter = RateLimiter(requests_per_second=10)
        wait_time = limiter.acquire(5)
        assert wait_time >= 0

    def test_acquire_blocks_when_depleted(self):
        """Test that acquire blocks when tokens depleted"""
        limiter = RateLimiter(requests_per_second=2, burst_capacity=2)

        # Deplete bucket
        limiter.acquire(2)

        # Next acquire should block
        start = time.time()
        limiter.acquire(1)
        elapsed = time.time() - start

        # Should have waited ~0.5s (1/2 requests per second)
        assert elapsed >= 0.4  # Allow some tolerance

    def test_tokens_refill_over_time(self):
        """Test that tokens refill at correct rate"""
        limiter = RateLimiter(requests_per_second=10, burst_capacity=10)

        # Deplete bucket
        limiter.acquire(10)

        # Wait for 0.5 seconds (should refill 5 tokens)
        time.sleep(0.5)

        # Should be able to acquire 5 tokens without blocking
        start = time.time()
        limiter.acquire(5)
        elapsed = time.time() - start

        # Should not have waited (tokens refilled)
        assert elapsed < 0.1


class TestTryAcquire:
    """Test non-blocking try_acquire"""

    def test_try_acquire_success(self):
        """Test try_acquire succeeds when tokens available"""
        limiter = RateLimiter(requests_per_second=10)
        result = limiter.try_acquire(1)
        assert result is True

    def test_try_acquire_fails_when_depleted(self):
        """Test try_acquire fails when no tokens available"""
        limiter = RateLimiter(requests_per_second=2, burst_capacity=2)

        # Deplete bucket
        limiter.acquire(2)

        # try_acquire should fail immediately
        result = limiter.try_acquire(1)
        assert result is False


class TestBurstCapacity:
    """Test burst capacity behavior"""

    def test_burst_allows_quick_requests(self):
        """Test burst capacity allows quick succession of requests"""
        limiter = RateLimiter(requests_per_second=5, burst_capacity=20)

        # Should be able to make 20 requests quickly
        start = time.time()
        for _ in range(20):
            limiter.acquire(1)
        elapsed = time.time() - start

        # Should complete quickly (< 1 second)
        assert elapsed < 1.0

    def test_burst_then_throttle(self):
        """Test that after burst, rate limiting kicks in"""
        limiter = RateLimiter(requests_per_second=5, burst_capacity=10)

        # Use up burst capacity
        for _ in range(10):
            limiter.acquire(1)

        # Next 5 requests should be throttled
        start = time.time()
        for _ in range(5):
            limiter.acquire(1)
        elapsed = time.time() - start

        # Should take ~1 second (5 requests at 5 req/s)
        assert elapsed >= 0.8  # Allow some tolerance


class TestStatistics:
    """Test usage statistics tracking"""

    def test_get_usage_stats(self):
        """Test getting usage statistics"""
        limiter = RateLimiter(requests_per_second=10)

        # Make some requests
        limiter.acquire(1)
        limiter.acquire(2)
        limiter.try_acquire(1)

        stats = limiter.get_stats()

        assert 'total_requests' in stats
        assert 'total_tokens_acquired' in stats
        assert 'total_wait_time' in stats
        assert stats['total_requests'] >= 3
        assert stats['total_tokens_acquired'] >= 4

    def test_track_wait_time(self):
        """Test that wait time is tracked correctly"""
        limiter = RateLimiter(requests_per_second=2, burst_capacity=2)

        # Deplete bucket
        limiter.acquire(2)

        # This should cause waiting
        limiter.acquire(1)

        stats = limiter.get_stats()

        # Should have recorded some wait time
        assert stats['total_wait_time'] > 0
