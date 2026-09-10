#!/usr/bin/env python3
"""
SEO & Quality Audit Script for VideoCameraHoliday
Scans all HTML files and provides scores for:
- On-page SEO
- EEAT (Experience, Expertise, Authoritativeness, Trustworthiness)
- Internal Links
- HTML Clean Code
"""

import os
import re
import json
import sys
from pathlib import Path
from urllib.parse import urlparse
from html.parser import HTMLParser
from collections import defaultdict

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing beautifulsoup4...")
    os.system(f"{sys.executable} -m pip install beautifulsoup4")
    from bs4 import BeautifulSoup


class HTMLQualityChecker(HTMLParser):
    """Check HTML quality issues"""
    def __init__(self):
        super().__init__()
        self.issues = []
        self.inline_styles = 0
        self.deprecated_tags = []
        self.semantic_tags = []
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # Check for inline styles
        if 'style' in attrs_dict:
            self.inline_styles += 1
            
        # Check for deprecated tags
        deprecated = ['font', 'center', 'big', 'strike', 'tt', 'frame', 'frameset']
        if tag in deprecated:
            self.deprecated_tags.append(tag)
            
        # Track semantic tags
        semantic = ['article', 'section', 'nav', 'header', 'footer', 'aside', 'main']
        if tag in semantic:
            self.semantic_tags.append(tag)


def calculate_seo_score(soup, html_content, url_path):
    """Calculate On-page SEO score (0-100)"""
    score = 0
    max_score = 100
    issues = []
    
    # Title tag (15 points)
    title = soup.find('title')
    if title and title.get_text().strip():
        title_text = title.get_text().strip()
        title_len = len(title_text)
        if 50 <= title_len <= 60:
            score += 15
        elif 30 <= title_len <= 70:
            score += 10
            issues.append(f"Title length ({title_len} chars) outside optimal range (50-60)")
        else:
            score += 5
            issues.append(f"Title length ({title_len} chars) too short or too long")
    else:
        issues.append("Missing title tag")
    
    # Meta description (15 points)
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        desc_text = meta_desc.get('content').strip()
        desc_len = len(desc_text)
        if 150 <= desc_len <= 160:
            score += 15
        elif 120 <= desc_len <= 180:
            score += 10
            issues.append(f"Meta description length ({desc_len} chars) outside optimal range")
        else:
            score += 5
            issues.append(f"Meta description length ({desc_len} chars) not optimal")
    else:
        issues.append("Missing meta description")
    
    # H1 tag (10 points)
    h1_tags = soup.find_all('h1')
    if len(h1_tags) == 1:
        score += 10
    elif len(h1_tags) == 0:
        issues.append("Missing H1 tag")
    else:
        score += 5
        issues.append(f"Multiple H1 tags found ({len(h1_tags)})")
    
    # Canonical URL (10 points)
    canonical = soup.find('link', rel='canonical')
    if canonical and canonical.get('href'):
        score += 10
    else:
        issues.append("Missing canonical URL")
    
    # Alt attributes on images (10 points)
    images = soup.find_all('img')
    if images:
        images_with_alt = [img for img in images if img.get('alt')]
        alt_percentage = (len(images_with_alt) / len(images)) * 100
        if alt_percentage == 100:
            score += 10
        elif alt_percentage >= 80:
            score += 7
            issues.append(f"{len(images) - len(images_with_alt)} images missing alt text")
        else:
            score += 3
            issues.append(f"Only {alt_percentage:.0f}% of images have alt text")
    else:
        score += 10  # No images is acceptable
    
    # Open Graph tags (10 points)
    og_tags = soup.find_all('meta', property=re.compile('^og:'))
    if len(og_tags) >= 4:  # og:title, og:description, og:image, og:url
        score += 10
    elif len(og_tags) >= 2:
        score += 5
        issues.append("Incomplete Open Graph tags")
    else:
        issues.append("Missing Open Graph tags")
    
    # Twitter cards (5 points)
    twitter_card = soup.find('meta', attrs={'name': 'twitter:card'})
    if twitter_card:
        score += 5
    else:
        issues.append("Missing Twitter card meta tag")
    
    # Schema.org/JSON-LD (10 points)
    json_ld = soup.find_all('script', type='application/ld+json')
    if json_ld:
        score += 10
    else:
        issues.append("Missing structured data (JSON-LD)")
    
    # Robots meta tag (5 points)
    robots = soup.find('meta', attrs={'name': 'robots'})
    if robots:
        score += 5
    else:
        issues.append("Missing robots meta tag")
    
    # Viewport meta tag (5 points)
    viewport = soup.find('meta', attrs={'name': 'viewport'})
    if viewport and viewport.get('content'):
        score += 5
    else:
        issues.append("Missing viewport meta tag")
    
    # Language attribute (5 points)
    html_tag = soup.find('html')
    if html_tag and html_tag.get('lang'):
        score += 5
    else:
        issues.append("Missing lang attribute on HTML tag")
    
    return score, max_score, issues


def calculate_eaat_score(soup, html_content, url_path):
    """Calculate EEAT score (0-100)"""
    score = 0
    max_score = 100
    issues = []
    
    # Author name present (15 points)
    author_meta = soup.find('meta', attrs={'name': 'author'})
    author_box = soup.find(class_=re.compile('author', re.I))
    if author_meta or author_box:
        score += 15
    else:
        issues.append("No author information found")
    
    # Author bio/description (15 points)
    if author_box and len(author_box.get_text()) > 50:
        score += 15
    elif author_box:
        score += 8
        issues.append("Author bio too short")
    else:
        issues.append("Missing author bio")
    
    # Publication date (10 points)
    date_meta = soup.find('meta', attrs={'property': 'article:published_time'})
    date_in_json = False
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            if 'datePublished' in str(data):
                date_in_json = True
                break
        except:
            pass
    
    if date_meta or date_in_json:
        score += 10
    else:
        issues.append("Missing publication date")
    
    # Last modified date (10 points)
    modified_meta = soup.find('meta', attrs={'property': 'article:modified_time'})
    modified_in_json = False
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            if 'dateModified' in str(data):
                modified_in_json = True
                break
        except:
            pass
    
    if modified_meta or modified_in_json:
        score += 10
    else:
        issues.append("Missing last modified date")
    
    # About page link (10 points)
    about_links = soup.find_all('a', href=re.compile('/about', re.I))
    if about_links:
        score += 10
    else:
        issues.append("No link to About page")
    
    # Contact info (10 points)
    contact_indicators = ['contact', 'email', 'mailto:', '@']
    has_contact = any(indicator in html_content.lower() for indicator in contact_indicators)
    if has_contact:
        score += 10
    else:
        issues.append("No contact information found")
    
    # Author credentials/expertise (10 points)
    expertise_keywords = ['expert', 'professional', 'experience', 'years', 'photographer', 'videographer', 'reviewed', 'tested']
    has_expertise = any(keyword in html_content.lower() for keyword in expertise_keywords)
    if has_expertise:
        score += 10
    else:
        issues.append("No expertise indicators found")
    
    # Trust signals (10 points)
    trust_signals = ['affiliate', 'disclosure', 'privacy', 'terms', 'cookie']
    trust_count = sum(1 for signal in trust_signals if signal in html_content.lower())
    if trust_count >= 2:
        score += 10
    elif trust_count == 1:
        score += 5
        issues.append("Limited trust signals (affiliate disclosure, privacy policy)")
    else:
        issues.append("Missing trust signals (affiliate disclosure, privacy policy)")
    
    # External authoritative links (10 points)
    external_links = [a for a in soup.find_all('a', href=True) 
                     if urlparse(a['href']).netloc and 'github.io' not in a['href']]
    if len(external_links) >= 3:
        score += 10
    elif len(external_links) >= 1:
        score += 5
        issues.append("Few external authoritative links")
    else:
        issues.append("No external authoritative links")
    
    return score, max_score, issues


def calculate_internal_links_score(soup, html_content, url_path):
    """Calculate Internal Links score (0-100)"""
    score = 0
    max_score = 100
    issues = []
    
    # Find all internal links
    all_links = soup.find_all('a', href=True)
    internal_links = []
    
    for link in all_links:
        href = link['href']
        # Check if it's an internal link
        if href.startswith('/') or href.startswith('./') or href.startswith('../'):
            internal_links.append({
                'href': href,
                'text': link.get_text().strip(),
                'has_title': bool(link.get('title'))
            })
        elif not urlparse(href).netloc:  # Relative link without protocol
            internal_links.append({
                'href': href,
                'text': link.get_text().strip(),
                'has_title': bool(link.get('title'))
            })
    
    # Number of internal links (30 points)
    num_links = len(internal_links)
    if num_links >= 15:
        score += 30
    elif num_links >= 10:
        score += 20
    elif num_links >= 5:
        score += 10
        issues.append(f"Only {num_links} internal links (aim for 10+)")
    else:
        issues.append(f"Very few internal links ({num_links})")
    
    # Diversity of internal links (20 points)
    unique_sections = set()
    for link in internal_links:
        href = link['href']
        if '/guides/' in href:
            unique_sections.add('guides')
        elif '/reviews/' in href:
            unique_sections.add('reviews')
        elif '/how-to/' in href:
            unique_sections.add('how-to')
        elif '/destinations/' in href:
            unique_sections.add('destinations')
        elif '/editing/' in href:
            unique_sections.add('editing')
        elif '/comparisons/' in href:
            unique_sections.add('comparisons')
    
    section_diversity = len(unique_sections)
    if section_diversity >= 4:
        score += 20
    elif section_diversity >= 2:
        score += 10
        issues.append(f"Links to only {section_diversity} sections")
    else:
        issues.append("Poor internal link diversity")
    
    # Anchor text quality (20 points)
    bad_anchor_texts = ['click here', 'here', 'read more', 'more', 'link', 'this']
    good_anchors = 0
    bad_anchors = 0
    
    for link in internal_links:
        text = link['text'].lower()
        if text and text not in bad_anchor_texts and len(text) > 3:
            good_anchors += 1
        elif text in bad_anchor_texts:
            bad_anchors += 1
    
    if good_anchors > 0 and bad_anchors == 0:
        score += 20
    elif good_anchors > bad_anchors:
        score += 10
        issues.append(f"{bad_anchors} links with poor anchor text")
    else:
        issues.append("Many links with poor anchor text (click here, read more)")
    
    # Breadcrumbs present (10 points)
    breadcrumbs = soup.find(class_=re.compile('breadcrumb', re.I))
    if breadcrumbs:
        score += 10
    else:
        issues.append("No breadcrumbs navigation")
    
    # Related posts/links section (10 points)
    related_section = soup.find(class_=re.compile('related', re.I))
    if related_section:
        score += 10
    else:
        issues.append("No related posts section")
    
    # Navigation menu present (10 points)
    nav_menu = soup.find('nav') or soup.find(class_=re.compile('nav', re.I))
    if nav_menu:
        score += 10
    else:
        issues.append("No navigation menu")
    
    return score, max_score, issues


def calculate_html_quality_score(soup, html_content, url_path):
    """Calculate HTML Clean Code score (0-100)"""
    score = 0
    max_score = 100
    issues = []
    
    # Check for HTML5 doctype (10 points)
    if html_content.strip().lower().startswith('<!doctype html>'):
        score += 10
    else:
        issues.append("Missing or invalid HTML5 doctype")
    
    # Semantic HTML elements (15 points)
    semantic_tags = ['article', 'section', 'nav', 'header', 'footer', 'aside', 'main']
    semantic_count = sum(1 for tag in semantic_tags if soup.find(tag))
    
    if semantic_count >= 5:
        score += 15
    elif semantic_count >= 3:
        score += 10
        issues.append("Limited use of semantic HTML elements")
    else:
        score += 5
        issues.append("Poor semantic HTML structure")
    
    # Inline styles (10 points - less is better)
    checker = HTMLQualityChecker()
    try:
        checker.feed(html_content)
        inline_styles = checker.inline_styles
        
        if inline_styles == 0:
            score += 10
        elif inline_styles <= 5:
            score += 7
            issues.append(f"{inline_styles} inline styles found")
        else:
            score += 3
            issues.append(f"Too many inline styles ({inline_styles})")
    except:
        score += 5
        issues.append("Could not parse HTML for inline styles")
    
    # Deprecated tags (10 points)
    try:
        deprecated = checker.deprecated_tags
        if not deprecated:
            score += 10
        else:
            score += 3
            issues.append(f"Deprecated tags found: {', '.join(set(deprecated))}")
    except:
        score += 5
    
    # Accessibility features (20 points)
    accessibility_score = 0
    
    # Skip links
    if soup.find(class_=re.compile('skip', re.I)):
        accessibility_score += 5
    
    # ARIA labels
    aria_elements = soup.find_all(attrs={'aria-label': True})
    if len(aria_elements) >= 3:
        accessibility_score += 5
    elif len(aria_elements) >= 1:
        accessibility_score += 3
    
    # Alt text on images (already checked in SEO, but count again)
    images = soup.find_all('img')
    if images:
        alt_count = sum(1 for img in images if img.get('alt'))
        if alt_count == len(images):
            accessibility_score += 5
        elif alt_count >= len(images) * 0.8:
            accessibility_score += 3
    
    # Form labels
    forms = soup.find_all('form')
    if forms:
        inputs = soup.find_all('input')
        labeled_inputs = sum(1 for inp in inputs if inp.get('aria-label') or inp.get('id'))
        if labeled_inputs >= len(inputs) * 0.8:
            accessibility_score += 5
    
    score += accessibility_score
    if accessibility_score < 15:
        issues.append("Limited accessibility features")
    
    # Meta charset (5 points)
    charset = soup.find('meta', attrs={'charset': True})
    if charset:
        score += 5
    else:
        issues.append("Missing meta charset")
    
    # Language attribute (5 points)
    html_tag = soup.find('html')
    if html_tag and html_tag.get('lang'):
        score += 5
    else:
        issues.append("Missing lang attribute")
    
    # Clean URL structure (5 points)
    if '.html' in url_path or url_path.endswith('/'):
        score += 5
    else:
        issues.append("URL structure could be cleaner")
    
    # No console errors indicators (10 points)
    # Check for common issues
    error_indicators = ['console.log', 'console.error', 'debugger']
    has_debug = any(indicator in html_content for indicator in error_indicators)
    if not has_debug:
        score += 10
    else:
        issues.append("Debug code found in HTML")
    
    # Proper heading hierarchy (10 points)
    headings = []
    for i in range(1, 7):
        h_tags = soup.find_all(f'h{i}')
        if h_tags:
            headings.extend([(i, h.get_text().strip()) for h in h_tags])
    
    if headings:
        # Check if headings follow proper hierarchy
        prev_level = 0
        proper_hierarchy = True
        for level, text in headings:
            if level > prev_level + 1 and prev_level > 0:
                proper_hierarchy = False
                break
            prev_level = level
        
        if proper_hierarchy:
            score += 10
        else:
            score += 5
            issues.append("Heading hierarchy has gaps")
    else:
        issues.append("No headings found")
    
    return min(score, max_score), max_score, issues


def audit_html_file(file_path):
    """Audit a single HTML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Calculate all scores
        seo_score, seo_max, seo_issues = calculate_seo_score(soup, html_content, file_path)
        eeat_score, eeat_max, eeat_issues = calculate_eeat_score(soup, html_content, file_path)
        links_score, links_max, links_issues = calculate_internal_links_score(soup, html_content, file_path)
        html_score, html_max, html_issues = calculate_html_quality_score(soup, html_content, file_path)
        
        # Calculate overall score
        overall_score = (seo_score + eeat_score + links_score + html_score) / 4
        
        return {
            'file': str(file_path),
            'seo': {
                'score': seo_score,
                'max': seo_max,
                'percentage': (seo_score / seo_max) * 100,
                'issues': seo_issues
            },
            'eeat': {
                'score': eeat_score,
                'max': eeat_max,
                'percentage': (eeat_score / eeat_max) * 100,
                'issues': eeat_issues
            },
            'internal_links': {
                'score': links_score,
                'max': links_max,
                'percentage': (links_score / links_max) * 100,
                'issues': links_issues
            },
            'html_quality': {
                'score': html_score,
                'max': html_max,
                'percentage': (html_score / html_max) * 100,
                'issues': html_issues
            },
            'overall': overall_score
        }
    except Exception as e:
        return {
            'file': str(file_path),
            'error': str(e)
        }


def generate_report(results, output_format='markdown'):
    """Generate audit report"""
    if output_format == 'json':
        return json.dumps(results, indent=2)
    
    # Markdown report
    report = ["# 📊 SEO & Quality Audit Report\n"]
    report.append(f"**Total files scanned:** {len(results)}\n")
    
    # Summary statistics
    valid_results = [r for r in results if 'error' not in r]
    if valid_results:
        avg_overall = sum(r['overall'] for r in valid_results) / len(valid_results)
        avg_seo = sum(r['seo']['percentage'] for r in valid_results) / len(valid_results)
        avg_eeat = sum(r['eeat']['percentage'] for r in valid_results) / len(valid_results)
        avg_links = sum(r['internal_links']['percentage'] for r in valid_results) / len(valid_results)
        avg_html = sum(r['html_quality']['percentage'] for r in valid_results) / len(valid_results)
        
        report.append("## 📈 Summary\n")
        report.append(f"- **Overall Average:** {avg_overall:.1f}%")
        report.append(f"- **SEO Score:** {avg_seo:.1f}%")
        report.append(f"- **EEAT Score:** {avg_eeat:.1f}%")
        report.append(f"- **Internal Links:** {avg_links:.1f}%")
        report.append(f"- **HTML Quality:** {avg_html:.1f}%\n")
    
    # Sort by overall score (worst first)
    valid_results.sort(key=lambda x: x['overall'])
    
    # Detailed results
    report.append("## 📋 Detailed Results\n")
    
    for result in valid_results[:20]:  # Show top 20 worst
        file_name = result['file'].replace('\\', '/').split('/')[-1]
        report.append(f"### {file_name}\n")
        report.append(f"**Overall Score:** {result['overall']:.1f}%\n")
        
        report.append(f"- SEO: {result['seo']['score']}/{result['seo']['max']} ({result['seo']['percentage']:.1f}%)")
        if result['seo']['issues']:
            for issue in result['seo']['issues'][:3]:
                report.append(f"  - ⚠️ {issue}")
        
        report.append(f"- EEAT: {result['eeat']['score']}/{result['eeat']['max']} ({result['eeat']['percentage']:.1f}%)")
        if result['eeat']['issues']:
            for issue in result['eeat']['issues'][:3]:
                report.append(f"  - ⚠️ {issue}")
        
        report.append(f"- Internal Links: {result['internal_links']['score']}/{result['internal_links']['max']} ({result['internal_links']['percentage']:.1f}%)")
        if result['internal_links']['issues']:
            for issue in result['internal_links']['issues'][:3]:
                report.append(f"  - ⚠️ {issue}")
        
        report.append(f"- HTML Quality: {result['html_quality']['score']}/{result['html_quality']['max']} ({result['html_quality']['percentage']:.1f}%)")
        if result['html_quality']['issues']:
            for issue in result['html_quality']['issues'][:3]:
                report.append(f"  - ⚠️ {issue}")
        
        report.append("")
    
    # Errors
    error_results = [r for r in results if 'error' in r]
    if error_results:
        report.append("## ❌ Errors\n")
        for result in error_results:
            report.append(f"- **{result['file']}**: {result['error']}")
    
    return '\n'.join(report)


def main():
    """Main function"""
    # Find all HTML files
    html_files = []
    for root, dirs, files in os.walk('.'):
        # Skip .git and node_modules directories
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '.github']]
        
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
    
    print(f"Found {len(html_files)} HTML files to audit\n")
    
    # Audit all files
    results = []
    for file_path in html_files:
        print(f"Auditing: {file_path}")
        result = audit_html_file(file_path)
        results.append(result)
    
    # Generate report
    output_format = os.environ.get('OUTPUT_FORMAT', 'markdown')
    report = generate_report(results, output_format)
    
    # Save report
    report_file = 'audit-report.md' if output_format == 'markdown' else 'audit-report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Audit complete! Report saved to {report_file}")
    
    # Output for GitHub Actions
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            valid_results = [r for r in results if 'error' not in r]
            if valid_results:
                avg_overall = sum(r['overall'] for r in valid_results) / len(valid_results)
                f.write(f"average_score={avg_overall:.1f}\n")
                f.write(f"files_scanned={len(valid_results)}\n")
                f.write(f"errors={len([r for r in results if 'error' in r])}\n")


if __name__ == '__main__':
    main()
