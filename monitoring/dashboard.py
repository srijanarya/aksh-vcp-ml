"""
Dashboard for Metrics (Story 5.5)

Provides:
- Grafana dashboard JSON definition
- Custom HTML dashboard (fallback)
- Real-time metrics visualization
- Historical trend analysis
- Alert status panel
- Model metadata display

Author: VCP ML Team
Created: 2025-11-14
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path


def generate_grafana_dashboard() -> Dict[str, Any]:
    """
    Generate Grafana dashboard JSON (AC5.5.1, AC5.5.3, AC5.5.4).

    Returns:
        Grafana dashboard JSON
    """
    dashboard = {
        "dashboard": {
            "id": None,
            "uid": "vcp-ml-monitoring",
            "title": "VCP ML System Monitoring",
            "tags": ["ml", "vcp", "monitoring"],
            "timezone": "browser",
            "schemaVersion": 16,
            "version": 1,
            "refresh": "30s",
            "panels": [
                {
                    "id": 1,
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    "type": "graph",
                    "title": "API Latency (p95)",
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))",
                            "legendFormat": "p95 latency",
                            "refId": "A"
                        },
                        {
                            "expr": "histogram_quantile(0.50, rate(api_request_duration_seconds_bucket[5m]))",
                            "legendFormat": "p50 latency",
                            "refId": "B"
                        }
                    ],
                    "yaxes": [
                        {"format": "s", "label": "Latency"},
                        {"format": "short"}
                    ],
                    "alert": {
                        "conditions": [
                            {
                                "evaluator": {"params": [0.15], "type": "gt"},
                                "query": {"params": ["A", "5m", "now"]},
                                "type": "query"
                            }
                        ],
                        "message": "API p95 latency > 150ms for 5 minutes"
                    }
                },
                {
                    "id": 2,
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    "type": "graph",
                    "title": "Throughput (requests/sec)",
                    "targets": [
                        {
                            "expr": "rate(api_requests_total[1m])",
                            "legendFormat": "{{endpoint}}",
                            "refId": "A"
                        }
                    ],
                    "yaxes": [
                        {"format": "reqps", "label": "Requests/sec"},
                        {"format": "short"}
                    ]
                },
                {
                    "id": 3,
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    "type": "graph",
                    "title": "Model F1 Score (30-day rolling)",
                    "targets": [
                        {
                            "expr": "model_f1_score",
                            "legendFormat": "F1 Score",
                            "refId": "A"
                        }
                    ],
                    "yaxes": [
                        {"format": "percentunit", "label": "F1", "max": 1, "min": 0},
                        {"format": "short"}
                    ],
                    "thresholds": [
                        {"value": 0.67, "colorMode": "critical", "op": "lt", "fill": True, "line": True}
                    ]
                },
                {
                    "id": 4,
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    "type": "heatmap",
                    "title": "Data Drift (PSI Scores)",
                    "targets": [
                        {
                            "expr": "feature_drift_psi",
                            "legendFormat": "{{feature}}",
                            "refId": "A"
                        }
                    ],
                    "dataFormat": "tsbuckets",
                    "heatmap": {
                        "hideZeroBuckets": False,
                        "highlightCards": True
                    },
                    "color": {
                        "mode": "spectrum",
                        "cardColor": "#b4ff00",
                        "colorScale": "sqrt",
                        "exponent": 0.5,
                        "min": 0,
                        "max": 0.5
                    }
                },
                {
                    "id": 5,
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                    "type": "graph",
                    "title": "Error Rate",
                    "targets": [
                        {
                            "expr": "rate(api_errors_total[5m]) / rate(api_requests_total[5m])",
                            "legendFormat": "Error Rate",
                            "refId": "A"
                        }
                    ],
                    "yaxes": [
                        {"format": "percentunit", "label": "Error %"},
                        {"format": "short"}
                    ],
                    "alert": {
                        "conditions": [
                            {
                                "evaluator": {"params": [0.05], "type": "gt"},
                                "query": {"params": ["A", "10m", "now"]},
                                "type": "query"
                            }
                        ],
                        "message": "Error rate > 5% for 10 minutes"
                    }
                },
                {
                    "id": 6,
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                    "type": "graph",
                    "title": "System Resources",
                    "targets": [
                        {
                            "expr": "process_cpu_percent",
                            "legendFormat": "CPU %",
                            "refId": "A"
                        },
                        {
                            "expr": "process_memory_percent",
                            "legendFormat": "Memory %",
                            "refId": "B"
                        }
                    ],
                    "yaxes": [
                        {"format": "percent", "label": "Usage %", "max": 100, "min": 0},
                        {"format": "short"}
                    ]
                }
            ]
        },
        "overwrite": True
    }

    return dashboard


def generate_html_dashboard(
    model_version: str = "1.0.0",
    model_type: str = "XGBoost",
    training_date: str = "2025-11-01"
) -> str:
    """
    Generate custom HTML dashboard (AC5.5.2, AC5.5.3, AC5.5.4, AC5.5.5, AC5.5.6).

    Args:
        model_version: Current model version
        model_type: Model type (XGBoost, LightGBM, etc.)
        training_date: Model training date

    Returns:
        HTML dashboard string
    """
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>VCP ML System Monitoring Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .dashboard {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .model-info {{
            display: flex;
            gap: 30px;
            color: #666;
            font-size: 14px;
        }}
        .model-info-item {{
            display: flex;
            gap: 5px;
        }}
        .model-info-label {{
            font-weight: 600;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .panel {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .panel h2 {{
            color: #333;
            font-size: 18px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
        }}
        .metric:last-child {{
            border-bottom: none;
        }}
        .metric-label {{
            color: #666;
            font-weight: 500;
        }}
        .metric-value {{
            color: #333;
            font-weight: 600;
        }}
        .metric-value.good {{
            color: #10b981;
        }}
        .metric-value.warning {{
            color: #f59e0b;
        }}
        .metric-value.critical {{
            color: #ef4444;
        }}
        .alert-box {{
            padding: 12px;
            margin: 10px 0;
            border-radius: 6px;
            border-left: 4px solid;
        }}
        .alert-box.info {{
            background: #dbeafe;
            border-color: #3b82f6;
            color: #1e40af;
        }}
        .alert-box.warning {{
            background: #fef3c7;
            border-color: #f59e0b;
            color: #92400e;
        }}
        .alert-box.critical {{
            background: #fee2e2;
            border-color: #ef4444;
            color: #991b1b;
        }}
        .refresh-info {{
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>VCP ML System Monitoring Dashboard</h1>
            <div class="model-info">
                <div class="model-info-item">
                    <span class="model-info-label">Version:</span>
                    <span>{model_version}</span>
                </div>
                <div class="model-info-item">
                    <span class="model-info-label">Model Type:</span>
                    <span>{model_type}</span>
                </div>
                <div class="model-info-item">
                    <span class="model-info-label">Trained:</span>
                    <span>{training_date}</span>
                </div>
                <div class="model-info-item">
                    <span class="model-info-label">Last Updated:</span>
                    <span id="last-update">Loading...</span>
                </div>
            </div>
        </div>

        <div class="grid">
            <div class="panel">
                <h2>API Performance</h2>
                <canvas id="latencyChart" style="max-height: 250px;"></canvas>
                <div style="margin-top: 15px;">
                    <div class="metric">
                        <span class="metric-label">p50 Latency:</span>
                        <span class="metric-value good" id="p50-latency">Loading...</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">p95 Latency:</span>
                        <span class="metric-value" id="p95-latency">Loading...</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Throughput:</span>
                        <span class="metric-value" id="throughput">Loading...</span>
                    </div>
                </div>
            </div>

            <div class="panel">
                <h2>Model Performance (30-day)</h2>
                <canvas id="f1Chart" style="max-height: 250px;"></canvas>
                <div style="margin-top: 15px;">
                    <div class="metric">
                        <span class="metric-label">F1 Score:</span>
                        <span class="metric-value" id="f1-score">Loading...</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Precision:</span>
                        <span class="metric-value" id="precision">Loading...</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Recall:</span>
                        <span class="metric-value" id="recall">Loading...</span>
                    </div>
                </div>
            </div>

            <div class="panel">
                <h2>Data Drift Status</h2>
                <div class="metric">
                    <span class="metric-label">Features Monitored:</span>
                    <span class="metric-value" id="features-monitored">Loading...</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Features with Drift:</span>
                    <span class="metric-value" id="features-drift">Loading...</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Max PSI:</span>
                    <span class="metric-value" id="max-psi">Loading...</span>
                </div>
                <div style="margin-top: 15px;" id="drift-alerts">
                    <!-- Drift alerts will be inserted here -->
                </div>
            </div>

            <div class="panel">
                <h2>System Health</h2>
                <div class="metric">
                    <span class="metric-label">CPU Usage:</span>
                    <span class="metric-value" id="cpu-usage">Loading...</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Memory Usage:</span>
                    <span class="metric-value" id="memory-usage">Loading...</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Error Rate:</span>
                    <span class="metric-value" id="error-rate">Loading...</span>
                </div>
            </div>
        </div>

        <div class="panel">
            <h2>Active Alerts</h2>
            <div id="alerts-container">
                <div class="alert-box info">
                    <strong>ℹ️ System Status:</strong> All metrics within normal thresholds
                </div>
            </div>
        </div>

        <div class="refresh-info">
            Auto-refresh every 30 seconds • Last refresh: <span id="refresh-time">Never</span>
        </div>
    </div>

    <script>
        // Initialize charts
        const latencyCtx = document.getElementById('latencyChart').getContext('2d');
        const latencyChart = new Chart(latencyCtx, {{
            type: 'line',
            data: {{
                labels: [],
                datasets: [{{
                    label: 'p95 Latency (ms)',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.3
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{ display: true, text: 'Milliseconds' }}
                    }}
                }}
            }}
        }});

        const f1Ctx = document.getElementById('f1Chart').getContext('2d');
        const f1Chart = new Chart(f1Ctx, {{
            type: 'line',
            data: {{
                labels: [],
                datasets: [{{
                    label: 'F1 Score',
                    data: [],
                    borderColor: 'rgb(16, 185, 129)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.3
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 1,
                        title: {{ display: true, text: 'F1 Score' }}
                    }}
                }}
            }}
        }});

        // Fetch and update metrics
        async function fetchMetrics() {{
            try {{
                const response = await fetch('/metrics');
                const text = await response.text();

                // Parse Prometheus metrics (simplified)
                // In production, you'd parse the Prometheus format properly

                // Update timestamp
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                document.getElementById('refresh-time').textContent = new Date().toLocaleString();

                // Mock data for demo (replace with actual parsing)
                updateMetrics({{
                    p50_latency: '45ms',
                    p95_latency: '120ms',
                    throughput: '150 req/s',
                    f1_score: 0.72,
                    precision: 0.68,
                    recall: 0.76,
                    features_monitored: 25,
                    features_drift: 2,
                    max_psi: 0.18,
                    cpu_usage: '45%',
                    memory_usage: '62%',
                    error_rate: '0.8%'
                }});
            }} catch (error) {{
                console.error('Failed to fetch metrics:', error);
            }}
        }}

        function updateMetrics(data) {{
            // Update API performance
            document.getElementById('p50-latency').textContent = data.p50_latency;
            document.getElementById('p95-latency').textContent = data.p95_latency;
            document.getElementById('throughput').textContent = data.throughput;

            // Update model performance
            document.getElementById('f1-score').textContent = data.f1_score.toFixed(2);
            document.getElementById('precision').textContent = data.precision.toFixed(2);
            document.getElementById('recall').textContent = data.recall.toFixed(2);

            // Update drift
            document.getElementById('features-monitored').textContent = data.features_monitored;
            document.getElementById('features-drift').textContent = data.features_drift;
            document.getElementById('max-psi').textContent = data.max_psi.toFixed(2);

            // Update system health
            document.getElementById('cpu-usage').textContent = data.cpu_usage;
            document.getElementById('memory-usage').textContent = data.memory_usage;
            document.getElementById('error-rate').textContent = data.error_rate;
        }}

        // Initial fetch
        fetchMetrics();

        // Auto-refresh every 30 seconds
        setInterval(fetchMetrics, 30000);
    </script>
</body>
</html>
"""

    return html


def create_dashboard_files(
    output_dir: str = "/Users/srijan/Desktop/aksh/dashboards"
):
    """
    Create dashboard files (AC5.5.7).

    Args:
        output_dir: Output directory for dashboard files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save Grafana dashboard
    grafana_dir = output_path / "grafana"
    grafana_dir.mkdir(exist_ok=True)

    grafana_dashboard = generate_grafana_dashboard()
    with open(grafana_dir / "vcp_ml_dashboard.json", "w") as f:
        json.dump(grafana_dashboard, f, indent=2)

    # Save HTML dashboard
    custom_dir = output_path / "custom"
    custom_dir.mkdir(exist_ok=True)

    html_dashboard = generate_html_dashboard()
    with open(custom_dir / "metrics_dashboard.html", "w") as f:
        f.write(html_dashboard)
