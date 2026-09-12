import os
import json
import re
import requests
import yaml
from typing import Dict, Any, List

class GlobalSEOPipeline:
    """Orchestrates the multi-agent SEO content generation pipeline."""

    def __init__(self, config_path: str = "global_seo_crew.yaml"):
        """Initialize the pipeline with configuration."""
        self.base_url = "https://dawidmillenium-design.github.io/HolidayVideoCamera/"
        
        # Load DeepSeek API Key from environment variables (Set in GitHub Secrets)
        self.deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_API_KEY_HERE")
        self.deepseek_api_url = "https://api.deepseek.com/v1/chat/completions"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: {config_path} not found. Using default settings.")
            self.config = {"target_languages": ["en-US"]}

    # ==========================================
    # EXISTING METHODS (Simulated for context)
    # ==========================================
    def generate_keyword_research(self, language: str) -> Dict[str, Any]:
        # Simulated: Identifies high-volume, low-competition keywords
        return {"primary": "best travel camera", "long_tail": ["compact camera for travel"], "search_intent": "commercial_investigation"}

    def generate_competitor_analysis(self, primary_kw: str, language: str) -> Dict[str, Any]:
        # Simulated: Analyzes top 5 SERP results
        return {"avg_word_count": 3500, "top_headings": ["Top Features", "Best Models"]}

    def generate_content_brief(self, language: str, keywords: Dict, competitor_data: Dict) -> Dict[str, Any]:
        # Simulated: Creates localized content briefs
        return {
            "h2_outline": ["Introduction", "Top Features", "Best Models 2026", "Buying Guide"],
            "target_word_count": competitor_data.get("avg_word_count", 4000),
            "tone": "Authoritative & Engaging",
            "target_audience": "Travel Vloggers"
        }

    def generate_schema_markup(self, language: str, primary_kw: str, canonical_url: str) -> Dict[str, Any]:
        # Simulated: Generates JSON-LD schema
        return {
            "meta_title": f"Best Travel Cameras for {language} in 2026",
            "meta_description": f"Discover the best travel cameras in {language}.",
            "json_ld": {}
        }

    def generate_internal_link_map(self, language: str) -> Dict[str, Any]:
        # Simulated: Injects 15-25 contextual internal links
        return {"hub_links": ["/reviews/"], "cluster_links": [], "regional_links": []}

    # ==========================================
    # 🚀 NEW: DEEPSEEK ON-PAGE SCORING ENGINE
    # ==========================================
    def score_content_with_deepseek(self, content: str, target_keyword: str) -> Dict[str, Any]:
        """
        Uses DeepSeek API to score generated HTML content similarly to SurferSEO or Scalenut.
        Acts as a Quality Gate before the final output is saved.
        """
        print(f"  -> Sending content to DeepSeek API for keyword: '{target_keyword}'...")
        
        # Truncate content to avoid exceeding token limits (approx 6000 words)
        truncated_content = content[:8000] 
        
        prompt = f"""You are an expert on-page SEO auditor (like SurferSEO). 
        Analyze the following content for the target keyword: "{target_keyword}".
        
        Strictly evaluate:
        1. Word count (Target: > 2500 words for pillar content).
        2. Keyword density (Ideal: 0.8% - 1.5%).
        3. Heading structure (H1-H3 must contain keyword variations).
        4. Readability (Paragraph length, use of lists/bolding).
        
        Return ONLY a valid JSON object matching this schema. No markdown wrapping.
        {{
          "seo_score": 0,
          "word_count": 0,
          "keyword_density_percent": 0.0,
          "heading_analysis": "string",
          "missing_semantic_keywords": ["keyword1", "keyword2"],
          "actionable_fixes": ["Fix 1", "Fix 2"]
        }}

        Content to analyze:
        {truncated_content}
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.deepseek_api_key}"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a strict SEO auditor. Always respond with valid JSON matching the requested schema."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = requests.post(self.deepseek_api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
            # Clean potential markdown wrapping just in case
            ai_response = re.sub(r'^```json\s*', '', ai_response, flags=re.MULTILINE)
            ai_response = re.sub(r'\s*```$', '', ai_response, flags=re.MULTILINE)
            
            return json.loads(ai_response)
            
        except Exception as e:
            print(f"  ⚠️ DeepSeek API Error: {e}")
            return {
                "seo_score": 0,
                "word_count": 0,
                "keyword_density_percent": 0.0,
                "heading_analysis": "Failed to analyze",
                "missing_semantic_keywords": [],
                "actionable_fixes": [f"API Error: {str(e)}"]
            }

    # ==========================================
    # UPDATED EXECUTION PIPELINE
    # ==========================================
    def execute_pipeline_for_language(self, language: str) -> Dict[str, Any]:
        """Execute the full pipeline for a single language."""
        print(f"\n{'='*60}")
        print(f"Processing language: {language}")
        print(f"{'='*60}")

        # Step 1: Keyword Research
        print("\n[1/7] Keyword Research...")
        keywords = self.generate_keyword_research(language)
        print(f"Primary KW: {keywords['primary']}")

        # Step 2: Competitor Analysis
        print("\n[2/7] Competitor Analysis...")
        competitor_data = self.generate_competitor_analysis(keywords['primary'], language)
        print(f"Avg word count: {competitor_data['avg_word_count']}")

        # Step 3: Content Brief
        print("\n[3/7] Creating Content Brief...")
        content_brief = self.generate_content_brief(language, keywords, competitor_data)
        print(f"Target word count: {content_brief['target_word_count']}")

        # Step 4: Schema Generation
        print("\n[4/7] Generating Schema Markup...")
        canonical_url = f"{self.base_url}{language}/guias/nuevas-camaras-2026/"
        schema = self.generate_schema_markup(language, keywords['primary'], canonical_url)
        print(f"Meta title: {schema['meta_title']}")

        # Step 5: EEAT Validation (simulated)
        print("\n[5/7] Validating EEAT...")
        eeat_checklist = {
            "author_box": True,
            "testing_methodology": True,
            "local_locations": True,
            "pros_and_cons": True,
            "last_updated": True
        }
        print("EEAT Checklist: All items passed ✓")

        # Step 6: Internal Link Mapping
        print("\n[6/7] Building Internal Links...")
        link_map = self.generate_internal_link_map(language)
        print(f"Total links: {len(link_map['hub_links']) + len(link_map['cluster_links']) + len(link_map['regional_links'])}")

        # 🚀 NEW STEP 7: DEEPSEEK ON-PAGE SCORING (Quality Gate)
        print("\n[7/7] Simulating Content Generation & Running DeepSeek Scorer...")
        # In a real scenario, your 'content_creator' agent generates the full HTML here. 
        # We simulate a generated HTML block to pass to DeepSeek for this demonstration:
        simulated_html = f"""
        <h1>{schema['meta_title']}</h1>
        <p>This is a simulated generated article about the {keywords['primary']} for {language} market.</p>
        <h2>Top Features of {keywords['primary']}</h2>
        <p>Detailed breakdown of sensor size, megapixels, and low-light performance.</p>
        <h2>Buying Guide</h2>
        <p>How to choose the right camera for your next trip.</p>
        """
        
        # Call DeepSeek
        deepseek_analysis = self.score_content_with_deepseek(simulated_html, keywords['primary'])
        print(f"DeepSeek SEO Score: {deepseek_analysis.get('seo_score', 'N/A')}/100")
        
        if deepseek_analysis.get('seo_score', 0) < 75:
            print("⚠️ Quality Gate Triggered: Score is below 75! The content_creator agent should rewrite this content.")
            
        # Compile final output
        output = {
            "language": language,
            "meta_data": {
                "title": schema['meta_title'],
                "description": schema['meta_description'],
                "canonical_url": canonical_url
            },
            "schema_markup": schema,
            "content_brief": content_brief,
            "internal_link_map": link_map,
            "keywords": keywords,
            "competitor_data": competitor_data,
            "eeat_validation": eeat_checklist,
            "deepseek_seo_analysis": deepseek_analysis # Added DeepSeek results to output
        }

        return output

    def save_intermediate_json(self, language: str, data: Dict[str, Any]):
        """Save intermediate JSON data following the schema."""
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"{language}_seo_data.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved data to {filepath}")

    def run_full_pipeline(self, languages: List[str] = None):
        """Run the pipeline for all target languages or specified subset."""
        if languages is None:
            languages = self.config.get("target_languages", ["en-US"])
            
        results = {}
        for lang in languages:
            try:
                output = self.execute_pipeline_for_language(lang)
                self.save_intermediate_json(lang, output)
                results[lang] = output
                print(f"\n✓ Completed pipeline for {lang}")
            except Exception as e:
                print(f"✗ Failed pipeline for {lang}: {e}")
                results[lang] = {"error": str(e)}
                
        return results

if __name__ == "__main__":
    pipeline = GlobalSEOPipeline()
    pipeline.run_full_pipeline()
