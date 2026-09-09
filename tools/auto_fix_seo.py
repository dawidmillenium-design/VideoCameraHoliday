#!/usr/bin/env python3
"""
Auto-Fix Critical SEO Issues
============================
Reads seo-audit-report.json and automatically fixes critical SEO issues:
- Missing <title>
- Missing <meta name="description">
- Missing <link rel="canonical">
- Missing <h1>

Flags multiple <h1> tags for manual review.

Usage:
    python tools/auto_fix_seo.py [--dry-run true|false] [--base-url URL] [--report FILE]
"""

import json
import os
import sys
import argparse
from datetime import datetime
from bs4 import BeautifulSoup, Comment

# Configuration
DEFAULT_BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday/"
DEFAULT_REPORT = "seo-audit-report.json"
OUTPUT_REPORT = "auto-fix-report.json"
OUTPUT_SUMMARY = "auto-fix-summary.txt"


def parse_args():
    parser = argparse.ArgumentParser(description="Auto-fix critical SEO issues from audit report")
    parser.add_argument("--dry-run", type=str, default="true", help="Run without making changes (true/false)")
    parser.add_argument("--base-url", type=str, default=DEFAULT_BASE_URL, help="Base URL for canonicals")
    parser.add_argument("--report", type=str, default=DEFAULT_REPORT, help="Path to seo-audit-report.json")
    return parser.parse_args()


def load_report(report_path):
    """Load the SEO audit report JSON."""
    if not os.path.exists(report_path):
        print(f"❌ Error: Report file '{report_path}' not found.")
        sys.exit(1)
    
    with open(report_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            # Handle both list and dict with 'pages' key
            if isinstance(data, list):
                return data
            return data.get('pages', [])
        except json.JSONDecodeError:
            print(f"❌ Error: Invalid JSON in '{report_path}'")
            sys.exit(1)


def generate_title_from_h1(soup):
    """Extract text from first H1 for title generation."""
    h1 = soup.find('h1')
    if h1 and h1.get_text(strip=True):
        text = h1.get_text(strip=True)[:60]
        return text
    return None


def generate_title_from_filename(filepath):
    """Generate a title from the filename."""
    name = os.path.basename(filepath)
    name = os.path.splitext(name)[0]
    # Convert kebab-case to Title Case
    title = name.replace('-', ' ').replace('_', ' ').title()
    return title[:60]


def generate_canonical_url(filepath, base_url):
    """Generate canonical URL. Handle index.html -> directory."""
    clean_path = filepath.lstrip('./')
    
    if clean_path.endswith('index.html'):
        dir_path = os.path.dirname(clean_path)
        relative = dir_path if dir_path else ""
        return f"{base_url}{relative}" + ("/" if relative else "")
    else:
        return f"{base_url}{clean_path}"


def generate_description(title, filepath):
    """Generate a default SEO description."""
    clean_title = title.replace('| VideoCameraHoliday', '').strip()
    if len(clean_title) > 60:
        clean_title = clean_title[:57] + "..."
    
    desc = f"Comprehensive review and guide for {clean_title} by VideoCameraHoliday. Expert tips, specs, and comparisons."
    return desc[:155] + "..." if len(desc) > 155 else desc


def fix_page(filepath, base_url, dry_run):
    """Apply SEO fixes to a single HTML file."""
    result = {
        'file': filepath,
        'fixed': [],
        'manual_review': [],
        'error': None
    }

    if not os.path.exists(filepath):
        result['error'] = "File not found"
        return result

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'lxml')
        head = soup.head
        body = soup.body
        
        if not head or not body:
            result['error'] = "Invalid HTML structure (missing head/body)"
            return result

        modified = False
        
        # FIX 1: Missing Title
        if not soup.title:
            h1_title = generate_title_from_h1(soup)
            file_title = generate_title_from_filename(filepath)
            final_title = h1_title if h1_title else file_title
            if not final_title:
                final_title = "VideoCameraHoliday Guide"
            
            title_tag = soup.new_tag("title")
            title_tag.string = f"{final_title} | VideoCameraHoliday"
            head.append(title_tag)
            result['fixed'].append("Added missing <title>")
            modified = True
        elif not soup.title.get_text(strip=True):
            h1_title = generate_title_from_h1(soup)
            file_title = generate_title_from_filename(filepath)
            final_title = h1_title if h1_title else file_title
            soup.title.string = f"{final_title} | VideoCameraHoliday"
            result['fixed'].append("Filled empty <title>")
            modified = True

        # FIX 2: Missing Description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if not meta_desc:
            current_title = soup.title.get_text(strip=True) if soup.title else ""
            desc_content = generate_description(current_title, filepath)
            
            meta_tag = soup.new_tag("meta")
            meta_tag['name'] = 'description'
            meta_tag['content'] = desc_content
            head.insert(0, meta_tag)
            result['fixed'].append("Added missing <meta description>")
            modified = True

        # FIX 3: Missing Canonical
        canonical = soup.find('link', rel='canonical')
        if not canonical:
            url = generate_canonical_url(filepath, base_url)
            link_tag = soup.new_tag("link")
            link_tag['rel'] = 'canonical'
            link_tag['href'] = url
            head.append(link_tag)
            result['fixed'].append(f"Added missing canonical: {url}")
            modified = True

        # FIX 4: Missing H1
        h1_tags = soup.find_all('h1')
        if len(h1_tags) == 0:
            current_title = soup.title.get_text(strip=True) if soup.title else ""
            h1_text = current_title.replace('| VideoCameraHoliday', '').strip()
            if not h1_text:
                h1_text = generate_title_from_filename(filepath)
            
            h1_tag = soup.new_tag("h1")
            h1_tag.string = h1_text
            
            main = soup.find('main')
            if main and main.contents:
                main.insert(0, h1_tag)
            elif body.contents:
                body.insert(0, h1_tag)
            
            result['fixed'].append("Added missing <h1>")
            modified = True
        
        # CHECK: Multiple H1s
        elif len(h1_tags) > 1:
            result['manual_review'].append(f"Found {len(h1_tags)} <h1> tags")
            comment = Comment(" TODO: Multiple H1s detected. Consolidate to single H1. ")
            h1_tags[0].insert_before(comment)
            modified = True

        if modified:
            if dry_run:
                print(f"  [DRY-RUN] Would fix: {filepath}")
            else:
                backup_path = f"{filepath}.bak"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                print(f"  [FIXED] {filepath}")

        return result

    except Exception as e:
        result['error'] = str(e)
        return result


def main():
    args = parse_args()
    dry_run = args.dry_run.lower() == 'true'
    
    print(f"🚀 Auto-Fix SEO Script Started")
    print(f"   Mode: {'DRY-RUN (No changes)' if dry_run else 'APPLY CHANGES'}")
    print(f"   Base URL: {args.base_url}")
    print(f"   Report: {args.report}")
    print("-" * 50)

    pages = load_report(args.report)
    critical_pages = [p for p in pages if p.get('severity') == 'critical']
    
    if not critical_pages:
        print("✅ No critical issues found in report. Nothing to fix.")
        # Still generate empty reports
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'mode': 'dry-run' if dry_run else 'applied',
            'summary': {'total': 0, 'fixed': 0, 'manual_review': 0, 'errors': 0},
            'details': []
        }
        with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        with open(OUTPUT_SUMMARY, 'w', encoding='utf-8') as f:
            f.write("No critical issues found.\n")
        return

    print(f"📊 Found {len(critical_pages)} pages with critical issues.")
    
    stats = {'total': 0, 'fixed': 0, 'manual_review': 0, 'errors': 0}
    results = []

    for page in critical_pages:
        file_path = page.get('file')
        if not file_path:
            url = page.get('url', '').lstrip('/')
            file_path = os.path.join(url, 'index.html') if url.endswith('/') else url
        
        if file_path.startswith('/'):
            file_path = file_path[1:]
            
        res = fix_page(file_path, args.base_url, dry_run)
        results.append(res)
        
        stats['total'] += 1
        if res['error']:
            stats['errors'] += 1
        elif res['fixed']:
            stats['fixed'] += 1
        if res['manual_review']:
            stats['manual_review'] += 1

    # Generate reports
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'mode': 'dry-run' if dry_run else 'applied',
        'summary': stats,
        'details': results
    }

    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)

    summary_lines = [
        "AUTO-FIX SEO SUMMARY",
        "====================",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Mode: {'Dry-Run' if dry_run else 'Applied'}",
        "",
        "Results:",
        f"- Total Pages Processed: {stats['total']}",
        f"- Successfully Fixed: {stats['fixed']}",
        f"- Requires Manual Review: {stats['manual_review']}",
        f"- Errors: {stats['errors']}",
        "",
        "Files requiring manual review (Multiple H1s):"
    ]
    
    for r in results:
        if r.get('manual_review'):
            summary_lines.append(f"- {r['file']}: {', '.join(r['manual_review'])}")

    with open(OUTPUT_SUMMARY, 'w', encoding='utf-8') as f:
        f.write('\n'.join(summary_lines))

    print("-" * 50)
    print(f"✅ Complete!")
    print(f"   Fixed: {stats['fixed']}")
    print(f"   Manual Review Needed: {stats['manual_review']}")
    print(f"   Errors: {stats['errors']}")
    print(f"   Reports saved to: {OUTPUT_REPORT}, {OUTPUT_SUMMARY}")


if __name__ == "__main__":
    main()
