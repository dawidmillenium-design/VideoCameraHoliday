#!/usr/bin/env python3
"""
Idempotent Design B injector.

Reads templates/design-b-fragment.html, extracts the three marker-delimited
sections, and splices them into every HTML file that does not already
contain the DESIGN-B-HEADER-START marker.

Key safety rules:
  - Never calls soup.head.clear() or replace_with().
  - Appends to <head>; inserts header at top of <body>; appends footer at end.
  - Skips any file that already contains the marker.
  - Excludes templates/ and build dirs.
"""

import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
FRAGMENT = ROOT / "templates" / "design-b-fragment.html"

EXCLUDE_DIRS = {"templates", "node_modules", ".git", "__pycache__",
                "scripts", "workspace", "data", "docs", "output"}

MARKER_HEADER = "=== DESIGN-B-HEADER-START ==="


def read_sections() -> dict:
    text = FRAGMENT.read_text(encoding="utf-8")

    def between(start_marker: str, end_marker: str) -> str:
        a = text.find(start_marker)
        b = text.find(end_marker)
        if a == -1 or b == -1 or b < a:
            raise SystemExit(f"Marker pair missing: {start_marker} / {end_marker}")
        return text[a + len(start_marker):b].strip()

    return {
        "head":   between("<!-- === DESIGN-B-HEAD-START === -->",
                          "<!-- === DESIGN-B-HEAD-END === -->"),
        "header": between("<!-- === DESIGN-B-HEADER-START === -->",
                          "<!-- === DESIGN-B-HEADER-END === -->"),
        "footer": between("<!-- === DESIGN-B-FOOTER-START === -->",
                          "<!-- === DESIGN-B-FOOTER-END === -->"),
    }


def _append_html(target, fragment_html: str):
    frag = BeautifulSoup(fragment_html, "html.parser")
    for node in list(frag.children):
        if hasattr(node, "extract"):
            target.append(node.extract())
        else:
            target.append(str(node))


def _prepend_html(target, fragment_html: str):
    frag = BeautifulSoup(fragment_html, "html.parser")
    for node in reversed(list(frag.children)):
        if hasattr(node, "extract"):
            target.insert(0, node.extract())
        else:
            target.insert(0, str(node))


def inject(file_path: Path, sections: dict) -> str:
    html = file_path.read_text(encoding="utf-8")
    if MARKER_HEADER in html:
        return "skip: already injected"

    soup = BeautifulSoup(html, "lxml")

    if not soup.head or not soup.body:
        return "skip: no <head> or <body>"

    # HEAD — append only. Never clear. Never replace.
    _append_html(soup.head, sections["head"])

    # HEADER — insert before the first real body element
    # (leave any leading <noscript> skip-links / SVG sprite at the very top)
    header_frag = BeautifulSoup(sections["header"], "html.parser")
    insert_at = 0
    for i, node in enumerate(soup.body.contents):
        if getattr(node, "name", None) not in (None, "noscript"):
            insert_at = i
            break
    for offset, node in enumerate(list(header_frag.children)):
        if hasattr(node, "extract"):
            soup.body.insert(insert_at + offset, node.extract())
        else:
            soup.body.insert(insert_at + offset, str(node))

    # FOOTER — append at end of body
    _append_html(soup.body, sections["footer"])

    file_path.write_text(str(soup), encoding="utf-8")
    return "injected"


def main():
    if not FRAGMENT.exists():
        sys.exit(f"Fragment not found: {FRAGMENT}")

    sections = read_sections()
    print(f"Loaded sections: {', '.join(sections)} "
          f"({sum(len(v) for v in sections.values())} chars)")

    all_html = list(ROOT.rglob("*.html"))
    candidates = [
        f for f in all_html
        if not any(part in EXCLUDE_DIRS for part in f.relative_to(ROOT).parts[:-1])
        and not f.name.endswith("_template.html")
    ]

    print(f"Found {len(candidates)} candidate files")

    stats = {"injected": 0, "skip: already injected": 0, "skip: no <head> or <body>": 0}

    for i, path in enumerate(candidates, 1):
        result = inject(path, sections)
        stats[result] = stats.get(result, 0) + 1
        if result == "injected":
            print(f"  ✓ {path.relative_to(ROOT)}")
        if i % 100 == 0:
            print(f"  ...{i}/{len(candidates)}")

    print("\nSummary:")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
