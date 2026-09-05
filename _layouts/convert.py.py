import os
import re

# Set the root directory to search ('.' means the current folder)
root_dir = '.' 

# Folders and files to ignore so we don't accidentally break them
ignore_folders = ['_includes', '_layouts', '.git']
ignore_files = ['header.html', 'footer.html', 'default.html']

for subdir, dirs, files in os.walk(root_dir):
    # Skip ignored folders
    dirs[:] = [d for d in dirs if d not in ignore_folders]
    
    for file in files:
        if file.endswith('.html') and file not in ignore_files:
            filepath = os.path.join(subdir, file)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip if the file already has Jekyll Front Matter (starts with ---)
            if content.strip().startswith('---'):
                print(f"Skipping (Already converted): {filepath}")
                continue
                
            # Extract meta data using Regex
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            desc_match = re.search(r'<meta name="description" content="(.*?)">', content, re.IGNORECASE)
            canon_match = re.search(r'<link rel="canonical" href="(.*?)">', content, re.IGNORECASE)
            
            # Extract JSON-LD script and Main content block
            json_ld_match = re.search(r'(<script type="application/ld\+json">.*?</script>)', content, re.IGNORECASE | re.DOTALL)
            main_match = re.search(r'(<main\b[^>]*>.*?</main>)', content, re.IGNORECASE | re.DOTALL)
            
            # If there's no main tag, skip it so we don't break non-standard pages
            if not main_match:
                print(f"Skipping (No <main> tag found): {filepath}")
                continue
                
            # Clean up extracted data
            title = title_match.group(1).strip() if title_match else "Holiday Video Camera"
            desc = desc_match.group(1).strip() if desc_match else ""
            canon = canon_match.group(1).strip() if canon_match else ""
            json_ld = json_ld_match.group(1) if json_ld_match else ""
            main_content = main_match.group(1)
            
            # Build the new Jekyll-ready content
            new_content = f"""---
layout: default
title: "{title}"
description: "{desc}"
canonical_url: "{canon}"
---

{json_ld}

{main_content}
"""
            # Write the new format back to the file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Successfully Converted: {filepath}")

print("All files processed!")