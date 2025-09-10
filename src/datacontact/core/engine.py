"""
Main data quality check execution engine.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
import logging

from .rules import DataQualityRule
from .results import DataQualityResult, DataQualityReport, CheckStatus


class DataQualityEngine:
    """Main engine for executing data quality checks."""
    
    def __init__(self, name: str = "DataQuality Engine"):
        self.name = name
        self.rules: List[DataQualityRule] = []
        self.logger = logging.getLogger(__name__)
        self.created_at = datetime.now()
    
    def add_rule(self, rule: DataQualityRule):
        """Add a data quality rule to the engine."""
        if not isinstance(rule, DataQualityRule):
            raise ValueError("Rule must be an instance of DataQualityRule")
        self.rules.append(rule)
        self.logger.info(f"Added rule: {rule.name}")
    
    def add_rules(self, rules: List[DataQualityRule]):
        """Add multiple data quality rules to the engine."""
        for rule in rules:
            self.add_rule(rule)
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule by name. Returns True if rule was found and removed."""
        initial_count = len(self.rules)
        self.rules = [rule for rule in self.rules if rule.name != rule_name]
        removed = len(self.rules) < initial_count
        if removed:
            self.logger.info(f"Removed rule: {rule_name}")
        return removed
    
    def get_rule(self, rule_name: str) -> Optional[DataQualityRule]:
        """Get a rule by name."""
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None
    
    def list_rules(self) -> List[str]:
        """Get list of all rule names."""
        return [rule.name for rule in self.rules]
    
    def execute_checks(self, data: pd.DataFrame, rule_names: Optional[List[str]] = None) -> DataQualityReport:
        """
        Execute data quality checks on the provided data.
        
        Args:
            data: pandas DataFrame to validate
            rule_names: Optional list of specific rule names to execute. If None, all rules are executed.
        
        Returns:
            DataQualityReport containing all check results
        """
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a pandas DataFrame")
        
        if data.empty:
            self.logger.warning("Empty DataFrame provided for quality checks")
        
        report = DataQualityReport()
        
        # Filter rules if specific rule names are provided
        rules_to_execute = self.rules
        if rule_names:
            rules_to_execute = [rule for rule in self.rules if rule.name in rule_names]
            missing_rules = set(rule_names) - {rule.name for rule in rules_to_execute}
            if missing_rules:
                self.logger.warning(f"Rules not found: {missing_rules}")
        
        if not rules_to_execute:
            self.logger.warning("No rules to execute")
            return report
        
        self.logger.info(f"Executing {len(rules_to_execute)} data quality checks on {len(data)} records")
        
        for rule in rules_to_execute:
            try:
                self.logger.debug(f"Executing rule: {rule.name}")
                result = rule.validate(data)
                report.add_result(result)
                self.logger.info(f"Rule '{rule.name}' completed with status: {result.status.value}")
                
            except Exception as e:
                self.logger.error(f"Error executing rule '{rule.name}': {str(e)}")
                error_result = DataQualityResult(
                    rule_name=rule.name,
                    status=CheckStatus.FAILED,
                    message=f"Execution error: {str(e)}",
                    timestamp=datetime.now(),
                    total_records=len(data)
                )
                report.add_result(error_result)
        
        summary = report.get_summary()
        self.logger.info(f"Quality check completed. Results: {summary['status_counts']}")
        
        return report
    
    def execute_single_check(self, data: pd.DataFrame, rule_name: str) -> DataQualityResult:
        """Execute a single data quality check by rule name."""
        rule = self.get_rule(rule_name)
        if not rule:
            raise ValueError(f"Rule '{rule_name}' not found")
        
        return rule.validate(data)
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the engine configuration."""
        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "total_rules": len(self.rules),
            "rules": [
                {
                    "name": rule.name,
                    "type": rule.__class__.__name__,
                    "description": rule.description,
                    "severity": rule.severity
                }
                for rule in self.rules
            ]
        }