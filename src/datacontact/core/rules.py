"""
Data quality rule definitions and validation logic.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
import pandas as pd
from datetime import datetime

from .results import DataQualityResult, CheckStatus


class DataQualityRule(ABC):
    """Abstract base class for data quality rules."""
    
    def __init__(self, name: str, description: str = "", severity: str = "error"):
        self.name = name
        self.description = description
        self.severity = severity
        self.created_at = datetime.now()
    
    @abstractmethod
    def validate(self, data: pd.DataFrame) -> DataQualityResult:
        """Execute the data quality check and return result."""
        pass
    
    def __str__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"


class CompletenessRule(DataQualityRule):
    """Check for missing/null values in specified columns."""
    
    def __init__(self, name: str, columns: list, threshold: float = 0.0, **kwargs):
        super().__init__(name, **kwargs)
        self.columns = columns if isinstance(columns, list) else [columns]
        self.threshold = threshold  # Maximum allowed missing percentage
    
    def validate(self, data: pd.DataFrame) -> DataQualityResult:
        """Check completeness of specified columns."""
        missing_data = {}
        total_records = len(data)
        affected_records = 0
        
        for column in self.columns:
            if column not in data.columns:
                return DataQualityResult(
                    rule_name=self.name,
                    status=CheckStatus.FAILED,
                    message=f"Column '{column}' not found in data",
                    timestamp=datetime.now(),
                    total_records=total_records
                )
            
            missing_count = data[column].isna().sum()
            missing_percentage = (missing_count / total_records) * 100 if total_records > 0 else 0
            missing_data[column] = {
                "missing_count": missing_count,
                "missing_percentage": missing_percentage
            }
            
            if missing_percentage > self.threshold:
                affected_records += missing_count
        
        max_missing_pct = max((missing_data[col]["missing_percentage"] for col in missing_data), default=0)
        
        if max_missing_pct > self.threshold:
            status = CheckStatus.FAILED
            message = f"Completeness check failed. Max missing percentage: {max_missing_pct:.2f}% (threshold: {self.threshold}%)"
        else:
            status = CheckStatus.PASSED
            message = f"Completeness check passed. Max missing percentage: {max_missing_pct:.2f}%"
        
        return DataQualityResult(
            rule_name=self.name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            details=missing_data,
            affected_records=affected_records,
            total_records=total_records
        )


class ValidityRule(DataQualityRule):
    """Check if values in columns meet specified validity criteria."""
    
    def __init__(self, name: str, column: str, validation_func: Callable, **kwargs):
        super().__init__(name, **kwargs)
        self.column = column
        self.validation_func = validation_func
    
    def validate(self, data: pd.DataFrame) -> DataQualityResult:
        """Check validity of values in specified column."""
        if self.column not in data.columns:
            return DataQualityResult(
                rule_name=self.name,
                status=CheckStatus.FAILED,
                message=f"Column '{self.column}' not found in data",
                timestamp=datetime.now(),
                total_records=len(data)
            )
        
        total_records = len(data)
        try:
            valid_mask = data[self.column].apply(self.validation_func)
            invalid_count = (~valid_mask).sum()
            invalid_percentage = (invalid_count / total_records) * 100 if total_records > 0 else 0
            
            if invalid_count > 0:
                status = CheckStatus.FAILED
                message = f"Validity check failed. {invalid_count} invalid values ({invalid_percentage:.2f}%)"
            else:
                status = CheckStatus.PASSED
                message = "Validity check passed. All values are valid"
            
            return DataQualityResult(
                rule_name=self.name,
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={
                    "invalid_count": invalid_count,
                    "invalid_percentage": invalid_percentage,
                    "column": self.column
                },
                affected_records=invalid_count,
                total_records=total_records
            )
        
        except Exception as e:
            return DataQualityResult(
                rule_name=self.name,
                status=CheckStatus.FAILED,
                message=f"Validation function error: {str(e)}",
                timestamp=datetime.now(),
                total_records=total_records
            )


class UniquenessRule(DataQualityRule):
    """Check for duplicate values in specified columns."""
    
    def __init__(self, name: str, columns: list, **kwargs):
        super().__init__(name, **kwargs)
        self.columns = columns if isinstance(columns, list) else [columns]
    
    def validate(self, data: pd.DataFrame) -> DataQualityResult:
        """Check uniqueness of values in specified columns."""
        missing_cols = [col for col in self.columns if col not in data.columns]
        if missing_cols:
            return DataQualityResult(
                rule_name=self.name,
                status=CheckStatus.FAILED,
                message=f"Columns not found: {missing_cols}",
                timestamp=datetime.now(),
                total_records=len(data)
            )
        
        total_records = len(data)
        duplicate_count = data.duplicated(subset=self.columns).sum()
        duplicate_percentage = (duplicate_count / total_records) * 100 if total_records > 0 else 0
        
        if duplicate_count > 0:
            status = CheckStatus.FAILED
            message = f"Uniqueness check failed. {duplicate_count} duplicate records ({duplicate_percentage:.2f}%)"
        else:
            status = CheckStatus.PASSED
            message = "Uniqueness check passed. No duplicate records found"
        
        return DataQualityResult(
            rule_name=self.name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            details={
                "duplicate_count": duplicate_count,
                "duplicate_percentage": duplicate_percentage,
                "columns": self.columns
            },
            affected_records=duplicate_count,
            total_records=total_records
        )