"""
DataContact Quality Check Management System

A comprehensive data quality management system for monitoring and ensuring
data integrity across various data sources and pipelines.
"""

__version__ = "0.1.0"
__author__ = "DataContact Team"

from .core.engine import DataQualityEngine
from .core.rules import DataQualityRule
from .core.results import DataQualityResult

__all__ = [
    "DataQualityEngine",
    "DataQualityRule", 
    "DataQualityResult",
]