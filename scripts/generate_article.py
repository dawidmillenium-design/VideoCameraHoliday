#!/usr/bin/env python3
"""
AI Article Generator using DeepSeek API
Generates SEO-optimized articles for VideoCameraHoliday blog
"""

import os
import json
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from bs4 import BeautifulSoup

# Initialize DeepSeek Client (OpenAI-compatible)
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# Get inputs from environment
ARTICLE_TOPIC = os.getenv("ARTICLE_TOPIC")
TARGET_LANGUAGE = os.getenv("TARGET_LANGUAGE", "en-US")
WORD_COUNT = int(os.getenv("WORD_COUNT", "2000"))
CONTENT_TYPE = os.getenv("CONTENT_TYPE", "comparison")

# Language mapping for prompts
LANGUAGE_MAP = {
    "en-US": ("English", "United States"),
    "th-TH": ("Thai", "Thailand"),
    "pl-PL": ("Polish", "Poland"),
    "de-DE": ("German", "Germany"),
    "ja-JP": ("Japanese", "Japan"),
    "es-ES": ("Spanish", "Spain"),
    "fr-FR": ("French", "France"),
}

def generate_article_prompt():
    """Generate the prompt for DeepSeek based on content type"""
    lang_name, region = LANGUAGE_MAP.get(TARGET_LANGUAGE, ("English", "United States"))
    
    prompts = {
        "review": f"""Write a comprehensive camera review in {lang_name} ({region}) for: {ARTICLE_TOPIC}

Requirements:
- Word count: approximately {WORD_COUNT} words
- Tone: Expert, first-hand experience, trustworthy
- Include: Technical specs, real-world testing, pros/cons, price analysis
- Structure: H1 title, 4-5 H2 sections, comparison tables if applicable
- SEO: Include primary keyword naturally 2-3 times
- EEAT: Mention specific testing scenarios and personal experience
- Format: Output clean HTML with proper heading hierarchy""",

        "comparison": f"""Write a detailed comparison article in {lang_name} ({region}): {ARTICLE_TOPIC}

Requirements:
- Word count: approximately {WORD_COUNT} words
- Tone: Objective, data-driven, helpful
- Include: Side-by-side comparison table, use cases for each, winner recommendation
- Structure: H1 title, intro, specs comparison, real-world tests, verdict
- SEO: Target commercial investigation intent
- EEAT: Reference actual testing in specific locations (Bangkok, Lisbon, Alps)
- Format: Output clean HTML with <table> for comparisons""",

        "buying-guide": f"""Write a comprehensive buying guide in {lang_name} ({region}): {ARTICLE_TOPIC}

Requirements:
- Word count: approximately {WORD_COUNT} words
- Tone: Educational, beginner-friendly but expert
- Include: Key features to consider, top 3-5 picks, budget options
- Structure: H1 title, buying criteria, product recommendations, FAQ
- SEO: Target informational + commercial intent
- EEAT: Explain why each pick suits specific travel scenarios
- Format: Output clean HTML with product cards""",

        "how-to": f"""Write a detailed tutorial in {lang_name} ({region}): {ARTICLE_TOPIC}

Requirements:
- Word count: approximately {WORD_COUNT} words
- Tone: Instructional, step-by-step, encouraging
- Include: Numbered steps, gear recommendations, troubleshooting tips
- Structure: H1 title, prerequisites, step-by-step guide, common mistakes
- SEO: Target informational intent with clear answers
- EEAT: Share personal field experience and lessons learned
- Format: Output clean HTML with <ol> for steps""",

        "destination-guide": f"""Write a destination-specific camera guide in {lang_name} ({region}): {ARTICLE_TOPIC}

Requirements:
- Word count: approximately {WORD_COUNT} words
- Tone: Travel-focused, practical, culturally aware
- Include: Location-specific challenges, gear recommendations, local regulations
- Structure: H1 title, destination overview, camera challenges, gear picks, tips
- SEO: Target location + camera keywords
- EEAT: Reference specific shooting locations and conditions
- Format: Output clean HTML with destination highlights"""
    }
    
    return prompts.get(CONTENT_TYPE, prompts["comparison"])

def generate_content(prompt: str) -> str:
    """Call DeepSeek API to generate content"""
    print(f"🤖 Generating content with DeepSeek (model: {os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')})...")
    print(f"📝 Topic: {ARTICLE_TOPIC}")
    print(f"🌍 Language: {TARGET_LANGUAGE}")
    print(f"📏 Target words: {WORD_COUNT}")
    
    try:
        response = client.chat.completions.create(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert travel photography and videography content writer. You write SEO-optimized, EEAT-compliant articles for VideoCameraHoliday blog. Output ONLY valid HTML5 content without markdown code blocks."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=4000,
            top_p=0.9
        )
        
        content = response.choices[0].message.content
        
        # Clean up markdown if present
        if content.startswith("```html"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        return content.strip()
        
    except Exception as e:
        print(f"❌ Error generating content: {e}")
        raise

def add_html_wrapper(content: str) -> str:
    """Add proper HTML structure with schema markup"""
    slug = ARTICLE_TOPIC.lower().replace(" ", "-").replace(":", "").replace("?", "")[:80]
    publish_date = datetime.now().strftime("%Y-%m-%d")
    
    # Extract title from content or use topic
    soup = BeautifulSoup(content, 'lxml')
    h1 = soup.find('h1')
    title = h1.get_text() if h1 else ARTICLE_TOPIC
    
    # Generate meta description
    first_paragraph = soup.find('p')
    meta_desc = first_paragraph.get_text()[:155] + "..." if first_paragraph else title
    
    html_wrapper = f"""<!DOCTYPE html>
<html lang="{TARGET_LANGUAGE}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{meta_desc}">
    <meta name="author" content="Dawid Millenium">
    <link rel="canonical" href="https://dawidmillenium-design.github.io/VideoCameraHoliday/{slug}.html">
    
    <!-- Open Graph -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{meta_desc}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://dawidmillenium-design.github.io/VideoCameraHoliday/{slug}.html">
    <meta property="og:locale" content="{TARGET_LANGUAGE.replace('-', '_')}">
    <meta property="article:published_time" content="{publish_date}">
    <meta property="article:author" content="Dawid Millenium">
    
    <!-- Schema.org -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "{title}",
        "description": "{meta_desc}",
        "author": {{
            "@type": "Person",
            "name": "Dawid Millenium",
            "url": "https://dawidmillenium-design.github.io/VideoCameraHoliday/about.html"
        }},
        "publisher": {{
            "@type": "Organization",
            "name": "VideoCameraHoliday",
            "logo": {{
                "@type": "ImageObject",
                "url": "https://dawidmillenium-design.github.io/VideoCameraHoliday/logo.png"
            }}
        }},
        "datePublished": "{publish_date}",
        "dateModified": "{publish_date}",
        "mainEntityOfPage": {{
            "@type": "WebPage",
            "@id": "https://dawidmillenium-design.github.io/VideoCameraHoliday/{slug}.html"
        }}
    }}
    </script>
</head>
<body>
    <main>
        {content}
    </main>
</body>
</html>"""
    
    return html_wrapper

def save_article(content: str):
    """Save the generated article to file"""
    # Create output directory
    output_dir = Path("generated-content")
    output_dir.mkdir(exist_ok=True)
    
    # Generate filename from topic
    slug = ARTICLE_TOPIC.lower().replace(" ", "-").replace(":", "").replace("?", "")[:80]
    filename = f"{slug}.html"
    filepath = output_dir / filename
    
    # Save file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Article saved to: {filepath}")
    print(f"📊 Content length: {len(content)} characters")
    
    # Save metadata
    metadata = {
        "topic": ARTICLE_TOPIC,
        "language": TARGET_LANGUAGE,
        "content_type": CONTENT_TYPE,
        "word_count_target": WORD_COUNT,
        "generated_at": datetime.now().isoformat(),
        "filename": filename
    }
    
    with open(output_dir / f"{slug}-metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Metadata saved to: {output_dir / f'{slug}-metadata.json'}")

def main():
    print("🚀 Starting AI Article Generation...")
    print("=" * 60)
    
    # Generate prompt
    prompt = generate_article_prompt()
    print(f"📋 Generated prompt for {CONTENT_TYPE} content type")
    
    # Generate content
    raw_content = generate_content(prompt)
    print("✅ Content generated successfully")
    
    # Add HTML wrapper
    final_html = add_html_wrapper(raw_content)
    print("✅ HTML structure added with schema markup")
    
    # Save article
    save_article(final_html)
    
    print("=" * 60)
    print("🎉 Article generation complete!")

if __name__ == "__main__":
    main()
