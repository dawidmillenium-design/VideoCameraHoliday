#!/usr/bin/env python3
"""
Add CSS and JS asset links to all HTML files that have mega menus
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

def update_file_with_assets(filepath):
    """Add CSS and JS asset links to a single HTML file"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False
    
    # Skip template files
    if any(x in filepath for x in ['mega-menu-nav.html', 'MEGA_MENU_INTEGRATION_EXAMPLE.html', 'mega-menu-footer.html']):
        return False
    
    # Check if file has mega menus (already updated)
    if 'mega-item' not in content:
        return False
    
    # Check if already has site-shell.css linked
    if 'site-shell.css' in content:
        return True  # Already done
    
    assets_path = get_relative_path_to_assets(filepath)
    
    # Find </head> and insert CSS link before it
    head_close = content.rfind('</head>')
    if head_close == -1:
        print(f"No </head> found in {filepath}")
        return False
    
    css_link = f'    <link rel="stylesheet" href="{assets_path}/site-shell.css">\n'
    content = content[:head_close] + css_link + content[head_close:]
    
    # Find the mobile-menu-toggle button and add JS script after it
    # Look for pattern like: <button class="mobile-menu-toggle"...>☰</button>
    mobile_btn_pattern = r'(<button[^>]*class="mobile-menu-toggle"[^>]*>.*?</button>)'
    match = re.search(mobile_btn_pattern, content, re.DOTALL)
    
    if match:
        js_script = f'\n    <script src="{assets_path}/site-shell.js"></script>'
        content = content[:match.end()] + js_script + content[match.end():]
    else:
        # Try alternative: look for nav-container closing and add script there
        nav_container_pattern = r'(<div[^>]*class="nav-container"[^>]*>.*?<button[^>]*mobile-menu-toggle[^>]*>.*?</button>)'
        match = re.search(nav_container_pattern, content, re.DOTALL)
        if match:
            js_script = f'\n            <script src="{assets_path}/site-shell.js"></script>'
            content = content[:match.end()] + js_script + content[match.end():]
        else:
            print(f"Could not find mobile menu button in {filepath}")
            # Still return True since we added CSS
            pass
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing {filepath}: {e}")
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
    
    print(f"Found {len(html_files)} HTML files")
    
    updated = 0
    skipped = 0
    errors = 0
    
    for filepath in html_files:
        result = update_file_with_assets(filepath)
        if result is True:
            updated += 1
        elif result is False:
            skipped += 1
    
    print(f"\nResults:")
    print(f"  Updated/Confirmed: {updated}")
    print(f"  Skipped: {skipped}")

if __name__ == '__main__':
    main()
