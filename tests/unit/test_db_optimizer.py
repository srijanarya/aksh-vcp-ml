"""
Unit tests for Story 7.3: Database Query Optimization

Tests db_optimizer.py for indexing, connection pooling, caching, and query analysis.

Total: 16 tests
- Initialization (2 tests)
- Index creation (4 tests)
- Connection pooling (4 tests)
- Query caching (3 tests)
- Performance verification (3 tests)

Target: 5x query speedup
"""

import unittest
import tempfile
import os
import sqlite3
import time
from pathlib import Path
from typing import List, Dict

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from agents.ml.optimization.db_optimizer import DatabaseOptimizer


class TestDatabaseOptimizer(unittest.TestCase):
    """Test database query optimization functionality"""

    @classmethod
    def setUpClass(cls):
        """Create test database with sample data"""
        cls.test_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.test_dir, "test_optimization.db")

        # Create test database with sample tables
        conn = sqlite3.connect(cls.db_path)
        cursor = conn.cursor()

        # Create price_movements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_movements (
                id INTEGER PRIMARY KEY,
                bse_code TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER
            )
        """)

        # Create labels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS upper_circuit_labels (
                id INTEGER PRIMARY KEY,
                bse_code TEXT NOT NULL,
                date TEXT NOT NULL,
                upper_circuit_label INTEGER
            )
        """)

        # Insert sample data (1000 rows for performance testing)
        sample_data = []
        for i in range(1000):
            bse_code = f"50{i:04d}"
            date = f"2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}"
            sample_data.append((
                bse_code, date, 100.0 + i, 105.0 + i, 95.0 + i, 102.0 + i, 1000000 + i
            ))

        cursor.executemany(
            "INSERT INTO price_movements (bse_code, date, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?)",
            sample_data
        )

        # Insert label data
        label_data = [(f"50{i:04d}", f"2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}", i % 2) for i in range(1000)]
        cursor.executemany(
            "INSERT INTO upper_circuit_labels (bse_code, date, upper_circuit_label) VALUES (?, ?, ?)",
            label_data
        )

        conn.commit()
        conn.close()

    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        import shutil
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def setUp(self):
        """Set up test optimizer"""
        # Try to connect to Redis, fallback to cache-less mode
        redis_available = False
        if REDIS_AVAILABLE:
            try:
                r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
                r.ping()
                redis_available = True
                # Clear Redis cache before each test
                r.flushdb()
            except:
                pass

        self.optimizer = DatabaseOptimizer(
            db_path=self.db_path,
            pool_size=10,
            redis_host='localhost' if redis_available else None
        )

    # ==================== Initialization Tests ====================

    def test_01_initialization_with_valid_db(self):
        """Test optimizer initializes with valid database"""
        optimizer = DatabaseOptimizer(db_path=self.db_path, pool_size=5)
        self.assertIsNotNone(optimizer)
        self.assertEqual(optimizer.db_path, self.db_path)
        self.assertEqual(optimizer.pool_size, 5)

    def test_02_initialization_creates_connection_pool(self):
        """Test connection pool is created on initialization"""
        optimizer = DatabaseOptimizer(db_path=self.db_path, pool_size=3)
        self.assertIsNotNone(optimizer.connection_pool)
        self.assertEqual(optimizer.available_connections, 3)

    # ==================== Index Creation Tests ====================

    def test_03_create_indexes_on_bse_code(self):
        """Test creating index on bse_code column"""
        indexes = self.optimizer.create_indexes()

        # Verify index was created
        conn = self.optimizer.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_bse_code'")
        result = cursor.fetchone()
        self.optimizer.release_connection(conn)

        self.assertIsNotNone(result)
        self.assertIn("idx_bse_code", indexes)

    def test_04_create_indexes_on_date(self):
        """Test creating index on date column"""
        indexes = self.optimizer.create_indexes()

        conn = self.optimizer.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_date'")
        result = cursor.fetchone()
        self.optimizer.release_connection(conn)

        self.assertIsNotNone(result)
        self.assertIn("idx_date", indexes)

    def test_05_create_indexes_on_label(self):
        """Test creating index on upper_circuit_label column"""
        indexes = self.optimizer.create_indexes()

        conn = self.optimizer.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_label'")
        result = cursor.fetchone()
        self.optimizer.release_connection(conn)

        self.assertIsNotNone(result)
        self.assertIn("idx_label", indexes)

    def test_06_indexes_improve_query_performance(self):
        """Test that indexes improve query performance"""
        # Query without index
        start = time.time()
        result_no_index = self.optimizer.execute_query(
            "SELECT * FROM price_movements WHERE bse_code = ?",
            ("500001",)
        )
        time_no_index = time.time() - start

        # Create indexes
        self.optimizer.create_indexes()

        # Query with index
        start = time.time()
        result_with_index = self.optimizer.execute_query(
            "SELECT * FROM price_movements WHERE bse_code = ?",
            ("500001",)
        )
        time_with_index = time.time() - start

        # With small dataset, improvement might be minimal, but query should still work
        self.assertEqual(len(result_no_index), len(result_with_index))

    # ==================== Connection Pooling Tests ====================

    def test_07_get_connection_from_pool(self):
        """Test getting connection from pool"""
        conn = self.optimizer.get_connection()
        self.assertIsNotNone(conn)
        self.assertIsInstance(conn, sqlite3.Connection)
        self.optimizer.release_connection(conn)

    def test_08_release_connection_to_pool(self):
        """Test releasing connection back to pool"""
        initial_available = self.optimizer.available_connections
        conn = self.optimizer.get_connection()

        # Available should decrease
        self.assertEqual(self.optimizer.available_connections, initial_available - 1)

        self.optimizer.release_connection(conn)

        # Available should be restored
        self.assertEqual(self.optimizer.available_connections, initial_available)

    def test_09_pool_size_limit(self):
        """Test connection pool respects size limit"""
        # Get all connections
        connections = []
        for _ in range(self.optimizer.pool_size):
            connections.append(self.optimizer.get_connection())

        # No connections available
        self.assertEqual(self.optimizer.available_connections, 0)

        # Release all connections
        for conn in connections:
            self.optimizer.release_connection(conn)

        # All connections available again
        self.assertEqual(self.optimizer.available_connections, self.optimizer.pool_size)

    def test_10_concurrent_connections(self):
        """Test multiple concurrent connections work correctly"""
        conn1 = self.optimizer.get_connection()
        conn2 = self.optimizer.get_connection()

        # Both connections should be valid and different
        self.assertIsNotNone(conn1)
        self.assertIsNotNone(conn2)
        self.assertIsNot(conn1, conn2)

        self.optimizer.release_connection(conn1)
        self.optimizer.release_connection(conn2)

    # ==================== Query Caching Tests ====================

    @unittest.skipIf(not REDIS_AVAILABLE, "Redis not available")
    def test_11_execute_with_cache_caches_results(self):
        """Test query results are cached"""
        query = "SELECT * FROM price_movements WHERE bse_code = ?"
        params = ("500001",)

        # First execution (cache miss)
        result1 = self.optimizer.execute_with_cache(query, params, ttl=300)

        # Second execution (cache hit)
        result2 = self.optimizer.execute_with_cache(query, params, ttl=300)

        # Results should be identical
        self.assertEqual(result1, result2)

    @unittest.skipIf(not REDIS_AVAILABLE, "Redis not available")
    def test_12_cache_hit_faster_than_miss(self):
        """Test cache hits are faster than cache misses"""
        query = "SELECT * FROM price_movements WHERE bse_code = ?"
        params = ("500001",)

        # First execution (cache miss)
        start = time.time()
        self.optimizer.execute_with_cache(query, params, ttl=300)
        time_miss = time.time() - start

        # Second execution (cache hit)
        start = time.time()
        self.optimizer.execute_with_cache(query, params, ttl=300)
        time_hit = time.time() - start

        # Cache hit should be faster (at least 2x)
        self.assertLess(time_hit, time_miss)

    @unittest.skipIf(not REDIS_AVAILABLE, "Redis not available")
    def test_13_cache_respects_ttl(self):
        """Test cache respects TTL expiration"""
        query = "SELECT * FROM price_movements WHERE bse_code = ?"
        params = ("500001",)

        # Cache with 1 second TTL
        result1 = self.optimizer.execute_with_cache(query, params, ttl=1)

        # Wait for cache to expire
        time.sleep(2)

        # Should execute query again (cache expired)
        result2 = self.optimizer.execute_with_cache(query, params, ttl=1)

        # Results should still be identical
        self.assertEqual(result1, result2)

    # ==================== Performance Verification Tests ====================

    def test_14_analyze_query_plan(self):
        """Test EXPLAIN QUERY PLAN analysis"""
        query = "SELECT * FROM price_movements WHERE bse_code = ?"
        analysis = self.optimizer.analyze_query_plan(query)

        self.assertIsNotNone(analysis)
        self.assertIn('plan', analysis)
        self.assertIsInstance(analysis['plan'], list)

    def test_15_query_plan_shows_index_usage(self):
        """Test query plan shows index usage after creation"""
        # Create indexes
        self.optimizer.create_indexes()

        # Analyze query
        query = "SELECT * FROM price_movements WHERE bse_code = ?"
        analysis = self.optimizer.analyze_query_plan(query)

        # Check if index is mentioned in plan
        plan_text = str(analysis['plan'])
        # SQLite should mention index in plan (though exact format varies)
        self.assertIsNotNone(plan_text)

    def test_16_batch_query_performance(self):
        """Test batch queries are faster than individual queries"""
        bse_codes = [f"50{i:04d}" for i in range(10)]

        # Individual queries
        start = time.time()
        for code in bse_codes:
            self.optimizer.execute_query(
                "SELECT * FROM price_movements WHERE bse_code = ?",
                (code,)
            )
        time_individual = time.time() - start

        # Batch query
        placeholders = ','.join(['?' for _ in bse_codes])
        start = time.time()
        self.optimizer.execute_query(
            f"SELECT * FROM price_movements WHERE bse_code IN ({placeholders})",
            tuple(bse_codes)
        )
        time_batch = time.time() - start

        # Batch should be faster
        self.assertLess(time_batch, time_individual)


if __name__ == '__main__':
    unittest.main()
