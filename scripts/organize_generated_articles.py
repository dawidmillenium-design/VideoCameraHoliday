#!/usr/bin/env python3
"""
Article Organizer Script
Reads metadata files and moves generated HTML articles into their correct 
language and category folders.
"""

import os
import json
import shutil
from pathlib import Path

# Configuration
SOURCE_DIR = Path("generated-content")  # Where your AI generator saves files
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"  # Set to "false" to actually move files

# Folder mapping: language -> content_type -> folder_name
FOLDER_MAP = {
    "en-US": {
        "comparison": "comparisons",
        "review": "reviews",
        "buying-guide": "guides",
        "how-to": "how-to",
        "destination-guide": "destinations",
        "accessories": "accessories",
        "editing": "editing"
    },
    "es-ES": {
        "comparison": "es-ES/comparaciones",
        "review": "es-ES/resenas",
        "buying-guide": "es-ES/guias",
        "how-to": "es-ES/como-hacer",
        "destination-guide": "es-ES/destinos",
        "accessories": "es-ES/accesorios",
        "editing": "es-ES/edicion"
    },
    "fr-FR": {
        "comparison": "fr-FR/comparaisons",
        "review": "fr-FR/avis",
        "buying-guide": "fr-FR/guides",
        "how-to": "fr-FR/comment-faire",
        "destination-guide": "fr-FR/destinations",
        "accessories": "fr-FR/accessoires",
        "editing": "fr-FR/montage"
    },
    "de-DE": {
        "comparison": "de-DE/vergleiche",
        "review": "de-DE/testberichte",
        "buying-guide": "de-DE/ratgeber",
        "how-to": "de-DE/anleitung",
        "destination-guide": "de-DE/reiseziele",
        "accessories": "de-DE/zubehoer",
        "editing": "de-DE/bearbeitung"
    },
    "ja-JP": {
        "comparison": "ja-JP/hikaku",
        "review": "ja-JP/review",
        "buying-guide": "ja-JP/guide",
        "how-to": "ja-JP/how-to",
        "destination-guide": "ja-JP/destinations",
        "accessories": "ja-JP/accessories",
        "editing": "ja-JP/editing"
    },
    "ko-KR": {
        "comparison": "ko-KR/bigyo",
        "review": "ko-KR/review",
        "buying-guide": "ko-KR/guide",
        "how-to": "ko-KR/how-to",
        "destination-guide": "ko-KR/destinations",
        "accessories": "ko-KR/accessories",
        "editing": "ko-KR/editing"
    },
    "zh-CN": {
        "comparison": "zh-CN/bijiao",
        "review": "zh-CN/review",
        "buying-guide": "zh-CN/guide",
        "how-to": "zh-CN/how-to",
        "destination-guide": "zh-CN/destinations",
        "accessories": "zh-CN/accessories",
        "editing": "zh-CN/editing"
    },
    "pl-PL": {
        "comparison": "pl-PL/porownania",
        "review": "pl-PL/recenzje",
        "buying-guide": "pl-PL/poradniki",
        "how-to": "pl-PL/jak-to-zrobic",
        "destination-guide": "pl-PL/destynacje",
        "accessories": "pl-PL/akcesoria",
        "editing": "pl-PL/edycja"
    },
    "th-TH": {
        "comparison": "th-TH/khiebthieb",
        "review": "th-TH/review",
        "buying-guide": "th-TH/guide",
        "how-to": "th-TH/how-to",
        "destination-guide": "th-TH/destinations",
        "accessories": "th-TH/accessories",
        "editing": "th-TH/editing"
    },
    "it-IT": {
        "comparison": "it-IT/confronti",
        "review": "it-IT/recensioni",
        "buying-guide": "it-IT/guide",
        "how-to": "it-IT/come-fare",
        "destination-guide": "it-IT/destinazioni",
        "accessories": "it-IT/accessori",
        "editing": "it-IT/montaggio"
    }
}

def get_target_folder(language: str, content_type: str) -> str:
    """Get the target folder path for a given language and content type."""
    lang_map = FOLDER_MAP.get(language, {})
    return lang_map.get(content_type, f"{language}/misc")  # Fallback to misc if type unknown

def organize_articles():
    """Main function to scan metadata and move files."""
    print("🗂️ Starting Article Organization...")
    print("=" * 70)
    if DRY_RUN:
        print("⚠️ DRY RUN MODE - No files will be moved")
    
    if not SOURCE_DIR.exists():
        print(f"❌ Source directory not found: {SOURCE_DIR}")
        return
    
    # Find all metadata files
    metadata_files = list(SOURCE_DIR.rglob("*-metadata.json"))
    print(f"📊 Found {len(metadata_files)} metadata files to process")
    
    moved_count = 0
    skipped_count = 0
    error_count = 0
    
    for meta_file in metadata_files:
        try:
            # Read metadata
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            
            language = meta.get("language", "en-US")
            content_type = meta.get("content_type", "buying-guide")
            filename = meta.get("filename", meta_file.stem.replace("-metadata", "") + ".html")
            
            # Find the corresponding HTML file
            html_file = meta_file.parent / filename
            
            if not html_file.exists():
                print(f"️ HTML file not found for {meta_file.name}")
                skipped_count += 1
                continue
            
            # Determine target folder
            target_folder_name = get_target_folder(language, content_type)
            target_dir = Path(target_folder_name)
            target_dir.mkdir(parents=True, exist_ok=True)
            
            target_path = target_dir / filename
            
            if DRY_RUN:
                print(f"  [DRY RUN] Would move: {html_file} -> {target_path}")
            else:
                # Move the file
                shutil.move(str(html_file), str(target_path))
                print(f"  ✅ Moved: {html_file.name} -> {target_folder_name}/")
                
                # Optionally move the metadata file too (comment out if you want to keep them)
                # shutil.move(str(meta_file), str(target_dir / meta_file.name))
            
            moved_count += 1
            
        except Exception as e:
            print(f"❌ Error processing {meta_file}: {e}")
            error_count += 1
    
    print("\n" + "=" * 70)
    print("🎉 Organization Complete!")
    print(f"  ✅ Files Moved: {moved_count}")
    print(f"  ⚠️ Skipped: {skipped_count}")
    print(f"  ❌ Errors: {error_count}")
    
    if DRY_RUN:
        print("\n️ This was a DRY RUN. Set DRY_RUN=false to actually move files.")

if __name__ == "__main__":
    organize_articles()
