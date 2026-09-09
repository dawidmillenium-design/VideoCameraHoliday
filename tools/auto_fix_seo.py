#!/usr/bin/env python3
"""
Auto-Fix SEO Script for VideoCameraHoliday

This script reads seo-audit-report.json and automatically fixes critical SEO issues:
- Missing <title> tags
- Missing <meta name="description"> tags
- Missing <link rel="canonical"> tags
- Missing or multiple <h1> tags

Usage:
    python tools/auto_fix_seo.py [--dry-run] [--base-url BASE_URL]

Arguments:
    --dry-run       Show what would be fixed without making changes (default: True)
    --base-url      Base URL for canonical links (default: https://dawidmillenium-design.github.io/VideoCameraHoliday/)

Output:
    - auto-fix-report.json: Detailed JSON report of all fixes
    - auto-fix-summary.txt: Human-readable summary
    - Backup files (.bak) created for each modified file
"""

import json
import os
import sys
import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

try:
    from bs4 import BeautifulSoup, Tag
except ImportError:
    print("ERROR: beautifulsoup4 not installed. Run: pip install beautifulsoup4 lxml")
    sys.exit(1)


class SEOFixer:
    """Automated SEO issue fixer using BeautifulSoup for safe HTML manipulation."""
    
    def __init__(self, base_url: str = "https://dawidmillenium-design.github.io/VideoCameraHoliday/", dry_run: bool = True):
        self.base_url = base_url.rstrip('/')
        self.dry_run = dry_run
        self.fixed_count = 0
        self.manual_review_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.fixes_log: List[Dict[str, Any]] = []
        self.manual_review_items: List[Dict[str, Any]] = []
        
    def generate_title_from_filename(self, filepath: str) -> str:
        """Generate SEO-friendly title from filename."""
        filename = Path(filepath).stem
        
        # Remove common prefixes/suffixes
        filename = re.sub(r'^index$', 'Home', filename)
        filename = re.sub(r'[-_]', ' ', filename)
        
        # Capitalize words
        title = ' '.join(word.capitalize() for word in filename.split())
        
        # Add site branding
        return f"{title} | VideoCameraHoliday"
    
    def generate_title_from_h1(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract title from first H1 tag if present."""
        h1 = soup.find('h1')
        if h1 and h1.get_text(strip=True):
            text = h1.get_text(strip=True)[:60]
            return f"{text} | VideoCameraHoliday"
        return None
    
    def generate_description_from_content(self, soup: BeautifulSoup, filepath: str) -> str:
        """Generate default SEO-friendly description."""
        filename = Path(filepath).stem
        filename_clean = re.sub(r'[-_]', ' ', filename)
        filename_cap = ' '.join(word.capitalize() for word in filename_clean.split())
        
        # Try to extract first paragraph for better description
        first_p = soup.find('p')
        if first_p and first_p.get_text(strip=True):
            text = first_p.get_text(strip=True)[:150]
            if len(text) > 50:
                return f"{text}..." if len(text) >= 150 else text
        
        # Default template
        return f"Comprehensive review and guide for {filename_cap} by VideoCameraHoliday. Expert analysis, comparisons, and buying advice."
    
    def generate_canonical_url(self, filepath: str) -> str:
        """Generate canonical URL from file path."""
        # Remove leading ./ if present
        clean_path = filepath.lstrip('./')
        
        # Handle index.html - point to directory
        if clean_path.endswith('index.html'):
            dir_path = clean_path.replace('index.html', '').rstrip('/')
            return f"{self.base_url}/{dir_path}" if dir_path else f"{self.base_url}/"
        
        return f"{self.base_url}/{clean_path}"
    
    def fix_missing_title(self, soup: BeautifulSoup, filepath: str) -> Tuple[bool, str]:
        """Fix missing title tag."""
        title_tag = soup.find('title')
        
        if title_tag and title_tag.get_text(strip=True):
            return False, "Title exists"
        
        # Try to get title from H1 first
        new_title = self.generate_title_from_h1(soup)
        
        # Fallback to filename
        if not new_title:
            new_title = self.generate_title_from_filename(filepath)
        
        # Create and insert title tag
        title_tag = soup.new_tag('title')
        title_tag.string = new_title
        
        head = soup.find('head')
        if head:
            # Insert as first child of head
            head.insert(0, title_tag)
            return True, f"Added title: {new_title}"
        else:
            return False, "No <head> tag found"
    
    def fix_missing_description(self, soup: BeautifulSoup, filepath: str) -> Tuple[bool, str]:
        """Fix missing meta description."""
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        
        if desc_tag and desc_tag.get('content', '').strip():
            return False, "Description exists"
        
        new_desc = self.generate_description_from_content(soup, filepath)
        
        desc_tag = soup.new_tag('meta')
        desc_tag['name'] = 'description'
        desc_tag['content'] = new_desc
        
        head = soup.find('head')
        if head:
            # Insert after title if possible
            title = head.find('title')
            if title:
                title.insert_after(desc_tag)
            else:
                head.insert(0, desc_tag)
            return True, f"Added description: {new_desc[:50]}..."
        else:
            return False, "No <head> tag found"
    
    def fix_missing_canonical(self, soup: BeautifulSoup, filepath: str) -> Tuple[bool, str]:
        """Fix missing canonical link."""
        canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
        
        if canonical_tag and canonical_tag.get('href', '').strip():
            return False, "Canonical exists"
        
        new_canonical = self.generate_canonical_url(filepath)
        
        canonical_tag = soup.new_tag('link')
        canonical_tag['rel'] = 'canonical'
        canonical_tag['href'] = new_canonical
        
        head = soup.find('head')
        if head:
            # Insert after description if possible
            desc = head.find('meta', attrs={'name': 'description'})
            if desc:
                desc.insert_after(canonical_tag)
            else:
                head.append(canonical_tag)
            return True, f"Added canonical: {new_canonical}"
        else:
            return False, "No <head> tag found"
    
    def fix_missing_h1(self, soup: BeautifulSoup, filepath: str) -> Tuple[bool, str]:
        """Fix missing H1 tag."""
        h1_tags = soup.find_all('h1')
        
        if len(h1_tags) == 0:
            # Generate H1 from title or filename
            title = soup.find('title')
            if title and title.get_text(strip=True):
                h1_text = title.get_text(strip=True).replace(' | VideoCameraHoliday', '')
            else:
                h1_text = self.generate_title_from_filename(filepath).replace(' | VideoCameraHoliday', '')
            
            # Limit H1 length
            h1_text = h1_text[:60]
            
            new_h1 = soup.new_tag('h1')
            new_h1.string = h1_text
            
            # Find best insertion point
            body = soup.find('body')
            if body:
                # Try to insert at top of body or main content
                main = body.find(['main', 'article', 'div', 'section'])
                if main:
                    main.insert(0, new_h1)
                else:
                    body.insert(0, new_h1)
                return True, f"Added H1: {h1_text}"
            else:
                return False, "No <body> tag found"
        
        elif len(h1_tags) > 1:
            # Multiple H1s - flag for manual review
            return False, f"Multiple H1s found ({len(h1_tags)}) - requires manual review"
        
        return False, "H1 exists"
    
    def fix_file(self, filepath: str) -> Dict[str, Any]:
        """Process a single file and apply all applicable fixes."""
        result = {
            'file': filepath,
            'issues_found': [],
            'fixes_applied': [],
            'manual_review_needed': False,
            'errors': [],
            'backup_created': False
        }
        
        try:
            # Read file
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'lxml')
            
            # Check and fix each issue type
            fixes = [
                ('title', self.fix_missing_title),
                ('description', self.fix_missing_description),
                ('canonical', self.fix_missing_canonical),
                ('h1', self.fix_missing_h1)
            ]
            
            made_changes = False
            
            for issue_type, fix_func in fixes:
                success, message = fix_func(soup, filepath)
                
                if 'requires manual review' in message.lower():
                    result['manual_review_needed'] = True
                    result['issues_found'].append(f"{issue_type}: {message}")
                    self.manual_review_items.append({
                        'file': filepath,
                        'issue': message,
                        'type': issue_type
                    })
                elif success:
                    made_changes = True
                    result['fixes_applied'].append(f"{issue_type}: {message}")
                    self.fixed_count += 1
                elif success is False and message != f"{issue_type.capitalize()} exists":
                    result['issues_found'].append(f"{issue_type}: {message}")
            
            # Save changes if any were made
            if made_changes and not self.dry_run:
                # Create backup
                backup_path = f"{filepath}.bak"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                result['backup_created'] = True
                
                # Write fixed content
                # Use the original formatting as much as possible
                fixed_content = str(soup)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                result['status'] = 'fixed'
            elif made_changes and self.dry_run:
                result['status'] = 'would_fix'
            else:
                result['status'] = 'no_changes_needed'
            
        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(str(e))
            self.error_count += 1
        
        return result
    
    def process_audit_report(self, report_path: str) -> Dict[str, Any]:
        """Process the SEO audit report and fix all critical issues."""
        if not os.path.exists(report_path):
            print(f"ERROR: Audit report not found: {report_path}")
            return {'error': 'Report not found'}
        
        # Load audit report
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        print(f"📊 Processing SEO audit report...")
        print(f"   Total pages: {report.get('summary', {}).get('total', 0)}")
        print(f"   Critical issues: {report.get('summary', {}).get('critical', 0)}")
        print(f"   Warnings: {report.get('summary', {}).get('warnings', 0)}")
        print()
        
        # Filter pages with critical issues
        critical_pages = []
        for page in report.get('pages', []):
            if page.get('issues'):
                has_critical = any(i.get('severity') == 'critical' for i in page['issues'])
                if has_critical:
                    critical_pages.append(page)
        
        print(f"🔧 Found {len(critical_pages)} pages with critical SEO issues")
        print()
        
        # Process each critical page
        for page in critical_pages:
            filepath = page.get('filePath', '')
            if not filepath or not os.path.exists(filepath):
                self.skipped_count += 1
                continue
            
            print(f"Processing: {filepath}")
            result = self.fix_file(filepath)
            self.fixes_log.append(result)
            
            if result['status'] == 'fixed':
                print(f"  ✅ Fixed: {', '.join(result['fixes_applied'])}")
            elif result['status'] == 'would_fix':
                print(f"  🔶 Would fix: {', '.join(result['fixes_applied'])}")
            elif result['manual_review_needed']:
                print(f"  ⚠️  Manual review needed: {result['issues_found']}")
                self.manual_review_count += 1
            elif result['status'] == 'error':
                print(f"  ❌ Error: {result['errors']}")
            else:
                print(f"  ℹ️  No changes needed")
        
        print()
        return self.generate_summary()
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary report."""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': self.dry_run,
            'base_url': self.base_url,
            'summary': {
                'fixed': self.fixed_count,
                'manual_review': self.manual_review_count,
                'skipped': self.skipped_count,
                'errors': self.error_count
            },
            'fixes': self.fixes_log,
            'manual_review_items': self.manual_review_items
        }
        
        return summary
    
    def save_reports(self, output_dir: str = '.'):
        """Save JSON and text reports."""
        summary = self.generate_summary()
        
        # Save JSON report
        json_path = os.path.join(output_dir, 'auto-fix-report.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"📄 JSON report saved: {json_path}")
        
        # Save text summary
        txt_path = os.path.join(output_dir, 'auto-fix-summary.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("AUTO-FIX SEO SUMMARY REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Timestamp: {summary['timestamp']}\n")
            f.write(f"Dry Run: {summary['dry_run']}\n")
            f.write(f"Base URL: {summary['base_url']}\n\n")
            f.write("-" * 60 + "\n")
            f.write("SUMMARY\n")
            f.write("-" * 60 + "\n")
            f.write(f"✅ Fixes Applied: {summary['summary']['fixed']}\n")
            f.write(f"⚠️  Manual Review Needed: {summary['summary']['manual_review']}\n")
            f.write(f"⏭️  Skipped: {summary['summary']['skipped']}\n")
            f.write(f"❌ Errors: {summary['summary']['errors']}\n\n")
            
            if summary['manual_review_items']:
                f.write("-" * 60 + "\n")
                f.write("ITEMS REQUIRING MANUAL REVIEW\n")
                f.write("-" * 60 + "\n")
                for item in summary['manual_review_items']:
                    f.write(f"\nFile: {item['file']}\n")
                    f.write(f"Issue: {item['issue']}\n")
                    f.write(f"Type: {item['type']}\n")
        
        print(f"📄 Text summary saved: {txt_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Auto-fix critical SEO issues from audit report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (show what would be fixed)
  python tools/auto_fix_seo.py
  
  # Apply fixes
  python tools/auto_fix_seo.py --dry-run false
  
  # Custom base URL
  python tools/auto_fix_seo.py --base-url https://example.com/site/
        """
    )
    
    parser.add_argument(
        '--dry-run',
        type=lambda x: x.lower() in ['true', '1', 'yes', 'y'],
        default=True,
        help='Show what would be fixed without making changes (default: True)'
    )
    
    parser.add_argument(
        '--base-url',
        default='https://dawidmillenium-design.github.io/VideoCameraHoliday/',
        help='Base URL for canonical links'
    )
    
    parser.add_argument(
        '--report',
        default='seo-audit-report.json',
        help='Path to SEO audit report JSON file'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔧 AUTO-FIX SEO SCRIPT")
    print("=" * 60)
    print(f"Dry Run: {args.dry_run}")
    print(f"Base URL: {args.base_url}")
    print(f"Audit Report: {args.report}")
    print("=" * 60)
    print()
    
    # Initialize fixer
    fixer = SEOFixer(base_url=args.base_url, dry_run=args.dry_run)
    
    # Process audit report
    summary = fixer.process_audit_report(args.report)
    
    # Save reports
    fixer.save_reports()
    
    # Print final summary
    print()
    print("=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"✅ Fixes Applied: {summary['summary']['fixed']}")
    print(f"⚠️  Manual Review Needed: {summary['summary']['manual_review']}")
    print(f"⏭️  Skipped: {summary['summary']['skipped']}")
    print(f"❌ Errors: {summary['summary']['errors']}")
    print("=" * 60)
    
    if args.dry_run:
        print()
        print("ℹ️  This was a DRY RUN. No files were modified.")
        print("   To apply fixes, run: python tools/auto_fix_seo.py --dry-run false")
    
    # Exit with appropriate code
    if summary['summary']['errors'] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
