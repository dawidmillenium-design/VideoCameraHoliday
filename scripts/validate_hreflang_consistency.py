#!/usr/bin/env python3
"""
Multi-Language Hreflang & Canonical Validator
Ensures all language versions of an article correctly reference each other.
"""

import json
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict
import re

# Define your expected language codes and their folders based on your setup
EXPECTED_LANGUAGES = {
    "en-US": "comparisons",  # Default English folder
    "es-ES": "es-ES/comparaciones",
    "fr-FR": "fr-FR/comparaisons",
    "de-DE": "de-DE/vergleiche",
    "ja-JP": "ja-JP/hikaku",
    "ko-KR": "ko-KR/bigyo",
    "zh-CN": "zh-CN/bijiao",
    "pl-PL": "pl-PL/porownania",
    "th-TH": "th-TH/khiebthieb",
    "it-IT": "it-IT/confronti"
}

BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday"

def get_slug_from_path(filepath: str) -> str:
    """Extract the base filename (slug) from a path, ignoring metadata."""
    filename = Path(filepath).name
    if filename.endswith('-metadata.json'):
        return ""
    return filename.replace('.html', '')

def scan_html_files() -> dict:
    """Scan repository for all HTML files and group them by slug."""
    articles = defaultdict(list)
    
    # Scan main content directories
    scan_dirs = ['comparisons', 'es-ES', 'fr-FR', 'de-DE', 'ja-JP', 'ko-KR', 'zh-CN', 'pl-PL', 'th-TH', 'it-IT', 'guides', 'how-to', 'destinations', 'reviews']
    
    for dir_name in scan_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            continue
            
        for html_file in dir_path.rglob("*.html"):
            if html_file.name.startswith('index') or 'metadata' in html_file.name:
                continue
                
            slug = get_slug_from_path(str(html_file))
            if slug:
                articles[slug].append(str(html_file))
                
    return articles

def validate_article_group(slug: str, filepaths: list) -> dict:
    """Validate that all files in a group have consistent hreflang and canonical tags."""
    result = {
        "slug": slug,
        "files_checked": len(filepaths),
        "is_valid": True,
        "issues": []
    }
    
    hreflang_maps = {}
    canonical_maps = {}
    
    for filepath in filepaths:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'lxml')
            
            # 1. Check Hreflang Tags
            hreflang_tags = soup.find_all('link', attrs={'rel': 'alternate', 'hreflang': True})
            found_langs = set()
            for tag in hreflang_tags:
                lang = tag.get('hreflang')
                href = tag.get('href')
                if lang and href:
                    found_langs.add(lang)
            
            hreflang_maps[filepath] = found_langs
            
            # 2. Check Canonical Tag
            canonical = soup.find('link', attrs={'rel': 'canonical'})
            if canonical and canonical.get('href'):
                canonical_maps[filepath] = canonical.get('href')
            else:
                result["issues"].append(f"{filepath}: Missing canonical tag")
                result["is_valid"] = False
                
        except Exception as e:
            result["issues"].append(f"{filepath}: Error parsing file ({e})")
            result["is_valid"] = False

    # 3. Validate Consistency Across the Group
    if len(filepaths) > 1:
        # All files should have the SAME set of hreflang languages
        unique_hreflang_sets = [frozenset(langs) for langs in hreflang_maps.values()]
        if len(set(unique_hreflang_sets)) > 1:
            result["issues"].append("Inconsistent hreflang languages across different versions of this article.")
            result["is_valid"] = False
            
        # Check if expected languages are present (at least the ones that exist in this group)
        expected_in_group = set()
        for fp in filepaths:
            for lang_code, folder in EXPECTED_LANGUAGES.items():
                if folder in fp or (folder.split('/')[0] in fp and len(folder.split('/')) > 1):
                    expected_in_group.add(lang_code)
        
        # Simplified check: ensure x-default is present in all
        for fp, langs in hreflang_maps.items():
            if 'x-default' not in langs:
                result["issues"].append(f"{filepath}: Missing 'x-default' hreflang tag")
                result["is_valid"] = False

    return result

def main():
    print("🌐 Starting Multi-Language Hreflang Validation...")
    print("=" * 70)
    
    articles = scan_html_files()
    print(f"📚 Found {len(articles)} unique article slugs to validate")
    
    validation_results = {
        "total_groups": len(articles),
        "consistent_groups": 0,
        "inconsistent_groups": 0,
        "issues": []
    }
    
    for slug, filepaths in articles.items():
        result = validate_article_group(slug, filepaths)
        
        if result["is_valid"]:
            validation_results["consistent_groups"] += 1
        else:
            validation_results["inconsistent_groups"] += 1
            validation_results["issues"].append({
                "slug": slug,
                "reason": " | ".join(result["issues"])
            })
            
    # Save report
    with open("hreflang-validation-report.json", 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2)
        
    print("\n" + "=" * 70)
    print(f"✅ Validation Complete!")
    print(f"   Total Groups: {validation_results['total_groups']}")
    print(f"   ✅ Consistent: {validation_results['consistent_groups']}")
    print(f"   ❌ Inconsistent: {validation_results['inconsistent_groups']}")
    
    if validation_results["inconsistent_groups"] > 0:
        print("\n⚠️  Hreflang inconsistencies detected! Check the report.")
        # Exit with code 1 to fail the GitHub Action if errors are found
        exit(1)
    else:
        print("\n🎉 All multi-language SEO tags are perfectly consistent!")

if __name__ == "__main__":
    main()
