#!/usr/bin/env python3
"""
Two-part remediation for the breadcrumb+hero injection:

  1. Fix the broken H1 / breadcrumb-current text ("Best s 2026" bug)
     by re-deriving the correct title from <title> with a suffix-only
     brand strip.

  2. Inject a BreadcrumbList JSON-LD <script> into <head> if one is
     not already present, using the visible breadcrumb trail as the
     source of truth. URLs are absolute (SITE_ORIGIN + path).

Only touches files that ALREADY contain class="breadcrumbs".
Files without the injection are skipped.

Default mode is DRY-RUN. Pass --apply to write.
"""

from __future__ import annotations

import argparse
import html as html_module
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SITE_ORIGIN = "https://dawidmillenium-design.github.io"
SITE_BASE = "/VideoCameraHoliday"

EXCLUDE_DIRS = {
    "templates", "scripts", "node_modules", ".git", "__pycache__",
    "workspace", "data", "docs", "output", "generated-content",
    "city-generator",
}

# ---------- Title cleaning (the fix for "Best s 2026") ----------

EMOJI_LEAD = re.compile(r"^\s*[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]+\s*")

# Only strip the brand when it appears as a trailing segment after a separator.
BRAND_SUFFIX = re.compile(
    r"\s*[|·•\-–—]\s*Holiday\s+Video\s+Camera\s*$",
    re.IGNORECASE,
)


def clean_title(raw: str) -> str:
    """Turn a <title> into a human H1. Only strips trailing brand."""
    t = html_module.unescape(raw).strip()
    t = EMOJI_LEAD.sub("", t)
    t = BRAND_SUFFIX.sub("", t)
    return t.strip()


# ---------- Breadcrumb nav extraction ----------

# Current-page <li> inside a breadcrumbs nav
CURRENT_LI_RE = re.compile(
    r'(<li[^>]*aria-current=["\']page["\'][^>]*>)(.*?)(</li>)',
    re.DOTALL | re.IGNORECASE,
)

# Hero H1 inside <section class="article-hero"> (first h1 after the section tag)
HERO_H1_RE = re.compile(
    r'(<section[^>]*\bclass=["\'][^"\']*\barticle-hero\b[^"\']*["\'][^>]*>'
    r'.*?<h1[^>]*>)(.*?)(</h1>)',
    re.DOTALL | re.IGNORECASE,
)

# All <li> children of the breadcrumbs nav (for building JSON-LD)
BREADCRUMB_NAV_RE = re.compile(
    r'<nav[^>]*\bclass=["\'][^"\']*\bbreadcrumbs\b[^"\']*["\'][^>]*>(.*?)</nav>',
    re.DOTALL | re.IGNORECASE,
)

BREADCRUMB_ITEM_RE = re.compile(
    r'<li[^>]*>\s*(?:<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>|([^<]+))\s*</li>',
    re.DOTALL | re.IGNORECASE,
)

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.DOTALL | re.IGNORECASE)

JSONLD_MARKER = "BreadcrumbList"


# ---------- Helpers ----------

def abs_url(href: str) -> str:
    """Turn a relative href into an absolute URL for JSON-LD."""
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith(SITE_BASE):
        return SITE_ORIGIN + href
    if href.startswith("/"):
        return SITE_ORIGIN + href
    # relative — this shouldn't happen in the breadcrumbs, but handle it
    return f"{SITE_ORIGIN}{SITE_BASE}/{href.lstrip('./')}"


def derive_canonical_url(path: Path) -> str:
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    if rel == "index.html":
        rel = ""
    elif rel.endswith("/index.html"):
        rel = rel[: -len("index.html")]
    return f"{SITE_ORIGIN}{SITE_BASE}/{rel}"


def build_breadcrumb_jsonld(html: str, page_url: str) -> str | None:
    """Return a <script type="application/ld+json"> string, or None."""
    nav_match = BREADCRUMB_NAV_RE.search(html)
    if not nav_match:
        return None
    nav_html = nav_match.group(1)

    items = []
    pos = 1
    for m in BREADCRUMB_ITEM_RE.finditer(nav_html):
        href, text_a, text_b = m.group(1), m.group(2), m.group(3)
        text = (text_a or text_b or "").strip()
        text = html_module.unescape(text).strip()
        if not text:
            continue
        url = abs_url(href) if href else page_url
        items.append({
            "@type": "ListItem",
            "position": pos,
            "name": text,
            "item": url,
        })
        pos += 1

    if not items:
        return None

    payload = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{body}\n</script>'


# ---------- Per-file processing ----------

def process(path: Path, apply: bool) -> dict:
    original = path.read_text(encoding="utf-8", errors="replace")

    # Skip files without the injection
    if 'class="breadcrumbs"' not in original:
        return {"status": "skip", "reason": "no breadcrumbs"}

    html = original
    changes = {"title_fixed": 0, "h1_fixed": 0, "jsonld_added": 0}

    # --- Derive correct title from <title> ---
    title_match = TITLE_RE.search(html)
    if not title_match:
        return {"status": "skip", "reason": "no <title>"}
    correct = clean_title(title_match.group(1))
    if not correct:
        return {"status": "skip", "reason": "empty title"}

    # --- Fix breadcrumb current page <li> ---
    def fix_current(m: re.Match) -> str:
        opening, content, closing = m.group(1), m.group(2), m.group(3)
        # Only fix if the visible text looks broken (short fragment)
        plain = re.sub(r"<[^>]+>", "", content).strip()
        if plain and (len(plain) < 12 or re.search(r"\bs\s+\d{4}\b", plain)):
            changes["title_fixed"] += 1
            # Preserve any wrapping tags, replace only the text
            new_inner = re.sub(r"[^<>]+", "", content).strip() or ""
            if "<a" in content:
                # keep the anchor, replace its text
                new_content = re.sub(
                    r"(<a[^>]*>)(.*?)(</a>)",
                    lambda mm: mm.group(1) + correct + mm.group(3),
                    content,
                    flags=re.DOTALL,
                )
            else:
                new_content = correct
            return opening + new_content + closing
        return m.group(0)

    html = CURRENT_LI_RE.sub(fix_current, html)

    # --- Fix hero H1 ---
    def fix_h1(m: re.Match) -> str:
        opening, content, closing = m.group(1), m.group(2), m.group(3)
        plain = re.sub(r"<[^>]+>", "", content).strip()
        if plain and (len(plain) < 12 or re.search(r"\bs\s+\d{4}\b", plain)):
            changes["h1_fixed"] += 1
            return opening + correct + closing
        return m.group(0)

    html = HERO_H1_RE.sub(fix_h1, html)

    # --- Add BreadcrumbList JSON-LD ---
    if JSONLD_MARKER not in html:
        page_url = derive_canonical_url(path)
        script = build_breadcrumb_jsonld(html, page_url)
        if script:
            # Insert before </head>
            html = re.sub(
                r"</head>",
                script + "\n</head>",
                html,
                count=1,
                flags=re.IGNORECASE,
            )
            changes["jsonld_added"] += 1

    if html == original:
        return {"status": "unchanged"}

    if apply:
        path.write_text(html, encoding="utf-8")
    return {"status": "updated", **changes}


# ---------- Main ----------

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
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    files = iter_candidates()
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"Mode: {mode}")
    print(f"Scanning {len(files)} files...\n")

    totals = {"updated": 0, "unchanged": 0, "skip": 0,
              "title_fixed": 0, "h1_fixed": 0, "jsonld_added": 0}
    samples = []

    for path in files:
        result = process(path, args.apply)
        totals[result["status"]] = totals.get(result["status"], 0) + 1
        for k in ("title_fixed", "h1_fixed", "jsonld_added"):
            totals[k] += result.get(k, 0)

        if result["status"] == "updated":
            if args.verbose and len(samples) < 10:
                samples.append((path.relative_to(ROOT),
                                {k: v for k, v in result.items()
                                 if k not in ("status",)}))
            totals["updated"] += 1

    if args.verbose and samples:
        print("Samples (first 10 updated files):")
        for rel, ch in samples:
            print(f"  {rel}  {ch}")
        print()

    print("=" * 60)
    print(f"  Files updated   : {totals['updated']}")
    print(f"  Files unchanged : {totals['unchanged']}")
    print(f"  Files skipped   : {totals['skip']}")
    print(f"  Titles fixed    : {totals['title_fixed']}")
    print(f"  H1s fixed       : {totals['h1_fixed']}")
    print(f"  JSON-LD added   : {totals['jsonld_added']}")
    print(f"  Mode            : {mode}")
    if not args.apply and totals["updated"] > 0:
        print("\n  Re-run with --apply to write changes.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
