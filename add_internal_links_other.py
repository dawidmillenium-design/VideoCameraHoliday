#!/usr/bin/env python3
"""
Add internal linking sections to review, guide, destination, and comparison pages.
Each page gets related-content sections with cross-links to relevant pages.
"""

import os
import re
import glob

BASE = os.path.dirname(os.path.abspath(__file__))

# ─── SHARED CSS ───
RELATED_CSS = """        .related-articles { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 20px; margin: 30px 0; }
        .related-card { background: #111; border: 1px solid #333; border-radius: 12px; padding: 20px; text-decoration: none; color: inherit; transition: border-color 0.2s; }
        .related-card:hover { border-color: #e94560; }
        .related-card h4 { color: #e94560; margin-top: 0; }
        .related-card p { font-size: 1.0rem; color: #999; margin-bottom: 0; }
        .related-section { margin-top: 50px; }
        .related-section h3 { color: #e94560; font-size: 1.4rem; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 8px; }"""

# ─── CITY DATABASE (for linking) ───
CITIES = {
    "london": ("London", "🇬🇧", "Europe"),
    "paris": ("Paris", "🇫🇷", "Europe"),
    "berlin": ("Berlin", "🇩🇪", "Europe"),
    "amsterdam": ("Amsterdam", "🇳🇱", "Europe"),
    "rome": ("Rome", "🇮🇹", "Europe"),
    "barcelona": ("Barcelona", "🇪🇸", "Europe"),
    "lisbon": ("Lisbon", "🇵🇹", "Europe"),
    "prague": ("Prague", "🇨🇿", "Europe"),
    "vienna": ("Vienna", "🇦🇹", "Europe"),
    "budapest": ("Budapest", "🇭🇺", "Europe"),
    "athens": ("Athens", "🇬🇷", "Europe"),
    "moscow": ("Moscow", "🇷🇺", "Europe"),
    "istanbul": ("Istanbul", "🇹🇷", "Europe"),
    "tokyo": ("Tokyo", "🇯🇵", "Asia"),
    "bangkok": ("Bangkok", "🇹🇭", "Asia"),
    "beijing": ("Beijing", "🇨🇳", "Asia"),
    "seoul": ("Seoul", "🇰🇷", "Asia"),
    "shanghai": ("Shanghai", "🇨🇳", "Asia"),
    "singapore": ("Singapore", "🇸🇬", "Asia"),
    "hong-kong": ("Hong Kong", "🇭🇰", "Asia"),
    "dubai": ("Dubai", "🇦🇪", "Asia"),
    "delhi": ("Delhi", "🇮🇳", "Asia"),
    "mumbai": ("Mumbai", "🇮🇳", "Asia"),
    "jaipur": ("Jaipur", "🇮🇳", "Asia"),
    "hanoi": ("Hanoi", "🇻🇳", "Asia"),
    "ho-chi-minh": ("Ho Chi Minh City", "🇻🇳", "Asia"),
    "chiang-mai": ("Chiang Mai", "🇹🇭", "Asia"),
    "siem-reap": ("Siem Reap", "🇰🇭", "Asia"),
    "bali": ("Bali", "🇮🇩", "Asia"),
    "osaka": ("Osaka", "🇯🇵", "Asia"),
    "new-york-city": ("New York City", "🇺🇸", "Americas"),
    "mexico-city": ("Mexico City", "🇲🇽", "Americas"),
    "rio-de-janeiro": ("Rio de Janeiro", "🇧🇷", "Americas"),
    "buenos-aires": ("Buenos Aires", "🇦🇷", "Americas"),
    "cusco": ("Cusco", "🇵🇪", "Americas"),
    "cairo": ("Cairo", "🇪🇬", "Africa"),
    "cape-town": ("Cape Town", "🇿🇦", "Africa"),
    "nairobi": ("Nairobi", "🇰🇪", "Africa"),
    "marrakech": ("Marrakech", "🇲🇦", "Africa"),
}

# ─── REVIEW DATABASE ───
REVIEWS = {
    "sony-zv-1-ii-review.html": ("Sony ZV-1 II Review", "1-inch sensor vlogging compact for city breaks."),
    "dji-osmo-pocket-4p-review.html": ("DJI Osmo Pocket 4 Pro Review", "Ultimate compact gimbal camera for travel."),
    "fujifilm-x100vi-review.html": ("Fujifilm X100VI Review", "APS-C film simulations for street photography."),
    "gopro-hero-13-review.html": ("GoPro Hero 13 Review", "Rugged, waterproof action camera."),
    "gopro-hero-13-black-alps-hiking-companion.html": ("GoPro Hero 13 Alps Hiking", "Packing light for mountain adventures."),
    "sony-zv-e10-ii-night-market-review.html": ("Sony ZV-E10 II Night Market Review", "APS-C interchangeable lens for night markets."),
    "iphone-16-pro-video-review.html": ("iPhone 16 Pro Video Review", "Pro video with Action Mode stabilization."),
    "dji-osmo-action-5-review.html": ("DJI Osmo Action 5 Pro Review", "Rugged action camera with low-light performance."),
    "dji-osmo-action-6-review.html": ("DJI Osmo Action 6 Review", "Deep dive and beach test action camera."),
    "dji-osmo-pocket-3-review.html": ("DJI Osmo Pocket 3 Review", "Pocket gimbal camera with great low-light."),
    "insta360-x5-review.html": ("Insta360 X5 Review", "8K 360° camera for capturing everything."),
    "insta360-go-3s-hands-free-review.html": ("Insta360 GO 3S Review", "Hands-free feather-light POV camera."),
    "canon-eos-r50-v-creator-kit-review.html": ("Canon EOS R50 V Creator Kit Review", "Entry-level mirrorless with great AF."),
    "fujifilm-x-m5-travel-review.html": ("Fujifilm X-M5 Travel Review", "Compact APS-C with film sims for travel."),
    "nikon-z50-ii-creator-kit-review.html": ("Nikon Z50 II Creator Kit Review", "APS-C mirrorless with flip screen."),
    "om-system-om-3-travel-review.html": ("OM System OM-3 Travel Review", "MFT compact with IBIS and weather sealing."),
    "panasonic-lumix-s5ii-review.html": ("Panasonic Lumix S5II Review", "Full-frame mirrorless with Phase Hybrid AF."),
    "dji-mini-4-pro-review.html": ("DJI Mini 4 Pro Review", "Best travel drone under 249g."),
    "dji-air-3-review.html": ("DJI Air 3 Review", "Dual-camera drone for travel."),
    "dji-air-3-travel-photography-review.html": ("DJI Air 3 Travel Photography", "Is the Air 3 worth the weight?"),
    "canon-powershot-v10-review.html": ("Canon PowerShot V10 Review", "Pocket vlog camera with built-in stand."),
    "insta360-ace-pro-review.html": ("Insta360 Ace Pro Review", "AI-powered action camera with low-light."),
    "gopro-max-2-review.html": ("GoPro Max 2 Review", "360° simplicity, waterproof and reframable."),
    "samsung-galaxy-s25-ultra-video.html": ("Samsung Galaxy S25 Ultra Review", "Flagship phone with pro Nightography."),
    "budget-4k-camcorder-roundup.html": ("Budget 4K Camcorder Roundup", "Affordable 4K camcorders tested."),
    "pocket-cinema-cameras-2026-roundup.html": ("Pocket Cinema Cameras 2026", "Cinema-quality in your pocket."),
    "akaso-ek7000-pro-review.html": ("Akaso EK7000 Pro Review", "Budget action cam for travel."),
    "sony-zv-1-ii-finland-northern-lights-videography.html": ("Sony ZV-1 II Northern Lights", "Chasing aurora in Finland."),
    "sony-zv-1-ii-lisbon-cobblestones-stabilization-test.html": ("Sony ZV-1 II Lisbon Stabilization", "Real-world stabilization on cobblestones."),
    "DJI-Osmo-Pocket-4P-Bangkok.html": ("DJI Osmo Pocket 4P Bangkok", "Low-light street videography in Bangkok."),
    "best-travel-cameras-2026.html": ("Best Travel Cameras 2026", "Ultimate guide from Santorini to Alps."),
    "canon-powershot-v10-travel-review.html": ("Canon PowerShot V10 Travel Review", "Pocket vlog camera for travel."),
    "insta360-x4-review.html": ("Insta360 X4 Review", "5.7K 360° camera for travel video."),
}

# ─── GUIDE DATABASE ───
GUIDES = {
    "best-compact-cameras-city-breaks.html": ("Best Compact Cameras for City Breaks 2026", "8 top compacts tested on city breaks."),
    "best-holiday-video-cameras-2026.html": ("Best Holiday Video Cameras 2026", "10 tested picks for every budget."),
    "best-camera-southeast-asia.html": ("Best Cameras for Southeast Asia", "Top picks for humid tropical conditions."),
    "best-budget-holiday-camera-under-500.html": ("Best Holiday Cameras Under $500", "Great video cameras on a budget."),
    "best-vlogging-cameras-travel-2026.html": ("Best Vlogging Cameras for Travel 2026", "Top vlogging picks tested on the road."),
    "best-waterproof-cameras-beach.html": ("Best Waterproof Cameras for Beach", "Tested in salt and sand."),
    "best-camera-hiking-holidays.html": ("Best Cameras for Hiking Holidays", "Lightweight, rugged picks for trails."),
    "best-camera-ski-holidays.html": ("Best Cameras for Ski Holidays", "Cold-weather cameras for the slopes."),
    "best-camera-for-family-holidays.html": ("Best Camera for Family Holidays", "Easy cameras for family memories."),
    "best-camcorder-family-vacation-2026.html": ("Best Camcorder for Family Vacation", "Zoom and battery for family trips."),
    "best-camera-cruise-vacations-2026.html": ("Best Camera for Cruise Vacations", "Salt-proof compact picks."),
    "best-low-light-camera-evening-vacation.html": ("Best Low Light Camera for Evenings", "Night markets and sunset scenes."),
    "best-mirrorless-camera-travel-video-2026.html": ("Best Mirrorless for Travel Video 2026", "APS-C vs full frame."),
    "best-point-and-shoot-travel-video-2026.html": ("Best Point and Shoot for Travel", "No lens swaps needed."),
    "best-camera-safari-holiday-video-2026.html": ("Best Camera for Safari Video", "Zoom and durability for safari."),
    "best-cameras-african-safari-2026.html": ("Best Cameras for African Safaris 2026", "Zoom and durability tested."),
    "how-to-choose-video-camera-holiday.html": ("How to Choose a Holiday Video Camera", "2026 buyer's guide."),
    "travel-camera-checklist-2026.html": ("Travel Camera Checklist 2026", "Everything to pack before you fly."),
    "what-to-film-european-night-markets.html": ("What to Film at European Night Markets", "Night market filming techniques."),
    "film-travel-videos-without-crowds.html": ("Film Travel Videos Without Crowds", "7 pro crowd-free techniques."),
    "quiet-camera-recording-tourist-spots.html": ("Quiet Camera for Tourist Spots", "Discreet filming in churches and museums."),
    "one-bag-travel-filmmaker-gear-list-2026.html": ("One-Bag Travel Filmmaker Gear List", "Complete carry-on gear list."),
    "rent-vs-buy-travel-camera-gear-2026.html": ("Rent vs Buy Travel Camera Gear", "Cost calculator for renting."),
    "state-of-travel-cameras-2026.html": ("State of Travel Cameras 2026", "Big picture of travel video gear."),
    "ultimate-holiday-video-camera-setup.html": ("Ultimate Holiday Video Camera Setup", "Complete rig guide."),
    "best-travel-camera-external-mic-input.html": ("Best Travel Camera with Mic Input", "Cameras with external mic jacks."),
    "best-travel-camera-flip-screen-2026.html": ("Best Travel Camera with Flip Screen", "Vlogging selfie picks."),
    "best-vlogging-camera-beginners-2026.html": ("Best Vlogging Camera for Beginners", "Starter picks $300–$1000."),
    "best-camera-kids-record-vacations.html": ("Best Camera for Kids Vacations", "Kid-friendly picks."),
    "camera-gifts-for-travelers.html": ("Camera Gifts for Travelers", "Gift ideas for videographers."),
    "when-to-buy-travel-camera-cheapest.html": ("When to Buy a Travel Camera Cheapest", "Price cycle guide."),
    "best-hybrid-travel-camera-2026.html": ("Best Hybrid Travel Camera 2026", "Stills and video in one body."),
    "best-video-camera-picks-holiday-adventure.html": ("Best Video Camera for Adventure", "Adventure travel video picks."),
    "best-video-cameras-holiday-travel-2026.html": ("Best Video Cameras for Holiday Travel", "12 top picks tested."),
    "best-travel-cameras-winter-unesco-adventures.html": ("Best Cameras for Winter UNESCO", "Winter UNESCO site adventures."),
    "becoming-travel-filmmaker-career-guide-2026.html": ("Becoming a Travel Filmmaker", "Portfolio, clients, making it pay."),
    "what-camera-do-travel-youtubers-use.html": ("What Cameras Travel YouTubers Use", "2026 creator setups."),
    "small-video-camera-backpacking-2026.html": ("Small Video Camera for Backpacking", "Lightweight ultralight picks."),
    "best-budget-vlogging-camera-europe.html": ("Best Budget Vlogging Camera Europe", "Budget picks tested across Europe."),
    "filming-southeast-asia-gear-guide-2026.html": ("Filming Southeast Asia Gear Guide", "Ultimate gear guide for SEA."),
    "ultimate-spring-travel-camera-packing-checklist-2027.html": ("Spring Camera Packing Checklist 2027", "Complete spring trip packing list."),
    "ultimate-holiday-travel-camera-guide-zv1-ii-hero13-pocket4p.html": ("Ultimate Holiday Camera Guide", "ZV-1 II, Hero 13, or Pocket 4P?"),
    "best-camera-holiday-videos-under-300.html": ("Best Camera for Holiday Videos Under $300", "Budget picks under $300."),
    "best-compact-cameras-for-travel.html": ("Best Compact Cameras for Travel 2026", "Top travel compacts tested."),
    "best-travel-camera-insurance.html": ("Best Travel Camera Insurance 2026", "Complete insurance guide."),
    "best-waterproof-cameras-cenotes-mexico.html": ("Best Waterproof Cameras for Cenotes", "Underwater tested in Mexico."),
    "rent-vs-buy-travel-camera-gear-turist-2026.html": ("Rent vs Buy Travel Camera Gear", "2026 cost calculator."),
    "travel-video-camera-settings-beginners.html": ("Travel Video Camera Settings for Beginners", "Settings guide for beginners."),
}

# ─── DESTINATION DATABASE ───
DESTINATIONS = {
    "best-cameras-city-breaks.html": ("Best Cameras for City Breaks", "Urban travel photography guide."),
    "bangkok-camera-guide.html": ("Bangkok Travel Camera Guide", "Complete Bangkok filming guide."),
    "best-cameras-beach-holidays.html": ("Best Cameras for Beach Holidays", "Tested in sand, salt, and sun."),
    "best-cameras-ski-holidays.html": ("Best Cameras for Ski Holidays", "Cold-weather slope cameras."),
    "best-cameras-desert-travel.html": ("Best Cameras for Desert Travel", "Heat, dust, and sand gear."),
    "underwater-camera-guide.html": ("Underwater Camera Guide", "Snorkelling and diving gear."),
    "african-safari-camera-setup.html": ("African Safari Camera Setup", "Safari gear and settings guide."),
    "dubai-travel-guide.html": ("Dubai Travel Guide", "Culture, attractions, filming tips."),
    "vietnam-camera-guide.html": ("Vietnam Travel Camera Guide", "Best gear for Vietnam."),
    "camera-guide-machu-picchu.html": ("Machu Picchu Camera Guide", "Complete 2026 guide."),
    "camera-guide-southeast-asia-complete-2026.html": ("Southeast Asia Camera Guide", "Humidity, temples, night markets."),
    "japan-cherry-blossom-camera-guide-2026.html": ("Japan Cherry Blossom Guide", "Sakura season gear and timing."),
    "best-camera-japan-cherry-blossom.html": ("Best Camera for Japan Cherry Blossom", "Sakura season gear."),
    "best-cameras-african-safari-2026.html": ("Best Cameras for African Safaris", "Zoom and durability tested."),
    "gopro-hero-13-unesco-world-heritage-sites.html": ("GoPro Hero 13 at UNESCO Sites", "World heritage filming."),
    "waterproof-camera-cenotes-mexico.html": ("Waterproof Camera for Cenotes", "Underwater-tested for cenotes."),
    "insta360-x5-settings-bali-beach-clubs.html": ("Insta360 X5 Settings for Bali", "360 settings for beach clubs."),
    "low-light-camera-settings-da-nang.html": ("Low Light Settings for Da Nang", "Night markets and Dragon Bridge."),
    "protect-camera-bangkok-humidity.html": ("Protect Camera from Humidity", "Stop mold in tropical climates."),
    "galapagos-cruise-gear-packing-list.html": ("Galapagos Cruise Gear List", "Complete packing guide."),
    "year-in-review-5-travel-videography-lessons-bangkok-finland.html": ("5 Travel Videography Lessons", "Year in review Bangkok to Finland."),
    "action-camera-white-water-rafting.html": ("Action Camera for White Water Rafting", "Best picks for rapids."),
    "best-action-camera-semporna-diving.html": ("Best Action Camera for Semporna Diving", "Underwater diving tested."),
    "best-action-camera-white-water-rafting.html": ("Best Action Camera for Rafting", "White water tested."),
    "gopro-hero-13-black-underwater-maldives-snorkeling.html": ("GoPro Hero 13 Underwater Maldives", "Snorkeling the Maldives reefs."),
    "lisbon-budget-cinematic-b-roll-dji-osmo-pocket-4p.html": ("Lisbon Cinematic B-Roll on Budget", "Capturing Lisbon with DJI Pocket 4P."),
}

# ─── COMPARISON DATABASE ───
COMPARISONS = {
    "action-camera-vs-gimbal-camera.html": ("Action Camera vs Gimbal Camera", "Which form factor wins for travel?"),
    "budget-vs-premium-travel-cameras.html": ("Budget vs Premium Travel Cameras", "Is premium worth the extra cost?"),
    "canon-r50-vs-sony-zv-e10-ii-youtube.html": ("Canon R50 vs Sony ZV-E10 II", "Head-to-head for YouTube travel."),
    "dji-action-5-pro-vs-gopro-hero-13.html": ("DJI Action 5 Pro vs GoPro Hero 13", "Action camera showdown."),
    "dji-osmo-action-6-vs-gopro-hero-13.html": ("DJI Osmo Action 6 vs GoPro Hero 13", "Latest action cam comparison."),
    "dji-pocket-3-vs-gopro-hero-13.html": ("DJI Pocket 3 vs GoPro Hero 13", "Gimbal vs action for travel."),
    "gopro-hero-12-vs-akaso-brave-7.html": ("GoPro Hero 12 vs Akaso Brave 7", "Premium vs budget action cam."),
    "gopro-hero-13-black-vs-dji-osmo-pocket-4p-santorini-sunset.html": ("Hero 13 Black vs Pocket 4P Santorini", "Tested at Santorini sunset."),
    "gopro-hero-13-vs-sony-zv-1-ii.html": ("GoPro Hero 13 vs Sony ZV-1 II", "Action vs compact for travel."),
    "insta360-go-3s-vs-dji-action-5.html": ("Insta360 GO 3S vs DJI Action 5", "Tiny vs rugged action cam."),
    "insta360-x5-vs-gopro-max.html": ("Insta360 X5 vs GoPro Max", "8K vs 5.7K 360 comparison."),
    "iphone-16-pro-vs-dedicated-camera.html": ("iPhone 16 Pro vs Dedicated Camera", "Phone vs camera for travel video."),
    "iphone-16-pro-vs-dji-pocket-3.html": ("iPhone 16 Pro vs DJI Pocket 3", "Smartphone vs gimbal camera."),
    "kaso-ek7000-pro-vs-gopro-hero.html": ("Akaso EK7000 Pro vs GoPro Hero", "Budget vs premium action cam."),
    "peak-design-vs-blackrapid.html": ("Peak Design vs BlackRapid", "Camera strap comparison for travel."),
    "sony-a7cr-vs-fujifilm-x-t50.html": ("Sony A7CR vs Fujifilm X-T50", "Full-frame vs APS-C travel."),
    "action-4-vs-insta360-x5-scuba.html": ("Action 4 vs Insta360 X5 Scuba", "Underwater dive comparison."),
    "action-camera-vs-camcorder-travel-2026.html": ("Action Camera vs Camcorder Travel", "Which is better for 2026?"),
    "action-camera-white-water-rafting.html": ("Action Camera for White Water Rafting", "Best picks for rapids."),
    "best-action-camera-white-water-rafting.html": ("Best Action Camera for Rafting", "White water tested."),
    "best-action-camera-semporna-diving.html": ("Best Action Camera for Semporna Diving", "Underwater diving tested."),
}

# ─── HELPER: ensure CSS ───
def ensure_css(html):
    if '<section class="related-section">' in html:
        return html  # already has related section
    if ".related-articles" in html and ".related-section" in html:
        return html  # has CSS
    # Add CSS before </style> or create new style block
    if "</style>" in html:
        html = html.replace("</style>", RELATED_CSS + "\n    </style>", 1)
    elif "</head>" in html:
        html = html.replace("</head>", "    <style>\n" + RELATED_CSS + "\n    </style>\n</head>", 1)
    return html

# ─── HELPER: find insertion point ───
SECTION_MARKER = '<section class="related-section">'

def find_insertion_point(html):
    """Find the best insertion point for the related section. Returns (index, prefix, suffix) or None."""
    # Try author-box
    for pat in [
        r'(\s*<!-- [Ii]nterviewer bio -->\s*\n\s*<div class="author-box")',
        r'(\s*<!-- author bio -->\s*\n\s*<div class="author-box")',
        r'(\s*<div class="author-box")',
        r'(\s*<div class="author-box" id="author")',
    ]:
        m = re.search(pat, html)
        if m and SECTION_MARKER not in html[:m.start()]:
            return (m.start(), '\n', '\n')
    # Try </article>
    if "</article>" in html:
        idx = html.rfind("</article>")
        if SECTION_MARKER not in html[:idx]:
            return (idx, '\n        ', '\n    ')
    # Try before footer
    if '<footer' in html:
        idx = html.find('<footer')
        if SECTION_MARKER not in html[:idx]:
            return (idx, '\n\n    ', '\n\n    ')
    # Try </main>
    if "</main>" in html:
        idx = html.rfind("</main>")
        if SECTION_MARKER not in html[:idx]:
            return (idx, '\n    ', '\n  ')
    return None

# ─── HELPER: build card ───
def card(href, title, desc):
    return (f'                <a class="related-card" href="{href}">\n'
            f'                    <h4>{title}</h4>\n'
            f'                    <p>{desc}</p>\n'
            f'                </a>')

def build_section(heading, cards_html):
    return (f'        <!-- ===== RELATED CONTENT – IMPROVED INTERNAL LINKING ===== -->\n'
            f'        <section class="related-section">\n'
            f'\n'
            f'            <h3>{heading}</h3>\n'
            f'            <div class="related-articles">\n'
            f'{cards_html}\n'
            f'            </div>\n'
            f'\n'
            f'        </section>\n')

def build_multi_section(sections):
    """sections = list of (heading, [cards])"""
    parts = [
        f'        <!-- ===== RELATED CONTENT – IMPROVED INTERNAL LINKING ===== -->\n',
        f'        <section class="related-section">\n',
    ]
    for heading, cards in sections:
        parts.append(f'\n            <h3>{heading}</h3>\n')
        parts.append(f'            <div class="related-articles">\n')
        for c in cards:
            parts.append(c + '\n')
        parts.append(f'            </div>\n')
    parts.append(f'\n        </section>\n')
    return ''.join(parts)


# ─── REVIEW PAGE PROCESSING ───
# Categorize reviews by type for cross-linking
REVIEW_CATEGORIES = {
    "action": [
        "gopro-hero-13-review.html", "dji-osmo-action-5-review.html", "dji-osmo-action-6-review.html",
        "insta360-go-3s-hands-free-review.html", "insta360-ace-pro-review.html", "gopro-max-2-review.html",
        "akaso-ek7000-pro-review.html", "gopro-hero-13-black-alps-hiking-companion.html",
        "insta360-x5-review.html",
    ],
    "gimbal": [
        "dji-osmo-pocket-4p-review.html", "dji-osmo-pocket-3-review.html", "canon-powershot-v10-review.html",
    ],
    "vlog_mirrorless": [
        "sony-zv-1-ii-review.html", "sony-zv-e10-ii-night-market-review.html", "canon-eos-r50-v-creator-kit-review.html",
        "fujifilm-x-m5-travel-review.html", "nikon-z50-ii-creator-kit-review.html", "om-system-om-3-travel-review.html",
        "panasonic-lumix-s5ii-review.html", "fujifilm-x100vi-review.html",
    ],
    "drone": [
        "dji-mini-4-pro-review.html", "dji-air-3-review.html", "dji-air-3-travel-photography-review.html",
    ],
    "phone": [
        "iphone-16-pro-video-review.html", "samsung-galaxy-s25-ultra-video.html",
    ],
    "roundup": [
        "budget-4k-camcorder-roundup.html", "pocket-cinema-cameras-2026-roundup.html",
        "best-travel-cameras-2026.html",
    ],
    "destination_test": [
        "sony-zv-1-ii-finland-northern-lights-videography.html",
        "sony-zv-1-ii-lisbon-cobblestones-stabilization-test.html",
        "DJI-Osmo-Pocket-4P-Bangkok.html",
        "gopro-hero-13-black-alps-hiking-companion.html",
    ],
}

def get_review_category(filename):
    for cat, files in REVIEW_CATEGORIES.items():
        if filename in files:
            return cat
    return "vlog_mirrorless"  # default

# Related cities for each review category
REVIEW_CITY_MAP = {
    "action": [("bangkok", "asia"), ("bali", "asia"), ("rio-de-janeiro", "americas")],
    "gimbal": [("london", "europe"), ("paris", "europe"), ("tokyo", "asia")],
    "vlog_mirrorless": [("paris", "europe"), ("tokyo", "asia"), ("new-york-city", "americas")],
    "drone": [("cape-town", "africa"), ("dubai", "asia"), ("barcelona", "europe")],
    "phone": [("new-york-city", "americas"), ("london", "europe"), ("tokyo", "asia")],
    "roundup": [("london", "europe"), ("bangkok", "asia"), ("mexico-city", "americas")],
    "destination_test": [("bangkok", "asia"), ("lisbon", "europe"), ("london", "europe")],
}


def process_review_page(filepath):
    filename = os.path.basename(filepath)
    if filename in ("index.html", "index2.html"):
        return "skip", "index page"
    if filename not in REVIEWS:
        return "skip", "not in review database"

    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
    if SECTION_MARKER in html:
        return "skip", "already has related-section"

    cat = get_review_category(filename)

    # Related reviews (same category, exclude self)
    same_cat = [f for f in REVIEW_CATEGORIES.get(cat, []) if f != filename and f in REVIEWS]
    # If not enough, pull from other categories
    if len(same_cat) < 3:
        others = [f for f in REVIEWS if f != filename and f not in same_cat]
        same_cat = (same_cat + others)[:3]
    else:
        same_cat = same_cat[:3]

    review_cards = []
    for rslug in same_cat:
        rtitle, rdesc = REVIEWS[rslug]
        review_cards.append(card(f"/VideoCameraHoliday/reviews/{rslug}", rtitle, rdesc))

    # Related city interviews
    city_list = REVIEW_CITY_MAP.get(cat, REVIEW_CITY_MAP["vlog_mirrorless"])
    city_cards = []
    for cslug, _ in city_list[:3]:
        if cslug in CITIES:
            cname, cflag, cregion = CITIES[cslug]
            city_cards.append(card(
                f"/VideoCameraHoliday/city-through-the-lens/{cslug}-interview-preview.html",
                f"{cflag} {cname} Through the Lens",
                f"Local videographer guide to filming in {cname}."
            ))

    section_html = build_multi_section([
        ("📸 More Camera Reviews", review_cards),
        ("🌍 Related City Interviews", city_cards),
    ])

    html = ensure_css(html)
    ip = find_insertion_point(html)
    if ip:
        idx, prefix, suffix = ip
        html = html[:idx] + prefix + section_html + suffix + html[idx:]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        return "done", f"processed (cat={cat})"
    return "skip", "no insertion point"


# ─── GUIDE PAGE PROCESSING ───
def process_guide_page(filepath):
    filename = os.path.basename(filepath)
    if filename in ("index.html",):
        return "skip", "index page"
    if filename not in GUIDES:
        return "skip", "not in guide database"

    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
    if SECTION_MARKER in html:
        return "skip", "already has related-section"

    # Related guides (pick 3 different ones)
    other_guides = [g for g in GUIDES if g != filename]
    # Try to pick relevant ones based on title keywords
    title_lower = GUIDES[filename][0].lower()
    relevant = []
    for g in other_guides:
        gtitle = GUIDES[g][0].lower()
        # Simple keyword matching
        score = 0
        for kw in ["city", "beach", "ski", "hiking", "safari", "budget", "vlog", "waterproof",
                     "low-light", "family", "compact", "mirrorless", "drone", "night", "beginner"]:
            if kw in title_lower and kw in gtitle:
                score += 2
        if score > 0:
            relevant.append((score, g))
    relevant.sort(reverse=True)
    picked = [g for _, g in relevant[:3]]
    if len(picked) < 3:
        remaining = [g for g in other_guides if g not in picked]
        picked = (picked + remaining)[:3]

    guide_cards = []
    for gslug in picked:
        gtitle, gdesc = GUIDES[gslug]
        guide_cards.append(card(f"/VideoCameraHoliday/guides/{gslug}", gtitle, gdesc))

    # Related city interviews
    city_cards = []
    if "southeast" in title_lower or "asia" in title_lower:
        cities = [("bangkok", "Asia"), ("tokyo", "Asia"), ("hanoi", "Asia")]
    elif "safari" in title_lower or "africa" in title_lower:
        cities = [("cape-town", "Africa"), ("nairobi", "Africa"), ("cairo", "Africa")]
    elif "beach" in title_lower or "waterproof" in title_lower or "underwater" in title_lower:
        cities = [("bali", "Asia"), ("rio-de-janeiro", "Americas"), ("cape-town", "Africa")]
    elif "ski" in title_lower or "winter" in title_lower or "hiking" in title_lower:
        cities = [("london", "Europe"), ("moscow", "Europe"), ("barcelona", "Europe")]
    elif "europe" in title_lower or "night market" in title_lower:
        cities = [("london", "Europe"), ("paris", "Europe"), ("istanbul", "Europe")]
    else:
        cities = [("london", "Europe"), ("tokyo", "Asia"), ("new-york-city", "Americas")]

    for cslug, _ in cities[:3]:
        if cslug in CITIES:
            cname, cflag, cregion = CITIES[cslug]
            city_cards.append(card(
                f"/VideoCameraHoliday/city-through-the-lens/{cslug}-interview-preview.html",
                f"{cflag} {cname} Through the Lens",
                f"Local videographer guide to filming in {cname}."
            ))

    section_html = build_multi_section([
        ("📚 More Buying Guides", guide_cards),
        ("🌍 Related City Interviews", city_cards),
    ])

    html = ensure_css(html)
    ip = find_insertion_point(html)
    if ip:
        idx, prefix, suffix = ip
        html = html[:idx] + prefix + section_html + suffix + html[idx:]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        return "done", "processed"
    return "skip", "no insertion point"


# ─── DESTINATION PAGE PROCESSING ───
def process_destination_page(filepath):
    filename = os.path.basename(filepath)
    if filename in ("index.html", "index2.html", "readme.txt"):
        return "skip", "index/skip page"
    # Skip _diff files
    if "_diff" in filename:
        return "skip", "diff file"
    if filename not in DESTINATIONS:
        return "skip", "not in destination database"

    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
    if SECTION_MARKER in html:
        return "skip", "already has related-section"

    title_lower = DESTINATIONS[filename][0].lower()

    # Related destinations
    other_dests = [d for d in DESTINATIONS if d != filename and "_diff" not in d]
    relevant = []
    for d in other_dests:
        dtitle = DESTINATIONS[d][0].lower()
        score = 0
        for kw in ["beach", "ski", "desert", "underwater", "safari", "city", "bangkok",
                     "vietnam", "japan", "dubai", "machu", "bali", "cenotes", "galapagos"]:
            if kw in title_lower and kw in dtitle:
                score += 2
        if score > 0:
            relevant.append((score, d))
    relevant.sort(reverse=True)
    picked = [d for _, d in relevant[:3]]
    if len(picked) < 3:
        remaining = [d for d in other_dests if d not in picked]
        picked = (picked + remaining)[:3]

    dest_cards = []
    for dslug in picked:
        dtitle, ddesc = DESTINATIONS[dslug]
        dest_cards.append(card(f"/VideoCameraHoliday/destinations/{dslug}", dtitle, ddesc))

    # Related city interviews
    city_cards = []
    if "bangkok" in title_lower or "vietnam" in title_lower or "southeast" in title_lower:
        cities = [("bangkok", "Asia"), ("hanoi", "Asia"), ("ho-chi-minh", "Asia")]
    elif "dubai" in title_lower or "desert" in title_lower:
        cities = [("dubai", "Asia"), ("cairo", "Africa"), ("marrakech", "Africa")]
    elif "safari" in title_lower or "africa" in title_lower:
        cities = [("cape-town", "Africa"), ("nairobi", "Africa"), ("cairo", "Africa")]
    elif "japan" in title_lower or "cherry" in title_lower:
        cities = [("tokyo", "Asia"), ("osaka", "Asia"), ("seoul", "Asia")]
    elif "machu" in title_lower or "cusco" in title_lower or "cenotes" in title_lower:
        cities = [("cusco", "Americas"), ("mexico-city", "Americas"), ("lima", "Americas")]
    elif "bali" in title_lower or "beach" in title_lower or "underwater" in title_lower:
        cities = [("bali", "Asia"), ("rio-de-janeiro", "Americas"), ("cape-town", "Africa")]
    elif "ski" in title_lower:
        cities = [("london", "Europe"), ("moscow", "Europe"), ("budapest", "Europe")]
    elif "city" in title_lower:
        cities = [("london", "Europe"), ("paris", "Europe"), ("tokyo", "Asia")]
    else:
        cities = [("london", "Europe"), ("tokyo", "Asia"), ("new-york-city", "Americas")]

    for cslug, _ in cities[:3]:
        if cslug in CITIES:
            cname, cflag, cregion = CITIES[cslug]
            city_cards.append(card(
                f"/VideoCameraHoliday/city-through-the-lens/{cslug}-interview-preview.html",
                f"{cflag} {cname} Through the Lens",
                f"Local videographer guide to filming in {cname}."
            ))

    section_html = build_multi_section([
        ("🏖️ More Destination Guides", dest_cards),
        ("🌍 Related City Interviews", city_cards),
    ])

    html = ensure_css(html)
    ip = find_insertion_point(html)
    if ip:
        idx, prefix, suffix = ip
        html = html[:idx] + prefix + section_html + suffix + html[idx:]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        return "done", "processed"
    return "skip", "no insertion point"


# ─── COMPARISON PAGE PROCESSING ───
def process_comparison_page(filepath):
    filename = os.path.basename(filepath)
    if filename in ("index.html", "readme.txt"):
        return "skip", "index/skip page"
    if filename not in COMPARISONS:
        return "skip", "not in comparison database"

    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
    if SECTION_MARKER in html:
        return "skip", "already has related-section"

    title_lower = COMPARISONS[filename][0].lower()

    # Related reviews — extract camera names from comparison title and match
    review_cards = []
    matched_reviews = []
    for rslug, (rtitle, rdesc) in REVIEWS.items():
        rtitle_l = rtitle.lower()
        # Check if any significant word from the comparison title appears in the review title
        comp_words = set(re.findall(r'\b\w+\b', title_lower)) - {"vs", "the", "for", "a", "an", "and", "or", "camera", "cameras", "review", "travel", "video"}
        review_words = set(re.findall(r'\b\w+\b', rtitle_l)) - {"vs", "the", "for", "a", "an", "and", "or", "camera", "cameras", "review", "travel", "video"}
        if comp_words & review_words:
            matched_reviews.append(rslug)

    if len(matched_reviews) < 3:
        # Add some default popular reviews
        defaults = ["dji-osmo-pocket-4p-review.html", "gopro-hero-13-review.html", "sony-zv-1-ii-review.html",
                      "fujifilm-x100vi-review.html", "iphone-16-pro-video-review.html"]
        for d in defaults:
            if d not in matched_reviews and d in REVIEWS:
                matched_reviews.append(d)
    matched_reviews = matched_reviews[:3]

    for rslug in matched_reviews:
        rtitle, rdesc = REVIEWS[rslug]
        review_cards.append(card(f"/VideoCameraHoliday/reviews/{rslug}", rtitle, rdesc))

    # Related comparisons
    other_comps = [c for c in COMPARISONS if c != filename]
    relevant = []
    for c in other_comps:
        ctitle = COMPARISONS[c][0].lower()
        score = 0
        for kw in ["action", "gimbal", "gopro", "dji", "iphone", "budget", "360", "underwater",
                     "pocket", "sony", "canon", "fujifilm", "drone", "camcorder"]:
            if kw in title_lower and kw in ctitle:
                score += 2
        if score > 0:
            relevant.append((score, c))
    relevant.sort(reverse=True)
    picked = [c for _, c in relevant[:3]]
    if len(picked) < 3:
        remaining = [c for c in other_comps if c not in picked]
        picked = (picked + remaining)[:3]

    comp_cards = []
    for cslug in picked:
        ctitle, cdesc = COMPARISONS[cslug]
        comp_cards.append(card(f"/VideoCameraHoliday/comparisons/{cslug}", ctitle, cdesc))

    section_html = build_multi_section([
        ("📸 Related Reviews", review_cards),
        ("⚔️ More Camera Comparisons", comp_cards),
    ])

    html = ensure_css(html)
    ip = find_insertion_point(html)
    if ip:
        idx, prefix, suffix = ip
        html = html[:idx] + prefix + section_html + suffix + html[idx:]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        return "done", "processed"
    return "skip", "no insertion point"


def main():
    sections = [
        ("reviews", os.path.join(BASE, "reviews"), process_review_page),
        ("guides", os.path.join(BASE, "guides"), process_guide_page),
        ("destinations", os.path.join(BASE, "destinations"), process_destination_page),
        ("comparisons", os.path.join(BASE, "comparisons"), process_comparison_page),
    ]

    for section_name, section_dir, processor in sections:
        pages = sorted(glob.glob(os.path.join(section_dir, "*.html")))
        done = skip = 0
        details = []
        for p in pages:
            status, msg = processor(p)
            if status == "done":
                done += 1
            else:
                skip += 1
                if "not in" in msg or "no insertion" in msg:
                    details.append(f"  [skip] {os.path.basename(p)}: {msg}")
        print(f"\n=== {section_name.upper()} ===")
        print(f"  {done} done, {skip} skipped")
        for d in details:
            print(d)


if __name__ == "__main__":
    main()
