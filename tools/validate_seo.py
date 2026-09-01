#!/usr/bin/env python3
"""Validate the static site's high-priority technical SEO invariants."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday/"

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonicals = []
        self.descriptions = []
        self.h1_count = 0
        self.lang = None
        self.title_parts = []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.lang = attrs.get("lang")
        elif tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "meta" and attrs.get("name", "").lower() == "description":
            self.descriptions.append(attrs.get("content", "").strip())
        elif tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonicals.append(attrs.get("href", "").strip())

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)


def expected_url(path):
    relative = path.relative_to(ROOT).as_posix()
    if relative == "index.html":
        relative = ""
    elif relative.endswith("/index.html"):
        relative = relative[:-10]
    return BASE_URL + relative


def main():
    errors = []
    canonical_pages = set()
    canonical_titles = {}
    for path in sorted(ROOT.rglob("*.html")):
        parser = PageParser()
        parser.feed(path.read_text(encoding="utf-8"))
        rel = path.relative_to(ROOT)
        title = "".join(parser.title_parts).strip()
        if not parser.lang:
            errors.append(f"{rel}: missing html lang")
        if not title:
            errors.append(f"{rel}: missing title")
        if len(parser.descriptions) != 1 or not parser.descriptions[0]:
            errors.append(f"{rel}: expected one non-empty meta description")
        if len(parser.canonicals) != 1:
            errors.append(f"{rel}: expected one canonical, found {len(parser.canonicals)}")
        elif not parser.canonicals[0].startswith(BASE_URL):
            errors.append(f"{rel}: canonical is outside the production site")
        elif parser.canonicals[0] == expected_url(path):
            canonical_pages.add(parser.canonicals[0])
            if title in canonical_titles:
                errors.append(f"{rel}: title duplicates {canonical_titles[title]}")
            else:
                canonical_titles[title] = rel
        if parser.h1_count != 1:
            errors.append(f"{rel}: expected one h1, found {parser.h1_count}")

    sitemap = ET.parse(ROOT / "sitemap.xml")
    sitemap_urls = [node.text.strip() for node in sitemap.findall(".//{*}loc")]
    duplicate_urls = [url for url, count in Counter(sitemap_urls).items() if count > 1]
    if duplicate_urls:
        errors.append("sitemap: duplicate URLs: " + ", ".join(duplicate_urls))
    if set(sitemap_urls) != canonical_pages:
        missing = canonical_pages - set(sitemap_urls)
        extra = set(sitemap_urls) - canonical_pages
        if missing:
            errors.append("sitemap: missing canonical pages: " + ", ".join(sorted(missing)))
        if extra:
            errors.append("sitemap: contains non-canonical pages: " + ", ".join(sorted(extra)))

    if errors:
        print("Technical SEO validation failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"Technical SEO validation passed for {len(list(ROOT.rglob("*.html")))} HTML pages and {len(sitemap_urls)} canonical sitemap URLs.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
