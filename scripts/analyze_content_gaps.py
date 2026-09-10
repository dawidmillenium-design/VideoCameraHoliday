#!/usr/bin/env python3
"""
AI Content Gap Analyzer
Scans existing HTML content and uses DeepSeek to suggest new low-competition topics.
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

def scan_existing_content() -> list:
    """Extract topics from all existing articles in the repository."""
    topics = []
    # Scan common content directories
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
                
                if title or h1:
                    topics.append({
                        "file": str(html_file),
                        "title": title.text.strip() if title else "",
                        "h1": h1.text.strip() if h1 else ""
                    })
            except Exception as e:
                print(f"Warning: Could not parse {html_file}: {e}")
    
    return topics

def suggest_new_topics(existing_topics: list) -> list:
    """Use DeepSeek to find content gaps and suggest new topics."""
    # Limit to first 50 topics to avoid overwhelming the context window
    topics_sample = existing_topics[:50]
    
    prompt = f"""You are an expert SEO content strategist for a travel camera blog called VideoCameraHoliday.

Here are some of the existing articles on the site (showing title/H1):
{json.dumps(topics_sample, indent=2)}

Based on this content, suggest 10 NEW article topics that:
1. Fill gaps in the current content
2. Target low-competition, long-tail keywords (easy to rank without backlinks)
3. Are highly relevant to travel photography/videography in 2026
4. Cover different camera types (action cams, mirrorless, smartphones, gimbals)
5. Address different travel scenarios (beach, mountains, cities, underwater, low-light)

For each topic, provide a JSON object with:
- "title": SEO-optimized title (include year 2026)
- "keyword": primary target long-tail keyword
- "reason": why this topic is valuable and low-competition (1-2 sentences)
- "content_type": one of [review, comparison, how-to, buying-guide, destination-guide]

Return ONLY a valid JSON array of objects. No markdown formatting."""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
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

def main():
    print("🧠 Starting AI Content Gap Analysis...")
    print("=" * 60)
    
    existing = scan_existing_content()
    print(f"📚 Found {len(existing)} existing articles to analyze")
    
    if len(existing) == 0:
        print("❌ No existing content found. Please check directory structure.")
        return
        
    print("🤖 Asking DeepSeek for content gap suggestions...")
    suggestions = suggest_new_topics(existing)
    
    if suggestions:
        report = {
            "existing_count": len(existing),
            "suggestions": suggestions,
            "generated_at": "2026-09-09"
        }
        
        with open("content-gap-report.json", 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"\n✅ Generated {len(suggestions)} topic suggestions!")
        print("📁 Saved to: content-gap-report.json")
        print("\nTop 3 Suggestions:")
        for i, topic in enumerate(suggestions[:3], 1):
            print(f"{i}. {topic['title']}")
            print(f"   Keyword: {topic['keyword']}")
            print(f"   Type: {topic['content_type']}")
            print()
    else:
        print("❌ Failed to generate suggestions.")

if __name__ == "__main__":
    main()
