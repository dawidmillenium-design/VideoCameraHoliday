#!/usr/bin/env python3
"""Create missing city HTML files for cities in JSON but not on disk."""

import json
from pathlib import Path

# Load city data
with open('/workspace/city-through-the-lens/all_50_cities.json', 'r') as f:
    CITIES = json.load(f)

# Get existing files
existing = set([f.stem for f in Path('/workspace/city-through-the-lens').glob('*-interview-preview.html')])

# Find missing
missing = []
for city in CITIES:
    if city['slug'] not in existing:
        missing.append(city)

print(f"Found {len(missing)} missing city files to create")

# Basic template for missing cities
template = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{city} Through the Lens | Holiday Video Camera</title>
  <meta name="description" content="Filming in {city}? Local videographer guide with real locations and tips.">
  <link rel="canonical" href="https://dawidmillenium-design.github.io/VideoCameraHoliday/city-through-the-lens/{slug}.html">
  <link rel="stylesheet" href="/assets/site-shell.css">
</head>
<body>
  <nav class="site-nav"><div class="container"><a href="/">Home</a><a href="/guides/">Guides</a><a href="/reviews/">Reviews</a><a href="/city-through-the-lens/">Cities</a></div></nav>
  <header class="site-header"><div class="container"><h1>Holiday Video Camera</h1></div></header>
  <main>
    <article class="container">
      <h1>City Through the Lens: {city}, {country}</h1>
      <p><em>This page is being updated with local videographer insights. Check back soon!</em></p>
      <h2>Quick Facts</h2>
      <ul>
        <li><strong>Top locations:</strong> {attr1}, {attr2}, {attr3}</li>
        <li><strong>Best season:</strong> {weather}</li>
        <li><strong>Airport:</strong> {airport}</li>
        <li><strong>Featured camera:</strong> {camera}</li>
      </ul>
    </article>
  </main>
  <footer class="site-footer"><div class="container"><p>&copy; 2026 Holiday Video Camera</p></div></footer>
</body>
</html>
'''

created = 0
for city in missing:
    slug = city['slug']
    filepath = Path(f'/workspace/city-through-the-lens/{slug}.html')
    
    content = template.format(
        city=city['city'],
        country=city['country'],
        slug=slug,
        attr1=city['attraction1'],
        attr2=city['attraction2'],
        attr3=city['attraction3'],
        weather=city['weather'],
        airport=city['airport'],
        camera=city['camera']
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    created += 1
    print(f"✓ Created: {city['city']}")

print(f"\nCreated {created} new city files")
