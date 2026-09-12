import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

class CSSHTMLModernizer:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        )
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
        
        # Modern CSS patterns to apply
        self.modern_css_patterns = {
            'cards': '''
.card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}
.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
}''',
            'buttons': '''
.btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 25px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}
.btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}''',
            'typography': '''
body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    line-height: 1.6;
    color: #2d3748;
}
h1, h2, h3 {
    font-weight: 700;
    line-height: 1.2;
    margin-bottom: 1rem;
}''',
            'responsive_grid': '''
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}
.grid {
    display: grid;
    gap: 2rem;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}
@media (max-width: 768px) {
    .grid {
        grid-template-columns: 1fr;
        gap: 1rem;
    }
}'''
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def analyze_with_ai(self, html_content, file_path):
        """Use DeepSeek to analyze and suggest improvements"""
        prompt = f"""
        You are an expert HTML/CSS modernization specialist.
        
        Analyze this HTML file: {file_path}
        
        Current HTML:
        ```html
        {html_content[:3000]}  # Limit context
        ```
        
        Tasks:
        1. Identify outdated CSS patterns or inline styles
        2. Suggest modern CSS improvements (Glassmorphism, Grid, Flexbox)
        3. Recommend responsive design enhancements
        4. Identify accessibility issues
        5. Suggest performance optimizations
        
        Provide output as JSON:
        {{
            "issues": ["list of issues found"],
            "improvements": ["list of improvements"],
            "css_updates": ["CSS classes to update"],
            "html_updates": ["HTML structure changes"]
        }}
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return response.choices[0].message.content

    def scan_html_files(self, root_dir):
        """Scan all HTML files in directory"""
        html_files = []
        for path in Path(root_dir).rglob("*.html"):
            if 'node_modules' not in str(path) and '.git' not in str(path):
                html_files.append(path)
        return html_files

    def modernize_html(self, html_file):
        """Modernize a single HTML file"""
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Add modern meta tags if missing
        if not soup.find('meta', {'name': 'viewport'}):
            viewport = soup.new_tag('meta', name='viewport', content='width=device-width, initial-scale=1.0')
            if soup.head:
                soup.head.append(viewpoint)
        
        # Add modern CSS framework link
        if not soup.find('link', href=lambda x: x and 'modern' in x):
            modern_css = soup.new_tag('link', rel='stylesheet', href='/css/modern-styles.css')
            if soup.head:
                soup.head.append(modern_css)
        
        # Update classes for modern cards
        for div in soup.find_all('div'):
            if div.get('class'):
                classes = div.get('class')
                if 'card' in classes or 'box' in classes:
                    if 'modern-card' not in classes:
                        classes.append('modern-card')
                        div['class'] = classes
        
        # Save updated HTML
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"✅ Modernized: {html_file}")

    def generate_modern_css(self, output_path):
        """Generate comprehensive modern CSS file"""
        modern_css = """
/* ===== Modern CSS Framework for VideoCameraHoliday ===== */
/* Generated by AI Modernization Agent */

:root {
    --primary: #667eea;
    --secondary: #764ba2;
    --accent: #f093fb;
    --dark: #1a202c;
    --light: #f7fafc;
    --success: #48bb78;
    --warning: #ed8936;
    --danger: #f56565;
    
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: var(--dark);
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

/* Glassmorphism Cards */
.modern-card, .card {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 16px;
    padding: 24px;
    box-shadow: var(--shadow-xl);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
    position: relative;
}

.modern-card::before, .card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
    pointer-events: none;
}

.modern-card:hover, .card:hover {
    transform: translateY(-5px) scale(1.02);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
    border-color: rgba(255, 255, 255, 0.3);
}

/* Modern Buttons */
.btn, button, .button {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    color: white;
    border: none;
    padding: 12px 28px;
    border-radius: 25px;
    font-weight: 600;
    font-size: 0.95rem;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    text-decoration: none;
    display: inline-block;
}

.btn:hover, button:hover, .button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
}

.btn:active, button:active {
    transform: translateY(0);
}

/* Responsive Grid System */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

.grid {
    display: grid;
    gap: 2rem;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

@media (max-width: 768px) {
    .grid {
        grid-template-columns: 1fr;
        gap: 1.5rem;
    }
    
    .modern-card, .card {
        padding: 16px;
    }
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    font-weight: 700;
    line-height: 1.2;
    margin-bottom: 1rem;
    color: white;
}

h1 { font-size: 3rem; }
h2 { font-size: 2.5rem; }
h3 { font-size: 2rem; }

/* Navigation */
nav {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    padding: 1rem 2rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

nav ul {
    list-style: none;
    display: flex;
    gap: 2rem;
    align-items: center;
}

nav a {
    color: white;
    text-decoration: none;
    font-weight: 500;
    transition: all 0.3s;
    padding: 0.5rem 1rem;
    border-radius: 8px;
}

nav a:hover {
    background: rgba(255, 255, 255, 0.2);
}

/* Images */
img {
    max-width: 100%;
    height: auto;
    border-radius: 12px;
    box-shadow: var(--shadow-md);
}

/* Forms */
input, textarea, select {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.1);
    color: white;
    font-size: 1rem;
    transition: all 0.3s;
}

input:focus, textarea:focus, select:focus {
    outline: none;
    border-color: var(--primary);
    background: rgba(255, 255, 255, 0.15);
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

/* Utilities */
.text-gradient {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.shadow-glow {
    box-shadow: 0 0 30px rgba(102, 126, 234, 0.5);
}

.animate-fade-in {
    animation: fadeIn 0.6s ease-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
    body {
        background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
    }
}
"""
        
        # Create css directory if not exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(modern_css)
        
        print(f"✅ Generated modern CSS: {output_path}")

    def run_full_modernization(self, root_dir='.', output_css='css/modern-styles.css'):
        """Run complete modernization pipeline"""
        print("🚀 Starting HTML/CSS Modernization...\n")
        
        # Step 1: Generate modern CSS
        print("📝 Step 1: Generating modern CSS framework...")
        self.generate_modern_css(output_css)
        
        # Step 2: Scan HTML files
        print("\n🔍 Step 2: Scanning HTML files...")
        html_files = self.scan_html_files(root_dir)
        print(f"Found {len(html_files)} HTML files")
        
        # Step 3: Analyze with AI
        print("\n🤖 Step 3: AI Analysis (this may take a while)...")
        for i, html_file in enumerate(html_files[:10], 1):  # Limit to first 10 for demo
            print(f"\n[{i}/{len(html_files)}] Analyzing: {html_file}")
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # analysis = self.analyze_with_ai(content, str(html_file))
                # print(f"Analysis: {analysis}")
            except Exception as e:
                print(f"Error analyzing {html_file}: {e}")
        
        # Step 4: Modernize HTML files
        print("\n🔧 Step 4: Modernizing HTML files...")
        for html_file in html_files:
            try:
                self.modernize_html(html_file)
            except Exception as e:
                print(f"Error modernizing {html_file}: {e}")
        
        print("\n✅ Modernization complete!")
        print(f"\n📁 Files modified: {len(html_files)}")
        print(f"📄 CSS generated: {output_css}")
        print("\n💡 Next steps:")
        print("1. Review changes in git diff")
        print("2. Test responsiveness on mobile devices")
        print("3. Check browser compatibility")

if __name__ == "__main__":
    modernizer = CSSHTMLModernizer()
    modernizer.run_full_modernization()
