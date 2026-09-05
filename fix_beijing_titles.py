#!/usr/bin/env python3
"""
Fix remaining "Beijing" title issues in city pages.
- Scan all *-interview-preview.html files
- Replace H1 and title containing "Beijing" with correct city name
"""

import os
import re
import glob

BASE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.join(BASE, "city-through-the-lens")

# City name mapping (slug -> display name)
CITY_NAMES = {
    "ahmedabad": "Ahmedabad",
    "amsterdam": "Amsterdam",
    "athens": "Athens",
    "baghdad": "Baghdad",
    "bali": "Bali",
    "bangalore": "Bangalore",
    "bangkok": "Bangkok",
    "barcelona": "Barcelona",
    "beijing": "Beijing",
    "berlin": "Berlin",
    "bogota": "Bogotá",
    "budapest": "Budapest",
    "buenos-aires": "Buenos Aires",
    "cairo": "Cairo",
    "cape-town": "Cape Town",
    "cartagena": "Cartagena",
    "chengdu": "Chengdu",
    "chennai": "Chennai",
    "chiang-mai": "Chiang Mai",
    "chongqing": "Chongqing",
    "cusco": "Cusco",
    "delhi": "Delhi",
    "dhaka": "Dhaka",
    "dongguan": "Dongguan",
    "dubai": "Dubai",
    "foshan": "Foshan",
    "guadalajara": "Guadalajara",
    "guangzhou": "Guangzhou",
    "hangzhou": "Hangzhou",
    "hanoi": "Hanoi",
    "ho-chi-minh": "Ho Chi Minh City",
    "hong-kong": "Hong Kong",
    "hyderabad": "Hyderabad",
    "istanbul": "Istanbul",
    "jaipur": "Jaipur",
    "jakarta": "Jakarta",
    "karachi": "Karachi",
    "kinshasa": "Kinshasa",
    "kolkata": "Kolkata",
    "lagos": "Lagos",
    "lahore": "Lahore",
    "lima": "Lima",
    "lisbon": "Lisbon",
    "london": "London",
    "luanda": "Luanda",
    "luang-prabang": "Luang Prabang",
    "manila": "Manila",
    "marrakech": "Marrakech",
    "mexico-city": "Mexico City",
    "moscow": "Moscow",
    "mumbai": "Mumbai",
    "nagoya": "Nagoya",
    "nairobi": "Nairobi",
    "nanjing": "Nanjing",
    "new-york-city": "New York City",
    "osaka": "Osaka",
    "paris": "Paris",
    "prague": "Prague",
    "rio-de-janeiro": "Rio de Janeiro",
    "riyadh": "Riyadh",
    "rome": "Rome",
    "santiago": "Santiago",
    "sao-paulo": "São Paulo",
    "seoul": "Seoul",
    "shanghai": "Shanghai",
    "shenyang": "Shenyang",
    "shenzhen": "Shenzhen",
    "siem-reap": "Siem Reap",
    "singapore": "Singapore",
    "tehran": "Tehran",
    "tianjin": "Tianjin",
    "tokyo": "Tokyo",
    "vienna": "Vienna",
    "xian": "Xi'an",
    "yangon": "Yangon",
}

def extract_city_slug(filename):
    """Extract slug from filename."""
    return filename.replace("-interview-preview.html", "")

def get_city_name(slug):
    """Get display name for a slug."""
    return CITY_NAMES.get(slug, slug.replace("-", " ").title())

def has_beijing_title(html):
    """Check if H1 or title contains 'Beijing'."""
    # Check H1
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    if h1_match and "Beijing" in h1_match.group(1):
        return True
    # Check title tag
    title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
    if title_match and "Beijing" in title_match.group(1):
        return True
    return False

def fix_beijing_titles(html, city_name):
    """Replace Beijing in H1 and title with city_name."""
    # Fix H1
    h1_pattern = r'(<h1[^>]*>)(.*?)(</h1>)'
    def h1_repl(match):
        content = match.group(2)
        # Replace "Beijing" with city_name (case-insensitive)
        new_content = re.sub(r'Beijing', city_name, content, flags=re.IGNORECASE)
        return match.group(1) + new_content + match.group(3)
    html = re.sub(h1_pattern, h1_repl, html, flags=re.DOTALL)

    # Fix title
    title_pattern = r'(<title>)(.*?)(</title>)'
    def title_repl(match):
        content = match.group(2)
        new_content = re.sub(r'Beijing', city_name, content, flags=re.IGNORECASE)
        return match.group(1) + new_content + match.group(3)
    html = re.sub(title_pattern, title_repl, html, flags=re.DOTALL)

    return html

def process_page(filepath):
    """Process a single city page."""
    filename = os.path.basename(filepath)
    slug = extract_city_slug(filename)
    city_name = get_city_name(slug)

    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    if not has_beijing_title(html):
        return slug, 'skip', 'no Beijing found'

    # Fix the titles
    html = fix_beijing_titles(html, city_name)

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    return slug, 'done', f'replaced Beijing with {city_name}'

def main():
    city_pages = sorted(glob.glob(os.path.join(CITY_DIR, "*-interview-preview.html")))

    done = 0
    skip = 0
    fail = 0
    results = []

    for filepath in city_pages:
        slug, status, msg = process_page(filepath)
        results.append((slug, status, msg))
        if status == 'done':
            done += 1
        elif status == 'skip':
            skip += 1
        else:
            fail += 1

    print(f"\n=== BEIJING TITLE FIX SUMMARY ===")
    print(f"  Done: {done}")
    print(f"  Skipped: {skip}")
    print(f"  Failed: {fail}")
    print(f"\n--- Details ---")
    for slug, status, msg in results:
        if status != 'skip':
            print(f"  [{status:4s}] {slug}: {msg}")

if __name__ == "__main__":
    main()