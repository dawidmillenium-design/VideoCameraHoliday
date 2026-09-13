#!/usr/bin/env python3
"""
Force inject Design B template sections across ALL HTML files.
Preserves the original page <title> and crucial meta tags, but replaces
header, footer, and the rest of the <head> with the Design B template.
"""

import os
import sys
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
    
    # Extract head content (excluding title, which we'll preserve per-page)
    head_content = ""
    if soup.head:
        for child in list(soup.head.children):
            if isinstance(child, str) and not child.strip():
                continue
            if getattr(child, 'name', None) != 'title':
                head_content += str(child) + "\n"
    
    header_html = str(soup.find('header')) if soup.find('header') else ""
    footer_html = str(soup.find('footer')) if soup.find('footer') else ""
    
    return {
        'head': head_content,
        'header': header_html,
        'footer': footer_html,
    }

def inject_design(file_path: Path, template: dict) -> tuple[bool, str]:
    """Inject Design B into a single file. Returns (success, message)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'lxml')
        modified = False

        # 1. Preserve original title and crucial meta tags
        original_title = str(soup.title) if soup.title else "<title>Untitled</title>"
        
        # Extract crucial metas (charset, viewport) to prevent mobile breakage
        crucial_metas = []
        for meta in soup.find_all('meta'):
            if meta.get('charset') or meta.get('name', '').lower() in ['viewport', 'description']:
                crucial_metas.append(str(meta))

        # 2. Update HEAD
        if soup.head and template['head']:
            soup.head.clear()
            # Rebuild head: crucial metas + original title + new template head
            head_html = "\n".join(crucial_metas) + "\n" + original_title + "\n" + template['head']
            new_head = BeautifulSoup(head_html, 'lxml').head
            soup.head.replace_with(new_head)
            modified = True
        elif not soup.head and template['head']:
            # Create head if missing
            new_head = soup.new_tag('head')
            new_head.append(BeautifulSoup("\n".join(crucial_metas) + "\n" + original_title + "\n" + template['head'], 'lxml').head)
            if soup.html:
                soup.html.insert(0, new_head)
            modified = True

        # 3. Replace HEADER
        if template['header']:
            old_header = soup.find('header')
            new_header = BeautifulSoup(template['header'], 'lxml').find('header')
            if old_header:
                old_header.replace_with(new_header)
            elif soup.body:
                soup.body.insert(0, new_header)
            modified = True

        # 4. Replace FOOTER
        if template['footer']:
            old_footer = soup.find('footer')
            new_footer = BeautifulSoup(template['footer'], 'lxml').find('footer')
            if old_footer:
                old_footer.replace_with(new_footer)
            elif soup.body:
                soup.body.append(new_footer)
            modified = True

        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            return True, "Updated"
        else:
            return True, "Skipped (no changes needed)"
            
    except Exception as e:
        return False, f"Error: {e}"

def main():
    print("🚀 Force Design B Injection — Starting")
    
    template = load_template()
    print("✅ Template loaded successfully")
    
    root = Path('.')
    # Find all HTML files, excluding templates, node_modules, and venv
    exclude_dirs = {'templates', 'node_modules', 'venv', '.git', '__pycache__'}
    html_files = [
        f for f in root.rglob("*.html") 
        if not any(part in exclude_dirs for part in f.parts)
    ]
    
    print(f"📁 Found {len(html_files)} HTML files to process")
    
    updated = 0
    skipped = 0
    errors = 0
    
    for file_path in html_files:
        success, msg = inject_design(file_path, template)
        if success:
            if msg == "Updated":
                updated += 1
            else:
                skipped += 1
        else:
            errors += 1
            print(f"  ❌ {file_path}: {msg}")
            
        # Progress indicator
        if (updated + skipped + errors) % 100 == 0:
            print(f"  Progress: {updated + skipped + errors}/{len(html_files)}")
    
    print(f"\n📊 Summary:")
    print(f"  Files scanned : {len(html_files)}")
    print(f"  Files updated : {updated}")
    print(f"  Files skipped : {skipped}")
    print(f"  Errors        : {errors}")
    print("✨ Done.")
    
    # Exit with error code if there were failures, so GitHub Actions catches it
    sys.exit(1 if errors > 0 else 0)

if __name__ == "__main__":
    main()
