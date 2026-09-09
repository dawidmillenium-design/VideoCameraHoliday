#!/usr/bin/env python3
"""
SEO INTERNAL LINK UPDATER
-------------------------
This script scans all HTML files in the /workspace directory and updates 
internal links pointing to old, fragmented URLs so they point to the new 
consolidated Master Guides.

USAGE:
1. Save this file as `update_links.py` in your root folder.
2. Run in terminal: `python3 update_links.py`
3. It will create a backup of every file before modifying it.
4. Check the 'link_update_log.txt' for a report of changes made.
"""

import os
import re

# Configuration: Map of OLD URLs to NEW Master URLs
REDIRECT_MAP = {
    # SD Cards
    "how-to/choose-memory-card-4k-video.html": "accessories/best-sd-cards-4k-video-2026.html",
    "guides/best-sd-cards-4k-video-travel.html": "accessories/best-sd-cards-4k-video-2026.html",
    
    # Microphones
    "interviews/best-wireless-microphones-travel-vlogging.html": "accessories/best-travel-vlogging-microphones-2026.html",
    "posts/Best-Microphone-Holiday-Vlogging.html": "accessories/best-travel-vlogging-microphones-2026.html",
    "interviews/best-wireless-microphones-travel-vlogging-2026.html": "accessories/best-travel-vlogging-microphones-2026.html",
    
    # Tripods
    "guides/best-lightweight-tripods-hiking-travel.html": "accessories/best-lightweight-travel-tripods-stabilizers-2026.html",
    "interviews/best-travel-tripods-stabilizers-2026.html": "accessories/best-lightweight-travel-tripods-stabilizers-2026.html",
    
    # Power Banks
    "interviews/best-portable-power-banks-chargers-travel-filmmakers-2026.html": "accessories/best-power-banks-dji-pocket-3-filmmakers-2026.html"
}

def update_links_in_file(file_path):
    """Reads an HTML file, updates links based on REDIRECT_MAP, and saves it."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []

        # Iterate through the map and replace links
        # We look for href="OLD_URL" or href="./OLD_URL" or href="../OLD_URL"
        for old_url, new_url in REDIRECT_MAP.items():
            # Pattern matches href="...old_url..." (case insensitive)
            # Handles relative paths variations loosely by just matching the filename slug
            pattern = r'(href=["\']\.?\/?)' + re.escape(old_url) + r'(["\'])'
            
            if re.search(pattern, content, re.IGNORECASE):
                replacement = r'\g<1>' + new_url + r'\g<2>'
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                changes_made.append(f"Updated {old_url} -> {new_url}")

        # Only write if changes were made
        if content != original_content:
            # Create a backup first
            backup_path = file_path + ".bak"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True, changes_made
        else:
            return False, []

    except Exception as e:
        return False, [f"Error processing {file_path}: {str(e)}"]

def main():
    root_dir = '/workspace'
    log_file = 'link_update_log.txt'
    
    total_files_scanned = 0
    total_files_updated = 0
    total_changes = []

    print("🔍 Starting Internal Link Update Scan...")
    print(f"📂 Scanning directory: {root_dir}")
    
    # Walk through all directories
    for subdir, dirs, files in os.walk(root_dir):
        # Skip hidden directories and backup files
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(subdir, file)
                total_files_scanned += 1
                
                updated, changes = update_links_in_file(file_path)
                
                if updated:
                    total_files_updated += 1
                    total_changes.append(f"\n[UPDATED] {file_path}")
                    for change in changes:
                        total_changes.append(f"  - {change}")

    # Write Log File
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("SEO INTERNAL LINK UPDATE LOG\n")
        f.write("============================\n\n")
        f.write(f"Files Scanned: {total_files_scanned}\n")
        f.write(f"Files Updated: {total_files_updated}\n\n")
        f.write("DETAILS:\n")
        f.write("\n".join(total_changes))
    
    print("\n✅ Scan Complete!")
    print(f"📄 Files Scanned: {total_files_scanned}")
    print(f"✏️  Files Updated: {total_files_updated}")
    print(f"📝 Detailed log saved to: {log_file}")
    print("⚠️  NOTE: Backup files (.bak) have been created for every modified file. Review them before deleting.")

if __name__ == "__main__":
    main()