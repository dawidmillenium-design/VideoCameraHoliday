#!/usr/bin/env python3
"""Auto-fix canonical URL issues across HTML files in the repository.

This script:
1. Scans all HTML files in the project
2. Identifies missing or incorrect canonical URLs
3. Auto-generates correct canonical URLs based on file paths
4. Updates files with fixed canonical tags
5. Generates a detailed report of changes made
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional, List, Dict
from urllib.parse import urljoin


BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday/"


class CanonicalParser(HTMLParser):
    """Parse HTML to extract canonical URLs."""
    
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonical: Optional[str] = None
        self.has_head = False
        
    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_dict = dict(attrs)
        
        if tag == "head":
            self.has_head = True
            
        if tag == "link":
            rel = attrs_dict.get("rel", "").lower()
            if "canonical" in rel:
                self.canonical = attrs_dict.get("href", "")


def generate_canonical_url(file_path: Path, root: Path, base_url: str = None) -> str:
    """Generate the correct canonical URL for a file."""
    if base_url is None:
        base_url = BASE_URL
    
    # Get relative path from root
    try:
        rel_path = file_path.relative_to(root)
    except ValueError:
        rel_path = file_path
    
    # Convert to URL path
    url_path = str(rel_path).replace("\\", "/")
    
    # Handle index.html files - should point to directory
    if url_path.endswith("index.html"):
        url_path = url_path[:-10]  # Remove 'index.html'
        if not url_path:
            url_path = ""
        elif not url_path.endswith("/"):
            url_path += "/"
    
    # Build full URL
    canonical = base_url.rstrip("/") + "/" + url_path.lstrip("/")
    
    # Clean up double slashes (except in protocol)
    canonical = re.sub(r'(?<!:)/+', '/', canonical)
    
    return canonical


def fix_canonical_in_file(file_path: Path, dry_run: bool = False, base_url: str = None) -> dict:
    """Fix canonical URL in a single HTML file."""
    if base_url is None:
        base_url = BASE_URL
    
    result = {
        "file": str(file_path),
        "original_canonical": None,
        "new_canonical": None,
        "issue": None,
        "fixed": False,
        "error": None
    }
    
    try:
        content = file_path.read_text(encoding='utf-8')
        parser = CanonicalParser()
        parser.feed(content)
        
        original_canonical = parser.canonical
        result["original_canonical"] = original_canonical
        
        # Generate correct canonical
        root = Path.cwd()
        correct_canonical = generate_canonical_url(file_path, root, base_url)
        result["new_canonical"] = correct_canonical
        
        needs_fix = False
        issue = None
        
        if not original_canonical:
            needs_fix = True
            issue = "missing_canonical"
        elif original_canonical != correct_canonical:
            # Check if it's close but has issues (e.g., http vs https, trailing slash)
            original_normalized = original_canonical.rstrip("/")
            correct_normalized = correct_canonical.rstrip("/")
            
            if original_normalized != correct_normalized:
                needs_fix = True
                issue = f"incorrect_canonical (was: {original_canonical})"
        
        result["issue"] = issue
        
        if needs_fix and not dry_run:
            # Create canonical tag
            canonical_tag = f'<link rel="canonical" href="{correct_canonical}">'
            
            if original_canonical:
                # Replace existing canonical
                pattern = r'<link\s+[^>]*rel=["\']canonical["\'][^>]*>'
                new_content = re.sub(pattern, canonical_tag, content, flags=re.IGNORECASE)
            else:
                # Add canonical after <head>
                new_content = re.sub(
                    r'(<head[^>]*>)',
                    f'\\1\n    {canonical_tag}',
                    content,
                    flags=re.IGNORECASE
                )
            
            file_path.write_text(new_content, encoding='utf-8')
            result["fixed"] = True
        elif needs_fix and dry_run:
            result["fixed"] = True  # Would fix in dry run
            
    except Exception as e:
        result["error"] = str(e)
    
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto-fix canonical URL issues in HTML files")
    ap.add_argument("--root", default=".", help="Root directory to scan")
    ap.add_argument("--pattern", default="**/*.html", help="File pattern to match")
    ap.add_argument("--report", default="canonical-fix-report.json", help="Output report file")
    ap.add_argument("--dry-run", action="store_true", help="Don't modify files, just report")
    ap.add_argument("--base-url", default=BASE_URL, help="Base URL for canonical generation")
    args = ap.parse_args()
    
    # Update BASE_URL if custom base provided
    base_url = args.base_url
    
    root = Path(args.root).resolve()
    html_files = list(root.glob(args.pattern))
    
    # Exclude common non-content directories
    exclude_dirs = {'node_modules', 'venv', '.git', '__pycache__', 'dist', 'build', 'assets'}
    html_files = [f for f in html_files if not any(excl in f.parts for excl in exclude_dirs)]
    
    if not html_files:
        print(f"No HTML files found matching pattern: {args.pattern}", file=sys.stderr)
        return 1
    
    print(f"Scanning {len(html_files)} HTML files...")
    
    results = []
    fixed_count = 0
    error_count = 0
    
    for file_path in sorted(html_files):
        result = fix_canonical_in_file(file_path, dry_run=args.dry_run, base_url=base_url)
        results.append(result)
        
        if result["error"]:
            error_count += 1
            print(f"  ❌ Error in {file_path}: {result['error']}")
        elif result["fixed"]:
            fixed_count += 1
            status = "🔧 Would fix" if args.dry_run else "✅ Fixed"
            print(f"  {status} {file_path}")
            print(f"     Old: {result['original_canonical'] or '(missing)'}")
            print(f"     New: {result['new_canonical']}")
        else:
            print(f"  ✓ OK {file_path}")
    
    # Generate report
    report = {
        "summary": {
            "total_files": len(html_files),
            "fixed_count": fixed_count,
            "error_count": error_count,
            "unchanged_count": len(html_files) - fixed_count - error_count,
            "dry_run": args.dry_run,
            "base_url": base_url
        },
        "results": results
    }
    
    report_path = Path(args.report)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n📊 Report saved to: {report_path}")
    
    if args.dry_run:
        print("\n⚠️  Dry run mode - no files were modified")
        print("   Run without --dry-run to apply fixes")
    
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
