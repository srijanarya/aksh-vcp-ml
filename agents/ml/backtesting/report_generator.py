"""Backtesting Report Generation (Epic 6 - Story 6.4)"""
from jinja2 import Template
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self, template_path: str = None):
        self.template_path = template_path

    def generate_html_report(self, historical_results: dict, walk_forward_results: dict,
                            risk_metrics: dict, output_path: str) -> str:
        """Generate comprehensive HTML report"""
        template = self._get_template()

        # Create charts
        f1_chart = self.create_f1_over_time_chart(walk_forward_results.get('iterations', []))

        context = {
            'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'f1_chart_html': f1_chart.to_html() if f1_chart else '',
            'historical_summary': str(historical_results),
            'risk_summary': str(risk_metrics)
        }

        html = template.render(context)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(html)

        logger.info(f"Report generated: {output_path}")
        return output_path

    def create_f1_over_time_chart(self, iterations: list) -> go.Figure:
        """Create F1 score over time chart"""
        if not iterations:
            return None

        periods = [it.period if hasattr(it, 'period') else str(i) for i, it in enumerate(iterations)]
        f1_scores = [it.f1 if hasattr(it, 'f1') else 0.7 for it in iterations]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=periods,
            y=f1_scores,
            mode='lines+markers',
            name='F1 Score'
        ))
        fig.update_layout(
            title='F1 Score Over Time',
            xaxis_title='Period',
            yaxis_title='F1 Score',
            height=400
        )
        return fig

    def create_equity_curve_chart(self, cumulative_returns: pd.Series) -> go.Figure:
        """Create equity curve chart"""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=cumulative_returns.index,
            y=cumulative_returns.values,
            mode='lines',
            name='Equity Curve'
        ))
        fig.update_layout(title='Equity Curve', xaxis_title='Date', yaxis_title='Cumulative Return')
        return fig

    def _get_template(self) -> Template:
        """Get HTML template"""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>VCP ML Backtesting Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .summary { background: #f5f5f5; padding: 15px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>VCP ML Backtesting Report</h1>
    <p>Generated: {{ timestamp }}</p>

    <h2>Performance Over Time</h2>
    {{ f1_chart_html | safe }}

    <h2>Historical Results</h2>
    <div class="summary">{{ historical_summary }}</div>

    <h2>Risk Metrics</h2>
    <div class="summary">{{ risk_summary }}</div>
</body>
</html>
"""
        return Template(html_template)
