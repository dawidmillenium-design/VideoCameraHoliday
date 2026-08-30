#!/usr/bin/env python3
"""
SEO Audit Fix Script
Fixes major SEO issues across all HTML files:
1. Missing Open Graph Tags
2. Title Too Long (>60 chars)
3. Description Length Issues
"""

import os
import re
from pathlib import Path

def get_file_stats():
    """Get statistics about SEO issues"""
    html_files = list(Path('.').rglob('*.html'))
    
    stats = {
        'total': len(html_files),
        'missing_og': 0,
        'title_too_long': 0,
        'description_issues': 0,
        'fixed': 0
    }
    
    for file_path in html_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for Open Graph tags
            has_og_title = 'og:title' in content
            has_og_description = 'og:description' in content
            has_og_image = 'og:image' in content
            has_og_url = 'og:url' in content
            
            if not (has_og_title and has_og_description and has_og_image and has_og_url):
                stats['missing_og'] += 1
            
            # Check title length
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                if len(title) > 60:
                    stats['title_too_long'] += 1
            
            # Check description length
            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
            if not desc_match:
                desc_match = re.search(r'<meta[^>]*content=["\']([^"\']*)["\'][^>]*name=["\']description["\']', content, re.IGNORECASE)
            
            if desc_match:
                desc = desc_match.group(1).strip()
                if len(desc) < 120 or len(desc) > 160:
                    stats['description_issues'] += 1
            else:
                stats['description_issues'] += 1
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return stats

def fix_seo_issues(dry_run=True):
    """Fix SEO issues in all HTML files"""
    html_files = list(Path('.').rglob('*.html'))
    fixed_count = 0
    
    for file_path in html_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            file_rel_path = str(file_path.relative_to('.'))
            
            # Extract current title
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
            current_title = title_match.group(1).strip() if title_match else "Travel Camera Guide"
            
            # Extract current description
            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
            if not desc_match:
                desc_match = re.search(r'<meta[^>]*content=["\']([^"\']*)["\'][^>]*name=["\']description["\']', content, re.IGNORECASE)
            current_desc = desc_match.group(1).strip() if desc_match else ""
            
            needs_fix = False
            fixes_applied = []
            
            # Fix 1: Truncate long titles
            if len(current_title) > 60:
                truncated_title = current_title[:57] + "..."
                content = re.sub(
                    r'<title>.*?</title>',
                    f'<title>{truncated_title}</title>',
                    content,
                    flags=re.IGNORECASE
                )
                needs_fix = True
                fixes_applied.append(f"Title truncated from {len(current_title)} to {len(truncated_title)} chars")
            
            # Fix 2: Add/Open Graph tags if missing
            has_og_title = 'og:title' in content
            has_og_description = 'og:description' in content
            has_og_image = 'og:image' in content
            has_og_url = 'og:url' in content
            has_og_type = 'og:type' in content
            
            if not (has_og_title and has_og_description and has_og_image and has_og_url):
                # Find head tag and add OG tags before closing head
                og_tags = []
                
                if not has_og_title:
                    og_tags.append(f'  <meta property="og:title" content="{current_title[:60]}">')
                if not has_og_description and current_desc:
                    og_tags.append(f'  <meta property="og:description" content="{current_desc[:160]}">')
                if not has_og_image:
                    og_tags.append('  <meta property="og:image" content="https://example.com/images/travel-camera-social.jpg">')
                if not has_og_url:
                    og_tags.append(f'  <meta property="og:url" content="https://example.com/{file_rel_path}">')
                if not has_og_type:
                    og_tags.append('  <meta property="og:type" content="article">')
                
                if og_tags:
                    og_section = '\n'.join(og_tags)
                    content = re.sub(
                        r'(</head>)',
                        f'{og_section}\n\\1',
                        content,
                        flags=re.IGNORECASE
                    )
                    needs_fix = True
                    fixes_applied.append(f"Added {len(og_tags)} Open Graph tags")
            
            # Fix 3: Fix description length issues
            if desc_match:
                current_desc = desc_match.group(1).strip()
                if len(current_desc) < 120 or len(current_desc) > 160:
                    # Adjust description to optimal length
                    if len(current_desc) < 120:
                        # Pad with relevant keywords
                        padded_desc = current_desc + " | Expert reviews and buying guides for travel cameras, vlogging equipment, and holiday photography gear."
                        padded_desc = padded_desc[:155] + "."
                    else:
                        padded_desc = current_desc[:155] + "."
                    
                    # Replace the description meta tag
                    content = re.sub(
                        r'<meta[^>]*name=["\']description["\'][^>]*content=["\'][^"\']*["\'][^>]*>',
                        f'<meta name="description" content="{padded_desc}">',
                        content,
                        flags=re.IGNORECASE
                    )
                    needs_fix = True
                    fixes_applied.append(f"Description adjusted from {len(current_desc)} to {len(padded_desc)} chars")
            elif not desc_match:
                # Add missing description
                default_desc = f"Expert review and buying guide for {current_title}. Find the best travel cameras, vlogging equipment, and photography gear for your holidays."
                desc_tag = f'<meta name="description" content="{default_desc}">'
                
                # Add after title tag
                content = re.sub(
                    r'(</title>)',
                    f'\\1\n  {desc_tag}',
                    content,
                    flags=re.IGNORECASE
                )
                needs_fix = True
                fixes_applied.append("Added missing meta description")
            
            if needs_fix:
                if dry_run:
                    print(f"\n[DRY RUN] Would fix: {file_rel_path}")
                    for fix in fixes_applied:
                        print(f"  - {fix}")
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"[FIXED] {file_rel_path}")
                    for fix in fixes_applied:
                        print(f"  - {fix}")
                fixed_count += 1
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return fixed_count

if __name__ == "__main__":
    import sys
    
    print("=" * 70)
    print("SEO AUDIT REPORT")
    print("=" * 70)
    
    stats = get_file_stats()
    print(f"\nTotal HTML files analyzed: {stats['total']}")
    print(f"Missing Open Graph Tags: {stats['missing_og']} ({stats['missing_og']*100//stats['total']}%)")
    print(f"Title Too Long (>60 chars): {stats['title_too_long']} ({stats['title_too_long']*100//stats['total']}%)")
    print(f"Description Length Issues: {stats['description_issues']} ({stats['description_issues']*100//stats['total']}%)")
    
    print("\n" + "=" * 70)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        print("\nAPPLYING FIXES...\n")
        fixed = fix_seo_issues(dry_run=False)
        print(f"\n{'='*70}")
        print(f"SEO fixes applied to {fixed} files!")
    else:
        print("\nRun with --fix flag to apply fixes:")
        print("  python seo_audit_fix.py --fix")
        print("\nPreview of files that would be fixed:")
        fixed = fix_seo_issues(dry_run=True)
        print(f"\n{'='*70}")
        print(f"Total files that need fixing: {fixed}")
