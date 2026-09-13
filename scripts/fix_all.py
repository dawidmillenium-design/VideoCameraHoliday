#!/usr/bin/env python3
"""
Combined fixer for VideoCameraHoliday HTML files.

Fixes, in one pass:
  1. Removes git merge-conflict markers (<<<<<<<, =======, >>>>>>>) that were
     accidentally committed. If the "theirs" side contains CSS rules that
     should be in a <style> tag, wraps them correctly and moves them to <head>.
  2. Removes the <base href="/VideoCameraHoliday/"> tag (it broke all ../ links).
  3. Rewrites root-relative hrefs ("/destinations/...") to include the
     /VideoCameraHoliday/ prefix so they resolve on GitHub Pages.
  4. Removes duplicate design-b.css stylesheet links.

Idempotent: safe to run repeatedly. Only writes files that actually changed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Comment


ROOT = Path(__file__).resolve().parent.parent
SITE_BASE = "/VideoCameraHoliday"

EXCLUDE_DIRS = {
    "templates", "scripts", "node_modules", ".git", "__pycache__",
    "workspace", "data", "docs", "output", "generated-content",
    "city-generator",
}

# Root-relative path prefixes that must be rewritten with the site base.
# Anything NOT in this list (external URLs, anchors, /VideoCameraHoliday/...)
# is left alone.
REWRITE_PREFIXES = (
    "reviews", "guides", "destinations", "how-to", "comparisons",
    "editing", "about", "city-through-the-lens", "city-interview-preview",
    "accessories", "interviews", "game",
)

# Same idea for top-level files.
REWRITE_FILES = (
    "privacy.html", "terms.html", "contact.html", "disclaimer.html",
    "sitemap.xml", "start-here.html", "camera-tests.html", "index.html",
)

DESIGN_B_CSS = f"{SITE_BASE}/assets/design-b.css"


# ---------------------------------------------------------------------------
# Step 1 — strip git conflict markers from raw HTML
# ---------------------------------------------------------------------------

CONFLICT_START = re.compile(r"^<{7} .*$", re.MULTILINE)
CONFLICT_MID   = re.compile(r"^={7}$",        re.MULTILINE)
CONFLICT_END   = re.compile(r"^>{7} .*$",     re.MULTILINE)


def strip_conflict_markers(html: str) -> tuple[str, int]:
    """
    Remove git conflict markers. Keeps the content of the "theirs" side
    (between ======= and >>>>>>>) and drops the "ours" side.

    Returns (cleaned_html, count_of_conflicts_removed).
    """
    # Split into segments around full conflict blocks:
    #   <<<<<<< ... \n (ours) \n ======= \n (theirs) \n >>>>>>> ...
    pattern = re.compile(
        r"^<{7}[^\n]*\n.*?^={7}\n(.*?)^>{7}[^\n]*\n?",
        re.MULTILINE | re.DOTALL,
    )
    count = 0

    def _replace(m: re.Match) -> str:
        nonlocal count
        count += 1
        theirs = m.group(1)
        # If the theirs-side is CSS-like (contains `selector {`), wrap in <style>
        if re.search(r"[.#a-zA-Z][\w\s,>.:#-]*\s*\{", theirs) and "{" in theirs:
            return f"<style>\n{theirs.strip()}\n</style>\n"
        return theirs

    cleaned = pattern.sub(_replace, html)

    # Also remove any orphan markers left behind by partial conflicts
    for marker in (CONFLICT_START, CONFLICT_MID, CONFLICT_END):
        cleaned, n = marker.subn("", cleaned)
        count += n

    return cleaned, count


# ---------------------------------------------------------------------------
# Step 2 — find and wrap orphan CSS text nodes in <body>
# ---------------------------------------------------------------------------

CSS_RULE_RE = re.compile(r"[.#a-zA-Z][\w\s,>.:#()\[\]-]*\s*\{[^{}]*\}")


def wrap_orphan_css(soup: BeautifulSoup) -> int:
    """
    Find text nodes in <body> that look like raw CSS and move them into
    a <style> tag in <head>. Returns count of nodes wrapped.
    """
    if not soup.body or not soup.head:
        return 0

    wrapped = 0
    for node in list(soup.body.find_all(string=True)):
        if isinstance(node, (Comment,)):
            continue
        text = str(node).strip()
        if not text or len(text) < 20:
            continue
        # Heuristic: at least 2 CSS rules and a high brace ratio
        if text.count("{") >= 2 and text.count("{") == text.count("}") \
           and len(CSS_RULE_RE.findall(text)) >= 2:
            style_tag = soup.new_tag("style")
            style_tag.string = "\n" + text + "\n"
            soup.head.append(style_tag)
            node.replace_with("")
            wrapped += 1

    return wrapped


# ---------------------------------------------------------------------------
# Step 3 — remove <base> tag
# ---------------------------------------------------------------------------

def remove_base_tag(soup: BeautifulSoup) -> int:
    if not soup.head:
        return 0
    n = 0
    for base in soup.head.find_all("base"):
        base.decompose()
        n += 1
    return n


# ---------------------------------------------------------------------------
# Step 4 — rewrite root-relative links
# ---------------------------------------------------------------------------

def _should_rewrite(href: str) -> str | None:
    """
    Return the corrected href if it needs rewriting, else None.
    """
    if not href or not href.startswith("/"):
        return None
    if href.startswith(SITE_BASE + "/") or href == SITE_BASE:
        return None  # already correct
    if href.startswith("//"):
        return None  # protocol-relative

    # /prefix/... (directory)
    stripped = href.lstrip("/")
    for prefix in REWRITE_PREFIXES:
        if stripped == prefix or stripped.startswith(prefix + "/"):
            return f"{SITE_BASE}/{stripped}"

    # /file.html
    if stripped in REWRITE_FILES:
        return f"{SITE_BASE}/{stripped}"

    return None


def rewrite_root_relative_links(soup: BeautifulSoup) -> int:
    fixed = 0
    for tag in soup.find_all(["a", "link", "script", "img", "source"]):
        for attr in ("href", "src"):
            if not tag.has_attr(attr):
                continue
            new = _should_rewrite(tag[attr])
            if new:
                tag[attr] = new
                fixed += 1
    return fixed


# ---------------------------------------------------------------------------
# Step 5 — deduplicate design-b.css stylesheet
# ---------------------------------------------------------------------------

def dedupe_design_b_css(soup: BeautifulSoup) -> int:
    if not soup.head:
        return 0
    seen = set()
    removed = 0
    for link in soup.head.find_all("link", rel="stylesheet"):
        href = link.get("href")
        if href in seen:
            link.decompose()
            removed += 1
        else:
            seen.add(href)
    return removed


# ---------------------------------------------------------------------------
# Per-file processing
# ---------------------------------------------------------------------------

def process_file(path: Path) -> dict:
    try:
        original = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        original = path.read_text(encoding="latin-1")

    # Step 1: strip conflict markers on the raw string (before parsing)
    cleaned, conflicts = strip_conflict_markers(original)

    # Steps 2-5: operate on the parsed tree
    soup = BeautifulSoup(cleaned, "lxml")

    wrapped_css = wrap_orphan_css(soup)
    bases_removed = remove_base_tag(soup)
    links_fixed = rewrite_root_relative_links(soup)
    css_dupes = dedupe_design_b_css(soup)

    new_html = str(soup)

    if new_html == original:
        return {"status": "unchanged"}

    path.write_text(new_html, encoding="utf-8")
    return {
        "status": "updated",
        "conflicts": conflicts,
        "wrapped_css": wrapped_css,
        "bases_removed": bases_removed,
        "links_fixed": links_fixed,
        "css_dupes": css_dupes,
    }


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
    candidates = iter_candidates()
    print(f"🔎 Scanning {len(candidates)} HTML files...\n")

    totals = {
        "updated": 0, "unchanged": 0,
        "conflicts": 0, "wrapped_css": 0, "bases_removed": 0,
        "links_fixed": 0, "css_dupes": 0,
    }

    for i, path in enumerate(candidates, 1):
        result = process_file(path)
        if result["status"] == "unchanged":
            totals["unchanged"] += 1
            continue

        totals["updated"] += 1
        for k in ("conflicts", "wrapped_css", "bases_removed",
                  "links_fixed", "css_dupes"):
            totals[k] += result.get(k, 0)

        # Print only files with meaningful changes
        if any(result.get(k, 0) for k in
               ("conflicts", "wrapped_css", "bases_removed", "css_dupes")) \
           or result.get("links_fixed", 0) > 5:
            print(f"  ✓ {path.relative_to(ROOT)}  "
                  f"(conflicts={result.get('conflicts', 0)}  "
                  f"css={result.get('wrapped_css', 0)}  "
                  f"base={result.get('bases_removed', 0)}  "
                  f"links={result.get('links_fixed', 0)}  "
                  f"dup_css={result.get('css_dupes', 0)})")

        if i % 100 == 0:
            print(f"  ...{i}/{len(candidates)}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Files updated              : {totals['updated']}")
    print(f"  Files unchanged            : {totals['unchanged']}")
    print(f"  Conflict markers removed   : {totals['conflicts']}")
    print(f"  Orphan CSS wrapped         : {totals['wrapped_css']}")
    print(f"  <base> tags removed        : {totals['bases_removed']}")
    print(f"  Root-relative links fixed  : {totals['links_fixed']}")
    print(f"  Duplicate design-b.css removed: {totals['css_dupes']}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
