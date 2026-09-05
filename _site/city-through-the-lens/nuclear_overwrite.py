#!/usr/bin/env python3
"""
NUCLEAR OVERWRITE SCRIPT: Regenerate all 50 city preview pages with accurate data.
Reads all_50_cities.json and overwrites each HTML file with city-specific content.
Preserves nav/header/footer structure but replaces ALL body content.
"""

import json
import re
from pathlib import Path

# Load the complete city data
with open('/workspace/city-through-the-lens/all_50_cities.json', 'r', encoding='utf-8') as f:
    CITIES = json.load(f)

print(f"Loaded {len(CITIES)} cities from JSON")

def extract_template_parts(html_content):
    """Extract nav, header, footer from existing HTML to preserve site structure."""
    # Extract <nav> section
    nav_match = re.search(r'(<nav[^>]*>.*?</nav>)', html_content, re.DOTALL)
    nav = nav_match.group(1) if nav_match else ''
    
    # Extract <header> section  
    header_match = re.search(r'(<header[^>]*>.*?</header>)', html_content, re.DOTALL)
    header = header_match.group(1) if header_match else ''
    
    # Extract <footer> section
    footer_match = re.search(r'(<footer[^>]*>.*?</footer>)', html_content, re.DOTALL)
    footer = footer_match.group(1) if footer_match else ''
    
    return nav, header, footer

def generate_city_body(city_data):
    """Generate completely new body content for a city using its JSON data."""
    city = city_data['city']
    country = city_data['country']
    camera = city_data['camera']
    challenge = city_data['challenge']
    attr1, tip1 = city_data['attraction1'], city_data['tip1']
    attr2, tip2 = city_data['attraction2'], city_data['tip2']
    attr3, tip3 = city_data['attraction3'], city_data['tip3']
    weather = city_data['weather']
    airport = city_data['airport']
    permits = city_data['permits']
    slug = city_data['slug']
    
    # Determine video embed (only Bangkok and Lima have real videos)
    if 'bangkok' in slug.lower():
        video_embed = '''<div class="video-slot">
  <div class="video-embed">
    <iframe src="https://www.youtube.com/embed/7_amUIdgHs4" title="Insta360 X5 Field Test — Bangkok, Thailand" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe>
  </div>
  <p class="video-caption">🎬 Real field footage: Insta360 X5 in Bangkok, Thailand</p>
</div>'''
    elif 'lima' in slug.lower():
        video_embed = '''<div class="video-slot">
  <div class="video-embed">
    <iframe src="https://www.youtube.com/embed/gRWhgo0KBqY" title="Insta360 X5 Peru — Huacachina Desert Oasis" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe>
  </div>
  <p class="video-caption">🎬 Real field footage: Insta360 X5 in Huacachina, Peru</p>
</div>'''
    else:
        video_embed = '''<div class="video-slot">
  <div class="video-placeholder">🎬 Local videographer interview coming soon — subscribe on YouTube to see it first</div>
</div>'''
    
    body = f'''
<main>
  <article itemscope itemtype="https://schema.org/Article">
    <div class="container">
      <nav class="breadcrumbs" aria-label="Breadcrumb">
        <a href="/">Home</a> › <a href="/city-through-the-lens/">Cities</a> › <span>{city}</span>
      </nav>
      
      <h1 itemprop="headline">City Through the Lens: {city}, {country}</h1>
      
      <p class="intro" itemprop="description">Local videographers reveal how they film their hometown — the real locations, permit hurdles, and techniques you won't find in guidebooks.</p>
      
      {video_embed}
      
      <section class="quick-takeaways">
        <h2>Quick Takeaways for Filmmakers</h2>
        <ul>
          <li><strong>Best filming season:</strong> {weather.split('.')[0]}</li>
          <li><strong>Top 3 landmarks:</strong> {attr1}, {attr2}, {attr3}</li>
          <li><strong>Main airport:</strong> {airport.split('(')[0].strip()}</li>
          <li><strong>Drone rules:</strong> {permits.split('Drones')[1] if 'Drones' in permits else 'Check local regulations'}</li>
          <li><strong>Featured camera:</strong> {camera}</li>
        </ul>
      </section>
      
      <section class="must-film-locations">
        <h2>3 Must-Film Locations in {city}</h2>
        
        <div class="location-card">
          <h3>1. {attr1}</h3>
          <p><strong>Filming Tip:</strong> {tip1}</p>
        </div>
        
        <div class="location-card">
          <h3>2. {attr2}</h3>
          <p><strong>Filming Tip:</strong> {tip2}</p>
        </div>
        
        <div class="location-card">
          <h3>3. {attr3}</h3>
          <p><strong>Filming Tip:</strong> {tip3}</p>
        </div>
      </section>
      
      <section class="weather-reality">
        <h2>Weather Reality Check</h2>
        <p>{weather}</p>
        <p><strong>Pro tip:</strong> Plan your shoot dates around these conditions. The "best" months mean better light, fewer crowds, and more predictable weather windows.</p>
      </section>
      
      <section class="airport-transfer">
        <h2>Airport Transfer & Arrival Tips</h2>
        <p><strong>{airport}</strong></p>
        <p>Factor in transfer time when booking flights. Arriving early gives you buffer for gear checks and acclimatization before shooting.</p>
      </section>
      
      <section class="permits-etiquette">
        <h2>Permits, Rules & Local Etiquette</h2>
        <p>{permits}</p>
        <p><strong>Remember:</strong> Always ask before filming people, especially in religious or residential areas. Respect local customs — it's the difference between getting great footage and being asked to delete it.</p>
      </section>
      
      <section class="coming-soon-interview">
        <h2>Coming Soon: Local Videographer Interview</h2>
        <p>We're currently filming interviews with local creators in {city} who will share:</p>
        <ul>
          <li>How they capture {attr1} without the crowds</li>
          <li>Their go-to settings for {challenge.lower()}</li>
          <li>Hidden spots tourists never find</li>
          <li>How to navigate permit requirements as a foreign filmmaker</li>
        </ul>
        <p><strong>Are you a videographer based in {city}?</strong> <a href="mailto:dawid@holidayvideocamera.com">Contact us</a> to be featured in this series.</p>
      </section>
    </div>
  </article>
</main>
'''
    return body

def generate_full_html(nav, header, footer, body, city_data):
    """Assemble the complete HTML file."""
    city = city_data['city']
    country = city_data['country']
    slug = city_data['slug']
    
    # Generate meta tags
    title = f"{city} Through the Lens: Local Videographer Guide | Holiday Video Camera"
    meta_desc = f"Filming in {city}? Local videographers reveal the best locations, permit rules, and techniques for capturing {country}'s top destinations."
    canonical = f"https://dawidmillenium-design.github.io/VideoCameraHoliday/city-through-the-lens/{slug}.html"
    
    # BreadcrumbList schema
    breadcrumb_schema = f'''{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{ "@type": "ListItem", "position": 1, "name": "Home", "item": "https://dawidmillenium-design.github.io/VideoCameraHoliday/" }},
    {{ "@type": "ListItem", "position": 2, "name": "Cities", "item": "https://dawidmillenium-design.github.io/VideoCameraHoliday/city-through-the-lens/" }},
    {{ "@type": "ListItem", "position": 3, "name": "{city}", "item": "{canonical}" }}
  ]
}}'''
    
    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{meta_desc}">
  <link rel="canonical" href="{canonical}">
  <link rel="stylesheet" href="/assets/site-shell.css">
  <script type="application/ld+json">{breadcrumb_schema}</script>
</head>
<body>
{nav}
{header}
{body}
{footer}
</body>
</html>
'''
    return full_html

# Process each city
processed = 0
errors = []

for city_data in CITIES:
    slug = city_data['slug']
    city_name = city_data['city']
    html_file = Path(f'/workspace/city-through-the-lens/{slug}.html')
    
    if not html_file.exists():
        errors.append(f"File not found: {html_file}")
        continue
    
    try:
        # Read existing HTML
        with open(html_file, 'r', encoding='utf-8') as f:
            existing_html = f.read()
        
        # Extract template parts
        nav, header, footer = extract_template_parts(existing_html)
        
        # Generate new body
        new_body = generate_city_body(city_data)
        
        # Assemble full HTML
        new_html = generate_full_html(nav, header, footer, new_body, city_data)
        
        # Write back
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_html)
        
        processed += 1
        print(f"✓ Updated: {city_name}")
        
    except Exception as e:
        errors.append(f"Error processing {city_name}: {str(e)}")
        print(f"✗ Error: {city_name} - {e}")

print(f"\n{'='*50}")
print(f"PROCESSING COMPLETE")
print(f"{'='*50}")
print(f"Successfully updated: {processed}/{len(CITIES)} files")
if errors:
    print(f"Errors encountered: {len(errors)}")
    for err in errors:
        print(f"  - {err}")
else:
    print("No errors encountered!")
