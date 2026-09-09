#!/usr/bin/env python3
"""Schema Markup Validator - Validates JSON-LD against schema.org standards."""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SchemaError:
    """Represents a schema validation error."""
    schema_type: str
    property_name: str
    error_type: str  # missing, invalid, wrong_type
    message: str
    severity: str  # error, warning, suggestion


@dataclass
class SchemaValidationReport:
    """Complete schema validation report."""
    file_path: str
    schemas_found: List[str]
    errors: List[SchemaError]
    warnings: List[SchemaError]
    suggestions: List[SchemaError]
    valid: bool
    corrected_schema: Optional[Dict] = None


class SchemaValidator:
    """Validates JSON-LD schemas against schema.org standards."""

    REQUIRED_PROPERTIES = {
        'Product': ['name', 'description', 'image'],
        'Article': ['headline', 'datePublished', 'author'],
        'Review': ['itemReviewed', 'reviewRating', 'author'],
        'FAQPage': ['mainEntity'],
        'BreadcrumbList': ['itemListElement'],
        'CollectionPage': ['name', 'description']
    }

    RATING_PROPERTIES = {
        'Review': ['ratingValue', 'bestRating', 'worstRating'],
        'AggregateRating': ['ratingValue', 'reviewCount']
    }

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.suggestions = []

    def extract_schemas(self, html_content: str) -> List[Dict]:
        """Extract all JSON-LD schemas from HTML."""
        schemas = []
        pattern = r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)

        for match in matches:
            try:
                schema = json.loads(match.strip())
                schemas.append(schema)
            except json.JSONDecodeError:
                continue

        return schemas

    def validate_schema(self, schema: Dict) -> List[SchemaError]:
        """Validate a single schema object."""
        errors = []
        schema_type = schema.get('@type', '')

        if not schema_type:
            errors.append(SchemaError(
                schema_type='Unknown',
                property_name='@type',
                error_type='missing',
                message='Schema missing @type property',
                severity='error'
            ))
            return errors

        # Check required properties
        required = self.REQUIRED_PROPERTIES.get(schema_type, [])
        for prop in required:
            if prop not in schema:
                errors.append(SchemaError(
                    schema_type=schema_type,
                    property_name=prop,
                    error_type='missing',
                    message=f'{schema_type} schema missing required property: {prop}',
                    severity='error'
                ))

        # Validate Review/Rating specific properties
        if schema_type == 'Review':
            rating = schema.get('reviewRating', {})
            if isinstance(rating, dict):
                for prop in self.RATING_PROPERTIES['Review']:
                    if prop not in rating:
                        errors.append(SchemaError(
                            schema_type=schema_type,
                            property_name=f'reviewRating.{prop}',
                            error_type='missing',
                            message=f'Review rating missing: {prop}',
                            severity='warning'
                        ))

        return errors

    def validate_file(self, file_path: str | Path) -> SchemaValidationReport:
        """Validate all schemas in an HTML file."""
        file_path = Path(file_path)
        content = file_path.read_text(encoding='utf-8', errors='replace')

        schemas = self.extract_schemas(content)
        all_errors = []
        schema_types = []

        for schema in schemas:
            schema_type = schema.get('@type', 'Unknown')
            schema_types.append(schema_type)
            errors = self.validate_schema(schema)
            all_errors.extend(errors)

        errors = [e for e in all_errors if e.severity == 'error']
        warnings = [e for e in all_errors if e.severity == 'warning']
        suggestions = [e for e in all_errors if e.severity == 'suggestion']

        return SchemaValidationReport(
            file_path=str(file_path),
            schemas_found=schema_types,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            valid=len(errors) == 0
        )

    def validate_batch(self, files: List[str | Path], output_file: Optional[str] = None) -> List[SchemaValidationReport]:
        """Validate multiple files."""
        reports = []
        for f in files:
            report = self.validate_file(f)
            reports.append(report)
            status = "✅" if report.valid else "❌"
            print(f"{status} {f}: {len(report.schemas_found)} schemas, {len(report.errors)} errors")

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "total_files": len(reports),
                "valid_files": sum(1 for r in reports if r.valid),
                "total_schemas": sum(len(r.schemas_found) for r in reports),
                "total_errors": sum(len(r.errors) for r in reports),
                "reports": [
                    {
                        "file": r.file_path,
                        "schemas": r.schemas_found,
                        "valid": r.valid,
                        "errors": [{"type": e.schema_type, "property": e.property_name, "message": e.message} for e in r.errors],
                        "warnings": [{"type": w.schema_type, "property": w.property_name, "message": w.message} for w in r.warnings]
                    }
                    for r in reports
                ]
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"\n📊 Report saved: {output_path}")

        return reports


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Schema Markup Validator")
    parser.add_argument("files", nargs="+", help="HTML files to validate")
    parser.add_argument("--output", "-o", default="schema_validation_report.json")
    args = parser.parse_args()

    validator = SchemaValidator()
    reports = validator.validate_batch(args.files, args.output)

    valid = sum(1 for r in reports if r.valid)
    print(f"\n{'='*50}")
    print(f"VALIDATION SUMMARY: {valid}/{len(reports)} files valid")
    print(f"{'='*50}")

    return 0 if valid == len(reports) else 1

if __name__ == "__main__":
    sys.exit(main())

