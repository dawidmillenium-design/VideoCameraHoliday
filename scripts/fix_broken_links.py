#!/usr/bin/env python3
"""
Broken Link Repair Script
Fixes broken internal links by finding appropriate replacement pages
Prioritizes high-traffic pages based on number of incoming broken links
"""

import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict

REPO_ROOT = Path("/workspace")
AUDIT_FILE = REPO_ROOT / "link-audit-report.json"

# Base URL mapping to local paths
BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday/"

def url_to_local_path(url: str) -> str:
    """Convert a full URL to a local file path relative to repo root."""
    # Remove base URL
    path = url.replace(BASE_URL, "")
    # Remove trailing slash for directories
    path = path.rstrip("/")
    # Add .html if missing
    if path and not path.endswith(".html"):
        path += ".html"
    return path

def find_existing_file(target_url: str) -> str | None:
    """Find an existing file that matches or is similar to the target."""
    target_path = url_to_local_path(target_url)
    target_name = Path(target_path).name
    
    # Direct match
    full_path = REPO_ROOT / target_path
    if full_path.exists():
        return str(full_path.relative_to(REPO_ROOT))
    
    # Try in guides directory
    guides_path = REPO_ROOT / "guides" / target_name
    if guides_path.exists():
        return str(guides_path.relative_to(REPO_ROOT))
    
    # Try to find similar filename
    if "guides" in target_path:
        search_dir = REPO_ROOT / "guides"
    else:
        search_dir = REPO_ROOT
    
    if search_dir.exists():
        for f in search_dir.glob("*.html"):
            # Check if filenames are similar
            if target_name.replace(".html", "") in f.name:
                return str(f.relative_to(REPO_ROOT))
    
    return None

def get_all_html_files() -> dict:
    """Get all HTML files with their titles for intelligent matching."""
    pages = {}
    for html_file in REPO_ROOT.rglob("*.html"):
        # Skip certain directories
        skip_dirs = {".git", "node_modules", "scripts", "assets", "css", "js"}
        if any(d in str(html_file) for d in skip_dirs):
            continue
        
        try:
            with open(html_file, "r", encoding="utf-8", errors="replace") as f:
                soup = BeautifulSoup(f.read(), "lxml")
                title_tag = soup.find("title")
                title = title_tag.text.strip() if title_tag else html_file.stem
                
                # Extract keywords from title
                keywords = set(title.lower().split())
                
                rel_path = str(html_file.relative_to(REPO_ROOT))
                pages[rel_path] = {
                    "title": title,
                    "keywords": keywords,
                    "name": html_file.name
                }
        except Exception as e:
            continue
    
    return pages

def find_best_replacement(broken_url: str, all_pages: dict) -> str | None:
    """Find the best replacement page for a broken link."""
    target_name = broken_url.split("/")[-1].replace("/", "").replace(".html", "")
    
    # Keywords to search for
    keywords = set(target_name.lower().replace("-", " ").split())
    
    best_match = None
    best_score = 0
    
    for path, info in all_pages.items():
        score = 0
        
        # Check filename match
        if target_name in info["name"].lower():
            score += 10
        
        # Check keyword overlap with title
        overlap = len(keywords & info["keywords"])
        score += overlap * 2
        
        # Prefer guides for guide-related content
        if "guides" in target_name and "guides/" in path:
            score += 5
        
        if score > best_score and score > 0:
            best_score = score
            best_match = path
    
    return best_match

def fix_links_in_file(file_path: str, fixes: dict, dry_run: bool = True) -> int:
    """Fix broken links in a single file."""
    full_path = REPO_ROOT / file_path
    if not full_path.exists():
        return 0
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        soup = BeautifulSoup(content, "lxml")
        modified = False
        fixed_count = 0
        
        for a in soup.find_all("a", href=True):
            href = a["href"]
            
            # Check if this is a broken link we need to fix
            if href in fixes:
                new_href = fixes[href]
                if new_href:
                    # Convert to site-root absolute path
                    if not new_href.startswith("/"):
                        new_href = f"/VideoCameraHoliday/{new_href}"
                    
                    print(f"   Fixing: {href} -> {new_href}")
                    a["href"] = new_href
                    modified = True
                    fixed_count += 1
        
        if modified and not dry_run:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(str(soup))
        
        return fixed_count
    
    except Exception as e:
        print(f"   Error processing {file_path}: {e}")
        return 0

def main():
    print("=" * 70)
    print("🔧 BROKEN LINK REPAIR SCRIPT")
    print("=" * 70)
    
    # Load audit report
    if not AUDIT_FILE.exists():
        print(f"❌ Audit file not found: {AUDIT_FILE}")
        return
    
    with open(AUDIT_FILE, "r") as f:
        audit_data = json.load(f)
    
    print(f"\n📊 Loaded audit report:")
    print(f"   Total problems: {audit_data['problem_count']}")
    print(f"   Canonical mismatches: {audit_data['summary']['canonical_mismatch']}")
    print(f"   Missing targets: {audit_data['summary']['missing_internal_target']}")
    
    # Get all HTML files for intelligent matching
    print("\n🔍 Scanning all HTML files...")
    all_pages = get_all_html_files()
    print(f"   Found {len(all_pages)} pages")
    
    # Extract broken links and prioritize by number of sources
    broken_links = {}
    for problem in audit_data["problems"]:
        if problem["type"] == "missing_internal_target":
            target = problem["target"]
            sources = problem["sources"]
            broken_links[target] = {
                "sources": sources,
                "source_count": len(sources),
                "replacement": None
            }
    
    # Sort by priority (most sources first)
    sorted_broken = sorted(
        broken_links.items(),
        key=lambda x: x[1]["source_count"],
        reverse=True
    )
    
    print("\n🎯 Top priority broken links:")
    for i, (url, info) in enumerate(sorted_broken[:15], 1):
        print(f"   {i}. {url.split('/')[-1]} ({info['source_count']} sources)")
    
    # Find replacements for broken links
    print("\n🔎 Finding replacement pages...")
    for url, info in sorted_broken:
        replacement = find_best_replacement(url, all_pages)
        info["replacement"] = replacement
        if replacement:
            print(f"   ✅ {url.split('/')[-1]} -> {replacement}")
        else:
            print(f"   ⚠️  {url.split('/')[-1]} -> No good match found")
    
    # Ask for confirmation
    print("\n" + "=" * 70)
    dry_run = input("Run in DRY RUN mode? (yes/no): ").strip().lower() != "no"
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be modified")
    else:
        confirm = input("\n⚠️  This will modify files. Continue? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            return
    
    # Create mapping of old URLs to new paths
    url_to_new_path = {}
    for url, info in sorted_broken:
        if info["replacement"]:
            url_to_new_path[url] = info["replacement"]
    
    # Group files by which broken links they contain
    files_to_fix = defaultdict(dict)
    for url, info in sorted_broken:
        if info["replacement"]:
            for source_url in info["sources"]:
                source_path = url_to_local_path(source_url)
                files_to_fix[source_path][url] = info["replacement"]
    
    # Fix the links
    print("\n🔨 Fixing broken links...")
    total_fixed = 0
    files_modified = 0
    
    for file_path, fixes in list(files_to_fix.items())[:50]:  # Limit to top 50 files
        count = fix_links_in_file(file_path, fixes, dry_run=dry_run)
        if count > 0:
            total_fixed += count
            files_modified += 1
            print(f"   Fixed {count} links in {file_path}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"   Files processed: {len(files_to_fix)}")
    print(f"   Files modified: {files_modified}")
    print(f"   Links fixed: {total_fixed}")
    
    if dry_run:
        print("\n💡 Run again with 'no' to apply changes")
    
    # Save report
    report = {
        "mode": "dry_run" if dry_run else "live",
        "files_processed": len(files_to_fix),
        "files_modified": files_modified,
        "links_fixed": total_fixed,
        "fixes_applied": [
            {"file": fp, "fixes": fixes}
            for fp, fixes in list(files_to_fix.items())[:20]
        ]
    }
    
    report_file = REPO_ROOT / "broken-link-fix-report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_file}")
    print("=" * 70)

if __name__ == "__main__":
    main()
