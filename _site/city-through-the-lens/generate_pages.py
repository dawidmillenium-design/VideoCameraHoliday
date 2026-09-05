import os
import json
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
OUTPUT_DIR = 'city-through-the-lens'
TEMPLATE_FILE = 'beijing-interview-preview.html' # Ensure this file is in the SAME folder as the script
SITEMAP_FILE = '../sitemap.xml' # Adjust path if needed
HUB_FILE = 'index.html' # Assumes script runs inside city-through-the-lens or adjusts path below

# If running from 'city-generator', output should be sibling or specific path
# Let's assume standard structure: root/city-through-the-lens/
# If script is in root/city-generator/, adjust OUTPUT_DIR to '../city-through-the-lens'
if not os.path.exists(OUTPUT_DIR):
    # Try parent directory if not found in current
    if os.path.exists(f'../{OUTPUT_DIR}'):
        OUTPUT_DIR = f'../{OUTPUT_DIR}'
        TEMPLATE_FILE = f'../{OUTPUT_DIR}/beijing-interview-preview.html'
        HUB_FILE = f'../{OUTPUT_DIR}/index.html'
        SITEMAP_FILE = '../sitemap.xml'
    else:
        # Create if nowhere to be found (might break paths, but ensures run)
        os.makedirs(OUTPUT_DIR)

# ==========================================
# HARDCODED DATA (Fixes the missing key error)
# ==========================================
cities_data = [
    {"city": "Bangalore", "country": "India", "camera": "Sony A7IV", "challenge": "Traffic & Dust", "attraction1": "Cubbon Park", "tip1": "Shoot early morning (6 AM) to avoid traffic haze. Use a polarizer.", "attraction2": "Bangalore Palace", "tip2": "Tripods require written permission.", "attraction3": "MG Road Metro", "tip3": "Great for night timelapses.", "weather": "Pleasant year-round. Monsoon June-Sept.", "airport": "Kempegowda (BLR). 45 mins by Uber.", "permits": "Public filming OK. Commercial needs permit.", "slug": "bangalore-interview-preview"},
    {"city": "Chennai", "country": "India", "camera": "Fujifilm X-T5", "challenge": "Extreme Humidity", "attraction1": "Marina Beach", "tip1": "Watch out for salt spray.", "attraction2": "Kapaleeshwarar Temple", "tip2": "No photography inside sanctum.", "attraction3": "Fort St. George", "tip3": "Best light at golden hour.", "weather": "Hot/Humid. Best Oct-Dec.", "airport": "Chennai (MAA). Metro connected.", "permits": "Strict rules on beaches/temples.", "slug": "chennai-interview-preview"},
    {"city": "Hyderabad", "country": "India", "camera": "Canon R6 Mark II", "challenge": "Crowds & Low Light", "attraction1": "Charminar", "tip1": "Shoot from Laad Bazaar balconies.", "attraction2": "Golconda Fort", "tip2": "Arrive early for sunset.", "attraction3": "Ramoji Film City", "tip3": "Requires entry ticket.", "weather": "Hot summers. Pleasant winters.", "airport": "Rajiv Gandhi (HYD). 45 mins.", "permits": "ASI permission needed for Charminar.", "slug": "hyderabad-interview-preview"},
    {"city": "Ahmedabad", "country": "India", "camera": "Nikon Z8", "challenge": "Heat & Heritage Rules", "attraction1": "Sabarmati Ashram", "tip1": "Quiet filming only. No tripods inside.", "attraction2": "Adalaj Stepwell", "tip2": "Best shadows at noon.", "attraction3": "Kankaria Lake", "tip3": "High ISO needed at night.", "weather": "Very hot Mar-Jun. Pleasant Nov-Feb.", "airport": "Sardar Vallabhbhai (AMD). 20 mins.", "permits": "Heritage sites strictly regulated.", "slug": "ahmedabad-interview-preview"},
    {"city": "Manila", "country": "Philippines", "camera": "DJI Osmo Pocket 3", "challenge": "Security & Traffic", "attraction1": "Intramuros", "tip1": "Horse carriages make great B-roll.", "attraction2": "Rizal Park", "tip2": "Guards strict about tripods.", "attraction3": "Binondo", "tip3": "Handheld walking shots best.", "weather": "Tropical. Dry season Nov-May.", "airport": "Ninoy Aquino (MNL). 30-60 mins.", "permits": "Permits required for Intramuros.", "slug": "manila-interview-preview"},
    {"city": "Jakarta", "country": "Indonesia", "camera": "Sony ZV-E1", "challenge": "Humidity & Permits", "attraction1": "Kota Tua", "tip1": "Watch for pickpockets.", "attraction2": "Monas", "tip2": "Great wide shots from park.", "attraction3": "Glodok", "tip3": "Low light challenges indoors.", "weather": "Hot/Humid. Rainy Oct-April.", "airport": "Soekarno-Hatta (CGK). Train fastest.", "permits": "Ministry of Tourism permit needed.", "slug": "jakarta-interview-preview"},
    {"city": "Bangkok", "country": "Thailand", "camera": "Panasonic GH6", "challenge": "Heat & Temple Etiquette", "attraction1": "Wat Arun", "tip1": "Best shot from across river.", "attraction2": "Grand Palace", "tip2": "Tripods banned inside.", "attraction3": "Khao San Road", "tip3": "High ISO essential.", "weather": "Cool season Nov-Feb best.", "airport": "Suvarnabhumi (BKK). Rail Link.", "permits": "Ask monks before filming.", "slug": "bangkok-interview-preview"},
    {"city": "Ho Chi Minh City", "country": "Vietnam", "camera": "Insta360 X4", "challenge": "Motorbike Chaos", "attraction1": "Ben Thanh Market", "tip1": "Negotiate before filming.", "attraction2": "War Remnants Museum", "tip2": "Flash banned. Respectful tone.", "attraction3": "Notre Dame", "tip3": "Street view best.", "weather": "Dry season Dec-Apr best.", "airport": "Tan Son Nhat (SGN). 20 mins.", "permits": "Police may delete unauthorized footage.", "slug": "ho-chi-minh-interview-preview"},
    {"city": "Cairo", "country": "Egypt", "camera": "Canon EOS R5", "challenge": "Sand & Harassment", "attraction1": "Pyramids", "tip1": "Go early to avoid buses.", "attraction2": "Khan el-Khalili", "tip2": "Small tip often required.", "attraction3": "Citadel", "tip3": "Best at sunset.", "weather": "Very hot May-Sept.", "airport": "Cairo (CAI). Uber recommended.", "permits": "Police escort often required.", "slug": "cairo-interview-preview"},
    {"city": "Istanbul", "country": "Turkey", "camera": "Sony A7S III", "challenge": "Crowds & Mixed Lighting", "attraction1": "Hagia Sophia", "tip1": "Respect prayer times.", "attraction2": "Blue Mosque", "tip2": "Closed during prayer.", "attraction3": "Grand Bazaar", "tip3": "Atmospheric low light.", "weather": "Spring/Autumn best.", "airport": "Istanbul (IST). Metro M11.", "permits": "Mosque filming restricted.", "slug": "istanbul-interview-preview"},
    {"city": "Tehran", "country": "Iran", "camera": "Fujifilm X-H2S", "challenge": "Political Sensitivity", "attraction1": "Golestan Palace", "tip1": "Tripods allowed with permit.", "attraction2": "Azadi Tower", "tip2": "Best from park base.", "attraction3": "Grand Bazaar", "tip3": "Ask before filming faces.", "weather": "Hot summers, cold winters.", "airport": "Imam Khomeini (IKA). Private transfer.", "permits": "Government approval mandatory.", "slug": "tehran-interview-preview"},
    {"city": "Riyadh", "country": "Saudi Arabia", "camera": "DJI Action 4", "challenge": "Extreme Heat", "attraction1": "Diriyah", "tip1": "Open late for cool shoots.", "attraction2": "Kingdom Centre", "tip2": "Mall approval needed.", "attraction3": "Al-Bujairi", "tip3": "Good for lifestyle.", "weather": "Extremely hot summer.", "airport": "King Khalid (RUH). 30 mins.", "permits": "Filming women without consent illegal.", "slug": "riyadh-interview-preview"},
    {"city": "Baghdad", "country": "Iraq", "camera": "Canon C70", "challenge": "Security", "attraction1": "National Museum", "tip1": "Permission essential.", "attraction2": "Al-Mustansiriya", "tip2": "Architecture focus.", "attraction3": "Tigris Corniche", "tip3": "Be discreet.", "weather": "Scorching summer.", "airport": "Baghdad (BGW). Pre-arranged transport.", "permits": "Government minders required.", "slug": "baghdad-interview-preview"},
    {"city": "Moscow", "country": "Russia", "camera": "Sony FX3", "challenge": "Cold & Bureaucracy", "attraction1": "Red Square", "tip1": "Tripods banned without pass.", "attraction2": "Metro", "tip2": "No tripods rush hour.", "attraction3": "Gorky Park", "tip3": "Winter sports footage.", "weather": "Harsh winter.", "airport": "Sheremetyevo (SVO). Aeroexpress.", "permits": "FSB approval for Red Square.", "slug": "moscow-interview-preview"},
    {"city": "Paris", "country": "France", "camera": "Leica Q3", "challenge": "Permits & Crowds", "attraction1": "Eiffel Tower", "tip1": "Night lights copyrighted.", "attraction2": "Louvre", "tip2": "Early morning essential.", "attraction3": "Montmartre", "tip3": "Street artists everywhere.", "weather": "Spring/Autumn best.", "airport": "CDG. RER B train.", "permits": "APIE permit for rigs.", "slug": "paris-interview-preview"},
    {"city": "London", "country": "UK", "camera": "Blackmagic 6K", "challenge": "Rain & Royal Restrictions", "attraction1": "Tower Bridge", "tip1": "South Bank best exterior.", "attraction2": "Westminster Abbey", "tip2": "No filming inside.", "attraction3": "Camden Market", "tip3": "Great street style.", "weather": "Unpredictable rain.", "airport": "Heathrow. Tube/Train.", "permits": "Mayor's permit for tripods.", "slug": "london-interview-preview"},
    {"city": "Kinshasa", "country": "DR Congo", "camera": "Canon R3", "challenge": "Power & Stability", "attraction1": "Congo River", "tip1": "Pirogues great subjects.", "attraction2": "Marché Central", "tip2": "Ask before filming.", "attraction3": "Académie Beaux-Arts", "tip3": "Vibrant murals.", "weather": "Heavy rain Nov-Mar.", "airport": "N'djili (FIH). Pre-arranged pickup.", "permits": "Gov authorization required.", "slug": "kinshasa-interview-preview"},
    {"city": "Lagos", "country": "Nigeria", "camera": "Sony A1", "challenge": "Traffic & Heat", "attraction1": "Lekki Centre", "tip1": "Canopy walkway.", "attraction2": "Nike Art Gallery", "tip2": "5 floors of art.", "attraction3": "Tarkwa Bay", "tip3": "Accessible by boat.", "weather": "Rainy Apr-Oct.", "airport": "Murtala Muhammed (LOS). Traffic heavy.", "permits": "State permit needed.", "slug": "lagos-interview-preview"},
    {"city": "Luanda", "country": "Angola", "camera": "Panasonic S5II", "challenge": "Cost & Access", "attraction1": "Marginal", "tip1": "Sunset walks.", "attraction2": "Fortaleza", "tip2": "Panoramic views.", "attraction3": "Ilha do Cabo", "tip3": "Vibrant nightlife.", "weather": "Dry May-Oct.", "airport": "Quatro de Fevereiro (LAD). Expensive taxis.", "permits": "Registration required.", "slug": "luanda-interview-preview"},
    {"city": "São Paulo", "country": "Brazil", "camera": "RED Komodo", "challenge": "Security & Scale", "attraction1": "Paulista Ave", "tip1": "Sunday closure great.", "attraction2": "Mercado Municipal", "tip2": "Low light interior.", "attraction3": "Beco do Batman", "tip3": "No flash.", "weather": "Rain common.", "airport": "Guarulhos (GRU). 45-60 mins.", "permits": "SP Cine facilitates.", "slug": "sao-paulo-interview-preview"},
    {"city": "Mexico City", "country": "Mexico", "camera": "Arri Alexa Mini", "challenge": "Altitude", "attraction1": "Zócalo", "tip1": "Flag ceremony daily.", "attraction2": "Chapultepec", "tip2": "Castle on hill.", "attraction3": "Xochimilco", "tip3": "Colorful boats.", "weather": "Mild year-round.", "airport": "Benito Juárez (MEX). 30 mins.", "permits": "IMCINE issues permits.", "slug": "mexico-city-interview-preview"},
    {"city": "Buenos Aires", "country": "Argentina", "camera": "Sony Venice", "challenge": "Late Nights", "attraction1": "La Boca", "tip1": "Colorful houses.", "attraction2": "Recoleta Cemetery", "tip2": "Respectful filming.", "attraction3": "Puerto Madero", "tip3": "Sleek modern look.", "weather": "Four seasons.", "airport": "Ezeiza (EZE). 45-60 mins.", "permits": "GCBA office friendly.", "slug": "buenos-aires-interview-preview"},
    {"city": "Rio de Janeiro", "country": "Brazil", "camera": "GoPro Hero 12", "challenge": "Safety", "attraction1": "Christ Redeemer", "tip1": "Go early for clouds.", "attraction2": "Sugarloaf", "tip2": "Sunset spectacular.", "attraction3": "Copacabana", "tip3": "Hide gear.", "weather": "Hot year-round.", "airport": "Galeão (GIG).", "permits": "Favela guide mandatory.", "slug": "rio-de-janeiro-interview-preview"},
    {"city": "Bogotá", "country": "Colombia", "camera": "Canon C300 III", "challenge": "Altitude & Rain", "attraction1": "La Candelaria", "tip1": "Cobblestones.", "attraction2": "Monserrate", "tip2": "Cable car up.", "attraction3": "Gold Museum", "tip3": "No photos inside.", "weather": "Rainy afternoons.", "airport": "El Dorado (BOG). 40 mins.", "permits": "Ministry Culture permits.", "slug": "bogota-interview-preview"},
    {"city": "Lima", "country": "Peru", "camera": "Panasonic Varicam", "challenge": "Fog", "attraction1": "Historic Centre", "tip1": "Colonial balconies.", "attraction2": "Miraflores", "tip2": "Paragliders.", "attraction3": "Huaca Pucllana", "tip3": "Night illumination.", "weather": "Foggy winter.", "airport": "Jorge Chávez (LIM). 45 mins.", "permits": "Municipal permits.", "slug": "lima-interview-preview"},
    {"city": "Santiago", "country": "Chile", "camera": "Fujifilm GFX 100", "challenge": "Smog", "attraction1": "Plaza de Armas", "tip1": "Bustling life.", "attraction2": "San Cristóbal", "tip2": "Andes backdrop.", "attraction3": "Lastarria", "tip3": "European feel.", "weather": "Dry summers.", "airport": "Arturo Merino (SCL). 35 mins.", "permits": "ChileFilm bureau.", "slug": "santiago-interview-preview"}
]

# ==========================================
# LOAD TEMPLATE
# ==========================================
try:
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        template_content = f.read()
    print(f"📄 Loaded template: {TEMPLATE_FILE}")
except FileNotFoundError:
    print(f"❌ Error: Could not find {TEMPLATE_FILE}. Please ensure Beijing file is in the same folder.")
    exit()

created_files = []
skipped_files = []

# ==========================================
# GENERATION LOGIC
# ==========================================
def generate_page_content(city):
    title_tag = f"Filming in {city['city']}: Camera Guide & Local Interview (Coming Soon) | Holiday Video Camera"
    meta_desc = f"{city['challenge']} in {city['country']}. Local videographer search, camera tips, permits & interview coming soon."
    if len(meta_desc) > 160:
        meta_desc = meta_desc[:157] + "..."
    
    canonical = f"https://dawidmillenium-design.github.io/VideoCameraHoliday/city-through-the-lens/{city['slug']}.html"
    
    intro_text = f"We are currently scouting for a local videographer in <strong>{city['city']}</strong>, {city['country']}, to document the challenges of {city['challenge']}. Until our interview is live, we recommend the <strong>{city['camera']}</strong> for its proven performance in similar conditions."
    
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
    
    logistics_text = f"<p><strong>Weather Reality:</strong> {city['weather']}</p><p><strong>Airport Transfer:</strong> {city['airport']}</p>"
    
    permit_points = [p.strip() for p in city['permits'].split('.') if p.strip()]
    permits_html = "<ul>" + "".join([f"<li>{point.strip()}</li>" for point in permit_points if len(point.strip()) > 0]) + "</ul>"
    
    questions_html = f"""
    <ul>
        <li>How do you handle {city['challenge']} when shooting at {city['attraction1']}?</li>
        <li>What are the specific permit costs for filming at {city['attraction2']}?</li>
        <li>Why is the {city['camera']} your top choice for {city['country']}?</li>
        <li>What is the best time of day to shoot {city['attraction3']} to avoid crowds?</li>
        <li>Can you share a story about a filming restriction you encountered in {city['city']}?</li>
    </ul>
    """
    
    content = template_content
    # Replacements
    content = content.replace('<title>Filming in Beijing: Camera Guide & Local Interview (Coming Soon) | Holiday Video Camera</title>', f'<title>{title_tag}</title>')
    content = content.replace('Filming in Beijing: Camera Guide & Local Interview (Coming Soon)', title_tag.split('|')[0].strip())
    content = content.replace('Beijing Through the Lens', f"{city['city']} Through the Lens")
    content = content.replace('> <span>Beijing</span></', f'> <span>{city["city"]}</span></')
    
    import re
    content = re.sub(r'<meta name="description" content="[^"]*" />', f'<meta name="description" content="{meta_desc}" />', content)
    content = re.sub(r'<link rel="canonical" href="[^"]*" />', f'<link rel="canonical" href="{canonical}" />', content)
    content = re.sub(r'<meta property="og:title" content="[^"]*" />', f'<meta property="og:title" content="{title_tag}" />', content)
    content = re.sub(r'<meta property="og:description" content="[^"]*" />', f'<meta property="og:description" content="{meta_desc}" />', content)
    content = re.sub(r'<meta property="og:url" content="[^"]*" />', f'<meta property="og:url" content="{canonical}" />', content)
    
    # Content injection (Fallback safe)
    if 'id="intro-text"' in content:
        content = re.sub(r'id="intro-text">.*?</p>', f'id="intro-text">{intro_text}</p>', content, flags=re.DOTALL)
    if 'id="locations-list"' in content:
        content = re.sub(r'id="locations-list">.*?</div>', f'id="locations-list">{locations_html}</div>', content, flags=re.DOTALL)
    if 'id="weather-info"' in content:
        content = re.sub(r'id="weather-info">.*?</p>', f'id="weather-info">{logistics_text}</p>', content, flags=re.DOTALL)
    if 'id="permits-info"' in content:
        content = re.sub(r'id="permits-info">.*?</ul>', f'id="permits-info">{permits_html}</ul>', content, flags=re.DOTALL)
    if 'id="coming-soon-questions"' in content:
        content = re.sub(r'id="coming-soon-questions">.*?</ul>', f'id="coming-soon-questions">{questions_html}</ul>', content, flags=re.DOTALL)
    
    return content

# Ensure output dir exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

for city in cities_data:
    slug = city['slug']
    filename = f"{OUTPUT_DIR}/{slug}.html"
    
    if os.path.exists(filename):
        skipped_files.append(filename)
        continue
    
    html_content = generate_page_content(city)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    created_files.append(filename)

print(f"✅ Created {len(created_files)} files.")
print(f"⏭️ Skipped {len(skipped_files)} existing files.")

# ==========================================
# UPDATE HUB
# ==========================================
HUB_PATH = os.path.join(OUTPUT_DIR, 'index.html')
if os.path.exists(HUB_PATH):
    with open(HUB_PATH, 'r', encoding='utf-8') as f:
        hub_content = f.read()

    countries = {}
    for city in cities_data:
        country = city['country']
        if country not in countries:
            countries[country] = []
        countries[country].append(city)

    country_sections = ""
    for country, city_list in countries.items():
        country_sections += f'<h2>{country}</h2>\n<div class="city-grid">\n'
        for city in city_list:
            country_sections += f'  <a href="{city["slug"]}.html" class="city-card"><h3>{city["city"]}</h3><p>{city["challenge"]}</p></a>\n'
        country_sections += '</div>\n'

    if '<main class="hub-content">' in hub_content:
        hub_content = hub_content.replace('<main class="hub-content">', f'<main class="hub-content">\n{country_sections}')
    elif '</main>' in hub_content:
        hub_content = hub_content.replace('</main>', f'{country_sections}</main>')
    
    with open(HUB_PATH, 'w', encoding='utf-8') as f:
        f.write(hub_content)
    print("✅ Hub page updated.")
else:
    print(f"⚠️ Hub file not found at {HUB_PATH}. Skipping.")

# ==========================================
# UPDATE SITEMAP
# ==========================================
# Try to find sitemap in parent or root
sitemap_paths = [SITEMAP_FILE, '../sitemap.xml', '../../sitemap.xml']
sitemap_found = None
for sp in sitemap_paths:
    if os.path.exists(sp):
        sitemap_found = sp
        break

if sitemap_found:
    today = datetime.now().strftime('%Y-%m-%d')
    with open(sitemap_found, 'r', encoding='utf-8') as f:
        sitemap_content = f.read()

    entries = ""
    for filename in created_files:
        slug = os.path.basename(filename).replace('.html', '')
        # Construct URL carefully based on where script ran
        entries += f"""  <url>
    <loc>https://dawidmillenium-design.github.io/VideoCameraHoliday/city-through-the-lens/{slug}.html</loc>
    <lastmod>{today}</lastmod>
    <priority>0.6</priority>
  </url>
"""
    sitemap_content = sitemap_content.replace('</urlset>', entries + '</urlset>')
    with open(sitemap_found, 'w', encoding='utf-8') as f:
        f.write(sitemap_content)
    print(f"✅ Sitemap updated at {sitemap_found}.")
else:
    print("⚠️ Sitemap.xml not found. Skipping update.")

print("\n🎉 COMPLETE! Check the generated files in the folder.")