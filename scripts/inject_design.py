#!/usr/bin/env python3
"""
Inject Design B header/footer/drawer into all HTML files in the repository.
Uses marker-based replacement so it can be run multiple times safely.
"""

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup

# Configuration
REPO_ROOT = Path(__file__).parent.parent
TEMPLATE_FILE = REPO_ROOT / "templates" / "design-b.html"
EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", "workspace", 
    "generated-content", "data", "media", "assets", "scripts"
}
# Only process HTML files in these top-level directories
TARGET_DIRS = {
    ".", "about", "accessories", "comparisons", "destinations", 
    "editing", "guides", "how-to", "reviews", "city-through-the-lens",
    "de-DE", "de", "es-ES", "es", "fr-FR", "it-IT", "ja-JP", "jp",
    "ko-KR", "pl-PL", "pt-br", "th-TH", "zh-CN"
}

def load_template():
    """Read the template file and extract the three sections."""
    if not TEMPLATE_FILE.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE_FILE}")
    
    content = TEMPLATE_FILE.read_text(encoding="utf-8")
    
    sections = {}
    for name in ["HEAD", "HEADER", "FOOTER"]:
        start_marker = f"<!-- === DESIGN-B-{name}-START === -->"
        end_marker = f"<!-- === DESIGN-B-{name}-END === -->"
        
        pattern = re.escape(start_marker) + r"(.*?)" + re.escape(end_marker)
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            raise ValueError(f"Missing section: {name} (markers not found)")
        
        sections[name.lower()] = match.group(1).strip()
    
    return sections

def process_file(file_path, sections):
    """Inject the Design B sections into a single HTML file."""
    try:
        html = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"  ⚠️  Skipping (encoding error): {file_path}")
        return False
    
    original = html
    
    # --- 1. Replace the <head> CSS block ---
    # Look for the first <style>...</style> inside <head>
    head_match = re.search(
        r'(<head[^>]*>)(.*?)(</head>)',
        html, re.DOTALL | re.IGNORECASE
    )
    if head_match:
        head_open, head_content, head_close = head_match.groups()
        
        # Remove all existing <style> blocks inside <head>
        head_content_clean = re.sub(
            r'<style[^>]*>.*?</style>', '', 
            head_content, flags=re.DOTALL | re.IGNORECASE
        )
        
        # Insert the new HEAD section right before </head>
        new_head = head_open + head_content_clean + sections["head"] + "\n" + head_close
        html = html[:head_match.start()] + new_head + html[head_match.end():]
    
    # --- 2. Replace the <header> (nav) block ---
    # Find everything between <body> and <main> or <article>
    body_match = re.search(r'(<body[^>]*>)', html, re.DOTALL | re.IGNORECASE)
    if body_match:
        body_start = body_match.end()
        
        # Find where the main content starts
        main_match = re.search(
            r'(<main[^>]*>|<article[^>]*>|<section[^>]*class="hero")',
            html[body_start:], re.DOTALL | re.IGNORECASE
        )
        
        if main_match:
            header_end = body_start + main_match.start()
            
            # Replace everything between <body> and <main> with the new header
            html = (
                html[:body_start] + "\n\n" +
                sections["header"] + "\n\n" +
                html[header_end:]
            )
    
    # --- 3. Replace the footer + scripts block ---
    # Find the last </footer> or </body> and replace everything before </body>
    footer_match = re.search(
        r'(</footer>|</main>|</article>)(.*?)(</body>)',
        html, re.DOTALL | re.IGNORECASE
    )
    if footer_match:
        footer_close, between, body_close = footer_match.groups()
        
        # Remove existing footer + scripts, insert new FOOTER section
        html = (
            html[:footer_match.start()] + 
            footer_close + "\n\n" +
            sections["footer"] + "\n\n" +
            body_close + html[footer_match.end():]
        )
    
    # --- 4. Write back if changed ---
    if html != original:
        file_path.write_text(html, encoding="utf-8")
        return True
    return False

def main():
    print("🚀 Design B Injection — Starting")
    print(f"📄 Template: {TEMPLATE_FILE}")
    
    sections = load_template()
    print(f"✅ Loaded sections: {', '.join(sections.keys())}")
    
    processed = 0
    updated = 0
    skipped = 0
    
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        
        # Only process files in target directories
        rel_path = Path(dirpath).relative_to(REPO_ROOT)
        if str(rel_path) not in TARGET_DIRS and str(rel_path) != ".":
            # Allow nested dirs within target dirs (e.g., guides/subdir)
            if not any(str(rel_path).startswith(t) for t in TARGET_DIRS if t != "."):
                continue
        
        for filename in filenames:
            if not filename.endswith(".html"):
                continue
            
            file_path = Path(dirpath) / filename
            processed += 1
            
            try:
                if process_file(file_path, sections):
                    updated += 1
                    print(f"  ✅ Updated: {file_path.relative_to(REPO_ROOT)}")
            except Exception as e:
                skipped += 1
                print(f"  ❌ Error: {file_path.relative_to(REPO_ROOT)} — {e}")
    
    print(f"\n📊 Summary: {processed} files scanned, {updated} updated, {skipped} errors")
    print("✨ Done.")

if __name__ == "__main__":
    main()
