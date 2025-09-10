"""
Unit tests for data quality engine.
"""

import pytest
import pandas as pd
from datetime import datetime

from datacontact.core.engine import DataQualityEngine
from datacontact.core.rules import CompletenessRule, ValidityRule, UniquenessRule
from datacontact.core.results import CheckStatus


class TestDataQualityEngine:
    """Test cases for DataQualityEngine."""
    
    def test_create_engine(self):
        """Test creating a data quality engine."""
        engine = DataQualityEngine("Test Engine")
        
        assert engine.name == "Test Engine"
        assert len(engine.rules) == 0
        assert isinstance(engine.created_at, datetime)
    
    def test_add_rule(self):
        """Test adding a rule to the engine."""
        engine = DataQualityEngine()
        rule = CompletenessRule("test_rule", ["col1"])
        
        engine.add_rule(rule)
        
        assert len(engine.rules) == 1
        assert engine.rules[0] == rule
    
    def test_add_invalid_rule(self):
        """Test adding an invalid rule raises ValueError."""
        engine = DataQualityEngine()
        
        with pytest.raises(ValueError, match="Rule must be an instance of DataQualityRule"):
            engine.add_rule("not a rule")
    
    def test_add_multiple_rules(self):
        """Test adding multiple rules at once."""
        engine = DataQualityEngine()
        rules = [
            CompletenessRule("rule1", ["col1"]),
            CompletenessRule("rule2", ["col2"])
        ]
        
        engine.add_rules(rules)
        
        assert len(engine.rules) == 2
    
    def test_remove_rule(self):
        """Test removing a rule by name."""
        engine = DataQualityEngine()
        rule = CompletenessRule("test_rule", ["col1"])
        engine.add_rule(rule)
        
        removed = engine.remove_rule("test_rule")
        
        assert removed is True
        assert len(engine.rules) == 0
    
    def test_remove_nonexistent_rule(self):
        """Test removing a rule that doesn't exist."""
        engine = DataQualityEngine()
        
        removed = engine.remove_rule("nonexistent")
        
        assert removed is False
    
    def test_get_rule(self):
        """Test getting a rule by name."""
        engine = DataQualityEngine()
        rule = CompletenessRule("test_rule", ["col1"])
        engine.add_rule(rule)
        
        found_rule = engine.get_rule("test_rule")
        
        assert found_rule == rule
    
    def test_get_nonexistent_rule(self):
        """Test getting a rule that doesn't exist."""
        engine = DataQualityEngine()
        
        found_rule = engine.get_rule("nonexistent")
        
        assert found_rule is None
    
    def test_list_rules(self):
        """Test listing all rule names."""
        engine = DataQualityEngine()
        engine.add_rules([
            CompletenessRule("rule1", ["col1"]),
            CompletenessRule("rule2", ["col2"])
        ])
        
        rule_names = engine.list_rules()
        
        assert rule_names == ["rule1", "rule2"]
    
    def test_execute_checks_success(self):
        """Test executing checks successfully."""
        engine = DataQualityEngine()
        engine.add_rule(CompletenessRule("completeness_check", ["col1"], threshold=0))
        
        data = pd.DataFrame({"col1": [1, 2, 3, 4, 5]})
        
        report = engine.execute_checks(data)
        
        assert len(report.results) == 1
        assert report.results[0].status == CheckStatus.PASSED
    
    def test_execute_checks_with_failures(self):
        """Test executing checks with failures."""
        engine = DataQualityEngine()
        engine.add_rule(CompletenessRule("completeness_check", ["col1"], threshold=0))
        
        data = pd.DataFrame({"col1": [1, 2, None, 4, 5]})  # Has missing value
        
        report = engine.execute_checks(data)
        
        assert len(report.results) == 1
        assert report.results[0].status == CheckStatus.FAILED
    
    def test_execute_specific_rules(self):
        """Test executing only specific rules."""
        engine = DataQualityEngine()
        engine.add_rules([
            CompletenessRule("rule1", ["col1"]),
            CompletenessRule("rule2", ["col2"])
        ])
        
        data = pd.DataFrame({"col1": [1, 2, 3], "col2": [1, 2, 3]})
        
        report = engine.execute_checks(data, rule_names=["rule1"])
        
        assert len(report.results) == 1
        assert report.results[0].rule_name == "rule1"
    
    def test_execute_nonexistent_rules(self):
        """Test executing rules that don't exist."""
        engine = DataQualityEngine()
        engine.add_rule(CompletenessRule("existing_rule", ["col1"]))
        
        data = pd.DataFrame({"col1": [1, 2, 3]})
        
        # This should execute 1 rule (existing_rule) and log warning about missing_rule
        report = engine.execute_checks(data, rule_names=["existing_rule", "missing_rule"])
        
        assert len(report.results) == 1
        assert report.results[0].rule_name == "existing_rule"
    
    def test_execute_checks_invalid_data(self):
        """Test executing checks with invalid data type."""
        engine = DataQualityEngine()
        
        with pytest.raises(ValueError, match="Data must be a pandas DataFrame"):
            engine.execute_checks("not a dataframe")
    
    def test_execute_checks_empty_data(self):
        """Test executing checks with empty DataFrame."""
        engine = DataQualityEngine()
        engine.add_rule(CompletenessRule("test_rule", ["col1"]))
        
        data = pd.DataFrame()
        
        report = engine.execute_checks(data)
        
        # Should still execute the rule, even with empty data
        assert len(report.results) == 1
    
    def test_execute_single_check(self):
        """Test executing a single check by rule name."""
        engine = DataQualityEngine()
        rule = CompletenessRule("test_rule", ["col1"])
        engine.add_rule(rule)
        
        data = pd.DataFrame({"col1": [1, 2, 3]})
        
        result = engine.execute_single_check(data, "test_rule")
        
        assert result.rule_name == "test_rule"
        assert result.status == CheckStatus.PASSED
    
    def test_execute_single_check_nonexistent_rule(self):
        """Test executing a single check for nonexistent rule."""
        engine = DataQualityEngine()
        data = pd.DataFrame({"col1": [1, 2, 3]})
        
        with pytest.raises(ValueError, match="Rule 'nonexistent' not found"):
            engine.execute_single_check(data, "nonexistent")
    
    def test_get_engine_info(self):
        """Test getting engine information."""
        engine = DataQualityEngine("Test Engine")
        rule = CompletenessRule("test_rule", ["col1"], description="Test description")
        engine.add_rule(rule)
        
        info = engine.get_engine_info()
        
        assert info["name"] == "Test Engine"
        assert info["total_rules"] == 1
        assert len(info["rules"]) == 1
        assert info["rules"][0]["name"] == "test_rule"
        assert info["rules"][0]["type"] == "CompletenessRule"
        assert info["rules"][0]["description"] == "Test description"
    
    def test_execute_checks_rule_error(self):
        """Test handling of rule execution errors."""
        engine = DataQualityEngine()
        
        # Create a rule that will cause an error
        class BadRule(CompletenessRule):
            def validate(self, data):
                raise Exception("Test error")
        
        engine.add_rule(BadRule("bad_rule", ["col1"]))
        
        data = pd.DataFrame({"col1": [1, 2, 3]})
        
        report = engine.execute_checks(data)
        
        assert len(report.results) == 1
        assert report.results[0].status == CheckStatus.FAILED
        assert "Execution error" in report.results[0].message