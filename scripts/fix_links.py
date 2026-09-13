#!/usr/bin/env python3
"""
fix_links.py
Automates the repair of broken internal links and generates missing content stubs.
"""

import os
import re
from datetime import datetime
from pathlib import Path

# Configuration
ROOT_DIR = Path(os.getcwd())
HTML_EXTENSIONS = ['.html']
STUB_DIR = ROOT_DIR

# 1. Path Normalization Map (Broken -> Fixed)
# Using regex patterns to ensure we catch variations in quotes/spaces
PATH_FIXES = [
    # Navigation & Core Pages
    (r'href=["\'](\.\./)+index\.html["\']', 'href="/index.html"'),
    (r'href=["\'](\.\./)+blog\.html["\']', 'href="/blog.html"'),
    (r'href=["\'](\.\./)+about\.html["\']', 'href="/about.html"'),
    (r'href=["\'](\.\./)+contact\.html["\']', 'href="/contact.html"'),
    (r'href=["\'](\.\./)+privacy\.html["\']', 'href="/privacy.html"'),
    (r'href=["\'](\.\./)+terms\.html["\']', 'href="/terms.html"'),
    (r'href=["\'](\.\./)+disclaimer\.html["\']', 'href="/disclaimer.html"'),
    
    # Assets (CSS/JS)
    (r'href=["\'](\.\./)+css/style\.css["\']', 'href="/css/style.css"'),
    (r'src=["\'](\.\./)+js/main\.js["\']', 'src="/js/main.js"'),
    (r'href=["\']style\.css["\']', 'href="/css/style.css"'), # Catch bare style.css
    
    # Specific Content Pages (Relative to root)
    (r'href=["\'](\.\./)+city-through-the-lens/["\']', 'href="/city-through-the-lens/"'),
    
    # Prefix Cleanup: Remove /VideoCameraHoliday/ prefix
    # This catches both href and src attributes
    (r'(href|src)=["\']/VideoCameraHoliday/', r'\1="/'),
]

# 2. Missing Content Remediation List
# Format: (Relative Path from Root, Title, H1 Text)
MISSING_PAGES = [
    ("reviews/dji-osmo-pocket-3-review.html", "DJI Osmo Pocket 3 Review - Coming Soon", "DJI Osmo Pocket 3 Review"),
    ("reviews/gopro-hero-13-review.html", "GoPro Hero 13 Review - Coming Soon", "GoPro Hero 13 Review"),
    ("guides/best-holiday-video-cameras-2026.html", "Best Holiday Video Cameras 2026 - Guide", "Best Holiday Video Cameras 2026"),
    ("reviews/dji-osmo-action-5-review.html", "DJI Osmo Action 5 Review - Coming Soon", "DJI Osmo Action 5 Review"),
    ("guides/best-budget-holiday-camera-under-500.html", "Best Budget Camera Under $500 - Guide", "Best Budget Holiday Camera Under $500"),
    ("reviews/sony-zv-1-ii-review.html", "Sony ZV-1 II Review - Coming Soon", "Sony ZV-1 II Review"),
    ("reviews/insta360-x5-review.html", "Insta360 X5 Review - Coming Soon", "Insta360 X5 Review"),
    ("reviews/iphone-16-pro-video-review.html", "iPhone 16 Pro Video Review - Coming Soon", "iPhone 16 Pro Video Review"),
    ("how-to/gear-maintenance-field-cleaning.html", "Gear Maintenance & Field Cleaning - Guide", "Gear Maintenance & Field Cleaning"),
]

def get_stub_html(title, h1_text):
    """Generates a basic SEO-friendly HTML stub."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | VideoCameraHoliday</title>
    <meta name="description" content="This comprehensive guide/review for {h1_text} is currently being written by our travel videography team. Check back soon for expert insights.">
    <link rel="canonical" href="https://videocameraholiday.com/{title.lower().replace(' - coming soon', '').replace(' - guide', '').replace(' ', '-').replace('/', '')}.html">
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <header>
        <nav>
            <a href="/">Home</a> | <a href="/blog.html">Blog</a> | <a href="/reviews">Reviews</a>
        </nav>
    </header>
    <main style="max-width: 800px; margin: 4rem auto; padding: 0 1rem; text-align: center;">
        <h1>{h1_text}</h1>
        <p style="font-size: 1.2rem; color: #555;">
            This comprehensive review/guide is currently being written by our travel videography team. 
            We are testing the gear in real-world holiday conditions to bring you the best advice.
        </p>
        <p><strong>Check back soon!</strong></p>
        <br>
        <a href="/" style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">Return to Homepage</a>
    </main>
    <footer>
        <p>&copy; {datetime.now().year} VideoCameraHoliday. All rights reserved.</p>
    </footer>
</body>
</html>
"""

def fix_file_content(content):
    """Applies regex replacements to file content."""
    modified = False
    new_content = content
    
    for pattern, replacement in PATH_FIXES:
        # Check if change occurs
        if re.search(pattern, new_content):
            new_content = re.sub(pattern, replacement, new_content)
            modified = True
            
    return new_content, modified

def create_stub_files():
    """Creates missing HTML stub files."""
    created_count = 0
    for rel_path, title, h1_text in MISSING_PAGES:
        full_path = ROOT_DIR / rel_path
        
        # Create directory if it doesn't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not full_path.exists():
            content = get_stub_html(title, h1_text)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Created stub: {rel_path}")
            created_count += 1
        else:
            print(f"⚠️  Skipped (exists): {rel_path}")
            
    return created_count

def process_html_files():
    """Recursively scans and fixes HTML files."""
    modified_count = 0
    scanned_count = 0
    
    for html_file in ROOT_DIR.rglob("*.html"):
        # Skip files inside .git or node_modules if present
        if '.git' in str(html_file) or 'node_modules' in str(html_file):
            continue
            
        scanned_count += 1
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content, was_modified = fix_file_content(content)
            
            if was_modified:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                modified_count += 1
                print(f"🔧 Fixed links in: {html_file.relative_to(ROOT_DIR)}")
                
        except Exception as e:
            print(f"❌ Error processing {html_file}: {e}")
            
    return modified_count, scanned_count

def main():
    print("🚀 Starting Link Repair Automation...")
    print("-" * 40)
    
    # Step 1: Fix existing files
    print("\n📂 Phase 1: Normalizing Paths & Cleaning Prefixes")
    mod_count, scan_count = process_html_files()
    
    # Step 2: Create missing stubs
    print("\n📄 Phase 2: Generating Missing Content Stubs")
    stub_count = create_stub_files()
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 AUTOMATION SUMMARY")
    print("=" * 40)
    print(f"Files Scanned:      {scan_count}")
    print(f"Files Modified:     {mod_count}")
    print(f"Stub Pages Created: {stub_count}")
    print("=" * 40)
    
    if mod_count == 0 and stub_count == 0:
        print("✨ No changes needed. Repository is clean.")
        return 0
    else:
        print("✅ Automation complete. Changes ready for commit.")
        return 0

if __name__ == "__main__":
    exit(main())
