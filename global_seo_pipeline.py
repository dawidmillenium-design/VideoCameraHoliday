import os
import json
import re
import requests
import yaml
from typing import Dict, Any, List
from datetime import datetime

class GlobalSEOPipeline:
    def __init__(self, config_path: str = "global_seo_crew.yaml"):
        self.base_url = "https://dawidmillenium-design.github.io/HolidayVideoCamera/"
        self.deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_API_KEY_HERE")
        self.deepseek_api_url = "https://api.deepseek.com/v1/chat/completions"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            self.config = {"target_languages": ["en-US"]}

    def _call_deepseek(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.deepseek_api_key}"}
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature
        }
        response = requests.post(self.deepseek_api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def generate_keyword_research(self, language: str) -> Dict[str, Any]:
        keywords_map = {
            "en-US": {
                "primary": "best travel camera",
                "long_tail": ["compact camera for travel", "lightweight vlogging camera", "mirrorless camera for travel"],
                "search_intent": "commercial_investigation"
            },
            "pl-PL": {
                "primary": "najlepszy aparat podróżniczy",
                "long_tail": ["kompaktowy aparat do podróży", "lekki aparat do vlogowania", "bezlustrowy aparat podróżny"],
                "search_intent": "commercial_investigation"
            },
            "it-IT": {
                "primary": "migliore fotocamera da viaggio",
                "long_tail": ["fotocamera compatta per viaggi", "macchina fotografica leggera", "mirrorless per viaggi"],
                "search_intent": "commercial_investigation"
            },
            "de-DE": {
                "primary": "beste reisekamera",
                "long_tail": ["kompakte kamera für reisen", "spiegellose systemkamera reise", "leichte kamera für urlaub"],
                "search_intent": "commercial_investigation"
            },
            "fr-FR": {
                "primary": "meilleur appareil photo voyage",
                "long_tail": ["appareil photo compact voyage", "caméra légère pour voyager", "mirrorless voyage"],
                "search_intent": "commercial_investigation"
            },
            "es-ES": {
                "primary": "mejor cámara de viaje",
                "long_tail": ["cámara compacta para viajar", "cámara ligera para viajes", "mirrorless para viajes"],
                "search_intent": "commercial_investigation"
            },
            "th-TH": {
                "primary": "กล้องท่องเที่ยวที่ดีที่สุด",
                "long_tail": ["กล้องคอมแพคสำหรับเดินทาง", "กล้องมิเรอร์เลสท่องเที่ยว", "กล้อง vlog น้ำหนักเบา"],
                "search_intent": "commercial_investigation"
            },
            "ja-JP": {
                "primary": "旅行用カメラ おすすめ",
                "long_tail": ["コンパクトカメラ 旅行", "ミラーレスカメラ トラベル", "軽量カメラ vlog"],
                "search_intent": "commercial_investigation"
            },
            "zh-CN": {
                "primary": "最佳旅行相机",
                "long_tail": ["便携式旅行相机", "轻便旅游相机", "无反相机 旅行"],
                "search_intent": "commercial_investigation"
            },
            "pt-BR": {
                "primary": "melhor câmera de viagem",
                "long_tail": ["câmera compacta para viagem", "câmera leve para viajar", "mirrorless para viagem"],
                "search_intent": "commercial_investigation"
            },
            "nl-NL": {
                "primary": "beste reiscamera",
                "long_tail": ["compacte camera voor reizen", "lichtgewicht camera reizen", "mirrorless reiscamera"],
                "search_intent": "commercial_investigation"
            }
        }
        return keywords_map.get(language, keywords_map["en-US"])

    def generate_content_brief(self, language: str, keywords: Dict) -> Dict[str, Any]:
        return {
            "h2_outline": ["Introduction to Travel Photography", "Key Features to Look For", "Top 5 Travel Cameras in 2026", "Buying Guide & Tips"],
            "target_word_count": 2500,
            "tone": "Authoritative, Engaging, and Practical",
            "target_audience": "Travel Vloggers and Photographers"
        }

    def generate_full_article(self, brief: Dict, keywords: Dict, language: str) -> str:
        print("  -> Instructing Content Creator Agent to write long-form Markdown...")
        system_prompt = "You are an expert SEO content writer and travel photography specialist. You write comprehensive, long-form, highly detailed Markdown articles optimized for search engines and human readers."
        
        user_prompt = f"""Write a comprehensive, long-form Markdown blog post (aim for 1500-2500+ words of rich, detailed content) based on this brief.
        
        Target Keyword: "{keywords['primary']}"
        Semantic Keywords to include naturally: {', '.join(keywords.get('long_tail', []))}, mirrorless, compact, image stabilization, 4K video, weather-sealed, battery life.
        
        Content Brief:
        - H2 Outline: {brief['h2_outline']}
        - Tone: {brief['tone']}
        - Target Audience: {brief['target_audience']}
        - Language: {language}
        
        STRICT Requirements:
        1. Start with valid Jekyll YAML frontmatter:
           ---
           layout: post
           title: "Catchy Title Including '{keywords['primary']}"
           target_keyword: "{keywords['primary']}"
           date: {datetime.now().strftime('%Y-%m-%d')}
           ---
        2. Use proper Markdown headings (H1 is the title, use H2 and H3 for sections).
        3. Include the target keyword in the H1, at least one H2, and naturally throughout (density ~1-1.5%).
        4. Include a Markdown comparison table, bulleted lists, and a "Pros & Cons" section to boost EEAT.
        5. Write naturally and avoid fluff. Be highly informative.
        
        Output ONLY the raw Markdown text. Do not wrap in ```markdown code blocks.
        """
        return self._call_deepseek(system_prompt, user_prompt, temperature=0.7)

    def score_content_with_deepseek(self, content: str, target_keyword: str) -> Dict[str, Any]:
        print(f"  -> Sending generated content to DeepSeek API for scoring (Keyword: '{target_keyword}')...")
        truncated_content = content[:8000] 
        
        prompt = f"""You are an expert on-page SEO auditor (like SurferSEO). Analyze this Markdown content for: "{target_keyword}".
        Evaluate: Word count, keyword density (ideal 0.8%-1.5%), heading structure, readability, and semantic keyword usage.
        Return ONLY valid JSON matching this schema:
        {{
          "seo_score": 0,
          "word_count": 0,
          "keyword_density_percent": 0.0,
          "heading_analysis": "string",
          "missing_semantic_keywords": ["kw1", "kw2"],
          "actionable_fixes": ["fix1", "fix2"]
        }}
        Content: {truncated_content}"""
        
        try:
            response_text = self._call_deepseek(
                "You are a strict SEO auditor. Always respond with valid JSON matching the requested schema.",
                prompt,
                temperature=0.1
            )
            response_text = re.sub(r'^```json\s*', '', response_text, flags=re.MULTILINE)
            response_text = re.sub(r'\s*```$', '', response_text, flags=re.MULTILINE)
            return json.loads(response_text)
        except Exception as e:
            return {"seo_score": 0, "error": str(e)}

    def execute_pipeline_for_language(self, language: str) -> Dict[str, Any]:
        print(f"\n{'='*60}\nProcessing language: {language}\n{'='*60}")
        
        keywords = self.generate_keyword_research(language)
        brief = self.generate_content_brief(language, keywords)
        
        generated_content = self.generate_full_article(brief, keywords, language)
        deepseek_analysis = self.score_content_with_deepseek(generated_content, keywords['primary'])
        print(f"✅ DeepSeek SEO Score: {deepseek_analysis.get('seo_score', 'N/A')}/100")
        
        output_dir = "_posts"
        os.makedirs(output_dir, exist_ok=True)
        safe_keyword = re.sub(r'[^a-z0-9]+', '-', keywords['primary'].lower()).strip('-')
        filename = f"{datetime.now().strftime('%Y-%m-%d')}-{safe_keyword}.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(generated_content)
        print(f"💾 Saved generated post to: {filepath}")
        
        analysis_path = os.path.join("output", f"{filename}.analysis.json")
        os.makedirs("output", exist_ok=True)
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump({"file": filename, "analysis": deepseek_analysis}, f, indent=2)
            
        return {"status": "success", "file": filepath, "score": deepseek_analysis.get('seo_score')}

    def run_full_pipeline(self, languages: List[str] = None):
        if languages is None:
            languages = self.config.get("target_languages", ["en-US"])
        for lang in languages:
            self.execute_pipeline_for_language(lang)

if __name__ == "__main__":
    pipeline = GlobalSEOPipeline()
    pipeline.run_full_pipeline()
