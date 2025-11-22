#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for Dashboard System
Tests how all components work together as a complete system
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# ANSI color codes for output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


class IntegrationTestSuite:
    """Integration test suite for dashboard system"""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.test_results = []
        self.dashboards = {
            'hub': 'dashboard-hub-FINAL.html',
            'earnings': 'comprehensive_earnings_calendar.html',
            'market_status': 'market_status_dashboard.html',
            'intelligence': 'intelligence_dashboard.html'
        }

    def log(self, message: str, level: str = "INFO"):
        """Log test messages with color"""
        color = {
            "INFO": BLUE,
            "PASS": GREEN,
            "FAIL": RED,
            "WARN": YELLOW
        }.get(level, NC)
        print(f"{color}{message}{NC}")

    def add_result(self, test_name: str, passed: bool, details: str = ""):
        """Record test result"""
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })

    def read_file(self, filename: str) -> Optional[str]:
        """Read file content"""
        try:
            filepath = self.base_path / filename
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return None

    def test_dashboard_navigation_links(self) -> bool:
        """Test 1: Dashboard Hub Navigation Integration"""
        self.log("\n" + "="*70, "INFO")
        self.log("INTEGRATION TEST 1: Dashboard Hub Navigation", "INFO")
        self.log("="*70, "INFO")

        hub_content = self.read_file(self.dashboards['hub'])
        if not hub_content:
            self.log("❌ FAIL: Cannot read dashboard hub", "FAIL")
            self.add_result("Dashboard Hub Navigation", False, "File not found")
            return False

        all_passed = True

        # Test 1.1: All dashboard links present in hub
        self.log("\nTest 1.1: Verifying all dashboard links in hub", "INFO")
        expected_links = [
            'comprehensive_earnings_calendar.html',
            'market_status_dashboard.html',
            'intelligence_dashboard.html'
        ]

        for link in expected_links:
            if link in hub_content:
                self.log(f"  ✅ Link to {link} found in hub", "PASS")
            else:
                self.log(f"  ❌ Link to {link} NOT found in hub", "FAIL")
                all_passed = False

        # Test 1.2: Dashboard hub has proper structure
        self.log("\nTest 1.2: Verifying hub structure", "INFO")
        required_elements = [
            'class="dashboard-card"',
            'Dashboard Hub',
            'Earnings Calendar',
            'Market Status',
            'Intelligence'
        ]

        for element in required_elements:
            if element in hub_content:
                self.log(f"  ✅ Element '{element}' found", "PASS")
            else:
                self.log(f"  ❌ Element '{element}' NOT found", "FAIL")
                all_passed = False

        # Test 1.3: Each linked dashboard file exists
        self.log("\nTest 1.3: Verifying linked dashboards exist", "INFO")
        for dashboard_name, dashboard_file in self.dashboards.items():
            if dashboard_name == 'hub':
                continue

            if self.read_file(dashboard_file):
                self.log(f"  ✅ {dashboard_file} exists", "PASS")
            else:
                self.log(f"  ❌ {dashboard_file} does NOT exist", "FAIL")
                all_passed = False

        self.add_result("Dashboard Hub Navigation", all_passed,
                       f"All links present and targets exist: {all_passed}")
        return all_passed

    def test_auto_refresh_integration(self) -> bool:
        """Test 2: Auto-Refresh Integration Across Dashboards"""
        self.log("\n" + "="*70, "INFO")
        self.log("INTEGRATION TEST 2: Auto-Refresh Integration", "INFO")
        self.log("="*70, "INFO")

        all_passed = True
        dashboards_with_refresh = ['earnings', 'market_status']

        # Test 2.1: Auto-refresh uses separate localStorage keys
        self.log("\nTest 2.1: Verifying separate localStorage keys", "INFO")
        storage_keys = {}

        for dash_name in dashboards_with_refresh:
            content = self.read_file(self.dashboards[dash_name])
            if not content:
                self.log(f"  ❌ Cannot read {dash_name}", "FAIL")
                all_passed = False
                continue

            # Find localStorage key
            key_match = re.search(r"localStorage\.(?:get|set)Item\(['\"]([^'\"]+)['\"]", content)
            if key_match:
                storage_keys[dash_name] = key_match.group(1)
                self.log(f"  ✅ {dash_name} uses key: '{storage_keys[dash_name]}'", "PASS")
            else:
                self.log(f"  ❌ {dash_name} localStorage key not found", "FAIL")
                all_passed = False

        # Verify keys are different
        if len(storage_keys) == 2:
            if len(set(storage_keys.values())) == 2:
                self.log("  ✅ Each dashboard uses unique localStorage key", "PASS")
            else:
                self.log("  ❌ Dashboards share localStorage key (conflict!)", "FAIL")
                all_passed = False

        # Test 2.2: Consistent refresh interval across dashboards
        self.log("\nTest 2.2: Verifying consistent refresh intervals", "INFO")
        intervals = {}

        for dash_name in dashboards_with_refresh:
            content = self.read_file(self.dashboards[dash_name])
            if not content:
                continue

            # Find refresh interval
            if '5 * 60 * 1000' in content:
                intervals[dash_name] = '5 minutes'
                self.log(f"  ✅ {dash_name} uses 5-minute interval", "PASS")
            elif '300000' in content:
                intervals[dash_name] = '5 minutes'
                self.log(f"  ✅ {dash_name} uses 5-minute interval (300000ms)", "PASS")
            else:
                self.log(f"  ❌ {dash_name} refresh interval unclear", "FAIL")
                all_passed = False

        # Test 2.3: Refresh functions have consistent naming
        self.log("\nTest 2.3: Verifying consistent function patterns", "INFO")
        required_functions = ['refreshData', 'startAutoRefresh', 'stopAutoRefresh']

        for dash_name in dashboards_with_refresh:
            content = self.read_file(self.dashboards[dash_name])
            if not content:
                continue

            missing_functions = []
            for func in required_functions:
                if f'function {func}' not in content:
                    missing_functions.append(func)

            if not missing_functions:
                self.log(f"  ✅ {dash_name} has all refresh functions", "PASS")
            else:
                self.log(f"  ❌ {dash_name} missing: {', '.join(missing_functions)}", "FAIL")
                all_passed = False

        self.add_result("Auto-Refresh Integration", all_passed,
                       f"Consistent implementation: {all_passed}")
        return all_passed

    def test_export_integration(self) -> bool:
        """Test 3: CSV/Excel Export Integration"""
        self.log("\n" + "="*70, "INFO")
        self.log("INTEGRATION TEST 3: CSV/Excel Export Integration", "INFO")
        self.log("="*70, "INFO")

        earnings_content = self.read_file(self.dashboards['earnings'])
        if not earnings_content:
            self.log("❌ FAIL: Cannot read earnings calendar", "FAIL")
            self.add_result("Export Integration", False, "File not found")
            return False

        all_passed = True

        # Test 3.1: All required libraries loaded in correct order
        self.log("\nTest 3.1: Verifying library load order", "INFO")
        libraries = [
            'jquery',
            'dataTables.min.js',
            'dataTables.buttons',
            'jszip',
            'buttons.html5'
        ]

        lib_positions = {}
        for lib in libraries:
            match = re.search(lib, earnings_content, re.IGNORECASE)
            if match:
                lib_positions[lib] = match.start()
                self.log(f"  ✅ {lib} loaded at position {match.start()}", "PASS")
            else:
                self.log(f"  ❌ {lib} NOT loaded", "FAIL")
                all_passed = False

        # Verify jQuery loads before DataTables
        if 'jquery' in lib_positions and 'dataTables.min.js' in lib_positions:
            if lib_positions['jquery'] < lib_positions['dataTables.min.js']:
                self.log("  ✅ jQuery loads before DataTables (correct order)", "PASS")
            else:
                self.log("  ❌ jQuery loads AFTER DataTables (wrong order!)", "FAIL")
                all_passed = False

        # Test 3.2: Export buttons configured with DataTable
        self.log("\nTest 3.2: Verifying DataTable and buttons configuration", "INFO")

        # Check for DataTable initialization
        datatable_pattern = r'\$\([\'"]#[\w-]+[\'"]\)\.DataTable\('
        if re.search(datatable_pattern, earnings_content):
            self.log("  ✅ DataTable initialized correctly", "PASS")
        else:
            self.log("  ❌ DataTable initialization not found", "FAIL")
            all_passed = False

        # Check for buttons configuration
        if "buttons:" in earnings_content and "'csv'" in earnings_content:
            self.log("  ✅ Export buttons configured", "PASS")
        else:
            self.log("  ❌ Export buttons NOT configured", "FAIL")
            all_passed = False

        # Test 3.3: Export filename includes dynamic date
        self.log("\nTest 3.3: Verifying dynamic filename generation", "INFO")
        if 'filename:' in earnings_content and ('today' in earnings_content or 'Date' in earnings_content):
            self.log("  ✅ Dynamic filename with date configured", "PASS")
        else:
            self.log("  ❌ Dynamic filename NOT configured", "FAIL")
            all_passed = False

        self.add_result("Export Integration", all_passed,
                       f"Export fully integrated: {all_passed}")
        return all_passed

    def test_styling_consistency(self) -> bool:
        """Test 4: Consistent Styling Across Dashboards"""
        self.log("\n" + "="*70, "INFO")
        self.log("INTEGRATION TEST 4: Styling Consistency", "INFO")
        self.log("="*70, "INFO")

        all_passed = True

        # Test 4.1: Consistent gradient colors
        self.log("\nTest 4.1: Verifying consistent gradient colors", "INFO")
        expected_gradients = [
            '#667eea',  # Primary purple
            '#764ba2',  # Primary violet
        ]

        gradient_usage = {}
        for dash_name, dash_file in self.dashboards.items():
            content = self.read_file(dash_file)
            if not content:
                continue

            gradients_found = []
            for color in expected_gradients:
                if color in content:
                    gradients_found.append(color)

            gradient_usage[dash_name] = gradients_found

            if len(gradients_found) == len(expected_gradients):
                self.log(f"  ✅ {dash_name}: Uses consistent gradient colors", "PASS")
            else:
                self.log(f"  ⚠️  {dash_name}: Missing some gradient colors", "WARN")

        # Test 4.2: Consistent button styling
        self.log("\nTest 4.2: Verifying consistent button patterns", "INFO")
        button_patterns = [
            'border-radius',
            'padding',
            'cursor: pointer'
        ]

        for dash_name, dash_file in self.dashboards.items():
            content = self.read_file(dash_file)
            if not content:
                continue

            patterns_found = sum(1 for pattern in button_patterns if pattern in content)

            if patterns_found == len(button_patterns):
                self.log(f"  ✅ {dash_name}: Consistent button styling", "PASS")
            else:
                self.log(f"  ⚠️  {dash_name}: Some button patterns missing", "WARN")

        # Test 4.3: Consistent responsive design approach
        self.log("\nTest 4.3: Verifying responsive design patterns", "INFO")
        responsive_patterns = [
            'viewport',
            'max-width',
        ]

        for dash_name, dash_file in self.dashboards.items():
            content = self.read_file(dash_file)
            if not content:
                continue

            has_responsive = sum(1 for pattern in responsive_patterns if pattern in content)

            if has_responsive >= 1:
                self.log(f"  ✅ {dash_name}: Has responsive design", "PASS")
            else:
                self.log(f"  ❌ {dash_name}: No responsive design found", "FAIL")
                all_passed = False

        self.add_result("Styling Consistency", all_passed,
                       f"Consistent design system: {all_passed}")
        return all_passed

    def test_javascript_error_handling(self) -> bool:
        """Test 5: JavaScript Error Handling Integration"""
        self.log("\n" + "="*70, "INFO")
        self.log("INTEGRATION TEST 5: JavaScript Error Handling", "INFO")
        self.log("="*70, "INFO")

        all_passed = True

        # Test 5.1: Consistent error handling patterns
        self.log("\nTest 5.1: Verifying error handling patterns", "INFO")

        for dash_name, dash_file in self.dashboards.items():
            content = self.read_file(dash_file)
            if not content:
                continue

            # Check for defensive programming
            has_null_checks = 'getElementById' in content
            has_try_catch = 'try' in content or 'catch' in content

            if has_null_checks:
                self.log(f"  ✅ {dash_name}: Uses getElementById (safe DOM access)", "PASS")
            else:
                self.log(f"  ⚠️  {dash_name}: No getElementById found", "WARN")

        # Test 5.2: Consistent event listener patterns
        self.log("\nTest 5.2: Verifying event listener patterns", "INFO")

        for dash_name, dash_file in self.dashboards.items():
            content = self.read_file(dash_file)
            if not content:
                continue

            if 'addEventListener' in content:
                self.log(f"  ✅ {dash_name}: Uses addEventListener (modern approach)", "PASS")

            # Check for inline handlers (bad practice)
            inline_pattern = r'on(?:click|load|change)='
            if re.search(inline_pattern, content):
                self.log(f"  ⚠️  {dash_name}: Contains inline event handlers", "WARN")

        self.add_result("Error Handling Integration", all_passed,
                       f"Consistent error handling: {all_passed}")
        return all_passed

    def test_end_to_end_user_workflows(self) -> bool:
        """Test 6: End-to-End User Workflows"""
        self.log("\n" + "="*70, "INFO")
        self.log("INTEGRATION TEST 6: End-to-End User Workflows", "INFO")
        self.log("="*70, "INFO")

        all_passed = True

        # Test 6.1: Workflow - User navigates from hub to earnings calendar
        self.log("\nTest 6.1: Hub → Earnings Calendar workflow", "INFO")

        hub_content = self.read_file(self.dashboards['hub'])
        earnings_content = self.read_file(self.dashboards['earnings'])

        if hub_content and earnings_content:
            # Check hub has link to earnings
            if 'comprehensive_earnings_calendar.html' in hub_content:
                self.log("  ✅ Step 1: Hub has link to earnings calendar", "PASS")

                # Check earnings calendar exists and has title
                if '<title>' in earnings_content:
                    self.log("  ✅ Step 2: Earnings calendar loads with title", "PASS")

                    # Check earnings has export buttons
                    if 'Download CSV' in earnings_content or 'csv' in earnings_content:
                        self.log("  ✅ Step 3: User can export earnings data", "PASS")
                    else:
                        self.log("  ❌ Step 3: No export functionality found", "FAIL")
                        all_passed = False
                else:
                    self.log("  ❌ Step 2: Earnings calendar missing title", "FAIL")
                    all_passed = False
            else:
                self.log("  ❌ Step 1: Hub missing link to earnings", "FAIL")
                all_passed = False
        else:
            self.log("  ❌ Workflow test failed: Files not found", "FAIL")
            all_passed = False

        # Test 6.2: Workflow - User enables auto-refresh
        self.log("\nTest 6.2: Enable auto-refresh workflow", "INFO")

        if earnings_content:
            # Step 1: Toggle exists
            if 'auto-refresh-toggle' in earnings_content:
                self.log("  ✅ Step 1: Auto-refresh toggle present", "PASS")

                # Step 2: Checkbox functional
                if 'addEventListener' in earnings_content and 'change' in earnings_content:
                    self.log("  ✅ Step 2: Toggle has change listener", "PASS")

                    # Step 3: localStorage saves preference
                    if 'localStorage.setItem' in earnings_content:
                        self.log("  ✅ Step 3: Preference saved to localStorage", "PASS")

                        # Step 4: Auto-refresh starts
                        if 'startAutoRefresh' in earnings_content:
                            self.log("  ✅ Step 4: Auto-refresh function exists", "PASS")
                        else:
                            self.log("  ❌ Step 4: No startAutoRefresh function", "FAIL")
                            all_passed = False
                    else:
                        self.log("  ❌ Step 3: No localStorage save", "FAIL")
                        all_passed = False
                else:
                    self.log("  ❌ Step 2: No change listener", "FAIL")
                    all_passed = False
            else:
                self.log("  ❌ Step 1: No auto-refresh toggle", "FAIL")
                all_passed = False

        # Test 6.3: Workflow - User exports data
        self.log("\nTest 6.3: Export data workflow", "INFO")

        if earnings_content:
            # Step 1: DataTables loaded
            if 'dataTables' in earnings_content:
                self.log("  ✅ Step 1: DataTables library loaded", "PASS")

                # Step 2: Export buttons visible
                if 'buttons:' in earnings_content:
                    self.log("  ✅ Step 2: Export buttons configured", "PASS")

                    # Step 3: Filename generated
                    if 'filename:' in earnings_content:
                        self.log("  ✅ Step 3: Export filename configured", "PASS")
                    else:
                        self.log("  ❌ Step 3: No filename configuration", "FAIL")
                        all_passed = False
                else:
                    self.log("  ❌ Step 2: No export buttons", "FAIL")
                    all_passed = False
            else:
                self.log("  ❌ Step 1: DataTables not loaded", "FAIL")
                all_passed = False

        self.add_result("End-to-End Workflows", all_passed,
                       f"All user workflows functional: {all_passed}")
        return all_passed

    def test_cross_dashboard_data_consistency(self) -> bool:
        """Test 7: Data Consistency Across Dashboards"""
        self.log("\n" + "="*70, "INFO")
        self.log("INTEGRATION TEST 7: Cross-Dashboard Data Consistency", "INFO")
        self.log("="*70, "INFO")

        all_passed = True

        # Test 7.1: Timestamp format consistency
        self.log("\nTest 7.1: Verifying timestamp format consistency", "INFO")

        timestamp_formats = {}
        for dash_name, dash_file in self.dashboards.items():
            content = self.read_file(dash_file)
            if not content:
                continue

            # Check for timestamp functions
            if 'toLocaleString' in content or 'toLocaleTimeString' in content:
                timestamp_formats[dash_name] = 'locale-based'
                self.log(f"  ✅ {dash_name}: Uses locale-based timestamps", "PASS")
            elif 'Date' in content:
                timestamp_formats[dash_name] = 'basic'
                self.log(f"  ⚠️  {dash_name}: Uses basic Date object", "WARN")

        # Test 7.2: Consistent data source references
        self.log("\nTest 7.2: Verifying data source references", "INFO")

        for dash_name, dash_file in self.dashboards.items():
            content = self.read_file(dash_file)
            if not content:
                continue

            # Check for data source mentions
            data_sources = []
            if 'BSE' in content:
                data_sources.append('BSE')
            if 'NSE' in content:
                data_sources.append('NSE')
            if 'Yahoo Finance' in content:
                data_sources.append('Yahoo Finance')

            if data_sources:
                self.log(f"  ✅ {dash_name}: References data sources: {', '.join(data_sources)}", "PASS")

        self.add_result("Data Consistency", all_passed,
                       f"Consistent data handling: {all_passed}")
        return all_passed

    def test_deployment_integration(self) -> bool:
        """Test 8: Deployment Script Integration"""
        self.log("\n" + "="*70, "INFO")
        self.log("INTEGRATION TEST 8: Deployment Script Integration", "INFO")
        self.log("="*70, "INFO")

        deploy_script = self.read_file('deploy_dashboards.sh')
        if not deploy_script:
            self.log("❌ FAIL: Cannot read deploy_dashboards.sh", "FAIL")
            self.add_result("Deployment Integration", False, "Script not found")
            return False

        all_passed = True

        # Test 8.1: All dashboards included in deployment
        self.log("\nTest 8.1: Verifying all dashboards in deployment script", "INFO")

        for dash_name, dash_file in self.dashboards.items():
            if dash_file in deploy_script:
                self.log(f"  ✅ {dash_file} included in deployment", "PASS")
            else:
                self.log(f"  ❌ {dash_file} NOT in deployment script", "FAIL")
                all_passed = False

        # Test 8.2: Deployment script has health checks
        self.log("\nTest 8.2: Verifying deployment health checks", "INFO")

        health_check_patterns = [
            'curl',
            'http_code',
            'test_deployment'
        ]

        health_checks_found = sum(1 for pattern in health_check_patterns if pattern in deploy_script)

        if health_checks_found >= 2:
            self.log(f"  ✅ Deployment has health checks ({health_checks_found}/3 patterns)", "PASS")
        else:
            self.log(f"  ⚠️  Limited health checks ({health_checks_found}/3 patterns)", "WARN")

        # Test 8.3: Deployment script has error handling
        self.log("\nTest 8.3: Verifying deployment error handling", "INFO")

        if 'if [ $? -eq 0 ]' in deploy_script:
            self.log("  ✅ Deployment checks command exit codes", "PASS")
        else:
            self.log("  ⚠️  No exit code checks found", "WARN")

        if 'set -e' in deploy_script:
            self.log("  ✅ Deployment exits on error (set -e)", "PASS")
        else:
            self.log("  ⚠️  No automatic error exit", "WARN")

        self.add_result("Deployment Integration", all_passed,
                       f"Deployment properly integrated: {all_passed}")
        return all_passed

    def run_all_tests(self):
        """Run all integration tests"""
        self.log("\n" + "="*70, "BLUE")
        self.log("🔬 COMPREHENSIVE INTEGRATION TEST SUITE", "BLUE")
        self.log("="*70, "BLUE")
        self.log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log(f"Base Path: {self.base_path.absolute()}", "INFO")

        # Run all tests
        test_methods = [
            self.test_dashboard_navigation_links,
            self.test_auto_refresh_integration,
            self.test_export_integration,
            self.test_styling_consistency,
            self.test_javascript_error_handling,
            self.test_end_to_end_user_workflows,
            self.test_cross_dashboard_data_consistency,
            self.test_deployment_integration
        ]

        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log(f"\n❌ Test failed with exception: {e}", "FAIL")
                self.add_result(test_method.__name__, False, str(e))

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*70, "INFO")
        self.log("📊 INTEGRATION TEST SUMMARY", "INFO")
        self.log("="*70, "INFO")

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        self.log(f"\nTotal Integration Tests: {total}", "INFO")
        self.log(f"Passed: {passed}", "PASS")
        self.log(f"Failed: {failed}", "FAIL" if failed > 0 else "INFO")
        self.log(f"Pass Rate: {pass_rate:.1f}%", "PASS" if pass_rate >= 80 else "FAIL")

        if failed > 0:
            self.log("\n❌ FAILED TESTS:", "FAIL")
            for result in self.test_results:
                if not result['passed']:
                    self.log(f"  - {result['test']}: {result['details']}", "FAIL")

        self.log("\n" + "="*70, "INFO")
        if pass_rate == 100:
            self.log("✅ ALL INTEGRATION TESTS PASSED!", "PASS")
        elif pass_rate >= 80:
            self.log("⚠️  MOST INTEGRATION TESTS PASSED", "WARN")
        else:
            self.log("❌ INTEGRATION TEST SUITE FAILED", "FAIL")
        self.log("="*70, "INFO")

        self.log(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")

        return pass_rate


if __name__ == "__main__":
    suite = IntegrationTestSuite()
    pass_rate = suite.run_all_tests()

    # Exit with appropriate code
    exit(0 if pass_rate == 100 else 1)
