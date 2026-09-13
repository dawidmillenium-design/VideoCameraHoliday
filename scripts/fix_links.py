import os
import re
from pathlib import Path

# Configuration
TARGET_DIR = "."  # Root of the repository
HTML_EXTENSIONS = {".html", ".htm"}

# 1. Path Normalization Rules (Old -> New)
PATH_REPLACEMENTS = [
    ("../index.html", "/index.html"),
    ("../blog.html", "/blog.html"),
    ("../about.html", "/about.html"),
    ("../contact.html", "/contact.html"),
    ("../privacy.html", "/privacy.html"),
    ("../terms.html", "/terms.html"),
    ("../disclaimer.html", "/disclaimer.html"),
    ("../css/style.css", "/css/style.css"),
    ("../js/main.js", "/js/main.js"),
    ('href="style.css"', 'href="/css/style.css"'),
    ("href='style.css'", "href='/css/style.css'"),
]

# 2. Missing Content Stubs to Generate
MISSING_STUBS = [
    "reviews/dji-osmo-pocket-3-review.html",
    "reviews/gopro-hero-13-review.html",
    "city-through-the-lens/index.html",
    "guides/best-holiday-video-cameras-2026.html",
    "reviews/dji-osmo-action-5-review.html",
    "guides/best-budget-holiday-camera-under-500.html",
    "reviews/sony-zv-1-ii-review.html",
    "reviews/insta360-x5-review.html",
    "reviews/iphone-16-pro-video-review.html",
]

STUB_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - VideoCameraHoliday</title>
    <meta name="description" content="Comprehensive review and guide for {title}. Our travel videography team is currently finalizing this detailed analysis. Check back soon!">
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <header>
        <nav>
            <a href="/">Home</a> | <a href="/blog.html">Blog</a> | <a href="/reviews/">Reviews</a>
        </nav>
    </header>
    <main>
        <h1>{title}</h1>
        <p><em>🚧 Under Construction 🚧</em></p>
        <p>Our travel videography team is currently writing this comprehensive review and guide. We are testing the gear in real-world conditions to bring you the most accurate, hands-on advice.</p>
        <p>Check back soon, or <a href="/">return to the homepage</a> to explore our completed guides.</p>
    </main>
    <footer>
        <p>&copy; 2026 VideoCameraHoliday. All rights reserved.</p>
    </footer>
    <script src="/js/main.js"></script>
</body>
</html>"""

def find_html_files():
    """Find all HTML files and print debug info"""
    html_files = []
    total_files = 0
    
    print(" Scanning repository for HTML files...")
    for root, dirs, files in os.walk(TARGET_DIR):
        # Skip hidden directories and common non-source folders
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'venv', 'node_modules', '.git', '__pycache__', 'scripts'}]
        
        for file in files:
            total_files += 1
            if Path(file).suffix.lower() in HTML_EXTENSIONS:
                file_path = Path(root) / file
                html_files.append(file_path)
    
    print(f"📊 Total files scanned: {total_files}")
    print(f"📄 HTML files found: {len(html_files)}")
    
    if len(html_files) > 0:
        print(f"📍 Sample files found:")
        for f in html_files[:5]:  # Show first 5
            print(f"   - {f}")
    
    return html_files

def fix_html_files(html_files):
    """Fix broken links in HTML files"""
    total_files_modified = 0
    total_replacements = 0
    
    for file_path in html_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            file_replacements = 0
            
            # CRITICAL FIX: Remove /VideoCameraHoliday/ prefix globally in href and src
            matches = re.findall(r'/VideoCameraHoliday/', content)
            if matches:
                file_replacements += len(matches)
                content = re.sub(r'(["\'])(\/VideoCameraHoliday\/)', r'\1/', content)
                content = content.replace('/VideoCameraHoliday/', '/')
            
            # Apply specific relative path replacements
            for old_path, new_path in PATH_REPLACEMENTS:
                count = content.count(old_path)
                if count > 0:
                    file_replacements += count
                    content = content.replace(old_path, new_path)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                total_files_modified += 1
                total_replacements += file_replacements
                print(f"  ✏️  Modified {file_path} ({file_replacements} replacements)")
                
        except Exception as e:
            print(f"⚠️ Error processing {file_path}: {e}")
            
    return total_files_modified, total_replacements

def create_stubs():
    """Create missing stub pages"""
    stubs_created = 0
    for stub_path in MISSING_STUBS:
        full_path = Path(TARGET_DIR) / stub_path
        if not full_path.exists():
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Extract readable title from filename
            filename = full_path.stem.replace('-', ' ').title()
            title = f"{filename} Review" if 'review' in stub_path else filename
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(STUB_TEMPLATE.format(title=title))
            stubs_created += 1
            print(f"✅ Created stub: {full_path}")
        else:
            print(f"⏭️  Stub already exists: {full_path}")
            
    return stubs_created

if __name__ == "__main__":
    print("🚀 Starting Link Remediation Script...")
    print("=" * 60)
    
    # Find HTML files with debug output
    html_files = find_html_files()
    print("=" * 60)
    
    if len(html_files) == 0:
        print("❌ ERROR: No HTML files found!")
        print("💡 Current working directory:", os.getcwd())
        print(" Directory contents:", os.listdir('.'))
        exit(1)
    
    # Fix the files
    print("🔧 Fixing broken links...")
    modified, replacements = fix_html_files(html_files)
    print(f"✅ Modified {modified} HTML files with {replacements} total replacements.")
    
    # Create stubs
    print("\n📝 Creating missing stub pages...")
    stubs = create_stubs()
    print(f"✅ Created {stubs} missing stub pages.")
    
    print("\n" + "=" * 60)
    print("🎉 Remediation complete! Run your audit again to verify.")
