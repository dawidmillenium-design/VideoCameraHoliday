#!/usr/bin/env python3
"""
ai_knowledge_base.py
Recursively scans the repository (including all language folders) and builds
ai-knowledge-base.json with structured page metadata and keyword aggregates.

Usage:
    python scripts/ai_knowledge_base.py \
        --root . \
        --output ai-knowledge-base.json \
        --exclude .git node_modules .github dist build .venv __pycache__
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Common stopwords so keyword extraction isn't polluted
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "you",
    "are", "was", "were", "has", "have", "had", "but", "not", "all", "any",
    "can", "will", "our", "out", "into", "about", "over", "than", "then",
    "they", "their", "them", "its", "it's", "a", "an", "of", "in", "on",
    "to", "is", "as", "at", "by", "or", "be", "do", "so", "if", "we",
    "i", "he", "she", "his", "her", "my", "me", "us", "no", "yes",
    # Polish / German / French / Spanish common words
    "der", "die", "das", "und", "ein", "eine", "ist", "mit", "für", "auf",
    "les", "des", "une", "est", "pour", "avec", "dans", "sur",
    "los", "las", "una", "por", "con", "para", "del",
    "nie", "jest", "się", "oraz", "przez", "dla", "jak", "tak",
}

# ---------------------------------------------------------------------------
# HTML parsing
# ---------------------------------------------------------------------------

class PageParser(HTMLParser):
    """Extract title, meta description, h1, h2, h3, and text from HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: str = ""
        self.description: str = ""
        self.canonical: str = ""
        self.h1: list[str] = []
        self.h2: list[str] = []
        self.h3: list[str] = []
        self.text_chunks: list[str] = []

        self._current_tag: str | None = None
        self._buffer: list[str] = []
        self._in_title = False
        self._skip_depth = 0  # inside <script> / <style> / <noscript>

    # -- helpers ------------------------------------------------------------
    def _flush(self) -> str:
        text = " ".join(self._buffer).strip()
        text = re.sub(r"\s+", " ", text)
        self._buffer.clear()
        return text

    # -- HTMLParser hooks ---------------------------------------------------
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k.lower(): (v or "") for k, v in attrs}

        if tag in ("script", "style", "noscript"):
            self._skip_depth += 1
            return

        if tag == "title":
            self._in_title = True
            self._buffer.clear()
            return

        if tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            content = attrs_dict.get("content", "").strip()
            if name == "description" and content:
                self.description = content
            elif prop == "og:description" and content and not self.description:
                self.description = content
            return

        if tag == "link":
            rel = attrs_dict.get("rel", "").lower()
            if rel == "canonical":
                self.canonical = attrs_dict.get("href", "").strip()
            return

        if tag in ("h1", "h2", "h3"):
            self._current_tag = tag
            self._buffer.clear()

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip_depth = max(0, self._skip_depth - 1)
            return

        if tag == "title":
            self.title = self._flush() or self.title
            self._in_title = False
            return

        if tag in ("h1", "h2", "h3") and self._current_tag == tag:
            text = self._flush()
            if text:
                {"h1": self.h1, "h2": self.h2, "h3": self.h3}[tag].append(text)
            self._current_tag = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        stripped = data.strip()
        if not stripped:
            return
        if self._in_title or self._current_tag:
            self._buffer.append(stripped)
        else:
            self.text_chunks.append(stripped)


def parse_html(path: Path) -> dict[str, Any] | None:
    """Parse a single HTML file. Returns None if unreadable."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logging.warning("Cannot read %s: %s", path, exc)
        return None

    # Skip files that clearly aren't real pages
    if len(raw) < 50:
        return None

    parser = PageParser()
    try:
        parser.feed(raw)
        parser.close()
    except Exception as exc:  # noqa: BLE001
        logging.warning("Parse error in %s: %s", path, exc)
        return None

    return {
        "title": parser.title,
        "description": parser.description,
        "canonical": parser.canonical,
        "h1": parser.h1,
        "h2": parser.h2,
        "h3": parser.h3,
        "text": " ".join(parser.text_chunks),
    }


# ---------------------------------------------------------------------------
# Keyword extraction
# ---------------------------------------------------------------------------

WORD_RE = re.compile(r"[A-Za-zÀ-ÿĄąĆćĘęŁłŃńÓóŚśŹźŻż]{3,}")


def extract_keywords(text: str, top_n: int = 15) -> list[str]:
    words = [w.lower() for w in WORD_RE.findall(text)]
    words = [w for w in words if w not in STOPWORDS]
    counts = Counter(words)
    return [w for w, _ in counts.most_common(top_n)]


# ---------------------------------------------------------------------------
# Language detection (UPDATED FOR STEP 2)
# ---------------------------------------------------------------------------

def detect_language(rel_path: Path) -> str:
    """
    Infer standard language code from the first folder.
    Normalizes variants like de-DE, de, ja-JP, jp to a single standard code.
    """
    if not rel_path.parts:
        return "en"
    
    first_part = rel_path.parts[0].lower()
    
    # Split by hyphen to get the base language (e.g., "de-de" -> "de")
    base_lang = first_part.split('-')[0]
    
    # Special case for 'jp' which is a common misnomer for 'ja'
    if base_lang == 'jp':
        return 'ja'
        
    return base_lang


def page_slug(rel_path: Path) -> str:
    """Turn es-ES/guias/foo.html into es-ES/guias/foo."""
    return str(rel_path.with_suffix("")).replace("\\", "/")


# ---------------------------------------------------------------------------
# Main scanner
# ---------------------------------------------------------------------------

def scan(root: Path, excludes: set[str]) -> dict[str, Any]:
    pages: list[dict[str, Any]] = []
    all_keywords: Counter[str] = Counter()
    titles_seen: Counter[str] = Counter()
    descriptions_missing = 0
    h1_missing = 0
    by_language: Counter[str] = Counter()

    html_files = [
        p for p in root.rglob("*.html")
        if not any(part in excludes for part in p.relative_to(root).parts)
    ]
    html_files.sort()

    logging.info("Found %d HTML files to scan", len(html_files))

    for path in html_files:
        rel = path.relative_to(root)
        data = parse_html(path)
        if data is None:
            continue

        lang = detect_language(rel)
        by_language[lang] += 1

        if not data["description"]:
            descriptions_missing += 1
        if not data["h1"]:
            h1_missing += 1

        titles_seen[data["title"].strip()] += 1

        combined = " ".join(
            [data["title"], data["description"], *data["h1"],
             *data["h2"], *data["h3"], data["text"]]
        )
        kws = extract_keywords(combined)
        all_keywords.update(kws)

        pages.append({
            "url": page_slug(rel),
            "path": str(rel).replace("\\", "/"),
            "language": lang,
            "title": data["title"],
            "description": data["description"],
            "canonical": data["canonical"],
            "h1": data["h1"],
            "h2": data["h2"],
            "h3": data["h3"],
            "keywords": kws,
            "word_count": len(data["text"].split()),
        })

    duplicate_titles = {t: c for t, c in titles_seen.items() if c > 1 and t}

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root.resolve()),
        "totals": {
            "html_files_found": len(html_files),
            "pages_indexed": len(pages),
            "by_language": dict(by_language.most_common()),
            "missing_meta_description": descriptions_missing,
            "missing_h1": h1_missing,
            "duplicate_titles": duplicate_titles,
        },
        "pages": pages,
        "keywords": [k for k, _ in all_keywords.most_common(100)],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build ai-knowledge-base.json recursively.")
    p.add_argument("--root", default=".", help="Repo root to scan (default: .)")
    p.add_argument("--output", default="ai-knowledge-base.json", help="Output JSON path")
    p.add_argument(
        "--exclude",
        nargs="*",
        default=[".git", "node_modules", ".github", "dist", "build", ".venv", "__pycache__"],
        help="Folder names to skip",
    )
    p.add_argument("--verbose", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    root = Path(args.root).resolve()
    if not root.is_dir():
        logging.error("Root is not a directory: %s", root)
        return 2

    result = scan(root, excludes=set(args.exclude))

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    logging.info(
        "Wrote %s — %d pages indexed across %d languages",
        out,
        result["totals"]["pages_indexed"],
        len(result["totals"]["by_language"]),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
