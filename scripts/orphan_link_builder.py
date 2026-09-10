#!/usr/bin/env python3
"""
Smart Internal Linking & Orphan Fixer
Finds "orphan" pages (pages with few incoming links) and uses DeepSeek 
to suggest relevant links from high-authority pages.
"""

import os
import json
import re
from pathlib import Path
from openai import OpenAI
from bs4 import BeautifulSoup
from collections import defaultdict

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

MAX_LINKS = int(os.getenv('MAX_LINKS', '3'))
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'

def scan_all_pages():
    """Scan all HTML files and map their content and existing links."""
    pages = {}
    # Directories to scan
    scan_dirs = ['comparisons', 'guides', 'reviews', 'how-to', 'destinations', 'interviews', 'posts', 'city-through-the-lens']
    
    for dir_name in scan_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists(): continue
        
        for html_file in dir_path.rglob("*.html"):
            if html_file.name.startswith('index'): continue
            
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'lxml')
                
                # Get text content for AI analysis
                text = soup.get_text(separator=' ', strip=True)[:1500] 
                
                # Find existing outgoing links
                links = [a.get('href') for a in soup.find_all('a', href=True) if a['href'].endswith('.html')]
                
                pages[str(html_file)] = {
                    'title': soup.find('title').text if soup.find('title') else html_file.stem,
                    'text': text,
                    'outgoing': links,
                    'incoming_count': 0 # Will calculate next
                }
            except Exception as e:
                pass
    return pages

def calculate_incoming_links(pages):
    """Count how many times each page is linked to."""
    counts = defaultdict(int)
    for path, data in pages.items():
        for link in data['outgoing']:
            # Normalize link path
            clean_link = link.lstrip('./')
            if clean_link in pages:
                counts[clean_link] += 1
    
    for path in pages:
        pages[path]['incoming_count'] = counts.get(path, 0)
    return pages

def find_orphans(pages):
    """Find pages with 0 or 1 incoming links."""
    orphans = {p: d for p, d in pages.items() if d['incoming_count'] < 2}
    return orphans

def suggest_source_pages(orphan_path, orphan_data, all_pages):
    """Ask DeepSeek which existing pages should link to this orphan."""
    # Get a list of potential "Hub" pages (pages with high incoming counts or index pages)
    potential_sources = [p for p, d in all_pages.items() if d['incoming_count'] > 5 or 'index' in p]
    
    if not potential_sources:
        potential_sources = list(all_pages.keys())[:20] # Fallback

    prompt = f"""I have an 'orphan' page on my travel camera blog that needs more internal links to be found by Google.

ORPHAN PAGE:
- URL: {orphan_path}
- Title: {orphan_data['title']}
- Content Preview: {orphan_data['text'][:500]}

POTENTIAL SOURCE PAGES (High Authority):
{json.dumps(potential_sources[:15], indent=2)}

Task: Select up to {MAX_LINKS} source pages from the list above that are topically relevant to the Orphan Page. 
For each source, provide a natural anchor text (3-5 words) that would fit into a sentence.

Return a JSON list of objects:
[
  {{"source_url": "path/to/source.html", "anchor_text": "natural anchor text"}},
  ...
]
Return ONLY valid JSON."""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content
        if content.startswith("```json"): content = content[7:]
        if content.endswith("```"): content = content[:-3]
        return json.loads(content)
    except Exception as e:
        print(f"Error: {e}")
        return []

def inject_link(source_path, target_url, anchor_text):
    """Add a link to the source page."""
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'lxml')
        
        # Find the last paragraph or a relevant section to append the link
        # For safety, we add a "Related Reading" section at the bottom of <main> or <body>
        main = soup.find('main') or soup.find('body')
        if not main: return False

        # Check if link already exists
        existing = [a.get('href') for a in soup.find_all('a', href=True)]
        if target_url in existing: return False

        # Create or find "Related Reading" div
        related = soup.find('div', class_='auto-generated-links')
        if not related:
            related = soup.new_tag('div', attrs={'class': 'auto-generated-links', 'style': 'margin-top:2rem; font-size:0.9em; color:#666;'})
            h4 = soup.new_tag('h4')
            h4.string = " Related Guides"
            related.append(h4)
            ul = soup.new_tag('ul')
            related.append(ul)
            main.append(related)
        else:
            ul = related.find('ul')
            if not ul:
                ul = soup.new_tag('ul')
                related.append(ul)

        li = soup.new_tag('li')
        a = soup.new_tag('a', href=target_url)
        a.string = anchor_text
        li.append(a)
        ul.append(li)

        if not DRY_RUN:
            with open(source_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
        return True
    except Exception as e:
        return False

def main():
    print("🔗 Starting Smart Internal Linking...")
    print("=" * 60)
    if DRY_RUN: print("️ DRY RUN MODE")

    print("1. Scanning site structure...")
    pages = scan_all_pages()
    print(f"   Found {len(pages)} content pages")

    print("2. Calculating link authority...")
    pages = calculate_incoming_links(pages)
    orphans = find_orphans(pages)
    print(f"   Found {len(orphans)} orphan pages (< 2 incoming links)")

    total_added = 0
    modified_files = set()

    # Process top 20 orphans to save API costs/time
    for i, (orphan_path, orphan_data) in enumerate(list(orphans.items())[:20]):
        print(f"\n[{i+1}/20] Analyzing: {orphan_path}")
        
        suggestions = suggest_source_pages(orphan_path, orphan_data, pages)
        
        for sug in suggestions:
            source = sug.get('source_url')
            anchor = sug.get('anchor_text')
            if source and anchor and source in pages:
                print(f"   -> Linking from {source} with anchor '{anchor}'")
                if inject_link(source, orphan_path, anchor):
                    total_added += 1
                    modified_files.add(source)

    # Summary
    summary = {
        "orphans_found": len(orphans),
        "links_added": total_added,
        "modified_files": list(modified_files)
    }
    
    with open("linking-summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
        
    print("\n" + "=" * 60)
    print(f"✅ Complete! Added {total_added} links across {len(modified_files)} files.")

if __name__ == "__main__":
    main()
