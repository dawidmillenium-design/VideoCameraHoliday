#!/usr/bin/env python3
"""
Safe Auto-Fix Critical SEO Issues
Automatically repairs missing titles, descriptions, canonicals, and H1s
while safely ignoring Jekyll templates and generated folders.
"""

import os
import json
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

# Configuration from environment
FIX_TITLES = os.getenv('FIX_TITLES', 'true').lower() == 'true'
FIX_DESCRIPTIONS = os.getenv('FIX_DESCRIPTIONS', 'true').lower() == 'true'
FIX_CANONICALS = os.getenv('FIX_CANONICALS', 'true').lower() == 'true'
FIX_H1 = os.getenv('FIX_H1', 'true').lower() == 'true'
CREATE_BACKUPS = os.getenv('CREATE_BACKUPS', 'true').lower() == 'true'
DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'

# 🛡️ CRITICAL: Directories to completely ignore to prevent breaking the site
SKIP_DIRS = {'_includes', '_layouts', '_site', 'node_modules', '.git', 'assets', 'workspace'}

def load_audit_report() -> dict:
    with open('seo-audit-report.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def should_skip_file(filepath: str) -> bool:
    """Check if the file is in a directory we should ignore."""
    path_parts = Path(filepath).parts
    return any(part in SKIP_DIRS for part in path_parts)

def create_backup(filepath: str):
    if CREATE_BACKUPS and not DRY_RUN:
        backup_path = f"{filepath}.bak"
        with open(filepath, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())

def generate_title_from_filename(filepath: str) -> str:
    filename = Path(filepath).stem
    for suffix in ['-index', '-preview', '-diff', '_diff']:
        filename = filename.replace(suffix, '')
    title = filename.replace('-', ' ').replace('_', ' ').title()
    if len(title) < 50:
        title = f"{title} | VideoCameraHoliday"
    return title[:60]

def generate_description_from_content(soup: BeautifulSoup, filepath: str) -> str:
    first_p = soup.find('p')
    if first_p and len(first_p.get_text()) > 100:
        desc = first_p.get_text()[:155].strip()
        if not desc.endswith('.'):
            desc = desc.rsplit(' ', 1)[0] + '...'
        return desc
    
    h1 = soup.find('h1')
    if h1:
        return f"{h1.get_text()[:120]}. Learn more about travel cameras and videography at VideoCameraHoliday."
    
    return f"{generate_title_from_filename(filepath)}. Comprehensive guide for travel photography and videography."

def generate_canonical_url(filepath: str) -> str:
    base_url = "https://dawidmillenium-design.github.io/VideoCameraHoliday"
    clean_path = filepath.replace('\\', '/').lstrip('./')
    if clean_path.endswith('/index.html'):
        clean_path = clean_path.replace('/index.html', '/')
    elif clean_path == 'index.html':
        clean_path = ''
    return f"{base_url}/{clean_path}"

def fix_missing_title(soup: BeautifulSoup, filepath: str) -> bool:
    title = soup.find('title')
    if not title or not title.text.strip():
        new_title = generate_title_from_filename(filepath)
        if soup.head:
            title_tag = soup.new_tag('title')
            title_tag.string = new_title
            soup.head.append(title_tag)
            return True
    return False

def fix_missing_description(soup: BeautifulSoup, filepath: str) -> bool:
    desc = soup.find('meta', attrs={'name': 'description'})
    if not desc or not desc.get('content', '').strip():
        new_desc = generate_description_from_content(soup, filepath)
        if soup.head:
            meta_tag = soup.new_tag('meta', attrs={'name': 'description', 'content': new_desc})
            soup.head.append(meta_tag)
            return True
    return False

def fix_missing_canonical(soup: BeautifulSoup, filepath: str) -> bool:
    canonical = soup.find('link', attrs={'rel': 'canonical'})
    if not canonical or not canonical.get('href', '').strip():
        new_canonical = generate_canonical_url(filepath)
        if soup.head:
            link_tag = soup.new_tag('link', attrs={'rel': 'canonical', 'href': new_canonical})
            soup.head.append(link_tag)
            return True
    return False

def fix_missing_h1(soup: BeautifulSoup, filepath: str) -> bool:
    h1s = soup.find_all('h1')
    if len(h1s) == 0:
        title = soup.find('title')
        h1_text = title.text.split('|')[0].strip() if title else generate_title_from_filename(filepath).replace(' | VideoCameraHoliday', '')
        body = soup.find('body') or soup.find('main')
        if body:
            h1_tag = soup.new_tag('h1')
            h1_tag.string = h1_text
            body.insert(0, h1_tag)
            return True
    return False

def fix_file(filepath: str, issues: list) -> dict:
    result = {'file': filepath, 'fixed': [], 'skipped': [], 'errors': []}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        soup = BeautifulSoup(content, 'lxml')
        modified = False
        
        for issue in issues:
            issue_text = issue.get('issue', '').lower()
            if 'missing title' in issue_text and FIX_TITLES and fix_missing_title(soup, filepath):
                result['fixed'].append('title'); modified = True
            elif 'missing description' in issue_text and FIX_DESCRIPTIONS and fix_missing_description(soup, filepath):
                result['fixed'].append('description'); modified = True
            elif 'missing canonical' in issue_text and FIX_CANONICALS and fix_missing_canonical(soup, filepath):
                result['fixed'].append('canonical'); modified = True
            elif 'no h1' in issue_text and FIX_H1 and fix_missing_h1(soup, filepath):
                result['fixed'].append('h1'); modified = True
        
        if modified and not DRY_RUN:
            create_backup(filepath)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
        return result
    except Exception as e:
        result['errors'].append(str(e))
        return result

def main():
    print("🔧 Starting SAFE SEO Auto-Fix...")
    print("=" * 70)
    if DRY_RUN:
        print("⚠️ DRY RUN MODE - No changes will be made to your files")
    
    report = load_audit_report()
    pages_with_issues = [p for p in report['pages'] if p.get('issues')]
    
    total_issues = total_fixed = total_skipped = total_errors = 0
    by_type = {'titles': 0, 'descriptions': 0, 'canonicals': 0, 'h1s': 0}
    fix_details = []
    skipped_files_count = 0
    
    for page in pages_with_issues:
        filepath = page['filePath']
        issues = page['issues']
        
        if not filepath.endswith('.html') or should_skip_file(filepath):
            skipped_files_count += 1
            continue
            
        if not Path(filepath).exists():
            continue
            
        result = fix_file(filepath, issues)
        total_issues += len(issues)
        total_fixed += len(result['fixed'])
        total_skipped += len(result['skipped'])
        total_errors += len(result['errors'])
        
        if 'title' in result['fixed']: by_type['titles'] += 1
        if 'description' in result['fixed']: by_type['descriptions'] += 1
        if 'canonical' in result['fixed']: by_type['canonicals'] += 1
        if 'h1' in result['fixed']: by_type['h1s'] += 1
        
        if result['fixed']:
            print(f"✅ Fixed: {filepath} ({', '.join(result['fixed'])})")
            
        fix_details.append(result)
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'dry_run': DRY_RUN,
        'total_issues_found': total_issues,
        'files_fixed': total_fixed,
        'files_skipped_templates': skipped_files_count,
        'errors': total_errors,
        'by_type': by_type
    }
    
    with open('seo-fix-summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
        
    print("\n" + "=" * 70)
    print("🎉 Safe SEO Auto-Fix Complete!")
    print(f"📊 Total Issues Processed: {total_issues}")
    print(f"✅ Files Successfully Fixed: {total_fixed}")
    print(f"🛡️ Template Files Safely Skipped: {skipped_files_count}")
    print(f"❌ Errors: {total_errors}")
    
    if DRY_RUN:
        print("\n⚠️ This was a DRY RUN. Run with DRY_RUN=false to apply fixes.")

if __name__ == "__main__":
    main()
