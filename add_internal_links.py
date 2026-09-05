#!/usr/bin/env python3
"""
Add improved internal linking structure to city-through-the-lens pages.
Pattern based on London/Paris/Bangkok/Tokyo/NYC reference pages.

Three sections per page:
1. Region-based city interview links (6 cities)
2. Recommended gear reviews (3 reviews)
3. Related guides (3 guide/destination pages)
"""

import os
import re
import glob

BASE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.join(BASE, "city-through-the-lens")

# ─── CITY DATABASE ───
# slug -> (display_name, flag, region, description)
CITIES = {
    # Europe
    "london":           ("London",          "🇬🇧", "Europe",  "Filming the Thames, Soho, and London's hidden corners."),
    "paris":            ("Paris",           "🇫🇷", "Europe",  "Filming the Eiffel Tower, Montmartre, and the Seine without the crowds."),
    "berlin":           ("Berlin",          "🇩🇪", "Europe",  "Brandenburg Gate, East Side Gallery, and Berlin's moody streets."),
    "amsterdam":        ("Amsterdam",       "🇳🇱", "Europe",  "Filming the canals, cycling culture, and the city's unique light."),
    "rome":             ("Rome",            "🇮🇹", "Europe",  "Filming the Colosseum, Vatican, and Roman streets at golden hour."),
    "barcelona":        ("Barcelona",       "🇪🇸", "Europe",  "Gaudí, beach, and Gothic Quarter – Barcelona through a local's lens."),
    "lisbon":           ("Lisbon",          "🇵🇹", "Europe",  "Capturing Portugal's colourful capital – from trams to the coast."),
    "prague":           ("Prague",          "🇨🇿", "Europe",  "Prague Castle, Charles Bridge, and the fairy-tale old town."),
    "vienna":           ("Vienna",          "🇦🇹", "Europe",  "Imperial palaces, coffeehouse culture, and classical music streets."),
    "budapest":         ("Budapest",        "🇭🇺", "Europe",  "Buda Castle, thermal baths, and the Danube at blue hour."),
    "athens":           ("Athens",          "🇬🇷", "Europe",  "The Acropolis, Plaka, and ancient ruins in modern light."),
    "moscow":           ("Moscow",          "🇷🇺", "Europe",  "Red Square, St Basil's, and Moscow's grand metro stations."),
    "istanbul":         ("Istanbul",        "🇹🇷", "Europe",  "Hagia Sophia, the Bosphorus, and East-meets-West street life."),
    # Asia
    "tokyo":            ("Tokyo",           "🇯🇵", "Asia",    "Neon nights, temples, and the fastest city on earth."),
    "bangkok":          ("Bangkok",         "🇹🇭", "Asia",    "Night markets, temples, and bustling canal life."),
    "beijing":          ("Beijing",         "🇨🇳", "Asia",    "Forbidden City, hutongs, and the Great Wall."),
    "seoul":            ("Seoul",           "🇰🇷", "Asia",    "Capturing Korea's capital – from bustling markets to quiet temples."),
    "shanghai":         ("Shanghai",        "🇨🇳", "Asia",    "The Bund, neon skylines, and old shikumen alleyways."),
    "singapore":        ("Singapore",       "🇸🇬", "Asia",    "Gardens by the Bay, hawker centres, and futuristic skyline."),
    "hong-kong":        ("Hong Kong",       "🇭🇰", "Asia",    "Symphony of Lights, Victoria Peak, and dense street markets."),
    "dubai":            ("Dubai",           "🇦🇪", "Asia",    "Burj Khalifa, desert dunes, and gold souk nightlife."),
    "delhi":            ("Delhi",           "🇮🇳", "Asia",    "Red Fort, Chandni Chowk, and Mughal-era street life."),
    "mumbai":           ("Mumbai",          "🇮🇳", "Asia",    "Gateway of India, Marine Drive, and Bollywood energy."),
    "bangalore":        ("Bangalore",       "🇮🇳", "Asia",    "Tech parks, leafy avenues, and vibrant pub culture."),
    "chennai":          ("Chennai",         "🇮🇳", "Asia",    "Marina Beach, temples, and South Indian film culture."),
    "hyderabad":        ("Hyderabad",       "🇮🇳", "Asia",    "Charminar, biryani stalls, and the old city's bazaars."),
    "kolkata":          ("Kolkata",         "🇮🇳", "Asia",    "Howrah Bridge, colonial architecture, and Durga Puja lights."),
    "jaipur":           ("Jaipur",          "🇮🇳", "Asia",    "Amber Fort, pink city walls, and royal palace courtyards."),
    "ahmedabad":        ("Ahmedabad",       "🇮🇳", "Asia",    "Sabarmati riverfront, pol neighbourhoods, and heritage stepwells."),
    "karachi":          ("Karachi",         "🇵🇰", "Asia",    "Clifton Beach, colonial buildings, and bustling street food."),
    "lahore":           ("Lahore",          "🇵🇰", "Asia",    "Badshahi Mosque, Walled City, and vibrant food streets."),
    "dhaka":            ("Dhaka",           "🇧🇩", "Asia",    "Lalbagh Fort, Sadarghat riverfront, and rickshaw art."),
    "jakarta":          ("Jakarta",         "🇮🇩", "Asia",    "Kota Tua, street markets, and the mega-city's raw energy."),
    "manila":           ("Manila",          "🇵🇭", "Asia",    "Intramuros, jeepneys, and Manila Bay sunsets."),
    "hanoi":            ("Hanoi",           "🇻🇳", "Asia",    "Old Quarter, Hoan Kiem Lake, and Hanoi's vibrant street life."),
    "ho-chi-minh":      ("Ho Chi Minh City","🇻🇳", "Asia",    "Capturing the energy of Saigon – from markets to motorbikes."),
    "chiang-mai":       ("Chiang Mai",      "🇹🇭", "Asia",    "Doi Suthep, Old City temples, and the Night Bazaar."),
    "siem-reap":        ("Siem Reap",       "🇰🇭", "Asia",    "Angkor Wat at sunrise, floating villages, and temple ruins."),
    "luang-prabang":    ("Luang Prabang",   "🇱🇦", "Asia",    "Alms ceremony, Kuang Si falls, and French-colonial charm."),
    "yangon":           ("Yangon",          "🇲🇲", "Asia",    "Shwedagon Pagoda, colonial downtown, and Bago river life."),
    "bali":             ("Bali",            "🇮🇩", "Asia",    "Rice terraces, temple ceremonies, and surf-beach sunsets."),
    "osaka":            ("Osaka",           "🇯🇵", "Asia",    "Dotonbori neon, Osaka Castle, and street-food paradise."),
    "nagoya":           ("Nagoya",          "🇯🇵", "Asia",    "Nagoya Castle, sakae district, and industrial heritage."),
    "tehran":           ("Tehran",          "🇮🇷", "Asia",    "Golestan Palace, Grand Bazaar, and Alborz mountain backdrops."),
    "riyadh":           ("Riyadh",          "🇸🇦", "Asia",    "Diriyah ruins, Kingdom Centre, and desert cityscapes."),
    "baghdad":          ("Baghdad",         "🇮🇶", "Asia",    "Tigris riverfront, Mutanabbi Street, and ancient heritage."),
    "guangzhou":        ("Guangzhou",       "🇨🇳", "Asia",    "Canton Tower, Shamian Island, and Pearl River nights."),
    "shenzhen":         ("Shenzhen",        "🇨🇳", "Asia",    "Huaqiangbei electronics, skyscraper parks, and Dafen art village."),
    "chengdu":          ("Chengdu",         "🇨🇳", "Asia",    "Pandas, Jinli Street, and Sichuan teahouse culture."),
    "chongqing":        ("Chongqing",       "🇨🇳", "Asia",    "Hongya Cave, Yangtze cable car, and the 3D cityscape."),
    "dongguan":         ("Dongguan",        "🇨🇳", "Asia",    "Manufacturing hub, Opium War Museum, and Keyuan gardens."),
    "foshan":           ("Foshan",          "🇨🇳", "Asia",    "Ancestral Temple, martial arts heritage, and Lingnan water towns."),
    "hangzhou":         ("Hangzhou",        "🇨🇳", "Asia",    "West Lake, tea plantations, and Song Dynasty pagodas."),
    "nanjing":          ("Nanjing",         "🇨🇳", "Asia",    "Sun Yat-sen Mausoleum, City Wall, and Confucius Temple area."),
    "shenyang":         ("Shenyang",        "🇨🇳", "Asia",    "Mukden Palace, Beiling Park, and Manchu heritage."),
    "tianjin":          ("Tianjin",         "🇨🇳", "Asia",    "European concession buildings, Hai River, and the Eye of Tianjin."),
    "xian":             ("Xi'an",           "🇨🇳", "Asia",    "Terracotta Army, Muslim Quarter, and the ancient city wall."),
    # Americas
    "new-york-city":    ("New York City",   "🇺🇸", "Americas", "Times Square, Central Park, and Brooklyn Bridge at blue hour."),
    "mexico-city":      ("Mexico City",     "🇲🇽", "Americas", "Zócalo, Teotihuacán, and Coyoacán's colourful streets."),
    "rio-de-janeiro":   ("Rio de Janeiro",  "🇧🇷", "Americas", "Christ the Redeemer, Copacabana, and the hills of the Marvelous City."),
    "buenos-aires":     ("Buenos Aires",    "🇦🇷", "Americas", "Tango, steaks, and the European charm of Argentina's capital."),
    "santiago":         ("Santiago",        "🇨🇱", "Americas", "Andes backdrop, Plaza de Armas, and San Cristóbal hill views."),
    "lima":             ("Lima",            "🇵🇪", "Americas", "Miraflores cliffs, colonial centre, and Pacific coast food scene."),
    "bogota":           ("Bogotá",          "🇨🇴", "Americas", "La Candelaria street art, Monserrate, and high-altitude light."),
    "cartagena":        ("Cartagena",       "🇨🇴", "Americas", "Walled old town, colourful colonial streets, and Caribbean humidity."),
    "guadalajara":      ("Guadalajara",     "🇲🇽", "Americas", "Hospicio Cabañas, Tlaquepaque crafts, and mariachi culture."),
    "sao-paulo":        ("São Paulo",       "🇧🇷", "Americas", "Avenida Paulista, street art, and the mega-city's vertical energy."),
    "cusco":            ("Cusco",           "🇵🇪", "Americas", "Plaza de Armas, Sacsayhuamán, and the gateway to Machu Picchu."),
    # Africa
    "cairo":            ("Cairo",           "🇪🇬", "Africa",   "Pyramids of Giza, Khan el-Khalili bazaar, and Nile sunsets."),
    "cape-town":        ("Cape Town",       "🇿🇦", "Africa",   "Table Mountain, V&A Waterfront, and colourful Bo-Kaap streets."),
    "nairobi":          ("Nairobi",         "🇰🇪", "Africa",   "Nairobi National Park, Giraffe Centre, and city safari sunsets."),
    "lagos":            ("Lagos",           "🇳🇬", "Africa",   "Lekki Conservation Centre, Victoria Island, and Afrobeat energy."),
    "kinshasa":         ("Kinshasa",        "🇨🇩", "Africa",   "Congo River, Académie des Beaux-Arts, and rumba street culture."),
    "luanda":           ("Luanda",          "🇦🇴", "Africa",   "Marginal waterfront, Fortaleza de São Miguel, and Atlantic sunsets."),
    "marrakech":        ("Marrakech",       "🇲🇦", "Africa",   "Jemaa el-Fnaa, souks, and Majorelle Garden blue."),
}

# ─── REVIEW DATABASE ───
# slug -> (title, description)
REVIEWS = {
    "sony-zv-1-ii-review.html":                 ("Sony ZV-1 II Review",                "1-inch sensor vlogging compact – ideal for street photography and vlogging."),
    "dji-osmo-pocket-4p-review.html":           ("DJI Osmo Pocket 4 Pro Review",       "The ultimate compact gimbal camera – perfect for busy streets."),
    "fujifilm-x100vi-review.html":              ("Fujifilm X100VI Review",             "APS-C sensor and film simulations – the street photographer's dream."),
    "gopro-hero-13-review.html":                ("GoPro Hero 13 Review",               "Rugged, waterproof, and ready for unpredictable weather."),
    "gopro-hero-13-black-alps-hiking-companion.html": ("GoPro Hero 13 Black Alps Hiking",  "Packing light for the mountains with the Hero 13 Black."),
    "sony-zv-e10-ii-night-market-review.html":  ("Sony ZV-E10 II Night Market Review", "APS-C sensor and interchangeable lenses – the best for night markets."),
    "iphone-16-pro-video-review.html":          ("iPhone 16 Pro Video Review",         "The camera you already have – with Action Mode for stabilization."),
    "dji-osmo-action-5-review.html":            ("DJI Osmo Action 5 Pro Review",       "Rugged action camera with great low-light and waterproofing."),
    "dji-osmo-action-6-review.html":            ("DJI Osmo Action 6 Review",           "Maldives deep dive and beach test – built for water and sand."),
    "dji-osmo-pocket-3-review.html":            ("DJI Osmo Pocket 3 Review",           "Pocket-sized gimbal camera with great low-light performance."),
    "insta360-x5-review.html":                  ("Insta360 X5 Review",                 "8K 360° camera – capture everything around you in one shot."),
    "insta360-go-3s-hands-free-review.html":    ("Insta360 GO 3S Review",              "Hands-free, feather-light, perfect for POV travel footage."),
    "canon-eos-r50-v-creator-kit-review.html":  ("Canon EOS R50 V Creator Kit Review", "Entry-level mirrorless with great AF for travel vlogging."),
    "fujifilm-x-m5-travel-review.html":         ("Fujifilm X-M5 Travel Review",        "Compact APS-C with film sims – a travel vlogger's delight."),
    "nikon-z50-ii-creator-kit-review.html":     ("Nikon Z50 II Creator Kit Review",    "APS-C mirrorless with flip screen and solid AF for creators."),
    "om-system-om-3-travel-review.html":        ("OM System OM-3 Travel Review",       "Micro four thirds compact – great IBIS and weather sealing."),
    "panasonic-lumix-s5ii-review.html":         ("Panasonic Lumix S5II Review",        "Full-frame mirrorless with Phase Hybrid AF for pro video."),
    "dji-mini-4-pro-review.html":               ("DJI Mini 4 Pro Review",              "Best travel drone under 249g – no registration needed."),
    "dji-air-3-review.html":                     ("DJI Air 3 Review",                   "Dual-camera drone for travel – wide and medium tele in one."),
    "canon-powershot-v10-review.html":          ("Canon PowerShot V10 Review",         "Pocket-sized vlog camera with built-in stand and mic."),
    "insta360-ace-pro-review.html":             ("Insta360 Ace Pro Review",            "AI-powered action camera with excellent low-light for travel."),
    "gopro-max-2-review.html":                  ("GoPro Max 2 Review",                 "360° simplicity – waterproof and easy to reframe later."),
    "samsung-galaxy-s25-ultra-video.html":      ("Samsung Galaxy S25 Ultra Review",    "Flagship phone video with pro-grade Nightography modes."),
    "budget-4k-camcorder-roundup.html":         ("Budget 4K Camcorder Roundup",        "Affordable 4K camcorders tested for holiday video."),
    "pocket-cinema-cameras-2026-roundup.html":  ("Pocket Cinema Cameras 2026",         "Cinema-quality in your pocket – Blackmagic and more."),
    "akaso-ek7000-pro-review.html":             ("Akaso EK7000 Pro Review",            "Budget action cam – does it hold up for travel video?"),
    "sony-zv-1-ii-finland-northern-lights-videography.html": ("Sony ZV-1 II Northern Lights",  "Chasing the Northern Lights in Finland with the ZV-1 II."),
    "sony-zv-1-ii-lisbon-cobblestones-stabilization-test.html": ("Sony ZV-1 II Lisbon Cobblestones", "Real-world stabilization test on Lisbon's cobblestones."),
    "DJI-Osmo-Pocket-4P-Bangkok.html":          ("DJI Osmo Pocket 4P in Bangkok",      "Low-light street videography guide for Bangkok nights."),
    "gopro-hero-13-black-alps-hiking-companion.html": ("GoPro Hero 13 Black Alps Hiking",  "Why the Hero 13 Black is your best Alps hiking companion."),
}

# ─── GUIDE/DESTINATION DATABASE ───
# path -> (title, description, type)
GUIDES = {
    "guides/best-compact-cameras-city-breaks.html":        ("Best Compact Cameras for City Breaks 2026", "8 top compact cameras tested on real city breaks."),
    "guides/best-holiday-video-cameras-2026.html":         ("Best Holiday Video Cameras 2026",          "10 tested picks for every trip and budget."),
    "guides/best-camera-southeast-asia.html":              ("Best Cameras for Southeast Asia",          "Top picks for filming in humid, tropical conditions."),
    "guides/best-budget-holiday-camera-under-500.html":    ("Best Holiday Cameras Under $500",         "Great video cameras that won't break the bank."),
    "guides/best-vlogging-cameras-travel-2026.html":       ("Best Vlogging Cameras for Travel 2026",   "Top vlogging picks tested on the road."),
    "guides/best-waterproof-cameras-beach.html":           ("Best Waterproof Cameras for Beach",       "Tested in salt and sand – beach-ready picks."),
    "guides/best-camera-hiking-holidays.html":             ("Best Cameras for Hiking Holidays",        "Lightweight, rugged picks for trail and summit."),
    "guides/best-camera-ski-holidays.html":                ("Best Cameras for Ski Holidays",           "Cold-weather cameras that survive the slopes."),
    "guides/best-camera-for-family-holidays.html":         ("Best Camera for Family Holidays",         "Easy-to-use cameras for family trip memories."),
    "guides/best-camcorder-family-vacation-2026.html":     ("Best Camcorder for Family Vacation",      "Zoom and battery life for family trips."),
    "guides/best-camera-cruise-vacations-2026.html":       ("Best Camera for Cruise Vacations",        "Salt-proof and compact picks for cruise travel."),
    "guides/best-low-light-camera-evening-vacation.html":  ("Best Low Light Camera for Evenings",      "Capture night markets and sunset scenes."),
    "guides/best-mirrorless-camera-travel-video-2026.html":("Best Mirrorless Camera for Travel Video", "APS-C vs full frame for travel video."),
    "guides/best-point-and-shoot-travel-video-2026.html":  ("Best Point and Shoot for Travel Video",   "No lens swaps needed – just point and shoot."),
    "guides/best-camera-safari-holiday-video-2026.html":   ("Best Camera for Safari Holiday Video",    "Zoom and durability for African safari video."),
    "guides/best-cameras-african-safari-2026.html":        ("Best Cameras for African Safaris 2026",   "Zoom and durability tested for safari."),
    "guides/how-to-choose-video-camera-holiday.html":      ("How to Choose a Holiday Video Camera",    "2026 buyer's guide – what matters for travel video."),
    "guides/travel-camera-checklist-2026.html":            ("Travel Camera Checklist 2026",            "Everything to pack before you fly."),
    "guides/what-to-film-european-night-markets.html":     ("What to Film at European Night Markets",  "Techniques for capturing night market atmosphere."),
    "guides/film-travel-videos-without-crowds.html":       ("Film Travel Videos Without Crowds",       "7 pro techniques for crowd-free footage."),
    "guides/quiet-camera-recording-tourist-spots.html":    ("Quiet Camera for Tourist Spots",          "Discreet filming in churches, museums, and temples."),
    "guides/one-bag-travel-filmmaker-gear-list-2026.html": ("One-Bag Travel Filmmaker Gear List",      "Complete carry-on gear list for travel video."),
    "guides/rent-vs-buy-travel-camera-gear-2026.html":     ("Rent vs Buy Travel Camera Gear",          "Cost calculator – when renting wins."),
    "guides/state-of-travel-cameras-2026.html":            ("State of Travel Cameras 2026",            "The big picture of travel video gear this year."),
    "guides/ultimate-holiday-video-camera-setup.html":     ("Ultimate Holiday Video Camera Setup",     "Complete rig guide from camera to mic to gimbal."),
    "guides/best-travel-camera-external-mic-input.html":   ("Best Travel Camera with Mic Input",       "Cameras with external mic jacks for better audio."),
    "guides/best-travel-camera-flip-screen-2026.html":     ("Best Travel Camera with Flip Screen",     "Vlogging selfie picks with articulating screens."),
    "guides/best-vlogging-camera-beginners-2026.html":     ("Best Vlogging Camera for Beginners",      "Under $300 to $1000 – starter picks."),
    "guides/best-camera-kids-record-vacations.html":       ("Best Camera for Kids to Record Vacations","Kid-friendly picks for family trip videos."),
    "guides/camera-gifts-for-travelers.html":              ("Camera Gifts for Travelers",              "Gift ideas for the travel videographer."),
    "guides/when-to-buy-travel-camera-cheapest.html":      ("When to Buy a Travel Camera Cheapest",    "Price cycle guide – timing your purchase."),
    "guides/best-hybrid-travel-camera-2026.html":          ("Best Hybrid Travel Camera 2026",          "Stills and video in one travel-ready body."),
    "guides/best-video-camera-picks-holiday-adventure.html":("Best Video Camera for Holiday Adventure","Picks for adventure and active travel video."),
    "guides/best-video-cameras-holiday-travel-2026.html":  ("Best Video Cameras for Holiday Travel",   "12 top picks tested for holiday video."),
    "guides/best-travel-cameras-winter-unesco-adventures.html": ("Best Travel Cameras for Winter UNESCO", "Winter UNESCO site adventures – gear that survives."),
    "guides/becoming-travel-filmmaker-career-guide-2026.html": ("Becoming a Travel Filmmaker",          "Portfolio, clients, and making it pay in 2026."),
    "guides/what-camera-do-travel-youtubers-use.html":     ("What Cameras Travel YouTubers Use",       "2026 creator setups revealed."),
    "guides/small-video-camera-backpacking-2026.html":     ("Small Video Camera for Backpacking",      "Lightweight picks for ultralight travel."),
    "guides/best-budget-vlogging-camera-europe.html":      ("Best Budget Vlogging Camera Europe",      "Top budget picks tested across Europe."),
    "guides/filming-southeast-asia-gear-guide-2026.html":  ("Filming Southeast Asia Gear Guide",       "The ultimate gear guide for SEA conditions."),
    "guides/ultimate-spring-travel-camera-packing-checklist-2027.html": ("Spring Travel Camera Packing List", "Complete packing checklist for spring 2027 trips."),
    "guides/ultimate-holiday-travel-camera-guide-zv1-ii-hero13-pocket4p.html": ("Ultimate Holiday Camera Guide", "ZV-1 II, Hero 13, or Pocket 4P – which to pick?"),
    # Destinations
    "destinations/best-cameras-city-breaks.html":               ("Best Cameras for City Breaks",            "Destination guide for urban travel photography."),
    "destinations/bangkok-camera-guide.html":                   ("Bangkok Travel Camera Guide",            "Complete guide to filming in Bangkok – locations, gear, and tips."),
    "destinations/best-cameras-beach-holidays.html":            ("Best Cameras for Beach Holidays",        "Tested in sand, salt, and sun – beach-ready picks."),
    "destinations/best-cameras-ski-holidays.html":              ("Best Cameras for Ski Holidays",          "Cold-weather cameras that survive the slopes."),
    "destinations/best-cameras-desert-travel.html":             ("Best Cameras for Desert Travel",         "Heat, dust, and sand – gear that handles it."),
    "destinations/underwater-camera-guide.html":                ("Underwater Camera Guide",               "Snorkelling and diving gear for underwater video."),
    "destinations/african-safari-camera-setup.html":            ("African Safari Camera Setup",            "Complete guide to safari camera gear and settings."),
    "destinations/dubai-travel-guide.html":                     ("Dubai Travel Guide",                     "Culture, attractions, and filming tips for Dubai."),
    "destinations/vietnam-camera-guide.html":                   ("Vietnam Travel Camera Guide",            "Best gear and filming tips for Vietnam."),
    "destinations/camera-guide-machu-picchu.html":              ("Machu Picchu Camera Guide",              "What camera to bring to Machu Picchu – complete 2026 guide."),
    "destinations/camera-guide-southeast-asia-complete-2026.html": ("Southeast Asia Camera Guide",        "Humidity, temples, and night markets – the right gear."),
    "destinations/japan-cherry-blossom-camera-guide-2026.html": ("Japan Cherry Blossom Camera Guide",     "Best cameras and timing for sakura season."),
    "destinations/best-camera-japan-cherry-blossom.html":       ("Best Camera for Japan Cherry Blossom",  "Sakura season gear and timing guide."),
    "destinations/best-cameras-african-safari-2026.html":       ("Best Cameras for African Safaris",      "Zoom and durability tested for safari."),
    "destinations/gopro-hero-13-unesco-world-heritage-sites.html": ("GoPro Hero 13 at UNESCO Sites",      "Filming world heritage sites with the Hero 13."),
    "destinations/waterproof-camera-cenotes-mexico.html":      ("Waterproof Camera for Cenotes Mexico",   "Underwater-tested picks for cenote diving."),
    "destinations/insta360-x5-settings-bali-beach-clubs.html":  ("Insta360 X5 Settings for Bali",         "The ultimate 360 settings guide for Bali beach clubs."),
    "destinations/low-light-camera-settings-da-nang.html":      ("Low Light Settings for Da Nang",         "Night markets and Dragon Bridge filming guide."),
    "destinations/protect-camera-bangkok-humidity.html":        ("Protect Camera from Bangkok Humidity",   "Stop mold and condensation in tropical climates."),
    "destinations/galapagos-cruise-gear-packing-list.html":     ("Galapagos Cruise Gear Packing List",     "Complete packing guide for a Galapagos cruise."),
    "destinations/year-in-review-5-travel-videography-lessons-bangkok-finland.html": ("5 Travel Videography Lessons", "Year in review from Bangkok to Finland."),
}

# ─── REGION-BASED GEAR/GUIDE ASSIGNMENTS ───
REGION_REVIEWS = {
    "Europe": [
        "sony-zv-1-ii-review.html",
        "dji-osmo-pocket-4p-review.html",
        "fujifilm-x100vi-review.html",
    ],
    "Asia": [
        "sony-zv-e10-ii-night-market-review.html",
        "dji-osmo-pocket-4p-review.html",
        "gopro-hero-13-review.html",
    ],
    "Americas": [
        "sony-zv-1-ii-review.html",
        "dji-osmo-pocket-4p-review.html",
        "iphone-16-pro-video-review.html",
    ],
    "Africa": [
        "sony-zv-1-ii-review.html",
        "gopro-hero-13-review.html",
        "dji-osmo-pocket-4p-review.html",
    ],
}

REGION_GUIDES = {
    "Europe": [
        "guides/best-compact-cameras-city-breaks.html",
        "guides/best-holiday-video-cameras-2026.html",
        "destinations/best-cameras-city-breaks.html",
    ],
    "Asia": [
        "guides/best-camera-southeast-asia.html",
        "guides/best-holiday-video-cameras-2026.html",
        "destinations/camera-guide-southeast-asia-complete-2026.html",
    ],
    "Americas": [
        "guides/best-compact-cameras-city-breaks.html",
        "guides/best-holiday-video-cameras-2026.html",
        "destinations/best-cameras-city-breaks.html",
    ],
    "Africa": [
        "guides/best-cameras-african-safari-2026.html",
        "destinations/african-safari-camera-setup.html",
        "guides/best-holiday-video-cameras-2026.html",
    ],
}

# City-specific review/guide overrides
CITY_OVERRIDES = {
    "bali": {
        "reviews": ["dji-osmo-action-6-review.html", "gopro-hero-13-review.html", "insta360-x5-review.html"],
        "guides": ["guides/best-waterproof-cameras-beach.html", "destinations/insta360-x5-settings-bali-beach-clubs.html", "guides/best-holiday-video-cameras-2026.html"],
    },
    "cape-town": {
        "reviews": ["gopro-hero-13-review.html", "dji-osmo-pocket-4p-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-cameras-african-safari-2026.html", "destinations/african-safari-camera-setup.html", "guides/best-holiday-video-cameras-2026.html"],
    },
    "nairobi": {
        "reviews": ["gopro-hero-13-review.html", "sony-zv-1-ii-review.html", "dji-osmo-pocket-4p-review.html"],
        "guides": ["guides/best-camera-safari-holiday-video-2026.html", "destinations/african-safari-camera-setup.html", "guides/best-holiday-video-cameras-2026.html"],
    },
    "marrakech": {
        "reviews": ["dji-osmo-pocket-4p-review.html", "fujifilm-x100vi-review.html", "gopro-hero-13-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-desert-travel.html"],
    },
    "cairo": {
        "reviews": ["dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-desert-travel.html"],
    },
    "dubai": {
        "reviews": ["dji-osmo-action-5-review.html", "dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html"],
        "guides": ["destinations/dubai-travel-guide.html", "destinations/best-cameras-desert-travel.html", "guides/best-holiday-video-cameras-2026.html"],
    },
    "riyadh": {
        "reviews": ["dji-osmo-action-5-review.html", "dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html"],
        "guides": ["destinations/best-cameras-desert-travel.html", "guides/best-holiday-video-cameras-2026.html", "guides/best-compact-cameras-city-breaks.html"],
    },
    "cusco": {
        "reviews": ["gopro-hero-13-review.html", "dji-osmo-pocket-4p-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["destinations/camera-guide-machu-picchu.html", "guides/best-holiday-video-cameras-2026.html", "guides/best-camera-hiking-holidays.html"],
    },
    "lima": {
        "reviews": ["sony-zv-1-ii-review.html", "dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html"],
        "guides": ["destinations/camera-guide-machu-picchu.html", "guides/best-holiday-video-cameras-2026.html", "guides/best-compact-cameras-city-breaks.html"],
    },
    "rio-de-janeiro": {
        "reviews": ["gopro-hero-13-review.html", "sony-zv-1-ii-review.html", "iphone-16-pro-video-review.html"],
        "guides": ["destinations/best-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "guides/best-waterproof-cameras-beach.html"],
    },
    "sao-paulo": {
        "reviews": ["sony-zv-1-ii-review.html", "dji-osmo-pocket-4p-review.html", "iphone-16-pro-video-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "buenos-aires": {
        "reviews": ["sony-zv-1-ii-review.html", "fujifilm-x100vi-review.html", "dji-osmo-pocket-4p-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "beijing": {
        "reviews": ["dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html", "dji-mini-4-pro-review.html"],
        "guides": ["guides/best-holiday-video-cameras-2026.html", "guides/best-compact-cameras-city-breaks.html", "destinations/best-cameras-city-breaks.html"],
    },
    "shanghai": {
        "reviews": ["dji-osmo-pocket-4p-review.html", "sony-zv-1-ii-review.html", "fujifilm-x100vi-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "hong-kong": {
        "reviews": ["dji-osmo-pocket-4p-review.html", "sony-zv-1-ii-review.html", "gopro-hero-13-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "tokyo": {
        "reviews": ["fujifilm-x100vi-review.html", "dji-osmo-pocket-4p-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "osaka": {
        "reviews": ["fujifilm-x100vi-review.html", "dji-osmo-pocket-4p-review.html", "sony-zv-e10-ii-night-market-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "seoul": {
        "reviews": ["fujifilm-x100vi-review.html", "dji-osmo-pocket-4p-review.html", "sony-zv-e10-ii-night-market-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "chiang-mai": {
        "reviews": ["sony-zv-e10-ii-night-market-review.html", "dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html"],
        "guides": ["guides/best-camera-southeast-asia.html", "destinations/camera-guide-southeast-asia-complete-2026.html", "guides/best-holiday-video-cameras-2026.html"],
    },
    "siem-reap": {
        "reviews": ["dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-camera-southeast-asia.html", "destinations/camera-guide-southeast-asia-complete-2026.html", "guides/best-holiday-video-cameras-2026.html"],
    },
    "hanoi": {
        "reviews": ["sony-zv-e10-ii-night-market-review.html", "dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html"],
        "guides": ["destinations/vietnam-camera-guide.html", "guides/best-camera-southeast-asia.html", "guides/best-holiday-video-cameras-2026.html"],
    },
    "ho-chi-minh": {
        "reviews": ["sony-zv-e10-ii-night-market-review.html", "dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html"],
        "guides": ["destinations/vietnam-camera-guide.html", "guides/best-camera-southeast-asia.html", "guides/best-holiday-video-cameras-2026.html"],
    },
    "jakarta": {
        "reviews": ["dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-camera-southeast-asia.html", "guides/best-waterproof-cameras-beach.html", "guides/best-holiday-video-cameras-2026.html"],
    },
    "manila": {
        "reviews": ["dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-camera-southeast-asia.html", "guides/best-waterproof-cameras-beach.html", "guides/best-holiday-video-cameras-2026.html"],
    },
    "yangon": {
        "reviews": ["dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-camera-southeast-asia.html", "destinations/camera-guide-southeast-asia-complete-2026.html", "guides/best-holiday-video-cameras-2026.html"],
    },
    "luang-prabang": {
        "reviews": ["dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-camera-southeast-asia.html", "destinations/camera-guide-southeast-asia-complete-2026.html", "guides/best-holiday-video-cameras-2026.html"],
    },
    "delhi": {
        "reviews": ["sony-zv-e10-ii-night-market-review.html", "dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html"],
        "guides": ["guides/best-holiday-video-cameras-2026.html", "guides/best-compact-cameras-city-breaks.html", "destinations/best-cameras-city-breaks.html"],
    },
    "mumbai": {
        "reviews": ["sony-zv-e10-ii-night-market-review.html", "dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html"],
        "guides": ["guides/best-holiday-video-cameras-2026.html", "guides/best-compact-cameras-city-breaks.html", "destinations/best-cameras-city-breaks.html"],
    },
    "jaipur": {
        "reviews": ["fujifilm-x100vi-review.html", "dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html"],
        "guides": ["guides/best-holiday-video-cameras-2026.html", "guides/best-compact-cameras-city-breaks.html", "destinations/best-cameras-desert-travel.html"],
    },
    "karachi": {
        "reviews": ["dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-holiday-video-cameras-2026.html", "guides/best-compact-cameras-city-breaks.html", "destinations/best-cameras-city-breaks.html"],
    },
    "istanbul": {
        "reviews": ["fujifilm-x100vi-review.html", "dji-osmo-pocket-4p-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/what-to-film-european-night-markets.html", "guides/best-holiday-video-cameras-2026.html"],
    },
    "athens": {
        "reviews": ["fujifilm-x100vi-review.html", "dji-osmo-pocket-4p-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "moscow": {
        "reviews": ["sony-zv-1-ii-review.html", "dji-osmo-pocket-4p-review.html", "fujifilm-x100vi-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-low-light-camera-evening-vacation.html", "guides/best-holiday-video-cameras-2026.html"],
    },
    "vienna": {
        "reviews": ["fujifilm-x100vi-review.html", "dji-osmo-pocket-4p-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "budapest": {
        "reviews": ["fujifilm-x100vi-review.html", "dji-osmo-pocket-4p-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-low-light-camera-evening-vacation.html", "guides/best-holiday-video-cameras-2026.html"],
    },
    "prague": {
        "reviews": ["fujifilm-x100vi-review.html", "dji-osmo-pocket-4p-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "lisbon": {
        "reviews": ["sony-zv-1-ii-review.html", "dji-osmo-pocket-4p-review.html", "fujifilm-x100vi-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "barcelona": {
        "reviews": ["fujifilm-x100vi-review.html", "dji-osmo-pocket-4p-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "amsterdam": {
        "reviews": ["sony-zv-1-ii-review.html", "dji-osmo-pocket-4p-review.html", "fujifilm-x100vi-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "berlin": {
        "reviews": ["fujifilm-x100vi-review.html", "dji-osmo-pocket-4p-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "nagoya": {
        "reviews": ["fujifilm-x100vi-review.html", "dji-osmo-pocket-4p-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "guadalajara": {
        "reviews": ["sony-zv-1-ii-review.html", "dji-osmo-pocket-4p-review.html", "iphone-16-pro-video-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "cartagena": {
        "reviews": ["gopro-hero-13-review.html", "dji-osmo-pocket-4p-review.html", "sony-zv-1-ii-review.html"],
        "guides": ["destinations/best-cameras-city-breaks.html", "guides/best-waterproof-cameras-beach.html", "guides/best-holiday-video-cameras-2026.html"],
    },
    "bogota": {
        "reviews": ["sony-zv-1-ii-review.html", "dji-osmo-pocket-4p-review.html", "iphone-16-pro-video-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "santiago": {
        "reviews": ["sony-zv-1-ii-review.html", "dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
    "mexico-city": {
        "reviews": ["sony-zv-1-ii-review.html", "dji-osmo-pocket-4p-review.html", "iphone-16-pro-video-review.html"],
        "guides": ["guides/best-compact-cameras-city-breaks.html", "guides/best-holiday-video-cameras-2026.html", "destinations/best-cameras-city-breaks.html"],
    },
}

# Already-done pages (skip)
DONE = {"london", "paris", "bangkok", "tokyo", "new-york-city"}

# Region emoji and heading
REGION_EMOJI = {
    "Europe": "🌍",
    "Asia": "🌏",
    "Americas": "🌎",
    "Africa": "🌍",
}
REGION_LABEL = {
    "Europe": "European",
    "Asia": "Asian",
    "Americas": "Americas",
    "Africa": "African",
}


def get_related_cities(slug, region, count=6):
    """Get related cities from the same region, excluding the current one."""
    same_region = [
        (s, info) for s, info in CITIES.items()
        if info[2] == region and s != slug and s not in DONE
    ]
    # Also include done pages from same region
    done_same = [
        (s, info) for s, info in CITIES.items()
        if info[2] == region and s != slug and s in DONE
    ]
    # Interleave: prioritize done pages first (they have full content), then others
    candidates = done_same + same_region
    return candidates[:count]


def get_reviews(slug, region):
    """Get 3 review links for a city."""
    if slug in CITY_OVERRIDES and "reviews" in CITY_OVERRIDES[slug]:
        return CITY_OVERRIDES[slug]["reviews"]
    return REGION_REVIEWS.get(region, REGION_REVIEWS["Europe"])


def get_guides(slug, region):
    """Get 3 guide/destination links for a city."""
    if slug in CITY_OVERRIDES and "guides" in CITY_OVERRIDES[slug]:
        return CITY_OVERRIDES[slug]["guides"]
    return REGION_GUIDES.get(region, REGION_GUIDES["Europe"])


def build_related_section(slug):
    """Build the HTML for the related-content section."""
    name, flag, region, desc = CITIES[slug]
    emoji = REGION_EMOJI[region]
    label = REGION_LABEL[region]

    # Section 1: Region-based city links
    related = get_related_cities(slug, region)
    city_links = []
    for cslug, (cname, cflag, cregion, cdesc) in related:
        city_links.append(
            f'                <a class="related-card" href="/VideoCameraHoliday/city-through-the-lens/{cslug}-interview-preview.html">\n'
            f'                    <h4>{cflag} {cname}</h4>\n'
            f'                    <p>{cdesc}</p>\n'
            f'                </a>'
        )

    # Section 2: Gear reviews
    review_slugs = get_reviews(slug, region)
    review_links = []
    for rslug in review_slugs:
        if rslug in REVIEWS:
            rtitle, rdesc = REVIEWS[rslug]
            review_links.append(
                f'                <a class="related-card" href="/VideoCameraHoliday/reviews/{rslug}">\n'
                f'                    <h4>{rtitle}</h4>\n'
                f'                    <p>{rdesc}</p>\n'
                f'                </a>'
            )

    # Section 3: Guides/destinations
    guide_paths = get_guides(slug, region)
    guide_links = []
    for gpath in guide_paths:
        if gpath in GUIDES:
            gtitle, gdesc = GUIDES[gpath]
            guide_links.append(
                f'                <a class="related-card" href="/VideoCameraHoliday/{gpath}">\n'
                f'                    <h4>{gtitle}</h4>\n'
                f'                    <p>{gdesc}</p>\n'
                f'                </a>'
            )

    # Build the full section
    html = (
        f'        <!-- ===== RELATED CONTENT – IMPROVED INTERNAL LINKING ===== -->\n'
        f'        <section class="related-section">\n'
        f'\n'
        f'            <h3>{emoji} More {label} City Interviews</h3>\n'
        f'            <div class="related-articles">\n'
        f'{chr(10).join(city_links)}\n'
        f'            </div>\n'
        f'\n'
        f'            <h3>📸 Recommended Gear for {name}</h3>\n'
        f'            <div class="related-articles">\n'
        f'{chr(10).join(review_links)}\n'
        f'            </div>\n'
        f'\n'
        f'            <h3>📚 Related Guides for Your {name} Trip</h3>\n'
        f'            <div class="related-articles">\n'
        f'{chr(10).join(guide_links)}\n'
        f'            </div>\n'
        f'\n'
        f'        </section>\n'
    )
    return html


# CSS to add if not present
RELATED_CSS = """        .related-section { margin-top: 50px; }
        .related-section h3 { color: #e94560; font-size: 1.4rem; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 8px; }"""

RELATED_CSS_FULL = """        .related-articles { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 20px; margin: 30px 0; }
        .related-card { background: #111; border: 1px solid #333; border-radius: 12px; padding: 20px; text-decoration: none; color: inherit; transition: border-color 0.2s; }
        .related-card:hover { border-color: #e94560; }
        .related-card h4 { color: #e94560; margin-top: 0; }
        .related-card p { font-size: 0.9rem; color: #888; margin-bottom: 0; }
        .related-section { margin-top: 50px; }
        .related-section h3 { color: #e94560; font-size: 1.4rem; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 8px; }"""


def ensure_css(html):
    """Add related CSS classes to the <style> block if not present."""
    has_related_section = ".related-section" in html
    has_related_articles = ".related-articles" in html

    if has_related_section and has_related_articles:
        return html  # already has all CSS

    if not has_related_articles and not has_related_section:
        # Need to add full CSS block
        # Try to add before </style>
        if "</style>" in html:
            css = RELATED_CSS_FULL
            html = html.replace("</style>", css + "\n    </style>", 1)
        elif '<link rel="stylesheet" href="/VideoCameraHoliday/assets/site-shell.css"' in html:
            # No <style> block, add one before the external CSS link
            style_block = f'<style>\n{RELATED_CSS_FULL}\n    </style>\n    '
            html = html.replace(
                '<link rel="stylesheet" href="/VideoCameraHoliday/assets/site-shell.css"',
                style_block + '<link rel="stylesheet" href="/VideoCameraHoliday/assets/site-shell.css"',
                1
            )
        elif "</head>" in html:
            style_block = f'  <style>\n{RELATED_CSS_FULL}\n  </style>\n'
            html = html.replace("</head>", style_block + "</head>", 1)
    elif not has_related_section:
        # Has related-articles but not related-section
        if "</style>" in html:
            html = html.replace("</style>", RELATED_CSS + "\n    </style>", 1)

    return html


def remove_old_more_city_interviews(html):
    """Remove the old 'More City Interviews' section if present."""
    # Pattern: <h2>🌍 More City Interviews</h2> ... up to the closing </div> before author-box
    # The old section looks like:
    #   <h2>🌍 More City Interviews</h2>
    #   <div class="related-articles">
    #     <a class="related-card" ...>...</a>
    #     ...
    #   </div>
    pattern = r'\s*<h2>🌍 More City Interviews</h2>\s*<div class="related-articles">.*?</div>\s*'
    html = re.sub(pattern, '', html, flags=re.DOTALL)
    return html


def insert_related_section(html, related_html):
    """Insert the related-content section before the author-box or before </article>."""
    # Try to find author-box
    author_patterns = [
        r'(\s*<!-- Interviewer bio -->\s*\n\s*<div class="author-box">)',
        r'(\s*<!-- author bio -->\s*\n\s*<div class="author-box">)',
        r'(\s*<div class="author-box">)',
        r'(\s*<div class="author-box" id="author">)',
    ]

    SECTION_MARKER = '<section class="related-section">'

    for pat in author_patterns:
        match = re.search(pat, html)
        if match:
            insert_point = match.start()
            # Check if there's already a related-section before the author-box
            before = html[:insert_point]
            if SECTION_MARKER in before:
                # Already has a related-section, skip insertion
                return html, True
            html = html[:insert_point] + '\n' + related_html + '\n' + html[insert_point:]
            return html, False

    # No author-box found, try to insert before </article>
    if "</article>" in html:
        idx = html.rfind("</article>")
        before = html[:idx]
        if SECTION_MARKER in before:
            return html, True
        html = html[:idx] + '\n' + related_html + '\n    ' + html[idx:]
        return html, False

    # Try before </main>
    if "</main>" in html:
        idx = html.rfind("</main>")
        before = html[:idx]
        if SECTION_MARKER in before:
            return html, True
        html = html[:idx] + '\n' + related_html + '\n  ' + html[idx:]
        return html, False

    return html, True  # skipped


def process_city_page(filepath):
    """Process a single city page. Returns (slug, status, message)."""
    filename = os.path.basename(filepath)
    slug = filename.replace("-interview-preview.html", "")

    if slug not in CITIES:
        return slug, "skip", "not in city database"
    if slug in DONE:
        return slug, "skip", "already done"

    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    # Check if already has the new related-section
    if 'class="related-section"' in html:
        return slug, "skip", "already has related-section"

    # Build the related-content section
    related_html = build_related_section(slug)

    # Remove old "More City Interviews" section
    html = remove_old_more_city_interviews(html)

    # Ensure CSS is present
    html = ensure_css(html)

    # Insert the related-content section
    html, skipped = insert_related_section(html, related_html)

    if skipped:
        return slug, "skip", "insertion point not found or already present"

    # Write the file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return slug, "done", "processed successfully"


def main():
    city_pages = sorted(glob.glob(os.path.join(CITY_DIR, "*-interview-preview.html")))

    done_count = 0
    skip_count = 0
    fail_count = 0
    results = []

    for filepath in city_pages:
        slug, status, msg = process_city_page(filepath)
        results.append((slug, status, msg))
        if status == "done":
            done_count += 1
        elif status == "skip":
            skip_count += 1
        else:
            fail_count += 1

    print(f"\n=== SUMMARY ===")
    print(f"Processed: {done_count} done, {skip_count} skipped, {fail_count} failed")
    print(f"\n--- Details ---")
    for slug, status, msg in results:
        if status != "skip" or "not in city database" in msg:
            print(f"  [{status:4s}] {slug}: {msg}")


if __name__ == "__main__":
    main()
