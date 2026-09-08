#!/usr/bin/env python3
"""Validate sitemap pages, internal anchors, and canonical URLs before deploy."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urldefrag, urljoin, urlparse


DEFAULT_BASE = "https://dawidmillenium-design.github.io/VideoCameraHoliday/"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.ids: set[str] = set()
        self.canonicals: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        if tag == "a" and values.get("name"):
            self.ids.add(values["name"])
        if tag == "a" and values.get("href") is not None:
            self.hrefs.append(values["href"].strip())
        if tag == "link" and "canonical" in values.get("rel", "").lower() and values.get("href"):
            self.canonicals.append(values["href"].strip())


def load_page(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return parser


def file_for_url(root: Path, base: str, url: str) -> Path | None:
    base_parts = urlparse(base)
    parts = urlparse(url)
    if parts.netloc != base_parts.netloc or not parts.path.startswith(base_parts.path):
        return None
    rel = unquote(parts.path[len(base_parts.path):])
    if not rel or rel.endswith("/"):
        return root / rel / "index.html"
    return root / rel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--sitemap", default="sitemap.xml")
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--report", default="link-audit-report.json")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    base = args.base.rstrip("/") + "/"
    sitemap_text = (root / args.sitemap).read_text(encoding="utf-8")
    sitemap_urls = sorted(set(re.findall(r"<loc>\s*([^<]+?)\s*</loc>", sitemap_text)))

    problems: list[dict] = []
    parsed_pages: dict[str, PageParser] = {}
    link_sources: dict[str, set[str]] = defaultdict(set)
    fragment_sources: dict[tuple[str, str], set[str]] = defaultdict(set)

    for page_url in sitemap_urls:
        page_file = file_for_url(root, base, page_url)
        if page_file is None or not page_file.is_file():
            problems.append({"type": "missing_sitemap_file", "url": page_url})
            continue
        parser = load_page(page_file)
        parsed_pages[page_url] = parser

        if len(parser.canonicals) != 1:
            problems.append({
                "type": "canonical_count",
                "source": page_url,
                "count": len(parser.canonicals),
                "values": parser.canonicals,
            })
        elif urldefrag(urljoin(page_url, parser.canonicals[0]))[0] != urldefrag(page_url)[0]:
            problems.append({
                "type": "canonical_mismatch",
                "source": page_url,
                "canonical": parser.canonicals[0],
            })

        for raw_href in parser.hrefs:
            if not raw_href or raw_href.startswith(("mailto:", "tel:", "javascript:", "data:")):
                continue
            absolute = urljoin(page_url, raw_href)
            target, fragment = urldefrag(absolute)
            link_sources[target].add(page_url)
            if fragment:
                fragment_sources[(target, fragment)].add(page_url)

    base_host = urlparse(base).netloc
    for target, sources in sorted(link_sources.items()):
        parsed = urlparse(target)
        if parsed.scheme not in ("http", "https") or parsed.netloc != base_host:
            continue
        target_file = file_for_url(root, base, target)
        if target_file is None:
            problems.append({"type": "missing_base_path", "target": target, "sources": sorted(sources)})
        elif not target_file.is_file():
            problems.append({"type": "missing_internal_target", "target": target, "sources": sorted(sources)})

    parser_cache = dict(parsed_pages)
    for (target, fragment), sources in sorted(fragment_sources.items()):
        if urlparse(target).netloc != base_host:
            continue
        target_file = file_for_url(root, base, target)
        if target_file is None or not target_file.is_file():
            continue
        parser = parser_cache.get(target)
        if parser is None:
            parser = load_page(target_file)
            parser_cache[target] = parser
        if fragment not in parser.ids:
            problems.append({"type": "missing_fragment", "target": target + "#" + fragment, "sources": sorted(sources)})

    summary = defaultdict(int)
    for problem in problems:
        summary[problem["type"]] += 1
    report = {
        "base": base,
        "sitemap_pages": len(sitemap_urls),
        "parsed_pages": len(parsed_pages),
        "unique_link_targets": len(link_sources),
        "problem_count": len(problems),
        "summary": dict(sorted(summary.items())),
        "problems": problems,
    }
    (root / args.report).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Checked {len(parsed_pages)}/{len(sitemap_urls)} sitemap pages and {len(link_sources)} unique link targets.")
    if problems:
        print(f"Found {len(problems)} problem(s): {dict(sorted(summary.items()))}", file=sys.stderr)
        return 1
    print("No broken internal links, fragments, sitemap files, or canonical URLs found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
