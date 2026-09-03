#!/usr/bin/env python3
"""
Thin Content Audit Script for VideoCameraHoliday Repository
============================================================

Scans all HTML files and identifies pages with thin content that could hurt SEO rankings.

Usage:
    python thin_content_audit.py [--repo-path PATH] [--output OUTPUT_FILE]

Author: SEO Audit Tool
Date: 2026-09-04
"""

import os
import re
import json
import argparse
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict


# Directories to exclude from audit
EXCLUDE_DIRS = {'assets', '_includes', '_layouts', 'node_modules', '.git', '__pycache__', 'repo_audit'}

# Thin content thresholds
WORD_COUNT_CRITICAL = 300
WORD_COUNT_WARNING = 500
META_DESC_MIN_LENGTH = 100
TITLE_MIN_LENGTH = 30
TITLE_MAX_LENGTH = 60


def find_html_files(repo_path):
    """Recursively find all HTML files, excluding specified directories."""
    html_files = []
    repo_path = Path(repo_path)
    
    for root, dirs, files in os.walk(repo_path):
        # Exclude specified directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if file.endswith('.html'):
                file_path = Path(root) / file
                # Also skip files in excluded subdirectories
                if any(exclude in str(file_path.relative_to(repo_path)) for exclude in EXCLUDE_DIRS):
                    continue
                html_files.append(file_path)
    
    return sorted(html_files)


def extract_visible_text(soup):
    """Extract visible text content, excluding script, style, and other non-content tags."""
    # Remove script and style elements
    for tag in soup.find_all(['script', 'style', 'noscript']):
        tag.decompose()
    
    # Remove navigation, footer, and other repeated content for word count
    # But keep them for link analysis
    text = soup.get_text(separator=' ', strip=True)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    return text


def count_words(text):
    """Count words in text."""
    if not text:
        return 0
    # Split by whitespace and filter empty strings
    words = [w for w in text.split() if len(w) > 1]
    return len(words)


def analyze_html_file(file_path, repo_path):
    """Analyze a single HTML file for content metrics."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {
            'file_path': str(file_path.relative_to(repo_path)),
            'error': f"Could not read file: {str(e)}",
            'status': 'ERROR'
        }
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Extract visible text
    visible_text = extract_visible_text(soup)
    word_count = count_words(visible_text)
    char_count = len(visible_text)
    
    # Count headings
    h1_count = len(soup.find_all('h1'))
    h2_count = len(soup.find_all('h2'))
    h3_count = len(soup.find_all('h3'))
    
    # Count paragraphs
    p_count = len(soup.find_all('p'))
    
    # Count list items
    li_count = len(soup.find_all('li'))
    
    # Analyze images
    images = soup.find_all('img')
    images_total = len(images)
    images_with_alt = sum(1 for img in images if img.get('alt', '').strip())
    images_without_alt = images_total - images_with_alt
    
    # Meta description
    meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
    meta_description = meta_desc_tag.get('content', '') if meta_desc_tag else ''
    meta_desc_length = len(meta_description)
    
    # Title tag
    title_tag = soup.find('title')
    title = title_tag.get_text(strip=True) if title_tag else ''
    title_length = len(title)
    
    # Count links
    links = soup.find_all('a', href=True)
    internal_links = 0
    external_links = 0
    
    base_domain = 'dawidmillenium-design.github.io'
    
    for link in links:
        href = link.get('href', '')
        if href.startswith(('http://', 'https://')):
            if base_domain in href or href.startswith('/'):
                internal_links += 1
            else:
                external_links += 1
        elif href.startswith('/') or href.startswith('#'):
            internal_links += 1
        else:
            # Relative links
            internal_links += 1
    
    # Determine status
    issues = []
    status = 'PASS'
    
    if word_count < WORD_COUNT_CRITICAL:
        status = 'CRITICAL'
        issues.append(f"Word count ({word_count}) is below critical threshold ({WORD_COUNT_CRITICAL})")
    elif word_count < WORD_COUNT_WARNING:
        status = 'THIN'
        issues.append(f"Word count ({word_count}) is below warning threshold ({WORD_COUNT_WARNING})")
    
    if h2_count == 0 and word_count > 50:  # Only flag if there's some content
        issues.append("No H2 headings found")
        if status == 'PASS':
            status = 'THIN'
    
    if meta_desc_length < META_DESC_MIN_LENGTH and meta_desc_length > 0:
        issues.append(f"Meta description ({meta_desc_length} chars) is too short (min: {META_DESC_MIN_LENGTH})")
        if status == 'PASS':
            status = 'THIN'
    
    if images_total == 0 and word_count > 100:
        issues.append("No images found")
        if status == 'PASS':
            status = 'THIN'
    
    if internal_links == 0 and word_count > 100:
        issues.append("No internal links found")
        if status == 'PASS':
            status = 'THIN'
    
    # Generate recommendations
    recommendations = []
    if word_count < WORD_COUNT_WARNING:
        recommendations.append(f"Expand content to at least {WORD_COUNT_WARNING} words with more detailed information, examples, and FAQs.")
    if h2_count == 0:
        recommendations.append("Add H2 headings to structure content and improve readability.")
    if meta_desc_length < META_DESC_MIN_LENGTH:
        recommendations.append(f"Write a compelling meta description of 150-160 characters.")
    if images_total == 0:
        recommendations.append("Add relevant images with descriptive alt text to enhance content.")
    if internal_links == 0:
        recommendations.append("Add internal links to related articles to improve site navigation and SEO.")
    if images_without_alt > 0:
        recommendations.append(f"Add alt text to {images_without_alt} image(s) for accessibility and SEO.")
    
    return {
        'file_path': str(file_path.relative_to(repo_path)),
        'url_path': '/' + str(file_path.relative_to(repo_path)).replace('\\', '/'),
        'title': title[:100] if title else 'No title',
        'word_count': word_count,
        'char_count': char_count,
        'headings': {
            'h1': h1_count,
            'h2': h2_count,
            'h3': h3_count,
            'total': h1_count + h2_count + h3_count
        },
        'paragraph_count': p_count,
        'list_items_count': li_count,
        'images': {
            'total': images_total,
            'with_alt': images_with_alt,
            'without_alt': images_without_alt
        },
        'meta_description': meta_description[:50] + '...' if len(meta_description) > 50 else meta_description,
        'meta_description_length': meta_desc_length,
        'title_length': title_length,
        'links': {
            'internal': internal_links,
            'external': external_links,
            'total': internal_links + external_links
        },
        'status': status,
        'issues': issues,
        'recommendations': recommendations
    }


def generate_report(results, output_format='markdown'):
    """Generate audit report in specified format."""
    
    # Sort results by status (CRITICAL first, then THIN, then PASS)
    status_order = {'CRITICAL': 0, 'THIN': 1, 'ERROR': 2, 'PASS': 3}
    results_sorted = sorted(results, key=lambda x: status_order.get(x.get('status', 'PASS'), 3))
    
    # Summary statistics
    total_files = len(results)
    critical_count = sum(1 for r in results if r.get('status') == 'CRITICAL')
    thin_count = sum(1 for r in results if r.get('status') == 'THIN')
    pass_count = sum(1 for r in results if r.get('status') == 'PASS')
    error_count = sum(1 for r in results if r.get('status') == 'ERROR')
    
    avg_word_count = sum(r.get('word_count', 0) for r in results if r.get('word_count')) / max(1, len([r for r in results if r.get('word_count')]))
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if output_format == 'json':
        report = {
            'audit_metadata': {
                'timestamp': timestamp,
                'total_files_scanned': total_files,
                'thresholds': {
                    'word_count_critical': WORD_COUNT_CRITICAL,
                    'word_count_warning': WORD_COUNT_WARNING,
                    'meta_description_min': META_DESC_MIN_LENGTH
                }
            },
            'summary': {
                'total_files': total_files,
                'critical': critical_count,
                'thin': thin_count,
                'pass': pass_count,
                'errors': error_count,
                'average_word_count': round(avg_word_count, 1)
            },
            'results': results_sorted
        }
        return json.dumps(report, indent=2)
    
    # Markdown format
    md = []
    md.append("# 🔍 Thin Content Audit Report")
    md.append("")
    md.append(f"**Generated:** {timestamp}")
    md.append("")
    
    # Summary section
    md.append("## 📊 Summary")
    md.append("")
    md.append(f"| Metric | Value |")
    md.append(f"|--------|-------|")
    md.append(f"| Total Files Scanned | {total_files} |")
    md.append(f"| ✅ Pass | {pass_count} |")
    md.append(f"| ⚠️ Thin Content | {thin_count} |")
    md.append(f"| 🚨 Critical | {critical_count} |")
    md.append(f"| ❌ Errors | {error_count} |")
    md.append(f"| 📈 Average Word Count | {avg_word_count:.1f} |")
    md.append("")
    
    # Thresholds
    md.append("### 🎯 Thresholds Used")
    md.append("")
    md.append(f"- **Critical:** Word count < {WORD_COUNT_CRITICAL}")
    md.append(f"- **Warning:** Word count < {WORD_COUNT_WARNING}")
    md.append(f"- **Meta Description Minimum:** {META_DESC_MIN_LENGTH} characters")
    md.append("")
    
    # Critical issues
    critical_results = [r for r in results_sorted if r.get('status') == 'CRITICAL']
    if critical_results:
        md.append("## 🚨 Critical Issues (Immediate Action Required)")
        md.append("")
        for result in critical_results:
            md.append(f"### [{result['file_path']}]({result.get('url_path', result['file_path'])})")
            md.append("")
            md.append(f"**Title:** {result.get('title', 'N/A')}")
            md.append("")
            md.append(f"| Metric | Value |")
            md.append(f"|--------|-------|")
            md.append(f"| Word Count | {result.get('word_count', 0)} |")
            md.append(f"| Headings (H1/H2/H3) | {result.get('headings', {}).get('h1', 0)}/{result.get('headings', {}).get('h2', 0)}/{result.get('headings', {}).get('h3', 0)} |")
            md.append(f"| Paragraphs | {result.get('paragraph_count', 0)} |")
            md.append(f"| Images | {result.get('images', {}).get('total', 0)} |")
            md.append(f"| Internal Links | {result.get('links', {}).get('internal', 0)} |")
            md.append("")
            
            if result.get('issues'):
                md.append("**Issues:**")
                for issue in result['issues']:
                    md.append(f"- ❌ {issue}")
                md.append("")
            
            if result.get('recommendations'):
                md.append("**Recommendations:**")
                for rec in result['recommendations']:
                    md.append(f"- 💡 {rec}")
                md.append("")
            
            md.append("---")
            md.append("")
    
    # Thin content warnings
    thin_results = [r for r in results_sorted if r.get('status') == 'THIN']
    if thin_results:
        md.append("## ⚠️ Thin Content Warnings")
        md.append("")
        for result in thin_results:
            md.append(f"### [{result['file_path']}]({result.get('url_path', result['file_path'])})")
            md.append("")
            md.append(f"**Title:** {result.get('title', 'N/A')} | **Words:** {result.get('word_count', 0)}")
            md.append("")
            
            if result.get('issues'):
                md.append("**Issues:**")
                for issue in result['issues']:
                    md.append(f"- ⚠️ {issue}")
                md.append("")
            
            if result.get('recommendations'):
                md.append("**Recommendations:**")
                for rec in result['recommendations']:
                    md.append(f"- 💡 {rec}")
                md.append("")
            
            md.append("---")
            md.append("")
    
    # Top performers (optional)
    pass_results = [r for r in results_sorted if r.get('status') == 'PASS']
    if pass_results:
        top_performers = sorted(pass_results, key=lambda x: x.get('word_count', 0), reverse=True)[:10]
        md.append("## ✅ Top Performing Pages (by Word Count)")
        md.append("")
        md.append("| Rank | File | Word Count | Headings | Images |")
        md.append("|------|------|------------|----------|--------|")
        for i, result in enumerate(top_performers, 1):
            h = result.get('headings', {})
            md.append(f"| {i} | {result['file_path'].split('/')[-1]} | {result.get('word_count', 0)} | {h.get('h1', 0)+h.get('h2', 0)+h.get('h3', 0)} | {result.get('images', {}).get('total', 0)} |")
        md.append("")
    
    # Error reports
    error_results = [r for r in results_sorted if r.get('status') == 'ERROR']
    if error_results:
        md.append("## ❌ File Read Errors")
        md.append("")
        for result in error_results:
            md.append(f"- `{result['file_path']}`: {result.get('error', 'Unknown error')}")
        md.append("")
    
    return '\n'.join(md)


def main():
    parser = argparse.ArgumentParser(description='Thin Content Audit for SEO')
    parser.add_argument('--repo-path', default='/workspace', help='Path to repository root')
    parser.add_argument('--output', default='thin_content_audit_report.md', help='Output file path')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown', help='Output format')
    parser.add_argument('--exclude-dirs', nargs='+', default=[], help='Additional directories to exclude')
    
    args = parser.parse_args()
    
    # Add custom exclude directories
    if args.exclude_dirs:
        EXCLUDE_DIRS.update(args.exclude_dirs)
    
    print(f"🔍 Starting Thin Content Audit...")
    print(f"📁 Repository Path: {args.repo_path}")
    print(f"📄 Output File: {args.output}")
    print(f"📊 Format: {args.format}")
    print("")
    
    # Find all HTML files
    print("📂 Scanning for HTML files...")
    html_files = find_html_files(args.repo_path)
    print(f"   Found {len(html_files)} HTML files to analyze")
    print("")
    
    # Analyze each file
    print("🔬 Analyzing content...")
    results = []
    for i, file_path in enumerate(html_files, 1):
        if i % 100 == 0:
            print(f"   Processed {i}/{len(html_files)} files...")
        result = analyze_html_file(file_path, args.repo_path)
        results.append(result)
    
    print(f"   ✅ Completed analysis of {len(results)} files")
    print("")
    
    # Generate report
    print("📝 Generating report...")
    report = generate_report(results, args.format)
    
    # Write report to file
    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"   ✅ Report saved to: {output_path.absolute()}")
    print("")
    
    # Print summary
    critical_count = sum(1 for r in results if r.get('status') == 'CRITICAL')
    thin_count = sum(1 for r in results if r.get('status') == 'THIN')
    pass_count = sum(1 for r in results if r.get('status') == 'PASS')
    
    print("=" * 60)
    print("📊 AUDIT SUMMARY")
    print("=" * 60)
    print(f"Total Files Scanned: {len(results)}")
    print(f"✅ Pass:           {pass_count}")
    print(f"⚠️  Thin Content:   {thin_count}")
    print(f"🚨 Critical:        {critical_count}")
    print("=" * 60)
    
    if critical_count > 0:
        print("")
        print("🚨 CRITICAL ISSUES FOUND - Immediate action required!")
        print("   Review the report for detailed recommendations.")
    
    print("")
    print(f"Full report available at: {output_path.absolute()}")


if __name__ == '__main__':
    main()
