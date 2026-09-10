#!/usr/bin/env python3
"""
Article Organizer Script
Moves files from generated-content/[lang]/[subfolder]/ to [lang]/[subfolder]/ 
and cleans up the temporary directory.
"""

import os
import shutil
from pathlib import Path

SOURCE_DIR = Path("generated-content")

def organize_articles():
    if not SOURCE_DIR.exists():
        print("✅ No 'generated-content' folder found. Nothing to organize.")
        return

    print("🗂️ Starting article organization...")
    
    # Iterate through all language folders inside generated-content
    for lang_dir in SOURCE_DIR.iterdir():
        if lang_dir.is_dir():
            lang_code = lang_dir.name
            target_dir = Path(lang_code)
            
            # Create the target language folder at the root if it doesn't exist
            target_dir.mkdir(parents=True, exist_ok=True)
            print(f"  ➡️ Processing: {lang_code}")
            
            # Move all files and subdirectories to the root language folder
            for item in lang_dir.iterdir():
                target_path = target_dir / item.name
                
                # If a file with the same name exists, we skip or overwrite based on preference.
                # Here we safely overwrite to ensure the latest AI generation is used.
                if item.is_dir():
                    if target_path.exists():
                        shutil.rmtree(target_path)
                    shutil.copytree(item, target_path)
                else:
                    shutil.copy2(item, target_path)
                    
            print(f"  ✅ Successfully moved contents to '{lang_code}/'")

    # Clean up the temporary generated-content folder
    print("🧹 Cleaning up temporary 'generated-content' folder...")
    shutil.rmtree(SOURCE_DIR)
    print("🎉 Organization complete! Ready to commit.")

if __name__ == "__main__":
    organize_articles()
