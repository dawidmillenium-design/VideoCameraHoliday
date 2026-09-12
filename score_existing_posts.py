import os
import re
import json
import requests
from pathlib import Path

class ExistingPostAuditor:
    def __init__(self):
        self.api_key = os.environ.get("DEEPSEEK_API_KEY")
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        # Adjust these paths to match your Jekyll structure
        self.search_dirs = ["_posts", "reviews", "destinations", "how-to"]

    def find_markdown_files(self):
        files = []
        for directory in self.search_dirs:
            if os.path.exists(directory):
                files.extend(list(Path(directory).rglob("*.md")))
        return files

    def extract_keyword_from_frontmatter(self, content):
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if match:
            import yaml
            fm = yaml.safe_load(match.group(1)) or {}
            return fm.get("target_keyword") or fm.get("tags", ["travel camera"])[0]
        return "travel camera" # fallback

    def score_post(self, filepath, content, keyword):
        print(f"  Scoring: {filepath} (Keyword: '{keyword}')")
        truncated = content[:8000]
        prompt = f"""You are an expert SEO auditor. Analyze this Markdown for: "{keyword}".
        Return ONLY valid JSON: {{"seo_score": 0, "word_count": 0, "keyword_density_percent": 0.0, "missing_semantic_keywords": [], "actionable_fixes": []}}
        Content: {truncated}"""
        
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a strict SEO auditor. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"]
            result = re.sub(r'^```json\s*', '', result, flags=re.MULTILINE)
            result = re.sub(r'\s*```$', '', result, flags=re.MULTILINE)
            return json.loads(result)
        except Exception as e:
            return {"error": str(e)}

    def run_audit(self):
        files = self.find_markdown_files()
        print(f"Found {len(files)} Markdown files to audit.\n")
        
        results = {}
        for filepath in files:
            content = filepath.read_text(encoding='utf-8')
            keyword = self.extract_keyword_from_frontmatter(content)
            score_data = self.score_post(str(filepath), content, keyword)
            results[str(filepath)] = score_data
            
            # Print quick summary
            score = score_data.get("seo_score", "N/A")
            print(f"  -> Score: {score}/100 | Words: {score_data.get('word_count', 'N/A')}\n")

        # Save full report
        with open("existing_posts_seo_audit.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print("✅ Full audit report saved to: existing_posts_seo_audit.json")

if __name__ == "__main__":
    auditor = ExistingPostAuditor()
    auditor.run_audit()
