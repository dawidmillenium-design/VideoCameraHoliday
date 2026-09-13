#!/usr/bin/env python3
"""
Expand thin-content HTML pages using the DeepSeek API.

Safety Features:
  - Accurately counts words inside the content container (matching auditor).
  - Refuses to process files already >= threshold.
  - Rejects AI output if it results in fewer words than the original.
  - Preserves existing <img> tags by prepending them to the new content.
  - Idempotent: skips files already marked with data-deepseek-expanded.
"""

import argparse
import csv
import os
import re
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup
from openai import OpenAI

# Files/directories to NEVER process
EXCLUDED_PATHS = {
    'templates/',
    'template/',
    '_templates/',
    'partials/',
    'includes/',
    'layouts/',
}

def should_exclude_file(file_path: Path) -> bool:
    """Check if file should be excluded from processing."""
    path_str = str(file_path).lower()
    return any(excluded in path_str for excluded in EXCLUDED_PATHS)
  

# ---------- Config ----------

DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEFAULT_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
PROMPT_PATH = Path(__file__).parent / "content_prompt.txt"
MARKER_ATTR = "data-deepseek-expanded"

# Priority order for finding the main content container
CONTENT_SELECTORS = [
    ("main", {}),
    ("article", {}),
    ("div", {"class": "content"}),
    ("div", {"class": "article-content"}),
    ("div", {"class": "post-content"}),
    ("div", {"class": "entry-content"}),
    ("div", {"id": "content"}),
    ("div", {"class": "main-content"}),
    ("section", {"class": "content"}),
]

BANNED_OUTPUT_RE = re.compile(r"<\s*(script|style|iframe|object|embed)\b", re.IGNORECASE)


# ---------- Helpers ----------

def find_content_container(soup: BeautifulSoup):
    for tag, attrs in CONTENT_SELECTORS:
        el = soup.find(tag, attrs) if attrs else soup.find(tag)
        if el:
            return el
    return soup.find("body")


def detect_language(soup: BeautifulSoup) -> str:
    html = soup.find("html")
    if html and html.get("lang"):
        return html["lang"]
    meta = soup.find("meta", attrs={"http-equiv": re.compile("content-language", re.I)})
    if meta and meta.get("content"):
        return meta["content"]
    return "en"


def is_already_expanded(soup: BeautifulSoup, container) -> bool:
    if container and container.get(MARKER_ATTR):
        return True
    return soup.find(string=re.compile(r"expanded-by:deepseek")) is not None


def count_words(text: str) -> int:
    """Accurate word count matching standard SEO auditors."""
    return len(text.split())


# ---------- DeepSeek call ----------

def build_prompt(template: str, title: str, rel_path: str,
                 existing_text: str, target_words: int, language: str) -> str:
    return (
        template
        .replace("{title}", title)
        .replace("{path}", rel_path)
        .replace("{existing_content}", existing_text)
        .replace("{target_words}", str(target_words))
        .replace("{language}", language)
    )


def call_deepseek(client: OpenAI, model: str, prompt: str, max_retries: int = 3) -> str:
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You output only clean HTML fragments. No prose, no markdown fences, no explanations."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=4000,
            )
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            last_exc = exc
            wait = 2 ** attempt
            print(f"  [retry {attempt}/{max_retries}] {exc} — sleeping {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"DeepSeek call failed after {max_retries} attempts: {last_exc}")


def sanitize_html_fragment(raw: str) -> str:
    """Remove markdown fences and reject obviously dangerous output."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    if BANNED_OUTPUT_RE.search(raw):
        raise ValueError("DeepSeek output contained forbidden tags (script/style/iframe)")
    return raw


# ---------- Per-file processing ----------

def process_file(client: OpenAI, model: str, prompt_template: str,
                 file_path: Path, base_dir: Path, target_words: int,
                 threshold: int, dry_run: bool) -> bool:
    rel = file_path.relative_to(base_dir)
    try:
        html = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        html = file_path.read_text(encoding="latin-1")

    soup = BeautifulSoup(html, "lxml")
    container = find_content_container(soup)

    if container is None:
        print(f"  [skip] {rel}: no content container found")
        return False

    if is_already_expanded(soup, container):
        print(f"  [skip] {rel}: already expanded")
        return False

    # 1. ACCURATE WORD COUNT (matches auditor)
    existing_text = container.get_text(separator=" ", strip=True)
    existing_word_count = count_words(existing_text)

    # 2. HARD THRESHOLD GATE
    if existing_word_count >= threshold:
        print(f"  [skip] {rel}: already has {existing_word_count} words (≥ {threshold} threshold)")
        return False

    if not existing_text:
        print(f"  [skip] {rel}: container has no text")
        return False

    title = (soup.title.get_text(strip=True) if soup.title else rel.name)
    language = detect_language(soup)

    prompt = build_prompt(
        prompt_template, title, str(rel), existing_text, target_words, language
    )

    if dry_run:
        print(f"\n===== DRY RUN: {rel} =====")
        print(f"  Current words: {existing_word_count} | Target: {target_words}")
        print(f"  Prompt length: {len(prompt)} chars")
        return False

    print(f"  → calling DeepSeek for {rel} ({existing_word_count} → {target_words} words)")
    raw = call_deepseek(client, model, prompt)
    fragment = sanitize_html_fragment(raw)

    # 3. REJECT IF WORD COUNT DECREASED
    new_soup = BeautifulSoup(fragment, "lxml")
    new_text = new_soup.get_text(separator=" ", strip=True)
    new_word_count = count_words(new_text)

    if new_word_count < existing_word_count:
        print(f"  [REJECT] {rel}: AI output reduced content ({existing_word_count} → {new_word_count} words). Skipping.")
        return False

    if new_word_count > target_words * 3:
        print(f"  [warn] {rel}: DeepSeek returned {new_word_count} words (way over target). Truncating.")
        # Simple truncation fallback if it goes wildly over
        fragment = fragment[: len(fragment) * target_words * 3 // new_word_count]
        new_soup = BeautifulSoup(fragment, "lxml")

    # 4. PRESERVE EXISTING IMAGES (The "Footgun" Fix)
    original_images = container.find_all('img')
    
    # Clear the container and rebuild it safely
    container.clear()
    
    # Prepend original images so they aren't lost
    for img in original_images:
        container.append(img)
        container.append(soup.new_tag('br')) # Add slight spacing

    # Append the new AI-generated content
    for child in list(new_soup.children):
        container.append(child)

    # Mark as expanded so re-runs are idempotent
    container[MARKER_ATTR] = "1"

    # Add an HTML comment marker near the top of the file
    marker_comment = soup.new_string("<!-- expanded-by:deepseek v1 -->\n")
    if soup.head:
        soup.head.insert(0, marker_comment)

    file_path.write_text(str(soup), encoding="utf-8")
    print(f"  ✓ {rel}: {existing_word_count} → {new_word_count} words")
    return True


# ---------- Main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="scripts/thin_content_report.csv")
    ap.add_argument("--batch-size", type=int, default=5, help="Max pages to process this run")
    ap.add_argument("--threshold", type=int, default=500, help="Only expand pages below this word count")
    ap.add_argument("--target-words", type=int, default=800)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--root", default=None, help="Repo root (default: parent of scripts/)")
    args = ap.parse_args()

    base_dir = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent

    csv_path = base_dir / args.csv
    if not csv_path.exists():
        sys.exit(f"CSV not found: {csv_path}\nRun scripts/audit_thin_content.py first.")

    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")

    # Read CSV, filter, sort worst-first
    rows = []
    with csv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                wc = int(row["word_count"])
            except (KeyError, ValueError):
                continue
            if wc < args.threshold:
                rows.append((wc, row["file_path"]))
    rows.sort()

    batch = rows[: args.batch_size]
    print(f"Found {len(rows)} candidates below {args.threshold} words.")
    print(f"Processing worst {len(batch)} this run.\n")

    if args.dry_run:
        client = None
    else:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            sys.exit("DEEPSEEK_API_KEY env var is not set")
        client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)

    modified = 0
    for _, rel_path in batch:
        file_path = base_dir / rel_path
        if not file_path.exists():
            print(f"  [skip] {rel_path}: file missing")
            continue
        try:
            if process_file(client, DEFAULT_MODEL, prompt_template, file_path, base_dir, 
                            args.target_words, args.threshold, args.dry_run):
                modified += 1
        except Exception as exc:
            print(f"  [error] {rel_path}: {exc}", file=sys.stderr)

    print(f"\nDone. Modified {modified}/{len(batch)} files.")


if __name__ == "__main__":
    main()
