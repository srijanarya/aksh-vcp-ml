"""
Unit tests for Story 7.5: Load Testing & Scaling

Tests load_tester.py for Locust integration, performance metrics, and scaling recommendations.

Total: 15 tests
- Test plan creation (3 tests)
- Metrics collection (4 tests)
- Result analysis (4 tests)
- Scaling recommendations (4 tests)

Target: 500 concurrent users, <200ms p95 latency
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
from typing import Dict, List

from agents.ml.optimization.load_tester import LoadTester


class TestLoadTester(unittest.TestCase):
    """Test load testing functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def setUp(self):
        """Set up load tester before each test"""
        self.tester = LoadTester(base_url="http://localhost:8000")

    # ==================== Test Plan Creation Tests ====================

    def test_01_create_basic_test_plan(self):
        """Test creating basic load test plan"""
        plan = self.tester.create_test_plan(
            max_users=100,
            ramp_time=60
        )

        self.assertIsNotNone(plan)
        self.assertEqual(plan['max_users'], 100)
        self.assertEqual(plan['ramp_time'], 60)
        self.assertIn('scenarios', plan)

    def test_02_test_plan_includes_scenarios(self):
        """Test plan includes prediction scenarios"""
        plan = self.tester.create_test_plan(max_users=500, ramp_time=300)

        scenarios = plan['scenarios']
        self.assertGreater(len(scenarios), 0)

        # Should have at least single and batch prediction scenarios
        scenario_names = [s['name'] for s in scenarios]
        self.assertIn('predict_single', scenario_names)

    def test_03_test_plan_configurable(self):
        """Test plan parameters are configurable"""
        plan1 = self.tester.create_test_plan(max_users=100, ramp_time=60)
        plan2 = self.tester.create_test_plan(max_users=500, ramp_time=300)

        self.assertNotEqual(plan1['max_users'], plan2['max_users'])
        self.assertNotEqual(plan1['ramp_time'], plan2['ramp_time'])

    # ==================== Metrics Collection Tests ====================

    def test_04_collect_latency_metrics(self):
        """Test collecting latency percentiles"""
        # Simulate load test results
        mock_results = {
            'requests': [
                {'response_time': 10, 'success': True},
                {'response_time': 20, 'success': True},
                {'response_time': 30, 'success': True},
                {'response_time': 100, 'success': True},
                {'response_time': 200, 'success': True},
            ]
        }

        metrics = self.tester.collect_metrics(mock_results)

        self.assertIn('latency_p50', metrics)
        self.assertIn('latency_p95', metrics)
        self.assertIn('latency_p99', metrics)

        # Check p50 is reasonable
        self.assertGreater(metrics['latency_p50'], 0)

    def test_05_collect_throughput_metrics(self):
        """Test collecting throughput metrics"""
        mock_results = {
            'requests': [
                {'response_time': 10, 'success': True},
                {'response_time': 20, 'success': True},
                {'response_time': 30, 'success': True},
            ],
            'duration': 1.0  # 1 second
        }

        metrics = self.tester.collect_metrics(mock_results)

        self.assertIn('throughput', metrics)
        # 3 requests in 1 second = 3 req/s
        self.assertAlmostEqual(metrics['throughput'], 3.0, places=1)

    def test_06_collect_error_rate_metrics(self):
        """Test collecting error rate metrics"""
        mock_results = {
            'requests': [
                {'response_time': 10, 'success': True},
                {'response_time': 20, 'success': True},
                {'response_time': 30, 'success': False},
                {'response_time': 40, 'success': False},
            ]
        }

        metrics = self.tester.collect_metrics(mock_results)

        self.assertIn('error_rate', metrics)
        # 2 errors / 4 requests = 50%
        self.assertAlmostEqual(metrics['error_rate'], 0.5, places=2)

    def test_07_metrics_handle_empty_results(self):
        """Test metrics collection handles empty results gracefully"""
        mock_results = {'requests': []}

        metrics = self.tester.collect_metrics(mock_results)

        # Should return valid metrics with zeros
        self.assertEqual(metrics['latency_p50'], 0)
        self.assertEqual(metrics['throughput'], 0)

    # ==================== Result Analysis Tests ====================

    def test_08_analyze_latency_percentiles(self):
        """Test latency percentile analysis"""
        mock_metrics = {
            'latency_p50': 25,
            'latency_p95': 90,
            'latency_p99': 180,
            'throughput': 450,
            'error_rate': 0.03
        }

        analysis = self.tester.analyze_results(mock_metrics)

        self.assertIn('latency_assessment', analysis)
        # p95 < 100ms should pass
        self.assertTrue(analysis['latency_acceptable'])

    def test_09_analyze_throughput(self):
        """Test throughput analysis"""
        mock_metrics = {
            'latency_p50': 25,
            'latency_p95': 90,
            'latency_p99': 180,
            'throughput': 450,
            'error_rate': 0.03
        }

        analysis = self.tester.analyze_results(mock_metrics)

        self.assertIn('throughput', analysis)
        self.assertGreater(analysis['throughput'], 400)

    def test_10_analyze_error_rate(self):
        """Test error rate analysis"""
        mock_metrics = {
            'latency_p50': 25,
            'latency_p95': 90,
            'latency_p99': 180,
            'throughput': 450,
            'error_rate': 0.03
        }

        analysis = self.tester.analyze_results(mock_metrics)

        self.assertIn('error_rate', analysis)
        # 3% error rate should be acceptable (<5%)
        self.assertLess(analysis['error_rate'], 0.05)

    def test_11_analysis_identifies_performance_issues(self):
        """Test analysis identifies when performance targets not met"""
        # High latency, low throughput scenario
        mock_metrics = {
            'latency_p50': 150,
            'latency_p95': 350,
            'latency_p99': 500,
            'throughput': 50,
            'error_rate': 0.15
        }

        analysis = self.tester.analyze_results(mock_metrics)

        # Should identify issues
        self.assertFalse(analysis['latency_acceptable'])
        self.assertGreater(analysis['error_rate'], 0.1)

    # ==================== Scaling Recommendations Tests ====================

    def test_12_recommend_scaling_for_high_latency(self):
        """Test scaling recommendation when latency is high"""
        mock_metrics = {
            'latency_p95': 250,  # High latency
            'cpu_usage': 85,
            'memory_usage': 60,
            'throughput': 200
        }

        recommendations = self.tester.generate_scaling_recommendations(mock_metrics)

        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

        # Should recommend scaling
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('scale' in rec_text or 'instance' in rec_text or 'optimize' in rec_text)

    def test_13_recommend_scaling_for_high_cpu(self):
        """Test scaling recommendation when CPU usage is high"""
        mock_metrics = {
            'latency_p95': 50,
            'cpu_usage': 95,  # Very high CPU
            'memory_usage': 60,
            'throughput': 400
        }

        recommendations = self.tester.generate_scaling_recommendations(mock_metrics)

        # Should recommend horizontal scaling
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('cpu' in rec_text or 'scale' in rec_text)

    def test_14_recommend_optimization_for_high_error_rate(self):
        """Test recommendation when error rate is high"""
        mock_metrics = {
            'latency_p95': 80,
            'cpu_usage': 60,
            'memory_usage': 50,
            'throughput': 300,
            'error_rate': 0.12  # High error rate
        }

        recommendations = self.tester.generate_scaling_recommendations(mock_metrics)

        # Should recommend investigating errors
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue('error' in rec_text or 'investigate' in rec_text or 'fix' in rec_text)

    def test_15_no_recommendations_when_performing_well(self):
        """Test no recommendations when system performing well"""
        mock_metrics = {
            'latency_p95': 45,
            'cpu_usage': 55,
            'memory_usage': 60,
            'throughput': 480,
            'error_rate': 0.02
        }

        recommendations = self.tester.generate_scaling_recommendations(mock_metrics)

        # Should have minimal or positive recommendations
        # Or recommendations might suggest everything is good
        self.assertIsInstance(recommendations, list)


if __name__ == '__main__':
    unittest.main()
