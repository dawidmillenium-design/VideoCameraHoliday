#!/usr/bin/env python3
"""
Fix the last 15 files with multi-line orphan CSS.

The earlier restore_html.py removed single-line orphan CSS rules.
These 15 files have multi-line CSS rules sitting outside any <style> tag.
This script WRAPS them in <style>...</style> instead of deleting them.

Safety:
  - Default is dry-run: prints what would be wrapped, writes nothing.
  - Pass --apply to actually write.
  - Refuses to wrap anything that looks like JavaScript.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {
    "templates", "scripts", "node_modules", ".git", "__pycache__",
    "workspace", "data", "docs", "output",
}

# A CSS rule: selector line ending with `{`, then properties, then `}`
CSS_BLOCK_RE = re.compile(
    r"(?<![<\w])"                         # not immediately after '<' or word char
    r"([.#a-zA-Z][\w\s,>.:#()\[\]&+~-]*?)"  # selector
    r"\s*\{([^{}]*?)\}",                    # body
    re.DOTALL,
)

# Signs of JavaScript — if any of these appear at the start of a block,
# we refuse to wrap it.
JS_SIGNALS = re.compile(
    r"^\s*(\(function|function\s*\(|var\s+|let\s+|const\s+|"
    r"window\.|document\.|if\s*\(|for\s*\(|return\s+)",
    re.MULTILINE,
)


def find_orphan_blocks(segment: str) -> list[tuple[int, int, str]]:
    """Return (start, end, text) for CSS blocks in a segment outside <style>."""
    out = []
    for m in CSS_BLOCK_RE.finditer(segment):
        # Skip if the block contains JS signals
        if JS_SIGNALS.search(m.group(0)):
            continue
        # Skip trivial one-character matches
        if len(m.group(0).strip()) < 10:
            continue
        out.append((m.start(), m.end(), m.group(0)))
    return out


def wrap_orphan_css(html: str) -> tuple[str, int, list[str]]:
    """Wrap orphan CSS blocks in <style> tags. Returns (new_html, count, previews)."""
    # Split into (outside, inside, outside, inside, ...) segments
    parts = re.split(
        r"(<style\b[^>]*>.*?</style>)",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    total = 0
    previews: list[str] = []

    for i, chunk in enumerate(parts):
        if i % 2 == 1:            # inside <style>…</style>
            continue
        blocks = find_orphan_blocks(chunk)
        if not blocks:
            continue

        new_chunk = []
        cursor = 0
        for start, end, text in blocks:
            new_chunk.append(chunk[cursor:start])
            new_chunk.append(f"<style>\n{text}\n</style>")
            previews.append(text[:200].replace("\n", " ⏎ "))
            cursor = end
        new_chunk.append(chunk[cursor:])
        parts[i] = "".join(new_chunk)
        total += len(blocks)

    return "".join(parts), total, previews


def process(path: Path, apply: bool) -> tuple[bool, int, list[str]]:
    html = path.read_text(encoding="utf-8", errors="replace")
    new_html, count, previews = wrap_orphan_css(html)
    if count == 0:
        return False, 0, []
    if apply:
        path.write_text(new_html, encoding="utf-8")
    return True, count, previews


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="Actually write changes (default is dry-run)")
    ap.add_argument("--verbose", action="store_true",
                    help="Print first 200 chars of each orphan block")
    args = ap.parse_args()

    candidates = []
    for p in ROOT.rglob("*.html"):
        rel_parts = p.relative_to(ROOT).parts[:-1]
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        if p.name.endswith("_template.html"):
            continue
        candidates.append(p)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"Mode: {mode}")
    print(f"Scanning {len(candidates)} files...\n")

    affected = 0
    total_blocks = 0

    for path in candidates:
        changed, count, previews = process(path, args.apply)
        if not changed:
            continue
        affected += 1
        total_blocks += count
        rel = path.relative_to(ROOT)
        marker = "✓" if args.apply else "•"
        print(f"  {marker} {rel}  (would wrap {count} block(s))")
        if args.verbose:
            for p in previews:
                print(f"      → {p}")

    print(f"\n{'=' * 60}")
    print(f"  Files affected : {affected}")
    print(f"  Blocks to wrap : {total_blocks}")
    print(f"  Mode           : {mode}")
    if not args.apply and affected > 0:
        print()
        print("  Re-run with --apply to write changes.")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
