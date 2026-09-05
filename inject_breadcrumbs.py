import os
import re
import json
import shutil
from pathlib import Path

# --- CONFIGURATION ---
TARGET_DIR = './city-through-the-lens'
BASE_URL = 'https://dawidmillenium-design.github.io/VideoCameraHoliday'
BACKUP_DIR = './city-through-the-lens-backup'

def get_city_name(filename):
    """Extracts a clean city name from the filename."""
    name = Path(filename).stem
    # Remove common suffixes like '-interview-preview'
    name = re.sub(r'-interview-preview$', '', name)
    # Replace hyphens with spaces and Title Case
    return name.replace('-', ' ').title()

def generate_breadcrumb_html(city_name):
    """Generates the semantic HTML breadcrumb."""
    return f"""
<nav class="breadcrumb" aria-label="Breadcrumb">
    <ol>
        <li><a href="{BASE_URL}/">Home</a></li>
        <li class="separator" aria-hidden="true">›</li>
        <li><a href="{BASE_URL}/city-through-the-lens/">City Series</a></li>
        <li class="separator" aria-hidden="true">›</li>
        <li aria-current="page">{city_name}</li>
    </ol>
</nav>
"""

def generate_json_ld(city_name, filename):
    """Generates the JSON-LD structured data."""
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": f"{BASE_URL}/"
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "City Series",
                "item": f"{BASE_URL}/city-through-the-lens/"
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": city_name,
                "item": f"{BASE_URL}/city-through-the-lens/{filename}"
            }
        ]
    }
    return f'<script type="application/ld+json">\n{json.dumps(data, indent=2)}\n</script>\n'

def main():
    target_path = Path(TARGET_DIR)
    
    if not target_path.exists():
        print(f"❌ Error: Directory '{TARGET_DIR}' not found. Please check the path.")
        return

    # 1. Create Backup
    if not Path(BACKUP_DIR).exists():
        print(f"📦 Creating backup of '{TARGET_DIR}' to '{BACKUP_DIR}'...")
        shutil.copytree(target_path, BACKUP_DIR)
    else:
        print("✅ Backup already exists. Skipping backup creation.")

    # 2. Process Files
    html_files = list(target_path.glob('*.html'))
    print(f"🔍 Found {len(html_files)} HTML files to process.")

    updated_count = 0
    for file_path in html_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip if already injected
        if 'class="breadcrumb"' in content and 'application/ld+json' in content:
            print(f"⏭️  Skipped {file_path.name} (Already contains breadcrumbs).")
            continue

        city_name = get_city_name(file_path.name)
        
        # Inject HTML before <main>
        breadcrumb_html = generate_breadcrumb_html(city_name)
        content = content.replace('<main', f'{breadcrumb_html}<main')

        # Inject JSON-LD before </head>
        json_ld = generate_json_ld(city_name, file_path.name)
        content = content.replace('</head>', f'{json_ld}</head>')

        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✅ Successfully updated: {file_path.name} ({city_name})")
        updated_count += 1

    print(f"\n Done! Successfully updated {updated_count} files.")

if __name__ == "__main__":
    main()