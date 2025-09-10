"""
Unit tests for data quality rules.
"""

import pytest
import pandas as pd
from datetime import datetime

from datacontact.core.rules import CompletenessRule, ValidityRule, UniquenessRule
from datacontact.core.results import CheckStatus


class TestCompletenessRule:
    """Test cases for CompletenessRule."""
    
    def test_completeness_rule_passed(self):
        """Test completeness rule that passes."""
        rule = CompletenessRule(
            name="test_completeness",
            columns=["col1", "col2"],
            threshold=10.0  # Allow up to 10% missing
        )
        
        # Create data with 5% missing values
        data = pd.DataFrame({
            "col1": [1, 2, 3, None, 5, 6, 7, 8, 9, 10],
            "col2": [1, 2, 3, 4, 5, 6, 7, 8, 9, None]
        })
        
        result = rule.validate(data)
        
        assert result.status == CheckStatus.PASSED
        assert result.rule_name == "test_completeness"
        assert result.total_records == 10
        assert "10.00%" in result.message  # 10% missing (1 out of 10 for each column)
    
    def test_completeness_rule_failed(self):
        """Test completeness rule that fails."""
        rule = CompletenessRule(
            name="test_completeness",
            columns=["col1"],
            threshold=5.0  # Allow up to 5% missing
        )
        
        # Create data with 20% missing values
        data = pd.DataFrame({
            "col1": [1, 2, None, None, 5, 6, 7, 8, 9, 10]
        })
        
        result = rule.validate(data)
        
        assert result.status == CheckStatus.FAILED
        assert "20.00%" in result.message  # 20% missing
        assert result.affected_records == 2
    
    def test_completeness_rule_missing_column(self):
        """Test completeness rule with missing column."""
        rule = CompletenessRule(
            name="test_completeness",
            columns=["missing_col"]
        )
        
        data = pd.DataFrame({"col1": [1, 2, 3]})
        
        result = rule.validate(data)
        
        assert result.status == CheckStatus.FAILED
        assert "not found" in result.message
    
    def test_completeness_rule_single_column(self):
        """Test completeness rule with single column (string input)."""
        rule = CompletenessRule(
            name="test_completeness",
            columns="col1",  # String instead of list
            threshold=0.0
        )
        
        data = pd.DataFrame({"col1": [1, 2, 3, None]})
        
        result = rule.validate(data)
        
        assert result.status == CheckStatus.FAILED
        assert result.affected_records == 1


class TestValidityRule:
    """Test cases for ValidityRule."""
    
    def test_validity_rule_passed(self):
        """Test validity rule that passes."""
        # Rule to check if values are positive
        rule = ValidityRule(
            name="positive_values",
            column="value",
            validation_func=lambda x: x > 0 if pd.notna(x) else True
        )
        
        data = pd.DataFrame({"value": [1, 2, 3, 4, 5]})
        
        result = rule.validate(data)
        
        assert result.status == CheckStatus.PASSED
        assert "All values are valid" in result.message
        assert result.affected_records == 0
    
    def test_validity_rule_failed(self):
        """Test validity rule that fails."""
        # Rule to check if values are positive
        rule = ValidityRule(
            name="positive_values",
            column="value",
            validation_func=lambda x: x > 0 if pd.notna(x) else True
        )
        
        data = pd.DataFrame({"value": [1, -2, 3, -4, 5]})
        
        result = rule.validate(data)
        
        assert result.status == CheckStatus.FAILED
        assert "2 invalid values" in result.message
        assert result.affected_records == 2
        assert "40.00%" in result.message  # 40% invalid
    
    def test_validity_rule_missing_column(self):
        """Test validity rule with missing column."""
        rule = ValidityRule(
            name="test_validity",
            column="missing_col",
            validation_func=lambda x: True
        )
        
        data = pd.DataFrame({"col1": [1, 2, 3]})
        
        result = rule.validate(data)
        
        assert result.status == CheckStatus.FAILED
        assert "not found" in result.message
    
    def test_validity_rule_function_error(self):
        """Test validity rule with validation function that raises an error."""
        def bad_validation_func(x):
            raise ValueError("Test error")
        
        rule = ValidityRule(
            name="test_validity",
            column="value",
            validation_func=bad_validation_func
        )
        
        data = pd.DataFrame({"value": [1, 2, 3]})
        
        result = rule.validate(data)
        
        assert result.status == CheckStatus.FAILED
        assert "Validation function error" in result.message


class TestUniquenessRule:
    """Test cases for UniquenessRule."""
    
    def test_uniqueness_rule_passed(self):
        """Test uniqueness rule that passes."""
        rule = UniquenessRule(
            name="unique_ids",
            columns=["id"]
        )
        
        data = pd.DataFrame({"id": [1, 2, 3, 4, 5]})
        
        result = rule.validate(data)
        
        assert result.status == CheckStatus.PASSED
        assert "No duplicate records" in result.message
        assert result.affected_records == 0
    
    def test_uniqueness_rule_failed(self):
        """Test uniqueness rule that fails."""
        rule = UniquenessRule(
            name="unique_ids",
            columns=["id"]
        )
        
        data = pd.DataFrame({"id": [1, 2, 2, 3, 3]})
        
        result = rule.validate(data)
        
        assert result.status == CheckStatus.FAILED
        assert "2 duplicate records" in result.message
        assert result.affected_records == 2
        assert "40.00%" in result.message  # 40% duplicates
    
    def test_uniqueness_rule_multiple_columns(self):
        """Test uniqueness rule with multiple columns."""
        rule = UniquenessRule(
            name="unique_combination",
            columns=["col1", "col2"]
        )
        
        data = pd.DataFrame({
            "col1": [1, 1, 2, 2, 1],
            "col2": [1, 2, 1, 2, 1]  # Last row is duplicate of first
        })
        
        result = rule.validate(data)
        
        assert result.status == CheckStatus.FAILED
        assert result.affected_records == 1  # One duplicate
    
    def test_uniqueness_rule_missing_column(self):
        """Test uniqueness rule with missing column."""
        rule = UniquenessRule(
            name="unique_test",
            columns=["missing_col"]
        )
        
        data = pd.DataFrame({"col1": [1, 2, 3]})
        
        result = rule.validate(data)
        
        assert result.status == CheckStatus.FAILED
        assert "not found" in result.message
    
    def test_uniqueness_rule_single_column_string(self):
        """Test uniqueness rule with single column as string."""
        rule = UniquenessRule(
            name="unique_test",
            columns="id"  # String instead of list
        )
        
        data = pd.DataFrame({"id": [1, 2, 2, 3]})
        
        result = rule.validate(data)
        
        assert result.status == CheckStatus.FAILED
        assert result.affected_records == 1