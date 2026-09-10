import os
from pathlib import Path
from bs4 import BeautifulSoup

BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday"

# The exact 8 files flagged by the validator
files_to_fix = [
    "ja-JP/nuevas-camaras-2026.html", 
    "reviews/insta360-x4-review.html",
    "reviews/sony-zv-1-ii-review.html",
    "reviews/insta360-go-3s-hands-free-review.html",
    "destinations/insta360-x4-travel-workflow-ipad-southeast-asia.html",
    "reviews/extreme-weather-camera-guide.html",
    "destinations/best-cameras-african-safari-2026.html",
    "how-to/film-travel-videos-without-crowds.html"
]

print("🔧 Starting Hreflang Fix for 8 files...\n")

for file_path in files_to_fix:
    path = Path(file_path)
    if not path.exists():
        print(f"⚠️ File not found (might have been moved): {file_path}")
        continue
    
    with open(path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    
    # Check if x-default already exists to avoid duplicates
    existing = soup.find('link', attrs={'rel': 'alternate', 'hreflang': 'x-default'})
    if existing:
        print(f"✅ Already has x-default: {file_path}")
        continue
    
    # Create the x-default tag
    x_default_tag = soup.new_tag('link', rel='alternate', hreflang='x-default', href=f"{BASE_URL}/{file_path}")
    
    # Append to head
    if soup.head:
        soup.head.append(x_default_tag)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"✅ Fixed: {file_path}")
    else:
        print(f"❌ No <head> tag found in: {file_path}")

print("\n🎉 Done! Commit these changes and run the validator again.")
