#!/usr/bin/env python3
"""EEAT Compliance Checker - Experience, Expertise, Authoritativeness, Trustworthiness."""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class EEATScore:
    """EEAT scores per category."""
    experience: float = 0.0
    expertise: float = 0.0
    authoritativeness: float = 0.0
    trustworthiness: float = 0.0
    overall: float = 0.0


@dataclass
class EEATReport:
    """Complete EEAT compliance report."""
    file_path: str
    scores: EEATScore
    missing_elements: List[str]
    recommendations: List[str]
    compliant: bool


class EEATComplianceChecker:
    """Checks EEAT compliance for content."""

    EXPERIENCE_SIGNALS = [
        (r'\b(we tested|our test|testing)\b', 'First-hand testing mention'),
        (r'\b(lab results|laboratory)\b', 'Lab testing'),
        (r'\b(real-world|field test)\b', 'Real-world testing'),
        (r'\b(hands-on|hands on)\b', 'Hands-on experience'),
    ]

    EXPERTISE_SIGNALS = [
        (r'<div[^>]*class=["\'][^"\']*author[^"\']*["\']', 'Author bio section'),
        (r'\b(expert|professional|certified)\b', 'Expert credentials'),
        (r'\b(\d+\+?\s*years?)\b', 'Years of experience'),
    ]

    AUTHORITY_SIGNALS = [
        (r'<link[^>]+rel=["\']canonical["\']', 'Canonical URL'),
        (r'schema\.org', 'Schema markup'),
        (r'\b(cited|according to|source:)\b', 'Citations'),
    ]

    TRUST_SIGNALS = [
        (r'https://', 'HTTPS'),
        (r'\b(updated|last modified|\d{4}-\d{2}-\d{2})\b', 'Last updated date'),
        (r'\b(disclosure|affiliate)\b', 'Affiliate disclosure'),
        (r'\b(privacy policy|contact)\b', 'Privacy/Contact info'),
    ]

    def check_file(self, file_path: str | Path) -> EEATReport:
        """Check EEAT compliance for a file."""
        path = Path(file_path)
        content = path.read_text(encoding='utf-8', errors='replace')

        scores = {'experience': 0, 'expertise': 0, 'authoritativeness': 0, 'trustworthiness': 0}
        missing = []
        recommendations = []

        # Check Experience
        exp_found = sum(1 for pattern, _ in self.EXPERIENCE_SIGNALS if re.search(pattern, content, re.I))
        scores['experience'] = (exp_found / len(self.EXPERIENCE_SIGNALS)) * 100
        if exp_found < 2:
            missing.append('First-hand testing mentions')
            recommendations.append('Add "we tested" or "our lab results" phrases')

        # Check Expertise
        exp_found = sum(1 for pattern, _ in self.EXPERTISE_SIGNALS if re.search(pattern, content, re.I))
        scores['expertise'] = (exp_found / len(self.EXPERTISE_SIGNALS)) * 100
        if exp_found < 2:
            missing.append('Author credentials')
            recommendations.append('Add author bio with credentials')

        # Check Authoritativeness
        auth_found = sum(1 for pattern, _ in self.AUTHORITY_SIGNALS if re.search(pattern, content, re.I))
        scores['authoritativeness'] = (auth_found / len(self.AUTHORITY_SIGNALS)) * 100
        if auth_found < 2:
            missing.append('Citations/references')
            recommendations.append('Add citations from authoritative sources')

        # Check Trustworthiness
        trust_found = sum(1 for pattern, _ in self.TRUST_SIGNALS if re.search(pattern, content, re.I))
        scores['trustworthiness'] = (trust_found / len(self.TRUST_SIGNALS)) * 100
        if trust_found < 3:
            missing.append('Trust indicators')
            recommendations.append('Add last updated date and disclosures')

        # Calculate overall
        overall = sum(scores.values()) / 4
        compliant = overall >= 70

        return EEATReport(
            file_path=str(path),
            scores=EEATScore(**scores, overall=overall),
            missing_elements=missing,
            recommendations=recommendations,
            compliant=compliant
        )

    def check_batch(self, files: List[str | Path], output_file: Optional[str] = None) -> List[EEATReport]:
        """Check multiple files."""
        reports = []
        for f in files:
            report = self.check_file(f)
            reports.append(report)
            status = "✅" if report.compliant else "❌"
            print(f"{status} {f}: EEAT Score {report.scores.overall:.1f}/100")

        if output_file:
            data = {
                "total_files": len(reports),
                "compliant_files": sum(1 for r in reports if r.compliant),
                "avg_score": sum(r.scores.overall for r in reports) / max(len(reports), 1),
                "reports": [
                    {
                        "file": r.file_path,
                        "scores": vars(r.scores),
                        "missing": r.missing_elements,
                        "recommendations": r.recommendations,
                        "compliant": r.compliant
                    }
                    for r in reports
                ]
            }

            with open(Path(output_file), 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

        return reports


def main():
    import argparse
    parser = argparse.ArgumentParser(description="EEAT Compliance Checker")
    parser.add_argument("files", nargs="+")
    parser.add_argument("--output", "-o", default="eeat_compliance_report.json")
    args = parser.parse_args()

    checker = EEATComplianceChecker()
    reports = checker.check_batch(args.files, args.output)

    compliant = sum(1 for r in reports if r.compliant)
    avg = sum(r.scores.overall for r in reports) / max(len(reports), 1)

    print(f"\n{'='*50}")
    print(f"EEAT SUMMARY: {compliant}/{len(reports)} compliant, Avg: {avg:.1f}/100")
    print(f"{'='*50}")

    return 0

if __name__ == "__main__":
    sys.exit(main())

