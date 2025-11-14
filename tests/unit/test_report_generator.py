"""Tests for Backtesting Report Generation (Epic 6 - Story 6.4)"""
import pytest
import pandas as pd
import tempfile
from pathlib import Path
from agents.ml.backtesting.report_generator import ReportGenerator

class TestReportGenerator:
    @pytest.fixture
    def generator(self):
        return ReportGenerator()

    @pytest.fixture
    def temp_output(self):
        temp_dir = tempfile.mkdtemp()
        return str(Path(temp_dir) / "report.html")

    def test_initialization(self, generator):
        assert generator is not None

    def test_generate_html_report(self, generator, temp_output):
        html_path = generator.generate_html_report({}, {}, {}, temp_output)
        assert Path(html_path).exists()

    def test_report_contains_title(self, generator, temp_output):
        generator.generate_html_report({}, {}, {}, temp_output)
        with open(temp_output) as f:
            content = f.read()
            assert 'VCP ML Backtesting Report' in content

    def test_create_f1_chart(self, generator):
        from agents.ml.backtesting.walk_forward_validator import WalkForwardIteration
        iterations = [
            WalkForwardIteration('2023-01', '2022-01-01', '2023-01-01', '2023-01-01', '2023-01-31', 0.70, 0.67, 0.74, 1200, 2.5)
        ]
        chart = generator.create_f1_over_time_chart(iterations)
        assert chart is not None

    def test_create_equity_curve(self, generator):
        returns = pd.Series([1.0, 1.1, 1.05, 1.15], index=pd.date_range('2023-01-01', periods=4))
        chart = generator.create_equity_curve_chart(returns)
        assert chart is not None

    def test_empty_iterations(self, generator):
        chart = generator.create_f1_over_time_chart([])
        assert chart is None

    def test_report_has_timestamp(self, generator, temp_output):
        generator.generate_html_report({}, {}, {}, temp_output)
        with open(temp_output) as f:
            content = f.read()
            assert 'Generated:' in content

    def test_report_has_sections(self, generator, temp_output):
        generator.generate_html_report({}, {}, {}, temp_output)
        with open(temp_output) as f:
            content = f.read()
            assert 'Performance Over Time' in content
            assert 'Historical Results' in content
            assert 'Risk Metrics' in content

    def test_template_rendering(self, generator):
        template = generator._get_template()
        assert template is not None

    def test_chart_with_multiple_points(self, generator):
        from agents.ml.backtesting.walk_forward_validator import WalkForwardIteration
        iterations = [
            WalkForwardIteration(f'2023-{i:02d}', '2022-01-01', '2023-01-01', '2023-01-01', '2023-01-31', 0.70+i*0.01, 0.67, 0.74, 1200, 2.5)
            for i in range(1, 6)
        ]
        chart = generator.create_f1_over_time_chart(iterations)
        assert chart is not None

    def test_output_path_creation(self, generator):
        import tempfile
        temp_dir = Path(tempfile.mkdtemp())
        output_path = str(temp_dir / "subdir" / "report.html")
        generator.generate_html_report({}, {}, {}, output_path)
        assert Path(output_path).exists()

    def test_html_validity(self, generator, temp_output):
        generator.generate_html_report({}, {}, {}, temp_output)
        with open(temp_output) as f:
            content = f.read()
            assert '<!DOCTYPE html>' in content
            assert '</html>' in content

    def test_report_with_results(self, generator, temp_output):
        results = {'2024': {'f1': 0.72}}
        generator.generate_html_report(results, {}, {}, temp_output)
        assert Path(temp_output).exists()

    def test_report_with_walk_forward(self, generator, temp_output):
        wf_results = {'iterations': []}
        generator.generate_html_report({}, wf_results, {}, temp_output)
        assert Path(temp_output).exists()

    def test_report_with_risk_metrics(self, generator, temp_output):
        risk = {'sharpe': 1.5, 'max_drawdown': -0.15}
        generator.generate_html_report({}, {}, risk, temp_output)
        assert Path(temp_output).exists()
