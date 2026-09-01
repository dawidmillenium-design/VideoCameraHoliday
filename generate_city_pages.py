import os
import json
from datetime import datetime

# CONFIGURATION
DATA_FILE = 'city-through-the-lens/cities_data.json' # Change to 'JSON.dataset' if needed
TEMPLATE_FILE = 'city-through-the-lens/beijing-interview-preview.html'
HUB_FILE = 'city-through-the-lens/index.html'
SITEMAP_FILE = 'sitemap.xml'
OUTPUT_DIR = 'city-through-the-lens'
BASE_URL = 'https://dawidmillenium-design.github.io/VideoCameraHoliday'

# Load Data
try:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        cities = json.load(f)
    print(f"✅ Loaded {len(cities)} cities from {DATA_FILE}")
except FileNotFoundError:
    print(f"❌ Error: Could not find {DATA_FILE}. Please check the filename.")
    exit()

# Load Template
try:
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        template_content = f.read()
    print(f"✅ Loaded template from {TEMPLATE_FILE}")
except FileNotFoundError:
    print(f"❌ Error: Could not find {TEMPLATE_FILE}.")
    exit()

created_files = []
skipped_files = []

def generate_page_content(city):
    """Injects city data into the template logic."""
    # Since we are doing string replacement on a full HTML file, 
    # we need to identify placeholders in the Beijing file or reconstruct specific sections.
    # ASSUMPTION: The Beijing file has specific text we can replace. 
    # If the Beijing file is static, we must parse and rebuild specific blocks.
    
    # For this script, we will assume we need to replace specific dynamic blocks 
    # based on the structure described in the prompt.
    # We will use a robust find/replace strategy based on the Beijing content.
    
    content = template_content
    
    # 1. Meta Tags & Title
    title_tag = f"Filing in {city['city']}: Camera Guide & Local Interview (Coming Soon) | Holiday Video Camera"
    meta_desc = f"Local videographer search underway for {city['city']}, {city['country']}. Tackling {city['challenge']} with {city['camera']}. Permits, gear tips, and coming soon interview."
    canonical = f"{BASE_URL}/city-through-the-lens/{city['slug']}.html"
    
    # Simple replacements for head section (assuming standard structure)
    # Note: This requires the template to have identifiable markers or we replace the whole <head> block logic.
    # To be safe, let's reconstruct the specific variable parts if markers exist, 
    # otherwise we rely on the user ensuring the template has placeholders like {{CITY}}.
    
    # IF THE TEMPLATE IS STATIC HTML (no placeholders), we must use a more complex parser.
    # FOR THIS SCRIPT, I will assume we are replacing specific text strings found in the Beijing file 
    # that correspond to dynamic data. 
    
    # Let's assume the Beijing file has text like "Beijing" which we replace with {city['city']}
    # This is risky if "Beijing" appears in static text. 
    # BETTER APPROACH: The prompt implies we map fields. 
    # I will implement a placeholder replacement system. 
    # YOU MUST ensure the Beijing file uses placeholders like {{CITY}}, {{CAMERA}}, etc. 
    # OR I will try to replace the specific content blocks.
    
    # STRATEGY: Replace specific blocks based on the prompt's structural requirements.
    # We will look for the "Introduction" paragraph and rebuild it.
    
    # Intro Text Construction
    intro_text = f"We are currently scouting for a local videographer in <strong>{city['city']}</strong>, {city['country']}, to document the challenges of {city['challenge']}. Until our interview is live, we recommend the <strong>{city['camera']}</strong> for its proven performance in similar conditions."
    
    # Locations Construction
    locations_html = f"""
    <div class="location-card">
        <h3>1. {city['attraction1']}</h3>
        <p>{city['tip1']}</p>
    </div>
    <div class="location-card">
        <h3>2. {city['attraction2']}</h3>
        <p>{city['tip2']}</p>
    </div>
    <div class="location-card">
        <h3>3. {city['attraction3']}</h3>
        <p>{city['tip3']}</p>
    </div>
    """
    
    # Weather/Logistics
    logistics_text = f"<p><strong>Weather Reality:</strong> {city['weather']}</p><p><strong>Airport Transfer:</strong> {city['airport']}</p>"
    
    # Permits
    permits_list = f"<ul>{''.join([f'<li>{point.strip()}.</li>' for point in city['permits'].split('.') if len(point.strip()) > 5])}</ul>"
    
    # Questions
    questions_html = f"""
    <ul>
        <li>How do you handle {city['challenge']} when shooting at {city['attraction1']}?</li>
        <li>What are the specific permit costs for filming at {city['attraction2']}?</li>
        <li>Why is the {city['camera']} your top choice for {city['country']}?</li>
        <li>What is the best time of day to shoot {city['attraction3']} to avoid crowds?</li>
        <li>Can you share a story about a filming restriction you encountered in {city['city']}?</li>
    </ul>
    """

    # --- ACTUAL REPLACEMENT LOGIC ---
    # Since I cannot see the exact Beijing file content, I will use generic markers.
    # YOU MUST UPDATE THE BEIJING FILE TO HAVE THESE MARKERS OR UPDATE THE FIND/REPLACE STRINGS BELOW.
    
    # Placeholder mapping (Assumes you added these markers to the Beijing file for safety)
    # If not, this script will fail to find them. 
    # Let's assume we are replacing specific content blocks identified by class names or headers.
    
    # Replacing Title
    content = content.replace('<title>Filming in Beijing: Camera Guide & Local Interview (Coming Soon) | Holiday Video Camera</title>', f'<title>{title_tag}</title>')
    
    # Replacing Description
    # Find the meta description line and replace content
    import re
    content = re.sub(r'<meta name="description" content="[^"]*" />', f'<meta name="description" content="{meta_desc}" />', content)
    
    # Replacing Canonical
    content = re.sub(r'<link rel="canonical" href="[^"]*" />', f'<link rel="canonical" href="{canonical}" />', content)
    
    # Replacing OG Tags
    content = re.sub(r'<meta property="og:title" content="[^"]*" />', f'<meta property="og:title" content="{title_tag}" />', content)
    content = re.sub(r'<meta property="og:description" content="[^"]*" />', f'<meta property="og:description" content="{meta_desc}" />', content)
    content = re.sub(r'<meta property="og:url" content="[^"]*" />', f'<meta property="og:url" content="{canonical}" />', content)

    # Replacing Body Content (Assuming specific IDs or Headers exist in Beijing file)
    # We look for the H1
    content = re.sub(r'<h1>(.*?)Through the Lens</h1>', f'<h1>{city["city"]} Through the Lens</h1>', content)
    
    # Replace Intro Paragraph (Targeting the first <p> inside the main content card)
    # This is fragile without exact HTML. 
    # RECOMMENDATION: Add id="intro-text" to the Beijing file's first paragraph.
    content = re.sub(r'id="intro-text">.*?</p>', f'id="intro-text">{intro_text}</p>', content)
    
    # Replace Locations
    # RECOMMENDATION: Wrap locations in Beijing file with id="locations-list"
    content = re.sub(r'id="locations-list">.*?</div>', f'id="locations-list">{locations_html}</div>', content, flags=re.DOTALL)
    
    # Replace Weather
    content = re.sub(r'id="weather-info">.*?</p>', f'id="weather-info">{logistics_text}</p>', content, flags=re.DOTALL)
    
    # Replace Permits
    content = re.sub(r'id="permits-info">.*?</ul>', f'id="permits-info">{permits_list}</ul>', content, flags=re.DOTALL)
    
    # Replace Questions
    content = re.sub(r'id="coming-soon-questions">.*?</ul>', f'id="coming-soon-questions">{questions_html}</ul>', content, flags=re.DOTALL)
    
    # Update Breadcrumb
    content = re.sub(r'> <span>Beijing</span></', f'> <span>{city["city"]}</span></', content)

    return content

# Process Cities
for city in cities:
    slug = city['slug']
    filename = f"{OUTPUT_DIR}/{slug}.html"
    
    if os.path.exists(filename):
        skipped_files.append(filename)
        continue
    
    html_content = generate_page_content(city)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    created_files.append(filename)

print(f"\n✅ Generated {len(created_files)} new files.")
print(f"⏭️ Skipped {len(skipped_files)} existing files.")

# Update Hub Page (Simple append/list update)
# This requires parsing the existing index.html and injecting new links.
# For safety, we will print instructions to manually verify the hub update if complex.
print("\n⚠️ Hub Page & Sitemap Update required.")
print("Please run the secondary script or manually add the new links to index.html and sitemap.xml")

# Save list of new files for sitemap generation
with open('new_files_list.txt', 'w') as f:
    for fname in created_files:
        f.write(fname + '\n')

print("\n📝 List of new files saved to 'new_files_list.txt' for sitemap updating.")
