"""
Example usage of the DataContact Quality Check Management System.

This example demonstrates how to use the data quality engine to check
the quality of a sample dataset.
"""

import pandas as pd
from datetime import datetime

from datacontact import DataQualityEngine
from datacontact.core.rules import CompletenessRule, ValidityRule, UniquenessRule
from datacontact.reports.exporters import ConsoleReporter, ReportExporter


def create_sample_data():
    """Create a sample dataset with some data quality issues."""
    data = {
        'id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'name': ['Alice', 'Bob', None, 'David', 'Eve', 'Frank', 'Grace', 'Henry', 'Ivy', None],
        'email': [
            'alice@email.com', 
            'bob@email.com', 
            'charlie@email.com', 
            'invalid-email',  # Invalid email format
            'eve@email.com',
            None,  # Missing email
            'grace@email.com',
            'henry@email.com',
            'ivy@email.com',
            'alice@email.com'  # Duplicate email
        ],
        'age': [25, 30, 35, -5, 40, 45, 50, 150, 60, 70],  # -5 and 150 are invalid ages
        'salary': [50000, 60000, 70000, 80000, None, 100000, 110000, 120000, 130000, 140000]
    }
    
    return pd.DataFrame(data)


def setup_data_quality_rules():
    """Set up data quality rules for the sample dataset."""
    rules = [
        # Completeness checks
        CompletenessRule(
            name="name_completeness",
            columns=["name"],
            threshold=10.0,  # Allow up to 10% missing names
            description="Check that names are not missing"
        ),
        
        CompletenessRule(
            name="email_completeness", 
            columns=["email"],
            threshold=5.0,  # Allow up to 5% missing emails
            description="Check that emails are not missing"
        ),
        
        # Validity checks
        ValidityRule(
            name="email_format",
            column="email",
            validation_func=lambda x: '@' in str(x) and '.' in str(x) if pd.notna(x) else True,
            description="Check that emails have valid format"
        ),
        
        ValidityRule(
            name="age_range",
            column="age", 
            validation_func=lambda x: 0 <= x <= 120 if pd.notna(x) else True,
            description="Check that ages are in valid range (0-120)"
        ),
        
        ValidityRule(
            name="salary_positive",
            column="salary",
            validation_func=lambda x: x > 0 if pd.notna(x) else True,
            description="Check that salaries are positive"
        ),
        
        # Uniqueness checks
        UniquenessRule(
            name="id_uniqueness",
            columns=["id"],
            description="Check that IDs are unique"
        ),
        
        UniquenessRule(
            name="email_uniqueness", 
            columns=["email"],
            description="Check that email addresses are unique"
        )
    ]
    
    return rules


def main():
    """Main example function."""
    print("DataContact Quality Check Management System - Example Usage")
    print("=" * 60)
    
    # Create sample data
    print("\n1. Creating sample dataset...")
    data = create_sample_data()
    print(f"Created dataset with {len(data)} records and {len(data.columns)} columns")
    print("\nSample data:")
    print(data.head())
    
    # Set up data quality engine
    print("\n2. Setting up data quality engine...")
    engine = DataQualityEngine("Example Engine")
    
    # Add rules
    rules = setup_data_quality_rules()
    engine.add_rules(rules)
    print(f"Added {len(rules)} data quality rules:")
    for rule in rules:
        print(f"  - {rule.name}: {rule.description}")
    
    # Execute data quality checks
    print("\n3. Executing data quality checks...")
    report = engine.execute_checks(data)
    
    # Display results
    print("\n4. Data Quality Results:")
    ConsoleReporter.print_summary(report)
    ConsoleReporter.print_detailed_results(report)
    
    # Generate and save reports
    print("\n5. Generating reports...")
    
    # JSON report
    json_report = ReportExporter.to_json(report)
    with open("/tmp/quality_report.json", "w") as f:
        f.write(json_report)
    print("JSON report saved to /tmp/quality_report.json")
    
    # HTML report
    html_report = ReportExporter.to_html(report)
    with open("/tmp/quality_report.html", "w") as f:
        f.write(html_report)
    print("HTML report saved to /tmp/quality_report.html")
    
    # CSV report
    ReportExporter.to_csv(report, "/tmp/quality_report.csv")
    print("CSV report saved to /tmp/quality_report.csv")
    
    # Show engine information
    print("\n6. Engine Information:")
    info = engine.get_engine_info()
    print(f"Engine: {info['name']}")
    print(f"Total Rules: {info['total_rules']}")
    print(f"Created: {info['created_at']}")
    
    # Demonstrate single rule execution
    print("\n7. Executing single rule...")
    single_result = engine.execute_single_check(data, "email_format")
    print(f"Single rule result: {single_result.status.value} - {single_result.message}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")


if __name__ == "__main__":
    main()