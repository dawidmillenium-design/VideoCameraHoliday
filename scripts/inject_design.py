#!/usr/bin/env python3
"""
Inject Design B header/footer/drawer into all HTML files in the repository.
Uses marker-based replacement so it can be run multiple times safely.
Fails if the template sections are empty to prevent silent corruption.
"""

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TEMPLATE_FILE = REPO_ROOT / "templates" / "design-b.html"
EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", "workspace",
    "generated-content", "data", "media", "assets", "scripts"
}
TARGET_DIRS = {
    ".", "about", "accessories", "comparisons", "destinations",
    "editing", "guides", "how-to", "reviews", "city-through-the-lens",
    "de-DE", "de", "es-ES", "es", "fr-FR", "it-IT", "ja-JP", "jp",
    "ko-KR", "pl-PL", "pt-br", "th-TH", "zh-CN"
}

def load_template():
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
            raise ValueError(f"❌ Missing section: {name} (markers not found in template)")

        body = match.group(1).strip()

        if len(body) < 20:
            raise ValueError(
                f"❌ Section '{name}' is suspiciously small ({len(body)} chars). "
                f"Did you forget to paste the content between the markers?"
            )

        sections[name.lower()] = body

    total = sum(len(v) for v in sections.values())
    print(f"✅ Loaded sections: {', '.join(sections.keys())} ({total} total chars)")
    return sections


def process_file(file_path, sections):
    try:
        html = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"  ⚠️  Skipping (encoding error): {file_path}")
        return False

    original = html

    # --- 1. Clean <head>: remove ALL previous design-b.css links and inline <style> blocks ---
    head_match = re.search(
        r'(<head[^>]*>)(.*?)(</head>)',
        html, re.DOTALL | re.IGNORECASE
    )
    if head_match:
        head_open, head_content, head_close = head_match.groups()

        # Remove ALL <style>...</style> blocks
        head_content = re.sub(
            r'<style[^>]*>.*?</style>', '',
            head_content, flags=re.DOTALL | re.IGNORECASE
        )

        # Remove ALL previous design-b.css <link> tags (dedupe bug fix)
        head_content = re.sub(
            r'<link[^>]*href=["\'][^"\']*design-b\.css["\'][^>]*>\s*',
            '', head_content, flags=re.IGNORECASE
        )

        # Remove duplicate "Design B" HTML comments left over from prior runs
        head_content = re.sub(
            r'<!--\s*Design B:[^>]*-->\s*',
            '', head_content, flags=re.IGNORECASE
        )

        # Remove leftover <noscript> design-b.css wrappers if any
        head_content = re.sub(
            r'<noscript>\s*<link[^>]*design-b\.css[^>]*>\s*</noscript>\s*',
            '', head_content, flags=re.DOTALL | re.IGNORECASE
        )

        new_head = (
            head_open.rstrip() + "\n    " +
            sections["head"].strip() + "\n" +
            head_content.strip() + "\n" +
            head_close
        )
        html = html[:head_match.start()] + new_head + html[head_match.end():]

    # --- 2. Replace everything between <body> and <main>/<article>/hero with new header ---
    body_match = re.search(r'(<body[^>]*>)', html, re.DOTALL | re.IGNORECASE)
    if body_match:
        body_start = body_match.end()
        main_match = re.search(
            r'(<main[^>]*>|<article[^>]*>|<section[^>]*class="hero")',
            html[body_start:], re.DOTALL | re.IGNORECASE
        )
        if main_match:
            header_end = body_start + main_match.start()
            html = (
                html[:body_start] + "\n\n" +
                sections["header"].strip() + "\n\n" +
                html[header_end:]
            )

    # --- 3. Replace everything between </main>/</article> and </body> with new footer ---
    footer_match = re.search(
        r'(</main>|</article>)(.*?)(</body>)',
        html, re.DOTALL | re.IGNORECASE
    )
    if footer_match:
        main_close, between, body_close = footer_match.groups()
        html = (
            html[:footer_match.start()] +
            main_close + "\n\n" +
            sections["footer"].strip() + "\n\n" +
            body_close + html[footer_match.end():]
        )

    if html != original:
        file_path.write_text(html, encoding="utf-8")
        return True
    return False


def main():
    print("🚀 Design B Injection — Starting")
    print(f"📄 Template: {TEMPLATE_FILE}")

    sections = load_template()

    processed = updated = skipped = 0

    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

        rel_path = Path(dirpath).relative_to(REPO_ROOT)
        if str(rel_path) not in TARGET_DIRS and str(rel_path) != ".":
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
