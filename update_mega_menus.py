#!/usr/bin/env python3
"""
Script to update all HTML files with mega menu navigation
"""

import os
import re
from pathlib import Path

# Mega menu HTML blocks
REVIEWS_MEGA_MENU = '''<li class="mega-item">
    <a href="/VideoCameraHoliday/reviews/" aria-haspopup="true" aria-expanded="false">
        Reviews <span class="dropdown-arrow">▾</span>
    </a>
    
    <div class="mega-menu" role="menu">
        <div class="mega-container">
            <div class="mega-column">
                <h4>Browse Categories</h4>
                <ul>
                    <li><a href="/VideoCameraHoliday/reviews/">📷 All Camera Reviews</a></li>
                    <li><a href="/VideoCameraHoliday/guides/best-waterproof-cameras-beach.html">🌊 Waterproof & Action</a></li>
                    <li><a href="/VideoCameraHoliday/guides/best-budget-holiday-camera-under-500.html">💰 Budget (Under $500)</a></li>
                    <li><a href="/VideoCameraHoliday/comparisons/">⚖️ Head-to-Head Comparisons</a></li>
                    <li><a href="/VideoCameraHoliday/guides/best-camera-hiking-holidays.html">🥾 Hiking & Adventure</a></li>
                </ul>
            </div>
            <div class="mega-column">
                <h4>Most Popular Reviews</h4>
                <ul>
                    <li><a href="/VideoCameraHoliday/reviews/dji-osmo-pocket-3-review.html">🏆 DJI Osmo Pocket 3</a></li>
                    <li><a href="/VideoCameraHoliday/reviews/gopro-hero-13-review.html">🏄 GoPro Hero 13</a></li>
                    <li><a href="/VideoCameraHoliday/reviews/insta360-x5-review.html">🔄 Insta360 X5</a></li>
                    <li><a href="/VideoCameraHoliday/reviews/iphone-16-pro-video-review.html">📱 iPhone 16 Pro</a></li>
                    <li><a href="/VideoCameraHoliday/reviews/sony-zv-1-ii-review.html">📸 Sony ZV-1 II</a></li>
                </ul>
            </div>
            <div class="mega-column">
                <h4>Featured Field Test</h4>
                <a href="/VideoCameraHoliday/interviews/insta360-x5-20-cities-world-tour.html" class="mega-featured">
                    <div class="mega-featured-img">🌍</div>
                    <span class="tag">Exclusive Interview</span>
                    <h5>The Insta360 X5 World Tour: 20 Cities</h5>
                    <p>Heat shutdowns, 999-hour uploads, and police bans across 5 continents. Read the raw field diary.</p>
                </a>
            </div>
        </div>
    </div>
</li>'''

BUYING_GUIDES_MEGA_MENU = '''<li class="mega-item">
    <a href="/VideoCameraHoliday/guides/" aria-haspopup="true" aria-expanded="false">
        Buying Guides <span class="dropdown-arrow">▾</span>
    </a>
    
    <div class="mega-menu" role="menu">
        <div class="mega-container">
            <div class="mega-column">
                <h4>By Budget</h4>
                <ul>
                    <li><a href="/VideoCameraHoliday/guides/best-holiday-video-cameras-2026.html">🏆 Best Cameras 2026</a></li>
                    <li><a href="/VideoCameraHoliday/guides/best-budget-holiday-camera-under-500.html">💰 Under $500</a></li>
                    <li><a href="/VideoCameraHoliday/guides/">💼 Under $1,000</a></li>
                    <li><a href="/VideoCameraHoliday/guides/">🎬 Professional ($2,000+)</a></li>
                </ul>
            </div>
            <div class="mega-column">
                <h4>By Use Case</h4>
                <ul>
                    <li><a href="/VideoCameraHoliday/guides/best-waterproof-cameras-beach.html">🌊 Waterproof & Beach</a></li>
                    <li><a href="/VideoCameraHoliday/guides/best-camera-hiking-holidays.html">🥾 Hiking & Backpacking</a></li>
                    <li><a href="/VideoCameraHoliday/destinations/best-cameras-beach-holidays.html">🏖️ Beach Holidays</a></li>
                    <li><a href="/VideoCameraHoliday/destinations/">⛷️ Ski & Snow</a></li>
                    <li><a href="/VideoCameraHoliday/destinations/">🏙️ City Breaks</a></li>
                </ul>
            </div>
            <div class="mega-column">
                <h4>Flagship Guide</h4>
                <a href="/VideoCameraHoliday/guides/best-holiday-video-cameras-2026.html" class="mega-featured">
                    <div class="mega-featured-img">🏆</div>
                    <span class="tag">Updated for 2026</span>
                    <h5>Best Holiday Video Cameras 2026</h5>
                    <p>The definitive roundup — 8 tested picks for every kind of trip and budget. If you only read one guide, read this one.</p>
                </a>
            </div>
        </div>
    </div>
</li>'''

DESTINATIONS_MEGA_MENU = '''<li class="mega-item">
    <a href="/VideoCameraHoliday/destinations/" aria-haspopup="true" aria-expanded="false">
        Destinations <span class="dropdown-arrow">▾</span>
    </a>
    
    <div class="mega-menu" role="menu">
        <div class="mega-container">
            <div class="mega-column">
                <h4>By Region</h4>
                <ul>
                    <li><a href="/VideoCameraHoliday/destinations/best-camera-southeast-asia.html">🌏 Southeast Asia</a></li>
                    <li><a href="/VideoCameraHoliday/destinations/">🗾 Japan</a></li>
                    <li><a href="/VideoCameraHoliday/destinations/">🇮🇸 Iceland & Nordic</a></li>
                    <li><a href="/VideoCameraHoliday/destinations/">🇧🇷 South America</a></li>
                    <li><a href="/VideoCameraHoliday/destinations/">🏜️ Middle East & Desert</a></li>
                </ul>
            </div>
            <div class="mega-column">
                <h4>By Environment</h4>
                <ul>
                    <li><a href="/VideoCameraHoliday/destinations/best-cameras-beach-holidays.html">🏖️ Beach & Islands</a></li>
                    <li><a href="/VideoCameraHoliday/destinations/">🏙️ City Breaks</a></li>
                    <li><a href="/VideoCameraHoliday/destinations/">⛷️ Ski & Snow</a></li>
                    <li><a href="/VideoCameraHoliday/techniques/underwater-filming-travel-guide.html">🤿 Underwater</a></li>
                    <li><a href="/VideoCameraHoliday/destinations/">🏜️ Desert & Heat</a></li>
                </ul>
            </div>
            <div class="mega-column">
                <h4>Featured Destination</h4>
                <a href="/VideoCameraHoliday/destinations/best-camera-southeast-asia.html" class="mega-featured">
                    <div class="mega-featured-img">🌴</div>
                    <span class="tag">Complete Guide</span>
                    <h5>The Right Camera for Southeast Asia</h5>
                    <p>Humidity, temples, night markets, monsoons. After 4 years testing 50+ cameras — the 3-camera kit that survives.</p>
                </a>
            </div>
        </div>
    </div>
</li>'''

HOW_TO_MEGA_MENU = '''<li class="mega-item">
    <a href="/VideoCameraHoliday/how-to/" aria-haspopup="true" aria-expanded="false">
        How-To <span class="dropdown-arrow">▾</span>
    </a>
    
    <div class="mega-menu" role="menu">
        <div class="mega-container">
            <div class="mega-column">
                <h4>Filming Techniques</h4>
                <ul>
                    <li><a href="/VideoCameraHoliday/how-to/">🤳 Stabilize Without a Gimbal</a></li>
                    <li><a href="/VideoCameraHoliday/techniques/timelapse-hyperlapse-travel.html">🌅 Timelapse & Hyperlapse</a></li>
                    <li><a href="/VideoCameraHoliday/techniques/underwater-filming-travel-guide.html">🤿 Underwater Filming</a></li>
                    <li><a href="/VideoCameraHoliday/how-to/">🎬 Storytelling & Composition</a></li>
                    <li><a href="/VideoCameraHoliday/how-to/">👤 Solo Filming Techniques</a></li>
                </ul>
            </div>
            <div class="mega-column">
                <h4>Workflow & Protection</h4>
                <ul>
                    <li><a href="/VideoCameraHoliday/how-to/gear-maintenance-field-cleaning.html">🔧 Gear Maintenance</a></li>
                    <li><a href="/VideoCameraHoliday/how-to/">🌧️ Protect Gear in Rain</a></li>
                    <li><a href="/VideoCameraHoliday/how-to/">❄️ Cold Weather Filming</a></li>
                    <li><a href="/VideoCameraHoliday/how-to/">💾 Back Up Footage on the Road</a></li>
                    <li><a href="/VideoCameraHoliday/how-to/">💳 Memory Card Guide</a></li>
                </ul>
            </div>
            <div class="mega-column">
                <h4>Essential Guide</h4>
                <a href="/VideoCameraHoliday/how-to/gear-maintenance-field-cleaning.html" class="mega-featured">
                    <div class="mega-featured-img">🔧</div>
                    <span class="tag">Evergreen Guide</span>
                    <h5>Gear Maintenance & Field Cleaning</h5>
                    <p>The 5-minute daily routine that saved my kit through monsoons, deserts, and 200 travel days per year. Battery care, sensor cleaning, and when to DIY.</p>
                </a>
            </div>
        </div>
    </div>
</li>'''

def get_nav_block_for_file(filepath):
    """Generate the complete nav block with mega menus for a given file path"""
    
    # Determine relative path prefix based on file location
    rel_path = os.path.relpath(filepath, '/workspace')
    depth = rel_path.count('/') 
    
    # Build prefix for links based on directory depth
    if depth == 0:
        prefix = "./"
    else:
        prefix = "../" * depth
    
    # For files in subdirectories, we need to adjust paths
    # But mega menus use absolute paths from root
    
    return f'''<ul class="nav-links">
        <li><a href="{prefix}" class="{'active' if 'index.html' in filepath and depth == 0 else ''}">Home</a></li>
        <li><a href="{prefix}city-through-the-lens/">Series</a></li>
        {REVIEWS_MEGA_MENU}
        {BUYING_GUIDES_MEGA_MENU}
        {DESTINATIONS_MEGA_MENU}
        {HOW_TO_MEGA_MENU}
        <li><a href="{prefix}editing/">Editing</a></li>
        <li><a href="{prefix}comparisons/">Comparisons</a></li>
        <li><a href="{prefix}about/">About</a></li>
    </ul>'''

def update_html_file(filepath):
    """Update a single HTML file with mega menu navigation"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False
    
    # Check if file has navigation (skip mega menu template files)
    if 'mega-menu-nav.html' in filepath or 'MEGA_MENU_INTEGRATION_EXAMPLE.html' in filepath or 'mega-menu-footer.html' in filepath:
        print(f"Skipping template file: {filepath}")
        return False
    
    # Find the nav-links section
    nav_pattern = r'(<ul class="nav-links">.*?</ul>)'
    match = re.search(nav_pattern, content, re.DOTALL)
    
    if not match:
        print(f"No nav-links found in {filepath}")
        return False
    
    # Generate new nav block
    rel_path = os.path.relpath(filepath, '/workspace')
    depth = rel_path.count('/')
    
    if depth == 0:
        prefix = "./"
    else:
        prefix = "../" * depth
    
    # Determine active class for home link
    is_index = 'index.html' in filepath and depth == 0
    active_class = 'class="active"' if is_index else ''
    
    new_nav = f'''<ul class="nav-links">
        <li><a href="{prefix}" {active_class}>Home</a></li>
        <li><a href="{prefix}city-through-the-lens/">Series</a></li>
        {REVIEWS_MEGA_MENU}
        {BUYING_GUIDES_MEGA_MENU}
        {DESTINATIONS_MEGA_MENU}
        {HOW_TO_MEGA_MENU}
        <li><a href="{prefix}editing/">Editing</a></li>
        <li><a href="{prefix}comparisons/">Comparisons</a></li>
        <li><a href="{prefix}about/">About</a></li>
    </ul>'''
    
    # Replace old nav with new nav
    new_content = content[:match.start()] + new_nav + content[match.end():]
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    except Exception as e:
        print(f"Error writing {filepath}: {e}")
        return False

def main():
    workspace = '/workspace'
    html_files = []
    
    # Find all HTML files
    for root, dirs, files in os.walk(workspace):
        # Skip .git directory
        if '.git' in root:
            continue
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                html_files.append(filepath)
    
    print(f"Found {len(html_files)} HTML files")
    
    updated = 0
    skipped = 0
    errors = 0
    
    for filepath in html_files:
        result = update_html_file(filepath)
        if result is True:
            updated += 1
        elif result is False:
            # Check if it was skipped intentionally
            if any(x in filepath for x in ['mega-menu-nav.html', 'MEGA_MENU_INTEGRATION_EXAMPLE.html', 'mega-menu-footer.html']):
                skipped += 1
            else:
                errors += 1
        else:
            skipped += 1
    
    print(f"\nResults:")
    print(f"  Updated: {updated}")
    print(f"  Skipped (templates): {skipped}")
    print(f"  Errors: {errors}")

if __name__ == '__main__':
    main()
