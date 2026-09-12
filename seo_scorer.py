import os
import sys
import json
import re
import requests

try:
    import yaml
except ImportError:
    print("Installing pyyaml...")
    os.system("pip install pyyaml")
    import yaml

def extract_frontmatter(content):
    """Extracts YAML frontmatter from Jekyll markdown files."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if match:
        return yaml.safe_load(match.group(1)) or {}
    return {}

def analyze_seo_with_deepseek(content, target_keyword):
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is not set.")
    
    # Truncate to ~6000 words to stay well within DeepSeek's context window and save tokens
    truncated_content = content[:8000] 
    
    prompt = f"""You are an expert on-page SEO auditor, similar to SurferSEO or Scalenut. 
Analyze the following markdown/HTML content for the target keyword: "{target_keyword}".

Evaluate these criteria strictly:
1. Word count (flag if < 800 words for pillar content).
2. Keyword density (ideal is 1.0% - 2.0% for the primary keyword).
3. Heading structure (H1 must contain the keyword, H2/H3 should contain semantic variations).
4. Readability (use of lists, tables, bold text, short paragraphs).
5. Missing semantic/LSI keywords that top-ranking travel/camera pages would include.

Return ONLY a valid JSON object matching this exact schema. Do not include markdown formatting like ```json.
{{
  "score": 0,
  "word_count": 0,
  "keyword_density_percent": 0.0,
  "heading_analysis": "Brief analysis of H1-H3 structure",
  "missing_keywords": ["keyword1", "keyword2"],
  "recommendations": ["Recommendation 1", "Recommendation 2"]
}}

Content to analyze:
{truncated_content}
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a strict, expert SEO auditor. Always respond with valid JSON matching the requested schema."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=data)
    response.raise_for_status()
    
    result = response.json()
    content_response = result["choices"][0]["message"]["content"]
    
    # Clean up any potential markdown wrapping just in case
    content_response = re.sub(r'^```json\s*', '', content_response, flags=re.MULTILINE)
    content_response = re.sub(r'\s*```$', '', content_response, flags=re.MULTILINE)
    
    return json.loads(content_response)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python seo_scorer.py <file_path>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        frontmatter = extract_frontmatter(content)
        target_keyword = frontmatter.get("target_keyword", frontmatter.get("tags", ["travel camera"])[0])
        
        print(f"::notice::Analyzing '{file_path}' for keyword: '{target_keyword}'")
        
        seo_analysis = analyze_seo_with_deepseek(content, target_keyword)
        
        print("::group::DeepSeek SEO Analysis Result")
        print(json.dumps(seo_analysis, indent=2))
        print("::endgroup::")
        
        # Format output for GitHub Actions
        recommendations = "\n- " + "\n- ".join(seo_analysis['recommendations'])
        missing_kw = ", ".join(seo_analysis['missing_keywords'])
        
        with open(os.environ.get('GITHUB_OUTPUT', 'seo_output.txt'), 'a') as f:
            f.write(f"seo_score={seo_analysis['score']}\n")
            f.write(f"seo_word_count={seo_analysis['word_count']}\n")
            f.write(f"seo_density={seo_analysis['keyword_density_percent']}%\n")
            f.write(f"seo_recommendations<<EOF\n{recommendations}\nEOF\n")
            f.write(f"seo_missing_keywords={missing_kw}\n")
            
        if seo_analysis['score'] < 70:
            print(f"::warning file={file_path}::SEO Score is {seo_analysis['score']}/100. Please review recommendations before merging.")
            # Uncomment the next line to strictly block merges with low SEO scores
            # sys.exit(1) 
            
    except Exception as e:
        print(f"::error::Failed to analyze SEO for {file_path}: {str(e)}")
        sys.exit(1)
