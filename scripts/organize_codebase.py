#!/usr/bin/env python3
"""
Minerva Codebase Organization Script
This script organizes the Minerva codebase according to the Minerva Master Ruleset.
It identifies and moves files to appropriate archive directories based on their type.
"""

import os
import shutil
import re
import glob
from pathlib import Path

# Archive directories
ARCHIVE_TEST = "archive/test_files"
ARCHIVE_BACKUP = "archive/backup_files"
ARCHIVE_DEMO = "archive/demo_files"
ARCHIVE_OLD_SCRIPTS = "archive/old_scripts"

# Extensions to identify backup files
BACKUP_PATTERNS = [".bak", ".backup", "_backup", ".save", ".fixed", ".orig", ".patch"]

# Patterns to identify test files
TEST_PATTERNS = ["test_*.py", "*_test.py", "test_*.js", "*_test.js", 
                 "test_*.html", "*_test.html", "simple_*.py", "minimal_*.py"]

# Patterns to identify demo files
DEMO_PATTERNS = ["*_demo.py", "*_demo.html", "*_example.*"]

# Legacy files to archive (from Minerva ruleset #7)
LEGACY_FILES = [
    "web/static/js/floating-chat.js",
    "web/static/js/chat/direct-chat.js",
    "web/static/js/chat/chat.js",
    "web/static/js/chat/chat-core.js"
]

def ensure_dir(directory):
    """Ensure a directory exists."""
    os.makedirs(directory, exist_ok=True)

def archive_file(src_path, archive_dir):
    """Archive a file to the specified directory."""
    if not os.path.exists(src_path):
        print(f"File not found: {src_path}")
        return False
    
    # Create the target directory
    ensure_dir(archive_dir)
    
    # Get the filename without the path
    filename = os.path.basename(src_path)
    
    # Create the full target path
    target_path = os.path.join(archive_dir, filename)
    
    # If the file already exists in the archive, append a number
    if os.path.exists(target_path):
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(os.path.join(archive_dir, f"{base}_{counter}{ext}")):
            counter += 1
        target_path = os.path.join(archive_dir, f"{base}_{counter}{ext}")
    
    try:
        shutil.move(src_path, target_path)
        print(f"Moved: {src_path} → {target_path}")
        return True
    except Exception as e:
        print(f"Error moving {src_path}: {e}")
        return False

def is_backup_file(filename):
    """Check if a file is a backup file."""
    for pattern in BACKUP_PATTERNS:
        if pattern in filename:
            return True
    return False

def organize_codebase(root_dir):
    """Organize the codebase by moving files to appropriate archive directories."""
    files_processed = {
        "backup": 0,
        "test": 0,
        "demo": 0,
        "legacy": 0
    }
    
    # Ensure archive directories exist
    ensure_dir(os.path.join(root_dir, ARCHIVE_BACKUP))
    ensure_dir(os.path.join(root_dir, ARCHIVE_TEST))
    ensure_dir(os.path.join(root_dir, ARCHIVE_DEMO))
    ensure_dir(os.path.join(root_dir, ARCHIVE_OLD_SCRIPTS))
    
    # Process backup files
    for root, _, files in os.walk(root_dir):
        for file in files:
            if is_backup_file(file):
                full_path = os.path.join(root, file)
                # Skip files already in archive
                if "archive" in full_path or "backup" in full_path or "test" in full_path:
                    continue
                
                if archive_file(full_path, os.path.join(root_dir, ARCHIVE_BACKUP)):
                    files_processed["backup"] += 1
    
    # Process test files (outside of test/ or tests/ directories)
    for pattern in TEST_PATTERNS:
        for file_path in glob.glob(os.path.join(root_dir, "**", pattern), recursive=True):
            # Skip files that are already in test directories or archive
            if "/test/" in file_path or "/tests/" in file_path or "/archive/" in file_path:
                continue
            if archive_file(file_path, os.path.join(root_dir, ARCHIVE_TEST)):
                files_processed["test"] += 1
    
    # Process demo and example files
    for pattern in DEMO_PATTERNS:
        for file_path in glob.glob(os.path.join(root_dir, "**", pattern), recursive=True):
            if "/archive/" in file_path:
                continue
            if archive_file(file_path, os.path.join(root_dir, ARCHIVE_DEMO)):
                files_processed["demo"] += 1
    
    # Process legacy files (from Minerva ruleset)
    for legacy_file in LEGACY_FILES:
        full_path = os.path.join(root_dir, legacy_file)
        if os.path.exists(full_path):
            if archive_file(full_path, os.path.join(root_dir, ARCHIVE_OLD_SCRIPTS)):
                files_processed["legacy"] += 1
    
    return files_processed

def main():
    """Main function."""
    print("Minerva Codebase Organization")
    print("============================")
    
    # Get the project root directory
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(f"Project root: {root_dir}")
    
    # Organize the codebase
    stats = organize_codebase(root_dir)
    
    # Print summary
    print("\nSummary:")
    print(f"Backup files archived: {stats['backup']}")
    print(f"Test files archived: {stats['test']}")
    print(f"Demo files archived: {stats['demo']}")
    print(f"Legacy files archived: {stats['legacy']}")
    print("\nOrganization complete!")

if __name__ == "__main__":
    main()
