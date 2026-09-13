#!/usr/bin/env python3
"""
Clean git merge conflict artifacts from HTML files.
SAFER VERSION: Only targets strict line-based git markers.
"""

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# STRICT Patterns: Only match if the line is EXACTLY a git marker
# This prevents it from touching HTML comments like <!-- ======= -->
MARKER_START = re.compile(r'^\s*<{7}\s*.*$')  # <<<<<<<
MARKER_MIDDLE = re.compile(r'^\s*={7}\s*$')   # ======= (must be alone on the line)
MARKER_END = re.compile(r'^\s*>{7}\s*.*$')    # >>>>>>>

EXCLUDED_DIRS = {'templates', 'node_modules', '.git', 'venv', '__pycache__', 'backups'}

def should_exclude(file_path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in file_path.parts)

def is_conflict_line(line: str) -> bool:
    """Returns True ONLY if the line is a strict git conflict marker."""
    if MARKER_START.match(line): return True
    if MARKER_MIDDLE.match(line): return True
    if MARKER_END.match(line): return True
    return False

def process_file(file_path: Path, dry_run: bool, force: bool, verbose: bool, log_file) -> dict:
    stats = {'scanned': 1, 'modified': 0, 'markers_removed': 0, 'errors': 0}
    
    try:
        try:
            content = file_path.read_text(encoding='utf-8')
            encoding = 'utf-8'
        except UnicodeDecodeError:
            content = file_path.read_text(encoding='latin-1')
            encoding = 'latin-1'
            
        lines = content.splitlines(keepends=True)
        new_lines = []
        modified = False
        markers_found = 0
        
        for line in lines:
            if is_conflict_line(line):
                modified = True
                markers_found += 1
                # Skip adding this line to new_lines (effectively deleting it)
            else:
                new_lines.append(line)
            
        if modified:
            stats['modified'] = 1
            stats['markers_removed'] += markers_found
            
            if dry_run:
                if verbose:
                    print(f"  🟡 Would clean: {file_path} ({markers_found} markers)")
                log_file.write(f"DRY-RUN: Would clean {file_path} ({markers_found} markers)\n")
            else:
                if not force:
                    backup_dir = Path("scripts/backups")
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = backup_dir / f"{file_path.name}_{timestamp}.bak"
                    shutil.copy2(file_path, backup_path)
                
                # Atomic write
                temp_path = file_path.with_suffix('.tmp')
                temp_path.write_text("".join(new_lines), encoding=encoding)
                temp_path.replace(file_path)
                
                if verbose:
                    print(f"  🟢 Cleaned: {file_path} ({markers_found} markers)")
                log_file.write(f"CLEANED: {file_path} ({markers_found} markers)\n")
                
        return stats
        
    except Exception as e:
        print(f"  🔴 Error processing {file_path}: {e}")
        log_file.write(f"ERROR: {file_path} - {e}\n")
        stats['errors'] = 1
        return stats

def validate_file(file_path: Path) -> bool:
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        lines = content.splitlines()
        for line in lines:
            if is_conflict_line(line):
                return False
        return True
    except Exception:
        return False

def main():
    parser = argparse.ArgumentParser(description="Clean git merge conflict artifacts.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed.")
    parser.add_argument("--force", action="store_true", help="Skip backup creation.")
    parser.add_argument("--verbose", action="store_true", help="Show detailed info.")
    parser.add_argument("--stats", action="store_true", help="Show statistics after completion.")
    args = parser.parse_args()

    print(" Starting Git Conflict Cleanup (Safe Mode)...")
    
    root_dir = Path(".")
    html_files = [f for f in root_dir.rglob("*.html") if f.is_file() and not should_exclude(f)]
    print(f"📁 Found {len(html_files)} HTML files to scan.")
    
    total_stats = {'scanned': 0, 'modified': 0, 'markers_removed': 0, 'errors': 0, 'validation_failed': 0}
    
    log_path = Path("scripts/cleanup_log.txt")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"\n--- Run: {datetime.now().isoformat()} ---\n")
        
        for file_path in html_files:
            stats = process_file(file_path, args.dry_run, args.force, args.verbose, log_file)
            for key in total_stats:
                total_stats[key] += stats[key]

    if not args.dry_run:
        print("\n🔍 Running validation pass...")
        for file_path in html_files:
            if not validate_file(file_path):
                print(f"  🔴 Validation failed (markers remain): {file_path}")
                total_stats['validation_failed'] += 1

    if args.stats or not args.dry_run:
        print("\n📊 Cleanup Statistics:")
        print(f"  Files scanned       : {total_stats['scanned']}")
        print(f"  Files modified      : {total_stats['modified']}")
        print(f"  Markers removed     : {total_stats['markers_removed']}")
        print(f"  Errors              : {total_stats['errors']}")
        if not args.dry_run:
            print(f"  Validation failures : {total_stats['validation_failed']}")

    if total_stats['validation_failed'] > 0 and not args.dry_run:
        print("\n CRITICAL: Some files still contain conflict markers.")
        sys.exit(1)
        
    print("\n✨ Cleanup complete!")
    sys.exit(0)

if __name__ == "__main__":
    main()
