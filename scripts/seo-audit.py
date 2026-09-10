#!/usr/bin/env python3
"""
SEO & Quality Audit Script for VideoCameraHoliday
Scans real HTML pages and scores: On-page SEO, EEAT, Internal Links, HTML Quality.
Excludes build output, backups, partials, and template/diff files.
"""

import os
import re
import json
import sys
import fnmatch
from urllib.parse import urlparse
from html.parser import HTMLParser

try:
    from bs4 import BeautifulSoup
except ImportError:
    os.system(f"{sys.executable} -m pip install beautifulsoup4")
    from bs4 import BeautifulSoup


# =====================================================================
# Directories and files to skip
# =====================================================================
SKIP_DIRS = {
    '.git', '.github', 'node_modules', '__pycache__',
    '_site',                          # Jekyll build output
    'city-through-the-lens-backup',   # backup folder
    'workspace',                      # WIP drafts
    'city-generator',                 # generator staging output
    '_includes', '_layouts',          # partials, not pages
}

SKIP_GLOBS = [
    '*_diff.html', '*_template.html', '*_original.html',
    'comparison_template.html', 'comparisons_original.html',
    'MEGA_MENU_INTEGRATION_EXAMPLE.html',
    'mega-menu-nav.html', 'mega-menu-footer.html',
    'toc.html.html',
]
SKIP_RE = [
    re.compile(r'^google[0-9a-f]+\.html$', re.I),
]


def should_skip_file(name):
    if not name.lower().endswith('.html'):
        return True
    low = name.lower()
    for g in SKIP_GLOBS:
        if fnmatch.fnmatch(low, g.lower()):
            return True
    for rx in SKIP_RE:
        if rx.match(name):
            return True
    return False


# =====================================================================
# HTML quality helper
# =====================================================================
class HTMLQualityChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inline_styles = 0
        self.deprecated_tags = []
        self.semantic_tags = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if 'style' in attrs_dict:
            self.inline_styles += 1
        if tag in ('font', 'center', 'big', 'strike', 'tt', 'frame', 'frameset'):
            self.deprecated_tags.append(tag)
        if tag in ('article', 'section', 'nav', 'header', 'footer', 'aside', 'main'):
            self.semantic_tags.append(tag)


# =====================================================================
# Scorers
# =====================================================================
def calculate_seo_score(soup, html_content, url_path):
    score, max_score, issues = 0, 100, []

    # Title (15)
    title = soup.find('title')
    if title and title.get_text().strip():
        n = len(title.get_text().strip())
        if 50 <= n <= 60:    score += 15
        elif 30 <= n <= 70:  score += 10; issues.append(f"Title length {n} outside 50-60")
        else:                score += 5;  issues.append(f"Title length {n} not optimal")
    else:
        issues.append("Missing title tag")

    # Meta description (15)
    md = soup.find('meta', attrs={'name': 'description'})
    if md and md.get('content'):
        n = len(md['content'].strip())
        if 150 <= n <= 160:  score += 15
        elif 120 <= n <= 180: score += 10; issues.append(f"Meta desc length {n} outside 150-160")
        else:                 score += 5;  issues.append(f"Meta desc length {n} not optimal")
    else:
        issues.append("Missing meta description")

    # H1 (10)
    h1s = soup.find_all('h1')
    if len(h1s) == 1: score += 10
    elif len(h1s) == 0: issues.append("Missing H1 tag")
    else: score += 5; issues.append(f"Multiple H1 tags ({len(h1s)})")

    # Canonical (10)
    if soup.find('link', rel='canonical'):
        score += 10
    else:
        issues.append("Missing canonical URL")

    # Img alt (10)
    imgs = soup.find_all('img')
    if imgs:
        with_alt = sum(1 for i in imgs if i.get('alt'))
        pct = with_alt / len(imgs) * 100
        if pct == 100: score += 10
        elif pct >= 80: score += 7; issues.append(f"{len(imgs)-with_alt} images missing alt")
        else:           score += 3; issues.append(f"Only {pct:.0f}% images have alt")
    else:
        score += 10

    # Open Graph (10)
    og = soup.find_all('meta', property=re.compile('^og:'))
    if len(og) >= 4: score += 10
    elif len(og) >= 2: score += 5; issues.append("Incomplete Open Graph tags")
    else: issues.append("Missing Open Graph tags")

    # Twitter (5)
    if soup.find('meta', attrs={'name': 'twitter:card'}):
        score += 5
    else:
        issues.append("Missing Twitter card")

    # JSON-LD (10)
    if soup.find_all('script', type='application/ld+json'):
        score += 10
    else:
        issues.append("Missing structured data (JSON-LD)")

    # Robots (5)
    if soup.find('meta', attrs={'name': 'robots'}):
        score += 5
    else:
        issues.append("Missing robots meta tag")

    # Viewport (5)
    if soup.find('meta', attrs={'name': 'viewport'}):
        score += 5
    else:
        issues.append("Missing viewport meta")

    # lang (5)
    if soup.find('html', lang=True):
        score += 5
    else:
        issues.append("Missing lang attribute")

    return score, max_score, issues


def calculate_eeat_score(soup, html_content, url_path):
    score, max_score, issues = 0, 100, []
    text_low = html_content.lower()

    author_meta = soup.find('meta', attrs={'name': 'author'})
    author_box = soup.find(class_=re.compile('author', re.I))
    if author_meta or author_box:
        score += 15
    else:
        issues.append("No author information found")

    if author_box and len(author_box.get_text()) > 50:
        score += 15
    elif author_box:
        score += 8; issues.append("Author bio too short")
    else:
        issues.append("Missing author bio")

    json_ld = soup.find_all('script', type='application/ld+json')
    has_pub = any('datePublished' in str(s) for s in json_ld)
    has_mod = any('dateModified' in str(s) for s in json_ld)

    if soup.find('meta', attrs={'property': 'article:published_time'}) or has_pub:
        score += 10
    else:
        issues.append("Missing publication date")

    if soup.find('meta', attrs={'property': 'article:modified_time'}) or has_mod:
        score += 10
    else:
        issues.append("Missing last modified date")

    if soup.find_all('a', href=re.compile('/about', re.I)):
        score += 10
    else:
        issues.append("No link to About page")

    if any(k in text_low for k in ['contact', 'mailto:', '@']):
        score += 10
    else:
        issues.append("No contact information")

    if any(k in text_low for k in ['expert', 'professional', 'experience', 'years',
                                   'videographer', 'photographer', 'tested', 'reviewed']):
        score += 10
    else:
        issues.append("No expertise indicators")

    trust = sum(1 for k in ['affiliate', 'disclosure', 'privacy', 'terms', 'cookie']
                if k in text_low)
    if trust >= 2:   score += 10
    elif trust == 1: score += 5; issues.append("Limited trust signals")
    else:            issues.append("Missing trust signals")

    external = [a for a in soup.find_all('a', href=True)
                if urlparse(a['href']).netloc and 'github.io' not in a['href']]
    if len(external) >= 3:   score += 10
    elif len(external) >= 1: score += 5; issues.append("Few external authoritative links")
    else:                    issues.append("No external authoritative links")

    return score, max_score, issues


def calculate_internal_links_score(soup, html_content, url_path):
    score, max_score, issues = 0, 100, []

    internal = []
    for a in soup.find_all('a', href=True):
        h = a['href']
        if h.startswith('/') or h.startswith('./') or h.startswith('../') \
           or not urlparse(h).netloc:
            internal.append({
                'href': h,
                'text': a.get_text().strip(),
                'has_title': bool(a.get('title')),
            })

    n = len(internal)
    if n >= 15:    score += 30
    elif n >= 10:  score += 20
    elif n >= 5:   score += 10; issues.append(f"Only {n} internal links")
    else:          issues.append(f"Very few internal links ({n})")

    sections = set()
    for link in internal:
        h = link['href']
        for sec in ('guides', 'reviews', 'how-to', 'destinations',
                    'editing', 'comparisons', 'city-through-the-lens'):
            if f'/{sec}/' in h:
                sections.add(sec)
    if len(sections) >= 4: score += 20
    elif len(sections) >= 2: score += 10; issues.append(f"Links to only {len(sections)} sections")
    else: issues.append("Poor internal link diversity")

    bad = {'click here', 'here', 'read more', 'more', 'link', 'this'}
    good, bad_count = 0, 0
    for link in internal:
        t = link['text'].lower()
        if t and t not in bad and len(t) > 3:
            good += 1
        elif t in bad:
            bad_count += 1
    if good > 0 and bad_count == 0:   score += 20
    elif good > bad_count:            score += 10; issues.append(f"{bad_count} poor anchor texts")
    else:                             issues.append("Many poor anchor texts")

    if soup.find(class_=re.compile('breadcrumb', re.I)):
        score += 10
    else:
        issues.append("No breadcrumbs")

    if soup.find(class_=re.compile('related', re.I)):
        score += 10
    else:
        issues.append("No related posts section")

    if soup.find('nav') or soup.find(class_=re.compile('nav', re.I)):
        score += 10
    else:
        issues.append("No navigation menu")

    return score, max_score, issues


def calculate_html_quality_score(soup, html_content, url_path):
    score, max_score, issues = 0, 100, []

    if html_content.lstrip().lower().startswith('<!doctype html>'):
        score += 10
    else:
        issues.append("Missing HTML5 doctype")

    semantic = ['article', 'section', 'nav', 'header', 'footer', 'aside', 'main']
    n_sem = sum(1 for t in semantic if soup.find(t))
    if n_sem >= 5:    score += 15
    elif n_sem >= 3:  score += 10; issues.append("Limited semantic HTML")
    else:             score += 5;  issues.append("Poor semantic HTML")

    checker = HTMLQualityChecker()
    try:
        checker.feed(html_content)
        ist = checker.inline_styles
        if ist == 0:    score += 10
        elif ist <= 5:  score += 7;  issues.append(f"{ist} inline styles")
        else:           score += 3;  issues.append(f"Too many inline styles ({ist})")
        if checker.deprecated_tags:
            score += 3; issues.append(f"Deprecated tags: {', '.join(set(checker.deprecated_tags))}")
        else:
            score += 10
    except Exception as e:
        score += 5; issues.append(f"HTML parser issue: {e}")

    # Accessibility (20)
    acc = 0
    if soup.find(class_=re.compile('skip', re.I)): acc += 5
    aria = soup.find_all(attrs={'aria-label': True})
    if len(aria) >= 3: acc += 5
    elif len(aria) >= 1: acc += 3
    imgs = soup.find_all('img')
    if imgs:
        alt_n = sum(1 for i in imgs if i.get('alt'))
        if alt_n == len(imgs): acc += 5
        elif alt_n >= len(imgs) * 0.8: acc += 3
    score += acc
    if acc < 15: issues.append("Limited accessibility features")

    if soup.find('meta', attrs={'charset': True}): score += 5
    else: issues.append("Missing meta charset")

    if soup.find('html', lang=True): score += 5
    else: issues.append("Missing lang attribute")

    if '.html' in url_path or url_path.endswith('/'):
        score += 5
    else:
        issues.append("Non-standard URL")

    if any(x in html_content for x in ['console.log', 'console.error', 'debugger']):
        issues.append("Debug code found")
    else:
        score += 10

    # Heading hierarchy (10)
    headings = []
    for i in range(1, 7):
        for h in soup.find_all(f'h{i}'):
            headings.append(i)
    if headings:
        ok = True
        prev = 0
        for lvl in headings:
            if lvl > prev + 1 and prev > 0:
                ok = False
                break
            prev = lvl
        if ok: score += 10
        else:  score += 5; issues.append("Heading hierarchy has gaps")
    else:
        issues.append("No headings")

    return min(score, max_score), max_score, issues


# =====================================================================
# Defensive wrapper + file auditor
# =====================================================================
def _safe(fn, soup, html, path):
    try:
        return fn(soup, html, path)
    except Exception as e:
        return 0, 100, [f"scorer crashed: {type(e).__name__}: {e}"]


def audit_html_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'html.parser')

        s1, m1, i1 = _safe(calculate_seo_score,            soup, html_content, file_path)
        s2, m2, i2 = _safe(calculate_eeat_score,           soup, html_content, file_path)
        s3, m3, i3 = _safe(calculate_internal_links_score, soup, html_content, file_path)
        s4, m4, i4 = _safe(calculate_html_quality_score,   soup, html_content, file_path)

        overall = (s1 + s2 + s3 + s4) / 4.0
        return {
            'file': str(file_path),
            'seo':            {'score': s1, 'max': m1, 'pct': (s1/m1)*100, 'issues': i1},
            'eeat':           {'score': s2, 'max': m2, 'pct': (s2/m2)*100, 'issues': i2},
            'internal_links': {'score': s3, 'max': m3, 'pct': (s3/m3)*100, 'issues': i3},
            'html_quality':   {'score': s4, 'max': m4, 'pct': (s4/m4)*100, 'issues': i4},
            'overall': overall,
        }
    except Exception as e:
        return {'file': str(file_path), 'error': f"{type(e).__name__}: {e}"}


# =====================================================================
# Report generator
# =====================================================================
def generate_report(results):
    out = ["# 📊 SEO & Quality Audit Report\n"]
    out.append(f"**Total files scanned:** {len(results)}\n")

    valid = [r for r in results if 'error' not in r]
    errs  = [r for r in results if 'error' in r]

    if valid:
        avg_o = sum(r['overall']               for r in valid) / len(valid)
        avg_s = sum(r['seo']['pct']            for r in valid) / len(valid)
        avg_e = sum(r['eeat']['pct']           for r in valid) / len(valid)
        avg_l = sum(r['internal_links']['pct'] for r in valid) / len(valid)
        avg_h = sum(r['html_quality']['pct']   for r in valid) / len(valid)

        out.append("## 📈 Summary\n")
        out.append(f"- **Overall Average:** {avg_o:.1f}%")
        out.append(f"- **SEO Score:** {avg_s:.1f}%")
        out.append(f"- **EEAT Score:** {avg_e:.1f}%")
        out.append(f"- **Internal Links:** {avg_l:.1f}%")
        out.append(f"- **HTML Quality:** {avg_h:.1f}%\n")

    if valid:
        out.append("## 📋 Detailed Results\n")
        for r in sorted(valid, key=lambda x: x['overall'])[:30]:
            name = r['file'].replace('\\', '/')
            out.append(f"### {name}\n")
            out.append(f"**Overall Score:** {r['overall']:.1f}%\n")
            for key, label in [('seo','SEO'), ('eeat','EEAT'),
                               ('internal_links','Internal Links'),
                               ('html_quality','HTML Quality')]:
                c = r[key]
                out.append(f"- **{label}:** {c['score']}/{c['max']} ({c['pct']:.1f}%)")
                for iss in c['issues'][:3]:
                    out.append(f"  - ⚠️ {iss}")
            out.append("")

    if errs:
        out.append(f"## ❌ Errors ({len(errs)} files)\n")
        for r in errs[:20]:
            out.append(f"- `{r['file']}`: {r['error']}")
        if len(errs) > 20:
            out.append(f"\n_…and {len(errs)-20} more._")

    return '\n'.join(out)


# =====================================================================
# File collection
# =====================================================================
def collect_html_files(root='.'):
    found = []
    for dirpath, dirs, files in os.walk(root):
        # skip unwanted directories (also nested git repos)
        dirs[:] = [d for d in dirs
                   if d not in SKIP_DIRS
                   and not os.path.exists(os.path.join(dirpath, d, '.git'))]
        for name in files:
            if not should_skip_file(name):
                found.append(os.path.join(dirpath, name))
    return sorted(found)


# =====================================================================
# Self-check: guarantees all scorers exist before any file is touched
# =====================================================================
def self_check():
    required = ['calculate_seo_score', 'calculate_eeat_score',
                'calculate_internal_links_score', 'calculate_html_quality_score']
    missing = [n for n in required if n not in globals()]
    if missing:
        sys.stderr.write(f"FATAL: missing scoring functions: {missing}\n")
        sys.exit(2)


# =====================================================================
# Main
# =====================================================================
def main():
    self_check()

    files = collect_html_files()
    print(f"Found {len(files)} HTML files to audit")

    results = []
    for f in files:
        results.append(audit_html_file(f))
        print(f"  audited: {f}")

    valid = [r for r in results if 'error' not in r]
    errs  = [r for r in results if 'error' in r]
    avg = (sum(r['overall'] for r in valid) / len(valid)) if valid else 0.0

    report = generate_report(results)
    with open('audit-report.md', 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ Audit complete: {len(valid)} scored, {len(errs)} errors, avg {avg:.1f}%")

    # ALWAYS emit outputs so workflow can never see empty / NaN
    out_path = os.environ.get('GITHUB_OUTPUT')
    if out_path:
        with open(out_path, 'a') as f:
            f.write(f"average_score={avg:.1f}\n")
            f.write(f"files_scanned={len(valid)}\n")
            f.write(f"errors={len(errs)}\n")
            f.write(f"should_alert={'true' if avg < 70 else 'false'}\n")


if __name__ == '__main__':
    main()
