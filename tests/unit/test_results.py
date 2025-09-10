"""
Unit tests for data quality results and reporting functionality.
"""

import pytest
from datetime import datetime
import pandas as pd

from datacontact.core.results import DataQualityResult, CheckStatus, DataQualityReport


class TestDataQualityResult:
    """Test cases for DataQualityResult class."""
    
    def test_create_basic_result(self):
        """Test creating a basic data quality result."""
        result = DataQualityResult(
            rule_name="test_rule",
            status=CheckStatus.PASSED,
            message="Test passed",
            timestamp=datetime.now()
        )
        
        assert result.rule_name == "test_rule"
        assert result.status == CheckStatus.PASSED
        assert result.message == "Test passed"
        assert isinstance(result.timestamp, datetime)
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = DataQualityResult(
            rule_name="test_rule",
            status=CheckStatus.FAILED,
            message="Test failed",
            timestamp=datetime.now(),
            affected_records=25,
            total_records=100
        )
        
        assert result.success_rate == 0.75  # (100-25)/100
    
    def test_success_rate_none_when_no_records(self):
        """Test success rate is None when record counts are not available."""
        result = DataQualityResult(
            rule_name="test_rule", 
            status=CheckStatus.PASSED,
            message="Test passed",
            timestamp=datetime.now()
        )
        
        assert result.success_rate is None
    
    def test_to_dict(self):
        """Test converting result to dictionary."""
        timestamp = datetime.now()
        result = DataQualityResult(
            rule_name="test_rule",
            status=CheckStatus.FAILED,
            message="Test failed",
            timestamp=timestamp,
            details={"error_count": 5},
            affected_records=5,
            total_records=100
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["rule_name"] == "test_rule"
        assert result_dict["status"] == "failed"
        assert result_dict["message"] == "Test failed"
        assert result_dict["timestamp"] == timestamp.isoformat()
        assert result_dict["details"] == {"error_count": 5}
        assert result_dict["affected_records"] == 5
        assert result_dict["total_records"] == 100
        assert result_dict["success_rate"] == 0.95


class TestDataQualityReport:
    """Test cases for DataQualityReport class."""
    
    def test_create_empty_report(self):
        """Test creating an empty report."""
        report = DataQualityReport()
        
        assert len(report.results) == 0
        assert isinstance(report.created_at, datetime)
    
    def test_add_result(self):
        """Test adding results to report."""
        report = DataQualityReport()
        result = DataQualityResult(
            rule_name="test_rule",
            status=CheckStatus.PASSED,
            message="Test passed",
            timestamp=datetime.now()
        )
        
        report.add_result(result)
        
        assert len(report.results) == 1
        assert report.results[0] == result
    
    def test_summary_empty_report(self):
        """Test summary for empty report."""
        report = DataQualityReport()
        summary = report.get_summary()
        
        assert summary["total_checks"] == 0
    
    def test_summary_with_results(self):
        """Test summary with multiple results."""
        report = DataQualityReport()
        
        # Add various results
        results = [
            DataQualityResult("rule1", CheckStatus.PASSED, "Passed", datetime.now(), total_records=100, affected_records=0),
            DataQualityResult("rule2", CheckStatus.FAILED, "Failed", datetime.now(), total_records=100, affected_records=10),
            DataQualityResult("rule3", CheckStatus.WARNING, "Warning", datetime.now(), total_records=50, affected_records=5),
        ]
        
        for result in results:
            report.add_result(result)
        
        summary = report.get_summary()
        
        assert summary["total_checks"] == 3
        assert summary["status_counts"]["passed"] == 1
        assert summary["status_counts"]["failed"] == 1 
        assert summary["status_counts"]["warning"] == 1
        assert summary["total_records_processed"] == 250
        assert summary["total_affected_records"] == 15
        assert summary["overall_success_rate"] == (250-15)/250  # 0.94