#!/usr/bin/env python3
"""
Enrich article bodies with Design B classes.
Safe to run multiple times (idempotent).
"""

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", "workspace",
    "generated-content", "data", "media", "assets", "scripts", "templates"
}


def slugify(text):
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)


def enrich(file_path):
    try:
        html = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False

    original = html

    # 1. Wrap "Disclosure:" paragraphs in the affiliate-disclosure class
    html = re.sub(
        r'(<p[^>]*>)(\s*<strong>\s*Disclosure[:\s]*</strong>.*?</p>)',
        r'<p class="affiliate-disclosure">\2',
        html, flags=re.DOTALL | re.IGNORECASE
    )

    # 2. Add id="..." to h2/h3 headings that don't have one (for anchor links)
    def add_id(match):
        tag, attrs, content = match.group(1), match.group(2), match.group(3)
        if 'id=' in attrs:
            return match.group(0)
        slug = slugify(re.sub(r'<[^>]+>', '', content))[:60]
        if not slug:
            return match.group(0)
        return f'<{tag}{attrs} id="{slug}">{content}</{tag}>'

    html = re.sub(
        r'<(h2|h3)([^>]*)>(.*?)</\1>',
        add_id, html, flags=re.DOTALL | re.IGNORECASE
    )

    # 3. Remove inline style attributes that fight with Design B
    #    (only removes style="" on main content tags, not on our own components)
    html = re.sub(
        r'(<(?:p|h2|h3|h4|ul|ol|li|a|div)(?![^>]*(?:site-header|drawer|hero|site-footer|card|share|cookie|takeaway))[^>]*)\s+style="[^"]*"',
        r'\1', html, flags=re.IGNORECASE
    )

    if html != original:
        file_path.write_text(html, encoding="utf-8")
        return True
    return False


def main():
    print("🚀 Enriching article bodies...")
    processed = updated = 0

    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            if not filename.endswith(".html"):
                continue
            file_path = Path(dirpath) / filename
            processed += 1
            try:
                if enrich(file_path):
                    updated += 1
                    print(f"  ✅ {file_path.relative_to(REPO_ROOT)}")
            except Exception as e:
                print(f"  ❌ {file_path.relative_to(REPO_ROOT)} — {e}")

    print(f"\n📊 {processed} scanned, {updated} updated")


if __name__ == "__main__":
    main()
