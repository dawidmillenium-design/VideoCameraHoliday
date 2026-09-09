#!/usr/bin/env python3
"""
Multi-Language AI Article Generator using DeepSeek API
Generates SEO-optimized articles in 10 languages for VideoCameraHoliday blog
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
WORD_COUNT = int(os.getenv("WORD_COUNT", "2000"))
CONTENT_TYPE = os.getenv("CONTENT_TYPE", "comparison")
GENERATE_ALL_LANGUAGES = os.getenv("GENERATE_ALL_LANGUAGES", "true").lower() == "true"

# Language configurations
LANGUAGES = {
    "en-US": {
        "name": "English",
        "region": "United States",
        "folder": "comparisons",
        "hreflang": "en-us"
    },
    "es-ES": {
        "name": "Spanish",
        "region": "Spain",
        "folder": "es-ES/comparaciones",
        "hreflang": "es-es"
    },
    "fr-FR": {
        "name": "French",
        "region": "France",
        "folder": "fr-FR/comparaisons",
        "hreflang": "fr-fr"
    },
    "de-DE": {
        "name": "German",
        "region": "Germany",
        "folder": "de-DE/vergleiche",
        "hreflang": "de-de"
    },
    "ja-JP": {
        "name": "Japanese",
        "region": "Japan",
        "folder": "ja-JP/hikaku",
        "hreflang": "ja-jp"
    },
    "ko-KR": {
        "name": "Korean",
        "region": "South Korea",
        "folder": "ko-KR/bigyo",
        "hreflang": "ko-kr"
    },
    "zh-CN": {
        "name": "Chinese (Simplified)",
        "region": "China",
        "folder": "zh-CN/bijiao",
        "hreflang": "zh-cn"
    },
    "pl-PL": {
        "name": "Polish",
        "region": "Poland",
        "folder": "pl-PL/porownania",
        "hreflang": "pl-pl"
    },
    "th-TH": {
        "name": "Thai",
        "region": "Thailand",
        "folder": "th-TH/khiebthieb",
        "hreflang": "th-th"
    },
    "it-IT": {
        "name": "Italian",
        "region": "Italy",
        "folder": "it-IT/confronti",
        "hreflang": "it-it"
    }
}

def generate_article_prompt(lang_code, lang_info):
    """Generate the prompt for DeepSeek based on content type and language"""
    
    prompts = {
        "review": f"""Write a comprehensive camera review in {lang_info['name']} ({lang_info['region']}) for: {ARTICLE_TOPIC}

Requirements:
- Word count: approximately {WORD_COUNT} words
- Tone: Expert, first-hand experience, trustworthy
- Include: Technical specs, real-world testing in {lang_info['region']}, pros/cons, price analysis in local currency
- Structure: H1 title, 4-5 H2 sections, comparison tables if applicable
- SEO: Include primary keyword naturally 2-3 times
- EEAT: Mention specific testing scenarios relevant to {lang_info['region']}
- Format: Output clean HTML with proper heading hierarchy
- Cultural adaptation: Adapt examples and use cases for {lang_info['region']} audience
- Local pricing: Mention prices in local currency when relevant""",

        "comparison": f"""Write a detailed comparison article in {lang_info['name']} ({lang_info['region']}): {ARTICLE_TOPIC}

Requirements:
- Word count: approximately {WORD_COUNT} words
- Tone: Objective, data-driven, helpful
- Include: Side-by-side comparison table, use cases for each, winner recommendation
- Structure: H1 title, intro, specs comparison, real-world tests in {lang_info['region']}, verdict
- SEO: Target commercial investigation intent
- EEAT: Reference actual testing in locations relevant to {lang_info['region']} travelers
- Format: Output clean HTML with <table> for comparisons
- Cultural adaptation: Focus on travel scenarios popular with {lang_info['name']} speakers
- Local availability: Mention which cameras are popular/available in {lang_info['region']}""",

        "buying-guide": f"""Write a comprehensive buying guide in {lang_info['name']} ({lang_info['region']}): {ARTICLE_TOPIC}

Requirements:
- Word count: approximately {WORD_COUNT} words
- Tone: Educational, beginner-friendly but expert
- Include: Key features to consider, top 3-5 picks with local pricing, budget options
- Structure: H1 title, buying criteria, product recommendations, FAQ
- SEO: Target informational + commercial intent
- EEAT: Explain why each pick suits specific travel scenarios for {lang_info['name']} speakers
- Format: Output clean HTML with product cards
- Cultural adaptation: Consider shopping habits and preferences in {lang_info['region']}""",

        "how-to": f"""Write a detailed tutorial in {lang_info['name']} ({lang_info['region']}): {ARTICLE_TOPIC}

Requirements:
- Word count: approximately {WORD_COUNT} words
- Tone: Instructional, step-by-step, encouraging
- Include: Numbered steps, gear recommendations available in {lang_info['region']}, troubleshooting tips
- Structure: H1 title, prerequisites, step-by-step guide, common mistakes
- SEO: Target informational intent with clear answers
- EEAT: Share personal field experience relevant to {lang_info['region']}
- Format: Output clean HTML with <ol> for steps
- Cultural adaptation: Use examples and locations familiar to {lang_info['name']} speakers""",

        "destination-guide": f"""Write a destination-specific camera guide in {lang_info['name']} ({lang_info['region']}): {ARTICLE_TOPIC}

Requirements:
- Word count: approximately {WORD_COUNT} words
- Tone: Travel-focused, practical, culturally aware
- Include: Location-specific challenges, gear recommendations, local regulations in {lang_info['region']}
- Structure: H1 title, destination overview, camera challenges, gear picks, tips
- SEO: Target location + camera keywords
- EEAT: Reference specific shooting locations and conditions
- Format: Output clean HTML with destination highlights
- Cultural adaptation: Respect local customs and photography laws""",

        "default": f"""Write a comprehensive article in {lang_info['name']} ({lang_info['region']}): {ARTICLE_TOPIC}

Requirements:
- Word count: approximately {WORD_COUNT} words
- Tone: Professional, engaging, informative
- Include: Detailed explanations, examples, practical tips
- Structure: H1 title, multiple H2 sections, conclusion
- SEO: Include relevant keywords naturally
- EEAT: Demonstrate expertise and experience
- Format: Output clean HTML with proper structure
- Cultural adaptation: Adapt content for {lang_info['name']} speakers in {lang_info['region']}"""
    }
    
    return prompts.get(CONTENT_TYPE, prompts["default"])

def generate_content(prompt: str, lang_code: str) -> str:
    """Call DeepSeek API to generate content in specific language"""
    lang_info = LANGUAGES[lang_code]
    
    print(f"🤖 Generating {lang_info['name']} content with DeepSeek...")
    print(f"📝 Topic: {ARTICLE_TOPIC}")
    print(f"🌍 Target: {lang_info['name']} ({lang_info['region']})")
    
    try:
        # System prompt varies by language
        system_prompts = {
            "en-US": "You are an expert travel photography and videography content writer. You write SEO-optimized, EEAT-compliant articles for VideoCameraHoliday blog. Output ONLY valid HTML5 content without markdown code blocks.",
            "es-ES": "Eres un escritor experto en contenido de fotografía y videografía de viajes. Escribes artículos optimizados para SEO y compatibles con EEAT para VideoCameraHoliday. Genera ÚNICAMENTE contenido HTML5 válido sin bloques de código markdown.",
            "fr-FR": "Vous êtes un rédacteur expert en contenu de photographie et vidéographie de voyage. Vous rédigez des articles optimisés pour le SEO et conformes aux normes EEAT pour VideoCameraHoliday. Produisez UNIQUEMENT du contenu HTML5 valide sans blocs de code markdown.",
            "de-DE": "Sie sind ein erfahrener Autor für Reise-Fotografie und Videografie-Inhalte. Sie schreiben SEO-optimierte, EEAT-konforme Artikel für VideoCameraHoliday. Geben Sie NUR gültigen HTML5-Inhalt ohne Markdown-Codeblöcke aus.",
            "ja-JP": "あなたは旅行写真・動画コンテンツの専門家ライターです。VideoCameraHoliday 向けの SEO 最適化された EEAT 準拠の記事を書きます。Markdown コードブロックなしで有効な HTML5 コンテンツのみを出力してください。",
            "ko-KR": "당신은 여행 사진 및 비디오 콘텐츠 전문 작가입니다. VideoCameraHoliday 를 위한 SEO 최적화, EEAT 준수 기사를 작성합니다. 마크다운 코드 블록 없이 유효한 HTML5 콘텐츠만 출력하세요.",
            "zh-CN": "您是一位专业的旅行摄影和摄像内容作家。您为 VideoCameraHoliday 撰写 SEO 优化、EEAT 合规的文章。仅输出有效的 HTML5 内容，不要使用 markdown 代码块。",
            "pl-PL": "Jesteś ekspertem w pisaniu treści o fotografii i wideografii podróżniczej. Piszesz artykuły zoptymalizowane pod kątem SEO i zgodne z EEAT dla VideoCameraHoliday. Wygeneruj WYŁĄCZNIE prawidłową treść HTML5 bez bloków kodu markdown.",
            "th-TH": "คุณคือนักเขียนเนื้อหาการถ่ายภาพและวิดีโอท่องเที่ยวผู้เชี่ยวชาญ คุณเขียนบทความที่ปรับแต่ง SEO และปฏิบัติตาม EEAT สำหรับ VideoCameraHoliday สร้างเนื้อหา HTML5 ที่ถูกต้องเท่านั้นโดยไม่มีบล็อกโค้ด markdown",
            "it-IT": "Sei uno scrittore esperto di contenuti di fotografia e videografia di viaggio. Scrivi articoli ottimizzati per SEO e conformi a EEAT per VideoCameraHoliday. Produci SOLO contenuti HTML5 validi senza blocchi di codice markdown."
        }
        
        response = client.chat.completions.create(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            messages=[
                {
                    "role": "system", 
                    "content": system_prompts.get(lang_code, system_prompts["en-US"])
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
        print(f"❌ Error generating {lang_info['name']} content: {e}")
        raise

def add_html_wrapper(content: str, lang_code: str, all_versions: dict) -> str:
    """Add proper HTML structure with schema markup and hreflang tags"""
    lang_info = LANGUAGES[lang_code]
    slug = ARTICLE_TOPIC.lower().replace(" ", "-").replace(":", "").replace("?", "")[:80]
    publish_date = datetime.now().strftime("%Y-%m-%d")
    
    # Extract title from content or use topic
    soup = BeautifulSoup(content, 'lxml')
    h1 = soup.find('h1')
    title = h1.get_text() if h1 else ARTICLE_TOPIC
    
    # Generate meta description
    first_paragraph = soup.find('p')
    meta_desc = first_paragraph.get_text()[:155] + "..." if first_paragraph else title
    
    # Build hreflang tags for all language versions
    hreflang_tags = ""
    base_url = "https://dawidmillenium-design.github.io/VideoCameraHoliday"
    
    for code, info in all_versions.items():
        hreflang_tags += f'    <link rel="alternate" hreflang="{info["hreflang"]}" href="{base_url}/{info["folder"]}/{slug}.html">\n'
    
    # Add x-default
    hreflang_tags += f'    <link rel="alternate" hreflang="x-default" href="{base_url}/comparisons/{slug}.html">\n'
    
    html_wrapper = f"""<!DOCTYPE html>
<html lang="{lang_code}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{meta_desc}">
    <meta name="author" content="Dawid Millenium">
    <link rel="canonical" href="{base_url}/{lang_info['folder']}/{slug}.html">
    
    <!-- Hreflang Tags for Multi-Language SEO -->
{hreflang_tags.strip()}
    
    <!-- Open Graph -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{meta_desc}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{base_url}/{lang_info['folder']}/{slug}.html">
    <meta property="og:locale" content="{lang_code.replace('-', '_')}">
    <meta property="article:published_time" content="{publish_date}">
    <meta property="article:author" content="Dawid Millenium">
    
    <!-- Schema.org -->
    <script type="application/ld+json">
{{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{title}",
    "description": "{meta_desc}",
    "inLanguage": "{lang_code}",
    "author": {{
        "@type": "Person",
        "name": "Dawid Millenium",
        "url": "{base_url}/about.html"
    }},
    "publisher": {{
        "@type": "Organization",
        "name": "VideoCameraHoliday",
        "logo": {{
            "@type": "ImageObject",
            "url": "{base_url}/logo.png"
        }}
    }},
    "datePublished": "{publish_date}",
    "dateModified": "{publish_date}",
    "mainEntityOfPage": {{
        "@type": "WebPage",
        "@id": "{base_url}/{lang_info['folder']}/{slug}.html"
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

def save_article(content: str, lang_code: str):
    """Save the generated article to file"""
    lang_info = LANGUAGES[lang_code]
    slug = ARTICLE_TOPIC.lower().replace(" ", "-").replace(":", "").replace("?", "")[:80]
    
    # Create output directory structure
    output_dir = Path("generated-content") / lang_info["folder"]
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{slug}.html"
    filepath = output_dir / filename
    
    # Save file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {lang_info['name']} article saved to: {filepath}")
    print(f" Content length: {len(content)} characters")
    
    # Save metadata
    metadata = {
        "topic": ARTICLE_TOPIC,
        "language": lang_code,
        "content_type": CONTENT_TYPE,
        "word_count_target": WORD_COUNT,
        "generated_at": datetime.now().isoformat(),
        "filename": filename,
        "folder": lang_info["folder"]
    }
    
    with open(output_dir / f"{slug}-metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def main():
    print(" Starting Multi-Language AI Article Generation...")
    print("=" * 70)
    print(f"📝 Topic: {ARTICLE_TOPIC}")
    print(f"📏 Target words: {WORD_COUNT} per language")
    print(f"📚 Content type: {CONTENT_TYPE}")
    print("=" * 70)
    
    # Determine which languages to generate
    if GENERATE_ALL_LANGUAGES:
        languages_to_generate = LANGUAGES
        print(f"🌍 Generating in ALL 10 languages")
    else:
        languages_to_generate = {"en-US": LANGUAGES["en-US"]}
        print(f"🌍 Generating in English only")
    
    print(f" Languages: {', '.join(languages_to_generate.keys())}")
    print("=" * 70)
    
    # Store all generated versions for hreflang cross-referencing
    all_versions = {}
    
    # Generate for each language
    for lang_code, lang_info in languages_to_generate.items():
        print(f"\n{'='*70}")
        print(f" Processing: {lang_info['name']} ({lang_code})")
        print(f"{'='*70}")
        
        try:
            # Generate prompt
            prompt = generate_article_prompt(lang_code, lang_info)
            
            # Generate content
            raw_content = generate_content(prompt, lang_code)
            print(f"✅ {lang_info['name']} content generated")
            
            # Add HTML wrapper (will be updated with all hreflang tags after all languages are done)
            final_html = add_html_wrapper(raw_content, lang_code, languages_to_generate)
            print(f"✅ HTML structure added with schema markup")
            
            # Save article
            save_article(final_html, lang_code)
            
            all_versions[lang_code] = lang_info
            
        except Exception as e:
            print(f"❌ Failed to generate {lang_info['name']}: {e}")
            continue
    
    print("\n" + "=" * 70)
    print("🎉 Multi-Language Article Generation Complete!")
    print("=" * 70)
    print(f"✅ Successfully generated {len(all_versions)} language versions")
    print(f" Output directory: generated-content/")
    print("=" * 70)

if __name__ == "__main__":
    main()
