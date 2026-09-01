#!/usr/bin/env python3
"""
NUCLEAR OVERWRITE: Regenerate all city preview pages with accurate JSON data.
Preserves nav/footer HTML structure but replaces ALL body content.
"""

import json
import os
import re

# Load the JSON dataset
with open('city-through-the-lens/JSON.dataset', 'r', encoding='utf-8') as f:
    cities_data = json.load(f)

# Template for generating city-specific content
def generate_city_content(city_data):
    city = city_data['city']
    country = city_data['country']
    camera = city_data['camera']
    challenge = city_data['challenge']
    attr1 = city_data['attraction1']
    tip1 = city_data['tip1']
    attr2 = city_data['attraction2']
    tip2 = city_data['tip2']
    attr3 = city_data['attraction3']
    tip3 = city_data['tip3']
    weather = city_data['weather']
    airport = city_data['airport']
    permits = city_data['permits']
    slug = city_data['slug']
    
    # Determine video embed based on city
    if city == "Bangkok":
        video_embed = '''<div class="video-slot">
  <div class="video-embed">
    <iframe src="https://www.youtube.com/embed/7_amUIdgHs4" title="Insta360 X5 Field Test â€” Bangkok, Thailand" frameborder="0" allowfullscreen loading="lazy"></iframe>
  </div>
  <p class="video-caption">ðŸŽ¬ Real field footage: Insta360 X5 in Bangkok, Thailand</p>
</div>'''
        video_schema = '''<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "Insta360 X5 Field Test â€” Bangkok, Thailand",
  "description": "Real-world Insta360 X5 footage shot on location in Bangkok, Thailand by travel videographer Dawid Millennium.",
  "thumbnailUrl": "https://i.ytimg.com/vi/7_amUIdgHs4/hqdefault.jpg",
  "uploadDate": "2026-08-25",
  "embedUrl": "https://www.youtube.com/embed/7_amUIdgHs4",
  "contentUrl": "https://youtube.com/shorts/7_amUIdgHs4",
  "author": { "@type": "Person", "name": "Dawid Millennium" },
  "publisher": { "@type": "Organization", "name": "Holiday Video Camera" }
}
</script>'''
    elif city == "Lima":
        video_embed = '''<div class="video-slot">
  <div class="video-embed">
    <iframe src="https://www.youtube.com/embed/gRWhgo0KBqY" title="Insta360 X5 Peru â€” Huacachina field footage" frameborder="0" allowfullscreen loading="lazy"></iframe>
  </div>
  <p class="video-caption">ðŸŽ¬ Real field footage: Insta360 X5 in Huacachina, Peru â€” shot by Dawid Millennium</p>
</div>'''
        video_schema = '''<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "Insta360 X5 in Peru â€” Huacachina Desert Oasis (Raw 360 Footage)",
  "description": "Raw Insta360 X5 360-degree footage filmed on location in Huacachina, Peru by travel videographer Dawid Millennium.",
  "thumbnailUrl": "https://i.ytimg.com/vi/gRWhgo0KBqY/hqdefault.jpg",
  "uploadDate": "2026-07-22",
  "duration": "PT14S",
  "embedUrl": "https://www.youtube.com/embed/gRWhgo0KBqY",
  "contentUrl": "https://www.youtube.com/watch?v=gRWhgo0KBqY",
  "author": { "@type": "Person", "name": "Dawid Millennium" },
  "publisher": { "@type": "Organization", "name": "Holiday Video Camera" }
}
</script>'''
    else:
        video_embed = '''<div class="video-slot">
  <div class="video-placeholder">ðŸŽ¬ Field video for this guide coming soon â€” subscribe on YouTube to see it first</div>
</div>'''
        video_schema = ''
    
    content = f'''
<article>
  <nav class="breadcrumbs" aria-label="Breadcrumb">
    <a href="/">Home</a> â€º <a href="/city-through-the-lens/">City Through the Lens</a> â€º <span>{city}</span>
  </nav>
  
  <h1>{city} Through the Lens: Local Filmmaking Insights</h1>
  <p class="intro"><strong>Country:</strong> {country} | <strong>Camera Used:</strong> {camera} | <strong>Main Challenge:</strong> {challenge}</p>
  
  {video_embed}
  
  <section class="quick-takeaways">
    <h2>ðŸŽ¯ Quick Takeaways for Filming in {city}</h2>
    <div class="takeaway-box">
      <p><strong>Best Time to Visit:</strong> {weather.split('.')[0] if '.' in weather else weather[:50]}</p>
      <p><strong>Top 3 Landmarks:</strong> {attr1}, {attr2}, {attr3}</p>
      <p><strong>Airport:</strong> {airport}</p>
      <p><strong>Key Rule:</strong> {permits.split('.')[0] if '.' in permits else permits[:60]}</p>
    </div>
  </section>
  
  <section class="must-film-locations">
    <h2>ðŸŽ¬ 3 Must-Film Locations in {city}</h2>
    
    <div class="location-card">
      <h3>1. {attr1}</h3>
      <p>{tip1}</p>
    </div>
    
    <div class="location-card">
      <h3>2. {attr2}</h3>
      <p>{tip2}</p>
    </div>
    
    <div class="location-card">
      <h3>3. {attr3}</h3>
      <p>{tip3}</p>
    </div>
  </section>
  
  <section class="weather-reality">
    <h2>ðŸŒ¤ï¸ Weather Reality for Videographers</h2>
    <p>{weather}</p>
    <p><strong>Pro Tip:</strong> Always check the forecast before your shoot day. In {city.split()[0] if ' ' in city else city}, weather can change rapidly, so have backup indoor locations ready.</p>
  </section>
  
  <section class="airport-transfer">
    <h2>âœˆï¸ Airport Transfer & Arrival Tips</h2>
    <p>{airport}</p>
    <p><strong>Gear Transport:</strong> Keep all cameras and lithium batteries in your carry-on. Check local customs rules for professional equipment.</p>
  </section>
  
  <section class="permits-etiquette">
    <h2>ðŸ“œ Permits & Local Etiquette</h2>
    <p>{permits}</p>
    <p><strong>Cultural Note:</strong> When filming in {country}, always ask permission before pointing your camera at people, especially in religious or private spaces. A smile and a gesture go a long way.</p>
  </section>
  
  <section class="coming-soon-interview">
    <h2>ðŸŽ™ï¸ Coming Soon: Local Videographer Interview</h2>
    <p>We're reaching out to local creators in {city} to ask:</p>
    <ul>
      <li>What's the one spot tourists always miss that you love filming?</li>
      <li>How do you handle {challenge.lower()}?</li>
      <li>What's your go-to setting for shooting at {attr1.split()[0] if ' ' in attr1 else attr1}?</li>
      <li>Any hidden gems for food B-roll near {attr2.split()[0] if ' ' in attr2 else attr2}?</li>
    </ul>
    <p><em>Want to be featured? Contact us!</em></p>
  </section>
  
  <section class="call-for-videographer">
    <h2>ðŸ“¹ Are You a Videographer Based in {city}?</h2>
    <p>We're building the ultimate resource for travel filmmakers. If you live in {city} and want to share your local expertise, <a href="/contact/">get in touch</a>. We'd love to feature your insights and footage in our City Through the Lens series.</p>
  </section>
  
  <section class="related-links">
    <h2>ðŸ”— Related Guides</h2>
    <ul>
      <li><a href="/guides/best-holiday-video-cameras-2026.html">Best Holiday Video Cameras 2026</a></li>
      <li><a href="/how-to/film-markets-street-food.html">How to Film Street Food Markets</a></li>
      <li><a href="/destinations/camera-guide-southeast-asia-complete-2026.html">Southeast Asia Camera Guide</a></li>
    </ul>
  </section>
</article>
'''
    
    return content, video_schema

# Process each city
for city_data in cities_data:
    city = city_data['city']
    slug = city_data['slug']
    filename = f"city-through-the-lens/{slug}.html"
    
    if not os.path.exists(filename):
        print(f"Skipping {city} - file does not exist")
        continue
    
    # Read existing file to extract nav and footer
    with open(filename, 'r', encoding='utf-8') as f:
        existing_html = f.read()
    
    # Extract navigation (everything up to and including <nav class="main-nav">...</nav>)
    nav_match = re.search(r'(<nav class="main-nav">.*?</nav>)', existing_html, re.DOTALL)
    nav_html = nav_match.group(1) if nav_match else ''
    
    # Extract header (site header with logo)
    header_match = re.search(r'(<header class="site-header">.*?</header>)', existing_html, re.DOTALL)
    header_html = header_match.group(1) if header_match else ''
    
    # Extract footer
    footer_match = re.search(r'(<footer class="site-footer">.*?</footer>)', existing_html, re.DOTALL)
    footer_html = footer_match.group(1) if footer_match else ''
    
    # Extract head section (for schema injection)
    head_match = re.search(r'(<head>.*?</head>)', existing_html, re.DOTALL)
    head_html = head_match.group(1) if head_match else ''
    
    # Generate new city-specific content
    new_content, video_schema = generate_city_content(city_data)
    
    # Update title and meta description
    city_name = city_data['city']
    country_name = city_data['country']
    new_title = f"{city_name} Filming Guide: Local Tips & Best Locations | Holiday Video Camera"
    new_meta = f"Expert filming guide for {city_name}, {country_name}. Real local insights on best locations, permits, weather, and camera settings from our City Through the Lens series."
    
    # Update head section with new title, meta, and schema
    updated_head = re.sub(r'<title>.*?</title>', f'<title>{new_title}</title>', head_html)
    updated_head = re.sub(r'<meta name="description" content=".*?" />', f'<meta name="description" content="{new_meta}" />', updated_head)
    
    # Add video schema if present
    if video_schema:
        # Remove any existing VideoObject schema first
        updated_head = re.sub(r'<script type="application/ld+json">.*?"VideoObject".*?</script>', '', updated_head, flags=re.DOTALL)
        # Insert new schema before closing head tag
        updated_head = updated_head.replace('</head>', f'{video_schema}</head>')
    
    # Add BreadcrumbList schema
    breadcrumb_schema = f'''<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{ "@type": "ListItem", "position": 1, "name": "Home", "item": "https://dawidmillenium-design.github.io/VideoCameraHoliday/" }},
    {{ "@type": "ListItem", "position": 2, "name": "City Through the Lens", "item": "https://dawidmillenium-design.github.io/VideoCameraHoliday/city-through-the-lens/" }},
    {{ "@type": "ListItem", "position": 3, "name": "{city_name}", "item": "https://dawidmillenium-design.github.io/VideoCameraHoliday/city-through-the-lens/{slug}.html" }}
  ]
}}
</script>'''
    updated_head = updated_head.replace('</head>', f'{breadcrumb_schema}</head>')
    
    # Reconstruct the full HTML
    new_html = f'''<!DOCTYPE html>
<html lang="en">
{updated_head}
<body>
{header_html}
{nav_html}
{new_content}
{footer_html}
</body>
</html>'''
    
    # Write the new file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_html)
    
    print(f"âœ… Regenerated: {city}")

print("\nðŸŽ‰ All city pages regenerated successfully!")
