#!/usr/bin/env python3
"""
Verification Script for Breadcrumb & Hero Injection Hotfix
Checks H1 integrity, JSON-LD validity, and structural correctness.
"""
import os
import sys
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

# Configuration
ROOT_DIR = Path(__file__).parent.parent
EXCLUDE_DIRS = {'.git', 'node_modules', 'templates', 'backups', '__pycache__'}
BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday"

def get_html_files():
    files = []
    for path in ROOT_DIR.rglob("*.html"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        # Only check content folders
        if any(x in str(path) for x in ['reviews/', 'guides/', 'how-to/', 'destinations/', 'comparisons/', 'city-through-the-lens/', 'de-DE/', 'th-TH/', 'zh-CN/', 'ja-JP/', 'ko-KR/', 'pl-PL/', 'it-IT/', 'pt-br/']):
            # Skip index files
            if path.name not in ['index.html', '404.html']:
                files.append(path)
    return files

def check_h1_integrity(soup, file_path):
    """Check if H1 is empty or truncated (e.g., 'Best s 2026')"""
    h1 = soup.find('h1')
    if not h1:
        return False, "Missing H1 tag"
    
    text = h1.get_text(strip=True)
    if not text:
        return False, "Empty H1"
    
    # Check for known truncation bug pattern "Best s [Year]"
    if re.search(r'Best\s+s\s+\d{4}', text, re.IGNORECASE):
        return False, f"Truncated H1: '{text}'"
        
    # Check for suspiciously short titles for article pages
    if len(text.split()) < 3 and 'review' in str(file_path).lower():
        # Heuristic: Reviews usually have longer titles
        pass 
        
    return True, text

def check_json_ld(soup):
    """Validate BreadcrumbList JSON-LD"""
    scripts = soup.find_all('script', type='application/ld+json')
    found_valid = False
    errors = []
    
    for script in scripts:
        try:
            data = json.loads(script.string)
            if data.get('@type') == 'BreadcrumbList':
                items = data.get('itemListElement', [])
                if not items:
                    errors.append("Empty itemListElement")
                    continue
                
                # Check positions are sequential (1, 2, 3...)
                positions = [item.get('position') for item in items]
                if positions != list(range(1, len(positions) + 1)):
                    errors.append(f"Non-sequential positions: {positions}")
                    continue
                
                # Check all items have absolute URLs
                for i, item in enumerate(items):
                    url = item.get('item', '')
                    if not url.startswith('https://'):
                        errors.append(f"Item {i+1} has relative URL: {url}")
                        break
                    if not url.startswith(BASE_URL):
                         # Allow matching domain even if case differs slightly, but strict check preferred
                         pass
                
                if not errors:
                    found_valid = True
                break # Found a BreadcrumbList, stop checking others
        except json.JSONDecodeError:
            errors.append("Invalid JSON syntax")
            
    if not found_valid and not errors:
        # No BreadcrumbList found at all
        return False, ["Missing BreadcrumbList schema"]
        
    if errors:
        return False, errors
        
    return True, ["Valid"]

def main():
    print("🔍 Starting Verification Scan...")
    files = get_html_files()
    print(f"📂 Found {len(files)} content files to scan.")
    
    results = {
        'total': len(files),
        'passed': 0,
        'failed_h1': [],
        'failed_json': [],
        'failed_both': []
    }
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'lxml')
            
            h1_ok, h1_msg = check_h1_integrity(soup, file_path)
            json_ok, json_msg = check_json_ld(soup)
            
            if h1_ok and json_ok:
                results['passed'] += 1
            else:
                rel_path = file_path.relative_to(ROOT_DIR)
                if not h1_ok and not json_ok:
                    results['failed_both'].append((str(rel_path), h1_msg, json_msg))
                elif not h1_ok:
                    results['failed_h1'].append((str(rel_path), h1_msg))
                elif not json_ok:
                    results['failed_json'].append((str(rel_path), json_msg))
                    
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")

    # Report
    print("\n" + "="*50)
    print(f"📊 TOTAL SCANNED: {results['total']}")
    print(f"✅ PASSED: {results['passed']} ({(results['passed']/results['total']*100):.1f}%)")
    print(f"❌ FAILED: {results['total'] - results['passed']}")
    print("="*50)
    
    if results['failed_h1']:
        print("\n🔴 BROKEN H1 TEXT:")
        for path, msg in results['failed_h1']:
            print(f"   - {path}: {msg}")
            
    if results['failed_json']:
        print("\n🔴 INVALID JSON-LD:")
        for path, msg in results['failed_json']:
            print(f"   - {path}: {msg}")
            
    if results['failed_both']:
        print("\n🔴 BOTH FAILED:")
        for path, h1_err, json_err in results['failed_both']:
            print(f"   - {path}: H1({h1_err}) | JSON({json_err})")

    # Exit Code for CI/CD
    if results['passed'] < results['total']:
        sys.exit(1)
    else:
        print("\n🎉 ALL FILES VALID!")
        sys.exit(0)

if __name__ == "__main__":
    main()
