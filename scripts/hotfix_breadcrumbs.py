#!/usr/bin/env python3
"""
hotfix_breadcrumbs.py (V2)

Injects missing BreadcrumbList JSON-LD and forces H1 tags into HTML files.
Skips workspace/, city-generator/, and generated-content/ directories.
"""

import os
import re
import json
from pathlib import Path
from bs4 import BeautifulSoup

# Configuration
BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday"
REPO_ROOT = Path(__file__).parent.parent

# Folders to ignore completely
EXCLUDE_DIRS = {
    '.git', 
    'node_modules', 
    'templates', 
    'backups', 
    'workspace', 
    'city-generator', 
    'generated-content'
}

def get_relative_path(file_path):
    """Get path relative to repo root."""
    try:
        return file_path.relative_to(REPO_ROOT)
    except ValueError:
        return file_path

def build_breadcrumb_schema(file_path):
    """Construct valid BreadcrumbList JSON-LD with absolute URLs."""
    rel_path = get_relative_path(file_path)
    parts = [p for p in rel_path.parts if p.endswith('.html') is False]
    
    lang_folders = ['de-DE', 'es-ES', 'fr-FR', 'th-TH', 'zh-CN', 'ja-JP', 'ko-KR', 'pl-PL', 'it-IT', 'pt-br']
    
    breadcrumbs = []
    current_url = BASE_URL + "/"
    
    # 1. Home Item
    breadcrumbs.append({
        "@type": "ListItem",
        "position": 1,
        "name": "Home",
        "item": BASE_URL + "/"
    })
    
    position = 2
    for part in parts:
        if part in lang_folders:
            current_url += part + "/"
            breadcrumbs.append({
                "@type": "ListItem",
                "position": position,
                "name": part.upper(),
                "item": current_url
            })
            position += 1
        elif part == 'city-generator':
            continue
        else:
            current_url += part + "/"
            clean_name = part.replace('-', ' ').title()
            
            breadcrumbs.append({
                "@type": "ListItem",
                "position": position,
                "name": clean_name,
                "item": current_url
            })
            position += 1

    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": breadcrumbs
    }

def process_file(file_path):
    """Process a single file: fix H1 and inject JSON-LD if missing."""
    try:
        # Read content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()

        soup = BeautifulSoup(content, 'lxml')
        modified = False
        
        # --- FIX 1: Ensure H1 exists (Aggressive Injection) ---
        h1 = soup.find('h1')
        if not h1:
            title_tag = soup.find('title')
            page_title = "Untitled Page"
            
            if title_tag and title_tag.string:
                clean_title = re.sub(r'\s*–\s*.*$', '', str(title_tag.string)).strip()
                page_title = clean_title if clean_title else str(title_tag.string).strip()
            
            new_h1 = soup.new_tag('h1')
            new_h1.string = page_title
            
            # Try to insert into .article-hero
            hero = soup.find('section', class_='article-hero')
            if not hero:
                hero = soup.find('div', class_='hero')
            if not hero:
                hero = soup.find('header', class_='hero')
            
            if hero:
                hero.insert(0, new_h1)
                modified = True
            else:
                # Fallback to main or body
                main = soup.find('main')
                if main:
                    main.insert(0, new_h1)
                    modified = True
                else:
                    body = soup.find('body')
                    if body:
                        body.insert(0, new_h1)
                        modified = True
        
        # --- FIX 2: Inject BreadcrumbList JSON-LD if missing ---
        has_breadcrumb = False
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            if script.string and '"BreadcrumbList"' in script.string:
                has_breadcrumb = True
                break
        
        if not has_breadcrumb:
            schema_obj = build_breadcrumb_schema(file_path)
            schema_json = json.dumps(schema_obj, indent=2)
            
            new_script = soup.new_tag('script', type='application/ld+json')
            new_script.string = schema_json
            
            if soup.head:
                soup.head.append(new_script)
                modified = True
            else:
                html_tag = soup.find('html')
                if html_tag:
                    new_head = soup.new_tag('head')
                    new_head.append(new_script)
                    html_tag.insert(0, new_head)
                    modified = True
        
        # Write back if modified
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            return True, "Fixed"
            
        return False, "OK"
        
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    print("🔍 Starting Hotfix Scan (V2)...")
    fixed_count = 0
    scanned_count = 0
    
    html_files = list(REPO_ROOT.rglob("*.html"))
    
    for file_path in html_files:
        if any(excl in str(file_path) for excl in EXCLUDE_DIRS):
            continue
            
        scanned_count += 1
        success, msg = process_file(file_path)
        
        if success:
            fixed_count += 1
            print(f"✅ Fixed: {file_path.relative_to(REPO_ROOT)}")
        elif msg != "OK":
            print(f"⚠️  {msg}: {file_path.relative_to(REPO_ROOT)}")
            
    print(f"\n📊 Hotfix Complete:")
    print(f"   Scanned: {scanned_count}")
    print(f"   Fixed:   {fixed_count}")

if __name__ == "__main__":
    main()
