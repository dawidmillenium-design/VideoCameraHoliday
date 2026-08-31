#!/usr/bin/env python3
"""Apply the shared navigation/footer shell without reformatting page content."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = "/VideoCameraHoliday/"

NAV = f'''<nav class="top-nav" aria-label="Primary navigation">
  <div class="nav-container">
    <a class="logo" href="{BASE}">📹 Holiday Video Camera</a>
    <button class="mobile-menu-toggle" type="button" aria-label="Toggle navigation" aria-expanded="false">☰</button>
    <ul class="nav-links">
      <li><a data-section="home" href="{BASE}">Home</a></li>
      <li><a data-section="city-through-the-lens" href="{BASE}city-through-the-lens/">Series</a></li>
      <li><a data-section="reviews" href="{BASE}reviews/">Reviews</a><ul class="dropdown-menu"><li><a href="{BASE}reviews/dji-osmo-pocket-3-review.html">DJI Pocket 3</a></li><li><a href="{BASE}reviews/gopro-hero-13-review.html">GoPro Hero 13</a></li><li><a href="{BASE}reviews/insta360-x5-review.html">Insta360 X5</a></li></ul></li>
      <li><a data-section="guides" href="{BASE}guides/">Buying Guides</a><ul class="dropdown-menu"><li><a href="{BASE}guides/best-holiday-video-cameras-2026.html">Best Cameras 2026</a></li><li><a href="{BASE}guides/best-budget-holiday-camera-under-500.html">Under $500</a></li><li><a href="{BASE}guides/best-waterproof-cameras-beach.html">Waterproof</a></li></ul></li>
      <li><a data-section="how-to" href="{BASE}how-to/">How-To</a></li><li><a data-section="destinations" href="{BASE}destinations/">Destinations</a></li><li><a data-section="editing" href="{BASE}editing/">Editing</a></li><li><a data-section="comparisons" href="{BASE}comparisons/">Comparisons</a></li><li><a data-section="about" href="{BASE}about/">About</a></li>
    </ul>
  </div>
</nav>'''

FOOTER = f'''<footer class="site-footer">
  <div class="footer-container">
    <section class="footer-section"><h4>Series</h4><ul><li><a href="{BASE}city-through-the-lens/">City Through the Lens</a></li><li><a href="{BASE}city-through-the-lens/#faq">Series FAQ</a></li></ul></section>
    <section class="footer-section"><h4>Guides</h4><ul><li><a href="{BASE}guides/best-holiday-video-cameras-2026.html">Best Cameras 2026</a></li><li><a href="{BASE}guides/best-budget-holiday-camera-under-500.html">Cameras Under $500</a></li><li><a href="{BASE}guides/best-waterproof-cameras-beach.html">Waterproof Cameras</a></li><li><a href="{BASE}guides/best-camera-hiking-holidays.html">Hiking Cameras</a></li></ul></section>
    <section class="footer-section"><h4>Reviews</h4><ul><li><a href="{BASE}reviews/dji-osmo-pocket-3-review.html">DJI Pocket 3</a></li><li><a href="{BASE}reviews/gopro-hero-13-review.html">GoPro Hero 13</a></li><li><a href="{BASE}reviews/insta360-x5-review.html">Insta360 X5</a></li></ul></section>
    <section class="footer-section"><h4>About</h4><ul><li><a href="{BASE}about/">About Us</a></li><li><a href="{BASE}">Home</a></li><li><a href="{BASE}sitemap.xml">Sitemap</a></li></ul></section>
  </div>
  <div class="footer-bottom"><p>© 2026 <a href="{BASE}">Holiday Video Camera</a> — Real travel camera testing. No lab charts.</p></div>
</footer>'''

STYLE = f'<link rel="stylesheet" href="{BASE}assets/site-shell.css">'
SCRIPT = f'<script src="{BASE}assets/site-shell.js" defer></script>'
NAV_RE = re.compile(r'<nav(?![^>]*class=["\'][^"\']*(?:breadcrumb|toc))[^>]*>.*?</nav>', re.I | re.S)
FOOTER_RE = re.compile(r'<footer\b[^>]*>.*?</footer>', re.I | re.S)

for page in sorted(ROOT.rglob('*.html')):
    text = page.read_text(encoding='utf-8')
    text = NAV_RE.sub('', text)
    text = FOOTER_RE.sub('', text)
    text = re.sub(r'\s*<link\s+rel=["\']stylesheet["\']\s+href=["\']/VideoCameraHoliday/assets/site-shell\.css["\']\s*/?>', '', text, flags=re.I)
    text = re.sub(r'\s*<script\s+src=["\']/VideoCameraHoliday/assets/site-shell\.js["\']\s+defer></script>', '', text, flags=re.I)
    # Load this after page-specific styles so the shared shell stays consistent.
    text = re.sub(r'(</head>)', '\n    ' + STYLE + r'\n\1', text, count=1, flags=re.I)
    text = re.sub(r'(<body\b[^>]*>)', r'\1\n' + NAV, text, count=1, flags=re.I)
    text = re.sub(r'(</body>)', FOOTER + '\n' + SCRIPT + r'\n\1', text, count=1, flags=re.I)
    page.write_text(text, encoding='utf-8')

print(f'Applied shared shell to {len(list(ROOT.rglob("*.html")))} HTML pages.')
