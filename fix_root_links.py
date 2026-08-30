#!/usr/bin/env python3
"""
Fix incorrect root-relative links by adding /VideoCameraHoliday/ prefix.
"""

import os
import re

def fix_root_relative_links(filepath):
    """Fix root-relative links in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"Error reading: {e}"
    
    original_content = content
    
    # Find and replace root-relative links without /VideoCameraHoliday/
    # Pattern: href="/<anything>" where <anything> doesn't start with VideoCameraHoliday
    # But exclude: href="#", href="https://", href="http://", etc.
    
    # Replace /path/to/page.html with /VideoCameraHoliday/path/to/page.html
    pattern = r'href="(/(?!VideoCameraHoliday)([^"#]*\.html))"'
    replacement = r'href="/VideoCameraHoliday/\2"'
    
    new_content = re.sub(pattern, replacement, content)
    
    # Also handle links to directories /path/ -> /VideoCameraHoliday/path/
    pattern_dir = r'href="(/(?!VideoCameraHoliday)([^"#]*)/)"'
    replacement_dir = r'href="/VideoCameraHoliday/\2/"'
    new_content = re.sub(pattern_dir, replacement_dir, new_content)
    
    if new_content != original_content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True, "Fixed root-relative links"
        except Exception as e:
            return False, f"Error writing: {e}"
    
    return False, "No root-relative links found"

def main():
    print("Fixing incorrect root-relative links...\n")
    
    fixed_count = 0
    
    for dirpath, dirnames, filenames in os.walk('.'):
        dirnames[:] = [d for d in dirnames if d not in ['.git', 'assets', '.github']]
        
        for filename in filenames:
            if filename.endswith('.html'):
                filepath = os.path.join(dirpath, filename)
                success, message = fix_root_relative_links(filepath)
                
                if success:
                    fixed_count += 1
                    rel_path = filepath.replace(os.getcwd(), '').lstrip('\\/')
                    print(f"[FIXED] {rel_path}")
    
    print(f"\n{'='*80}")
    print(f"Summary: Fixed {fixed_count} files with root-relative links")

if __name__ == '__main__':
    main()
