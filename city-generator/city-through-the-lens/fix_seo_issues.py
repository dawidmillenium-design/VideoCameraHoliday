import os
import json
from datetime import datetime

# CONFIG
CITY_DIR = 'city-through-the-lens'
SITEMAP_FILE = 'sitemap.xml'
BASE_URL = 'https://dawidmillenium-design.github.io/VideoCameraHoliday'
TODAY = datetime.now().strftime('%Y-%m-%d')

# 1. INTERNAL LINKING STRATEGY (Contextual Links)
# These links will be injected into the Conclusion of every city page
INTERNAL_LINKS_HTML = """
<div class="seo-internal-links" style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #333;">
    <h4>📚 Related Guides for Your Trip</h4>
    <ul style="list-style: none; padding: 0;">
        <li>👉 <a href="/VideoCameraHoliday/guides/best-holiday-video-cameras-2026.html" style="color: #e94560; text-decoration: none;"><strong>Best Holiday Cameras 2026</strong> – Top picks for every budget.</a></li>
        <li>👉 <a href="/VideoCameraHoliday/how-to/gear-maintenance-field-cleaning.html" style="color: #e94560; text-decoration: none;"><strong>Gear Maintenance Guide</strong> – How to clean your camera after dusty trips.</a></li>
        <li>👉 <a href="/VideoCameraHoliday/city-through-the-lens/" style="color: #e94560; text-decoration: none;"><strong>Back to City Hub</strong> – See all 50 city filming guides.</a></li>
    </ul>
</div>
"""

# 2. FAQ SCHEMA GENERATOR
def generate_faq_schema(city_name, challenge, attraction1):
    questions = [
        {
            "question": f"What is the best camera for filming in {city_name}?",
            "answer": f"For {city_name}, we recommend a camera that handles {challenge.lower()}. Check our full review of the top travel cameras for 2026."
        },
        {
            "question": f"Do I need a permit to film at {attraction1}?",
            "answer": f"Permit rules for {attraction1} vary. In {city_name}, commercial shoots often require permission, while handheld personal vlogging is usually tolerated. Always check local regulations."
        },
        {
            "question": f"When is the best time to visit {city_name} for filming?",
            "answer": f"The best time depends on avoiding {challenge.lower()}. Generally, the dry season offers the most stable conditions for videography in {city_name}."
        }
    ]
    
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": []
    }
    
    for q in questions:
        schema["mainEntity"].append({
            "@type": "Question",
            "name": q["question"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": q["answer"]
            }
        })
    
    return json.dumps(schema, indent=2)

# PROCESS FILES
files_updated = 0
for filename in os.listdir(CITY_DIR):
    if not filename.endswith('.html') or filename == 'index.html' or filename == 'hub.html':
        continue
    
    filepath = os.path.join(CITY_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # FIX 1: Add Internal Links before </article>
    if '<div class="seo-internal-links"' not in content:
        content = content.replace('</article>', f'{INTERNAL_LINKS_HTML}\n</article>')
    
    # FIX 2: Add Last Updated Date near H1
    if 'Last Updated' not in content:
        date_badge = f'<p style="color: #666; font-size: 0.9rem; margin-top: -20px; margin-bottom: 20px;">📅 Last Updated: {TODAY}</p>'
        # Insert after H1
        import re
        content = re.sub(r'(</h1>)', r'\1' + date_badge, content, count=1)
    
    # FIX 3: Add FAQ Schema before closing </body>
    # Extract city name roughly from H1 for the schema
    h1_match = re.search(r'<h1>(.*?) Through the Lens</h1>', content)
    city_name = h1_match.group(1) if h1_match else "This City"
    
    # Simple extraction for challenge/attraction (fallback if regex fails)
    challenge = "local challenges"
    attraction1 = "major attractions"
    
    faq_schema = generate_faq_schema(city_name, challenge, attraction1)
    faq_script = f"\n<script type=\"application/ld+json\">\n{faq_schema}\n</script>\n"
    
    if '"@type": "FAQPage"' not in content:
        content = content.replace('</body>', f'{faq_script}</body>')
    
    # Save updates
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    files_updated += 1

print(f"✅ Updated {files_updated} city pages with internal links, dates, and FAQ schema.")

# FIX 4: UPDATE SITEMAP
if os.path.exists(SITEMAP_FILE):
    with open(SITEMAP_FILE, 'r', encoding='utf-8') as f:
        sitemap = f.read()
    
    new_entries = ""
    for filename in os.listdir(CITY_DIR):
        if filename.endswith('.html') and filename != 'index.html' and filename != 'hub.html':
            slug = filename.replace('.html', '')
            url = f"{BASE_URL}/city-through-the-lens/{slug}"
            entry = f"""  <url>
    <loc>{url}</loc>
    <lastmod>{TODAY}</lastmod>
    <priority>0.6</priority>
  </url>
"""
            if url not in sitemap:
                new_entries += entry
    
    if new_entries:
        sitemap = sitemap.replace('</urlset>', new_entries + '</urlset>')
        with open(SITEMAP_FILE, 'w', encoding='utf-8') as f:
            f.write(sitemap)
        print("✅ Sitemap.xml updated with new city URLs.")
    else:
        print("ℹ️ Sitemap already up to date.")
else:
    print("⚠️ sitemap.xml not found. Create one manually.")

print("\n🎉 SEO Fixes Complete! Commit these changes to boost your score.")