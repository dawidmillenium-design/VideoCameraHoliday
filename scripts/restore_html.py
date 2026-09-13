#!/usr/bin/env python3
"""
SUBTRACTIVE-ONLY HTML restorer for VideoCameraHoliday.

Guarantees:
  - NEVER creates new tags
  - NEVER wraps anything in <style>
  - NEVER restructures the DOM tree
  - Only removes the specific junk patterns documented below

Fixes applied (each is a plain string removal):
  1. Raw git conflict markers (<<<<<<<, =======, >>>>>>>)
  2. HTML-escaped conflict markers (&gt;&gt;&gt;…, &lt;&lt;&lt;…)
  3. Stray <base href="..."> tags
  4. Duplicate <link ... design-b.css> (keeps the first occurrence)
  5. Orphan CSS text nodes sitting outside any <style> block
  6. Duplicate <head>, <body> opening tags (keeps the first)
  7. Duplicate </html> closing tags (keeps the first)

Anything that looks like a duplicate but is ambiguous is LEFT ALONE.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {
    "templates", "scripts", "node_modules", ".git", "__pycache__",
    "workspace", "data", "docs", "output", "generated-content",
    "city-generator",
}


# ---------------------------------------------------------------------------
# Removal helpers — all operate on raw HTML strings (no bs4)
# ---------------------------------------------------------------------------

def strip_raw_conflicts(html: str) -> tuple[str, int]:
    """Remove standard git conflict blocks, keep the 'theirs' side text."""
    pattern = re.compile(
        r"^<{7}[^\n]*\n.*?^={7}\n(.*?)^>{7}[^\n]*\n?",
        re.MULTILINE | re.DOTALL,
    )
    count = 0

    def _sub(m: re.Match) -> str:
        nonlocal count
        count += 1
        return m.group(1)

    html = pattern.sub(_sub, html)
    # Orphan markers on their own lines
    for pat in (r"^<{7}[^\n]*\n", r"^={7}\n", r"^>{7}[^\n]*\n"):
        html, n = re.subn(pat, "", html, flags=re.MULTILINE)
        count += n
    return html, count


def strip_escaped_conflicts(html: str) -> tuple[str, int]:
    """Remove HTML-escaped conflict markers (&gt;×7 etc.)."""
    count = 0
    for pat in (
        r"&gt;{3,}[^\n<]*",
        r"&lt;{3,}[^\n<]*",
        r"={3,}\s*(?=\n|</)",       # stray ==== lines in escaped output
    ):
        html, n = re.subn(pat, "", html)
        count += n
    return html, count


def strip_base_tags(html: str) -> tuple[str, int]:
    return re.subn(r"<base\s+[^>]*>\s*", "", html, flags=re.IGNORECASE)


def dedupe_design_css(html: str) -> tuple[str, int]:
    """Keep the first <link ... design-b.css>; remove the rest."""
    pattern = re.compile(
        r"<link[^>]+href=\"[^\"]*design-b\.css\"[^>]*>\s*",
        re.IGNORECASE,
    )
    matches = list(pattern.finditer(html))
    if len(matches) <= 1:
        return html, 0

    result = html
    for m in reversed(matches[1:]):
        result = result[: m.start()] + result[m.end():]
    return result, len(matches) - 1


def strip_orphan_css(html: str) -> tuple[str, int]:
    """
    Remove CSS-rule-looking lines that sit OUTSIDE any <style> block.
    Splits on <style>...</style> and only touches the 'outside' segments.
    Never wraps anything — purely deletes lines that match a CSS rule pattern.
    """
    parts = re.split(
        r"(<style\b[^>]*>.*?</style>)",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    total = 0
    # A CSS rule line: starts with . or # or a letter, has { ... } on one line
    css_line = re.compile(
        r"^\s*[.#a-zA-Z][\w\s,>.:#()\[\]&+~-]*\s*\{[^{}\n]*\}\s*$",
        re.MULTILINE,
    )
    for i, chunk in enumerate(parts):
        if i % 2 == 1:            # inside <style>…</style>
            continue
        new_chunk, n = css_line.subn("", chunk)
        parts[i] = new_chunk
        total += n
    return "".join(parts), total


def dedupe_structural_tags(html: str) -> tuple[str, dict]:
    """Keep the FIRST opening <head>, <body>, and closing </html>; drop later ones."""
    counts = {"dup_head": 0, "dup_body": 0, "dup_html_close": 0}

    for tag_name, key, close in (
        ("head", "dup_head", False),
        ("body", "dup_body", False),
        ("html", "dup_html_close", True),
    ):
        if close:
            pattern = re.compile(r"</" + tag_name + r"\s*>", re.IGNORECASE)
        else:
            pattern = re.compile(
                r"<" + tag_name + r"\b[^>]*>", re.IGNORECASE
            )
        matches = list(pattern.finditer(html))
        if len(matches) <= 1:
            continue
        result = html
        for m in reversed(matches[1:]):
            result = result[: m.start()] + result[m.end():]
        html = result
        counts[key] = len(matches) - 1

    return html, counts


# ---------------------------------------------------------------------------
# Per-file processing
# ---------------------------------------------------------------------------

def fix_html(html: str) -> tuple[str, dict]:
    stats: dict[str, int] = {}
    for label, fn in (
        ("raw_conflicts", strip_raw_conflicts),
        ("escaped_conflicts", strip_escaped_conflicts),
        ("base_tags", strip_base_tags),
        ("dup_css", dedupe_design_css),
        ("orphan_css", strip_orphan_css),
    ):
        html, n = fn(html)
        if n:
            stats[label] = n

    html, structural = dedupe_structural_tags(html)
    for k, v in structural.items():
        if v:
            stats[k] = v

    # Cleanup: remove totally empty lines left behind
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html, stats


def process_file(path: Path) -> dict:
    original = path.read_text(encoding="utf-8", errors="replace")
    fixed, stats = fix_html(original)
    if fixed == original:
        return {"status": "unchanged"}
    path.write_text(fixed, encoding="utf-8")
    return {"status": "updated", **stats}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def iter_candidates() -> list[Path]:
    out = []
    for p in ROOT.rglob("*.html"):
        rel_parts = p.relative_to(ROOT).parts[:-1]
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        if p.name.endswith("_template.html"):
            continue
        out.append(p)
    return out


def main() -> int:
    files = iter_candidates()
    print(f"🔧 Restoring {len(files)} HTML files...\n")

    totals: dict[str, int] = {}
    updated = 0

    for i, path in enumerate(files, 1):
        result = process_file(path)
        if result["status"] == "unchanged":
            continue
        updated += 1
        for k, v in result.items():
            if k == "status":
                continue
            totals[k] = totals.get(k, 0) + v

        rel = path.relative_to(ROOT)
        summary = " ".join(f"{k}={v}" for k, v in result.items()
                           if k != "status")
        print(f"  ✓ {rel}  ({summary})")

        if i % 100 == 0:
            print(f"  ...{i}/{len(files)}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Files updated   : {updated}")
    print(f"  Files unchanged : {len(files) - updated}")
    for k in sorted(totals):
        print(f"  {k:20s}: {totals[k]}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
