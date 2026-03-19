#!/usr/bin/env python3
# ./admin_scripts/dev-

import os

# simple dev output on console of repo structure tree for reference
# can be run at any time, makes no changes, console output only for ref or adding output manually to .md files if needed

# folders to exclude(makes output tree huge/plus not required)
EXCLUDED_DIRS = {
    ".git", "site", "__pycache__", ".ipynb_checkpoints", ".venv",
    "env", ".mypy_cache", ".pytest_cache", ".vscode", ".DS_Store",
    ".idea", "node_modules", "dev_archive", "docs copy - pre index data preload optimisation"
}

# file extensions to exclude
EXCLUDED_EXTENSIONS = {".pyc", ".log", ".tmp"}

# file or folder name prefixes to exclude
EXCLUDED_PREFIXES = ("testrel_", "test_")  

def print_tree(base_path, prefix=""):
    try:
        entries = sorted(os.listdir(base_path))
    except PermissionError:
        return  # skip inaccessible folders

    entries = [
        e for e in entries
        # exclude hidden entries
        if not e.startswith(".")
        # exclude specific directories
        and e not in EXCLUDED_DIRS
        # exclude by name prefix
        and not any(e.startswith(p) for p in EXCLUDED_PREFIXES)
        # exclude by extension for files
        and not (
            os.path.isfile(os.path.join(base_path, e))
            and os.path.splitext(e)[1] in EXCLUDED_EXTENSIONS
        )
    ]

    count = len(entries)

    for i, entry in enumerate(entries):
        path = os.path.join(base_path, entry)
        connector = "└── " if i == count - 1 else "├── "
        if os.path.isdir(path):
            print(f"{prefix}{connector}{entry}/")
            new_prefix = "    " if i == count - 1 else "│   "
            print_tree(path, prefix + new_prefix)
        else:
            print(f"{prefix}{connector}📄 {entry}")

# start from current dir
print_tree(os.getcwd())
