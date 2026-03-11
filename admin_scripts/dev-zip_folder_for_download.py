#!/usr/bin/env python3
"""
admin-zip_folder_for_download.py

Zip up a folder for easy offline download/sharing of folders with multiple file contents. 
This is a stand-alone process. Just run as-is to get the needed zip - some options
allow specifying the output name, others just take the raw folder name. 

Key behaviours:
- pass an explicit folder path, or a folder name to search for(to zip up)
- By default, zip is created next to the folder (same parent directory)
- The zip contains a top level folder, so extracting recreates the folder cleanly
- Sensible default excludes, plus your own --exclude patterns
- btw if output zip is placed inside the folder being zipped, it will be skipped

E.g
1) Zip an explicit folder path, output next to it
   python3 admin_scripts/admin-zip_folder_for_download.py --path docs/data_yml

2) Find folder by name anywhere under repo root, error if multiple matches
   python3 admin_scripts/admin-zip_folder_for_download.py --name data_yml

3) Find by name under specific root, and set an explicit output path
   python3 admin_scripts/admin-zip_folder_for_download.py --name data_yml --search-root /workspaces/csc-map-of-the-world --out /workspaces/csc-map-of-the-world/data_yml_for_download.zip

4) Add excludes
   python3 admin_scripts/admin-zip_folder_for_download.py --path . --exclude ".git/*" --exclude "site/*"
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


DEFAULT_EXCLUDES = [
    ".git/*",
    ".github/*",
    ".venv/*",
    "venv/*",
    "__pycache__/*",
    ".pytest_cache/*",
    ".mypy_cache/*",
    ".ruff_cache/*",
    ".tox/*",
    ".ipynb_checkpoints/*",
    "node_modules/*",
    "site/*",
    "*.pyc",
    "*.pyo",
    "*.DS_Store",
]


@dataclass(frozen=True)
class ResolveResult:
    folder: Path
    found_by: str


def find_repo_root(start: Path) -> Path:
    """
    Walk upwards looking for a .git folder. If not found, use the start dir
    """
    cur = start.resolve()
    for _ in range(50):
        if (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start.resolve()


def match_any(path_posix: str, patterns: Iterable[str]) -> bool:
    for pat in patterns:
        if fnmatch.fnmatch(path_posix, pat):
            return True
    return False


def resolve_target_folder(
    folder_path: Optional[str],
    folder_name: Optional[str],
    search_root: Optional[str],
) -> ResolveResult:
    if folder_path:
        p = Path(folder_path).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"Folder path does not exist: {p}")
        if not p.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {p}")
        return ResolveResult(folder=p, found_by="path")

    if not folder_name:
        raise ValueError("You must provide either --path or --name")

    root = Path(search_root).expanduser().resolve() if search_root else find_repo_root(Path.cwd())
    if not root.exists():
        raise FileNotFoundError(f"Search root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Search root is not a directory: {root}")

    matches: List[Path] = []
    for d in root.rglob(folder_name):
        if d.is_dir() and d.name == folder_name:
            matches.append(d.resolve())

    if not matches:
        raise FileNotFoundError(f"No folder named '{folder_name}' found under: {root}")

    if len(matches) > 1:
        pretty = "\n".join(f"  - {m}" for m in sorted(matches))
        raise RuntimeError(
            f"Multiple folders named '{folder_name}' found, please use --path, or narrow with --search-root.\n{pretty}"
        )

    return ResolveResult(folder=matches[0], found_by=f"name under {root}")


def default_output_path(folder: Path, suffix: str = "") -> Path:
    base = folder.name
    if suffix:
        base = f"{base}_{suffix}"
    return folder.parent / f"{base}.zip"


def iter_files(folder: Path) -> Iterable[Path]:
    for p in folder.rglob("*"):
        if p.is_file():
            yield p


def safe_zip_write(
    zf: zipfile.ZipFile,
    src_file: Path,
    arcname: Path,
) -> None:
    """
    Write file into zip, preserving unix mode where possible
    """
    st = src_file.stat()
    zi = zipfile.ZipInfo.from_file(src_file, arcname.as_posix())
    if os.name != "nt":
        zi.external_attr = (st.st_mode & 0xFFFF) << 16
    with src_file.open("rb") as f:
        zf.writestr(zi, f.read(), compress_type=zipfile.ZIP_DEFLATED)


def zip_folder(
    folder: Path,
    out_zip: Path,
    excludes: List[str],
    include_hidden: bool,
    dry_run: bool,
) -> Tuple[int, int]:
    folder = folder.resolve()
    out_zip = out_zip.resolve()

    if out_zip.exists():
        out_zip.unlink()

    total = 0
    added = 0

    # If output zip is inside the folder being zipped, skip it while scanning
    skip_out_zip = False
    try:
        skip_out_zip = out_zip.is_relative_to(folder)  # py3.9+ on pathlib in 3.12 yes
    except Exception:
        # fallback for older semantics, though your env is likely 3.10+
        try:
            out_zip.relative_to(folder)
            skip_out_zip = True
        except Exception:
            skip_out_zip = False

    for f in iter_files(folder):
        total += 1

        if skip_out_zip and f.resolve() == out_zip:
            continue

        rel = f.relative_to(folder)
        rel_posix = rel.as_posix()

        if not include_hidden:
            parts = rel.parts
            if any(part.startswith(".") for part in parts):
                continue

        if match_any(rel_posix, excludes):
            continue

        # store inside zip as: <folder_name>/<relative_path>
        arc = Path(folder.name) / rel

        if dry_run:
            added += 1
            continue

        out_zip.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out_zip, "a", compression=zipfile.ZIP_DEFLATED) as zf:
            safe_zip_write(zf, f, arc)
        added += 1

    return total, added


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Zip a folder for download")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--path", help="Explicit folder path to zip, relative or absolute")
    g.add_argument("--name", help="Folder name to search for under --search-root (or repo root by default)")

    p.add_argument(
        "--search-root",
        help="Root directory to search under when using --name. Default is repo root (detected via .git), else CWD",
    )
    p.add_argument(
        "--out",
        help="Output zip file path. Default is <folder_parent>/<folder_name>.zip",
    )
    p.add_argument(
        "--suffix",
        help="Optional suffix appended to output file name, ignored if --out is provided",
        default="",
    )
    p.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Exclude glob patterns relative to the folder, can be repeated, example, 'site/*', '*.parquet'",
    )
    p.add_argument(
        "--no-default-excludes",
        action="store_true",
        help="Disable built in excludes like .git, node_modules, site, caches",
    )
    p.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include dotfiles and dotfolders. By default they are skipped",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write a zip, just report what would be included",
    )
    return p.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    try:
        resolved = resolve_target_folder(args.path, args.name, args.search_root)
        folder = resolved.folder

        excludes = []
        if not args.no_default_excludes:
            excludes.extend(DEFAULT_EXCLUDES)
        excludes.extend(args.exclude or [])

        out_zip = Path(args.out).expanduser().resolve() if args.out else default_output_path(folder, args.suffix)

        total, added = zip_folder(
            folder=folder,
            out_zip=out_zip,
            excludes=excludes,
            include_hidden=bool(args.include_hidden),
            dry_run=bool(args.dry_run),
        )

        if args.dry_run:
            print(f"[DRY RUN] Folder: {folder} ({resolved.found_by})")
            print(f"[DRY RUN] Would create: {out_zip}")
            print(f"[DRY RUN] Files scanned: {total}, files included: {added}")
        else:
            print(f"Folder: {folder} ({resolved.found_by})")
            print(f"Created zip: {out_zip}")
            print(f"Files scanned: {total}, files included: {added}")

        return 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
