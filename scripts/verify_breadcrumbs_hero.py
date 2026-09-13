#!/usr/bin/env python3
"""
verify_breadcrumbs_hero.py

Scans HTML files to verify the presence of Breadcrumbs, Hero Sections, and Schema.org markup.
Excludes temporary directories like workspace/, city-generator/, and generated-content/.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
# Directories to completely ignore during scanning
EXCLUDE_DIRS = {
    '.git', 
    'node_modules', 
    'templates', 
    'backups', 
    'scripts', 
    'workspace',        # Ignored: Temporary work files
    'city-generator',   # Ignored: Auto-generated drafts
    'generated-content' # Ignored: Staging content
}

REPO_ROOT = Path(__file__).parent.parent

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def get_encoding(file_path):
    """Detect encoding."""
    for enc in ['utf-8', 'latin-1']:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read()
            return enc
        except:
            continue
    return 'utf-8'

def check_breadcrumbs(soup):
    """Check for valid breadcrumb indicators."""
    # Look for nav with breadcrumbs class or aria-label
    if soup.find('nav', class_='breadcrumbs'):
        return True
    if soup.find('nav', attrs={'aria-label': 'Breadcrumb'}):
        return True
    if soup.find(attrs={'itemtype': 'https://schema.org/BreadcrumbList'}):
        return True
    
    # Check JSON-LD
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        if script.string and '"BreadcrumbList"' in script.string:
            try:
                # Validate JSON structure roughly
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'BreadcrumbList':
                    return True
                if isinstance(data, list):
                    for item in data:
                        if item.get('@type') == 'BreadcrumbList':
                            return True
            except json.JSONDecodeError:
                continue
    return False

def check_hero(soup):
    """Check for hero section indicators."""
    if soup.find('section', class_='hero'):
        return True
    if soup.find('div', class_='hero'):
        return True
    if soup.find('header', class_='hero'):
        return True
    if soup.find('section', class_='article-hero'):
        return True
    if soup.find('div', class_='hero-banner'):
        return True
    return False

def check_h1(soup):
    """Check for valid H1 tag."""
    h1 = soup.find('h1')
    if not h1:
        return False, "Missing H1 tag"
    text = h1.get_text().strip()
    if not text:
        return False, "Empty H1 tag"
    # Check for obvious truncation bugs (e.g., "Best s 2026")
    if re.search(r'^[A-Z][a-z]*\s[s]\s\d{4}$', text):
        return False, f"Truncated H1: '{text}'"
    return True, "OK"

def check_json_ld(soup):
    """Check for valid BreadcrumbList JSON-LD."""
    scripts = soup.find_all('script', type='application/ld+json')
    found_valid = False
    errors = []
    
    for script in scripts:
        if not script.string:
            continue
        if '"BreadcrumbList"' in script.string:
            try:
                data = json.loads(script.string)
                # Handle both single object and array of objects
                items = data if isinstance(data, list) else [data]
                
                for item in items:
                    if item.get('@type') == 'BreadcrumbList':
                        found_valid = True
                        # Check structure
                        if 'itemListElement' not in item:
                            errors.append("Missing itemListElement")
                        else:
                            # Check for relative URLs
                            for entry in item['itemListElement']:
                                if isinstance(entry, dict):
                                    url = entry.get('item', '')
                                    if url and not url.startswith('http'):
                                        errors.append(f"Item {entry.get('position')} has relative URL: '{url}'")
                                    # Check positions
                                    if not isinstance(entry.get('position'), int):
                                        errors.append(f"Invalid position type")
            except json.JSONDecodeError:
                errors.append("Invalid JSON syntax")
    
    if not found_valid:
        return False, ["Missing BreadcrumbList schema"]
    if errors:
        return False, errors
    return True, "OK"

def scan_file(file_path):
    """Scan a single file and return status."""
    encoding = get_encoding(file_path)
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'lxml')
        
        # Checks
        has_breadcrumbs = check_breadcrumbs(soup)
        has_hero = check_hero(soup)
        h1_ok, h1_msg = check_h1(soup)
        json_ok, json_msg = check_json_ld(soup)
        
        passed = has_breadcrumbs and has_hero and h1_ok and json_ok
        
        issues = []
        if not has_breadcrumbs:
            issues.append("Missing Breadcrumbs")
        if not has_hero:
            issues.append("Missing Hero")
        if not h1_ok:
            issues.append(f"H1({h1_msg})")
        if not json_ok:
            issues.append(f"JSON({json_msg})")
            
        return passed, issues
        
    except Exception as e:
        return False, [f"Error: {str(e)}"]

def main():
    parser = argparse.ArgumentParser(description="Verify Breadcrumbs and Hero injection")
    parser.add_argument('--verbose', action='store_true', help="Show all files")
    parser.add_argument('--json', action='store_true', help="Output JSON")
    parser.add_argument('--fail-if-below', type=float, default=90.0, help="Fail if pass rate below %")
    parser.add_argument('--output', type=str, help="Save report to file")
    
    args = parser.parse_args()
    
    html_files = []
    for path in REPO_ROOT.rglob("*.html"):
        if any(excl in str(path) for excl in EXCLUDE_DIRS):
            continue
        html_files.append(path)
    
    results = {
        'total': len(html_files),
        'passed': 0,
        'failed': 0,
        'failed_files': []
    }
    
    output_lines = []
    output_lines.append("🔍 Starting Verification Scan...")
    output_lines.append(f"📂 Found {len(html_files)} content files to scan.\n")
    
    for file_path in html_files:
        passed, issues = scan_file(file_path)
        rel_path = str(file_path.relative_to(REPO_ROOT))
        
        if passed:
            results['passed'] += 1
            if args.verbose:
                print(f"✅ {rel_path}")
        else:
            results['failed'] += 1
            results['failed_files'].append({'path': rel_path, 'issues': issues})
            if args.verbose:
                print(f"❌ {rel_path}: {', '.join(issues)}")
    
    # Summary
    pass_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
    
    summary = f"""
==================================================
📊 TOTAL SCANNED: {results['total']}
✅ PASSED: {results['passed']} ({pass_rate:.1f}%)
❌ FAILED: {results['failed']}
==================================================
"""
    print(summary)
    output_lines.append(summary)
    
    # List failures by category
    missing_h1 = []
    missing_json = []
    both_failed = []
    
    for item in results['failed_files']:
        issues_str = " | ".join(item['issues'])
        h1_fail = any("H1" in i for i in item['issues'])
        json_fail = any("JSON" in i for i in item['issues'])
        
        if h1_fail and json_fail:
            both_failed.append(f"   - {item['path']}: {issues_str}")
        elif h1_fail:
            missing_h1.append(f"   - {item['path']}: {issues_str}")
        elif json_fail:
            missing_json.append(f"   - {item['path']}: {issues_str}")
    
    if missing_h1:
        print(f"\n🔴 BROKEN H1 TEXT:")
        for line in missing_h1[:10]: print(line)
        if len(missing_h1) > 10: print(f"   ... and {len(missing_h1)-10} more")
        
    if missing_json:
        print(f"\n🔴 INVALID JSON-LD:")
        for line in missing_json[:10]: print(line)
        if len(missing_json) > 10: print(f"   ... and {len(missing_json)-10} more")
        
    if both_failed:
        print(f"\n🔴 BOTH FAILED:")
        for line in both_failed[:10]: print(line)
        if len(both_failed) > 10: print(f"   ... and {len(both_failed)-10} more")

    # Save report if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write("\n".join(output_lines))
        print(f"\n💾 Report saved to {args.output}")

    # Exit code logic
    if pass_rate < args.fail_if_below:
        print(f"\n❌ FAIL: Pass rate {pass_rate:.1f}% is below threshold {args.fail_if_below}%")
        sys.exit(1)
    else:
        print(f"\n🎉 SUCCESS: Pass rate {pass_rate:.1f}% meets threshold.")
        sys.exit(0)

if __name__ == "__main__":
    main()
