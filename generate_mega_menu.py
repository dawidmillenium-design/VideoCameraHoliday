#!/usr/bin/env python3
"""
Generate MEGA MENU navigation and footer HTML for Holiday Video Camera site.
This script scans all HTML files and creates organized navigation structures.
"""

import os
from pathlib import Path

def get_all_html_files():
    """Scan repository and organize HTML files by category."""
    categories = {
        'guides': [],
        'reviews': [],
        'how-to': [],
        'destinations': [],
        'editing': [],
        'interviews': [],
        'comparisons': [],
        'city-through-the-lens': [],
        'root': []
    }
    
    base_path = Path('/workspace')
    
    for html_file in base_path.rglob('*.html'):
        rel_path = html_file.relative_to(base_path)
        parts = rel_path.parts
        
        # Skip index files for article listings
        if html_file.name in ['index.html', 'index2.html']:
            continue
            
        # Determine category
        if len(parts) > 1 and parts[0] in categories:
            cat = parts[0]
            title = html_file.stem.replace('-', ' ').replace('_', ' ').title()
            # Clean up titles
            title = title.replace('2026', '').replace('2027', '').strip()
            categories[cat].append({
                'path': str(rel_path),
                'title': title,
                'filename': html_file.name
            })
        elif len(parts) == 1:
            # Root level files
            title = html_file.stem.replace('-', ' ').replace('_', ' ').title()
            title = title.replace('24Fps', '24fps').replace('120Fps', '120fps')
            categories['root'].append({
                'path': str(rel_path),
                'title': title,
                'filename': html_file.name
            })
    
    # Sort each category
    for cat in categories:
        categories[cat].sort(key=lambda x: x['title'])
    
    return categories

def generate_mega_menu_html(categories):
    """Generate the top mega menu HTML."""
    
    html = '''<!-- MEGA MENU NAVIGATION -->
<nav class="top-nav">
    <div class="nav-container">
        <a href="./" class="logo">📹 Holiday Video Camera</a>
        <button class="mobile-menu-toggle" onclick="document.querySelector('.nav-links').classList.toggle('active')">☰</button>
        <ul class="nav-links">
            <li><a href="./" class="active">Home</a></li>
            
            <!-- GUIDES MEGA MENU -->
            <li class="mega-item">
                <a href="./guides/">Guides ▼</a>
                <div class="mega-menu">
                    <div class="mega-container">
'''
    
    # Group guides into subcategories
    buying_guides = [g for g in categories['guides'] if 'best' in g['title'].lower() or 'budget' in g['title'].lower() or 'compact' in g['title'].lower()]
    destination_guides = [g for g in categories['guides'] if any(x in g['title'].lower() for x in ['ski', 'hiking', 'waterproof', 'beach', 'southeast', 'city'])]
    other_guides = [g for g in categories['guides'] if g not in buying_guides and g not in destination_guides]
    
    html += '''                        <div class="mega-column">
                            <h4>🛒 Buying Guides</h4>
                            <ul>
'''
    for g in buying_guides[:8]:
        html += f'                                <li><a href="./{g["path"]}">{g["title"]}</a></li>\n'
    html += '''                            </ul>
                        </div>
                        <div class="mega-column">
                            <h4>🏖️ Destination Guides</h4>
                            <ul>
'''
    for g in destination_guides[:8]:
        html += f'                                <li><a href="./{g["path"]}">{g["title"]}</a></li>\n'
    html += '''                            </ul>
                        </div>
                        <div class="mega-column">
                            <h4>📋 Planning & Tips</h4>
                            <ul>
'''
    for g in other_guides[:8]:
        html += f'                                <li><a href="./{g["path"]}">{g["title"]}</a></li>\n'
    html += '''                            </ul>
                        </div>
                        <div class="mega-column">
                            <h4>🎯 Quick Links</h4>
                            <ul>
                                <li><a href="./guides/best-holiday-video-cameras-2026.html">Best Cameras 2026</a></li>
                                <li><a href="./guides/best-budget-holiday-camera-under-500.html">Under $500</a></li>
                                <li><a href="./guides/travel-camera-checklist-2026.html">Camera Checklist</a></li>
                                <li><a href="./guides/state-of-travel-cameras-2026.html">State of Cameras</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </li>
            
            <!-- REVIEWS MEGA MENU -->
            <li class="mega-item">
                <a href="./reviews/">Reviews ▼</a>
                <div class="mega-menu">
                    <div class="mega-container">
                        <div class="mega-column">
                            <h4>📸 Gimbal Cameras</h4>
                            <ul>
'''
    
    gimbal_reviews = [r for r in categories['reviews'] if any(x in r['title'].lower() for x in ['pocket', 'osmo', 'gimbal'])]
    for r in gimbal_reviews[:8]:
        html += f'                                <li><a href="./{r["path"]}">{r["title"]}</a></li>\n'
    
    html += '''                            </ul>
                        </div>
                        <div class="mega-column">
                            <h4>🎬 Action Cameras</h4>
                            <ul>
'''
    
    action_reviews = [r for r in categories['reviews'] if any(x in r['title'].lower() for x in ['gopro', 'action', 'insta360'])]
    for r in action_reviews[:8]:
        html += f'                                <li><a href="./{r["path"]}">{r["title"]}</a></li>\n'
    
    html += '''                            </ul>
                        </div>
                        <div class="mega-column">
                            <h4>📱 Vlogging & Mirrorless</h4>
                            <ul>
'''
    
    vlog_reviews = [r for r in categories['reviews'] if any(x in r['title'].lower() for x in ['zv', 'vlogging', 'mirrorless', 'canon', 'sony', 'fujifilm', 'nikon', 'panasonic', 'iphone'])]
    for r in vlog_reviews[:8]:
        html += f'                                <li><a href="./{r["path"]}">{r["title"]}</a></li>\n'
    
    html += '''                            </ul>
                        </div>
                        <div class="mega-column">
                            <h4>🎥 Roundups</h4>
                            <ul>
                                <li><a href="./reviews/pocket-cinema-cameras-2026-roundup.html">Pocket Cinema Cameras</a></li>
                                <li><a href="./reviews/budget-4k-camcorder-roundup.html">Budget 4K Camcorders</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </li>
            
            <!-- HOW-TO MEGA MENU -->
            <li class="mega-item">
                <a href="./how-to/">How-To ▼</a>
                <div class="mega-menu">
                    <div class="mega-container">
                        <div class="mega-column">
                            <h4>🎬 Filming Techniques</h4>
                            <ul>
'''
    
    filming_ht = [h for h in categories['how-to'] if 'film' in h['title'].lower()]
    for h in filming_ht[:8]:
        html += f'                                <li><a href="./{h["path"]}">{h["title"]}</a></li>\n'
    
    html += '''                            </ul>
                        </div>
                        <div class="mega-column">
                            <h4>🔧 Technical Skills</h4>
                            <ul>
'''
    
    tech_ht = [h for h in categories['how-to'] if any(x in h['title'].lower() for x in ['stabilize', 'backup', 'memory', 'edit', 'vertical', 'audio'])]
    for h in tech_ht[:8]:
        html += f'                                <li><a href="./{h["path"]}">{h["title"]}</a></li>\n'
    
    html += '''                            </ul>
                        </div>
                        <div class="mega-column">
                            <h4>⚡ Quick Tips</h4>
                            <ul>
                                <li><a href="./how-to/stabilize-videos-without-gimbal.html">No Gimbal Needed</a></li>
                                <li><a href="./how-to/backup-travel-photos-videos.html">Backup Footage</a></li>
                                <li><a href="./how-to/choose-memory-card-4k-video.html">Memory Cards</a></li>
                                <li><a href="./how-to/film-better-holiday-videos.html">Better Videos</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </li>
            
            <!-- DESTINATIONS MEGA MENU -->
            <li class="mega-item">
                <a href="./destinations/">Destinations ▼</a>
                <div class="mega-menu">
                    <div class="mega-container">
                        <div class="mega-column">
                            <h4>🏖️ Beach & Water</h4>
                            <ul>
                                <li><a href="./destinations/best-cameras-beach-holidays.html">Beach Holidays</a></li>
                                <li><a href="./destinations/underwater-camera-guide.html">Underwater Guide</a></li>
                            </ul>
                        </div>
                        <div class="mega-column">
                            <h4>🏔️ Adventure</h4>
                            <ul>
                                <li><a href="./destinations/best-cameras-ski-holidays.html">Ski Holidays</a></li>
                                <li><a href="./destinations/best-cameras-desert-travel.html">Desert Travel</a></li>
                            </ul>
                        </div>
                        <div class="mega-column">
                            <h4>🏙️ City Breaks</h4>
                            <ul>
                                <li><a href="./destinations/best-cameras-city-breaks.html">City Breaks</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </li>
            
            <!-- EDITING MEGA MENU -->
            <li class="mega-item">
                <a href="./editing/">Editing ▼</a>
                <div class="mega-menu">
                    <div class="mega-container">
                        <div class="mega-column">
                            <h4>✂️ Editing Software</h4>
                            <ul>
                                <li><a href="./editing/best-editing-apps-holiday-footage.html">Best Editing Apps</a></li>
                                <li><a href="./editing/post-travel-videos-youtube.html">Post to YouTube</a></li>
                            </ul>
                        </div>
                        <div class="mega-column">
                            <h4>🎨 Color & Style</h4>
                            <ul>
                                <li><a href="./editing/color-grading-travel-videos.html">Color Grading</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </li>
            
            <!-- COMPARISONS MEGA MENU -->
            <li class="mega-item">
                <a href="./comparisons/">Comparisons ▼</a>
                <div class="mega-menu">
                    <div class="mega-container">
                        <div class="mega-column">
                            <h4>⚔️ Head-to-Head</h4>
                            <ul>
'''
    
    for c in categories['comparisons'][:8]:
        html += f'                                <li><a href="./{c["path"]}">{c["title"]}</a></li>\n'
    
    html += '''                            </ul>
                        </div>
                        <div class="mega-column">
                            <h4>💰 Value Picks</h4>
                            <ul>
                                <li><a href="./comparisons/budget-vs-premium-travel-cameras.html">Budget vs Premium</a></li>
                                <li><a href="./comparisons/action-camera-vs-gimbal-camera.html">Action vs Gimbal</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </li>
            
            <!-- CITY THROUGH THE LENS -->
            <li><a href="./city-through-the-lens/">🌍 City Series</a></li>
            
            <!-- INTERVIEWS (hidden on desktop, shown in footer) -->
        </ul>
    </div>
</nav>'''
    
    return html

def generate_mega_footer_html(categories):
    """Generate the mega footer HTML."""
    
    html = '''<!-- MEGA FOOTER -->
<footer class="site-footer">
    <div class="footer-container">
        <div class="footer-section">
            <h4>🎬 Series</h4>
            <ul>
                <li><a href="./city-through-the-lens/">City Through the Lens</a></li>
                <li><a href="./city-through-the-lens/#faq">Series FAQ</a></li>
            </ul>
        </div>
        
        <div class="footer-section">
            <h4>🛒 Top Buying Guides</h4>
            <ul>
                <li><a href="./guides/best-holiday-video-cameras-2026.html">Best Cameras 2026</a></li>
                <li><a href="./guides/best-budget-holiday-camera-under-500.html">Under $500</a></li>
                <li><a href="./guides/best-waterproof-cameras-beach.html">Waterproof Cameras</a></li>
                <li><a href="./guides/best-camera-hiking-holidays.html">Hiking Cameras</a></li>
                <li><a href="./guides/best-camera-ski-holidays.html">Ski Holiday Cameras</a></li>
                <li><a href="./guides/travel-camera-checklist-2026.html">Camera Checklist</a></li>
            </ul>
        </div>
        
        <div class="footer-section">
            <h4>📸 Popular Reviews</h4>
            <ul>
                <li><a href="./reviews/dji-osmo-pocket-3-review.html">DJI Pocket 3</a></li>
                <li><a href="./reviews/gopro-hero-13-review.html">GoPro Hero 13</a></li>
                <li><a href="./reviews/insta360-x5-review.html">Insta360 X5</a></li>
                <li><a href="./reviews/dji-osmo-action-5-review.html">DJI Action 5 Pro</a></li>
                <li><a href="./reviews/sony-zv-1-ii-review.html">Sony ZV-1 II</a></li>
                <li><a href="./reviews/iphone-16-pro-video-review.html">iPhone 16 Pro</a></li>
            </ul>
        </div>
        
        <div class="footer-section">
            <h4>🎬 How-To Essentials</h4>
            <ul>
                <li><a href="./how-to/stabilize-videos-without-gimbal.html">Stabilize Without Gimbal</a></li>
                <li><a href="./how-to/backup-travel-photos-videos.html">Backup Footage</a></li>
                <li><a href="./how-to/film-yourself-solo.html">Film Yourself Solo</a></li>
                <li><a href="./how-to/choose-memory-card-4k-video.html">Choose Memory Card</a></li>
                <li><a href="./how-to/film-in-rain-protect-gear.html">Film in Rain</a></li>
            </ul>
        </div>
        
        <div class="footer-section">
            <h4>🏖️ Destinations</h4>
            <ul>
                <li><a href="./destinations/best-cameras-beach-holidays.html">Beach Holidays</a></li>
                <li><a href="./destinations/best-cameras-ski-holidays.html">Ski Holidays</a></li>
                <li><a href="./destinations/best-cameras-city-breaks.html">City Breaks</a></li>
                <li><a href="./destinations/best-cameras-desert-travel.html">Desert Travel</a></li>
                <li><a href="./destinations/underwater-camera-guide.html">Underwater Guide</a></li>
            </ul>
        </div>
        
        <div class="footer-section">
            <h4>✂️ Editing</h4>
            <ul>
                <li><a href="./editing/color-grading-travel-videos.html">Color Grading</a></li>
                <li><a href="./editing/best-editing-apps-holiday-footage.html">Editing Apps</a></li>
                <li><a href="./editing/post-travel-videos-youtube.html">Post to YouTube</a></li>
                <li><a href="./24fps-vs-120fps-holiday-edit-ai-music-sync.html">24fps vs 120fps</a></li>
            </ul>
        </div>
        
        <div class="footer-section">
            <h4>⚔️ Comparisons</h4>
            <ul>
                <li><a href="./comparisons/dji-pocket-3-vs-gopro-hero-13.html">Pocket 3 vs Hero 13</a></li>
                <li><a href="./comparisons/iphone-16-pro-vs-dedicated-camera.html">iPhone vs Camera</a></li>
                <li><a href="./comparisons/budget-vs-premium-travel-cameras.html">Budget vs Premium</a></li>
                <li><a href="./comparisons/action-camera-vs-gimbal-camera.html">Action vs Gimbal</a></li>
            </ul>
        </div>
        
        <div class="footer-section">
            <h4>📰 All Interviews</h4>
            <ul>
'''
    
    # Add top interviews
    featured_interviews = [i for i in categories['interviews'][:12]]
    for i in featured_interviews:
        html += f'                <li><a href="./{i["path"]}">{i["title"]}</a></li>\n'
    
    html += '''                <li><a href="./interviews/">View All Interviews →</a></li>
            </ul>
        </div>
        
        <div class="footer-section">
            <h4>ℹ️ About</h4>
            <ul>
                <li><a href="./about/">About Us</a></li>
                <li><a href="./">Home</a></li>
                <li><a href="./sitemap.xml">Sitemap</a></li>
            </ul>
        </div>
    </div>
    
    <div class="footer-bottom">
        <p>© 2026 <a href="./">Holiday Video Camera</a> — Real travel camera testing. No lab charts.</p>
    </div>
</footer>'''
    
    return html

def main():
    print("Scanning repository for HTML files...")
    categories = get_all_html_files()
    
    print("\n📊 File counts by category:")
    for cat, files in categories.items():
        print(f"   {cat}: {len(files)} files")
    
    print("\n✅ Generating mega menu HTML...")
    mega_menu = generate_mega_menu_html(categories)
    
    print("✅ Generating mega footer HTML...")
    mega_footer = generate_mega_footer_html(categories)
    
    # Save mega menu to file
    with open('/workspace/mega-menu-nav.html', 'w') as f:
        f.write(mega_menu)
    print("📄 Saved mega menu to: /workspace/mega-menu-nav.html")
    
    # Save mega footer to file
    with open('/workspace/mega-menu-footer.html', 'w') as f:
        f.write(mega_footer)
    print("📄 Saved mega footer to: /workspace/mega-menu-footer.html")
    
    # Create an example HTML file showing how to integrate
    example_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mega Menu Integration Example</title>
    <link rel="stylesheet" href="mega-menu.css">
</head>
<body>

<!-- STEP 1: Include the mega menu CSS in your <head> -->
<!-- Add this line to your existing <style> block or link to mega-menu.css -->
<link rel="stylesheet" href="mega-menu.css">

<!-- STEP 2: Replace your existing <nav class="top-nav">...</nav> with this: -->
{mega_menu}

<!-- STEP 3: Your page content goes here -->
<article class="container">
    <h1>Your Article Content</h1>
    <p>This is where your article content goes...</p>
</article>

<!-- STEP 4: Replace your existing <footer class="site-footer">...</footer> with this: -->
{mega_footer}

<script>
// Optional: Add smooth hover delay for better UX
document.querySelectorAll('.mega-item').forEach(item => {{
    let timeout;
    item.addEventListener('mouseenter', () => {{
        clearTimeout(timeout);
    }});
    item.addEventListener('mouseleave', () => {{
        timeout = setTimeout(() => {{
            // Menu will auto-hide via CSS
        }}, 200);
    }});
}});
</script>

</body>
</html>
'''
    
    with open('/workspace/MEGA_MENU_INTEGRATION_EXAMPLE.html', 'w') as f:
        f.write(example_html)
    print("📄 Created integration example: /workspace/MEGA_MENU_INTEGRATION_EXAMPLE.html")
    
    # Create README with instructions
    readme = '''# MEGA MENU Implementation Guide

## Files Created

1. **mega-menu.css** - CSS styles for the mega menu and footer
2. **mega-menu-nav.html** - Top navigation mega menu HTML
3. **mega-menu-footer.html** - Bottom footer mega menu HTML  
4. **MEGA_MENU_INTEGRATION_EXAMPLE.html** - Example showing integration

## How to Implement

### Step 1: Add CSS to All Pages

Add this line to the `<head>` section of every HTML file:
```html
<link rel="stylesheet" href="mega-menu.css">
```

Or copy the contents of `mega-menu.css` into your existing `<style>` block.

### Step 2: Replace Navigation

In every HTML file, find your existing:
```html
<nav class="top-nav">...</nav>
```

Replace it with the contents of `mega-menu-nav.html`.

### Step 3: Replace Footer

In every HTML file, find your existing:
```html
<footer class="site-footer">...</footer>
```

Replace it with the contents of `mega-menu-footer.html`.

## SEO Benefits

This mega menu structure creates a **Hub-and-Spoke model** that:

1. **Passes link equity** from homepage to all articles
2. **Eliminates orphaned pages** - every page is reachable within 2 clicks
3. **Creates topical silos** - Google understands your content hierarchy
4. **Improves crawlability** - search bots can discover all 160+ pages easily
5. **Enhances user experience** - visitors can navigate to any content instantly

## Mobile Responsive

The mega menu automatically converts to an accordion-style menu on mobile devices (under 1024px width).

## Categories Organized

- **Guides**: Buying guides, destination guides, planning tips
- **Reviews**: Gimbal cameras, action cameras, vlogging cameras, roundups
- **How-To**: Filming techniques, technical skills, quick tips
- **Destinations**: Beach, ski, city breaks, desert, underwater
- **Editing**: Software, color grading, YouTube posting
- **Comparisons**: Head-to-head reviews, value picks
- **Interviews**: Featured in footer (60+ articles)
- **City Through the Lens**: Dedicated series link

---

Generated for: Holiday Video Camera
Total files analyzed: 160+ HTML files
'''
    
    with open('/workspace/MEGA_MENU_README.md', 'w') as f:
        f.write(readme)
    print("📄 Created implementation guide: /workspace/MEGA_MENU_README.md")
    
    print("\n✅ DONE! Follow the instructions in MEGA_MENU_README.md to implement.")

if __name__ == '__main__':
    main()
