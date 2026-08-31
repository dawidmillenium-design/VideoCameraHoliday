import os
import re

# CONFIGURATION
# Change this to '.' to look in the CURRENT folder (city-generator)
# Or change to '../city-through-the-lens' if you move the HTML files there later
CITY_DIR = '.'

# Map slugs to specific Unsplash/LoremFlickr keywords for better relevance
city_keywords = {
    "tokyo": "tokyo,street,night",
    "shanghai": "shanghai,bund,skyline",
    "beijing": "forbidden,city,architecture",
    "osaka": "osaka,dotonbori,street",
    "chongqing": "chongqing,cyberpunk,city",
    "seoul": "seoul,gyeongbokgung,palace",
    "mumbai": "mumbai,gateway,india",
    "delhi": "delhi,red,fort",
    "dhaka": "dhaka,rickshaw,street",
    "karachi": "karachi,seaside,clifton",
    "kolkata": "kolkata,howrah,bridge",
    "lahore": "lahore,badshahi,mosque",
    "bangalore": "bangalore,cubbon,park",
    "chennai": "chennai,marina,beach",
    "hyderabad": "hyderabad,charminar",
    "ahmedabad": "ahmedabad,sabarmati,ashram",
    "manila": "manila,intramuros,walls",
    "jakarta": "jakarta,kota,tua",
    "bangkok": "bangkok,wat,arun",
    "ho-chi-minh": "saigon,notre,dame",
    "cairo": "giza,pyramids,desert",
    "istanbul": "istanbul,hagia,sophia",
    "tehran": "tehran,azadi,tower",
    "riyadh": "riyadh,diriyah,ruins",
    "baghdad": "baghdad,tigris,river",
    "moscow": "moscow,red,square",
    "paris": "paris,eiffel,tower",
    "london": "london,tower,bridge",
    "kinshasa": "kinshasa,congo,river",
    "lagos": "lagos,lekki,bridge",
    "luanda": "luanda,marginal,waterfront",
    "sao-paulo": "sao,paulo,paulista",
    "mexico-city": "mexico,city,zocalo",
    "buenos-aires": "buenos,aires,boca",
    "rio-de-janeiro": "rio,christ,redeemer",
    "bogota": "bogota,candelaria,streets",
    "lima": "lima,miraflores,cliffs",
    "santiago": "santiago,san,cristobal"
}

def get_image_url(slug, topic):
    """Generates a dynamic image URL using LoremFlickr (stable for demos)"""
    keyword = city_keywords.get(slug, f"{slug},city,travel")
    # Add a lock hash based on slug so the image doesn't change on every reload
    lock_id = abs(hash(slug)) % 10000 
    return f"https://loremflickr.com/800/450/{keyword}?lock={lock_id}"

def add_images_to_file(filepath, slug):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if images already exist to avoid duplicates
    if '<img src=' in content and 'loremflickr' in content.lower():
        return False

    # Format city name for alt text (e.g., "ho-chi-minh" -> "Ho Chi Minh")
    city_name = slug.replace('-', ' ').title()
    
    # 1. Hero Image URL
    hero_url = get_image_url(slug, "city,street,atmosphere")
    hero_img = f"""
    <div class="hero-image-container" style="margin: 20px 0; border-radius: 8px; overflow: hidden; border: 1px solid #333;">
        <img src="{hero_url}" alt="Cinematic street view of {city_name} showing local atmosphere and lighting conditions for videographers" width="800" height="450" style="width: 100%; height: auto; display: block;" loading="eager">
        <p style="font-size: 0.8rem; color: #888; margin: 10px 0 0 0; text-align: center;"><em>Figure 1: Typical filming environment in {city_name}.</em></p>
    </div>
    """

    # 2. Gear/Action Image URL
    gear_url = get_image_url(slug, "camera,filming,gear")
    gear_img = f"""
    <div class="content-image" style="margin: 20px 0; float: right; width: 300px; margin-left: 20px; background: #1a1a2e; padding: 10px; border-radius: 4px;">
        <img src="{gear_url}" alt="Videographer holding camera stabilizer in {city_name}" width="300" height="200" style="width: 100%; height: auto; border-radius: 4px;" loading="lazy">
        <p style="font-size: 0.75rem; color: #888; margin-top: 5px;"><em>Local videographers often use gimbals here.</em></p>
    </div>
    """

    # 3. Location Detail Image URL
    loc_url = get_image_url(slug, "landmark,architecture,travel")
    loc_img = f"""
    <div class="content-image" style="margin: 20px 0; clear: both; border-radius: 8px; overflow: hidden; border: 1px solid #333;">
        <img src="{loc_url}" alt="Iconic landmark in {city_name} popular for travel vlogs" width="800" height="450" style="width: 100%; height: auto; display: block;" loading="lazy">
        <p style="font-size: 0.75rem; color: #888; margin: 10px 0 0 0; text-align: center;"><em>One of the top locations mentioned in our interview prep.</em></p>
    </div>
    """

    # --- INJECTION LOGIC ---
    
    # 1. Inject Hero after </h1>
    # We look for the main H1 tag
    content = re.sub(r'(</h1>)', r'\1\n' + hero_img, content, count=1)
    
    # 2. Inject Gear Image after first <h2> (usually "Key Takeaways" or "Introduction")
    # We try to find the first H2 in the main content area
    match_h2 = re.search(r'<h2>(.*?)</h2>', content)
    if match_h2:
        # Insert after the closing tag of the first H2 found
        insert_pos = match_h2.end()
        content = content[:insert_pos] + '\n' + gear_img + content[insert_pos:]
    
    # 3. Inject Location Image before "Conclusion" H2
    # Look for <h2>Conclusion</h2> specifically
    content = re.sub(r'(<h2>Conclusion</h2>)', loc_img + r'\n\1', content, count=1)

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

# EXECUTION
print("🚀 Starting Image Injection in current folder...")

files_updated = 0
files_skipped = 0

# Iterate all HTML files in the CURRENT directory
for filename in os.listdir(CITY_DIR):
    # Only process city preview files (exclude index, hub, etc.)
    if filename.endswith('.html') and 'interview-preview' in filename:
        filepath = os.path.join(CITY_DIR, filename)
        
        # Extract slug: "tokyo-interview-preview.html" -> "tokyo"
        slug = filename.replace('-interview-preview.html', '')
        
        success = add_images_to_file(filepath, slug)
        
        if success:
            print(f"✅ Added images to {filename}")
            files_updated += 1
        else:
            print(f"⏭️ Skipped {filename} (Images already present)")
            files_skipped += 1

print(f"\n🎉 Done! Updated {files_updated} files. Skipped {files_skipped}.")
print("💡 Tip: Commit these changes. The images will load dynamically from LoremFlickr.")