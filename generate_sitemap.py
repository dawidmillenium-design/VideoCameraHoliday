import os
from datetime import date

# Config
folder = '/workspace'
base_url = "https://dawidmillenium-design.github.io/VideoCameraHoliday/"
today = date.today().isoformat()

urls = []

# Scan for all HTML files recursively
for root, dirs, files in os.walk(folder):
    # Skip hidden directories and common non-content folders
    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]
    
    for f in files:
        if f.endswith('.html'):
            # Get the full path and convert to relative path from /workspace
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, folder)
            # Convert to URL path (forward slashes)
            url_path = rel_path.replace(os.sep, '/')
            # Build the full URL
            urls.append(f"  <url>\n    <loc>{base_url}{url_path}</loc>\n    <lastmod>{today}</lastmod>\n    <priority>0.6</priority>\n  </url>")

# Create XML content
sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>
"""

# Save to root
with open('/workspace/sitemap.xml', 'w', encoding='utf-8') as f:
    f.write(sitemap_content)

print("✅ sitemap.xml created in root folder!")
print(f"📄 Included {len(urls)} HTML pages.")
