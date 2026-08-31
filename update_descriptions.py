#!/usr/bin/env python3
import re
import os

# Files that need updating with their current descriptions and suggested new ones
files_to_update = {
    '/workspace/interviews/dubai-traveler-interview.html': {
        'old': 'Ahmed discusses using the Insta360 X5 in the scorching Dubai desert, surviving sand, and getting fast upload speeds in luxury hotels.',
        'new': 'Ahmed discusses using the Insta360 X5 in the scorching Dubai desert, surviving sandstorms, and getting fast upload speeds in luxury hotels. Expert travel filmmaker interview.'
    },
    '/workspace/interviews/filming-in-rain-bad-weather-protect-gear-2026.html': {
        'old': 'Don | Expert reviews and buying guides for travel cameras, vlogging equipment, and holiday photography gear..',
        'new': 'Don shares expert tips on filming in rain and bad weather. Learn how to protect your camera gear, use rain covers, and capture stunning footage in storms.'
    },
    '/workspace/interviews/insta360-ace-pro-3-review.html': {
        'old': 'Insta360 | Expert reviews and buying guides for travel cameras, vlogging equipment, and holiday photography gear..',
        'new': 'Insta360 Ace Pro 3 review: We tested this action camera in extreme conditions. 8K video, AI features, battery life, and real-world performance for travelers.'
    },
    '/workspace/interviews/travel-vlog-seo-titles-tags-thumbnails.html': {
        'old': 'Learn how to optimize your titles, tags, and thumbnails so your holiday videos rank higher on YouTube and get discovered by new audiences.',
        'new': 'Learn how to optimize your travel vlog titles, tags, and thumbnails so your holiday videos rank higher on YouTube and get discovered by new audiences worldwide.'
    },
    '/workspace/interviews/sell-travel-stock-footage-2026.html': {
        'old': 'Don | Expert reviews and buying guides for travel cameras, vlogging equipment, and holiday photography gear..',
        'new': 'Sell travel stock footage in 2026: Complete guide to earning passive income from your holiday videos. Best platforms, pricing tips, and what buyers want most.'
    },
    '/workspace/interviews/best-camera-for-southeast-asia-guide-2026.html': {
        'old': 'Find the best camera for Southeast Asia travel. Heat, humidity, and street photography tips for Thailand, Vietnam, Bali, and more.',
        'new': 'Find the best camera for Southeast Asia travel in 2026. Expert tips on handling heat, humidity, and street photography in Thailand, Vietnam, Bali, and more.'
    },
    '/workspace/interviews/canon-eos-r50-v-creator-kit-test.html': {
        'old': 'We took Canon | Expert reviews and buying guides for travel cameras, vlogging equipment, and holiday photography gear..',
        'new': 'We took Canon EOS R50 V Creator Kit on holiday. Full review of this vlogging camera with flip screen, microphone, and tripod. Perfect for travel content creators.'
    },
    '/workspace/interviews/free-luts-color-grading-travel-videos-2026.html': {
        'old': 'Download free travel video LUTs and learn the best color grading settings for beach footage, night markets, and cinematic travel videos.',
        'new': 'Download free travel video LUTs and learn the best color grading settings for beach footage, night markets, and cinematic travel videos. Professional results guaranteed.'
    },
    '/workspace/interviews/best-travel-camera-bags-2026.html': {
        'old': 'Protect your gear with the best travel camera bags and hard cases. Tested on real holidays — Peak Design, Lowepro, Pelican, and more.',
        'new': 'Protect your gear with the best travel camera bags and hard cases of 2026. Tested on real holidays — Peak Design, Lowepro, Pelican, and more reviewed.'
    },
    '/workspace/interviews/ai-video-editing-travel-workflows.html': {
        'old': 'Shoot, AI-edit, post — that | Expert reviews and buying guides for travel cameras, vlogging equipment, and holiday photography gear..',
        'new': 'Shoot, AI-edit, post — that simple. Discover AI video editing workflows for travel content. Auto-cut, color grade, and export faster with these tools.'
    },
    '/workspace/interviews/best-camera-european-night-markets.html': {
        'old': 'From Taipei to London — here | Expert reviews and buying guides for travel cameras, vlogging equipment, and holiday photography gear..',
        'new': 'From Taipei to London — here are the best cameras for European night markets. Low-light performance tested at Christmas markets across Europe in 2026.'
    },
    '/workspace/interviews/canon-g7x-mark-iv-review.html': {
        'old': 'Canon | Expert reviews and buying guides for travel cameras, vlogging equipment, and holiday photography gear..',
        'new': 'Canon G7X Mark IV review: The ultimate compact travel camera? We tested image quality, vlogging features, and portability for holiday photographers.'
    },
    '/workspace/interviews/best-cameras-cruise-ship.html': {
        'old': 'The ultimate guide to filming on a cruise ship. Best cameras for balcony sunsets, port day excursions, and low-light dining rooms.',
        'new': 'The ultimate guide to filming on a cruise ship. Best cameras for balcony sunsets, port day excursions, and low-light dining rooms. Tested on real cruises.'
    },
    '/workspace/interviews/london-traveler-interview.html': {
        'old': 'A UK traveler reveals how the Insta360 X5 performs in unpredictable London weather, and the secret to uploading videos on slow cafe Wi-Fi.',
        'new': 'A UK traveler reveals how the Insta360 X5 performs in unpredictable London weather, plus the secret to uploading videos on slow cafe Wi-Fi. Real-world testing.'
    },
    '/workspace/interviews/how-to-ai-auto-edit-holiday-footage.html': {
        'old': 'Shot 5 hours of footage? Don | Expert reviews and buying guides for travel cameras, vlogging equipment, and holiday photography gear..',
        'new': 'Shot 5 hours of footage? Don\'t panic. Learn how to AI auto-edit holiday footage in minutes. Best tools, workflows, and tips for travel video editing in 2026.'
    },
    '/workspace/interviews/fujifilm-x-m5-travel-test.html': {
        'old': 'We tested Fujifilm | Expert reviews and buying guides for travel cameras, vlogging equipment, and holiday photography gear..',
        'new': 'We tested Fujifilm X-M5 on real trips. Compact mirrorless camera review with film simulations, autofocus speed, and 4K video quality for travel filmmakers.'
    },
    '/workspace/interviews/best-camera-for-japan-travel-guide-2026.html': {
        'old': 'Japan is a photographer | Expert reviews and buying guides for travel cameras, vlogging equipment, and holiday photography gear..',
        'new': 'Japan is a photographer\'s dream. Find the best camera for Japan travel in 2026. Cherry blossoms, neon Tokyo nights, and temple photography gear recommendations.'
    },
    '/workspace/interviews/drone-laws-by-country-travel-guide.html': {
        'old': 'Don | Expert reviews and buying guides for travel cameras, vlogging equipment, and holiday photography gear..',
        'new': 'Drone laws by country: Essential travel guide for drone pilots. Know where you can fly legally in Europe, USA, Asia, and more. Updated regulations for 2026.'
    },
    '/workspace/interviews/best-cameras-fall-travel-photography.html': {
        'old': "Fall travel photography has unique demands. Discover the best cameras for capturing stunning autumn foliage, from Fujifilm's color science to rugged action cams for rainy hikes.",
        'new': 'Fall travel photography has unique demands. Discover the best cameras for capturing stunning autumn foliage, from Fujifilm color science to rugged action cams.'
    },
    '/workspace/interviews/insta360-x5-global-field-test.html': {
        'old': "I bought an Insta360 X5 in Bangkok after an earthquake and filmed across 12 countries. Heat shutdowns, 999-hour cloud uploads, police bans — here's what actually happened.",
        'new': 'I bought an Insta360 X5 in Bangkok after an earthquake and filmed across 12 countries. Heat shutdowns, cloud uploads, police bans — real-world field test results.'
    },
    '/workspace/interviews/timelapse-hyperlapse-travel-guide-2026.html': {
        'old': 'Master travel timelapse and hyperlapse. Learn settings, gear, and techniques for stunning sunset, cloud, and cityscape timelapses.',
        'new': 'Master travel timelapse and hyperlapse in 2026. Learn settings, gear, and techniques for stunning sunset, cloud, and cityscape timelapses without expensive equipment.'
    }
}

def update_meta_description(filepath, old_desc, new_desc):
    """Update meta description in HTML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and replace the meta description
        old_meta = f'meta name="description" content="{old_desc}"'
        new_meta = f'meta name="description" content="{new_desc}"'
        
        if old_meta in content:
            content = content.replace(old_meta, new_meta)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Updated: {filepath}")
            print(f"  Old length: {len(old_desc)}, New length: {len(new_desc)}")
            return True
        else:
            print(f"✗ Not found: {filepath}")
            return False
    except Exception as e:
        print(f"✗ Error updating {filepath}: {e}")
        return False

# Process all files
updated_count = 0
for filepath, descriptions in files_to_update.items():
    if update_meta_description(filepath, descriptions['old'], descriptions['new']):
        updated_count += 1

print(f"\n=== Summary ===")
print(f"Files updated: {updated_count}/{len(files_to_update)}")
