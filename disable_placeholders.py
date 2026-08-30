#!/usr/bin/env python3
"""
Remove or disable placeholder href="#" links.
Options:
1. Remove the <a> tag entirely and keep text
2. Convert <a> to <button> disabled
3. Remove href="#" and add onclick="return false"
"""

import os
import re

def remove_placeholder_links(filepath):
    """Remove or disable placeholder affiliate links."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"Error reading: {e}"
    
    original_content = content
    
    # Strategy: Convert affiliate link anchors to spans (remove the clickability)
    # Pattern: <a href="#" ... >Check Price on Amazon</a>
    # Replace with: <span class="btn" style="opacity:0.5;cursor:not-allowed;">Check Price on Amazon</span>
    
    # This preserves the text and styling but makes it non-clickable
    def replace_placeholder_link(match):
        full_tag = match.group(0)
        # Extract content and attributes
        text_match = re.search(r'>([^<]+)<\/a>', full_tag)
        text = text_match.group(1) if text_match else "Link"
        
        # Keep class and other attributes except href
        class_match = re.search(r'class="([^"]*)"', full_tag)
        class_str = f'class="{class_match.group(1)}"' if class_match else 'class="btn"'
        
        # Check for rel attribute
        rel_match = re.search(r'rel="([^"]*)"', full_tag)
        rel_str = f'rel="{rel_match.group(1)}"' if rel_match else ''
        
        # Return disabled span
        title = "Affiliate link coming soon"
        return f'<span {class_str} {rel_str} title="{title}" style="opacity:0.5; cursor:not-allowed; display:inline-block;">{text}</span>'
    
    # Replace all href="#" links
    new_content = re.sub(
        r'<a\s+href="#"[^>]*>([^<]*)<\/a>',
        replace_placeholder_link,
        content
    )
    
    if new_content != original_content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            # Count changes
            changes = len(re.findall(r'<a\s+href="#"[^>]*>([^<]*)<\/a>', original_content))
            return True, f"Disabled {changes} placeholder links"
        except Exception as e:
            return False, f"Error writing: {e}"
    
    return False, "No placeholder links found"

def main():
    print("Disabling placeholder href='#' links...\n")
    
    fixed_count = 0
    total_links = 0
    
    for dirpath, dirnames, filenames in os.walk('.'):
        dirnames[:] = [d for d in dirnames if d not in ['.git', 'assets', '.github']]
        
        for filename in filenames:
            if filename.endswith('.html'):
                filepath = os.path.join(dirpath, filename)
                success, message = remove_placeholder_links(filepath)
                
                if success:
                    fixed_count += 1
                    # Extract number of links from message
                    links_match = re.search(r'Disabled (\d+)', message)
                    if links_match:
                        total_links += int(links_match.group(1))
                        rel_path = filepath.replace(os.getcwd(), '').lstrip('\\/')
                        print(f"[DISABLED] {rel_path} - {message}")
    
    print(f"\n{'='*80}")
    print(f"Summary: Disabled {total_links} placeholder links in {fixed_count} files")

if __name__ == '__main__':
    main()
