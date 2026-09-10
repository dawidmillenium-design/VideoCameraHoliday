#!/usr/bin/env python3
"""
Content-Quality Guardrail for Internal Links.
Ensures link contexts are factually accurate, not misleading, and pass the "plain text" test.
"""

import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup

# Configuration
SITE_ROOT = Path(__file__).parent.parent
SITEMAP_FILE = SITE_ROOT / "sitemap.xml"

# Rules to catch misleading context based on recent PR feedback
MISLEADING_CONTEXT_RULES = [
    {
        "id": "size_contradiction_fullframe",
        "pattern": r"\b(smaller|compact|pocketable|lightweight)\b.*\b(full-frame|full frame)\b",
        "message": "Calling a full-frame camera 'smaller', 'compact', or 'pocketable' is misleading."
    },
    {
        "id": "misleading_compact_category",
        "pattern": r"\bcompact-camera (technique|guide|review)\b.*\b(R5|A7S|GH6|drone|UAV|full-frame)\b",
        "message": "Labeling non-compact gear (R5, A7S, GH6, drones) as 'compact-camera technique' is inaccurate."
    },
    {
        "id": "unverified_stabilization",
        "pattern": r"\b(stronger|better|superior|best)\b.*\bstabilization\b",
        "message": "Claims of 'stronger/better stabilization' must be verified against target specs."
    },
    {
        "id": "unverified_autofocus",
        "pattern": r"\b(stronger|better|superior|best)\b.*\bautofocus\b",
        "message": "Claims of 'stronger/better autofocus' must be verified against target specs."
    }
]

GENERIC_ANCHOR_PATTERNS = [
    r"^(click here|read more|learn more|this page|here|more)$"
]

def parse_sitemap():
    """Extract all URLs from the sitemap."""
    if not SITEMAP_FILE.exists():
        print(f"❌ Sitemap not found at {SITEMAP_FILE}")
        sys.exit(1)
    
    tree = ET.parse(SITEMAP_FILE)
    root = tree.getroot()
    
    # Handle namespace if present
    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls = []
    for loc in root.findall('.//sm:loc', ns):
        urls.append(loc.text)
    
    # Fallback if no namespace
    if not urls:
        for loc in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
            urls.append(loc.text)
            
    return urls

def get_local_path(url):
    """Convert a sitemap URL to a local file path."""
    # Extract path from URL (e.g., https://domain.com/VideoCameraHoliday/reviews/... -> /VideoCameraHoliday/reviews/...)
    # Assuming the repo root maps to the web root
    match = re.search(r'(\/[a-zA-Z0-9\-_\/]+\.html)', url)
    if match:
        return SITE_ROOT / match.group(1).lstrip('/')
    return None

def extract_links_with_context(file_path):
    """Extract internal links and their surrounding paragraph context."""
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        
        # Only check internal links starting with /
        if not href.startswith('/'):
            continue
            
        anchor_text = a_tag.get_text(strip=True)
        
        # Get parent paragraph for context
        parent_p = a_tag.find_parent('p')
        context_text = parent_p.get_text(strip=True) if parent_p else anchor_text
        
        links.append({
            'href': href,
            'anchor': anchor_text,
            'context': context_text,
            'source': file_path
        })
        
    return links

def validate_link(link):
    """Run all guardrail checks on a single link."""
    issues = []
    context_lower = link['context'].lower()
    
    # 1. Check for misleading factual claims
    for rule in MISLEADING_CONTEXT_RULES:
        if re.search(rule['pattern'], context_lower, re.IGNORECASE):
            issues.append(f"Rule [{rule['id']}]: {rule['message']}")
            
    # 2. Plain text test: Check for generic anchors
    for pattern in GENERIC_ANCHOR_PATTERNS:
        if re.match(pattern, link['anchor'].lower()):
            issues.append(f"Generic anchor text '{link['anchor']}' fails the plain text test.")
            
    # 3. Check if target exists (basic sanity check)
    target_path = get_local_path(f"https://dummy.com{link['href']}")
    if target_path and not target_path.exists():
        issues.append(f"Target file does not exist: {link['href']}")
        
    return issues

def main():
    print("️  Running Content-Quality Guardrail...\n")
    
    urls = parse_sitemap()
    total_issues = 0
    files_checked = 0
    
    for url in urls:
        file_path = get_local_path(url)
        if not file_path or not file_path.exists():
            continue
            
        files_checked += 1
        links = extract_links_with_context(file_path)
        
        for link in links:
            issues = validate_link(link)
            if issues:
                total_issues += len(issues)
                rel_path = file_path.relative_to(SITE_ROOT)
                print(f"⚠️  File: {rel_path}")
                print(f"   Link: {link['href']}")
                print(f"   Context: '{link['context'][:80]}...'")
                for issue in issues:
                    print(f"   ❌ {issue}")
                print()

    print(f"✅ Checked {files_checked} sitemap pages.")
    
    if total_issues > 0:
        print(f"\n❌ FAILED: Found {total_issues} content-quality issues.")
        print("Please fix the misleading contexts before merging.")
        sys.exit(1)
    else:
        print("\n🎉 PASSED: All link contexts meet quality standards.")
        sys.exit(0)

if __name__ == '__main__':
    main()
