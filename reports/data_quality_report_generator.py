"""
Data Quality Report Generator
Creates comprehensive, formatted reports on data validation and quality metrics
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import json
from pathlib import Path

from data_sources.validation_database import ValidationDatabase
from utils.fiscal_year_utils import DataTimestamp, IndianFiscalYear


class DataQualityReportGenerator:
    """
    Generates comprehensive data quality reports in multiple formats
    """

    def __init__(self, db_path: str = None, output_dir: str = "quality_reports"):
        """
        Initialize report generator

        Args:
            db_path: Path to validation database
            output_dir: Directory for report output
        """
        self.db = ValidationDatabase(db_path or "data_validation.db")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_comprehensive_report(self, company_code: str = None,
                                     period_days: int = 7,
                                     format: str = 'all') -> Dict[str, str]:
        """
        Generate comprehensive data quality report

        Args:
            company_code: Optional company filter
            period_days: Period to analyze
            format: Output format ('html', 'markdown', 'json', 'all')

        Returns:
            Dictionary with paths to generated reports
        """
        # Gather report data
        report_data = self._gather_report_data(company_code, period_days)

        # Generate timestamp for filenames
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        prefix = f"{company_code}_" if company_code else "system_"

        generated_files = {}

        # Generate reports in requested formats
        if format in ['html', 'all']:
            html_path = self._generate_html_report(report_data, timestamp_str, prefix)
            generated_files['html'] = html_path

        if format in ['markdown', 'all']:
            md_path = self._generate_markdown_report(report_data, timestamp_str, prefix)
            generated_files['markdown'] = md_path

        if format in ['json', 'all']:
            json_path = self._generate_json_report(report_data, timestamp_str, prefix)
            generated_files['json'] = json_path

        return generated_files

    def _gather_report_data(self, company_code: Optional[str], period_days: int) -> Dict:
        """
        Gather all data needed for the report

        Args:
            company_code: Optional company filter
            period_days: Period to analyze

        Returns:
            Complete report data
        """
        report_data = {
            'metadata': {
                'generated_at': DataTimestamp.create_timestamp(),
                'report_type': 'company' if company_code else 'system-wide',
                'company_code': company_code,
                'period_days': period_days,
                'period_start': (datetime.now() - timedelta(days=period_days)).isoformat(),
                'period_end': datetime.now().isoformat()
            }
        }

        # Get quality trends
        report_data['quality_trends'] = self.db.get_quality_trends(company_code, period_days)

        # Get confidence history
        if company_code:
            report_data['confidence_history'] = self.db.get_confidence_history(company_code, period_days)
            report_data['latest_validation'] = self.db.get_latest_validation(company_code)
        else:
            report_data['confidence_history'] = self._get_system_confidence_history(period_days)

        # Get discrepancy analysis
        report_data['discrepancies'] = self._analyze_discrepancies(company_code, period_days)

        # Get source reliability analysis
        report_data['source_reliability'] = self._analyze_source_reliability(company_code, period_days)

        # Get validation statistics
        report_data['validation_stats'] = self._get_validation_statistics(company_code, period_days)

        # Get recommendations
        report_data['recommendations'] = self._generate_recommendations(report_data)

        return report_data

    def _analyze_discrepancies(self, company_code: Optional[str], period_days: int) -> Dict:
        """Analyze discrepancies in the data"""
        discrepancies = self.db.get_discrepancy_report(company_code, threshold_pct=5.0)

        analysis = {
            'total_discrepancies': len(discrepancies),
            'by_severity': {
                'critical': [],  # > 50% discrepancy
                'high': [],      # 20-50% discrepancy
                'medium': [],    # 10-20% discrepancy
                'low': []        # 5-10% discrepancy
            },
            'by_metric': {},
            'top_issues': []
        }

        for disc in discrepancies:
            disc_pct = disc.get('discrepancy_pct', 0)

            # Categorize by severity
            if disc_pct > 50:
                analysis['by_severity']['critical'].append(disc)
            elif disc_pct > 20:
                analysis['by_severity']['high'].append(disc)
            elif disc_pct > 10:
                analysis['by_severity']['medium'].append(disc)
            else:
                analysis['by_severity']['low'].append(disc)

            # Count by metric
            metric = disc.get('metric_name', 'unknown')
            if metric not in analysis['by_metric']:
                analysis['by_metric'][metric] = {'count': 0, 'avg_discrepancy': 0, 'max_discrepancy': 0}

            analysis['by_metric'][metric]['count'] += 1
            analysis['by_metric'][metric]['max_discrepancy'] = max(
                analysis['by_metric'][metric]['max_discrepancy'],
                disc_pct
            )

        # Identify top issues
        critical_issues = analysis['by_severity']['critical'][:5]
        for issue in critical_issues:
            analysis['top_issues'].append({
                'company': issue.get('company_code'),
                'metric': issue.get('metric_name'),
                'discrepancy': issue.get('discrepancy_pct'),
                'sources': f"{issue.get('source_1')} vs {issue.get('source_2')}",
                'resolution': issue.get('resolution', 'Pending review')
            })

        return analysis

    def _analyze_source_reliability(self, company_code: Optional[str], period_days: int) -> Dict:
        """Analyze reliability of different data sources"""
        cursor = self.db.conn.cursor()

        query = """
            SELECT
                source_name,
                COUNT(*) as total_fetches,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors
            FROM source_tracking
            WHERE fetch_timestamp >= datetime('now', '-{} days')
        """.format(period_days)

        if company_code:
            query += f" AND company_code = '{company_code}'"

        query += " GROUP BY source_name"

        cursor.execute(query)
        results = cursor.fetchall()

        reliability = {}
        for row in results:
            source, total, successful, errors = row
            reliability[source] = {
                'total_attempts': total,
                'successful': successful,
                'errors': errors,
                'success_rate': (successful / total * 100) if total > 0 else 0,
                'reliability_score': self._calculate_reliability_score(successful, total, errors)
            }

        return reliability

    def _calculate_reliability_score(self, successful: int, total: int, errors: int) -> float:
        """Calculate reliability score for a data source"""
        if total == 0:
            return 0

        base_score = (successful / total) * 100

        # Penalize for errors
        error_penalty = min(30, errors * 5)
        score = base_score - error_penalty

        return max(0, min(100, score))

    def _get_validation_statistics(self, company_code: Optional[str], period_days: int) -> Dict:
        """Get validation statistics"""
        cursor = self.db.conn.cursor()

        stats = {}

        # Total validations
        query = """
            SELECT COUNT(*) FROM validation_results
            WHERE validation_timestamp >= datetime('now', '-{} days')
        """.format(period_days)

        if company_code:
            query += f" AND company_code = '{company_code}'"

        cursor.execute(query)
        stats['total_validations'] = cursor.fetchone()[0]

        # Average confidence
        query = """
            SELECT AVG(confidence_score) FROM validation_results
            WHERE validation_timestamp >= datetime('now', '-{} days')
        """.format(period_days)

        if company_code:
            query += f" AND company_code = '{company_code}'"

        cursor.execute(query)
        result = cursor.fetchone()
        stats['avg_confidence'] = result[0] if result[0] else 0

        # Confidence distribution
        query = """
            SELECT
                SUM(CASE WHEN confidence_score >= 80 THEN 1 ELSE 0 END) as high,
                SUM(CASE WHEN confidence_score >= 60 AND confidence_score < 80 THEN 1 ELSE 0 END) as medium,
                SUM(CASE WHEN confidence_score < 60 THEN 1 ELSE 0 END) as low
            FROM validation_results
            WHERE validation_timestamp >= datetime('now', '-{} days')
        """.format(period_days)

        if company_code:
            query += f" AND company_code = '{company_code}'"

        cursor.execute(query)
        result = cursor.fetchone()
        stats['confidence_distribution'] = {
            'high': result[0] or 0,
            'medium': result[1] or 0,
            'low': result[2] or 0
        }

        return stats

    def _get_system_confidence_history(self, period_days: int) -> List[Dict]:
        """Get system-wide confidence history"""
        cursor = self.db.conn.cursor()

        query = """
            SELECT
                DATE(timestamp) as date,
                AVG(overall_confidence) as avg_confidence,
                COUNT(DISTINCT company_code) as companies
            FROM confidence_scores
            WHERE timestamp >= datetime('now', '-{} days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """.format(period_days)

        cursor.execute(query)
        results = cursor.fetchall()

        history = []
        for row in results:
            history.append({
                'date': row[0],
                'avg_confidence': row[1],
                'companies_validated': row[2]
            })

        return history

    def _generate_recommendations(self, report_data: Dict) -> List[str]:
        """Generate actionable recommendations based on report data"""
        recommendations = []

        # Check overall confidence
        avg_confidence = report_data.get('validation_stats', {}).get('avg_confidence', 0)
        if avg_confidence < 60:
            recommendations.append("🚨 CRITICAL: Average data confidence is below 60%. Investigate data sources immediately.")
        elif avg_confidence < 80:
            recommendations.append("⚠️ WARNING: Average data confidence is moderate. Consider adding more data sources.")

        # Check discrepancies
        discrepancy_data = report_data.get('discrepancies', {})
        critical_count = len(discrepancy_data.get('by_severity', {}).get('critical', []))
        if critical_count > 0:
            recommendations.append(f"🔍 Found {critical_count} critical discrepancies (>50%). Manual review required.")

        # Check source reliability
        source_data = report_data.get('source_reliability', {})
        for source, reliability in source_data.items():
            if reliability.get('success_rate', 100) < 80:
                recommendations.append(f"📡 {source} has low success rate ({reliability['success_rate']:.1f}%). Check API/scraper.")

        # Check data freshness
        if report_data.get('latest_validation'):
            latest_time = report_data['latest_validation'].get('validation_timestamp')
            if latest_time:
                age_hours = (datetime.now() - pd.to_datetime(latest_time)).total_seconds() / 3600
                if age_hours > 24:
                    recommendations.append(f"📅 Latest validation is {age_hours:.0f} hours old. Run fresh validation.")

        # Provide positive feedback if all is well
        if not recommendations:
            recommendations.append("✅ Data quality metrics are within acceptable ranges.")
            recommendations.append("✅ All data sources are functioning properly.")
            recommendations.append("✅ No critical discrepancies detected.")

        return recommendations

    def _generate_html_report(self, report_data: Dict, timestamp: str, prefix: str) -> str:
        """Generate HTML format report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Data Quality Report - {timestamp}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 1px solid #ecf0f1;
            padding-bottom: 5px;
        }}
        .metric {{
            display: inline-block;
            margin: 10px;
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 5px;
            min-width: 150px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2980b9;
        }}
        .metric-label {{
            font-size: 12px;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 10px;
            text-align: left;
        }}
        td {{
            padding: 8px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .high-confidence {{
            background-color: #d4edda;
        }}
        .medium-confidence {{
            background-color: #fff3cd;
        }}
        .low-confidence {{
            background-color: #f8d7da;
        }}
        .recommendation {{
            padding: 10px;
            margin: 10px 0;
            border-left: 4px solid #3498db;
            background-color: #e8f4fd;
        }}
        .timestamp {{
            color: #95a5a6;
            font-size: 12px;
            text-align: right;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Data Quality Report</h1>
        <p><strong>Type:</strong> {report_data['metadata']['report_type']}</p>
        <p><strong>Period:</strong> {report_data['metadata']['period_start']} to {report_data['metadata']['period_end']}</p>
        """

        # Add validation statistics
        stats = report_data.get('validation_stats', {})
        html_content += f"""
        <h2>📈 Validation Statistics</h2>
        <div>
            <div class="metric">
                <div class="metric-value">{stats.get('total_validations', 0)}</div>
                <div class="metric-label">Total Validations</div>
            </div>
            <div class="metric">
                <div class="metric-value">{stats.get('avg_confidence', 0):.1f}%</div>
                <div class="metric-label">Average Confidence</div>
            </div>
            <div class="metric">
                <div class="metric-value">{stats.get('confidence_distribution', {}).get('high', 0)}</div>
                <div class="metric-label">High Confidence</div>
            </div>
            <div class="metric">
                <div class="metric-value">{stats.get('confidence_distribution', {}).get('medium', 0)}</div>
                <div class="metric-label">Medium Confidence</div>
            </div>
            <div class="metric">
                <div class="metric-value">{stats.get('confidence_distribution', {}).get('low', 0)}</div>
                <div class="metric-label">Low Confidence</div>
            </div>
        </div>
        """

        # Add source reliability
        html_content += """
        <h2>🔌 Data Source Reliability</h2>
        <table>
            <tr>
                <th>Source</th>
                <th>Success Rate</th>
                <th>Total Attempts</th>
                <th>Errors</th>
                <th>Reliability Score</th>
            </tr>
        """

        for source, data in report_data.get('source_reliability', {}).items():
            html_content += f"""
            <tr>
                <td>{source}</td>
                <td>{data.get('success_rate', 0):.1f}%</td>
                <td>{data.get('total_attempts', 0)}</td>
                <td>{data.get('errors', 0)}</td>
                <td>{data.get('reliability_score', 0):.1f}</td>
            </tr>
            """

        html_content += "</table>"

        # Add discrepancy analysis
        discrepancies = report_data.get('discrepancies', {})
        html_content += f"""
        <h2>🔍 Discrepancy Analysis</h2>
        <p>Total Discrepancies: {discrepancies.get('total_discrepancies', 0)}</p>
        """

        if discrepancies.get('top_issues'):
            html_content += """
            <table>
                <tr>
                    <th>Company</th>
                    <th>Metric</th>
                    <th>Discrepancy %</th>
                    <th>Sources</th>
                    <th>Resolution</th>
                </tr>
            """
            for issue in discrepancies['top_issues']:
                html_content += f"""
                <tr>
                    <td>{issue.get('company', 'N/A')}</td>
                    <td>{issue.get('metric', 'N/A')}</td>
                    <td>{issue.get('discrepancy', 0):.1f}%</td>
                    <td>{issue.get('sources', 'N/A')}</td>
                    <td>{issue.get('resolution', 'Pending')}</td>
                </tr>
                """
            html_content += "</table>"

        # Add recommendations
        html_content += "<h2>💡 Recommendations</h2>"
        for rec in report_data.get('recommendations', []):
            html_content += f'<div class="recommendation">{rec}</div>'

        # Add footer
        html_content += f"""
        <div class="timestamp">
            Generated: {report_data['metadata']['generated_at']['timestamp']}
        </div>
    </div>
</body>
</html>
        """

        # Save file
        file_path = self.output_dir / f"{prefix}quality_report_{timestamp}.html"
        file_path.write_text(html_content)

        return str(file_path)

    def _generate_markdown_report(self, report_data: Dict, timestamp: str, prefix: str) -> str:
        """Generate Markdown format report"""
        md_content = f"""# 📊 Data Quality Report

**Generated:** {report_data['metadata']['generated_at']['timestamp']}
**Type:** {report_data['metadata']['report_type']}
**Period:** {report_data['metadata']['period_start']} to {report_data['metadata']['period_end']}

---

## 📈 Validation Statistics

"""
        stats = report_data.get('validation_stats', {})
        md_content += f"""
| Metric | Value |
|--------|-------|
| Total Validations | {stats.get('total_validations', 0)} |
| Average Confidence | {stats.get('avg_confidence', 0):.1f}% |
| High Confidence Count | {stats.get('confidence_distribution', {}).get('high', 0)} |
| Medium Confidence Count | {stats.get('confidence_distribution', {}).get('medium', 0)} |
| Low Confidence Count | {stats.get('confidence_distribution', {}).get('low', 0)} |

## 🔌 Data Source Reliability

| Source | Success Rate | Attempts | Errors | Reliability |
|--------|-------------|----------|--------|-------------|
"""

        for source, data in report_data.get('source_reliability', {}).items():
            md_content += f"| {source} | {data.get('success_rate', 0):.1f}% | {data.get('total_attempts', 0)} | {data.get('errors', 0)} | {data.get('reliability_score', 0):.1f} |\n"

        # Add discrepancy analysis
        discrepancies = report_data.get('discrepancies', {})
        md_content += f"""

## 🔍 Discrepancy Analysis

**Total Discrepancies:** {discrepancies.get('total_discrepancies', 0)}

### Severity Distribution
- Critical (>50%): {len(discrepancies.get('by_severity', {}).get('critical', []))}
- High (20-50%): {len(discrepancies.get('by_severity', {}).get('high', []))}
- Medium (10-20%): {len(discrepancies.get('by_severity', {}).get('medium', []))}
- Low (5-10%): {len(discrepancies.get('by_severity', {}).get('low', []))}

"""

        if discrepancies.get('top_issues'):
            md_content += """### Top Issues

| Company | Metric | Discrepancy | Sources | Resolution |
|---------|--------|-------------|---------|------------|
"""
            for issue in discrepancies['top_issues']:
                md_content += f"| {issue.get('company', 'N/A')} | {issue.get('metric', 'N/A')} | {issue.get('discrepancy', 0):.1f}% | {issue.get('sources', 'N/A')} | {issue.get('resolution', 'Pending')} |\n"

        # Add recommendations
        md_content += "\n## 💡 Recommendations\n\n"
        for rec in report_data.get('recommendations', []):
            md_content += f"- {rec}\n"

        # Add footer
        md_content += f"""

---

*Report generated by Data Quality Report Generator v1.0*
*Timestamp: {timestamp}*
"""

        # Save file
        file_path = self.output_dir / f"{prefix}quality_report_{timestamp}.md"
        file_path.write_text(md_content)

        return str(file_path)

    def _generate_json_report(self, report_data: Dict, timestamp: str, prefix: str) -> str:
        """Generate JSON format report"""
        # Save file
        file_path = self.output_dir / f"{prefix}quality_report_{timestamp}.json"
        file_path.write_text(json.dumps(report_data, indent=2, default=str))

        return str(file_path)

    def close(self):
        """Clean up resources"""
        self.db.close()


# Test the report generator
if __name__ == "__main__":
    print("Testing Data Quality Report Generator")
    print("=" * 60)

    generator = DataQualityReportGenerator()

    # Generate system-wide report
    print("\nGenerating system-wide report...")
    files = generator.generate_comprehensive_report(
        company_code=None,
        period_days=7,
        format='all'
    )

    print("\nGenerated reports:")
    for format_type, path in files.items():
        print(f"  {format_type}: {path}")

    # Generate company-specific report
    print("\n\nGenerating company-specific report for TCS...")
    files = generator.generate_comprehensive_report(
        company_code='TCS',
        period_days=30,
        format='all'
    )

    print("\nGenerated reports:")
    for format_type, path in files.items():
        print(f"  {format_type}: {path}")

    generator.close()
    print("\n✅ Data Quality Report Generator test complete!")
    print(f"Reports saved to: {generator.output_dir}")