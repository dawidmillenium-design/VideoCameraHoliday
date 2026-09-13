#!/usr/bin/env python3
"""
Hotfix Script V2: Aggressively fixes missing H1 tags and injects BreadcrumbList JSON-LD.
"""
import os
import re
import json
from pathlib import Path
from bs4 import BeautifulSoup

# Configuration
BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday"
REPO_ROOT = Path(__file__).parent.parent

# Folders to ignore completely (workspace is excluded here)
EXCLUDE_DIRS = {'.git', 'node_modules', 'templates', 'backups', 'workspace', 'city-generator'}

def get_relative_path(file_path):
    """Get path relative to repo root for URL construction."""
    try:
        return file_path.relative_to(REPO_ROOT)
    except ValueError:
        return file_path

def build_breadcrumb_schema(file_path, title):
    """Construct valid BreadcrumbList JSON-LD with absolute URLs."""
    rel_path = get_relative_path(file_path)
    parts = [p for p in rel_path.parts if p.endswith('.html') is False]
    
    # Handle language folders correctly
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
    for i, part in enumerate(parts):
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
        
        # --- FIX 1: Ensure H1 exists ---
        h1 = soup.find('h1')
        if not h1:
            # Try to find title in <title> tag
            title_tag = soup.find('title')
            page_title = "Untitled Page"
            if title_tag and title_tag.string:
                # Clean title
                page_title = re.sub(r'\s*–\s*.*$', '', title_tag.string).strip()
                if not page_title: page_title = title_tag.string.strip()
            
            new_h1 = soup.new_tag('h1')
            new_h1.string = page_title
            
            # Strategy A: Look for article-hero
            hero = soup.find('section', class_='article-hero')
            if hero:
                hero.insert(0, new_h1)
                modified = True
            else:
                # Strategy B: Look for ANY section with class containing 'hero'
                any_hero = soup.find(['section', 'div', 'header'], class_=re.compile(r'hero'))
                if any_hero:
                    any_hero.insert(0, new_h1)
                    modified = True
                else:
                    # Strategy C: Prepend to <main>
                    main = soup.find('main')
                    if main:
                        main.insert(0, new_h1)
                        modified = True
                    else:
                        # Strategy D: Prepend to <body> directly (last resort)
                        body = soup.find('body')
                        if body:
                            body.insert(0, new_h1)
                            modified = True
        
        # --- FIX 2: Inject BreadcrumbList JSON-LD if missing ---
        existing_json = soup.find('script', type='application/ld+json')
        has_breadcrumb = False
        if existing_json and existing_json.string:
            if '"BreadcrumbList"' in existing_json.string:
                has_breadcrumb = True
        
        if not has_breadcrumb:
            schema_obj = build_breadcrumb_schema(file_path, "Title")
            schema_json = json.dumps(schema_obj, indent=2)
            
            new_script = soup.new_tag('script', type='application/ld+json')
            new_script.string = schema_json
            
            if soup.head:
                soup.head.append(new_script)
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
    print("🔍 Starting Hotfix Scan V2...")
    fixed_count = 0
    scanned_count = 0
    
    html_files = list(REPO_ROOT.rglob("*.html"))
    
    for file_path in html_files:
        # Skip excluded dirs
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
