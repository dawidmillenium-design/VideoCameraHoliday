#!/usr/bin/env python3
"""
Hotfix Script: Injects missing BreadcrumbList JSON-LD and fixes H1 tags.
Targets only files that failed the previous verification.
"""
import os
import re
import json
from pathlib import Path
from bs4 import BeautifulSoup

# Configuration
BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday"
REPO_ROOT = Path(".")

# Files to skip (templates, indexes, etc.)
SKIP_DIRS = {"templates", "node_modules", ".git", "backups", "city-generator"}
SKIP_FILES = {"index.html", "index2.html", "index3.html", "hub.html", "404.html"}

def get_breadcrumb_data(file_path):
    """Generate breadcrumb JSON-LD based on file path."""
    parts = list(file_path.parts)
    
    # Remove language folders from breadcrumb logic if needed, but keep them in URL
    # Construct breadcrumbs
    breadcrumbs = []
    current_url = BASE_URL
    position = 1
    
    # Add Home
    breadcrumbs.append({
        "@type": "ListItem",
        "position": position,
        "name": "Home",
        "item": f"{BASE_URL}/"
    })
    position += 1
    
    # Iterate through folders
    for part in parts[:-1]: # Exclude filename
        if part.endswith('.html') or part in SKIP_DIRS:
            continue
        
        # Clean folder name for display
        name = part.replace('-', ' ').replace('_', ' ').title()
        # Fix common over-capitalizations
        name = re.sub(r'\b(And|Or|The|A|An|For|In|On|At|To|Vs)\b', lambda m: m.group(1).lower(), name)
        
        current_url = f"{current_url}/{part}"
        breadcrumbs.append({
            "@type": "ListItem",
            "position": position,
            "name": name,
            "item": f"{current_url}/"
        })
        position += 1
    
    # Add Current Page
    filename = parts[-1]
    page_name = filename.replace('.html', '').replace('-', ' ').replace('_', ' ').title()
    page_name = re.sub(r'\b(And|Or|The|A|An|For|In|On|At|To|Vs|&)\b', lambda m: m.group(1).lower(), page_name)
    
    current_url = f"{current_url}/{filename}"
    breadcrumbs.append({
        "@type": "ListItem",
        "position": position,
        "name": page_name,
        "item": current_url
    })
    
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": breadcrumbs
    }

def fix_file(file_path):
    """Inject JSON-LD and fix H1 if missing."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except:
            return False

    soup = BeautifulSoup(content, 'lxml')
    modified = False
    
    # 1. Check/Inject JSON-LD
    if '"@type": "BreadcrumbList"' not in content:
        schema_data = get_breadcrumb_data(file_path)
        schema_script = soup.new_tag('script', type='application/ld+json')
        schema_script.string = json.dumps(schema_data, indent=2)
        
        # Append to head or body if head missing
        if soup.head:
            soup.head.append(schema_script)
        else:
            soup.insert(0, schema_script)
        modified = True
        print(f"✅ Injected JSON-LD: {file_path}")
    
    # 2. Fix Missing H1
    h1 = soup.find('h1')
    if not h1 or not h1.get_text().strip():
        # Try to get title from <title> tag
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text().strip()
            # Clean brand suffixes
            clean_title = re.sub(r'\s*–\s*.*$', '', title_text)
            if not clean_title:
                clean_title = title_text
            
            # Find best place to insert H1 (inside main or article)
            target = soup.find('main') or soup.find('article') or soup.find('body')
            if target:
                new_h1 = soup.new_tag('h1')
                new_h1.string = clean_title
                # Insert at top of target
                target.insert(0, new_h1)
                modified = True
                print(f"✅ Fixed H1: {file_path} -> '{clean_title}'")

    if modified:
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        return True
    return False

def main():
    print("🚀 Starting Hotfix...")
    count = 0
    
    # Scan all HTML files
    for html_file in REPO_ROOT.rglob("*.html"):
        # Skip excluded dirs
        if any(part in SKIP_DIRS for part in html_file.parts):
            continue
        # Skip excluded files
        if html_file.name in SKIP_FILES:
            continue
            
        if fix_file(html_file):
            count += 1
            
    print(f"🎉 Hotfix Complete! Modified {count} files.")

if __name__ == "__main__":
    main()
