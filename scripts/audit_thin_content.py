#!/usr/bin/env python3
"""
Thin Content Audit Script for Static HTML Websites
==================================================
Scans all .html files in a repository, calculates body content word count,
and generates a prioritized CSV + Markdown report of pages below the
word-count threshold.

Designed to run safely inside GitHub Actions:
  - Always exits with code 0 (unless a fatal config error occurs), so a
    "no thin pages found" result does not fail the pipeline.
  - Writes scripts/thin_content_report.csv, creating directories as needed.
  - Logs per-file parse failures to stderr instead of silently skipping.

Author: SEO Technical Auditor
Date: 2026
"""

import csv
import re
import sys
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("BeautifulSoup is required: pip install beautifulsoup4 lxml")


# ---------- Configuration ----------

WORD_COUNT_THRESHOLD = 500

# 1 CJK character ~= 1 word. Some SEO tools use 1.5-2; tune as needed.
CJK_CHARS_PER_WORD = 1.0

CJK_RE = re.compile(
    r'[\u3040-\u30ff'      # Hiragana + Katakana
    r'\u3400-\u4dbf'       # CJK Extension A
    r'\u4e00-\u9fff'       # CJK Unified Ideographs
    r'\uf900-\ufaff'       # CJK Compatibility Ideographs
    r'\uff66-\uff9f]'      # Halfwidth Katakana
)

CONTENT_CLASS_RE = re.compile(
    r'(^|[-_])('
    r'content|article-content|post-content|entry-content|main-content'
    r')([-_]|$)',
    re.IGNORECASE,
)

BOILERPLATE_TAGS = ('script', 'style', 'nav', 'footer', 'header', 'aside')

CSV_FIELDNAMES = ['file_path', 'word_count', 'page_title', 'action']


# ---------- Exclusion ----------

def is_excluded(html_file: Path) -> bool:
    """
    Return True if this HTML file should be skipped by the audit.
    Excludes:
      - template files (*_template.html)
      - 404 pages
      - any index.html (category / listing pages)
    """
    name = html_file.name
    if name.endswith('_template.html'):
        return True
    if '404' in name.lower():
        return True
    if name == 'index.html':
        return True
    return False


# ---------- Parsing / extraction ----------

def remove_boilerplate_tags(soup: BeautifulSoup) -> BeautifulSoup:
    """Strip tags whose text should not count toward content word count."""
    for tag_name in BOILERPLATE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    return soup


def _is_ancestor(ancestor, node) -> bool:
    """Identity-based ancestor check (Tag.__eq__ is unreliable in bs4)."""
    return any(p is ancestor for p in node.parents)


def extract_main_content(soup: BeautifulSoup) -> str:
    """
    Extract text content, counting each region exactly once.

    Priority:
      1. <main> and/or <article> elements
      2. common content container classes / id="content"
      3. <body> after boilerplate removal
      4. whole document

    Nested candidates are collapsed to their outermost ancestor so that an
    <article> inside <main> (or a <div class="content"> inside <main>) is
    not counted twice.
    """
    candidates = []

    main_tag = soup.find('main')
    if main_tag:
        candidates.append(main_tag)

    candidates.extend(soup.find_all('article'))

    if not candidates:
        candidates.extend(
            soup.find_all(['div', 'section'], class_=CONTENT_CLASS_RE)
        )
        id_content = soup.find(id='content')
        if id_content:
            candidates.append(id_content)

    if candidates:
        top_level = [
            c for c in candidates
            if not any(c is not o and _is_ancestor(o, c) for o in candidates)
        ]
        return ' '.join(
            el.get_text(separator=' ', strip=True) for el in top_level
        )

    body = soup.find('body')
    if body:
        return body.get_text(separator=' ', strip=True)
    return soup.get_text(separator=' ', strip=True)


def clean_text_for_word_count(text: str) -> str:
    """Normalize whitespace and strip zero-width / non-breaking characters."""
    text = re.sub(r'[\xa0\u200b\u200c\u200d]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def count_words(text: str) -> int:
    """
    Whitespace-delimited words for Latin scripts, plus one word per CJK
    character (so CJK pages aren't massively under-counted).
    """
    if not text:
        return 0

    cjk_chars = len(CJK_RE.findall(text))
    latin_text = CJK_RE.sub(' ', text)   # so CJK chars aren't also split
    latin_words = sum(1 for w in latin_text.split() if w)

    return latin_words + int(round(cjk_chars / CJK_CHARS_PER_WORD))


def get_page_title(soup: BeautifulSoup) -> str:
    title_tag = soup.find('title')
    return title_tag.get_text(strip=True) if title_tag else 'No Title'


def get_action_recommendation(word_count: int) -> str:
    if word_count < 100:
        return 'Consider Noindex or Merge'
    if word_count < 200:
        return 'Expand Significantly or Noindex'
    if word_count < 300:
        return 'Expand to 500+ words'
    if word_count < 400:
        return 'Expand to 600+ words'
    if word_count < 500:
        return 'Expand to 800+ words'
    return 'OK'


# ---------- Per-file audit ----------

def audit_html_file(file_path: Path, base_dir: Path):
    """
    Audit a single HTML file.
    Returns a dict on success, or None if the file could not be read/parsed
    (with a diagnostic printed to stderr).
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            content = file_path.read_text(encoding='latin-1')
        except Exception as exc:
            print(f"[skip] {file_path}: {exc}", file=sys.stderr)
            return None
    except Exception as exc:
        print(f"[skip] {file_path}: {exc}", file=sys.stderr)
        return None

    # Parse (fall back to stdlib parser if lxml is unavailable)
    try:
        soup = BeautifulSoup(content, 'lxml')
    except Exception:
        try:
            soup = BeautifulSoup(content, 'html.parser')
        except Exception as exc:
            print(f"[skip] {file_path}: parse failed: {exc}", file=sys.stderr)
            return None

    soup = remove_boilerplate_tags(soup)
    text = clean_text_for_word_count(extract_main_content(soup))
    word_count = count_words(text)

    try:
        rel_path = str(file_path.relative_to(base_dir))
    except ValueError:
        rel_path = str(file_path)

    return {
        'file_path': rel_path,
        'word_count': word_count,
        'page_title': get_page_title(soup),
        'action': get_action_recommendation(word_count),
    }


# ---------- Reporting ----------

def generate_markdown_table(results: list) -> str:
    if not results:
        return "No thin content pages found."

    md = "| File Path | Word Count | Page Title | Action Recommendation |\n"
    md += "|-----------|------------|------------|----------------------|\n"

    for r in sorted(results, key=lambda x: x['word_count']):
        title = r['page_title'].replace('|', r'\|')
        if len(title) > 60:
            title = title[:57] + '...'
        md += (
            f"| {r['file_path']} | {r['word_count']} | "
            f"{title} | {r['action']} |\n"
        )

    return md


def save_csv_report(results: list, output_path: Path) -> None:
    """Write the CSV report, creating parent directories as needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for r in sorted(results, key=lambda x: x['word_count']):
            writer.writerow(r)


# ---------- Entry point ----------

def main():
    # Resolve so symlinks / GH Actions cwd don't shift the base dir
    base_dir = Path(__file__).resolve().parent.parent

    print("=" * 60)
    print("THIN CONTENT AUDIT SCRIPT")
    print("=" * 60)
    print(f"\nScanning directory: {base_dir}")

    all_html_files = list(base_dir.rglob("*.html"))
    files_to_audit = [f for f in all_html_files if not is_excluded(f)]
    excluded_count = len(all_html_files) - len(files_to_audit)

    print(f"Found {len(all_html_files)} total HTML files")
    print(f"Excluded {excluded_count} files (templates, 404, index pages)")
    print(f"Auditing {len(files_to_audit)} content pages\n")

    thin_content_pages = []
    failures = []

    for i, html_file in enumerate(files_to_audit, 1):
        if i % 100 == 0:
            print(f"Progress: {i}/{len(files_to_audit)} files processed...")

        result = audit_html_file(html_file, base_dir)
        if result is None:
            failures.append(html_file)
            continue
        if result['word_count'] < WORD_COUNT_THRESHOLD:
            thin_content_pages.append(result)

    print(f"\n{'=' * 60}")
    print("AUDIT COMPLETE")
    print(f"{'=' * 60}")
    print(f"Total pages audited: {len(files_to_audit)}")
    print(
        f"Thin content pages (< {WORD_COUNT_THRESHOLD} words): "
        f"{len(thin_content_pages)}"
    )
    if failures:
        print(f"Failed to read/parse: {len(failures)}")
        for f in failures[:10]:
            print(f"  - {f.relative_to(base_dir) if f.is_relative_to(base_dir) else f}")
        if len(failures) > 10:
            print(f"  ... and {len(failures) - 10} more")
    print(f"{'=' * 60}\n")

    if thin_content_pages:
        print("THIN CONTENT PAGES REPORT")
        print("-" * 60)
        print(generate_markdown_table(thin_content_pages))
        print("-" * 60)

        csv_output = base_dir / "scripts" / "thin_content_report.csv"
        save_csv_report(thin_content_pages, csv_output)
        print(f"\nCSV report saved to: {csv_output}")

        # Summary by action category
        print("\n\nSUMMARY BY ACTION CATEGORY:")
        print("-" * 40)
        action_counts = {}
        for page in thin_content_pages:
            action_counts[page['action']] = action_counts.get(page['action'], 0) + 1
        for action, count in sorted(action_counts.items(), key=lambda x: -x[1]):
            print(f"  {action}: {count} pages")
    else:
        print(
            f"No thin content pages found! "
            f"All pages have {WORD_COUNT_THRESHOLD}+ words."
        )
        # Still write an empty CSV with headers so downstream tooling
        # (like expand_thin_content.py) doesn't blow up on a missing file.
        csv_output = base_dir / "scripts" / "thin_content_report.csv"
        save_csv_report([], csv_output)
        print(f"Empty CSV (headers only) written to: {csv_output}")

    # Explicit success exit — never fail CI on "no thin pages"
    return 0


if __name__ == "__main__":
    sys.exit(main())
