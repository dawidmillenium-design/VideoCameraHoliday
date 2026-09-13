#!/usr/bin/env python3
"""
Force inject Design B template across ALL HTML files.
No skipping - every file gets updated.
"""

import os
from pathlib import Path
from bs4 import BeautifulSoup

def load_template():
    """Load Design B template sections."""
    template_path = Path("templates/design-b.html")
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'lxml')
    
    # Extract sections
    head_content = ""
    if soup.head:
        for child in list(soup.head.children):
            if str(child).strip():
                head_content += str(child) + "\n"
    
    header_html = ""
    header = soup.find('header')
    if header:
        header_html = str(header)
    
    footer_html = ""
    footer = soup.find('footer')
    if footer:
        footer_html = str(footer)
    
    return {
        'head': head_content,
        'header': header_html,
        'footer': footer_html,
        'total_chars': len(head_content) + len(header_html) + len(footer_html)
    }

def inject_design(file_path: Path, template: dict) -> bool:
    """Inject Design B into a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'lxml')
        
        # 1. Update HEAD
        if soup.head and template['head']:
            # Clear existing head content but keep title
            title = soup.head.find('title')
            soup.head.clear()
            if title:
                soup.head.append(title)
                soup.head.append('\n')
            soup.head.append(template['head'])
        
        # 2. Replace HEADER
        if template['header']:
            old_header = soup.find('header')
            if old_header:
                old_header.replace_with(BeautifulSoup(template['header'], 'lxml').find('header'))
            elif soup.body:
                # Insert header at top of body
                new_header = BeautifulSoup(template['header'], 'lxml').find('header')
                soup.body.insert(0, new_header)
        
        # 3. Replace FOOTER
        if template['footer']:
            old_footer = soup.find('footer')
            if old_footer:
                old_footer.replace_with(BeautifulSoup(template['footer'], 'lxml').find('footer'))
            elif soup.body:
                # Append footer to body
                new_footer = BeautifulSoup(template['footer'], 'lxml').find('footer')
                soup.body.append(new_footer)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        return True
    except Exception as e:
        print(f"  ❌ Error on {file_path.name}: {e}")
        return False

def main():
    print("🚀 Force Design B Injection — Starting")
    
    # Load template
    template = load_template()
    print(f" Template loaded: {template['total_chars']} chars")
    
    # Find all HTML files
    root = Path('.')
    html_files = list(root.rglob("*.html"))
    
    # Exclude templates and special files
    exclude_patterns = ['templates/', 'node_modules/', '__pycache__/']
    html_files = [
        f for f in html_files 
        if not any(pattern in str(f) for pattern in exclude_patterns)
    ]
    
    print(f"📁 Found {len(html_files)} HTML files to process")
    
    # Process all files
    updated = 0
    errors = 0
    
    for file_path in html_files:
        if inject_design(file_path, template):
            updated += 1
            if updated % 100 == 0:
                print(f"  Progress: {updated}/{len(html_files)}")
        else:
            errors += 1
    
    print(f"\n📊 Summary:")
    print(f"  Files scanned: {len(html_files)}")
    print(f"  Files updated: {updated}")
    print(f"  Errors: {errors}")
    print("✨ Done.")

if __name__ == "__main__":
    main()
