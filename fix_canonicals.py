#!/usr/bin/env python3
"""
Fix broken canonical URLs by pointing them to actual pages.
Updates pages to use self-canonicals when target pages don't exist.
"""

import os
import re
from pathlib import Path

def get_page_url(filepath):
    """Get the actual page URL from filepath."""
    rel_path = filepath.replace('\\', '/').replace(os.getcwd().replace('\\', '/'), '').lstrip('/')
    
    # Normalize URL
    if rel_path.endswith('index.html'):
        rel_path = rel_path.replace('index.html', '')
    elif rel_path.endswith('index2.html'):
        rel_path = rel_path.replace('index2.html', '')
    
    base_url = "https://dawidmillenium-design.github.io/VideoCameraHoliday"
    if rel_path:
        return f"{base_url}/{rel_path}"
    return f"{base_url}/"

def file_exists(canonical_url):
    """Check if canonical target exists in repo."""
    parsed_path = canonical_url.replace('https://dawidmillenium-design.github.io/VideoCameraHoliday/', '')
    parsed_path = parsed_path.rstrip('/')
    
    # Try with .html
    if not parsed_path.endswith('.html'):
        check_path = parsed_path + '.html'
    else:
        check_path = parsed_path
    
    filepath = os.path.join(os.getcwd(), check_path.replace('/', '\\'))
    
    if os.path.isfile(filepath):
        return True
    
    # Try as directory with index.html
    dir_path = os.path.join(os.getcwd(), parsed_path.replace('/', '\\'), 'index.html')
    if os.path.isfile(dir_path):
        return True
    
    return False

def fix_file(filepath):
    """Fix canonical URL in a single HTML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"Error reading: {e}"
    
    original_content = content
    
    # Find current canonical
    canonical_match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', content)
    if not canonical_match:
        return False, "No canonical found"
    
    current_canonical = canonical_match.group(1)
    
    # Check if canonical target exists
    if file_exists(current_canonical):
        return False, f"Canonical OK: {current_canonical}"
    
    # Get actual page URL
    actual_url = get_page_url(filepath)
    
    # Replace canonical
    new_content = content.replace(
        f'<link rel="canonical" href="{current_canonical}"',
        f'<link rel="canonical" href="{actual_url}"'
    )
    
    # Write back if changed
    if new_content != original_content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True, f"Fixed: {current_canonical} -> {actual_url}"
        except Exception as e:
            return False, f"Error writing: {e}"
    
    return False, "No changes needed"

def main():
    print("Fixing broken canonical URLs...\n")
    
    fixed_count = 0
    failed_count = 0
    
    for dirpath, dirnames, filenames in os.walk('.'):
        dirnames[:] = [d for d in dirnames if d not in ['.git', 'assets', '.github']]
        
        for filename in filenames:
            if filename.endswith('.html'):
                filepath = os.path.join(dirpath, filename)
                success, message = fix_file(filepath)
                
                if success:
                    fixed_count += 1
                    rel_path = filepath.replace(os.getcwd(), '').lstrip('\\/')
                    print(f"[FIXED] {rel_path}")
                    print(f"        {message}\n")
    
    print(f"\n{'='*80}")
    print(f"Summary: Fixed {fixed_count} files")

if __name__ == '__main__':
    main()
