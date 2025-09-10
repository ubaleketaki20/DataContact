"""
Report generation and export functionality for data quality results.
"""

import json
import csv
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd

from ..core.results import DataQualityReport, DataQualityResult


class ReportExporter:
    """Export data quality reports in various formats."""
    
    @staticmethod
    def to_json(report: DataQualityReport, include_summary: bool = True) -> str:
        """Export report to JSON format."""
        data = {
            "report_metadata": {
                "created_at": report.created_at.isoformat(),
                "total_checks": len(report.results)
            },
            "results": [result.to_dict() for result in report.results]
        }
        
        if include_summary:
            data["summary"] = report.get_summary()
        
        return json.dumps(data, indent=2, default=str)
    
    @staticmethod
    def to_csv(report: DataQualityReport, filename: str = None) -> str:
        """Export report to CSV format."""
        if not report.results:
            return ""
        
        # Convert results to tabular format
        rows = []
        for result in report.results:
            row = {
                "rule_name": result.rule_name,
                "status": result.status.value,
                "message": result.message,
                "timestamp": result.timestamp.isoformat(),
                "affected_records": result.affected_records,
                "total_records": result.total_records,
                "success_rate": result.success_rate
            }
            rows.append(row)
        
        if filename:
            df = pd.DataFrame(rows)
            df.to_csv(filename, index=False)
            return f"Report exported to {filename}"
        else:
            # Return CSV string
            if rows:
                fieldnames = rows[0].keys()
                output = []
                output.append(','.join(fieldnames))
                for row in rows:
                    output.append(','.join(str(row.get(field, '')) for field in fieldnames))
                return '\n'.join(output)
            return ""
    
    @staticmethod
    def to_html(report: DataQualityReport) -> str:
        """Export report to HTML format."""
        summary = report.get_summary()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Data Quality Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .warning {{ color: orange; }}
                .skipped {{ color: gray; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .details {{ font-size: 0.9em; color: #666; }}
            </style>
        </head>
        <body>
            <h1>Data Quality Report</h1>
            
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Total Checks:</strong> {summary.get('total_checks', 0)}</p>
                <p><strong>Generated:</strong> {summary.get('created_at', 'Unknown')}</p>
        """
        
        if 'status_counts' in summary:
            html += "<p><strong>Status Distribution:</strong></p><ul>"
            for status, count in summary['status_counts'].items():
                html += f'<li class="{status}">{status.title()}: {count}</li>'
            html += "</ul>"
        
        if summary.get('overall_success_rate') is not None:
            success_rate = summary['overall_success_rate'] * 100
            html += f"<p><strong>Overall Success Rate:</strong> {success_rate:.2f}%</p>"
        
        html += "</div><h2>Detailed Results</h2><table><tr>"
        html += "<th>Rule Name</th><th>Status</th><th>Message</th><th>Affected Records</th><th>Total Records</th><th>Success Rate</th><th>Timestamp</th>"
        html += "</tr>"
        
        for result in report.results:
            status_class = result.status.value
            success_rate_str = f"{result.success_rate*100:.2f}%" if result.success_rate is not None else "N/A"
            html += f"""
            <tr>
                <td>{result.rule_name}</td>
                <td class="{status_class}">{result.status.value.title()}</td>
                <td>{result.message}</td>
                <td>{result.affected_records or 'N/A'}</td>
                <td>{result.total_records or 'N/A'}</td>
                <td>{success_rate_str}</td>
                <td>{result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
            </tr>
            """
        
        html += "</table></body></html>"
        return html


class ConsoleReporter:
    """Generate console-friendly reports for data quality results."""
    
    @staticmethod
    def print_summary(report: DataQualityReport):
        """Print a summary of the data quality report to console."""
        summary = report.get_summary()
        
        print("=" * 60)
        print("DATA QUALITY REPORT SUMMARY")
        print("=" * 60)
        print(f"Generated: {summary.get('created_at', 'Unknown')}")
        print(f"Total Checks: {summary.get('total_checks', 0)}")
        
        if 'status_counts' in summary:
            print("\nStatus Distribution:")
            for status, count in summary['status_counts'].items():
                print(f"  {status.title()}: {count}")
        
        if summary.get('overall_success_rate') is not None:
            success_rate = summary['overall_success_rate'] * 100
            print(f"\nOverall Success Rate: {success_rate:.2f}%")
        
        if summary.get('total_records_processed'):
            print(f"Total Records Processed: {summary['total_records_processed']}")
            print(f"Total Affected Records: {summary.get('total_affected_records', 0)}")
        
        print("=" * 60)
    
    @staticmethod
    def print_detailed_results(report: DataQualityReport):
        """Print detailed results for each data quality check."""
        if not report.results:
            print("No data quality check results to display.")
            return
        
        print("\nDETAILED RESULTS:")
        print("-" * 80)
        
        for i, result in enumerate(report.results, 1):
            status_symbol = {
                "passed": "✓",
                "failed": "✗", 
                "warning": "⚠",
                "skipped": "○"
            }.get(result.status.value, "?")
            
            print(f"\n{i}. {result.rule_name} {status_symbol}")
            print(f"   Status: {result.status.value.upper()}")
            print(f"   Message: {result.message}")
            
            if result.total_records:
                print(f"   Records: {result.affected_records or 0}/{result.total_records}")
            
            if result.success_rate is not None:
                print(f"   Success Rate: {result.success_rate*100:.2f}%")
            
            print(f"   Timestamp: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if result.details:
                print(f"   Details: {result.details}")
        
        print("-" * 80)