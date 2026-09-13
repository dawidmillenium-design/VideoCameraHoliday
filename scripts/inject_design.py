#!/usr/bin/env python3
"""
Design B injector — SAFE, IDEMPOTENT, SELF-CLEANING.

This script is a full replacement for earlier injectors. On each run it:

  1. Removes ALL existing Design B blocks (headers, drawers, footers,
     cookie banners, shared <script>), including duplicates from previous
     runs that left two copies of the header/footer on every page.
  2. Removes the broken <link href="/assets/design-b.css"> (missing repo
     prefix) and deduplicates identical stylesheet links.
  3. Ensures <base href="/VideoCameraHoliday/"> is present so relative
     links resolve correctly on GitHub Pages.
  4. Ensures <link rel="canonical"> matches the file's deployed URL.
  5. Re-injects ONE clean copy of the head/header/footer sections, wrapped
     in marker comments so re-runs are no-ops.

Idempotency markers:
    <!-- === DESIGN-B-HEAD-START === -->     ... <!-- === DESIGN-B-HEAD-END === -->
    <!-- === DESIGN-B-HEADER-START === -->   ... <!-- === DESIGN-B-HEADER-END === -->
    <!-- === DESIGN-B-FOOTER-START === -->   ... <!-- === DESIGN-B-FOOTER-END === -->

If all three marker pairs appear exactly once, the header/footer/head
injection step is skipped; base/canonical/CSS fixes still run (they are
cheap no-ops when already correct).
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from bs4 import BeautifulSoup, Comment, NavigableString
except ImportError:
    sys.exit("beautifulsoup4 is required: pip install beautifulsoup4 lxml")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

SITE_ORIGIN = "https://dawidmillenium-design.github.io"
SITE_BASE   = "/VideoCameraHoliday"          # must start with /

FRAGMENT_PATH = ROOT / "templates" / "design-b-fragment.html"

EXCLUDE_DIRS = {
    "templates", "scripts", "node_modules", ".git", "__pycache__",
    "workspace", "data", "docs", "output", "generated-content",
    "city-generator",
}

# Markers used both to detect existing injections and to wrap new ones.
MARKER_HEAD_START    = " === DESIGN-B-HEAD-START === "
MARKER_HEAD_END      = " === DESIGN-B-HEAD-END === "
MARKER_HEADER_START  = " === DESIGN-B-HEADER-START === "
MARKER_HEADER_END    = " === DESIGN-B-HEADER-END === "
MARKER_FOOTER_START  = " === DESIGN-B-FOOTER-START === "
MARKER_FOOTER_END    = " === DESIGN-B-FOOTER-END === "

# Stylesheet path that the fragment expects. The injector enforces this.
DESIGN_B_CSS = f"{SITE_BASE}/assets/design-b.css"

# Substrings that uniquely identify the shared Design B <script> block.
SCRIPT_FINGERPRINTS = (
    "hvcDesignBLoaded",
    "hvc-cookie-consent",
    "drawerToggle",
)


# ---------------------------------------------------------------------------
# Fragment loading
# ---------------------------------------------------------------------------

def _load_fragment_text() -> str:
    """Read the fragment file if it exists, otherwise fail loudly."""
    if not FRAGMENT_PATH.exists():
        sys.exit(
            f"Missing fragment: {FRAGMENT_PATH}\n"
            f"Create it or restore it from git history before running this script."
        )
    return FRAGMENT_PATH.read_text(encoding="utf-8")


def _section(fragment_text: str, start_marker: str, end_marker: str) -> str:
    """Return the substring strictly between the two marker strings."""
    a = fragment_text.find(start_marker)
    b = fragment_text.find(end_marker)
    if a == -1 or b == -1 or b < a:
        sys.exit(f"Marker pair missing in fragment: {start_marker!r} / {end_marker!r}")
    return fragment_text[a + len(start_marker):b].strip()


def read_sections() -> dict[str, str]:
    text = _load_fragment_text()
    return {
        "head":   _section(text, f"<!--{MARKER_HEAD_START}-->",   f"<!--{MARKER_HEAD_END}-->"),
        "header": _section(text, f"<!--{MARKER_HEADER_START}-->", f"<!--{MARKER_HEADER_END}-->"),
        "footer": _section(text, f"<!--{MARKER_FOOTER_START}-->", f"<!--{MARKER_FOOTER_END}-->"),
    }


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _nodes_from_html(html: str) -> list:
    """Parse an HTML fragment and return its top-level nodes."""
    frag = BeautifulSoup(html, "html.parser")
    return list(frag.children)


def _append_nodes(target, nodes) -> None:
    for node in nodes:
        if hasattr(node, "extract"):
            target.append(node.extract())
        else:
            target.append(str(node))


def _insert_nodes(target, index: int, nodes) -> None:
    for offset, node in enumerate(nodes):
        if hasattr(node, "extract"):
            target.insert(index + offset, node.extract())
        else:
            target.insert(index + offset, str(node))


# ---------------------------------------------------------------------------
# Detection / idempotency
# ---------------------------------------------------------------------------

def _comment_count(soup: BeautifulSoup, marker: str) -> int:
    return sum(
        1
        for c in soup.find_all(string=lambda t: isinstance(t, Comment))
        if marker in str(c)
    )


def is_already_correct(soup: BeautifulSoup) -> bool:
    """True iff each Design B marker appears exactly once."""
    return (
        _comment_count(soup, MARKER_HEAD_START)   == 1
        and _comment_count(soup, MARKER_HEADER_START) == 1
        and _comment_count(soup, MARKER_FOOTER_START) == 1
    )


# ---------------------------------------------------------------------------
# Removal — strip any existing Design B content (from any previous run)
# ---------------------------------------------------------------------------

def remove_existing_design_b(soup: BeautifulSoup) -> int:
    """Remove every Design B header / drawer / footer / banner / script."""
    removed = 0

    # Headers
    for el in soup.find_all("header", class_="site-header"):
        el.decompose()
        removed += 1

    # Drawers
    for el in soup.find_all("aside", id="siteDrawer"):
        el.decompose()
        removed += 1

    # Backdrops
    for el in soup.find_all("div", id="drawerBackdrop"):
        el.decompose()
        removed += 1

    # Footers
    for el in soup.find_all("footer", class_="site-footer"):
        el.decompose()
        removed += 1

    # Cookie banners
    for el in soup.find_all("div", id="cookieBanner"):
        el.decompose()
        removed += 1

    # Design B <script> blocks
    for script in soup.find_all("script"):
        text = script.string or ""
        if any(fp in text for fp in SCRIPT_FINGERPRINTS):
            script.decompose()
            removed += 1

    # Stray marker comments (from a partial previous run)
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        if any(m in str(c) for m in (
            MARKER_HEAD_START, MARKER_HEAD_END,
            MARKER_HEADER_START, MARKER_HEADER_END,
            MARKER_FOOTER_START, MARKER_FOOTER_END,
        )):
            c.extract()
            removed += 1

    return removed


# ---------------------------------------------------------------------------
# Head hygiene — CSS, base, canonical
# ---------------------------------------------------------------------------

def fix_css_links(soup: BeautifulSoup) -> dict[str, int]:
    """Remove the broken /assets/design-b.css link and dedupe stylesheets."""
    stats = {"removed_bad": 0, "deduped": 0}

    # Remove the broken path variant
    for link in soup.find_all("link", rel="stylesheet", href="/assets/design-b.css"):
        link.decompose()
        stats["removed_bad"] += 1

    # Deduplicate by href
    seen = set()
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href")
        if href in seen:
            link.decompose()
            stats["deduped"] += 1
        else:
            seen.add(href)

    return stats


def ensure_base_tag(soup: BeautifulSoup) -> int:
    """Ensure exactly one <base href="/VideoCameraHoliday/"> in <head>."""
    if not soup.head:
        return 0

    desired = SITE_BASE + "/"
    bases = soup.head.find_all("base")

    if not bases:
        soup.head.insert(0, soup.new_tag("base", href=desired))
        return 1

    # Keep the first, correct it if needed, remove extras
    changed = 0
    if bases[0].get("href") != desired:
        bases[0]["href"] = desired
        changed = 1
    for extra in bases[1:]:
        extra.decompose()
        changed += 1
    return changed


def _canonical_url_for(file_path: Path) -> str:
    """Compute the deployed canonical URL for a source file."""
    rel = str(file_path.relative_to(ROOT)).replace("\\", "/")

    # index.html → directory form
    if rel == "index.html":
        rel = ""
    elif rel.endswith("/index.html"):
        rel = rel[: -len("index.html")]

    return f"{SITE_ORIGIN}{SITE_BASE}/{rel}"


def ensure_canonical(soup: BeautifulSoup, file_path: Path) -> int:
    """Ensure exactly one correct <link rel="canonical"> in <head>."""
    if not soup.head:
        return 0

    desired = _canonical_url_for(file_path)
    canonicals = soup.head.find_all("link", rel="canonical")

    if not canonicals:
        soup.head.append(soup.new_tag("link", rel="canonical", href=desired))
        return 1

    changed = 0
    if canonicals[0].get("href") != desired:
        canonicals[0]["href"] = desired
        changed = 1
    for extra in canonicals[1:]:
        extra.decompose()
        changed += 1
    return changed


# ---------------------------------------------------------------------------
# Injection
# ---------------------------------------------------------------------------

def inject_sections(soup: BeautifulSoup, sections: dict[str, str]) -> None:
    """Inject one clean copy of head/header/footer with marker comments."""
    if not soup.head or not soup.body:
        return

    # --- HEAD ---
    _append_nodes(soup.head, [Comment(MARKER_HEAD_START)])
    _append_nodes(soup.head, _nodes_from_html(sections["head"]))
    _append_nodes(soup.head, [Comment(MARKER_HEAD_END)])

    # --- HEADER (top of body, after leading whitespace / noscript) ---
    insert_idx = 0
    for i, node in enumerate(soup.body.contents):
        name = getattr(node, "name", None)
        if name in (None, "noscript"):
            continue
        insert_idx = i
        break

    header_nodes = [Comment(MARKER_HEADER_START)] \
                 + _nodes_from_html(sections["header"]) \
                 + [Comment(MARKER_HEADER_END)]
    _insert_nodes(soup.body, insert_idx, header_nodes)

    # --- FOOTER (bottom of body) ---
    _append_nodes(soup.body, [Comment(MARKER_FOOTER_START)])
    _append_nodes(soup.body, _nodes_from_html(sections["footer"]))
    _append_nodes(soup.body, [Comment(MARKER_FOOTER_END)])


# ---------------------------------------------------------------------------
# Per-file processing
# ---------------------------------------------------------------------------

def process_file(file_path: Path, sections: dict[str, str]) -> dict:
    try:
        html = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        html = file_path.read_text(encoding="latin-1")

    soup = BeautifulSoup(html, "lxml")

    if not soup.head or not soup.body:
        return {"status": "skip", "reason": "no <head> or <body>"}

    # Snapshot: are we already clean?
    was_correct = is_already_correct(soup)

    stats = {
        "removed_blocks": 0,
        "removed_bad_css": 0,
        "deduped_css": 0,
        "base_changes": 0,
        "canonical_changes": 0,
    }

    if was_correct:
        # Head/header/footer already good — only touch head hygiene.
        css = fix_css_links(soup)
        stats["removed_bad_css"] = css["removed_bad"]
        stats["deduped_css"]     = css["deduped"]
        stats["base_changes"]    = ensure_base_tag(soup)
        stats["canonical_changes"] = ensure_canonical(soup, file_path)
    else:
        # Full clean + re-inject.
        stats["removed_blocks"] = remove_existing_design_b(soup)
        css = fix_css_links(soup)
        stats["removed_bad_css"] = css["removed_bad"]
        stats["deduped_css"]     = css["deduped"]
        stats["base_changes"]    = ensure_base_tag(soup)
        stats["canonical_changes"] = ensure_canonical(soup, file_path)
        inject_sections(soup, sections)

    # Detect whether anything actually changed
    new_html = str(soup)
    if new_html == html:
        return {"status": "unchanged", **stats}

    file_path.write_text(new_html, encoding="utf-8")
    return {"status": "updated", **stats}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _iter_candidate_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*.html"):
        rel_parts = path.relative_to(ROOT).parts[:-1]
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        if path.name.endswith("_template.html"):
            continue
        files.append(path)
    return files


def main() -> int:
    sections = read_sections()
    print(f"📦 Loaded fragment sections: "
          f"head={len(sections['head'])}h  "
          f"header={len(sections['header'])}h  "
          f"footer={len(sections['footer'])}h")

    candidates = _iter_candidate_files()
    print(f"🔎 Found {len(candidates)} candidate HTML files\n")

    totals = {
        "updated": 0, "unchanged": 0, "skip": 0,
        "removed_blocks": 0, "removed_bad_css": 0, "deduped_css": 0,
        "base_changes": 0, "canonical_changes": 0,
    }

    for i, path in enumerate(candidates, 1):
        result = process_file(path, sections)
        status = result["status"]

        if status == "skip":
            totals["skip"] += 1
            continue

        if status == "unchanged":
            totals["unchanged"] += 1
            continue

        totals["updated"] += 1
        for key in ("removed_blocks", "removed_bad_css", "deduped_css",
                    "base_changes", "canonical_changes"):
            totals[key] += result.get(key, 0)

        print(f"  ✓ {path.relative_to(ROOT)}  "
              f"(removed={result['removed_blocks']}  "
              f"badcss={result['removed_bad_css']}  "
              f"dedup={result['deduped_css']}  "
              f"base={result['base_changes']}  "
              f"canon={result['canonical_changes']})")

        if i % 100 == 0:
            print(f"  ...{i}/{len(candidates)}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Files updated   : {totals['updated']}")
    print(f"  Files unchanged : {totals['unchanged']}")
    print(f"  Files skipped   : {totals['skip']}")
    print(f"  Design-B blocks removed : {totals['removed_blocks']}")
    print(f"  Broken CSS links removed: {totals['removed_bad_css']}")
    print(f"  Duplicate CSS links removed: {totals['deduped_css']}")
    print(f"  <base> tags fixed : {totals['base_changes']}")
    print(f"  Canonical links fixed: {totals['canonical_changes']}")
    print("=" * 60)

    # Never fail CI on "nothing to do"
    return 0


if __name__ == "__main__":
    sys.exit(main())
