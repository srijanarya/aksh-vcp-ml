"""
Unit tests for Dashboard for Metrics (Story 5.5)

Tests cover:
- AC5.5.1: Grafana dashboard JSON
- AC5.5.2: Custom HTML dashboard
- AC5.5.3: Real-time metrics display
- AC5.5.4: Historical trend analysis
- AC5.5.5: Alert status panel
- AC5.5.6: Model metadata display
- AC5.5.7: Dashboard deployment
"""

import pytest
import json
import tempfile
from pathlib import Path


class TestGrafanaDashboard:
    """Test AC5.5.1: Grafana dashboard"""

    def test_generate_grafana_dashboard(self):
        """Test Grafana dashboard JSON generation"""
        from monitoring.dashboard import generate_grafana_dashboard

        dashboard_json = generate_grafana_dashboard()

        assert dashboard_json is not None
        assert isinstance(dashboard_json, dict)

    def test_grafana_dashboard_has_panels(self):
        """Test that Grafana dashboard has required panels"""
        from monitoring.dashboard import generate_grafana_dashboard

        dashboard = generate_grafana_dashboard()

        # Should have dashboard key
        assert 'dashboard' in dashboard or 'panels' in dashboard

    def test_grafana_dashboard_valid_json(self):
        """Test that Grafana dashboard is valid JSON"""
        from monitoring.dashboard import generate_grafana_dashboard

        dashboard = generate_grafana_dashboard()

        # Should be serializable to JSON
        json_str = json.dumps(dashboard)
        assert len(json_str) > 0


class TestCustomHTMLDashboard:
    """Test AC5.5.2: Custom HTML dashboard"""

    def test_generate_html_dashboard(self):
        """Test HTML dashboard generation"""
        from monitoring.dashboard import generate_html_dashboard

        html = generate_html_dashboard()

        assert html is not None
        assert isinstance(html, str)
        assert len(html) > 0

    def test_html_dashboard_has_structure(self):
        """Test that HTML dashboard has proper structure"""
        from monitoring.dashboard import generate_html_dashboard

        html = generate_html_dashboard()

        # Should have basic HTML tags
        assert '<!DOCTYPE html>' in html
        assert '<html>' in html
        assert '<body>' in html
        assert '</html>' in html

    def test_html_dashboard_has_title(self):
        """Test that HTML dashboard has title"""
        from monitoring.dashboard import generate_html_dashboard

        html = generate_html_dashboard()

        assert '<title>' in html
        assert 'VCP ML' in html or 'Dashboard' in html

    def test_html_dashboard_has_charts(self):
        """Test that HTML dashboard includes chart references"""
        from monitoring.dashboard import generate_html_dashboard

        html = generate_html_dashboard()

        # Should reference charting library
        assert 'chart' in html.lower() or 'plot' in html.lower()


class TestDashboardSave:
    """Test dashboard file saving"""

    def test_save_grafana_dashboard(self):
        """Test saving Grafana dashboard to file"""
        from monitoring.dashboard import generate_grafana_dashboard

        dashboard = generate_grafana_dashboard()

        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(dashboard, f)
            temp_path = f.name

        try:
            # Verify file exists and is valid
            with open(temp_path, 'r') as f:
                loaded = json.load(f)

            assert loaded == dashboard
        finally:
            Path(temp_path).unlink()

    def test_save_html_dashboard(self):
        """Test saving HTML dashboard to file"""
        from monitoring.dashboard import generate_html_dashboard

        html = generate_html_dashboard()

        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            temp_path = f.name

        try:
            # Verify file exists
            assert Path(temp_path).exists()

            # Verify content
            with open(temp_path, 'r') as f:
                content = f.read()

            assert content == html
        finally:
            Path(temp_path).unlink()


class TestDashboardPanels:
    """Test AC5.5.3: Real-time metrics display"""

    def test_dashboard_has_api_performance_panel(self):
        """Test dashboard includes API performance metrics"""
        from monitoring.dashboard import generate_grafana_dashboard

        dashboard = generate_grafana_dashboard()

        # Convert to string to search
        dashboard_str = json.dumps(dashboard)

        # Should mention latency or performance
        assert 'latency' in dashboard_str.lower() or 'performance' in dashboard_str.lower()

    def test_dashboard_has_model_performance_panel(self):
        """Test dashboard includes model performance metrics"""
        from monitoring.dashboard import generate_grafana_dashboard

        dashboard = generate_grafana_dashboard()
        dashboard_str = json.dumps(dashboard)

        # Should mention F1 or model metrics
        assert 'f1' in dashboard_str.lower() or 'model' in dashboard_str.lower()

    def test_dashboard_has_drift_panel(self):
        """Test dashboard includes drift metrics"""
        from monitoring.dashboard import generate_grafana_dashboard

        dashboard = generate_grafana_dashboard()
        dashboard_str = json.dumps(dashboard)

        # Should mention drift or PSI
        assert 'drift' in dashboard_str.lower() or 'psi' in dashboard_str.lower()


class TestDashboardMetadata:
    """Test AC5.5.6: Model metadata display"""

    def test_html_dashboard_shows_model_info(self):
        """Test that HTML dashboard can show model metadata"""
        from monitoring.dashboard import generate_html_dashboard

        html = generate_html_dashboard(
            model_version="1.0.0",
            model_type="XGBoost",
            training_date="2025-11-01"
        )

        # Should include model info somewhere
        assert '1.0.0' in html or 'version' in html.lower()


class TestDashboardIntegration:
    """Integration tests for dashboard"""

    def test_both_dashboards_generated(self):
        """Test that both Grafana and HTML dashboards can be generated"""
        from monitoring.dashboard import generate_grafana_dashboard, generate_html_dashboard

        grafana = generate_grafana_dashboard()
        html = generate_html_dashboard()

        assert grafana is not None
        assert html is not None
        assert isinstance(grafana, dict)
        assert isinstance(html, str)

    def test_dashboards_directory_structure(self):
        """Test creating dashboard directory structure"""
        from monitoring.dashboard import create_dashboard_files

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dashboard files
            create_dashboard_files(output_dir=tmpdir)

            # Verify files exist
            dashboards_dir = Path(tmpdir)

            # Check for subdirectories
            grafana_dir = dashboards_dir / "grafana"
            custom_dir = dashboards_dir / "custom"

            assert grafana_dir.exists()
            assert custom_dir.exists()

            # Check if dashboard files were created
            files = list(grafana_dir.glob('*.json')) + list(custom_dir.glob('*.html'))
            assert len(files) >= 2  # At least Grafana JSON and HTML dashboard
