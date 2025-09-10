"""
Command-line interface for DataContact Quality Check Management.
"""

import click
import pandas as pd
import json
import sys
from pathlib import Path

from .core.engine import DataQualityEngine
from .core.rules import CompletenessRule, ValidityRule, UniquenessRule
from .reports.exporters import ReportExporter, ConsoleReporter


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """DataContact Quality Check Management System"""
    pass


@cli.command()
@click.argument('data_file', type=click.Path(exists=True))
@click.option('--rules-config', '-r', type=click.Path(exists=True), 
              help='JSON file with data quality rules configuration')
@click.option('--output', '-o', type=click.Path(), 
              help='Output file for results (JSON format)')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'html', 'console']), 
              default='console', help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def check(data_file, rules_config, output, format, verbose):
    """Run data quality checks on a data file."""
    
    try:
        # Load data
        if verbose:
            click.echo(f"Loading data from {data_file}...")
        
        if data_file.endswith('.csv'):
            data = pd.read_csv(data_file)
        elif data_file.endswith('.json'):
            data = pd.read_json(data_file)
        elif data_file.endswith(('.xlsx', '.xls')):
            data = pd.read_excel(data_file)
        else:
            click.echo(f"Error: Unsupported file format for {data_file}", err=True)
            sys.exit(1)
        
        if verbose:
            click.echo(f"Loaded {len(data)} records with {len(data.columns)} columns")
        
        # Initialize engine
        engine = DataQualityEngine("CLI Engine")
        
        # Load rules
        if rules_config:
            if verbose:
                click.echo(f"Loading rules from {rules_config}...")
            rules = load_rules_from_config(rules_config)
            engine.add_rules(rules)
        else:
            # Add default rules
            if verbose:
                click.echo("Using default data quality rules...")
            add_default_rules(engine, data)
        
        if verbose:
            click.echo(f"Executing {len(engine.rules)} data quality checks...")
        
        # Execute checks
        report = engine.execute_checks(data)
        
        # Output results
        if format == 'console' or not output:
            ConsoleReporter.print_summary(report)
            if verbose:
                ConsoleReporter.print_detailed_results(report)
        
        if output:
            if format == 'json':
                content = ReportExporter.to_json(report)
                with open(output, 'w') as f:
                    f.write(content)
            elif format == 'csv':
                ReportExporter.to_csv(report, str(output))
            elif format == 'html':
                content = ReportExporter.to_html(report)
                with open(output, 'w') as f:
                    f.write(content)
            
            click.echo(f"Results exported to {output}")
        
        # Exit with error code if any checks failed
        summary = report.get_summary()
        failed_count = summary.get('status_counts', {}).get('failed', 0)
        if failed_count > 0:
            sys.exit(1)
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('data_file', type=click.Path(exists=True))
def inspect(data_file):
    """Inspect a data file and suggest quality checks."""
    
    try:
        # Load data
        if data_file.endswith('.csv'):
            data = pd.read_csv(data_file)
        elif data_file.endswith('.json'):
            data = pd.read_json(data_file)
        elif data_file.endswith(('.xlsx', '.xls')):
            data = pd.read_excel(data_file)
        else:
            click.echo(f"Error: Unsupported file format for {data_file}", err=True)
            sys.exit(1)
        
        click.echo("DATA INSPECTION REPORT")
        click.echo("=" * 50)
        click.echo(f"File: {data_file}")
        click.echo(f"Shape: {data.shape[0]} rows, {data.shape[1]} columns")
        
        click.echo("\nCOLUMN ANALYSIS:")
        click.echo("-" * 50)
        
        for col in data.columns:
            null_count = data[col].isna().sum()
            null_pct = (null_count / len(data)) * 100
            dtype = data[col].dtype
            unique_count = data[col].nunique()
            
            click.echo(f"{col}:")
            click.echo(f"  Type: {dtype}")
            click.echo(f"  Null values: {null_count} ({null_pct:.1f}%)")
            click.echo(f"  Unique values: {unique_count}")
            
            if null_pct > 0:
                click.echo(f"  → Suggest: Completeness check (threshold: {null_pct:.1f}%)")
            
            if unique_count == len(data) and null_count == 0:
                click.echo(f"  → Suggest: Uniqueness check")
            
            click.echo()
        
        click.echo("SUGGESTED RULES CONFIG:")
        click.echo("-" * 50)
        
        # Generate sample rules config
        rules_config = generate_sample_rules_config(data)
        click.echo(json.dumps(rules_config, indent=2))
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


def load_rules_from_config(config_file: str):
    """Load data quality rules from a JSON configuration file."""
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    rules = []
    
    for rule_config in config.get('rules', []):
        rule_type = rule_config.get('type')
        name = rule_config.get('name')
        
        if rule_type == 'completeness':
            rules.append(CompletenessRule(
                name=name,
                columns=rule_config.get('columns', []),
                threshold=rule_config.get('threshold', 0.0),
                description=rule_config.get('description', ''),
                severity=rule_config.get('severity', 'error')
            ))
        
        elif rule_type == 'uniqueness':
            rules.append(UniquenessRule(
                name=name,
                columns=rule_config.get('columns', []),
                description=rule_config.get('description', ''),
                severity=rule_config.get('severity', 'error')
            ))
    
    return rules


def add_default_rules(engine: DataQualityEngine, data: pd.DataFrame):
    """Add default data quality rules based on data analysis."""
    
    # Add completeness checks for all columns
    for col in data.columns:
        null_pct = (data[col].isna().sum() / len(data)) * 100
        if null_pct > 0:
            engine.add_rule(CompletenessRule(
                name=f"completeness_{col}",
                columns=[col],
                threshold=null_pct + 1,  # Allow current level + 1%
                description=f"Completeness check for {col}"
            ))
    
    # Add uniqueness check for columns that appear to be identifiers
    for col in data.columns:
        if data[col].nunique() == len(data) and data[col].notna().all():
            engine.add_rule(UniquenessRule(
                name=f"uniqueness_{col}",
                columns=[col],
                description=f"Uniqueness check for {col} (appears to be an identifier)"
            ))


def generate_sample_rules_config(data: pd.DataFrame):
    """Generate a sample rules configuration based on data analysis."""
    rules = []
    
    for col in data.columns:
        null_pct = (data[col].isna().sum() / len(data)) * 100
        
        if null_pct > 0:
            rules.append({
                "type": "completeness",
                "name": f"completeness_{col}",
                "columns": [col],
                "threshold": round(null_pct, 2),
                "description": f"Completeness check for {col}",
                "severity": "error"
            })
        
        if data[col].nunique() == len(data) and data[col].notna().all():
            rules.append({
                "type": "uniqueness", 
                "name": f"uniqueness_{col}",
                "columns": [col],
                "description": f"Uniqueness check for {col}",
                "severity": "error"
            })
    
    return {"rules": rules}


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()