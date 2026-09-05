#!/usr/bin/env python3
import os
import re
import json

# City data for the 23 remaining problematic cities (including Beijing which we skip)
CITY_DATA = {
    "ahmedabad": {
        "name": "Ahmedabad",
        "country": "India",
        "landmarks": ["Sabarmati Ashram", "Akshardham Temple", "Old City (Pols)"],
        "airport": "Sardar Vallabhbhai Patel International Airport (AMD)",
        "weather": "Hot dry climate, summer temps up to 45°C, monsoon June-September",
        "tips": "Modest dress for temples, best light November-February, avoid midday heat"
    },
    "baghdad": {
        "name": "Baghdad",
        "country": "Iraq",
        "landmarks": ["Al-Mustansiriya University", "Mutanabbi Street", "Tigris River"],
        "airport": "Baghdad International Airport (BGW)",
        "weather": "Extreme summer heat (50°C+), mild winters, dust storms common",
        "tips": "Security considerations, filming permits required, respect local customs"
    },
    "bangalore": {
        "name": "Bangalore",
        "country": "India",
        "landmarks": ["Cubbon Park", "Bangalore Palace", "KR Market"],
        "airport": "Kempegowda International Airport (BLR)",
        "weather": "Moderate year-round, monsoon May-October, pleasant December-February",
        "tips": "Tech hub with modern infrastructure, traffic challenges, garden city aesthetic"
    },
    "chennai": {
        "name": "Chennai",
        "country": "India",
        "landmarks": ["Marina Beach", "Kapaleeshwarar Temple", "Fort St. George"],
        "airport": "Chennai International Airport (MAA)",
        "weather": "Hot humid climate, monsoon October-December, summer temps 40°C+",
        "tips": "Conservative dress code, temple filming restrictions, coastal lighting"
    },
    "dongguan": {
        "name": "Dongguan",
        "country": "China",
        "landmarks": ["Keyuan Garden", "Humen Bridge", "Songshan Lake"],
        "airport": "Guangzhou Baiyun (CAN) or Shenzhen Bao'an (SZX)",
        "weather": "Subtropical, hot humid summers, mild winters, typhoon season",
        "tips": "Manufacturing hub, modern infrastructure, permit requirements for drones"
    },
    "foshan": {
        "name": "Foshan",
        "country": "China",
        "landmarks": ["Ancestral Temple", "Nanfeng Kiln", "Xiqiao Mountain"],
        "airport": "Guangzhou Baiyun (CAN) or Foshan Shadi (FUO)",
        "weather": "Subtropical monsoon, hot humid summers, mild dry winters",
        "tips": "Martial arts heritage, ceramic culture, Greater Bay Area access"
    },
    "guangzhou": {
        "name": "Guangzhou",
        "country": "China",
        "landmarks": ["Canton Tower", "Chen Clan Ancestral Hall", "Pearl River"],
        "airport": "Guangzhou Baiyun International Airport (CAN)",
        "weather": "Subtropical, hot humid summers, mild winters, typhoon risk",
        "tips": "Cantonese culture, food capital, modern skyline vs old town contrast"
    },
    "hangzhou": {
        "name": "Hangzhou",
        "country": "China",
        "landmarks": ["West Lake", "Lingyin Temple", "Grand Canal"],
        "airport": "Hangzhou Xiaoshan International Airport (HGH)",
        "weather": "Four distinct seasons, plum rain season June-July, autumn ideal",
        "tips": "Historic scenic beauty, tech hub (Alibaba), poetic landscape filming"
    },
    "hong-kong": {
        "name": "Hong Kong",
        "country": "China (SAR)",
        "landmarks": ["Victoria Peak", "Tsim Sha Tsui Promenade", "Tai O Fishing Village"],
        "airport": "Hong Kong International Airport (HKG)",
        "weather": "Subtropical, hot humid summers, mild winters, typhoon season",
        "tips": "Drone restrictions strict, dense urban canyons, neon night photography"
    },
    "hyderabad": {
        "name": "Hyderabad",
        "country": "India",
        "landmarks": ["Charminar", "Golconda Fort", "Ramoji Film City"],
        "airport": "Rajiv Gandhi International Airport (HYD)",
        "weather": "Hot semi-arid, summer 40°C+, monsoon July-September",
        "tips": "Film city access, Nizam heritage, biryani culture, tech corridor"
    },
    "kinshasa": {
        "name": "Kinshasa",
        "country": "DR Congo",
        "landmarks": ["Congo River", "Kinshasa Fine Arts Academy", "Marché de la Liberté"],
        "airport": "N'djili International Airport (FIH)",
        "weather": "Tropical wet/dry, rainy season October-May, hot year-round",
        "tips": "Music capital of Africa, river scenes, vibrant street life"
    },
    "lagos": {
        "name": "Lagos",
        "country": "Nigeria",
        "landmarks": ["Lekki Conservation Centre", "National Theatre", "Tafawa Balewa Square"],
        "airport": "Murtala Muhammed International Airport (LOS)",
        "weather": "Tropical, rainy season April-October, hot humid year-round",
        "tips": "Nollywood hub, Afrobeat culture, lagoon scenes, traffic considerations"
    },
    "luanda": {
        "name": "Luanda",
        "country": "Angola",
        "landmarks": ["Fortaleza de São Miguel", "Ilha do Luanda", "Agostinho Neto Mausoleum"],
        "airport": "Quatro de Fevereiro Airport (LAD)",
        "weather": "Hot semi-arid, rainy season November-April, coastal breeze",
        "tips": "Portuguese colonial architecture, Atlantic coastline, emerging film scene"
    },
    "moscow": {
        "name": "Moscow",
        "country": "Russia",
        "landmarks": ["Red Square", "Saint Basil's Cathedral", "Moscow Metro"],
        "airport": "Sheremetyevo (SVO), Domodedovo (DME), or Vnukovo (VKO)",
        "weather": "Continental, cold winters (-20°C), warm summers, snow Nov-March",
        "tips": "Metro filming requires permit, winter golden hour short, grand architecture"
    },
    "nagoya": {
        "name": "Nagoya",
        "country": "Japan",
        "landmarks": ["Nagoya Castle", "Atsuta Shrine", "Toyota Commemorative Museum"],
        "airport": "Chubu Centrair International Airport (NGO)",
        "weather": "Four seasons, hot humid summers, cool winters, cherry spring",
        "tips": "Industrial heartland, castle reconstruction, samurai heritage"
    },
    "nanjing": {
        "name": "Nanjing",
        "country": "China",
        "landmarks": ["Sun Yat-sen Mausoleum", "Confucius Temple", "Yangtze River Bridge"],
        "airport": "Nanjing Lukou International Airport (NKG)",
        "weather": "Four seasons, hot summers, cold damp winters, plum rain June",
        "tips": "Ancient capital history, memorial halls, Yangtze scenes"
    },
    "riyadh": {
        "name": "Riyadh",
        "country": "Saudi Arabia",
        "landmarks": ["Kingdom Centre", "Diriyah (UNESCO)", "Al Masmak Fortress"],
        "airport": "King Khalid International Airport (RUH)",
        "weather": "Extreme desert heat (45°C+), cool winters, no rain",
        "tips": "Conservative dress, Ramadan considerations, Vision 2030 modernization"
    },
    "shenyang": {
        "name": "Shenyang",
        "country": "China",
        "landmarks": ["Shenyang Imperial Palace", "Marshal Zhang's Mansion", "Beiling Park"],
        "airport": "Shenyang Taoxian International Airport (SHE)",
        "weather": "Continental monsoon, cold dry winters, hot humid summers",
        "tips": "Manchu heritage, industrial northeast, imperial history"
    },
    "shenzhen": {
        "name": "Shenzhen",
        "country": "China",
        "landmarks": ["Ping An Finance Centre", "Window of the World", "Dameisha Beach"],
        "airport": "Shenzhen Bao'an International Airport (SZX)",
        "weather": "Subtropical, hot humid summers, mild winters, typhoon season",
        "tips": "Tech innovation hub, modern architecture, rapid development story"
    },
    "tehran": {
        "name": "Tehran",
        "country": "Iran",
        "landmarks": ["Golestan Palace", "Azadi Tower", "Grand Bazaar"],
        "airport": "Imam Khomeini International Airport (IKA)",
        "weather": "Semi-arid, hot dry summers, cold winters, mountain backdrop",
        "tips": "Persian architecture, bazaar filming etiquette, Alborz mountains"
    },
    "tianjin": {
        "name": "Tianjin",
        "country": "China",
        "landmarks": ["Tianjin Eye", "Ancient Culture Street", "Haihe River"],
        "airport": "Tianjin Binhai International Airport (TSN)",
        "weather": "Continental monsoon, hot summers, cold dry winters",
        "tips": "Colonial architecture, river scenes, Beijing alternative"
    },
    "xian": {
        "name": "Xi'an",
        "country": "China",
        "landmarks": ["Terracotta Army", "City Wall", "Muslim Quarter"],
        "airport": "Xi'an Xianyang International Airport (XIY)",
        "weather": "Continental, hot summers, cold dry winters, dust in spring",
        "tips": "Ancient capital, terracotta filming rules, Silk Road heritage"
    }
}

def fix_city_file(city_key, data):
    filepath = f"/workspace/city-through-the-lens/{city_key}-interview-preview.html"
    
    if not os.path.exists(filepath):
        print(f"⚠️ File not found: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace H1 header
    old_h1_pattern = r'<h1>Beijing Filming Guide.*?</h1>'
    new_h1 = f'<h1>{data["name"]} Filming Guide: Capturing {data["landmarks"][0]} & Local Life</h1>'
    content = re.sub(old_h1_pattern, new_h1, content, flags=re.IGNORECASE | re.DOTALL)
    
    # Replace any Forbidden City mentions
    content = re.sub(r'Forbidden City', data['landmarks'][0], content, flags=re.IGNORECASE)
    content = re.sub(r'Temple of Heaven', data['landmarks'][1] if len(data['landmarks']) > 1 else 'local temples', content, flags=re.IGNORECASE)
    content = re.sub(r'PEK airport|Beijing Capital.*?Airport', data['airport'], content, flags=re.IGNORECASE)
    content = re.sub(r'dust storms.*?(from Mongolia)?', 'local weather patterns', content, flags=re.IGNORECASE)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed: {city_key}")
    return True

# Skip beijing
cities_to_fix = [k for k in CITY_DATA.keys()]

print("🔧 Starting fix for remaining cities...\n")
fixed_count = 0
for city_key in cities_to_fix:
    if fix_city_file(city_key, CITY_DATA[city_key]):
        fixed_count += 1

print(f"\n✅ Completed: {fixed_count}/{len(cities_to_fix)} files fixed")
