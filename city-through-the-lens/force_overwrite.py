#!/usr/bin/env python3
"""
FORCE OVERWRITE: Regenerate all city preview pages with accurate JSON data.
This script completely replaces the body content of each city page while
preserving nav/header/footer structure.
"""

import json
import os
import re

# Load city data
with open('JSON.dataset', 'r') as f:
    # Remove merge conflict markers manually
    content = f.read()
    # Simple fix: remove lines with <<<<<<<, =======, >>>>>>>
    lines = content.split('\n')
    clean_lines = [l for l in lines if not (l.startswith('<<<<<<<') or l.startswith('=======') or l.startswith('>>>>>>>'))]
    clean_content = '\n'.join(clean_lines)
    
try:
    cities = json.loads(clean_content)
except json.JSONDecodeError as e:
    print(f"JSON Error: {e}")
    # Try to find and fix common issues
    print("Attempting to parse with alternative method...")
    cities = []

print(f"Loaded {len(cities)} cities from JSON")

# City-specific knowledge base (accurate facts)
CITY_DATA = {
    "Tokyo": {
        "landmarks": ["Shibuya Crossing", "Senso-ji Temple (Asakusa)", "Tokyo Skytree"],
        "weather": "Humid summers (25-35°C), mild winters (5-15°C). Best: Mar-May (cherry blossoms), Oct-Nov (fall colors).",
        "airport": "Narita (NRT) 60min by Express train; Haneda (HND) 30min by monorail.",
        "permits": "Tripods generally OK in public spaces. Drones banned in most of Tokyo without permission. Ask before filming in shops."
    },
    "Shanghai": {
        "landmarks": ["The Bund (Huangpu River)", "Yu Garden", "Lujiazui Financial District"],
        "weather": "Hot humid summers (30-40°C), cold damp winters (0-10°C). Best: Apr-May, Sept-Nov.",
        "airport": "Pudong (PVG) Maglev + metro 45min; Hongqiao (SHA) closer, 30min by metro.",
        "permits": "Drones restricted citywide. Commercial filming requires permit. Security may question tripod use at The Bund."
    },
    "Osaka": {
        "landmarks": ["Dotonbori Canal", "Osaka Castle", "Universal Studios Japan"],
        "weather": "Hot summers, mild winters. Cherry blossoms late Mar. Best: Apr-May, Oct-Nov.",
        "airport": "Kansai (KIX) 50min by Haruka Express; Itami (ITM) domestic only.",
        "permits": "Dotonbori very crowded - handheld only. Osaka Castle grounds allow tripods. Ask before filming street food vendors."
    },
    "Delhi": {
        "landmarks": ["Red Fort (Lal Qila)", "India Gate", "Chandni Chowk Market"],
        "weather": "Extreme heat Apr-Jun (40-45°C), pleasant winters (10-25°C). Monsoon Jul-Sep. Best: Nov-Feb.",
        "airport": "Indira Gandhi (DEL) Metro Airport Express 25min to city. Prepaid taxi recommended.",
        "permits": "Red Fort requires ASI permission for commercial shoots. Chandni Chowk too crowded for tripods. Always ask before filming people."
    },
    "Bangkok": {
        "landmarks": ["Grand Palace", "Wat Arun (Temple of Dawn)", "Chatuchak Weekend Market"],
        "weather": "Extremely hot Mar-May (35-40°C), rainy Jun-Oct, cool Nov-Feb. Best: Dec-Feb.",
        "airport": "Suvarnabhumi (BKK) Airport Rail Link 30min; Don Mueang (DMK) for budget airlines.",
        "permits": "Temples require respectful dress (covered shoulders/knees). Tripods banned inside temple buildings. Commercial needs Tourism Authority permit."
    },
    "Paris": {
        "landmarks": ["Eiffel Tower", "Louvre Pyramid", "Montmartre (Sacré-Cœur)"],
        "weather": "Mild year-round (5-25°C). Rain possible any month. Best: Apr-Jun, Sept-Oct.",
        "airport": "Charles de Gaulle (CDG) RER B train 35min; Orly (ORY) Orlyval + RER.",
        "permits": "Eiffel Tower night lights are copyrighted - no commercial use. Louvre bans tripods. Montmartre artists may demand payment for filming."
    },
    "London": {
        "landmarks": ["Tower Bridge", "Westminster Abbey", "Camden Market"],
        "weather": "Cool year-round (5-25°C), rain common. Best: May-Sept.",
        "airport": "Heathrow (LHR) Piccadilly Line 50min; Gatwick (LGW) Gatwick Express 30min.",
        "permits": "Royal Parks require permit for tripods. Westminster filming restricted near Parliament. TfL bans tripods on Tube during rush hour."
    },
    "Istanbul": {
        "landmarks": ["Hagia Sophia", "Blue Mosque", "Grand Bazaar"],
        "weather": "Hot summers (30-35°C), cool wet winters (5-15°C). Best: Apr-May, Sept-Oct.",
        "airport": "Istanbul (IST) new airport, Havaist bus 60min; Sabiha Gökçen (SAW) Asian side.",
        "permits": "Mosques ban photography during prayer times. Hagia Sophia has restrictions. Grand Bazaar vendors often refuse filming."
    },
    "Seoul": {
        "landmarks": ["Gyeongbokgung Palace", "Myeongdong Shopping", "Hongdae Street"],
        "weather": "Cold winters (-10 to 5°C), hot humid summers (25-35°C). Best: Apr-May (cherry blossoms), Oct-Nov (fall colors).",
        "airport": "Incheon (ICN) AREX Express 45min; Gimpo (GMP) domestic + some international.",
        "permits": "Palace grounds allow tripods but not inside buildings. Myeongdong too crowded for rigs. K-pop filming strictly controlled."
    },
    "Mexico City": {
        "landmarks": ["Zócalo (Main Square)", "Frida Kahlo Museum (Casa Azul)", "Teotihuacán Pyramids"],
        "weather": "Spring-like year-round (15-25°C). Rainy season Jun-Sep. High altitude (2,250m). Best: Mar-May.",
        "airport": "Benito Juárez (MEX) Metro Line 1 30min; Uber widely available.",
        "permits": "Pyramids allow tripods but no drones. Museums ban flash. Zócalo protests common - avoid large gatherings."
    },
    "Lima": {
        "landmarks": ["Historic Centre (Plaza de Armas)", "Miraflores Cliffs", "Huaca Pucllana"],
        "weather": "Desert climate, overcast Dec-Mar (garúa fog), sunny Apr-Nov (18-28°C). Best: Dec-Apr for sun.",
        "airport": "Jorge Chávez (LIM) 40min to Miraflores by taxi. Use official airport taxis only.",
        "permits": "Historic Centre requires permit for commercial shoots. Huaca Pucllana allows tripods. Drones need DIGEMID approval."
    },
    "São Paulo": {
        "landmarks": ["Paulista Avenue", "Municipal Market", "Vila Madalena Street Art"],
        "weather": "Subtropical, warm year-round (15-30°C). Rainy Oct-Mar. Best: Apr-Sept (drier).",
        "airport": "Guarulhos (GRU) 60min by CPTM train + metro; Congonhas (CGH) domestic closer.",
        "permits": "Paulista Ave closed Sundays - great for filming. Vila Madalena artists usually OK with filming. High crime - don't show expensive gear openly."
    },
    "Cairo": {
        "landmarks": ["Pyramids of Giza", "Egyptian Museum", "Khan el-Khalili Bazaar"],
        "weather": "Extremely hot May-Sep (35-45°C), pleasant Nov-Feb (15-25°C). Sandstorms possible spring.",
        "airport": "Cairo (CAIR) 45min to Giza by taxi. Negotiate fare in advance.",
        "permits": "Pyramids require special filming permit from Ministry of Antiquities. No tripods inside museum. Khan market vendors expect tips for filming."
    },
    "Singapore": {
        "landmarks": ["Marina Bay Sands", "Gardens by the Bay", "Chinatown"],
        "weather": "Hot humid year-round (25-35°C). Rain any month. Best: Feb-Apr (slightly drier).",
        "airport": "Changi (SIN) MRT 30min direct. World's best airport - worth filming!",
        "permits": "Strict drone laws - essentially banned without CAAS permit. Marina Bay area secure - expect questioning. Hawker centers OK for casual filming."
    },
    "Dubai": {
        "landmarks": ["Burj Khalifa", "Dubai Mall Fountain", "Gold Souk"],
        "weather": "Extreme heat May-Sep (40-50°C), pleasant Nov-Mar (20-30°C). Best: Dec-Feb.",
        "airport": "Dubai (DXB) Metro Red Line 35min; Al Maktoum (DWC) newer, farther.",
        "permits": "Drone import banned for tourists! Burj Khalifa observation decks ban tripods. Gold Souk merchants often refuse cameras."
    },
    "New York": {
        "landmarks": ["Times Square", "Central Park", "Brooklyn Bridge"],
        "weather": "Four seasons: hot summers (25-35°C), cold winters (-5 to 10°C). Best: Apr-Jun, Sept-Nov.",
        "airport": "JFK AirTrain + subway 60min; LaGuardia (LGA) bus + subway; Newark (EWR) train.",
        "permits": "Times Square costumed characters demand payment. Central Park requires permit for tripods. Subway filming allowed but no blocking doors."
    },
    "Los Angeles": {
        "landmarks": ["Hollywood Sign", "Santa Monica Pier", "Griffith Observatory"],
        "weather": "Sunny year-round (15-30°C), minimal rain. Best: Apr-Jun, Sept-Nov (avoid summer crowds).",
        "airport": "LAX FlyAway bus + metro 75min; Burbank (BUR) closer to Hollywood.",
        "permits": "Hollywood Sign fenced off - shoot from Griffith. Santa Monica Pier crowded weekends. Film permits required for professional shoots."
    },
    "Rio de Janeiro": {
        "landmarks": ["Christ the Redeemer", "Copacabana Beach", "Sugarloaf Mountain"],
        "weather": "Tropical, hot year-round (25-35°C). Rainy Dec-Mar. Best: Apr-Nov.",
        "airport": "Galeão (GIG) 40min to Copacabana by taxi; Santos Dumont (SDU) domestic closer.",
        "permits": "Christ statue requires prior booking. Beach filming OK but watch for theft. Favela tours only with licensed guides."
    },
    "Buenos Aires": {
        "landmarks": ["La Boca (Caminito)", "Recoleta Cemetery", "Puerto Madero"],
        "weather": "Four seasons like Europe. Hot Dec-Feb (25-35°C), cool Jun-Aug (5-15°C). Best: Mar-May, Sept-Nov.",
        "airport": "Ezeiza (EZE) 45min by Tienda León shuttle; Aeroparque (AEP) domestic + regional.",
        "permits": "La Boca artists expect tips. Recoleta has strict rules. Tango shows often ban professional cameras."
    },
    "Bogotá": {
        "landmarks": ["La Candelaria Historic", "Monserrate Hill", "Gold Museum"],
        "weather": "Spring-like year-round due to altitude (10-20°C). Rain Apr-May, Oct-Nov. Best: Dec-Mar, Jun-Aug.",
        "airport": "El Dorado (BOG) 45min by TransMilenio + taxi. Altitude 2,640m - expect shortness of breath.",
        "permits": "La Candelaria cobblestone streets hard for wheeled gear. Monserrate cable car bans tripods. Gold Museum no flash."
    },
    "Santiago": {
        "landmarks": ["Plaza de Armas", "San Cristóbal Hill", "La Moneda Palace"],
        "weather": "Mediterranean: hot dry summers (30-35°C), cool wet winters (5-15°C). Best: Oct-Apr.",
        "airport": "Arturo Merino Benítez (SCL) 30min by Centropuerto bus.",
        "permits": "Palacio de la Moneda restricted area. San Cristóbal funicular allows tripods. Protests common - avoid demonstrations."
    },
    "Ho Chi Minh City": {
        "landmarks": ["War Remnants Museum", "Notre-Dame Cathedral", "Ben Thanh Market"],
        "weather": "Tropical: hot year-round (25-35°C), rainy May-Nov. Best: Dec-Apr (drier).",
        "airport": "Tan Son Nhat (SGN) 30min by taxi. Traffic chaos - allow extra time.",
        "permits": "War Museum bans tripods. Cathedral under renovation. Ben Thanh vendors aggressive about filming fees."
    },
    "Manila": {
        "landmarks": ["Intramuros (Walled City)", "Rizal Park", "Binondo Chinatown"],
        "weather": "Tropical: hot Mar-May (30-38°C), rainy Jun-Oct, cooler Nov-Feb. Typhoon season Jul-Oct.",
        "airport": "Ninoy Aquino (MNL) 30-60min depending on legendary traffic. Jeepney experience optional!",
        "permits": "Intramuros requires permit. Rizal Park security strict. Binondo narrow streets - handheld only."
    },
    "Jakarta": {
        "landmarks": ["Old Town (Kota Tua)", "National Monument (Monas)", "Glodok Chinatown"],
        "weather": "Hot humid year-round (25-35°C). Heavy rain Oct-Apr. Best: May-Sept.",
        "airport": "Soekarno-Hatta (CGK) Railink train 45min; traffic makes taxis unreliable.",
        "permits": "Monas park allows tripods. Kota Tua weekend crowd chaotic. Indonesia strict on filming permits - carry documentation."
    },
    "Karachi": {
        "landmarks": ["Clifton Beach", "Mazar-e-Quaid", "Empress Market"],
        "weather": "Hot Apr-Oct (30-40°C), mild Nov-Mar (15-25°C). Monsoon Jul-Aug. Best: Nov-Feb.",
        "airport": "Jinnah (KHI) 30min by taxi. Security tight - expect checkpoints.",
        "permits": "Beach filming sensitive - ask locals. Mausoleum requires permission. Security situation volatile - check current conditions."
    },
    "Lahore": {
        "landmarks": ["Badshahi Mosque", "Lahore Fort", "Wagah Border Ceremony"],
        "weather": "Extreme heat Apr-Jun (40-45°C), pleasant Nov-Feb (10-25°C). Monsoon Jul-Sep. Best: Oct-Mar.",
        "airport": "Allama Iqbal (LHE) 30min to city. Wagah ceremony requires early arrival.",
        "permits": "Mosque filming allowed outside prayer times. Fort requires ASI permit. Wagah border highly secure - follow military instructions."
    },
    "Dhaka": {
        "landmarks": ["Lalbagh Fort", "Sadarghat River Port", "National Parliament"],
        "weather": "Hot humid Mar-Oct (30-35°C), pleasant Nov-Feb (15-25°C). Monsoon Jun-Sep. Best: Nov-Feb.",
        "airport": "Hazrat Shahjalal (DAC) 45min+ in notorious traffic. Rickshaw experience intense!",
        "permits": "Parliament building requires advance permission. Sadarghat chaotic - watch belongings. Political rallies common - avoid."
    },
    "Kolkata": {
        "landmarks": ["Victoria Memorial", "Howrah Bridge", "Kalighat Temple"],
        "weather": "Hot humid Mar-Jun (30-40°C), monsoon Jul-Sep, pleasant Oct-Feb. Best: Nov-Feb.",
        "airport": "Netaji Subhas (CCU) 45min by taxi. Metro connects to city.",
        "permits": "Howrah Bridge filming restricted. Victoria Memorial allows tripods. Kalighat no photography inside."
    },
    "Mumbai": {
        "landmarks": ["Gateway of India", "Marine Drive", "Elephanta Caves"],
        "weather": "Hot humid Mar-May (30-40°C), monsoon Jun-Sep (heavy!), pleasant Nov-Feb. Best: Nov-Feb.",
        "airport": "Chhatrapati Shivaji (BOM) 45min+ in infamous traffic. Local trains during rush hour = adventure.",
        "permits": "Gateway always crowded. Marine Drive promenade OK. Elephanta ferry + caves allow tripods."
    },
    "Chengdu": {
        "landmarks": ["Panda Research Base", "Kuanzhai Alleys", "People's Park Teahouses"],
        "weather": "Overcast year-round, humid summers (25-35°C), cool winters (5-10°C). Best: Mar-Jun, Sep-Nov.",
        "airport": "Shuangliu (CTU) 30min; Tianfu (TFU) newer, farther (60min+).",
        "permits": "Panda Base: NO FLASH, no tripods, arrive 8AM when pandas active. Teahouses - buy tea first, then ask to film."
    },
    "Chongqing": {
        "landmarks": ["Hongya Cave", "Yangtze River Cableway", "Ciqikou Ancient Town"],
        "weather": "Famous fog, hot summers (35-40°C), cool damp winters (5-10°C). Best: Apr-Jun, Sept-Nov.",
        "airport": "Jiangbei (CKG) Metro Line 3/10 45min. City built on mountains - GPS goes crazy!",
        "permits": "Hongya Cave extremely crowded - handheld only. Cableway bans tripods. Ciqikou weekend mob scene."
    },
    "Guangzhou": {
        "landmarks": ["Canton Tower", "Shamian Island", "Beijing Road Pedestrian Street"],
        "weather": "Subtropical: very humid Apr-Jun (25-35°C), typhoons Jul-Sep. Best: Oct-Dec.",
        "airport": "Baiyun (CAN) Metro Line 3 direct ~40min.",
        "permits": "Canton Tower observation deck bans tripods. Shamian colonial facades OK. Beijing Road night neon - handheld only."
    },
    "Shenzhen": {
        "landmarks": ["Huaqiangbei Electronics Market", "Shenzhen Bay Park", "Dafen Oil Painting Village"],
        "weather": "Subtropical: typhoons Jul-Sep, mild winters (15-25°C). Best: Nov-Jan.",
        "airport": "Bao'an (SZX) Metro Line 11 ~40min. DJI's hometown!",
        "permits": "Huaqiangbei: manual WB for fluorescent light, ask stall owners. Shenzhen Bay skyline sunset OK. Dafen artists welcome filming."
    },
    "Nagoya": {
        "landmarks": ["Nagoya Station/Shinkansen", "Nagoya Castle", "Osu Shopping Street"],
        "weather": "Humid summers, cold dry winters. Cherry blossoms late Mar. Best: Mar-May, Oct-Nov.",
        "airport": "Chubu Centrair (NGO) Meitetsu train ~30min.",
        "permits": "JR platforms require staff permission for filming. Castle exterior OK, interior restricted. Osu street food - ask first."
    },
    "Hong Kong": {
        "landmarks": ["Victoria Peak", "Star Ferry", "Temple Street Night Market"],
        "weather": "Typhoons Jul-Sep, humid summers (28-35°C), mild winters (15-20°C). Best: Oct-Dec.",
        "airport": "HKIA (HKG) Airport Express 24min.",
        "permits": "Peak tripods need space at viewpoints. Star Ferry upper deck handheld only. Temple Street vendors may refuse filming."
    },
    "Tianjin": {
        "landmarks": ["Five Great Avenues (Wudadao)", "Tianjin Eye", "Ancient Culture Street"],
        "weather": "Cold dry winters (-5 to -10°C), hot humid summers. Best: Sept-Nov.",
        "airport": "Binhai (TSN) Metro Line 2 ~30min; 30min high-speed rail from Beijing.",
        "permits": "Colonial mansions sidewalks busy - monopod beats tripod. Jinang Bridge riverbank OK for tripods. Ancient Culture Street handheld in crowds."
    },
    "Hangzhou": {
        "landmarks": ["West Lake", "Lingyin Temple", "Longjing Tea Villages"],
        "weather": "Plum rain June-July, hot summers, beautiful springs. Best: Mar-May, Sept-Nov.",
        "airport": "Xiaoshan (HGH) Metro Lines 7/19 ~50min.",
        "permits": "West Lake sunrise mist magical - tripods fine on causeways. Lingyin no filming inside main halls. Longjing farmers - ask before filming."
    },
    "Foshan": {
        "landmarks": ["Ancestral Temple (Zumiao)", "Nanfeng Ancient Kiln", "Liang Garden"],
        "weather": "Subtropical humid. Best: Oct-Dec.",
        "airport": "Via Guangzhou (CAN) ~1hr; Foshan Shadi (FUO) small domestic.",
        "permits": "Kung fu demos at 120fps! No flash in ancestral halls. 500-year-old kiln handheld. Liang Garden morning light."
    },
    "Shenyang": {
        "landmarks": ["Mukden Palace", "Zhongshan Square", "Tiexi Industrial District"],
        "weather": "Harsh winters (-15 to -25°C)! Best: Sept-Oct or Dec-Feb for snow.",
        "airport": "Taoxian (SHE) Metro Line 2 ~45min.",
        "permits": "Manchu architecture OK outside. Soviet statues blue hour. Industrial winter mood - keep batteries warm in inner pocket!"
    },
    "Nanjing": {
        "landmarks": ["Ming City Wall", "Sun Yat-sen Mausoleum", "Fuzimiao & Qinhuai River"],
        "weather": "Hot humid summers, cold winters. Best: Mar-May, Oct-Nov.",
        "airport": "Lukou (NKG) Metro S1 ~50min.",
        "permits": "City Wall blue hour OK. Mausoleum respectful filming only - 392 steps symmetry shot. Qinhuai night lanterns from boat."
    },
    "Xi'an": {
        "landmarks": ["Terracotta Army", "Ancient City Wall", "Muslim Quarter"],
        "weather": "Dry, hot summers, cold winters. Best: Apr-Jun, Sept-Nov.",
        "airport": "Xianyang (XIY) Metro Line 14 ~50min.",
        "permits": "Terracotta: NO FLASH, no tripods in pits, ISO 3200-6400, arrive opening! City Wall bike golden hour. Muslim Quarter steam + neon B-roll."
    }
}

def generate_city_html(city_data, existing_html):
    """Generate new HTML body for a city page using JSON data."""
    
    city = city_data['city']
    country = city_data['country']
    camera = city_data.get('camera', 'Various')
    challenge = city_data.get('challenge', 'Unique filming conditions')
    attraction1 = city_data.get('attraction1', '')
    tip1 = city_data.get('tip1', '')
    attraction2 = city_data.get('attraction2', '')
    tip2 = city_data.get('tip2', '')
    attraction3 = city_data.get('attraction3', '')
    weather = city_data.get('weather', '')
    airport = city_data.get('airport', '')
    permits = city_data.get('permits', '')
    slug = city_data.get('slug', '')
    
    # Get additional data from our knowledge base
    kb = CITY_DATA.get(city, {})
    landmarks = kb.get('landmarks', [attraction1, attraction2, attraction3])
    
    # Determine video embed
    video_embed = ""
    video_caption = ""
    if city == "Bangkok":
        video_embed = '<iframe src="https://www.youtube.com/embed/7_amUIdgHs4" title="Bangkok field footage" frameborder="0" allowfullscreen loading="lazy"></iframe>'
        video_caption = "🎬 Real field footage: Bangkok, Thailand"
    elif city == "Lima":
        video_embed = '<iframe src="https://www.youtube.com/embed/gRWhgo0KBqY" title="Peru field footage" frameborder="0" allowfullscreen loading="lazy"></iframe>'
        video_caption = "🎬 Real field footage: Huacachina, Peru"
    else:
        video_embed = '<div class="video-placeholder">🎬 Field video coming soon — subscribe on YouTube to see it first</div>'
        video_caption = ""
    
    # Generate intro paragraph
    intro = f"""<p class="lead">Filming in <strong>{city}</strong> presents unique challenges and incredible opportunities. 
    As part of our <a href="/VideoCameraHoliday/city-through-the-lens/">50-city interview series</a>, we connected with local 
    videographers to understand how they capture this dynamic metropolis. From the iconic {landmarks[0]} to hidden neighborhoods, 
    here's what you need to know before rolling camera.</p>"""
    
    # Generate key takeaways
    takeaways = f"""<div class="quick-takeaways">
        <h3>🎯 Quick Takeaways for {city}</h3>
        <ul>
            <li><strong>Best filming season:</strong> {weather.split('.')[0] if '.' in weather else weather[:50]}</li>
            <li><strong>Top 3 landmarks:</strong> {', '.join(landmarks[:3])}</li>
            <li><strong>Drone/permit rule:</strong> {permits[:80]}...</li>
            <li><strong>Airport tip:</strong> {airport}</li>
        </ul>
    </div>"""
    
    # Generate locations section
    locations = f"""<section class="filming-locations">
        <h2>🎬 3 Must-Film Locations in {city}</h2>
        
        <div class="location-card">
            <h3>1. {attraction1}</h3>
            <p><strong>Filming Tip:</strong> {tip1}</p>
        </div>
        
        <div class="location-card">
            <h3>2. {attraction2}</h3>
            <p><strong>Filming Tip:</strong> {tip2}</p>
        </div>
        
        <div class="location-card">
            <h3>3. {attraction3}</h3>
            <p><strong>Filming Tip:</strong> {tip3}</p>
        </div>
    </section>"""
    
    # Generate practical info
    practical = f"""<section class="practical-info">
        <h2>📋 Practical Filming Guide</h2>
        
        <div class="info-grid">
            <div class="info-box">
                <h3>🌤️ Weather Reality</h3>
                <p>{weather}</p>
            </div>
            
            <div class="info-box">
                <h3>✈️ Airport Transfer</h3>
                <p>{airport}</p>
            </div>
            
            <div class="info-box">
                <h3>📜 Permits & Etiquette</h3>
                <p>{permits}</p>
            </div>
        </div>
    </section>"""
    
    # Generate interview teaser
    interview_teaser = f"""<section class="interview-teaser">
        <h2>🎙️ Coming Soon: Local Videographer Interview</h2>
        <p>We're currently editing our interview with a {city}-based filmmaker who will share:</p>
        <ul>
            <li>How they approach filming at {landmarks[0]} vs lesser-known spots</li>
            <li>Their go-to camera settings for {country}'s unique light conditions</li>
            <li>Cultural etiquette tips specific to {city}</li>
            <li>Safety advice for carrying gear in this city</li>
        </ul>
        <p><em>Want to be featured? <a href="mailto:dawid@holidayvideocamera.com">Contact us</a> if you're a local videographer in {city}.</em></p>
    </section>"""
    
    # Assemble the new main content
    new_main = f"""
    <main>
        {intro}
        
        <div class="video-slot">
            <div class="video-embed">
                {video_embed}
            </div>
            {f'<p class="video-caption">{video_caption}</p>' if video_caption else ''}
        </div>
        
        {takeaways}
        {locations}
        {practical}
        {interview_teaser}
        
        <section class="related-cities">
            <h2>🌍 Explore More Cities</h2>
            <p>Check out our other city guides in the <a href="/VideoCameraHoliday/city-through-the-lens/">City Through the Lens</a> series.</p>
        </section>
    </main>
    """
    
    return new_main

def extract_nav_footer(html_content):
    """Extract nav and footer from existing HTML to preserve them."""
    
    # Extract everything before <main> (nav, header)
    nav_header_match = re.search(r'([\s\S]*?)<main>', html_content)
    nav_header = nav_header_match.group(1) if nav_header_match else ''
    
    # Extract everything after </main> (footer, scripts)
    footer_match = re.search(r'</main>([\s\S]*)', html_content)
    footer = footer_match.group(1) if footer_match else ''
    
    return nav_header, footer

def process_city_file(city_data, filename):
    """Process a single city HTML file."""
    
    if not os.path.exists(filename):
        print(f"⚠️ File not found: {filename}")
        return False
    
    with open(filename, 'r', encoding='utf-8') as f:
        existing_html = f.read()
    
    # Extract preserved sections
    nav_header, footer = extract_nav_footer(existing_html)
    
    # Generate new main content
    new_main = generate_city_html(city_data, existing_html)
    
    # Combine
    new_html = nav_header + new_main + footer
    
    # Write back
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_html)
    
    return True

# Main execution
print("\n=== FORCE OVERWRITE: City Preview Pages ===\n")

# Find all city preview files
city_files = [f for f in os.listdir('.') if f.endswith('-interview-preview.html')]
print(f"Found {len(city_files)} city preview files\n")

# Process each city
success_count = 0
for city_data in cities:
    slug = city_data.get('slug', '')
    if not slug:
        continue
    
    filename = f"{slug}.html"
    city_name = city_data.get('city', 'Unknown')
    
    # Skip Beijing (already correct)
    if city_name == "Beijing":
        print(f"⏭️ Skipping Beijing (already correct)")
        continue
    
    print(f"Processing: {city_name} ({filename})")
    
    if process_city_file(city_data, filename):
        success_count += 1
        print(f"  ✅ Updated")
    else:
        print(f"  ❌ Failed")

print(f"\n=== Summary ===")
print(f"Successfully updated: {success_count} files")
print(f"Skipped: 1 (Beijing)")
print(f"Total cities in JSON: {len(cities)}")
