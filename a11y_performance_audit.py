#!/usr/bin/env python3
"""
Comprehensive Web Accessibility (a11y) and Front-End Performance Audit Script

This script scans a static HTML repository and generates a detailed audit report covering:
1. CSS Architecture & Dead Code Audit
2. WCAG Color Contrast Audit

Author: AI Assistant
Requirements: beautifulsoup4 (pip install beautifulsoup4)
"""

import os
import re
import json
from collections import defaultdict
from bs4 import BeautifulSoup
from pathlib import Path


# =============================================================================
# WCAG Contrast Calculation (implemented without external library)
# =============================================================================

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def rgb_to_hex(r, g, b):
    """Convert RGB to hex color."""
    return '#{:02x}{:02x}{:02x}'.format(int(r), int(g), int(b))


def parse_color(color_str):
    """Parse color string (hex, rgb, rgba, named colors) to RGB tuple."""
    if not color_str:
        return None
    
    color_str = color_str.strip().lower()
    
    # Named colors (common ones)
    named_colors = {
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'red': (255, 0, 0),
        'green': (0, 128, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
        'cyan': (0, 255, 255),
        'magenta': (255, 0, 255),
        'gray': (128, 128, 128),
        'grey': (128, 128, 128),
        'silver': (192, 192, 192),
        'navy': (0, 0, 128),
        'olive': (128, 128, 0),
        'teal': (0, 128, 128),
        'aqua': (0, 255, 255),
        'fuchsia': (255, 0, 255),
        'lime': (0, 255, 0),
        'maroon': (128, 0, 0),
        'purple': (128, 0, 128),
        'orange': (255, 165, 0),
        'pink': (255, 192, 203),
        'brown': (165, 42, 42),
        'coral': (255, 127, 80),
        'crimson': (220, 20, 60),
        'darkblue': (0, 0, 139),
        'darkgreen': (0, 100, 0),
        'darkred': (139, 0, 0),
        'gold': (255, 215, 0),
        'indigo': (75, 0, 130),
        'ivory': (255, 255, 240),
        'khaki': (240, 230, 140),
        'lavender': (230, 230, 250),
        'lightblue': (173, 216, 230),
        'lightgray': (211, 211, 211),
        'lightgrey': (211, 211, 211),
        'lightgreen': (144, 238, 144),
        'lightyellow': (255, 255, 224),
        'tan': (210, 180, 140),
        'thistle': (216, 191, 216),
        'tomato': (255, 99, 71),
        'turquoise': (64, 224, 208),
        'violet': (238, 130, 238),
        'wheat': (245, 222, 179),
        'transparent': None,
    }
    
    if color_str in named_colors:
        return named_colors[color_str]
    
    # Hex color
    if color_str.startswith('#'):
        return hex_to_rgb(color_str)
    
    # RGB/RGBA
    rgb_match = re.match(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*[\d.]+)?\s*\)', color_str)
    if rgb_match:
        r, g, b = map(int, rgb_match.groups())
        return (r, g, b)
    
    return None


def get_luminance(rgb):
    """Calculate relative luminance according to WCAG 2.1."""
    if not rgb:
        return None
    
    def adjust(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    
    r, g, b = rgb
    return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)


def calculate_contrast_ratio(color1_rgb, color2_rgb):
    """Calculate WCAG contrast ratio between two colors."""
    lum1 = get_luminance(color1_rgb)
    lum2 = get_luminance(color2_rgb)
    
    if lum1 is None or lum2 is None:
        return None
    
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    
    return (lighter + 0.05) / (darker + 0.05)


def check_wcag_aa(contrast_ratio, is_large_text=False):
    """Check if contrast ratio meets WCAG AA standards."""
    if is_large_text:
        return contrast_ratio >= 3.0
    else:
        return contrast_ratio >= 4.5


# =============================================================================
# CSS Parsing and Analysis
# =============================================================================

def parse_css_rules(css_content):
    """Parse CSS content and extract rules with selectors and properties."""
    rules = []
    
    # Remove comments
    css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
    
    # Match CSS rules: selector { properties }
    rule_pattern = re.compile(r'([^{}]+)\{([^{}]*)\}', re.MULTILINE)
    
    for match in rule_pattern.finditer(css_content):
        selector = match.group(1).strip()
        properties_str = match.group(2).strip()
        
        # Parse properties
        properties = {}
        for prop_match in re.finditer(r'([\w-]+)\s*:\s*([^;]+);?', properties_str):
            prop_name = prop_match.group(1).strip().lower()
            prop_value = prop_match.group(2).strip()
            properties[prop_name] = prop_value
        
        # Handle media queries
        if '@media' in selector:
            # For simplicity, we'll treat media query rules separately
            inner_rules = parse_css_rules(match.group(2))
            for inner_rule in inner_rules:
                inner_rule['media'] = selector
                rules.append(inner_rule)
        else:
            rules.append({
                'selector': selector,
                'properties': properties,
                'media': None
            })
    
    return rules


def extract_classes_from_selectors(selectors):
    """Extract class names from CSS selectors."""
    classes = set()
    class_pattern = re.compile(r'\.([a-zA-Z_][a-zA-Z0-9_-]*)')
    
    for selector in selectors:
        matches = class_pattern.findall(selector)
        classes.update(matches)
    
    return classes


def extract_html_classes(html_content):
    """Extract all class names used in HTML content."""
    classes = set()
    class_pattern = re.compile(r'class\s*=\s*["\']([^"\']+)["\']')
    
    for match in class_pattern.finditer(html_content):
        class_list = match.group(1).split()
        classes.update(class_list)
    
    return classes


def find_conflicting_rules(rules_by_file, target_selector='.mega-menu'):
    """Find conflicting CSS rules for a specific selector across files."""
    conflicts = []
    
    # Group rules by selector
    selector_props = defaultdict(lambda: defaultdict(dict))
    
    for filepath, rules in rules_by_file.items():
        for rule in rules:
            if rule['selector'] == target_selector:
                for prop, value in rule['properties'].items():
                    if prop in ['background', 'background-color', 'grid-template-columns', 
                                'display', 'position', 'padding', 'border']:
                        key = (prop, value)
                        existing = selector_props[target_selector][prop]
                        
                        if existing and filepath not in existing.get('files', []):
                            # Conflict detected
                            conflicts.append({
                                'property': prop,
                                'file1': list(existing.get('files', []))[0] if existing.get('files') else 'unknown',
                                'value1': existing.get('value'),
                                'file2': filepath,
                                'value2': value,
                                'selector': target_selector
                            })
                        
                        if 'files' not in existing:
                            existing['files'] = set()
                            existing['value'] = value
                        existing['files'].add(filepath)
    
    return conflicts


# =============================================================================
# File Scanning
# =============================================================================

def scan_repository(repo_path):
    """Scan repository for HTML and CSS files."""
    html_files = []
    css_files = []
    
    for root, dirs, files in os.walk(repo_path):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv']]
        
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith('.html'):
                html_files.append(filepath)
            elif file.endswith('.css'):
                css_files.append(filepath)
    
    return html_files, css_files


def read_file_content(filepath):
    """Read file content with error handling."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}")
        return ""


def extract_inline_styles(html_content):
    """Extract inline <style> tags from HTML content."""
    styles = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for style_tag in soup.find_all('style'):
        if style_tag.string:
            styles.append(style_tag.string)
    
    return styles


# =============================================================================
# Main Audit Functions
# =============================================================================

def run_css_architecture_audit(repo_path, html_files, css_files):
    """Run CSS Architecture & Dead Code Audit."""
    print("\n" + "="*80)
    print("CSS ARCHITECTURE & DEAD CODE AUDIT")
    print("="*80)
    
    results = {
        'css_files_analyzed': [],
        'total_rules': 0,
        'duplicate_selectors': [],
        'conflicting_rules': [],
        'unused_classes': [],
        'all_defined_classes': set(),
        'all_used_classes': set()
    }
    
    # Parse all CSS files
    css_rules_by_file = {}
    all_defined_classes = set()
    
    print(f"\nAnalyzing {len(css_files)} CSS files...")
    
    for css_file in css_files:
        content = read_file_content(css_file)
        if not content:
            continue
        
        rel_path = os.path.relpath(css_file, repo_path)
        results['css_files_analyzed'].append(rel_path)
        
        rules = parse_css_rules(content)
        css_rules_by_file[rel_path] = rules
        results['total_rules'] += len(rules)
        
        # Extract defined classes
        selectors = [rule['selector'] for rule in rules]
        defined_classes = extract_classes_from_selectors(selectors)
        all_defined_classes.update(defined_classes)
        
        print(f"  ✓ {rel_path}: {len(rules)} rules, {len(defined_classes)} classes")
    
    results['all_defined_classes'] = all_defined_classes
    
    # Check for conflicts between site-shell.css and mega-menu.css
    print("\nChecking for conflicting rules between site-shell.css and mega-menu.css...")
    
    shell_rules = []
    mega_rules = []
    
    for filepath, rules in css_rules_by_file.items():
        if 'site-shell.css' in filepath:
            shell_rules.extend(rules)
        elif 'mega-menu.css' in filepath:
            mega_rules.extend(rules)
    
    # Find conflicts for .mega-menu selector
    target_selector = '.mega-menu'
    shell_mega_props = {}
    mega_menu_props = {}
    
    for rule in shell_rules:
        if rule['selector'] == target_selector:
            shell_mega_props.update(rule['properties'])
    
    for rule in mega_rules:
        if rule['selector'] == target_selector:
            mega_menu_props.update(rule['properties'])
    
    conflicts_found = []
    for prop in set(shell_mega_props.keys()) & set(mega_menu_props.keys()):
        if shell_mega_props[prop] != mega_menu_props[prop]:
            conflicts_found.append({
                'selector': target_selector,
                'property': prop,
                'site_shell_value': shell_mega_props[prop],
                'mega_menu_value': mega_menu_props[prop]
            })
            results['conflicting_rules'].append({
                'selector': target_selector,
                'property': prop,
                'site_shell_value': shell_mega_props[prop],
                'mega_menu_value': mega_menu_props[prop]
            })
    
    if conflicts_found:
        print(f"  ⚠ Found {len(conflicts_found)} conflicting property(ies) for {target_selector}:")
        for conflict in conflicts_found:
            print(f"    - {conflict['property']}:")
            print(f"      site-shell.css: {conflict['site_shell_value']}")
            print(f"      mega-menu.css:  {conflict['mega_menu_value']}")
    else:
        print("  ✓ No direct conflicts found for .mega-menu selector")
    
    # Also check .mega-container
    target_selector = '.mega-container'
    shell_container_props = {}
    mega_container_props = {}
    
    for rule in shell_rules:
        if rule['selector'] == target_selector:
            shell_container_props.update(rule['properties'])
    
    for rule in mega_rules:
        if rule['selector'] == target_selector:
            mega_container_props.update(rule['properties'])
    
    conflicts_found = []
    for prop in set(shell_container_props.keys()) & set(mega_container_props.keys()):
        if shell_container_props[prop] != mega_container_props[prop]:
            conflicts_found.append({
                'selector': target_selector,
                'property': prop,
                'site_shell_value': shell_container_props[prop],
                'mega_menu_value': mega_container_props[prop]
            })
            results['conflicting_rules'].append({
                'selector': target_selector,
                'property': prop,
                'site_shell_value': shell_container_props[prop],
                'mega_menu_value': mega_container_props[prop]
            })
    
    if conflicts_found:
        print(f"  ⚠ Found {len(conflicts_found)} conflicting property(ies) for {target_selector}:")
        for conflict in conflicts_found:
            print(f"    - {conflict['property']}:")
            print(f"      site-shell.css: {conflict['site_shell_value']}")
            print(f"      mega-menu.css:  {conflict['mega_menu_value']}")
    
    # Scan HTML files for used classes
    print(f"\nScanning {len(html_files)} HTML files for used classes...")
    all_used_classes = set()
    
    for html_file in html_files:
        content = read_file_content(html_file)
        if not content:
            continue
        
        # Extract classes from HTML
        html_classes = extract_html_classes(content)
        all_used_classes.update(html_classes)
        
        # Also extract inline styles and their classes
        inline_styles = extract_inline_styles(content)
        for style_content in inline_styles:
            style_classes = extract_classes_from_selectors([style_content])
            all_used_classes.update(extract_html_classes(style_content))
    
    results['all_used_classes'] = all_used_classes
    
    # Find unused classes
    unused_classes = all_defined_classes - all_used_classes
    
    print(f"\nDefined classes: {len(all_defined_classes)}")
    print(f"Used classes: {len(all_used_classes)}")
    print(f"Unused classes (potential dead code): {len(unused_classes)}")
    
    if unused_classes:
        print("\nUnused classes (candidates for removal):")
        for cls in sorted(unused_classes)[:50]:  # Show first 50
            print(f"  - {cls}")
        if len(unused_classes) > 50:
            print(f"  ... and {len(unused_classes) - 50} more")
    
    results['unused_classes'] = sorted(list(unused_classes))
    
    return results


def run_wcag_contrast_audit(repo_path, css_files, html_files):
    """Run WCAG Color Contrast Audit."""
    print("\n" + "="*80)
    print("WCAG COLOR CONTRAST AUDIT")
    print("="*80)
    
    results = {
        'color_pairs_analyzed': 0,
        'failing_combinations': [],
        'passing_combinations': [],
        'footer_issues': []
    }
    
    # Collect all color declarations
    color_declarations = []
    
    print("\nExtracting color declarations from CSS files...")
    
    for css_file in css_files:
        content = read_file_content(css_file)
        if not content:
            continue
        
        rel_path = os.path.relpath(css_file, repo_path)
        rules = parse_css_rules(content)
        
        for rule in rules:
            fg_color = None
            bg_color = None
            
            if 'color' in rule['properties']:
                fg_color = parse_color(rule['properties']['color'])
            
            if 'background-color' in rule['properties']:
                bg_color = parse_color(rule['properties']['background-color'])
            elif 'background' in rule['properties']:
                # Try to extract background color from shorthand
                bg_value = rule['properties']['background']
                bg_color = parse_color(bg_value.split()[0] if bg_value else '')
            
            # Check if this is a footer-related selector
            is_footer = 'footer' in rule['selector'].lower()
            
            if fg_color and bg_color:
                contrast = calculate_contrast_ratio(fg_color, bg_color)
                if contrast:
                    color_declarations.append({
                        'file': rel_path,
                        'selector': rule['selector'],
                        'fg_color': rule['properties'].get('color', ''),
                        'bg_color': rule['properties'].get('background-color', '') or rule['properties'].get('background', ''),
                        'fg_rgb': fg_color,
                        'bg_rgb': bg_color,
                        'contrast_ratio': contrast,
                        'is_footer': is_footer
                    })
    
    # Also check inline styles in HTML
    print("Extracting color declarations from HTML inline styles...")
    
    for html_file in html_files:
        content = read_file_content(html_file)
        if not content:
            continue
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Check style tags
        for style_tag in soup.find_all('style'):
            if style_tag.string:
                rules = parse_css_rules(style_tag.string)
                for rule in rules:
                    fg_color = None
                    bg_color = None
                    
                    if 'color' in rule['properties']:
                        fg_color = parse_color(rule['properties']['color'])
                    
                    if 'background-color' in rule['properties']:
                        bg_color = parse_color(rule['properties']['background-color'])
                    
                    if fg_color and bg_color:
                        contrast = calculate_contrast_ratio(fg_color, bg_color)
                        if contrast:
                            color_declarations.append({
                                'file': os.path.relpath(html_file, repo_path),
                                'selector': f"<style> {rule['selector']}",
                                'fg_color': rule['properties'].get('color', ''),
                                'bg_color': rule['properties'].get('background-color', ''),
                                'fg_rgb': fg_color,
                                'bg_rgb': bg_color,
                                'contrast_ratio': contrast,
                                'is_footer': 'footer' in rule['selector'].lower()
                            })
        
        # Check inline styles
        for elem in soup.find_all(style=True):
            style_str = elem.get('style', '')
            fg_match = re.search(r'color\s*:\s*([^;]+)', style_str)
            bg_match = re.search(r'background(?:-color)?\s*:\s*([^;]+)', style_str)
            
            if fg_match and bg_match:
                fg_color = parse_color(fg_match.group(1))
                bg_color = parse_color(bg_match.group(1))
                
                if fg_color and bg_color:
                    contrast = calculate_contrast_ratio(fg_color, bg_color)
                    if contrast:
                        color_declarations.append({
                            'file': os.path.relpath(html_file, repo_path),
                            'selector': f"<{elem.name} inline>",
                            'fg_color': fg_match.group(1),
                            'bg_color': bg_match.group(1),
                            'fg_rgb': fg_color,
                            'bg_rgb': bg_color,
                            'contrast_ratio': contrast,
                            'is_footer': False
                        })
    
    results['color_pairs_analyzed'] = len(color_declarations)
    
    # Analyze contrast ratios
    print(f"\nAnalyzing {len(color_declarations)} color combinations...")
    
    failing_normal = []
    failing_large = []
    passing = []
    footer_failures = []
    
    for decl in color_declarations:
        ratio = decl['contrast_ratio']
        passes_aa = check_wcag_aa(ratio, is_large_text=False)
        passes_aa_large = check_wcag_aa(ratio, is_large_text=True)
        
        decl['passes_aa_normal'] = passes_aa
        decl['passes_aa_large'] = passes_aa_large
        
        if not passes_aa:
            failing_normal.append(decl)
            if decl['is_footer']:
                footer_failures.append(decl)
        elif not passes_aa_large:
            failing_large.append(decl)
        else:
            passing.append(decl)
    
    results['failing_combinations'] = failing_normal + failing_large
    results['passing_combinations'] = passing
    results['footer_issues'] = footer_failures
    
    # Report results
    print(f"\nResults:")
    print(f"  Total color pairs analyzed: {len(color_declarations)}")
    print(f"  Passing WCAG AA (normal text): {len(passing)}")
    print(f"  Failing WCAG AA (normal text, ratio < 4.5:1): {len(failing_normal)}")
    print(f"  Failing WCAG AA (large text only, ratio < 3:1): {len(failing_large)}")
    
    if footer_failures:
        print(f"\n⚠ FOOTER CONTRAST ISSUES ({len(footer_failures)} found):")
        print("-" * 80)
        for issue in footer_failures[:10]:  # Show first 10
            print(f"  File: {issue['file']}")
            print(f"  Selector: {issue['selector']}")
            print(f"  Colors: {issue['fg_color']} on {issue['bg_color']}")
            print(f"  Contrast Ratio: {issue['contrast_ratio']:.2f}:1")
            print(f"  Required: 4.5:1 (normal text) or 3:1 (large text)")
            print()
    
    if failing_normal:
        print(f"\n⚠ ALL CONTRAST FAILURES ({len(failing_normal)} total):")
        print("-" * 80)
        for i, issue in enumerate(failing_normal[:20], 1):  # Show first 20
            severity = "🔴 FOOTER" if issue['is_footer'] else "  "
            print(f"{i}. {severity} {issue['file']}")
            print(f"   Selector: {issue['selector']}")
            print(f"   Colors: {issue['fg_color']} on {issue['bg_color']}")
            print(f"   Contrast Ratio: {issue['contrast_ratio']:.2f}:1 (fails AA)")
            print()
        
        if len(failing_normal) > 20:
            print(f"... and {len(failing_normal) - 20} more failures")
    
    if failing_large:
        print(f"\n⚠ LARGE TEXT ONLY FAILURES ({len(failing_large)} total):")
        print("-" * 80)
        for i, issue in enumerate(failing_large[:10], 1):
            print(f"{i}. {issue['file']}")
            print(f"   Selector: {issue['selector']}")
            print(f"   Colors: {issue['fg_color']} on {issue['bg_color']}")
            print(f"   Contrast Ratio: {issue['contrast_ratio']:.2f}:1")
            print(f"   Status: Passes normal text (≥4.5:1) but fails large text (<3:1)")
            print()
    
    return results


def generate_report(css_results, wcag_results, output_path):
    """Generate a comprehensive JSON and Markdown report."""
    
    # JSON Report
    json_report = {
        'audit_summary': {
            'css_files_analyzed': len(css_results['css_files_analyzed']),
            'total_css_rules': css_results['total_rules'],
            'defined_classes': len(css_results['all_defined_classes']),
            'used_classes': len(css_results['all_used_classes']),
            'unused_classes': len(css_results['unused_classes']),
            'conflicting_rules': len(css_results['conflicting_rules']),
            'color_pairs_analyzed': wcag_results['color_pairs_analyzed'],
            'wcag_failing_combinations': len(wcag_results['failing_combinations']),
            'wcag_passing_combinations': len(wcag_results['passing_combinations']),
            'footer_contrast_issues': len(wcag_results['footer_issues'])
        },
        'css_audit': css_results,
        'wcag_audit': wcag_results
    }
    
    # Convert sets to lists for JSON serialization
    json_report['css_audit']['all_defined_classes'] = list(css_results['all_defined_classes'])
    json_report['css_audit']['all_used_classes'] = list(css_results['all_used_classes'])
    
    with open(output_path.replace('.md', '.json'), 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2, default=str)
    
    # Markdown Report
    md_report = f"""# Web Accessibility & Performance Audit Report

Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

| Metric | Value |
|--------|-------|
| CSS Files Analyzed | {len(css_results['css_files_analyzed'])} |
| Total CSS Rules | {css_results['total_rules']} |
| Defined Classes | {len(css_results['all_defined_classes'])} |
| Used Classes | {len(css_results['all_used_classes'])} |
| **Unused Classes** | **{len(css_results['unused_classes'])}** |
| Conflicting Rules | {len(css_results['conflicting_rules'])} |
| Color Pairs Analyzed | {wcag_results['color_pairs_analyzed']} |
| **WCAG Failures** | **{len(wcag_results['failing_combinations'])}** |
| Footer Issues | {len(wcag_results['footer_issues'])} |

---

## 1. CSS Architecture & Dead Code Audit

### Files Analyzed
"""
    
    for f in css_results['css_files_analyzed']:
        md_report += f"- `{f}`\n"
    
    md_report += "\n### Conflicting Rules\n\n"
    
    if css_results['conflicting_rules']:
        for conflict in css_results['conflicting_rules']:
            md_report += f"""#### Selector: `{conflict['selector']}`

| Property | site-shell.css | mega-menu.css |
|----------|----------------|---------------|
| {conflict['property']} | `{conflict['site_shell_value']}` | `{conflict['mega_menu_value']}` |

"""
    else:
        md_report += "No conflicting rules found.\n"
    
    md_report += "\n### Unused CSS Classes (Dead Code)\n\n"
    
    if css_results['unused_classes']:
        md_report += f"**{len(css_results['unused_classes'])} unused classes found:**\n\n"
        md_report += "| Class Name |\n|------------|\n"
        for cls in css_results['unused_classes'][:50]:
            md_report += f"| `{cls}` |\n"
        if len(css_results['unused_classes']) > 50:
            md_report += f"\n*... and {len(css_results['unused_classes']) - 50} more (see JSON report)*\n"
    else:
        md_report += "No unused classes found.\n"
    
    md_report += """
---

## 2. WCAG Color Contrast Audit

### Summary

"""
    
    if wcag_results['failing_combinations']:
        md_report += f"**⚠ {len(wcag_results['failing_combinations'])} color combinations fail WCAG AA standards**\n\n"
    else:
        md_report += "**✓ All color combinations pass WCAG AA standards**\n\n"
    
    if wcag_results['footer_issues']:
        md_report += f"""### 🚨 Footer Contrast Issues (Priority)

{len(wcag_results['footer_issues'])} footer color combinations fail WCAG AA:

| File | Selector | Foreground | Background | Ratio | Required |
|------|----------|------------|------------|-------|----------|
"""
        for issue in wcag_results['footer_issues'][:10]:
            md_report += f"| `{issue['file']}` | `{issue['selector']}` | `{issue['fg_color']}` | `{issue['bg_color']}` | {issue['contrast_ratio']:.2f}:1 | 4.5:1 |\n"
        md_report += "\n"
    
    if wcag_results['failing_combinations']:
        md_report += """### All Failing Combinations

| File | Selector | Foreground | Background | Ratio | Status |
|------|----------|------------|------------|-------|--------|
"""
        for issue in wcag_results['failing_combinations'][:30]:
            status = "🔴 Footer" if issue['is_footer'] else "Normal"
            md_report += f"| `{issue['file']}` | `{issue['selector']}` | `{issue['fg_color']}` | `{issue['bg_color']}` | {issue['contrast_ratio']:.2f}:1 | {status} |\n"
        
        if len(wcag_results['failing_combinations']) > 30:
            md_report += f"\n*... and {len(wcag_results['failing_combinations']) - 30} more (see JSON report)*\n"
    
    md_report += """
---

## Recommendations

### CSS Architecture
1. **Resolve Conflicts**: Review and consolidate conflicting rules between `site-shell.css` and `mega-menu.css`
2. **Remove Dead Code**: Consider removing unused CSS classes to reduce file size
3. **Consolidate Files**: Consider merging related CSS files to avoid duplication

### WCAG Accessibility
1. **Fix Footer Contrast**: Prioritize fixing footer text colors against dark backgrounds
2. **Review All Failures**: Address all failing color combinations to meet WCAG AA standards
3. **Test with Tools**: Verify fixes using browser accessibility tools

---

*Report generated by Web Accessibility & Performance Audit Script*
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    
    print(f"\n✅ Reports generated:")
    print(f"   - Markdown: {output_path}")
    print(f"   - JSON: {output_path.replace('.md', '.json')}")


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Main entry point for the audit script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Web Accessibility & Performance Audit')
    parser.add_argument('--repo-path', default='/workspace', help='Path to repository root')
    parser.add_argument('--output', default='/workspace/audit_report.md', help='Output report path')
    args = parser.parse_args()
    
    repo_path = args.repo_path
    output_path = args.output
    
    print("="*80)
    print("WEB ACCESSIBILITY & FRONT-END PERFORMANCE AUDIT")
    print("="*80)
    print(f"\nRepository: {repo_path}")
    print(f"Output: {output_path}\n")
    
    # Scan repository
    print("Scanning repository...")
    html_files, css_files = scan_repository(repo_path)
    print(f"Found {len(html_files)} HTML files and {len(css_files)} CSS files")
    
    # Run audits
    css_results = run_css_architecture_audit(repo_path, html_files, css_files)
    wcag_results = run_wcag_contrast_audit(repo_path, css_files, html_files)
    
    # Generate report
    generate_report(css_results, wcag_results, output_path)
    
    print("\n" + "="*80)
    print("AUDIT COMPLETE")
    print("="*80)


if __name__ == '__main__':
    main()
