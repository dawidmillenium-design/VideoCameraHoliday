#!/usr/bin/env python3
"""
Auto-fixes specific hreflang and canonical issues identified by the validator.
"""
import os
from pathlib import Path
from bs4 import BeautifulSoup

BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday"

# The 10 files that need fixing based on the latest validation report
FILES_TO_FIX = {
    # 8 Files missing 'x-default' hreflang tag
    "ja-JP/guias/nuevas-camaras-2026.html": "x-default",
    "reviews/insta360-x4-review.html": "x-default",
    "reviews/sony-zv-1-ii-review.html": "x-default",
    "reviews/insta360-go-3s-hands-free-review.html": "x-default",
    "destinations/insta360-x4-travel-workflow-ipad-southeast-asia.html": "x-default",
    "reviews/extreme-weather-camera-guide.html": "x-default",
    "destinations/best-cameras-african-safari-2026.html": "x-default",
    "how-to/film-travel-videos-without-crowds.html": "x-default",
    
    # 2 Files missing 'canonical' tag
    "reviews/gopro-hero-12-review.html": "canonical",
    "reviews/canon-r50-review.html": "canonical"
}

def fix_file(filepath):
    path = Path(filepath)
    if not path.exists():
        print(f"⚠️ File not found: {filepath}")
        return False
    
    with open(path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    
    head = soup.head
    if not head:
        print(f"⚠️ No <head> tag in {filepath}")
        return False

    modified = False
    issue = FILES_TO_FIX[filepath]
    
    # Construct the correct URL for this file
    clean_path = filepath.replace('\\', '/').lstrip('/')
    file_url = f"{BASE_URL}/{clean_path}"

    if issue == "x-default":
        existing = head.find('link', attrs={'rel': 'alternate', 'hreflang': 'x-default'})
        if not existing:
            tag = soup.new_tag('link', rel='alternate', hreflang='x-default', href=file_url)
            head.append(tag)
            modified = True
            print(f"✅ Added x-default to {filepath}")

    elif issue == "canonical":
        existing = head.find('link', attrs={'rel': 'canonical'})
        if not existing:
            tag = soup.new_tag('link', rel='canonical', href=file_url)
            head.append(tag)
            modified = True
            print(f"✅ Added canonical to {filepath}")

    if modified:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        return True
    
    return False

def main():
    print("🔧 Starting Hreflang & Canonical Auto-Fix...")
    fixed_count = 0
    for filepath, issue in FILES_TO_FIX.items():
        if fix_file(filepath):
            fixed_count += 1
            
    print(f"\n🎉 Done! Successfully updated {fixed_count} files.")
    print("Please commit these changes and re-run the validator workflow.")

if __name__ == "__main__":
    main()
