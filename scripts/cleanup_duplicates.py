#!/usr/bin/env python3
"""
Cleanup script to remove duplicate Design B blocks and fix broken CSS paths.
Run this ONCE after the injector has been fixed.
"""
import sys
from pathlib import Path
from bs4 import BeautifulSoup, Comment

ROOT = Path(__file__).resolve().parent.parent

def is_duplicate_marker(soup, marker_text):
    """Check if a marker comment appears more than once."""
    return len(soup.find_all(string=lambda text: isinstance(text, Comment) and marker_text in text)) > 1

def cleanup_page(file_path: Path) -> str:
    html = file_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")
    modified = False

    # --- Fix 1: Remove the second, duplicate header and drawer ---
    # The old header starts after the first drawer's </aside>.
    # We can find it by looking for the duplicate 'siteDrawer' ID.
    first_drawer = soup.find(id="siteDrawer")
    if first_drawer:
        # Find all elements with this ID after the first one and remove them
        for duplicate in first_drawer.find_next_siblings(id="siteDrawer"):
            # Find the enclosing <aside> or <header> and remove it
            parent = duplicate.find_parent(['aside', 'header'])
            if parent:
                # Also remove the backdrop that comes with it
                backdrop = parent.find_previous_sibling(id="drawerBackdrop")
                if backdrop:
                    backdrop.decompose()
                parent.decompose()
                modified = True

    # --- Fix 2: Fix the broken CSS link in <head> ---
    bad_link = soup.find("link", href="/assets/design-b.css")
    if bad_link:
        bad_link.decompose()
        modified = True

    # --- Fix 3: Deduplicate identical CSS links in <head> ---
    seen_hrefs = set()
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href")
        if href in seen_hrefs:
            link.decompose()
            modified = True
        else:
            seen_hrefs.add(href)

    if modified:
        file_path.write_text(str(soup), encoding="utf-8")
        return "cleaned"
    return "skipped"

def main():
    all_html = list(ROOT.rglob("*.html"))
    # Filter out templates and scripts as before
    exclude_dirs = {"templates", "scripts", "node_modules", ".git", "__pycache__"}
    candidates = [
        f for f in all_html
        if not any(part in exclude_dirs for part in f.relative_to(ROOT).parts[:-1])
    ]

    cleaned_count = 0
    for file_path in candidates:
        result = cleanup_page(file_path)
        if result == "cleaned":
            cleaned_count += 1
            print(f"  ✓ Cleaned: {file_path.relative_to(ROOT)}")

    print(f"\nDone. Cleaned {cleaned_count} files.")

if __name__ == "__main__":
    main()
