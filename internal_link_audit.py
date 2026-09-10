#!/usr/bin/env python3
"""
Internal Link Audit Script for VideoCameraHoliday
Analyzes sitemap URLs, finds orphan pages, broken links, and linking opportunities.
"""

import os
import re
from pathlib import Path
from collections import defaultdict
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import json

BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday/"
WORKSPACE = Path("/workspace")

def load_sitemap_urls():
    """Extract all URLs from sitemap.xml"""
    sitemap_path = WORKSPACE / "sitemap.xml"
    urls = []
    
    try:
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        for url in root.findall('.//ns:url', ns):
            loc = url.find('ns:loc', ns)
            if loc is not None and loc.text:
                urls.append(loc.text)
    except Exception as e:
        print(f"Error parsing sitemap: {e}")
    
    return urls

def url_to_relative_path(url):
    """Convert absolute URL to relative file path"""
    if not url.startswith(BASE_URL):
        return None
    relative = url.replace(BASE_URL, "")
    if relative.endswith("/"):
        relative += "index.html"
    return WORKSPACE / relative

def get_all_html_files():
    """Get all HTML files in workspace"""
    html_files = []
    for root, dirs, files in os.walk(WORKSPACE):
        # Skip workspace, node_modules, .git directories
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]
        for file in files:
            if file.endswith('.html'):
                html_files.append(Path(root) / file)
    return html_files

def extract_internal_links(html_path):
    """Extract all internal links from an HTML file"""
    links = []
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        for tag in soup.find_all(['a', 'link']):
            href = tag.get('href') or tag.get('src')
            if not href:
                continue
            
            # Skip external links, anchors, mailto, tel, javascript
            if href.startswith(('http://', 'https://', '#', 'mailto:', 'tel:', 'javascript:')):
                continue
            
            # Skip CSS/JS files
            if href.endswith(('.css', '.js')):
                continue
            
            # Normalize path
            if href.startswith('/VideoCameraHoliday/'):
                href = href.replace('/VideoCameraHoliday/', '')
            
            links.append(href)
    except Exception as e:
        print(f"Error reading {html_path}: {e}")
    
    return links

def check_link_exists(link, all_files_set):
    """Check if a linked target exists"""
    # Handle directory indexes
    if link.endswith('/'):
        link += 'index.html'
    
    # Remove query strings and fragments
    link = link.split('?')[0].split('#')[0]
    
    # Check various path formats
    possible_paths = [
        WORKSPACE / link,
        WORKSPACE / link.replace('.html', '/index.html'),
    ]
    
    for path in possible_paths:
        if path.exists():
            return True, path
    
    return False, None

def analyze_incoming_links(sitemap_urls, all_html_files):
    """Build a graph of incoming links per page"""
    incoming_links = defaultdict(list)
    
    for html_file in all_html_files:
        links = extract_internal_links(html_file)
        relative_path = str(html_file.relative_to(WORKSPACE))
        
        for link in links:
            # Normalize link path
            if link.endswith('/'):
                link += 'index.html'
            link = link.split('?')[0].split('#')[0]
            
            # Store incoming link
            incoming_links[link].append({
                'source': relative_path,
                'anchor': 'link'  # Could extract anchor text if needed
            })
    
    return incoming_links

def main():
    print("=" * 70)
    print("INTERNAL LINK AUDIT - VideoCameraHoliday")
    print("=" * 70)
    
    # Load sitemap URLs
    print("\n📋 Loading sitemap URLs...")
    sitemap_urls = load_sitemap_urls()
    print(f"   Found {len(sitemap_urls)} URLs in sitemap.xml")
    
    # Get all HTML files
    print("\n📁 Scanning HTML files...")
    all_html_files = get_all_html_files()
    print(f"   Found {len(all_html_files)} HTML files")
    
    # Create sets for quick lookup
    sitemap_paths = set()
    for url in sitemap_urls:
        path = url_to_relative_path(url)
        if path:
            sitemap_paths.add(str(path.relative_to(WORKSPACE)))
    
    all_files_set = {str(f.relative_to(WORKSPACE)) for f in all_html_files}
    
    # Analyze incoming links
    print("\n🔗 Analyzing internal link structure...")
    incoming_links = analyze_incoming_links(sitemap_urls, all_html_files)
    
    # Find orphan pages (in sitemap but no incoming links from sitemap pages)
    print("\n🔍 Finding orphan pages...")
    orphans = []
    for url in sitemap_urls:
        path = url_to_relative_path(url)
        if not path:
            continue
        
        relative_path = str(path.relative_to(WORKSPACE))
        # Check if this page has incoming links
        if relative_path not in incoming_links or len(incoming_links[relative_path]) == 0:
            # Only consider content pages, not index/hub pages
            if 'index.html' not in relative_path or relative_path.count('/') > 1:
                orphans.append(relative_path)
    
    print(f"   Found {len(orphans)} potential orphan pages:")
    for orphan in orphans[:10]:  # Show first 10
        print(f"      - {orphan}")
    if len(orphans) > 10:
        print(f"      ... and {len(orphans) - 10} more")
    
    # Find pages with few incoming links
    print("\n📊 Analyzing pages with low incoming link count...")
    low_authority_pages = []
    for url in sitemap_urls:
        path = url_to_relative_path(url)
        if not path:
            continue
        
        relative_path = str(path.relative_to(WORKSPACE))
        incoming_count = len(incoming_links.get(relative_path, []))
        
        if incoming_count < 3:
            low_authority_pages.append({
                'path': relative_path,
                'incoming_count': incoming_count
            })
    
    low_authority_pages.sort(key=lambda x: x['incoming_count'])
    print(f"   Found {len(low_authority_pages)} pages with fewer than 3 incoming links")
    print("   Top 10 lowest authority pages:")
    for page in low_authority_pages[:10]:
        print(f"      - {page['path']} ({page['incoming_count']} incoming links)")
    
    # Check for broken links
    print("\n❌ Checking for broken internal links...")
    broken_links = []
    for html_file in all_html_files:
        links = extract_internal_links(html_file)
        for link in links:
            exists, target_path = check_link_exists(link, all_files_set)
            if not exists:
                broken_links.append({
                    'source': str(html_file.relative_to(WORKSPACE)),
                    'target': link
                })
    
    print(f"   Found {len(broken_links)} broken internal links")
    if broken_links[:5]:
        print("   First 5 broken links:")
        for bl in broken_links[:5]:
            print(f"      - {bl['source']} → {bl['target']}")
    
    # Find linked targets not in sitemap
    print("\n📝 Finding valid linked targets missing from sitemap...")
    linked_targets = set()
    for html_file in all_html_files:
        links = extract_internal_links(html_file)
        for link in links:
            exists, target_path = check_link_exists(link, all_files_set)
            if exists:
                linked_targets.add(str(target_path.relative_to(WORKSPACE)))
    
    missing_from_sitemap = linked_targets - sitemap_paths
    # Filter out non-content files
    missing_from_sitemap = [p for p in missing_from_sitemap 
                           if not p.startswith('workspace/') 
                           and 'preview' not in p.lower()]
    
    print(f"   Found {len(missing_from_sitemap)} valid pages missing from sitemap")
    print("   Examples:")
    for missing in list(missing_from_sitemap)[:10]:
        print(f"      - {missing}")
    
    # Calculate average anchors per page
    print("\n📈 Calculating link density...")
    total_links = sum(len(incoming_links[p]) for p in incoming_links)
    avg_links = total_links / len(all_html_files) if all_html_files else 0
    print(f"   Average internal links per page: {avg_links:.1f}")
    
    # Generate report
    print("\n" + "=" * 70)
    print("AUDIT SUMMARY")
    print("=" * 70)
    print(f"Sitemap URLs audited:          {len(sitemap_urls)}")
    print(f"Broken internal links:         {len(broken_links)}")
    print(f"Orphan sitemap pages:          {len(orphans)}")
    print(f"Pages with <3 incoming links:  {len(low_authority_pages)}")
    print(f"Average internal anchors/page: {avg_links:.1f}")
    print(f"Valid targets not in sitemap:  {len(missing_from_sitemap)}")
    
    # Save detailed report
    report = {
        'audit_date': '2026-01-01',
        'sitemap_urls': len(sitemap_urls),
        'broken_links': broken_links,
        'orphans': orphans,
        'low_authority_pages': low_authority_pages,
        'missing_from_sitemap': list(missing_from_sitemap),
        'average_links_per_page': avg_links
    }
    
    report_path = WORKSPACE / "link-audit-report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: {report_path}")
    
    # Priority recommendations
    print("\n" + "=" * 70)
    print("PRIORITY RECOMMENDATIONS")
    print("=" * 70)
    
    if orphans:
        print("\n1. 🚨 CRITICAL: Add incoming links to orphan pages:")
        for orphan in orphans[:3]:
            print(f"   - {orphan}")
            print(f"     Action: Add to relevant hub pages and related articles")
    
    if low_authority_pages:
        print(f"\n2. ⚠️  HIGH: Strengthen {len(low_authority_pages)} low-authority pages:")
        print("   Focus on city pages and comparison pages with contextual links")
    
    if missing_from_sitemap:
        print(f"\n3. 📋 MEDIUM: Add {len(missing_from_sitemap)} valid pages to sitemap:")
        print("   Review and add important comparison and how-to pages")
    
    if broken_links:
        print(f"\n4. 🔧 FIX: Repair {len(broken_links)} broken links")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
