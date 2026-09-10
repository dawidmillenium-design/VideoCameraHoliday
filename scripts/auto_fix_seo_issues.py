#!/usr/bin/env python3
"""
Auto-Fix Critical SEO Issues
Automatically repairs missing titles, descriptions, canonicals, and H1s
based on the seo-audit-report.json
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

def load_audit_report() -> dict:
    """Load the SEO audit report"""
    with open('seo-audit-report.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def create_backup(filepath: str):
    """Create a backup of the file before modifying"""
    if CREATE_BACKUPS and not DRY_RUN:
        backup_path = f"{filepath}.bak"
        with open(filepath, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        print(f"  💾 Created backup: {backup_path}")

def generate_title_from_filename(filepath: str) -> str:
    """Generate a SEO-friendly title from the filename"""
    filename = Path(filepath).stem
    # Remove common suffixes
    for suffix in ['-index', '-preview', '-diff', '_diff']:
        filename = filename.replace(suffix, '')
    
    # Convert slug to title case
    title = filename.replace('-', ' ').replace('_', ' ').title()
    
    # Add site name
    if len(title) < 50:
        title = f"{title} | VideoCameraHoliday"
    
    return title[:60]  # Keep under 60 chars

def generate_description_from_content(soup: BeautifulSoup, filepath: str) -> str:
    """Generate a meta description from the page content"""
    # Try to get first paragraph
    first_p = soup.find('p')
    if first_p and len(first_p.get_text()) > 100:
        desc = first_p.get_text()[:155].strip()
        if not desc.endswith('.'):
            desc = desc.rsplit(' ', 1)[0] + '...'
        return desc
    
    # Try to get from H1
    h1 = soup.find('h1')
    if h1:
        return f"{h1.get_text()[:120]}. Learn more about travel cameras and videography at VideoCameraHoliday."
    
    # Fallback
    title = generate_title_from_filename(filepath)
    return f"{title}. Comprehensive guide for travel photography and videography."

def generate_canonical_url(filepath: str) -> str:
    """Generate canonical URL from file path"""
    base_url = "https://dawidmillenium-design.github.io/VideoCameraHoliday"
    
    # Clean up path
    clean_path = filepath.replace('\\', '/')
    if clean_path.startswith('./'):
        clean_path = clean_path[2:]
    
    # Handle index files
    if clean_path.endswith('/index.html'):
        clean_path = clean_path.replace('/index.html', '/')
    elif clean_path == 'index.html':
        clean_path = ''
    
    return f"{base_url}/{clean_path}"

def fix_missing_title(soup: BeautifulSoup, filepath: str) -> bool:
    """Fix missing title tag"""
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
    """Fix missing meta description"""
    desc = soup.find('meta', attrs={'name': 'description'})
    if not desc or not desc.get('content', '').strip():
        new_desc = generate_description_from_content(soup, filepath)
        if soup.head:
            meta_tag = soup.new_tag('meta', attrs={'name': 'description', 'content': new_desc})
            soup.head.append(meta_tag)
            return True
    return False

def fix_missing_canonical(soup: BeautifulSoup, filepath: str) -> bool:
    """Fix missing canonical URL"""
    canonical = soup.find('link', attrs={'rel': 'canonical'})
    if not canonical or not canonical.get('href', '').strip():
        new_canonical = generate_canonical_url(filepath)
        if soup.head:
            link_tag = soup.new_tag('link', attrs={'rel': 'canonical', 'href': new_canonical})
            soup.head.append(link_tag)
            return True
    return False

def fix_missing_h1(soup: BeautifulSoup, filepath: str) -> bool:
    """Fix missing H1 heading"""
    h1s = soup.find_all('h1')
    if len(h1s) == 0:
        # Generate H1 from title or filename
        title = soup.find('title')
        if title:
            h1_text = title.text.split('|')[0].strip()
        else:
            h1_text = generate_title_from_filename(filepath).replace(' | VideoCameraHoliday', '')
        
        # Insert H1 at the beginning of body or main
        body = soup.find('body') or soup.find('main')
        if body:
            h1_tag = soup.new_tag('h1')
            h1_tag.string = h1_text
            body.insert(0, h1_tag)
            return True
    return False

def fix_file(filepath: str, issues: list) -> dict:
    """Fix all issues in a single file"""
    result = {
        'file': filepath,
        'fixed': [],
        'skipped': [],
        'errors': []
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'lxml')
        modified = False
        
        for issue in issues:
            issue_text = issue.get('issue', '').lower()
            
            if 'missing title' in issue_text and FIX_TITLES:
                if fix_missing_title(soup, filepath):
                    result['fixed'].append('title')
                    modified = True
                else:
                    result['skipped'].append('title')
            
            elif 'missing description' in issue_text and FIX_DESCRIPTIONS:
                if fix_missing_description(soup, filepath):
                    result['fixed'].append('description')
                    modified = True
                else:
                    result['skipped'].append('description')
            
            elif 'missing canonical' in issue_text and FIX_CANONICALS:
                if fix_missing_canonical(soup, filepath):
                    result['fixed'].append('canonical')
                    modified = True
                else:
                    result['skipped'].append('canonical')
            
            elif 'no h1' in issue_text and FIX_H1:
                if fix_missing_h1(soup, filepath):
                    result['fixed'].append('h1')
                    modified = True
                else:
                    result['skipped'].append('h1')
        
        if modified and not DRY_RUN:
            create_backup(filepath)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
        
        return result
        
    except Exception as e:
        result['errors'].append(str(e))
        return result

def main():
    print("🔧 Starting SEO Auto-Fix...")
    print("=" * 70)
    
    if DRY_RUN:
        print("️  DRY RUN MODE - No changes will be made")
        print("=" * 70)
    
    # Load audit report
    report = load_audit_report()
    pages_with_issues = [p for p in report['pages'] if p.get('issues')]
    
    print(f"📊 Found {len(pages_with_issues)} pages with issues")
    print(f" Fixes enabled:")
    print(f"   - Titles: {FIX_TITLES}")
    print(f"   - Descriptions: {FIX_DESCRIPTIONS}")
    print(f"   - Canonicals: {FIX_CANONICALS}")
    print(f"   - H1s: {FIX_H1}")
    print("=" * 70)
    
    # Track statistics
    total_issues = 0
    total_fixed = 0
    total_skipped = 0
    total_errors = 0
    by_type = {
        'titles': 0,
        'descriptions': 0,
        'canonicals': 0,
        'h1s': 0
    }
    
    fix_details = []
    
    # Process each page
    for page in pages_with_issues:
        filepath = page['filePath']
        issues = page['issues']
        
        # Skip non-HTML files
        if not filepath.endswith('.html'):
            continue
        
        # Skip files that don't exist
        if not Path(filepath).exists():
            print(f"⚠️  File not found: {filepath}")
            continue
        
        print(f"\n📄 Processing: {filepath}")
        result = fix_file(filepath, issues)
        
        total_issues += len(issues)
        total_fixed += len(result['fixed'])
        total_skipped += len(result['skipped'])
        total_errors += len(result['errors'])
        
        # Update by_type counts
        if 'title' in result['fixed']:
            by_type['titles'] += 1
        if 'description' in result['fixed']:
            by_type['descriptions'] += 1
        if 'canonical' in result['fixed']:
            by_type['canonicals'] += 1
        if 'h1' in result['fixed']:
            by_type['h1s'] += 1
        
        if result['fixed']:
            print(f"   ✅ Fixed: {', '.join(result['fixed'])}")
        if result['skipped']:
            print(f"   ⚠️  Skipped: {', '.join(result['skipped'])}")
        if result['errors']:
            print(f"   ❌ Errors: {', '.join(result['errors'])}")
        
        fix_details.append(result)
    
    # Generate summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'dry_run': DRY_RUN,
        'total_issues': total_issues,
        'fixed': total_fixed,
        'skipped': total_skipped,
        'errors': total_errors,
        'by_type': by_type,
        'files_processed': len(fix_details)
    }
    
    # Save summary
    with open('seo-fix-summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    with open('seo-fix-details.json', 'w', encoding='utf-8') as f:
        json.dump(fix_details, f, indent=2)
    
    # Print final summary
    print("\n" + "=" * 70)
    print("🎉 SEO Auto-Fix Complete!")
    print("=" * 70)
    print(f"Total Issues: {total_issues}")
    print(f"Fixed: {total_fixed}")
    print(f"Skipped: {total_skipped}")
    print(f"Errors: {total_errors}")
    print("\nBreakdown:")
    for issue_type, count in by_type.items():
        print(f"  - {issue_type}: {count}")
    
    if DRY_RUN:
        print("\n⚠️  This was a DRY RUN. No files were modified.")
        print("Run again with dry_run=false to apply fixes.")
    else:
        print(f"\n✅ All fixes applied. Check git status for changes.")

if __name__ == "__main__":
    main()
