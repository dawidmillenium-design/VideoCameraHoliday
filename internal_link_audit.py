#!/usr/bin/env python3
"""Audit internal links for the indexable pages listed in sitemap.xml."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday/"
BASE_PATH = "/VideoCameraHoliday/"
ROOT = Path(__file__).resolve().parent
SITEMAP = ROOT / "sitemap.xml"
EXCLUDED_DIRS = {
    ".git", ".github", "node_modules", "__pycache__", ".venv", "venv",
    "_site", "dist", "build", "workspace", "city-generator",
}


def load_sitemap_urls() -> list[str]:
    tree = ET.parse(SITEMAP)
    root = tree.getroot()
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [
        element.text.strip()
        for element in root.findall(".//sm:loc", namespace)
        if element.text and element.text.strip().startswith(BASE_URL)
    ]


def url_to_key(url: str) -> str | None:
    parsed = urlparse(url)
    expected = urlparse(BASE_URL)
    if parsed.netloc and parsed.netloc.lower() != expected.netloc.lower():
        return None

    path = unquote(parsed.path)
    if path in {"/VideoCameraHoliday", "/VideoCameraHoliday/"}:
        return "index.html"
    if not path.startswith(BASE_PATH):
        return None

    key = path[len(BASE_PATH):].lstrip("/")
    if not key:
        return "index.html"
    if key.endswith("/"):
        key += "index.html"
    return key


def source_url(key: str) -> str:
    return BASE_URL if key == "index.html" else urljoin(BASE_URL, key)


def resolve_internal_href(href: str, source_key: str) -> str | None:
    href = (href or "").strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    return url_to_key(urljoin(source_url(source_key), href))


def all_deployable_files() -> set[str]:
    files: set[str] = set()
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        files.add(relative.as_posix())
    return files


def extract_page(key: str) -> tuple[list[tuple[str, str]], str | None]:
    path = ROOT / key
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    links: list[tuple[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        target = resolve_internal_href(anchor.get("href", ""), key)
        if target:
            anchor_text = " ".join(anchor.get_text(" ", strip=True).split())
            links.append((target, anchor_text))

    canonical = None
    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value)
    if canonical_tag and canonical_tag.get("href"):
        canonical = resolve_internal_href(canonical_tag["href"], key)
    return links, canonical


def write_markdown(report: dict) -> None:
    lines = [
        "## 📊 SEO & Internal Link Audit Report",
        "",
        f"- Audit date: {report['audit_date']}",
        f"- Sitemap pages: {report['sitemap_urls']}",
        f"- Parsed pages: {report['parsed_pages']}",
        f"- Broken internal links: {len(report['broken_links'])}",
        f"- Canonical mismatches: {len(report['canonical_mismatches'])}",
        f"- Orphan pages: {len(report['orphans'])}",
        f"- Pages with fewer than 3 incoming sources: {len(report['low_authority_pages'])}",
        f"- Linked HTML pages absent from sitemap: {len(report['missing_from_sitemap'])}",
        f"- Average internal anchors per sitemap page: {report['average_links_per_page']:.1f}",
        "",
    ]

    if report["broken_links"]:
        lines.extend(["### Broken internal links", ""])
        for item in report["broken_links"][:100]:
            lines.append(f"- `{item['source']}` → `{item['target']}`")
        lines.append("")

    if report["canonical_mismatches"]:
        lines.extend(["### Canonical mismatches", ""])
        for item in report["canonical_mismatches"]:
            lines.append(
                f"- `{item['source']}` declares `{item['canonical'] or 'missing/invalid'}`"
            )
        lines.append("")

    if report["orphans"]:
        lines.extend(["### Orphan pages", ""])
        lines.extend(f"- `{page}`" for page in report["orphans"])
        lines.append("")

    lines.append(
        "The workflow fails when a broken internal link or canonical mismatch is found."
    )
    (ROOT / "audit-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    sitemap_urls = load_sitemap_urls()
    sitemap_keys = [url_to_key(url) for url in sitemap_urls]
    sitemap_keys = [key for key in sitemap_keys if key]
    sitemap_set = set(sitemap_keys)
    existing = all_deployable_files()

    incoming_sources: dict[str, set[str]] = defaultdict(set)
    broken: set[tuple[str, str]] = set()
    linked_not_in_sitemap: set[str] = set()
    canonical_mismatches: list[dict[str, str | None]] = []
    parsed_pages = 0
    internal_anchor_count = 0

    for source_key in sitemap_keys:
        if source_key not in existing:
            broken.add(("sitemap.xml", source_key))
            continue

        parsed_pages += 1
        links, canonical = extract_page(source_key)
        internal_anchor_count += len(links)

        if canonical != source_key:
            canonical_mismatches.append(
                {"source": source_key, "canonical": canonical}
            )

        for target_key, _anchor in links:
            if target_key not in existing:
                broken.add((source_key, target_key))
                continue
            if target_key in sitemap_set and target_key != source_key:
                incoming_sources[target_key].add(source_key)
            elif target_key.endswith((".html", "/index.html")):
                linked_not_in_sitemap.add(target_key)

    orphans = sorted(
        key for key in sitemap_keys
        if key != "index.html" and not incoming_sources.get(key)
    )
    low_authority = sorted(
        (
            {"path": key, "incoming_count": len(incoming_sources.get(key, set()))}
            for key in sitemap_keys
            if key != "index.html" and len(incoming_sources.get(key, set())) < 3
        ),
        key=lambda item: (item["incoming_count"], item["path"]),
    )

    report = {
        "audit_date": datetime.now(timezone.utc).date().isoformat(),
        "sitemap_urls": len(sitemap_keys),
        "parsed_pages": parsed_pages,
        "broken_links": [
            {"source": source, "target": target}
            for source, target in sorted(broken)
        ],
        "canonical_mismatches": canonical_mismatches,
        "orphans": orphans,
        "low_authority_pages": low_authority,
        "missing_from_sitemap": sorted(linked_not_in_sitemap),
        "average_links_per_page": (
            internal_anchor_count / parsed_pages if parsed_pages else 0
        ),
    }

    (ROOT / "link-audit-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_markdown(report)

    print(json.dumps({
        "sitemap_pages": report["sitemap_urls"],
        "parsed_pages": report["parsed_pages"],
        "broken_links": len(report["broken_links"]),
        "canonical_mismatches": len(report["canonical_mismatches"]),
        "orphans": len(report["orphans"]),
        "low_authority_pages": len(report["low_authority_pages"]),
        "missing_from_sitemap": len(report["missing_from_sitemap"]),
        "average_links_per_page": round(report["average_links_per_page"], 1),
    }, indent=2))

    return 1 if report["broken_links"] or report["canonical_mismatches"] else 0


if __name__ == "__main__":
    sys.exit(main())
