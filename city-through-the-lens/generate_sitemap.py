import os
from datetime import date

# Config
folder = '.'
base_url = "https://dawidmillenium-design.github.io/VideoCameraHoliday/city-through-the-lens/"
today = date.today().isoformat()

urls = []

# Scan for HTML files
for f in os.listdir(folder):
    if f.endswith('.html') and 'index' not in f:
        slug = f.replace('.html', '')
        urls.append(f"  <url>\n    <loc>{base_url}{slug}.html</loc>\n    <lastmod>{today}</lastmod>\n    <priority>0.6</priority>\n  </url>")

# Create XML content
sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>
"""

# Save to root (go up one level from city-through-the-lens)
output_path = '../sitemap.xml'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(sitemap_content)

print("✅ sitemap.xml created in root folder!")
print(f"📄 Included {len(urls)} city pages.")
