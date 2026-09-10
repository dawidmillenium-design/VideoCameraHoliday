#!/usr/bin/env python3
"""
Automated SEO Tag Fixer
Injects missing x-default hreflang and canonical tags into specific HTML files.
"""

import os
from pathlib import Path
from bs4 import BeautifulSoup

# Base URL for your site
BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday"

# The 10 files and the specific tags they are missing
FILES_TO_FIX = {
    # --- Missing x-default hreflang tags ---
    "ja-JP/guias/nuevas-camaras-2026.html": ["x-default"],
    "reviews/insta360-x4-review.html": ["x-default"],
    "reviews/sony-zv-1-ii-review.html": ["x-default"],
    "reviews/insta360-go-3s-hands-free-review.html": ["x-default"],
    "destinations/insta360-x4-travel-workflow-ipad-southeast-asia.html": ["x-default"],
    "reviews/extreme-weather-camera-guide.html": ["x-default"],
    "destinations/best-cameras-african-safari-2026.html": ["x-default"],
    "how-to/film-travel-videos-without-crowds.html": ["x-default"],
    
    # --- Missing canonical tags ---
    "reviews/gopro-hero-12-review.html": ["canonical"],
    "reviews/canon-r50-review.html": ["canonical"],
}

def fix_file(filepath, missing_tags):
    """Parses the file and injects missing tags into the <head>."""
    path = Path(filepath)
    
    if not path.exists():
        print(f"⚠️ File not found: {filepath} (Skipping)")
        return False

    # Read and parse HTML
    with open(path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')

    head = soup.head
    if not head:
        print(f" No <head> tag found in {filepath}")
        return False

    modified = False
    # Construct the full URL for the tag
    file_url = f"{BASE_URL}/{filepath}"

    # 1. Fix x-default
    if "x-default" in missing_tags:
        existing = head.find('link', attrs={'rel': 'alternate', 'hreflang': 'x-default'})
        if not existing:
            tag = soup.new_tag('link', rel='alternate', hreflang='x-default', href=file_url)
            head.append(tag)
            modified = True
            print(f"  ✅ Added x-default to {filepath}")

    # 2. Fix canonical
    if "canonical" in missing_tags:
        existing = head.find('link', attrs={'rel': 'canonical'})
        if not existing:
            tag = soup.new_tag('link', rel='canonical', href=file_url)
            head.append(tag)
            modified = True
            print(f"  ✅ Added canonical to {filepath}")

    # Save the file only if changes were made
    if modified:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        return True
    return False

def main():
    print("🔧 Starting automated SEO tag injection...")
    print("=" * 50)
    
    fixed_count = 0
    for filepath, missing_tags in FILES_TO_FIX.items():
        print(f"Processing: {filepath}")
        if fix_file(filepath, missing_tags):
            fixed_count += 1
            
    print("=" * 50)
    print(f"🎉 Done! Successfully updated {fixed_count} files.")
    print("\n⚠️ Note: Don't forget to move 'ja-JP/guias/nuevas-camaras-2026.html' to 'es-ES/guias/' as it is a Spanish file!")

if __name__ == "__main__":
    main()
