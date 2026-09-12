#!/usr/bin/env python3
"""
Generate sitemap.xml for VideoCameraHoliday.
Scans all HTML files, excludes templates/junk, adds lastmod + priority.
Adds hreflang alternates for translated article versions.
"""

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

REPO_ROOT = Path(__file__).parent.parent
SITEMAP_PATH = REPO_ROOT / "sitemap.xml"
BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday"

# Folders we never include in the sitemap
EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", "workspace",
    "generated-content", "data", "media", "assets", "scripts",
    "templates", "city-generator", "city-interview-preview",
    ".github", "node_modules", "interviews", "game",
    "spanish SEO", "data/content_brief",
}

# Files we never include
EXCLUDE_FILES = {
    "404.html",
    "comparison_template.html",
    "comparisons_original.html",
    "MEGA_MENU_INTEGRATION_EXAMPLE.html",
    "mega-menu-footer.html",
    "mega-menu-nav.html",
    "test.html.txt",
    "googlef5307df871e4912d.html",
    "BingSiteAuth.xml",
}

# Folders where hreflang applies (same article translated across languages)
LANGUAGE_DIRS = [
    "de-DE", "de", "es-ES", "es", "fr-FR", "it-IT",
    "ja-JP", "jp", "ko-KR", "pl-PL", "pt-br", "th-TH", "zh-CN"
]

# Priority rules by path signature
PRIORITY_RULES = [
    (r"^$", "1.0"),                                    # homepage
    (r"^index\.html$", "1.0"),
    (r"^(reviews|guides|destinations|how-to|comparisons|editing|accessories)/$", "0.9"),  # hubs
    (r"^(de-DE|es-ES|fr-FR|it-IT|ja-JP|ko-KR|pl-PL|pt-br|th-TH|zh-CN)/$", "0.9"),          # language homes
    (r"^city-through-the-lens/$", "0.8"),
    (r"^about/$", "0.7"),
    (r"^(reviews|guides|destinations|how-to|comparisons)/[^/]+\.html$", "0.8"),
    (r"^(de-DE|es-ES|fr-FR|it-IT|ja-JP|ko-KR|pl-PL|pt-br|th-TH|zh-CN)/[^/]+\.html$", "0.7"),
    (r"^city-through-the-lens/[^/]+\.html$", "0.6"),
    (r"^city-generator/", "0.4"),
]

# Changefreq rules
CHANGEFREQ_RULES = [
    (r"^$|^index\.html$", "weekly"),
    (r"^(reviews|guides|destinations|how-to)/$", "weekly"),
    (r"^(reviews|guides|destinations|how-to)/", "monthly"),
    (r".*", "monthly"),
]


def should_exclude(path: Path) -> bool:
    """Return True if this file should NOT be in the sitemap."""
    rel = path.relative_to(REPO_ROOT)
    parts = rel.parts
    # Exclude if any parent directory is on the blocklist
    for part in parts[:-1]:
        if part in EXCLUDE_DIRS:
            return True
    # Exclude specific files
    if path.name in EXCLUDE_FILES:
        return True
    # Skip any file inside a `_diff`, `_original`, or `.bak` pattern
    if re.search(r"(_diff|_original|_old|\.bak|\.tmp)", path.name, re.IGNORECASE):
        return True
    return False


def get_lastmod(path: Path) -> str:
    """Get the last modification date from git, or file mtime as fallback."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(path)],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            # Format: 2026-09-11T15:30:00+00:00 → keep date part only
            return result.stdout.strip().split("T")[0]
    except Exception:
        pass
    # Fallback to filesystem mtime
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")


def rel_url(path: Path) -> str:
    """Convert file path to URL path relative to BASE_URL."""
    rel = path.relative_to(REPO_ROOT).as_posix()
    # index.html → /folder/ (or / at root)
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        rel = rel[:-len("index.html")]
    return "/" + rel


def get_priority(url_path: str) -> str:
    for pattern, priority in PRIORITY_RULES:
        if re.match(pattern, url_path.lstrip("/")):
            return priority
    return "0.5"


def get_changefreq(url_path: str) -> str:
    for pattern, freq in CHANGEFREQ_RULES:
        if re.match(pattern, url_path.lstrip("/")):
            return freq
    return "monthly"


def build_hreflang_map(all_urls: list) -> dict:
    """
    Group URLs by their relative article name across languages.
    Returns dict: { 'filename_or_empty': { 'de-DE': url, 'fr-FR': url, ... } }
    """
    groups = {}
    for url in all_urls:
        # Strip leading /
        u = url.lstrip("/")
        # Detect language folder
        parts = u.split("/") if u else []
        lang = "x-default"
        if parts and parts[0] in LANGUAGE_DIRS:
            lang = parts[0]
            parts = parts[1:]
        # Key: remaining path (or empty for homepage)
        key = "/".join(parts) if parts else ""
        # Normalize: strip trailing /
        key = key.rstrip("/")
        groups.setdefault(key, {})[lang] = url
    # Convert to full URLs and add x-default
    result = {}
    for key, langs in groups.items():
        full = {}
        for lang, url in langs.items():
            full[lang] = BASE_URL + url
        if "de-DE" in full and "x-default" not in full:
            full["x-default"] = full["de-DE"]
        # Only include groups with at least 2 languages
        if len(full) >= 2:
            result[key] = full
    return result


def escape_url(url: str) -> str:
    """Escape special chars in URL while preserving path structure."""
    return quote(url, safe="/:?=&#%")


def xml_escape(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))


def generate_sitemap():
    print("🚀 Generating sitemap.xml...")

    # 1. Collect all HTML files
    html_files = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            if not filename.endswith(".html"):
                continue
            path = Path(dirpath) / filename
            if should_exclude(path):
                continue
            html_files.append(path)

    print(f"   Found {len(html_files)} HTML files")

    # 2. Build URL list
    urls = []
    for path in sorted(html_files):
        url_path = rel_url(path)
        full_url = BASE_URL + url_path
        urls.append({
            "loc": full_url,
            "lastmod": get_lastmod(path),
            "changefreq": get_changefreq(url_path),
            "priority": get_priority(url_path),
        })

    # 3. Sort: homepage first, then hubs, then alphabetical
    urls.sort(key=lambda u: (
        0 if u["loc"] == BASE_URL + "/" else
        1 if len(u["loc"].rstrip("/").split("/")) <= 5 else
        2,
        u["loc"]
    ))

    # 4. Build hreflang map
    all_urls = [rel_url(p) for p in html_files]
    hreflang_map = build_hreflang_map(all_urls)
    print(f"   Found {len(hreflang_map)} multilingual article groups")

    # 5. Write XML
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
        '',
    ]

    for entry in urls:
        lines.append("  <url>")
        lines.append(f'    <loc>{xml_escape(entry["loc"])}</loc>')
        lines.append(f'    <lastmod>{entry["lastmod"]}</lastmod>')
        lines.append(f'    <changefreq>{entry["changefreq"]}</changefreq>')
        lines.append(f'    <priority>{entry["priority"]}</priority>')

        # Add hreflang alternates if this URL belongs to a group
        rel = entry["loc"].replace(BASE_URL, "/")
        # Extract key (strip lang folder)
        u = rel.lstrip("/")
        parts = u.split("/") if u else []
        if parts and parts[0] in LANGUAGE_DIRS:
            parts = parts[1:]
        key = "/".join(parts).rstrip("/") if parts else ""

        if key in hreflang_map:
            for lang, alt_url in sorted(hreflang_map[key].items()):
                lines.append(
                    f'    <xhtml:link rel="alternate" hreflang="{lang}" '
                    f'href="{xml_escape(alt_url)}"/>'
                )

        lines.append("  </url>")
        lines.append("")

    lines.append("</urlset>")

    SITEMAP_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"✅ Wrote {len(urls)} URLs to {SITEMAP_PATH}")
    print(f"   File size: {SITEMAP_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    generate_sitemap()
