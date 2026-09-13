#!/usr/bin/env python3
"""
READ-ONLY HTML damage diagnostic for VideoCameraHoliday.

Scans every .html file and reports which ones show signs of:
  - duplicate <head> / <body> tags
  - raw or HTML-escaped git conflict markers
  - JavaScript wrapped inside <style> tags
  - adjacent </style><style> blocks
  - duplicate design-b.css <link> tags
  - stray <base> tags

This script ONLY READS. It never writes, deletes, or moves any file.
"""

from __future__ import annotations

import os
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {
    "templates", "scripts", "node_modules", ".git", "__pycache__",
    "workspace", "data", "docs", "output", "generated-content",
    "city-generator",
}


PATTERNS = {
    "duplicate_head":    re.compile(r"<head\b", re.IGNORECASE),
    "duplicate_body":    re.compile(r"<body\b", re.IGNORECASE),
    "duplicate_html":    re.compile(r"</html>", re.IGNORECASE),
    "raw_conflict":      re.compile(r"^<{7}|^={7}$|^>{7}", re.MULTILINE),
    "escaped_conflict":  re.compile(r"&(lt|gt);{3,}"),
    "js_in_style":       re.compile(r"<style>\s*\n?\s*\(function\s*\(", re.MULTILINE),
    "adjacent_style":    re.compile(r"</style>\s*<style>"),
    "orphan_css_text":   re.compile(r"^\s*\.[a-z][\w-]*\s*\{", re.MULTILINE),
    "stray_base":        re.compile(r"<base\s+href", re.IGNORECASE),
    "design_css_link":   re.compile(
        r'<link[^>]+href="(?:/VideoCameraHoliday)?/assets/design-b\.css"',
        re.IGNORECASE,
    ),
}


def _counts(html: str) -> dict[str, int]:
    return {name: len(pat.findall(html)) for name, pat in PATTERNS.items()}


def classify(path: Path):
    try:
        html = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return {"path": path, "error": str(exc)}

    c = _counts(html)
    issues = []

    if c["duplicate_head"] > 1:
        issues.append(f"multiple <head> ({c['duplicate_head']})")
    if c["duplicate_body"] > 1:
        issues.append(f"multiple <body> ({c['duplicate_body']})")
    if c["duplicate_html"] > 1:
        issues.append(f"multiple </html> ({c['duplicate_html']})")
    if c["raw_conflict"] > 0:
        issues.append(f"raw conflict markers ({c['raw_conflict']})")
    if c["escaped_conflict"] > 0:
        issues.append(f"escaped conflict markers ({c['escaped_conflict']})")
    if c["js_in_style"] > 0:
        issues.append(f"JS in <style> ({c['js_in_style']})")
    if c["adjacent_style"] > 0:
        issues.append(f"</style><style> ({c['adjacent_style']})")
    if c["stray_base"] > 0:
        issues.append(f"stray <base> ({c['stray_base']})")
    if c["design_css_link"] > 1:
        issues.append(f"dup design-b.css link ({c['design_css_link']})")
    if c["orphan_css_text"] > 0 and c["js_in_style"] == 0 and c["adjacent_style"] == 0:
        issues.append(f"orphan CSS text ({c['orphan_css_text']})")

    return {
        "path": path,
        "rel": str(path.relative_to(ROOT)),
        "issues": issues,
        "severity": len(issues),
    }


def iter_candidates() -> list[Path]:
    out = []
    for p in ROOT.rglob("*.html"):
        rel_parts = p.relative_to(ROOT).parts[:-1]
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        if p.name.endswith("_template.html"):
            continue
        out.append(p)
    return out


def print_report(results: list[dict]) -> None:
    clean    = [r for r in results if r.get("severity", 0) == 0]
    broken   = [r for r in results if r.get("severity", 0) >= 1]
    critical = [r for r in broken if r["severity"] >= 3]
    moderate = [r for r in broken if r["severity"] == 2]
    minor    = [r for r in broken if r["severity"] == 1]
    errors   = [r for r in results if "error" in r]

    print("=" * 68)
    print("HTML DAMAGE DIAGNOSTIC (READ-ONLY)")
    print("=" * 68)
    print(f"  Total files scanned : {len(results)}")
    print(f"  Clean               : {len(clean)}")
    print(f"  Broken (any issue)  : {len(broken)}")
    print(f"    critical (3+)     : {len(critical)}")
    print(f"    moderate (2)      : {len(moderate)}")
    print(f"    minor (1)         : {len(minor)}")
    if errors:
        print(f"  Read errors         : {len(errors)}")
    print("=" * 68)
    print()

    def _show(label: str, items: list, limit: int) -> None:
        if not items:
            return
        print(f"{label} — first {min(limit, len(items))} of {len(items)}:")
        print("-" * 68)
        for r in sorted(items, key=lambda x: x["rel"])[:limit]:
            print(f"  {r['rel']}")
            for issue in r["issues"]:
                print(f"      • {issue}")
        if len(items) > limit:
            print(f"  ... and {len(items) - limit} more")
        print()

    _show("🚨 CRITICAL FILES (3+ issues)", critical, 40)
    _show("⚠️  MODERATE FILES (2 issues)", moderate, 30)
    _show("ℹ️  MINOR FILES (1 issue)", minor, 30)

    tally: Counter[str] = Counter()
    for r in broken:
        for issue in r["issues"]:
            tally[issue.split(" (")[0]] += 1
    if tally:
        print("ISSUE TALLY")
        print("-" * 68)
        for issue, count in tally.most_common():
            print(f"  {issue:40s} {count}")
        print()

    if errors:
        print("READ ERRORS")
        print("-" * 68)
        for r in errors:
            print(f"  {r['path']}: {r['error']}")


def write_step_summary(results: list[dict]) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    clean    = [r for r in results if r.get("severity", 0) == 0]
    broken   = [r for r in results if r.get("severity", 0) >= 1]
    critical = [r for r in broken if r["severity"] >= 3]

    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("# HTML Damage Diagnostic (READ-ONLY)\n\n")
        f.write("| Metric | Count |\n|---|---|\n")
        f.write(f"| Files scanned | {len(results)} |\n")
        f.write(f"| Clean | {len(clean)} |\n")
        f.write(f"| Broken | {len(broken)} |\n")
        f.write(f"| Critical (3+) | {len(critical)} |\n\n")
        if critical:
            f.write("## Critical files (first 30)\n\n")
            f.write("| File | Issues |\n|---|---|\n")
            for r in sorted(critical, key=lambda x: x["rel"])[:30]:
                f.write(f"| `{r['rel']}` | {'; '.join(r['issues'])} |\n")


def main() -> int:
    candidates = iter_candidates()
    print(f"Scanning {len(candidates)} HTML files...\n")
    results = [r for r in (classify(p) for p in candidates) if r]
    print_report(results)
    write_step_summary(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
