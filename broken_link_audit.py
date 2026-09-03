#!/usr/bin/env python3
"""
Broken Link Audit Script for VideoCameraHoliday Repository
Scans all HTML files for broken internal and external links
"""

import os
import re
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin
from collections import defaultdict
from datetime import datetime

class LinkExtractor(HTMLParser):
    """Extract all links from HTML files"""
    
    def __init__(self, base_url=''):
        super().__init__()
        self.links = []
        self.base_url = base_url
        self.current_file = ''
        
    def handle_starttag(self, tag, attrs):
        if tag in ['a', 'link', 'script', 'img', 'source']:
            attrs_dict = dict(attrs)
            attr_name = 'href' if tag in ['a', 'link'] else 'src'
            
            if attr_name in attrs_dict:
                url = attrs_dict[attr_name]
                # Skip data URLs, javascript, mailto, tel
                if url.startswith(('data:', 'javascript:', 'mailto:', 'tel:', '#')):
                    return
                
                self.links.append({
                    'url': url,
                    'tag': tag,
                    'attr': attr_name,
                    'file': self.current_file,
                    'line': self.getpos()[0]
                })

def find_html_files(root_dir, exclude_dirs=None):
    """Find all HTML files recursively"""
    if exclude_dirs is None:
        exclude_dirs = {'assets', '_includes', '_layouts', 'node_modules', '.git', '__pycache__', 'repo_audit'}
    
    html_files = []
    for root, dirs, files in os.walk(root_dir):
        # Remove excluded directories from search
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.html'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_dir)
                html_files.append(rel_path)
    
    return sorted(html_files)

def normalize_url(url, base_repo_path=''):
    """Normalize URL to local file path"""
    # Remove query strings and fragments
    url = url.split('#')[0].split('?')[0]
    
    # Handle absolute GitHub Pages URLs
    if url.startswith('https://dawidmillenium-design.github.io/VideoCameraHoliday/'):
        url = url.replace('https://dawidmillenium-design.github.io/VideoCameraHoliday/', '')
    
    # Handle root-relative URLs
    if url.startswith('/VideoCameraHoliday/'):
        url = url.replace('/VideoCameraHoliday/', '')
    elif url.startswith('/'):
        url = url[1:]
    
    return url

def check_internal_link_exists(url, repo_root, current_file):
    """Check if internal link exists"""
    # Normalize URL
    url = normalize_url(url)
    
    # Skip external URLs
    if url.startswith(('http://', 'https://', '//')):
        return True, 'external'
    
    # Build full path
    if url == '':
        url = 'index.html'
    
    # Try direct path
    full_path = os.path.join(repo_root, url)
    if os.path.exists(full_path):
        return True, 'exists'
    
    # Try with .html extension
    if not url.endswith('.html'):
        full_path_html = full_path + '.html'
        if os.path.exists(full_path_html):
            return True, 'exists'
    
    # Try index.html in directory
    full_path_index = os.path.join(full_path, 'index.html')
    if os.path.exists(full_path_index):
        return True, 'exists'
    
    return False, 'missing'

def extract_external_urls(links):
    """Extract unique external URLs"""
    external_urls = set()
    for link in links:
        url = link['url']
        if url.startswith(('http://', 'https://')):
            external_urls.add(url)
    return sorted(external_urls)

def scan_file_for_links(file_path, repo_root):
    """Scan a single HTML file for links"""
    full_path = os.path.join(repo_root, file_path)
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return [], f"Error reading file: {e}"
    
    parser = LinkExtractor()
    parser.current_file = file_path
    
    try:
        parser.feed(content)
    except Exception as e:
        return [], f"Error parsing HTML: {e}"
    
    return parser.links, None

def generate_report(broken_links, missing_files, external_urls, output_file='broken_links_audit.md'):
    """Generate markdown report"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report = []
    report.append("# 🔗 Broken Link Audit Report")
    report.append(f"\n**Generated:** {timestamp}")
    report.append(f"\n**Repository:** VideoCameraHoliday")
    report.append("\n---\n")
    
    # Summary
    report.append("## 📊 Summary")
    report.append(f"\n- **Total Internal Broken Links:** {len(broken_links)}")
    report.append(f"- **Missing Files Referenced:** {len(missing_files)}")
    report.append(f"- **External URLs Found:** {len(external_urls)}")
    report.append(f"- **Status:** {'❌ Issues Found' if broken_links else '✅ All Internal Links Valid'}")
    report.append("\n---\n")
    
    # Broken Internal Links
    if broken_links:
        report.append("## 🚨 Broken Internal Links\n")
        report.append("| Source File | Line | Broken Link | Type |")
        report.append("|-------------|------|-------------|------|")
        
        # Group by source file
        by_file = defaultdict(list)
        for link in broken_links:
            by_file[link['file']].append(link)
        
        for file_path, links in sorted(by_file.items()):
            for link in links:
                report.append(f"| `{link['file']}` | {link['line']} | `{link['url']}` | {link['tag']} |")
        
        report.append("\n---\n")
    
    # Missing Files
    if missing_files:
        report.append("## 📁 Missing Files Referenced\n")
        report.append("These files are linked but don't exist in the repository:\n")
        
        for file_path, references in sorted(missing_files.items()):
            report.append(f"### `{file_path}`")
            report.append(f"**Referenced in {len(references)} file(s):**\n")
            for ref in references[:10]:  # Show first 10 references
                report.append(f"- `{ref['file']}` (line {ref['line']})")
            if len(references) > 10:
                report.append(f"- ... and {len(references) - 10} more")
            report.append("")
        
        report.append("\n---\n")
    
    # External URLs (for manual verification)
    if external_urls:
        report.append("## 🌐 External URLs (Manual Verification Required)\n")
        report.append("These external URLs should be manually checked for validity:\n")
        
        # Group by domain
        by_domain = defaultdict(list)
        for url in external_urls:
            domain = urlparse(url).netloc
            by_domain[domain].append(url)
        
        for domain, urls in sorted(by_domain.items(), key=lambda x: len(x[1]), reverse=True):
            report.append(f"\n### {domain} ({len(urls)} links)")
            for url in urls[:20]:  # Show first 20 per domain
                report.append(f"- `{url}`")
            if len(urls) > 20:
                report.append(f"- ... and {len(urls) - 20} more")
        
        report.append("\n\n> 💡 **Tip:** Use tools like [W3C Link Checker](https://validator.w3.org/checklink) or [Screaming Frog](https://www.screamingfrog.co.uk/seo-spider/) to verify external links.\n")
    
    # Recommendations
    report.append("\n---\n")
    report.append("## 💡 Recommendations\n")
    
    if broken_links:
        report.append("1. **Fix Broken Internal Links:** Update or remove links pointing to missing files")
        report.append("2. **Create Missing Files:** If files should exist, create them with proper content")
        report.append("3. **Update Navigation:** Check mega menus and breadcrumbs for outdated links")
    
    if external_urls:
        report.append("4. **Verify External Links:** Manually check external URLs or use automated tools")
        report.append("5. **Consider Link Monitoring:** Set up regular checks for external link health")
    
    if not broken_links:
        report.append("✅ **Great job!** All internal links are valid. Consider setting up regular audits to maintain link health.")
    
    report.append("\n---\n")
    report.append("*Report generated by Broken Link Audit Script*")
    
    # Write report
    report_text = '\n'.join(report)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    return report_text

def main():
    """Main audit function"""
    print("🔍 Starting Broken Link Audit...")
    print("=" * 60)
    
    repo_root = '/workspace'
    
    # Find all HTML files
    print("\n📂 Scanning for HTML files...")
    html_files = find_html_files(repo_root)
    print(f"   Found {len(html_files)} HTML files")
    
    # Extract all links
    print("\n🔗 Extracting links from all files...")
    all_links = []
    errors = []
    
    for file_path in html_files:
        links, error = scan_file_for_links(file_path, repo_root)
        if error:
            errors.append({'file': file_path, 'error': error})
        else:
            all_links.extend(links)
    
    print(f"   Extracted {len(all_links)} links")
    if errors:
        print(f"   ⚠️  {len(errors)} files had parsing errors")
    
    # Separate internal and external links
    internal_links = [l for l in all_links if not l['url'].startswith(('http://', 'https://'))]
    external_links = [l for l in all_links if l['url'].startswith(('http://', 'https://'))]
    
    print(f"   - Internal links: {len(internal_links)}")
    print(f"   - External links: {len(external_links)}")
    
    # Check internal links
    print("\n✅ Checking internal link validity...")
    broken_links = []
    missing_files = defaultdict(list)
    
    for i, link in enumerate(internal_links):
        if i % 1000 == 0:
            print(f"   Progress: {i}/{len(internal_links)} links checked")
        
        exists, status = check_internal_link_exists(link['url'], repo_root, link['file'])
        
        if not exists:
            broken_links.append(link)
            # Normalize the missing file path
            missing_file = normalize_url(link['url'])
            if missing_file and not missing_file.startswith(('http', 'data', 'javascript')):
                missing_files[missing_file].append(link)
    
    print(f"   Found {len(broken_links)} broken internal links")
    print(f"   Referencing {len(missing_files)} missing files")
    
    # Extract unique external URLs
    external_urls = extract_external_urls(external_links)
    print(f"\n🌐 Found {len(external_urls)} unique external URLs")
    
    # Generate report
    print("\n📝 Generating audit report...")
    report = generate_report(broken_links, missing_files, external_urls)
    
    print("\n" + "=" * 60)
    print("✅ Audit Complete!")
    print(f"\n📄 Report saved to: /workspace/broken_links_audit.md")
    print(f"\n📊 Quick Summary:")
    print(f"   - Broken Internal Links: {len(broken_links)}")
    print(f"   - Missing Files: {len(missing_files)}")
    print(f"   - External URLs: {len(external_urls)}")
    
    if broken_links:
        print(f"\n🚨 Action Required: Fix {len(broken_links)} broken links")
    else:
        print(f"\n✅ All internal links are valid!")
    
    return {
        'broken_links': broken_links,
        'missing_files': dict(missing_files),
        'external_urls': external_urls,
        'total_files_scanned': len(html_files),
        'total_links_found': len(all_links)
    }

if __name__ == '__main__':
    results = main()
