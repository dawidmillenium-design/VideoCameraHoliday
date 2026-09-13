#!/usr/bin/env python3
"""
clean_git_conflicts.py

A production-grade script to scan and clean git merge conflict artifacts 
from HTML files in a static site repository.

Features:
- Recursive scanning with exclusions (.git, templates, node_modules)
- Smart regex-based removal of conflict markers while preserving content
- Atomic file operations with automatic backups
- Comprehensive logging and statistics
- CI/CD friendly with exit codes and dry-run modes
"""

import argparse
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Optional

# --- Configuration & Constants ---

SCRIPT_DIR = Path(__file__).parent
BACKUP_DIR = SCRIPT_DIR / "backups"
LOG_FILE = SCRIPT_DIR / "cleanup_log.txt"

EXCLUDE_DIRS = {".git", "node_modules", "templates", "__pycache__"}
HTML_EXTENSION = ".html"

# Regex Patterns
# Matches lines starting with <<<<<<<
PATTERN_START = re.compile(r'^\s*<<<<<<<.*', re.MULTILINE)
# Matches lines containing ONLY ======= (with optional whitespace)
PATTERN_MIDDLE = re.compile(r'^\s*=======\s*$', re.MULTILINE)
# Matches lines starting with >>>>>>>
PATTERN_END = re.compile(r'^\s*>>>>>>>.*', re.MULTILINE)
# Matches embedded markers like <body>======= or text<<<<<<
PATTERN_EMBEDDED = re.compile(r'(<[^>]*?)={5,}|={5,}([^<]*?>)?')

# Colors for Terminal Output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def log_message(message: str, level: str = "INFO", verbose: bool = False):
    """Print colored messages to stdout."""
    icon = "📊"
    color = Colors.RESET
    
    if level == "SUCCESS":
        icon = "🟢"
        color = Colors.GREEN
    elif level == "WARNING":
        icon = "🟡"
        color = Colors.YELLOW
    elif level == "ERROR":
        icon = "🔴"
        color = Colors.RED
    elif level == "STATS":
        icon = "📈"
        color = Colors.BLUE
    elif level == "DRY":
        icon = "💧"
        color = Colors.BLUE

    if verbose or level in ["ERROR", "WARNING", "SUCCESS", "STATS"]:
        print(f"{color}{icon} [{level}] {message}{Colors.RESET}")

def get_encoding(file_path: Path) -> Optional[str]:
    """Detect encoding by trying UTF-8 first, then latin-1."""
    encodings = ['utf-8', 'latin-1']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read()
            return enc
        except UnicodeDecodeError:
            continue
        except Exception:
            return None
    return None

def create_backup(file_path: Path, force: bool = False) -> Optional[Path]:
    """Create a timestamped backup of the file."""
    if force:
        return None
    
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    relative_name = "_".join(file_path.relative_to(SCRIPT_DIR.parent).parts)
    backup_path = BACKUP_DIR / f"{relative_name}.{timestamp}.bak"
    
    try:
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception as e:
        log_message(f"Failed to create backup for {file_path}: {e}", "ERROR")
        return None

def clean_content(content: str) -> Tuple[str, int, List[str]]:
    """
    Clean the content by removing conflict markers.
    Returns: (cleaned_content, lines_removed, preview_markers)
    """
    lines = content.splitlines(keepends=True)
    cleaned_lines = []
    removed_count = 0
    preview_markers = []
    
    # Track consecutive empty lines to collapse them if > 3
    consecutive_empty = 0
    
    for line in lines:
        original_line = line
        
        # Check for full line markers
        is_marker_line = (
            line.strip().startswith('<<<<<<<') or
            re.match(r'^\s*=======\s*$', line) or
            line.strip().startswith('>>>>>>>')
        )
        
        if is_marker_line:
            # Extract a preview of the marker for logging
            if len(preview_markers) < 3:
                preview_markers.append(line.strip()[:60])
            removed_count += 1
            # If the line was purely a marker, we skip adding it (effectively removing it)
            # However, if there is content AFTER the marker on the same line, we keep the content
            # Logic: If line is JUST marker + newline, remove entirely.
            # If line is Marker + Content, strip marker.
            
            stripped = line.strip()
            if stripped.startswith('<<<<<<<'):
                # Try to preserve content after the marker if it exists on same line
                # Usually markers are on their own line, but handle edge case
                parts = line.split('<<<<<<<', 1)
                if len(parts) > 1 and len(parts[1]) > 0:
                    # Check if the rest is just the branch name/hash
                    rest = parts[1].split('\n')[0] # Get content before newline
                    if not re.match(r'\s*HEAD\s*$', rest) and not re.match(r'\s*[a-f0-9]+\s*$', rest):
                         # There seems to be actual content mixed in? Rare. 
                         # Safer to remove the whole line for standard git conflicts.
                         pass 
            continue
        
        # Check for embedded markers (e.g., <div>=======)
        if '=======' in line or '<<<<<<<' in line or '>>>>>>>' in line:
            # Apply regex to clean embedded markers
            # Replace <tag>==== with <tag>
            line = re.sub(r'(</?\w+[^>]*?)={5,}', r'\1', line)
            # Replace ======</tag> with </tag> (less common but possible)
            line = re.sub(r'={5,}(</?\w+[^>]*?>)', r'\1', line)
            # Remove any stray markers left
            line = line.replace('<<<<<<<', '').replace('>>>>>>>', '').replace('=======', '')
            
            if line != original_line and len(preview_markers) < 3:
                preview_markers.append(f"Embedded fix: {original_line.strip()[:40]}...")

        cleaned_lines.append(line)
    
    # Rejoin and handle excessive newlines resulting from removals
    final_content = "".join(cleaned_lines)
    
    # Collapse 4+ newlines into 2 (cleanup side effect)
    final_content = re.sub(r'\n{4,}', '\n\n', final_content)
    
    return final_content, removed_count, preview_markers

def atomic_write(file_path: Path, content: str, encoding: str):
    """Write content atomically using a temp file."""
    temp_file = file_path.with_suffix('.tmp_clean')
    try:
        with open(temp_file, 'w', encoding=encoding) as f:
            f.write(content)
        temp_file.replace(file_path)
        return True
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink()
        raise e

def scan_repository(root: Path) -> List[Path]:
    """Recursively find all HTML files excluding specific directories."""
    html_files = []
    for path in root.rglob(f'*{HTML_EXTENSION}'):
        # Check if any part of the path is in EXCLUDE_DIRS
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        html_files.append(path)
    return html_files

def validate_cleanup(file_path: Path) -> bool:
    """Verify no conflict markers remain in the file."""
    try:
        enc = get_encoding(file_path)
        if not enc: return False
        with open(file_path, 'r', encoding=enc) as f:
            content = f.read()
        if '<<<<<<<' in content or '=======' in content or '>>>>>>>' in content:
            return False
        return True
    except Exception:
        return False

def main():
    parser = argparse.ArgumentParser(description="Clean git merge conflict artifacts from HTML files.")
    parser.add_argument('--dry-run', action='store_true', help="Preview changes without modifying files.")
    parser.add_argument('--force', action='store_true', help="Skip backup creation.")
    parser.add_argument('--verbose', action='store_true', help="Show detailed processing info.")
    parser.add_argument('--stats', action='store_true', help="Show summary statistics after completion.")
    
    args = parser.parse_args()
    
    root_dir = SCRIPT_DIR.parent
    log_entries = []
    
    stats = {
        "scanned": 0,
        "modified": 0,
        "markers_removed": 0,
        "errors": 0,
        "failed_validation": 0
    }
    
    if args.dry_run:
        log_message("Running in DRY-RUN mode. No files will be modified.", "DRY")
    
    # Initialize Log File
    if not args.dry_run:
        with open(LOG_FILE, 'w', encoding='utf-8') as lf:
            lf.write(f"Cleanup Log - {datetime.now().isoformat()}\n")
            lf.write("-" * 50 + "\n")

    html_files = scan_repository(root_dir)
    stats["scanned"] = len(html_files)
    
    log_message(f"Found {len(html_files)} HTML files to scan.", "STATS")
    
    for file_path in html_files:
        try:
            encoding = get_encoding(file_path)
            if not encoding:
                log_message(f"Skipping {file_path}: Unable to detect encoding.", "WARNING", args.verbose)
                stats["errors"] += 1
                continue

            with open(file_path, 'r', encoding=encoding) as f:
                original_content = f.read()
            
            # Calculate initial word count roughly
            original_words = len(original_content.split())
            
            cleaned_content, removed_count, previews = clean_content(original_content)
            
            if removed_count > 0 or cleaned_content != original_content:
                stats["markers_removed"] += removed_count
                
                if args.dry_run:
                    log_message(f"Would modify: {file_path}", "DRY", True)
                    log_message(f"  Lines/Markers to remove: {removed_count}", "DRY", True)
                    if previews:
                        for p in previews:
                            log_message(f"  Preview: {p}", "DRY", True)
                else:
                    # Create Backup
                    backup_path = create_backup(file_path, args.force)
                    if backup_path and not args.force:
                        log_message(f"Backed up to: {backup_path.name}", "INFO", args.verbose)
                    
                    # Atomic Write
                    atomic_write(file_path, cleaned_content, encoding)
                    
                    # Validation Pass
                    if not validate_cleanup(file_path):
                        log_message(f"VALIDATION FAILED: {file_path} still contains markers!", "ERROR")
                        stats["failed_validation"] += 1
                        # Attempt to restore backup if validation fails? 
                        # For now, log error.
                    else:
                        stats["modified"] += 1
                    
                    # Log Entry
                    new_words = len(cleaned_content.split())
                    log_entry = f"{file_path} | Removed: {removed_count} | Words: {original_words} -> {new_words}\n"
                    with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                        lf.write(log_entry)
                    
                    log_message(f"Cleaned: {file_path} ({removed_count} markers)", "SUCCESS", args.verbose)
            
        except Exception as e:
            log_message(f"Error processing {file_path}: {e}", "ERROR")
            stats["errors"] += 1

    # Final Statistics
    if args.stats or args.dry_run:
        print("\n" + "="*40)
        log_message("CLEANUP STATISTICS", "STATS")
        print("="*40)
        log_message(f"Total Files Scanned:      {stats['scanned']}", "STATS")
        log_message(f"Total Files Modified:     {stats['modified']}", "STATS")
        log_message(f"Total Markers Removed:    {stats['markers_removed']}", "STATS")
        if stats['errors'] > 0:
            log_message(f"Files with Errors:        {stats['errors']}", "ERROR")
        if stats['failed_validation'] > 0:
            log_message(f"Files Failed Validation:  {stats['failed_validation']}", "ERROR")
        print("="*40)

    # Exit Code Logic for CI/CD
    if stats['failed_validation'] > 0:
        log_message("CRITICAL: Some files still contain conflict markers after cleanup.", "ERROR")
        sys.exit(1)
    
    if stats['errors'] > 0 and not args.dry_run:
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
