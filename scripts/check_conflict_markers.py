#!/usr/bin/env python3
"""
Fail CI if any tracked text file contains an unresolved git merge conflict marker.

Runs against `git ls-files` so it never touches node_modules, dist, or build output.
File types checked: .html, .htm, .css, .js, .mjs, .json, .md, .xml, .svg, .yml, .yaml

Escape hatch: add  <!-- allow-conflict-markers -->  (HTML) or  # allow-conflict-markers
(Markdown/YAML/Python) to a file to skip it. Use only for files that legitimately
contain the marker text (documentation, tests).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

EXTENSIONS = {
    ".html", ".htm", ".css", ".js", ".mjs", ".json",
    ".md", ".xml", ".svg", ".yml", ".yaml",
}

# Git conflict markers: 7+ of the same char, followed by optional branch name
# for `<<<` and `>>>`, and nothing for `===`.
MARKER_RE = re.compile(r"^(<{7,}(?: .*)?|={7,}|>{7,}(?: .*)?)$")

ESCAPE_RE = re.compile(r"allow-conflict-markers", re.IGNORECASE)


def tracked_files() -> list[Path]:
    """Return git-tracked files with the extensions we care about."""
    try:
        out = subprocess.check_output(
            ["git", "ls-files"], text=True, stderr=subprocess.PIPE
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("::error::git is not available — run this inside the repo", file=sys.stderr)
        sys.exit(2)

    return [
        Path(line) for line in out.splitlines()
        if line and Path(line).suffix.lower() in EXTENSIONS
    ]


def find_markers(path: Path) -> list[tuple[int, str]]:
    """Return [(line_no, line_text), ...] for every conflict marker in the file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"::warning::Cannot read {path}: {exc}", file=sys.stderr)
        return []

    if ESCAPE_RE.search(text):
        return []

    hits: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if MARKER_RE.match(line.rstrip()):
            hits.append((lineno, line.rstrip()))
    return hits


def main() -> int:
    offenders: dict[Path, list[tuple[int, str]]] = {}

    for path in tracked_files():
        hits = find_markers(path)
        if hits:
            offenders[path] = hits

    if not offenders:
        print("✅ No merge conflict markers found in tracked files.")
        return 0

    print("❌ Unresolved merge conflict markers detected:\n")
    for path, hits in sorted(offenders.items()):
        # Emit GitHub Actions error annotations so the PR shows inline markers
        for lineno, text in hits:
            # GitHub Actions annotation format
            print(f"::error file={path},line={lineno}::conflict marker: {text[:60]}")
        print(f"  {path}")
        for lineno, text in hits[:5]:
            print(f"    line {lineno}: {text[:80]}")
        if len(hits) > 5:
            print(f"    …and {len(hits) - 5} more")
        print()

    print(f"Failing build: {len(offenders)} file(s) contain conflict markers.")
    print("Resolve the markers, commit the fixed files, and push again.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
