#!/usr/bin/env python3
"""
Smart Internal Linking Engine
Uses DeepSeek to find and inject relevant internal links into new articles.
"""

import os
import json
from pathlib import Path
from openai import OpenAI
from bs4 import BeautifulSoup

# Initialize DeepSeek Client
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

def get_existing_pages() -> list:
    """Scan repository for all existing HTML pages to use as link targets."""
    pages = []
    scan_dirs = ['comparisons', 'guides', 'reviews', 'how-to', 'destinations', 'interviews']
    
    for dir_name in scan_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            continue
            
        for html_file in dir_path.glob("*.html"):
            # Skip index files
            if html_file.name.startswith('index'):
                continue
                
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'lxml')
                
                title = soup.find('title')
                h1 = soup.find('h1')
                
                # Build URL path
                url_path = f"/{html_file}"
                
                pages.append({
                    "path": str(html_file),
                    "title": title.text.strip() if title else "",
                    "h1": h1.text.strip() if h1 else "",
                    "url": url_path
                })
            except Exception as e:
                pass  # Skip files that can't be parsed
    
    return pages

def suggest_links(article_content: str, existing_pages: list) -> list:
    """Use DeepSeek to suggest 3-5 relevant internal links."""
    # Limit to first 30 pages to avoid context overflow
    pages_sample = existing_pages[:30]
    
    prompt = f"""Given this new article content and a list of existing pages on the same website, suggest 3-5 highly relevant internal links.

NEW ARTICLE CONTENT (first 1500 characters):
{article_content[:1500]}

EXISTING PAGES ON THE SITE:
{json.dumps(pages_sample, indent=2)}

Return a JSON array of objects. Each object should contain:
- "anchor_text": natural, descriptive anchor text (3-6 words)
- "url": the exact URL path from the existing pages list
- "reason": brief explanation of why this link is relevant (1 sentence)

Only suggest links that are genuinely topically relevant to the new article. Return ONLY valid JSON, no markdown."""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3  # Low temperature for more precise results
        )
        
        content = response.choices[0].message.content
        # Clean up markdown if present
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
            
        return json.loads(content)
    except Exception as e:
        print(f"Error calling DeepSeek API: {e}")
        return []

def inject_links(filepath: str, links: list):
    """Add suggested links to the article as a 'Related Articles' section."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'lxml')
        
        # Find the main content area
        main = soup.find('main') or soup.find('body')
        if not main:
            print(f"  Warning: Could not find main/body tag in {filepath}")
            return
        
        # Create "Related Articles" section
        related_section = soup.new_tag('div', attrs={'class': 'related-articles', 'style': 'margin-top: 3rem; padding: 2rem; background: #f8f9fa; border-radius: 8px;'})
        
        related_h2 = soup.new_tag('h2')
        related_h2.string = "📚 Related Articles"
        related_section.append(related_h2)
        
        ul = soup.new_tag('ul', attrs={'style': 'list-style-type: none; padding: 0;'})
        
        for link in links[:5]:  # Max 5 links
            li = soup.new_tag('li', attrs={'style': 'margin-bottom: 0.5rem;'})
            a = soup.new_tag('a', href=link['url'])
            a.string = link['anchor_text']
            a['title'] = link.get('reason', '')
            a['style'] = 'color: #0066cc; text-decoration: none;'
            li.append(a)
            ul.append(li)
        
        related_section.append(ul)
        main.append(related_section)
        
        # Save modified file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
    except Exception as e:
        print(f"  Error injecting links into {filepath}: {e}")

def main():
    print(" Starting Smart Internal Linking...")
    print("=" * 60)
    
    print("📚 Scanning existing pages...")
    existing_pages = get_existing_pages()
    print(f"   Found {len(existing_pages)} existing pages")
    
    if len(existing_pages) == 0:
        print("❌ No existing pages found. Cannot generate links.")
        return
        
    generated_dir = Path("generated-content")
    if not generated_dir.exists():
        print("❌ generated-content/ directory not found")
        return
        
    print(" Analyzing new articles and generating links...")
    total_links_added = 0
    
    for html_file in generated_dir.rglob("*.html"):
        # Skip metadata files
        if 'metadata' in html_file.name:
            continue
            
        print(f"\n📄 Processing: {html_file.name}")
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            links = suggest_links(content, existing_pages)
            
            if links:
                inject_links(str(html_file), links)
                print(f"   ✅ Added {len(links)} internal links")
                total_links_added += len(links)
            else:
                print(f"   ⚠️ No relevant links found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
    print("\n" + "=" * 60)
    print(f"🎉 Internal Linking Complete!")
    print(f"   Total links added: {total_links_added}")

if __name__ == "__main__":
    main()
