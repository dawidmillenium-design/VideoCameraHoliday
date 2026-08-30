#!/usr/bin/env python3
"""
Comprehensive audit of broken canonical URLs, incorrect links, and placeholders.
"""

import os
import re
from pathlib import Path
from urllib.parse import urlparse, urljoin
from collections import defaultdict

def extract_html_metadata(html_content, filepath):
    """Extract canonical URL, links, and metadata from HTML."""
    data = {
        'filepath': filepath,
        'canonical': None,
        'links': [],
        'placeholder_links': [],
        'incorrect_root_links': [],
        'h1': None,
    }
    
    # Extract canonical URL
    canonical_match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', html_content)
    if canonical_match:
        data['canonical'] = canonical_match.group(1)
    
    # Extract all href links
    for match in re.finditer(r'href=["\'](#[^"\']*)["\']', html_content):
        data['placeholder_links'].append(match.group(1))
    
    # Extract href="#" specifically
    for match in re.finditer(r'href=["\'](#)["\']', html_content):
        data['placeholder_links'].append('#')
    
    # Extract root-relative links without /VideoCameraHoliday/
    for match in re.finditer(r'href=["\'](/(?!VideoCameraHoliday)[^"\']*\.html)["\']', html_content):
        link = match.group(1)
        data['incorrect_root_links'].append(link)
    
    # Extract H1
    h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content)
    if h1_match:
        data['h1'] = h1_match.group(1).strip()
    
    return data

def get_url_from_filepath(filepath):
    """Convert filesystem path to URL."""
    # Get relative path from repo root
    rel_path = filepath.replace('\\', '/').replace(os.getcwd().replace('\\', '/'), '').lstrip('/')
    # Remove index.html or index2.html
    if rel_path.endswith('index.html') or rel_path.endswith('index2.html'):
        rel_path = rel_path.rsplit('/', 1)[0] + '/'
    elif rel_path == 'index.html':
        rel_path = ''
    
    return f"https://dawidmillenium-design.github.io/VideoCameraHoliday/{rel_path}"

def file_exists_in_repo(canonical_url):
    """Check if the target of a canonical URL exists in the repo."""
    # Parse the canonical URL to extract the path
    parsed = urlparse(canonical_url)
    path = parsed.path.replace('/VideoCameraHoliday/', '')
    
    # Remove trailing slash and look for file
    if path.endswith('/'):
        check_paths = [
            os.path.join(os.getcwd(), path + 'index.html'),
            os.path.join(os.getcwd(), path.rstrip('/') + '.html'),
        ]
    else:
        check_paths = [
            os.path.join(os.getcwd(), path),
        ]
    
    return any(os.path.isfile(p) for p in check_paths)

def scan_directory(root_dir='.'):
    """Scan all HTML files in directory."""
    html_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip .git and assets directories
        dirnames[:] = [d for d in dirnames if d not in ['.git', 'assets', '.github']]
        
        for filename in filenames:
            if filename.endswith('.html'):
                filepath = os.path.join(dirpath, filename)
                html_files.append(filepath)
    
    return sorted(html_files)

def main():
    issues = {
        'broken_canonicals': [],  # Canonical URLs that point to non-existent pages
        'incorrect_root_links': [],  # Links missing /VideoCameraHoliday/
        'placeholder_links': [],  # href="#" or href="#something"
        'orphan_pages': [],  # Pages with canonical but no one links to them
    }
    
    all_canonicals = {}  # Map of canonical URLs to source files
    all_pages = {}  # Map of page URLs to filepaths
    
    print("Scanning HTML files...")
    html_files = scan_directory()
    print(f"Found {len(html_files)} HTML files\n")
    
    # First pass: collect all pages and canonicals
    for filepath in html_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            continue
        
        data = extract_html_metadata(content, filepath)
        page_url = get_url_from_filepath(filepath)
        all_pages[page_url] = filepath
        
        if data['canonical']:
            all_canonicals[data['canonical']] = filepath
    
    # Second pass: validate and collect issues
    for filepath in html_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            continue
        
        data = extract_html_metadata(content, filepath)
        page_url = get_url_from_filepath(filepath)
        
        # Issue 1: Broken canonical URLs
        if data['canonical']:
            canonical = data['canonical']
            # Check if canonical target exists
            if not file_exists_in_repo(canonical):
                issues['broken_canonicals'].append({
                    'file': filepath,
                    'page_url': page_url,
                    'canonical': canonical,
                    'h1': data['h1'],
                })
        
        # Issue 2: Incorrect root-relative links
        if data['incorrect_root_links']:
            for link in data['incorrect_root_links']:
                issues['incorrect_root_links'].append({
                    'file': filepath,
                    'page_url': page_url,
                    'link': link,
                    'h1': data['h1'],
                })
        
        # Issue 3: Placeholder links
        if data['placeholder_links']:
            issues['placeholder_links'].append({
                'file': filepath,
                'page_url': page_url,
                'placeholder_count': len(data['placeholder_links']),
                'h1': data['h1'],
            })
    
    # Report findings
    print("=" * 80)
    print("AUDIT RESULTS")
    print("=" * 80)
    
    print(f"\n1. BROKEN CANONICAL URLs ({len(issues['broken_canonicals'])} pages)")
    print("-" * 80)
    for issue in issues['broken_canonicals'][:10]:  # Show first 10
        rel_path = issue['file'].replace(os.getcwd(), '').lstrip('\\/')
        print(f"  {rel_path}")
        print(f"    Page: {issue['page_url']}")
        print(f"    Canonical: {issue['canonical']}")
    if len(issues['broken_canonicals']) > 10:
        print(f"  ... and {len(issues['broken_canonicals']) - 10} more")
    
    print(f"\n2. INCORRECT ROOT-RELATIVE LINKS ({len(set(i['file'] for i in issues['incorrect_root_links']))} pages)")
    print("-" * 80)
    for issue in issues['incorrect_root_links'][:10]:  # Show first 10
        rel_path = issue['file'].replace(os.getcwd(), '').lstrip('\\/')
        print(f"  {rel_path}")
        print(f"    Link: {issue['link']}")
    if len(issues['incorrect_root_links']) > 10:
        print(f"  ... and {len(issues['incorrect_root_links']) - 10} more")
    
    print(f"\n3. PLACEHOLDER href='#' LINKS ({len(issues['placeholder_links'])} pages, {sum(i['placeholder_count'] for i in issues['placeholder_links'])} total placeholders)")
    print("-" * 80)
    for issue in issues['placeholder_links'][:10]:  # Show first 10
        rel_path = issue['file'].replace(os.getcwd(), '').lstrip('\\/')
        print(f"  {rel_path} ({issue['placeholder_count']} placeholders)")
    if len(issues['placeholder_links']) > 10:
        print(f"  ... and {len(issues['placeholder_links']) - 10} more")
    
    # Save detailed report
    with open('audit_report.txt', 'w', encoding='utf-8') as f:
        f.write("DETAILED CANONICAL URL AUDIT\n")
        f.write("=" * 80 + "\n\n")
        
        for issue in issues['broken_canonicals']:
            rel_path = issue['file'].replace(os.getcwd(), '').lstrip('\\/')
            f.write(f"{rel_path}\n")
            f.write(f"  Current URL: {issue['page_url']}\n")
            f.write(f"  Canonical: {issue['canonical']}\n")
            f.write(f"  Title: {issue['h1']}\n")
            f.write("\n")
    
    print(f"\nDetailed report saved to audit_report.txt")
    print("\nSummary:")
    print(f"  - {len(issues['broken_canonicals'])} pages with broken canonical URLs")
    print(f"  - {len(set(i['file'] for i in issues['incorrect_root_links']))} pages with incorrect root-relative links")
    print(f"  - {len(issues['placeholder_links'])} pages with placeholder links")

if __name__ == '__main__':
    main()
