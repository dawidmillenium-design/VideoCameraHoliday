#!/usr/bin/env python3
"""
Inject breadcrumbs + article-hero into every article page.

================================================================
FOLDERS THAT ARE ALWAYS SKIPPED (double protection)
================================================================

  Layer 1 — EXCLUDE_DIRS:
    These folders are pruned from os.walk() before descent.
    Scripts, templates, node_modules, generated content, etc.

  Layer 2 — Top-level allowlist:
    Even if a folder survives Layer 1, the script only processes
    files whose FIRST path segment is on the allowlist:
      - English categories: guides, reviews, destinations, ...
      - Language folders:   de-DE, es-ES, fr-FR, it-IT, ja-JP, ...

    This means _posts/, output/, templates/, scripts/, node_modules/,
    generated-content/, and every other folder are NEVER touched —
    they're not on the allowlist.

================================================================
USAGE
================================================================
  python scripts/inject_hero_breadcrumbs.py              # apply
  python scripts/inject_hero_breadcrumbs.py --dry-run    # preview
  python scripts/inject_hero_breadcrumbs.py --target=de-DE  # one folder
"""

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DRY_RUN = "--dry-run" in sys.argv

# Optional --target=<folder>
TARGET = None
for arg in sys.argv[1:]:
    if arg.startswith("--target="):
        TARGET = arg.split("=", 1)[1].strip("/")


# ============================================================
# LAYER 1 — Directories to prune during os.walk()
# ============================================================
# These are never descended into. If a folder appears here,
# os.walk() removes it from its list of subdirectories, so
# the script doesn't even see the files inside it.
#
# This is the primary exclusion mechanism.
# ============================================================

EXCLUDE_DIRS = {
    # Version control / package managers
    ".git",
    "node_modules",         # ← EXPLICITLY EXCLUDED
    ".github",
    "vendor",

    # Build / dev / cache
    "__pycache__",
    ".cache",
    ".venv",
    "venv",
    "dist",
    "build",
    "coverage",

    # Content pipelines and internal tooling
    "scripts",              # ← EXPLICITLY EXCLUDED (script's own home)
    "templates",            # ← EXPLICITLY EXCLUDED (design-b.html lives here)
    "generated-content",    # ← EXPLICITLY EXCLUDED
    "output",               # ← EXPLICITLY EXCLUDED
    "_posts",               # ← EXPLICITLY EXCLUDED (Jekyll posts)

    # Internal / non-public folders
    "workspace",
    "docs",
    "data",
    "content",
    "media",
    "assets",
    "interviews",
    "game",
    "city-generator",
    "city-interview-preview",
    "spanish SEO",
    "data/content_brief",
}


# ============================================================
# LAYER 2 — Top-level allowlist
# ============================================================
# Only files whose FIRST path segment (relative to repo root)
# is one of these keys will ever be processed.
#
# Everything else — including _posts/, output/, templates/,
# scripts/, node_modules/, generated-content/ — is skipped.
# ============================================================

# English category folders → 3-level breadcrumb
CATEGORY_LABELS = {
    "guides": "Guides",
    "reviews": "Reviews",
    "destinations": "Destinations",
    "how-to": "How-To",
    "comparisons": "Comparisons",
    "editing": "Editing",
    "accessories": "Accessories",
    "city-through-the-lens": "City Through the Lens",
}

# Language folders → 2-level breadcrumb with translated "Home"
LANGUAGE_LABELS = {
    "de-DE": "Startseite",
    "de":    "Startseite",
    "es-ES": "Inicio",
    "es":    "Inicio",
    "fr-FR": "Accueil",
    "it-IT": "Home",
    "ja-JP": "ホーム",
    "jp":    "ホーム",
    "ko-KR": "홈",
    "pl-PL": "Start",
    "pt-br": "Início",
    "th-TH": "หน้าแรก",
    "zh-CN": "首页",
}

# Language codes for the `lang` attribute on the hero
LANGUAGE_CODES = {
    "de-DE": "de",
    "de":    "de",
    "es-ES": "es",
    "es":    "es",
    "fr-FR": "fr",
    "it-IT": "it",
    "ja-JP": "ja",
    "jp":    "ja",
    "ko-KR": "ko",
    "pl-PL": "pl",
    "pt-br": "pt-BR",
    "th-TH": "th",
    "zh-CN": "zh-CN",
}


# ============================================================
# Files to skip by exact name
# ============================================================
# Hub index pages, templates, legal pages — these don't need
# an article hero (they have their own hub design).
# ============================================================

EXCLUDE_FILES = {
    "index.html",
    "index2.html",
    "index3.html",
    "hub.html",
    "404.html",
    "contact.html",
    "privacy.html",
    "terms.html",
    "start-here.html",
    "camera-tests.html",
    "comparison_template.html",
    "comparisons_original.html",
    "MEGA_MENU_INTEGRATION_EXAMPLE.html",
}


# ============================================================
# Helpers
# ============================================================

def slug_to_title(slug: str) -> str:
    """'best-holiday-video-cameras-2026' → 'Best Holiday Video Cameras 2026'."""
    words = re.split(r"[-_]", slug)
    out = []
    for w in words:
        if not w:
            continue
        if w.isupper() and len(w) <= 5:
            out.append(w)
        else:
            out.append(w.capitalize())
    return " ".join(out)


def find_h1(html: str):
    """Return (offset, inner_html, length) of first <h1> inside <body>."""
    body_match = re.search(
        r"<body[^>]*>(.*?)</body>",
        html, re.DOTALL | re.IGNORECASE
    )
    if not body_match:
        return None, None, None
    body = body_match.group(1)
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.DOTALL | re.IGNORECASE)
    if not h1_match:
        return None, None, None
    offset = body_match.start(1) + h1_match.start()
    return offset, h1_match.group(1).strip(), h1_match.end() - h1_match.start()


def derive_title_from_meta(html: str, slug: str) -> str:
    """Fallback: use <title> stripped of branding, or the slug."""
    title_match = re.search(
        r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE
    )
    if title_match:
        raw = title_match.group(1).strip()
        raw = re.sub(r"^\s*[^\w]+\s*", "", raw)
        for sep in [" – ", " — ", " | ", " · ", " - "]:
            raw = raw.split(sep)[0]
        raw = raw.replace("Holiday Video Camera", "").strip(" -–—|·")
        if raw:
            return raw
    return slug_to_title(slug)


def xml_escape(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))


def build_breadcrumbs(items) -> str:
    """items: list of (label, href_or_None, is_current)."""
    lis = []
    for label, href, current in items:
        if current:
            lis.append(f'        <li aria-current="page">{xml_escape(label)}</li>')
        else:
            lis.append(f'        <li><a href="{href}">{xml_escape(label)}</a></li>')
    joined = "\n".join(lis)
    return (
        '\n<nav class="breadcrumbs" aria-label="Breadcrumb">\n'
        '    <ol>\n'
        f'{joined}\n'
        '    </ol>\n'
        '</nav>\n'
    )


def build_hero(page_title_html: str, lang: str = "en") -> str:
    lang_attr = f' lang="{lang}"' if lang and lang != "en" else ""
    return (
        f'\n<section class="article-hero"{lang_attr}>\n'
        f'    <h1>{page_title_html}</h1>\n'
        '</section>\n'
    )


# ============================================================
# Processing
# ============================================================

def process_file(file_path: Path) -> bool:
    """Return True if the file was modified."""

    # ---- LAYER 2 GUARD ----
    # Only allow files inside an approved top-level folder.
    rel = file_path.relative_to(REPO_ROOT)
    parts = rel.parts
    if len(parts) < 2:
        return False

    top_folder = parts[0]
    is_category = top_folder in CATEGORY_LABELS
    is_language = top_folder in LANGUAGE_LABELS

    if not (is_category or is_language):
        # Not a category folder, not a language folder → skip.
        # This alone protects _posts/, output/, templates/, scripts/,
        # node_modules/, generated-content/ and anything else.
        return False

    # ---- Read file ----
    try:
        html = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False

    # ---- Idempotency check ----
    if 'class="breadcrumbs"' in html:
        return False

    # ---- Find insertion anchor ----
    article_match = re.search(
        r"(<article\b[^>]*>|<main\b[^>]*>)",
        html, re.DOTALL | re.IGNORECASE
    )
    if not article_match:
        return False

    # ---- Build breadcrumb items ----
    lang_code = "en"
    breadcrumb_items = []

    if is_category:
        # 3-level breadcrumb: Home › Category › Page
        breadcrumb_items.append(("Home", "/VideoCameraHoliday/", False))
        breadcrumb_items.append(
            (CATEGORY_LABELS[top_folder],
             f"/VideoCameraHoliday/{top_folder}/",
             False)
        )
    else:  # is_language
        # 2-level breadcrumb: <localized Home> › Page
        lang_code = LANGUAGE_CODES.get(top_folder, "")
        breadcrumb_items.append(
            (LANGUAGE_LABELS[top_folder],
             f"/VideoCameraHoliday/{top_folder}/",
             False)
        )

    # ---- Extract page title ----
    h1_offset, h1_inner, h1_len = find_h1(html)
    if h1_inner:
        page_title_html = re.sub(
            r'<a[^>]*>(.*?)</a>', r"\1",
            h1_inner, flags=re.DOTALL
        ).strip()
    else:
        page_title_html = derive_title_from_meta(html, file_path.stem)

    plain_title = re.sub(r"<[^>]+>", "", page_title_html).strip()
    breadcrumb_items.append((plain_title, None, True))

    # ---- Assemble insertion ----
    breadcrumbs_html = build_breadcrumbs(breadcrumb_items)
    hero_html = build_hero(page_title_html, lang_code)
    insertion = breadcrumbs_html + hero_html + "\n"

    insert_at = article_match.start()
    html_new = html[:insert_at] + insertion + html[insert_at:]

    # ---- Remove the original H1 (now duplicated) ----
    if h1_offset is not None:
        adjusted_start = h1_offset + len(insertion)
        adjusted_end = adjusted_start + h1_len
        html_new = html_new[:adjusted_start] + html_new[adjusted_end:]
        html_new = re.sub(r"\n{3,}", "\n\n", html_new)

    if not DRY_RUN:
        file_path.write_text(html_new, encoding="utf-8")
    return True


def main():
    target_msg = f" [target: {TARGET}]" if TARGET else ""
    mode = "DRY RUN" if DRY_RUN else "APPLY"
    print(f"🚀 {mode} — Injecting breadcrumbs + hero{target_msg}\n")

    processed = 0
    updated = 0
    skipped = 0
    per_folder = {}

    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        # ---- LAYER 1 — prune excluded directories ----
        # This prevents os.walk() from descending into them at all.
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

        rel_dir = Path(dirpath).relative_to(REPO_ROOT)
        if not rel_dir.parts:
            continue

        top = rel_dir.parts[0]

        # ---- LAYER 2 — only descend into approved top-level folders ----
        if top not in CATEGORY_LABELS and top not in LANGUAGE_LABELS:
            # Not a recognized category/language folder → skip entirely
            dirnames[:] = []
            continue

        # Optional --target filter
        if TARGET and top != TARGET:
            dirnames[:] = []
            continue

        for filename in filenames:
            if not filename.endswith(".html"):
                continue
            if filename in EXCLUDE_FILES:
                continue

            file_path = Path(dirpath) / filename
            processed += 1

            try:
                if process_file(file_path):
                    updated += 1
                    per_folder[top] = per_folder.get(top, 0) + 1
                    print(f"  ✅ {file_path.relative_to(REPO_ROOT)}")
                else:
                    skipped += 1
            except Exception as e:
                skipped += 1
                print(f"  ❌ {file_path.relative_to(REPO_ROOT)} — {e}")

    print(f"\n📊 Scanned: {processed} | Updated: {updated} | Skipped: {skipped}")
    if per_folder:
        print("\n📁 Breakdown by folder:")
        for folder in sorted(per_folder):
            print(f"   {folder:24s} {per_folder[folder]:>4} files")
    if DRY_RUN:
        print("\n💡 Run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
