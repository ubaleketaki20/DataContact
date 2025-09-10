"""
Core data quality check results and reporting functionality.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class CheckStatus(Enum):
    """Status of a data quality check."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class DataQualityResult:
    """Result of a data quality check execution."""
    
    rule_name: str
    status: CheckStatus
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    affected_records: Optional[int] = None
    total_records: Optional[int] = None
    
    @property
    def success_rate(self) -> Optional[float]:
        """Calculate success rate if record counts are available."""
        if self.total_records and self.affected_records is not None:
            return (self.total_records - self.affected_records) / self.total_records
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "rule_name": self.rule_name,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details or {},
            "affected_records": self.affected_records,
            "total_records": self.total_records,
            "success_rate": self.success_rate
        }


class DataQualityReport:
    """Collection of data quality check results with summary statistics."""
    
    def __init__(self):
        self.results: List[DataQualityResult] = []
        self.created_at = datetime.now()
    
    def add_result(self, result: DataQualityResult):
        """Add a data quality check result."""
        self.results.append(result)
    
    def get_summary(self) -> Dict[str, Any]:
        """Generate summary statistics for all results."""
        if not self.results:
            return {"total_checks": 0}
        
        status_counts = {}
        for status in CheckStatus:
            status_counts[status.value] = sum(1 for r in self.results if r.status == status)
        
        total_records = sum(r.total_records for r in self.results if r.total_records)
        total_affected = sum(r.affected_records for r in self.results if r.affected_records)
        
        return {
            "total_checks": len(self.results),
            "status_counts": status_counts,
            "overall_success_rate": (total_records - total_affected) / total_records if total_records > 0 else None,
            "created_at": self.created_at.isoformat(),
            "total_records_processed": total_records,
            "total_affected_records": total_affected
        }