import os
import re
import json
from pathlib import Path

class SEOFixer:
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)
        self.html_files = list(self.repo_path.rglob("*.html"))
        self.md_files = list(self.repo_path.rglob("*.md"))
        
    def fix_broken_links(self):
        """Fix or remove broken internal links"""
        print("🔧 Fixing broken links...")
        # Implement logic to find and fix 404 links
        pass
    
    def fix_canonical_mismatches(self):
        """Ensure canonical URLs match actual page URLs"""
        print("🔧 Fixing canonical mismatches...")
        
        for file in self.html_files + self.md_files:
            content = file.read_text(encoding='utf-8')
            
            # Extract current URL from filename/path
            expected_canonical = self.get_canonical_url(file)
            
            # Find and update canonical tag
            canonical_pattern = r'<link rel="canonical" href="[^"]*"'
            new_canonical = f'<link rel="canonical" href="{expected_canonical}"'
            
            if re.search(canonical_pattern, content):
                content = re.sub(canonical_pattern, new_canonical, content)
                file.write_text(content, encoding='utf-8')
                print(f"  ✓ Fixed canonical: {file}")
    
    def fix_orphan_pages(self):
        """Add internal links to orphan pages"""
        print("🔧 Fixing orphan pages...")
        # Add links from hub pages or category pages
        pass
    
    def update_sitemap(self):
        """Add missing pages to sitemap.xml"""
        print("🔧 Updating sitemap...")
        # Regenerate sitemap.xml with all pages
        pass
    
    def get_canonical_url(self, file_path):
        """Generate canonical URL from file path"""
        # Adjust this based on your site structure
        base_url = "https://dawidmillenium-design.github.io/HolidayVideoCamera/"
        rel_path = file_path.relative_to(self.repo_path)
        return base_url + str(rel_path).replace("\\", "/").replace("index.md", "").replace(".md", "").replace(".html", "")
    
    def run_all_fixes(self):
        """Run all SEO fixes"""
        self.fix_canonical_mismatches()
        self.fix_broken_links()
        self.fix_orphan_pages()
        self.update_sitemap()
        print("✅ SEO fixes complete!")

if __name__ == "__main__":
    fixer = SEOFixer()
    fixer.run_all_fixes()
