#!/usr/bin/env python3
"""Auto-fix SEO title issues across HTML files in the repository.

This script:
1. Scans all HTML files in the project
2. Identifies titles that are too short, too long, or missing
3. Auto-generates optimized titles based on content
4. Updates files with fixed titles
5. Generates a detailed report of changes made
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional


class TitleParser(HTMLParser):
    """Parse HTML to extract title and main heading."""
    
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: Optional[str] = None
        self.h1: Optional[str] = None
        self.meta_description: Optional[str] = None
        self.in_title = False
        self.in_h1 = False
        self.h1_found = False
        
    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_dict = dict(attrs)
        
        if tag == "title":
            self.in_title = True
            
        if tag == "h1" and not self.h1_found:
            self.in_h1 = True
            self.h1_found = True
            
        if tag == "meta" and attrs_dict.get("name", "").lower() == "description":
            self.meta_description = attrs_dict.get("content", "")
    
    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        elif tag == "h1":
            self.in_h1 = False
    
    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title = (self.title or "") + data
        elif self.in_h1:
            self.h1 = (self.h1 or "") + data


def extract_text_content(html_content: str) -> str:
    """Extract readable text content from HTML for title generation."""
    # Remove script and style elements
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    # Remove comments
    html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
    # Extract text between tags
    text = re.sub(r'<[^>]+>', ' ', html_content)
    # Normalize whitespace
    text = ' '.join(text.split())
    return text[:500]  # Limit to first 500 chars


def generate_optimal_title(content: str, h1: Optional[str], meta_desc: Optional[str], current_title: Optional[str]) -> str:
    """Generate an SEO-optimized title based on content analysis."""
    
    # Priority 1: Use H1 if it exists and is well-formed
    if h1:
        h1_clean = h1.strip()
        if 30 <= len(h1_clean) <= 60:
            return h1_clean
        elif len(h1_clean) < 30 and meta_desc:
            # Combine H1 with part of meta description
            desc_preview = meta_desc[:max(0, 55 - len(h1_clean) - 3)]
            return f"{h1_clean} - {desc_preview}"
    
    # Priority 2: Use meta description if available
    if meta_desc and len(meta_desc) >= 30:
        words = meta_desc.split()
        title = ""
        for word in words:
            if len(title) + len(word) + 1 > 55:
                break
            title = f"{title} {word}".strip()
        if title:
            return title
    
    # Priority 3: Extract from content
    text_content = content.strip()
    if text_content:
        # Try to get first sentence or meaningful phrase
        sentences = re.split(r'[.!?]', text_content)
        for sentence in sentences:
            sentence = sentence.strip()
            if 20 <= len(sentence) <= 60 and len(sentence.split()) >= 3:
                return sentence
        
        # Fallback: truncate first meaningful chunk
        words = text_content.split()[:10]
        return ' '.join(words)
    
    # Last resort: generic title
    return "Video Camera Holiday - Professional Services"


def validate_title(title: Optional[str]) -> tuple[bool, list[str]]:
    """Validate title and return issues found."""
    issues = []
    
    if not title or not title.strip():
        issues.append("missing")
        return False, issues
    
    title = title.strip()
    length = len(title)
    
    if length < 30:
        issues.append(f"too_short ({length} chars, min 30)")
    elif length > 60:
        issues.append(f"too_long ({length} chars, max 60)")
    
    # Check for keyword stuffing (repeated words)
    words = title.lower().split()
    word_counts = {}
    for word in words:
        if len(word) > 3:  # Ignore short words
            word_counts[word] = word_counts.get(word, 0) + 1
    
    for word, count in word_counts.items():
        if count > 2:
            issues.append(f"keyword_stuffing ('{word}' appears {count} times)")
    
    return len(issues) == 0, issues


def fix_title_in_file(file_path: Path, dry_run: bool = False) -> dict:
    """Fix title in a single HTML file."""
    result = {
        "file": str(file_path),
        "original_title": None,
        "new_title": None,
        "issues": [],
        "fixed": False,
        "error": None
    }
    
    try:
        content = file_path.read_text(encoding='utf-8')
        parser = TitleParser()
        parser.feed(content)
        
        original_title = parser.title.strip() if parser.title else None
        result["original_title"] = original_title
        
        is_valid, issues = validate_title(original_title)
        result["issues"] = issues
        
        if not is_valid:
            # Generate new title
            text_content = extract_text_content(content)
            new_title = generate_optimal_title(
                text_content, 
                parser.h1, 
                parser.meta_description,
                original_title
            )
            result["new_title"] = new_title
            
            if not dry_run:
                # Replace title in HTML
                if original_title:
                    # Replace existing title
                    new_content = re.sub(
                        r'<title>.*?</title>',
                        f'<title>{new_title}</title>',
                        content,
                        flags=re.IGNORECASE | re.DOTALL
                    )
                else:
                    # Add title after <head>
                    new_content = re.sub(
                        r'(<head[^>]*>)',
                        f'\\1\n    <title>{new_title}</title>',
                        content,
                        flags=re.IGNORECASE
                    )
                
                file_path.write_text(new_content, encoding='utf-8')
            
            result["fixed"] = True
        else:
            result["new_title"] = original_title
            
    except Exception as e:
        result["error"] = str(e)
    
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto-fix SEO title issues in HTML files")
    ap.add_argument("--root", default=".", help="Root directory to scan")
    ap.add_argument("--pattern", default="**/*.html", help="File pattern to match")
    ap.add_argument("--report", default="title-fix-report.json", help="Output report file")
    ap.add_argument("--dry-run", action="store_true", help="Don't modify files, just report")
    ap.add_argument("--min-length", type=int, default=30, help="Minimum title length")
    ap.add_argument("--max-length", type=int, default=60, help="Maximum title length")
    args = ap.parse_args()
    
    root = Path(args.root).resolve()
    html_files = list(root.glob(args.pattern))
    
    # Exclude common non-content directories
    exclude_dirs = {'node_modules', 'venv', '.git', '__pycache__', 'dist', 'build'}
    html_files = [f for f in html_files if not any(excl in f.parts for excl in exclude_dirs)]
    
    if not html_files:
        print(f"No HTML files found matching pattern: {args.pattern}", file=sys.stderr)
        return 1
    
    print(f"Scanning {len(html_files)} HTML files...")
    
    results = []
    fixed_count = 0
    error_count = 0
    
    for file_path in html_files:
        result = fix_title_in_file(file_path, dry_run=args.dry_run)
        results.append(result)
        
        if result["error"]:
            error_count += 1
            print(f"  ❌ Error in {file_path}: {result['error']}")
        elif result["fixed"]:
            fixed_count += 1
            status = "🔧 Would fix" if args.dry_run else "✅ Fixed"
            print(f"  {status} {file_path}")
            print(f"     Old: {result['original_title'] or '(missing)'}")
            print(f"     New: {result['new_title']}")
        else:
            print(f"  ✓ OK {file_path}")
    
    # Generate report
    report = {
        "summary": {
            "total_files": len(html_files),
            "fixed_count": fixed_count,
            "error_count": error_count,
            "unchanged_count": len(html_files) - fixed_count - error_count,
            "dry_run": args.dry_run
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
