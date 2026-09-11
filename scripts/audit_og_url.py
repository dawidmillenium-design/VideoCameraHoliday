#!/usr/bin/env python3
"""
Audit og:url, canonical, and social-image tags across every tracked HTML file.

Checks performed:
  1. og:url points to a file that actually exists in the repo
  2. og:url matches <link rel="canonical"> (normalized for trailing slash + case)
  3. og:image and twitter:image, when present, resolve to a real file OR external URL
  4. (--strict) Every page must have og:url, canonical, og:image, twitter:image

Exits 1 on any error. Warnings alone do not fail the build.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

SITE_BASE = "https://dawidmillenium-design.github.io/VideoCameraHoliday/"
SITE_PATH = "/VideoCameraHoliday/"

META_OG_URL = re.compile(
    r'<meta\s+property=["\']og:url["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
META_OG_IMAGE = re.compile(
    r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
META_TW_IMAGE = re.compile(
    r'<meta\s+name=["\']twitter:image["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
LINK_CANONICAL = re.compile(
    r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def tracked_html() -> list[Path]:
    out = subprocess.check_output(["git", "ls-files", "*.html"], text=True)
    return [Path(line) for line in out.splitlines() if line]


def normalize(url: str) -> str:
    """Reduce a URL to a canonical, repo-relative path for comparison."""
    if not url:
        return ""
    parsed = urlparse(url)
    path = parsed.path or url.split("?", 1)[0]

    # Strip site base whether absolute or root-relative
    for base in (SITE_PATH, "/", ""):
        if base and path.startswith(base):
            path = path[len(base):]
            break

    path = unquote(path).lstrip("/")

    # index.html and directory forms are equivalent
    if path.endswith("index.html"):
        path = path[: -len("index.html")]
    elif path.endswith("/index.html"):
        path = path[: -len("index.html")]

    return path.rstrip("/").lower()


def file_exists(repo_relative: str) -> bool:
    if not repo_relative:
        return False
    p = Path(repo_relative)
    if p.exists():
        return True
    # Directory-style URLs also match their index.html
    if (p / "index.html").exists():
        return True
    return False


def audit(strict: bool) -> int:
    errors = 0
    warnings = 0
    html_files = tracked_html()

    if not html_files:
        print("::error::No tracked HTML files found")
        return 1

    for path in html_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        og_url_m = META_OG_URL.search(text)
        canonical_m = LINK_CANONICAL.search(text)
        og_image_m = META_OG_IMAGE.search(text)
        tw_image_m = META_TW_IMAGE.search(text)

        og_url = og_url_m.group(1) if og_url_m else None
        canonical = canonical_m.group(1) if canonical_m else None
        og_image = og_image_m.group(1) if og_image_m else None
        tw_image = tw_image_m.group(1) if tw_image_m else None

        # ---- Strict presence checks ----
        if strict:
            for label, value in (
                ("og:url", og_url),
                ("canonical", canonical),
                ("og:image", og_image),
                ("twitter:image", tw_image),
            ):
                if not value:
                    print(f"::error file={path}::missing {label}")
                    errors += 1

        # ---- og:url existence ----
        if og_url:
            rel = normalize(og_url)
            if not file_exists(rel):
                print(
                    f"::error file={path}::og:url points to a file that does not exist: "
                    f"{og_url}  (resolved: {rel or '∅'})"
                )
                errors += 1

        # ---- canonical existence ----
        if canonical:
            rel = normalize(canonical)
            if not file_exists(rel):
                print(
                    f"::error file={path}::canonical points to a file that does not exist: "
                    f"{canonical}  (resolved: {rel or '∅'})"
                )
                errors += 1

        # ---- og:url ↔ canonical consistency ----
        if og_url and canonical and normalize(og_url) != normalize(canonical):
            print(
                f"::error file={path}::og:url and canonical disagree\n"
                f"    og:url   : {og_url}\n"
                f"    canonical: {canonical}"
            )
            errors += 1

        # ---- Social images: allow external, require existence for local ----
        for label, value in (("og:image", og_image), ("twitter:image", tw_image)):
            if not value:
                continue
            parsed = urlparse(value)
            if parsed.scheme in ("http", "https"):
                # External — assume OK, but flag obvious typos
                if not parsed.netloc:
                    print(f"::warning file={path}::{label} has an http(s) URL with no host: {value}")
                    warnings += 1
                continue
            rel = normalize(value)
            if not file_exists(rel):
                print(
                    f"::warning file={path}::{label} points to a file not found in repo: {value}"
                )
                warnings += 1

    print()
    print(f"Audited {len(html_files)} HTML files")
    print(f"Errors:   {errors}")
    print(f"Warnings: {warnings}")

    return 1 if errors else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Fail if og:url, canonical, og:image, or twitter:image is missing entirely",
    )
    args = ap.parse_args()
    return audit(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
