#!/usr/bin/env python3
"""
Smart Internal Linking & Orphan Fixer (FIXED)
Recursively scans ALL folders (including language dirs) and correctly
normalizes URLs so links match page paths.
"""

import os
import json
import re
from pathlib import Path
from openai import OpenAI
from bs4 import BeautifulSoup
from collections import defaultdict

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

MAX_LINKS = int(os.getenv('MAX_LINKS', '3'))
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'
REPO_ROOT = Path(".")

# Folders we never want to scan
EXCLUDE_DIRS = {".git", "node_modules", ".github", "dist", "build", ".venv", "__pycache__", "scripts", "assets", "css", "js", "images"}


def canonical_key(raw: str) -> str:
    """
    Convert any path or href into a canonical page key.
    Examples:
      /VideoCameraHoliday/reviews/foo.html       -> reviews/foo.html
      https://x.com/VideoCameraHoliday/reviews/foo -> reviews/foo.html
      ../reviews/foo.html                        -> reviews/foo.html
      /reviews/foo                               -> reviews/foo.html
      reviews/foo/                               -> reviews/foo/index.html
    """
    if not raw:
        return ""
    s = raw.strip()
    # strip query/fragment
    s = s.split("?")[0].split("#")[0]
    # strip protocol + domain
    s = re.sub(r"^https?://[^/]+", "", s)
    # strip known base paths
    s = re.sub(r"^/(dawidmillenium-design/)?VideoCameraHoliday/?", "", s)
    # collapse leading ../ and ./
    while s.startswith("../") or s.startswith("./"):
        s = s[3:] if s.startswith("../") else s[2:]
    # remove leading slash
    s = s.lstrip("/")
    # add .html if it's a page URL without extension
    if s and not s.endswith(".html") and not s.endswith("/"):
        s += ".html"
    # directory -> index.html
    if s.endswith("/"):
        s += "index.html"
    return s.lower()


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts & EXCLUDE_DIRS)


def scan_all_pages():
    """Scan ALL HTML files anywhere in the repo."""
    pages = {}
    for html_file in REPO_ROOT.rglob("*.html"):
        if should_skip(html_file):
            continue
        # skip obvious non-content files
        if html_file.name in {"404.html", "googlef5307df871e4912d.html"}:
            continue

        rel = html_file.as_posix()
        key = canonical_key(rel)

        try:
            with open(html_file, "r", encoding="utf-8", errors="replace") as f:
                soup = BeautifulSoup(f.read(), "lxml")
        except Exception as e:
            print(f"   skip {rel}: {e}")
            continue

        text = soup.get_text(separator=" ", strip=True)[:1500]
        links = [a["href"] for a in soup.find_all("a", href=True)]
        title_tag = soup.find("title")

        pages[key] = {
            "file_path": rel,
            "title": title_tag.text.strip() if title_tag else html_file.stem,
            "text": text,
            "outgoing": links,
            "incoming_count": 0,
        }
    return pages


def calculate_incoming_links(pages):
    counts = defaultdict(int)
    for _, data in pages.items():
        for raw_link in data["outgoing"]:
            key = canonical_key(raw_link)
            if key in pages and key != canonical_key(data["file_path"]):
                counts[key] += 1
    for key, data in pages.items():
        data["incoming_count"] = counts.get(key, 0)
    return pages


def find_orphans(pages):
    return {p: d for p, d in pages.items() if d["incoming_count"] < 2}


def suggest_source_pages(orphan_key, orphan_data, all_pages):
    potential_sources = [
        p for p, d in all_pages.items()
        if d["incoming_count"] >= 3
    ]
    if not potential_sources:
        potential_sources = list(all_pages.keys())[:20]

    # give DeepSeek the human-readable titles, not just paths
    source_catalog = [
        {"url": p, "title": all_pages[p]["title"]}
        for p in potential_sources[:40]
    ]

    prompt = f"""You are an SEO expert. Choose up to {MAX_LINKS} high-authority source pages that should link to this ORPHAN page.

ORPHAN PAGE
- URL: {orphan_key}
- Title: {orphan_data['title']}
- Preview: {orphan_data['text'][:400]}

CANDIDATE SOURCE PAGES (pick only topically relevant ones):
{json.dumps(source_catalog, indent=2)}

Return ONLY a JSON array. Each item:
{{"source_url": "<one of the source_url values above>", "anchor_text": "<3-5 word natural anchor>"}}
If nothing is relevant, return [].
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip())
    except Exception as e:
        print(f"   API error: {e}")
        return []


def inject_link(source_key, target_key, anchor_text, all_pages):
    source_path = Path(all_pages[source_key]["file_path"])
    if not source_path.exists():
        return False
    try:
        with open(source_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "lxml")

        # Build target href: always site-root absolute, with base path
        target_path = all_pages[target_key]["file_path"]  # e.g. reviews/foo.html
        target_href = f"/VideoCameraHoliday/{target_path}"

        # skip if link already exists
        existing = [a.get("href", "") for a in soup.find_all("a", href=True)]
        if any(canonical_key(h) == target_key for h in existing):
            return False

        main = soup.find("main") or soup.find("body")
        if not main:
            return False

        related = soup.find("div", class_="auto-generated-links")
        if not related:
            related = soup.new_tag("div", attrs={
                "class": "auto-generated-links",
                "style": "margin-top:2rem;font-size:0.9em;color:#666;"
            })
            h4 = soup.new_tag("h4")
            h4.string = "🔗 Related Guides"
            related.append(h4)
            ul = soup.new_tag("ul")
            related.append(ul)
            main.append(related)
        else:
            ul = related.find("ul")
            if not ul:
                ul = soup.new_tag("ul")
                related.append(ul)

        li = soup.new_tag("li")
        a = soup.new_tag("a", href=target_href)
        a.string = anchor_text
        li.append(a)
        ul.append(li)

        if not DRY_RUN:
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(str(soup))
        return True
    except Exception as e:
        print(f"   inject error on {source_path}: {e}")
        return False


def main():
    print("🔗 Smart Internal Linking (FIXED)")
    print("=" * 60)
    if DRY_RUN:
        print("⚠️  DRY RUN MODE — no files will be changed")

    print("1. Scanning ALL pages recursively...")
    pages = scan_all_pages()
    print(f"   Indexed {len(pages)} pages")

    print("2. Calculating incoming links...")
    pages = calculate_incoming_links(pages)
    orphans = find_orphans(pages)
    print(f"   Orphans (<2 incoming): {len(orphans)}")

    # sort by fewest incoming links so worst offenders go first
    orphans_sorted = sorted(orphans.items(), key=lambda kv: kv[1]["incoming_count"])

    total_added = 0
    modified_files = set()

    for i, (orphan_key, orphan_data) in enumerate(orphans_sorted[:50]):
        print(f"\n[{i+1}/{min(50, len(orphans_sorted))}] {orphan_key}")
        suggestions = suggest_source_pages(orphan_key, orphan_data, pages)
        for sug in suggestions:
            source_key = canonical_key(sug.get("source_url", ""))
            anchor = (sug.get("anchor_text") or "").strip()
            if source_key in pages and anchor:
                if inject_link(source_key, orphan_key, anchor, pages):
                    total_added += 1
                    modified_files.add(pages[source_key]["file_path"])
                    print(f"   ✅ {source_key} -> {orphan_key}")

    summary = {
        "total_pages": len(pages),
        "total_links": sum(d["incoming_count"] for d in pages.values()),
        "orphans_found": len(orphans),
        "links_added": total_added,
        "modified_files": sorted(modified_files),
    }
    with open("linking-summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 60)
    print(f"✅ Done. Added {total_added} links across {len(modified_files)} files.")


if __name__ == "__main__":
    main()
