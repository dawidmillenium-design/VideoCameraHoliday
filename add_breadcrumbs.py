#!/usr/bin/env python3
"""
Add breadcrumb navigation to all city-through-the-lens pages.
- Home > City Through the Lens > [City Name]
- Includes JSON-LD structured data for SEO
"""

import os
import re
import glob

BASE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.join(BASE, "city-through-the-lens")

# Breadcrumb HTML template
BREADCRUMB_HTML = '''
        <!-- ===== BREADCRUMB ===== -->
        <nav class="breadcrumb" aria-label="Breadcrumb">
            <div class="container">
                <ol itemscope itemtype="https://schema.org/BreadcrumbList">
                    <li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
                        <a itemprop="item" href="/VideoCameraHoliday/">
                            <span itemprop="name">Home</span>
                        </a>
                        <meta itemprop="position" content="1" />
                    </li>
                    <li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
                        <a itemprop="item" href="/VideoCameraHoliday/city-through-the-lens/">
                            <span itemprop="name">City Through the Lens</span>
                        </a>
                        <meta itemprop="position" content="2" />
                    </li>
                    <li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
                        <span itemprop="name">{city_name}</span>
                        <meta itemprop="position" content="3" />
                    </li>
                </ol>
            </div>
        </nav>
'''

# CSS to add if not present
BREADCRUMB_CSS = '''
        /* Breadcrumb navigation */
        .breadcrumb {
            background: #111;
            padding: 12px 0;
            border-bottom: 1px solid #333;
            font-size: 0.85rem;
            color: #888;
        }
        .breadcrumb .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 0 20px;
        }
        .breadcrumb ol {
            list-style: none;
            margin: 0;
            padding: 0;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
        }
        .breadcrumb li {
            display: inline-flex;
            align-items: center;
        }
        .breadcrumb li:not(:last-child)::after {
            content: "›";
            margin: 0 10px;
            color: #555;
            font-size: 1.1rem;
        }
        .breadcrumb a {
            color: #e94560;
            text-decoration: none;
            transition: color 0.2s;
        }
        .breadcrumb a:hover {
            color: #ff6b6b;
            text-decoration: underline;
        }
        .breadcrumb li:last-child span {
            color: #e0e0e0;
            font-weight: 500;
        }
'''

def get_city_name(filepath):
    """Extract city name from the file or H1."""
    filename = os.path.basename(filepath)
    # Try to get from filename first
    slug = filename.replace("-interview-preview.html", "")
    # Convert slug to title case
    city_name = slug.replace("-", " ").title()
    
    # Special cases
    overrides = {
        "new-york-city": "New York City",
        "ho-chi-minh": "Ho Chi Minh City",
        "sao-paulo": "São Paulo",
        "rio-de-janeiro": "Rio de Janeiro",
        "mexico-city": "Mexico City",
        "cape-town": "Cape Town",
        "chiang-mai": "Chiang Mai",
        "siem-reap": "Siem Reap",
        "luang-prabang": "Luang Prabang",
        "hong-kong": "Hong Kong",
        "buenos-aires": "Buenos Aires",
        "guadalajara": "Guadalajara",
        "cartagena": "Cartagena",
        "marrakech": "Marrakech",
        "kolkata": "Kolkata",
        "hyderabad": "Hyderabad",
        "bangalore": "Bangalore",
        "chennai": "Chennai",
        "ahmedabad": "Ahmedabad",
        "chongqing": "Chongqing",
        "guangzhou": "Guangzhou",
        "shenzhen": "Shenzhen",
        "chengdu": "Chengdu",
        "hangzhou": "Hangzhou",
        "nanjing": "Nanjing",
        "shenyang": "Shenyang",
        "dongguan": "Dongguan",
        "foshan": "Foshan",
        "tianjin": "Tianjin",
        "xian": "Xi'an",
        "yangon": "Yangon",
    }
    if slug in overrides:
        city_name = overrides[slug]
    
    return city_name

def has_breadcrumb(html):
    """Check if the page already has a breadcrumb."""
    return 'class="breadcrumb"' in html

def add_css(html):
    """Add breadcrumb CSS to the page if not present."""
    if '.breadcrumb' in html:
        return html
    
    # Find the <style> block with non-critical CSS
    if '</style>' in html:
        # Insert before the closing </style>
        html = html.replace('</style>', BREADCRUMB_CSS + '\n    </style>', 1)
    elif '</head>' in html:
        # No style block found, create one
        html = html.replace('</head>', '    <style>\n' + BREADCRUMB_CSS + '\n    </style>\n</head>', 1)
    
    return html

def add_breadcrumb(html, city_name):
    """Insert breadcrumb after the header."""
    breadcrumb_html = BREADCRUMB_HTML.format(city_name=city_name)
    
    # Look for the closing header tag
    if '</header>' in html:
        # Insert breadcrumb right after </header>
        html = html.replace('</header>', '</header>\n' + breadcrumb_html, 1)
        return html, True
    
    # Fallback: insert after <header> if the closing tag isn't found
    if '<header' in html:
        # Try to find the end of the header block
        pattern = r'(<header[^>]*>.*?</header>)'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            header_end = match.end()
            html = html[:header_end] + '\n' + breadcrumb_html + html[header_end:]
            return html, True
    
    return html, False

def process_page(filepath):
    """Process a single city page."""
    filename = os.path.basename(filepath)
    slug = filename.replace("-interview-preview.html", "")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Check if breadcrumb already exists
    if has_breadcrumb(html):
        return slug, 'skip', 'already has breadcrumb'
    
    # Get city name
    city_name = get_city_name(filepath)
    
    # Add CSS
    html = add_css(html)
    
    # Add breadcrumb
    html, success = add_breadcrumb(html, city_name)
    
    if not success:
        return slug, 'fail', 'could not insert breadcrumb'
    
    # Write the file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return slug, 'done', f'added breadcrumb for {city_name}'

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
    
    print(f"\n=== BREADCRUMB ADDITION SUMMARY ===")
    print(f"  Done: {done}")
    print(f"  Skipped: {skip}")
    print(f"  Failed: {fail}")
    print(f"\n--- Details ---")
    for slug, status, msg in results:
        if status != 'skip':
            print(f"  [{status:4s}] {slug}: {msg}")

if __name__ == "__main__":
    main()