#!/usr/bin/env python3
"""
Fix HTML files that are missing the mobile menu toggle button
"""

import os
import re

def get_relative_path_to_assets(filepath):
    """Calculate relative path from file location to assets folder"""
    rel_path = os.path.relpath(filepath, '/workspace')
    depth = rel_path.count('/')
    
    if depth == 0:
        return "./assets"
    else:
        return "../" * depth + "assets"

def fix_file(filepath):
    """Add mobile menu toggle button and JS script to a file"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False
    
    # Skip if already has mobile-menu-toggle
    if 'mobile-menu-toggle' in content or 'menu-toggle' in content:
        return True
    
    # Skip template files
    if any(x in filepath for x in ['mega-menu-nav.html', 'MEGA_MENU_INTEGRATION_EXAMPLE.html', 'mega-menu-footer.html']):
        return True
    
    # Check if file has mega menus
    if 'mega-item' not in content:
        return True
    
    assets_path = get_relative_path_to_assets(filepath)
    
    # Find nav-container div and add button after logo
    nav_container_pattern = r'(<div[^>]*class="nav-container"[^>]*>\s*<a[^>]*class="logo"[^>]*>[^<]*</a>)'
    match = re.search(nav_container_pattern, content)
    
    if match:
        # Add button and script after logo
        insert_html = f'''<button class="mobile-menu-toggle" onclick="document.querySelector('.nav-links').classList.toggle('active')">☰</button>
            <script src="{assets_path}/site-shell.js"></script>'''
        content = content[:match.end()] + '\n            ' + insert_html + content[match.end():]
        
        # Also ensure CSS is linked
        if 'site-shell.css' not in content:
            head_close = content.rfind('</head>')
            if head_close != -1:
                css_link = f'    <link rel="stylesheet" href="{assets_path}/site-shell.css">\n'
                content = content[:head_close] + css_link + content[head_close:]
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {filepath}")
            return True
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
            return False
    else:
        print(f"Could not find nav-container pattern in {filepath}")
        return False

def main():
    workspace = '/workspace'
    html_files = []
    
    # Find all HTML files
    for root, dirs, files in os.walk(workspace):
        if '.git' in root:
            continue
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                html_files.append(filepath)
    
    fixed = 0
    for filepath in html_files:
        if fix_file(filepath):
            fixed += 1
    
    print(f"\nProcessed {len(html_files)} files, ensured {fixed} have proper structure")

if __name__ == '__main__':
    main()
