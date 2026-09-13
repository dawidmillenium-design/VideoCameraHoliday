#!/usr/bin/env python3
"""
Targeted fix: add /VideoCameraHoliday/ prefix to root-relative links
in article bodies.

STRICT SAFETY:
  - Only modifies href="..." and src="..." attribute values.
  - Only adds a prefix when the path starts with '/' and is missing it.
  - Never touches external URLs, anchors (#foo), mailto:, tel:.
  - Never modifies anything that already starts with /VideoCameraHoliday/.
  - Default mode is DRY-RUN. Pass --apply to write.

This will fix links like:
    href="/destinations/foo.html"
into:
    href="/VideoCameraHoliday/destinations/foo.html"

Header, footer, and drawer links are already correct and will be skipped.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SITE_BASE = "/VideoCameraHoliday"

EXCLUDE_DIRS = {
    "templates", "scripts", "node_modules", ".git", "__pycache__",
    "workspace", "data", "docs", "output", "generated-content",
    "city-generator",
}

# Root-relative path prefixes that need the site base prepended.
PATH_PREFIXES = (
    "destinations", "guides", "how-to", "reviews", "comparisons",
    "editing", "about", "city-through-the-lens", "accessories",
    "interviews", "game",
)

# Root-level HTML files that also need the prefix.
ROOT_FILES = (
    "privacy.html", "terms.html", "contact.html", "disclaimer.html",
    "sitemap.xml", "start-here.html", "index.html", "camera-tests.html",
)

# Match href="..." and src="..." — both quote styles.
ATTR_RE = re.compile(
    r'\b(href|src)=(["\'])(/[^"\'\s>]+)\2',
    re.IGNORECASE,
)


def needs_prefix(path: str) -> str | None:
    """Return the corrected path, or None if it's already correct."""
    if not path.startswith("/"):
        return None
    if path.startswith("//"):                        # protocol-relative
        return None
    if path == SITE_BASE or path.startswith(SITE_BASE + "/"):
        return None                                   # already correct

    stripped = path.lstrip("/")
    for p in PATH_PREFIXES:
        if stripped == p or stripped.startswith(p + "/"):
            return f"{SITE_BASE}/{stripped}"
    if stripped in ROOT_FILES:
        return f"{SITE_BASE}/{stripped}"
    return None


def fix_html(html: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (new_html, list_of_(old, new)_pairs)."""
    fixes: list[tuple[str, str]] = []

    def _sub(m: re.Match) -> str:
        attr, quote, path = m.group(1), m.group(2), m.group(3)
        fixed = needs_prefix(path)
        if fixed is None:
            return m.group(0)
        fixes.append((path, fixed))
        return f'{attr}={quote}{fixed}{quote}'

    return ATTR_RE.sub(_sub, html), fixes


def process(path: Path, apply: bool):
    original = path.read_text(encoding="utf-8", errors="replace")
    fixed, changes = fix_html(original)
    if fixed == original:
        return 0, []
    if apply:
        path.write_text(fixed, encoding="utf-8")
    return len(changes), changes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verbose", action="store_true",
                    help="Print each old→new link pair")
    ap.add_argument("--only", default=None,
                    help="Limit to a single file (relative path)")
    args = ap.parse_args()

    if args.only:
        targets = [ROOT / args.only]
    else:
        targets = []
        for p in ROOT.rglob("*.html"):
            rel_parts = p.relative_to(ROOT).parts[:-1]
            if any(part in EXCLUDE_DIRS for part in rel_parts):
                continue
            if p.name.endswith("_template.html"):
                continue
            targets.append(p)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"Mode: {mode}")
    print(f"Scanning {len(targets)} files...\n")

    total_files = 0
    total_links = 0

    for path in targets:
        count, changes = process(path, args.apply)
        if count == 0:
            continue
        total_files += 1
        total_links += count
        rel = path.relative_to(ROOT)
        marker = "✓" if args.apply else "•"
        print(f"  {marker} {rel}  ({count} link(s))")
        if args.verbose:
            for old, new in changes[:5]:
                print(f"      {old}")
                print(f"      → {new}")
            if len(changes) > 5:
                print(f"      ... and {len(changes) - 5} more")

    print(f"\n{'=' * 60}")
    print(f"  Files affected  : {total_files}")
    print(f"  Links to fix    : {total_links}")
    print(f"  Mode            : {mode}")
    if not args.apply and total_links > 0:
        print("\n  Re-run with --apply to write changes.")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
