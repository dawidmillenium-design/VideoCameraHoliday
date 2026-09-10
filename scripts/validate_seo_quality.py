#!/usr/bin/env python3
"""
SEO Quality Validator
Checks generated articles for critical SEO issues before publishing.
"""

import json
from pathlib import Path
from bs4 import BeautifulSoup

def validate_article(filepath: str) -> dict:
    """Check a single article for critical SEO issues."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'lxml')
        
        issues = []
        
        # Check title
        title = soup.find('title')
        if not title or not title.text.strip():
            issues.append("Missing title")
        elif len(title.text.strip()) > 60:
            issues.append(f"Title too long ({len(title.text)} chars)")
            
        # Check meta description
        desc = soup.find('meta', attrs={'name': 'description'})
        if not desc or not desc.get('content', '').strip():
            issues.append("Missing meta description")
        elif len(desc.get('content', '')) < 120:
            issues.append(f"Meta description too short ({len(desc.get('content', ''))} chars)")
            
        # Check canonical URL
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if not canonical or not canonical.get('href', '').strip():
            issues.append("Missing canonical URL")
            
        # Check H1 heading
        h1s = soup.find_all('h1')
        if len(h1s) == 0:
            issues.append("No H1 heading found")
        elif len(h1s) > 1:
            issues.append(f"Multiple H1s found ({len(h1s)})")
            
        # Check schema markup
        schema = soup.find('script', attrs={'type': 'application/ld+json'})
        if not schema:
            issues.append("Missing schema.org JSON-LD markup")
            
        return {
            "file": str(filepath),
            "valid": len(issues) == 0,
            "issues": issues
        }
    except Exception as e:
        return {
            "file": str(filepath),
            "valid": False,
            "issues": [f"Error parsing file: {str(e)}"]
        }

def main():
    print(" Starting SEO Quality Validation...")
    print("=" * 60)
    
    generated_dir = Path("generated-content")
    if not generated_dir.exists():
        print("❌ generated-content/ directory not found")
        return
        
    results = []
    valid_count = 0
    invalid_count = 0
    
    # Scan all HTML files in generated-content
    for html_file in generated_dir.rglob("*.html"):
        # Skip metadata files
        if 'metadata' in html_file.name:
            continue
            
        result = validate_article(html_file)
        results.append(result)
        
        if result["valid"]:
            valid_count += 1
            print(f"✅ {html_file.name}: Valid")
        else:
            invalid_count += 1
            print(f"❌ {html_file.name}: {', '.join(result['issues'])}")
            
    # Save validation report
    report = {
        "total_files": len(results),
        "valid": valid_count,
        "invalid": invalid_count,
        "details": results
    }
    
    with open("seo-validation-report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        
    print("\n" + "=" * 60)
    print(f"📊 Validation Summary:")
    print(f"   Total files: {len(results)}")
    print(f"   ✅ Valid: {valid_count}")
    print(f"   ❌ Invalid: {invalid_count}")
    print(f"📁 Report saved to: seo-validation-report.json")
    
    if invalid_count > 0:
        print("\n⚠️  Some articles have SEO issues. Review the report before publishing.")
    else:
        print("\n🎉 All articles passed SEO validation!")

if __name__ == "__main__":
    main()
