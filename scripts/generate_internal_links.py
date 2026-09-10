#!/usr/bin/env python3
"""
Smart Internal Linking Engine (FIXED)
Injects relevant internal links into newly generated articles.
Now scans the ENTIRE repo and normalizes URLs correctly.
"""

import os
import json
import re
from pathlib import Path
from openai import OpenAI
from bs4 import BeautifulSoup

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

EXCLUDE_DIRS = {".git", "node_modules", ".github", "dist", "build", ".venv", "__pycache__", "scripts", "assets", "css", "js", "images"}


def canonical_key(raw: str) -> str:
    if not raw:
        return ""
    s = raw.strip().split("?")[0].split("#")[0]
    s = re.sub(r"^https?://[^/]+", "", s)
    s = re.sub(r"^/(dawidmillenium-design/)?VideoCameraHoliday/?", "", s)
    while s.startswith("../") or s.startswith("./"):
        s = s[3:] if s.startswith("../") else s[2:]
    s = s.lstrip("/")
    if s and not s.endswith(".html") and not s.endswith("/"):
        s += ".html"
    if s.endswith("/"):
        s += "index.html"
    return s.lower()


def should_skip(path: Path) -> bool:
    return bool(set(path.parts) & EXCLUDE_DIRS)


def get_existing_pages() -> list:
    pages = []
    for html_file in Path(".").rglob("*.html"):
        if should_skip(html_file):
            continue
        if html_file.name.startswith("index"):
            continue
        try:
            with open(html_file, "r", encoding="utf-8", errors="replace") as f:
                soup = BeautifulSoup(f.read(), "lxml")
            title = soup.find("title")
            h1 = soup.find("h1")
            pages.append({
                "path": html_file.as_posix(),
                "url": f"/VideoCameraHoliday/{html_file.as_posix()}",
                "title": title.text.strip() if title else "",
                "h1": h1.text.strip() if h1 else "",
            })
        except Exception:
            continue
    return pages


def suggest_links(article_content: str, existing_pages: list) -> list:
    pages_sample = existing_pages[:60]
    prompt = f"""Suggest 3-5 highly relevant internal links for this new article.

NEW ARTICLE (excerpt):
{article_content[:1500]}

EXISTING PAGES:
{json.dumps(pages_sample, indent=2)}

Return ONLY a JSON array of:
[{{"anchor_text": "3-6 word anchor", "url": "<exact url from list>", "reason": "why relevant"}}]
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.choices[0].message.content.strip()
        for fence in ("```json", "```"):
            if content.startswith(fence):
                content = content[len(fence):]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip())
    except Exception as e:
        print(f"   API error: {e}")
        return []


def inject_links(filepath: str, links: list):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "lxml")

        main = soup.find("main") or soup.find("body")
        if not main:
            return

        existing = {canonical_key(a.get("href", "")) for a in soup.find_all("a", href=True)}

        section = soup.new_tag("div", attrs={
            "class": "related-articles",
            "style": "margin-top:3rem;padding:2rem;background:#f8f9fa;border-radius:8px;",
        })
        h2 = soup.new_tag("h2")
        h2.string = "📚 Related Articles"
        section.append(h2)

        ul = soup.new_tag("ul", attrs={"style": "list-style:none;padding:0;"})
        added = 0
        for link in links[:5]:
            if canonical_key(link["url"]) in existing:
                continue
            li = soup.new_tag("li", attrs={"style": "margin-bottom:0.5rem;"})
            a = soup.new_tag("a", href=link["url"])
            a.string = link["anchor_text"]
            a["title"] = link.get("reason", "")
            a["style"] = "color:#0066cc;text-decoration:none;"
            li.append(a)
            ul.append(li)
            added += 1

        if added == 0:
            return

        section.append(ul)
        main.append(section)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(str(soup))
    except Exception as e:
        print(f"   inject error: {e}")


def main():
    print("🔗 Smart Internal Linking Engine (FIXED)")
    print("=" * 60)

    existing_pages = get_existing_pages()
    print(f"   Found {len(existing_pages)} existing pages")

    # Scan every HTML file that isn't already in the index? No —
    # we only want to process NEW articles. Change this path to whichever
    # folder your article generator writes to now.
    TARGET_DIR = Path("workspace")  # <-- change if you generate elsewhere

    if not TARGET_DIR.exists():
        print(f"❌ {TARGET_DIR}/ not found — nothing to do.")
        return

    total = 0
    for html_file in TARGET_DIR.rglob("*.html"):
        print(f"\n📄 {html_file}")
        try:
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()
            links = suggest_links(content, existing_pages)
            if links:
                inject_links(str(html_file), links)
                print(f"   ✅ {len(links)} link(s) added")
                total += len(links)
            else:
                print("   ⚠️ No suggestions")
        except Exception as e:
            print(f"   ❌ {e}")

    print("\n" + "=" * 60)
    print(f"🎉 Done. Total links added: {total}")


if __name__ == "__main__":
    main()
