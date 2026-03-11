#!/usr/bin/env python3
# python ./admin_scripts/admin-ORCHASTRATOR-rebuild_all_assets.py

"""
This is a script to kick-off everything needed when new data is added, refreshed etc. 
Should just run as-is within the codespace. For an overview of what is about to be run
look below for the block '# Scripts'

Rebuild graph assets, then ingest external search and vector artifacts.

Pipeline
  1) Full graph builder
  2) Lite graph builder
  3) Explorer assets, lite_index, adjacency, degree, graph_search_index
  4) Source list JSON v1, archive to source_nodes.list.json
  5) Source list DICT v2, archive to source_nodes.dict.json, and leave as default source_nodes.json
  6) sources.md page
  7) Ingest external files(Post local python processing via : csc_motw_corpus_build.ipynb (RH)) from data_externally_processed 
  into docs/data and docs/data/csc_artifacts,  overwrite existing files, report exactly what changed.

External inbox layout, if exist we take these from inbox and move them to where they need to be in /docs 
This is the enabler to ensure they're available for use within the search/graph/network etc
  data_externally_processed/search_index.json      -> docs/data/search_index.json
  data_externally_processed/motw_index.faiss       -> docs/data/csc_artifacts/motw_index.faiss
  data_externally_processed/motw_chunks.parquet    -> docs/data/csc_artifacts/motw_chunks.parquet
  data_externally_processed/motw_vectors.parquet   -> docs/data/csc_artifacts/motw_vectors.parquet
  data_externally_processed/state.json             -> docs/data/csc_artifacts/state.json
"""

from __future__ import annotations
import argparse, os, shutil, subprocess, sys, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DATA = ROOT / "docs" / "data"
EXT_INBOX = ROOT / "data_externally_processed"
ARTI_DIR  = DOCS_DATA / "csc_artifacts"

## Scripts
# This is what we're going to run here, order (for some) is important
# note that all scripts should be prefixed with admin- for consistency/visibility
S_FULL   = ROOT / "admin_scripts" / "admin-build_cytoscape_json.py"
S_LITE   = ROOT / "admin_scripts" / "admin-build_cytoscape_json_lite.py"
S_EXPL   = ROOT / "admin_scripts" / "admin-build_explorer_assets.py"
S_SRC_V1 = ROOT / "admin_scripts" / "admin-extract_JSON_form_sources_relations_v1.py"
S_SRC_V2 = ROOT / "admin_scripts" / "admin-extract_DICT_form_sources_relations_v2.py"
S_PAGE   = ROOT / "admin_scripts" / "admin-re-build-sources-page.py"
if not S_PAGE.exists():
    S_PAGE = ROOT / "admin_scripts" / "admin-re_build-sources-page.py"
##

# Our back-end data source files, underpinning front-end graphs/search etc. 
REPORT_FILES = [
    "graph_data.json",
    "crosswalk.json",
    "graph_data.lite.json",
    "node_details.json",
    "lite_index.json",
    "adjacency.json",
    "degree.json",
    "graph_search_index.json",
    "search_index.json",
    "source_nodes.json",
    "source_nodes.list.json",
    "source_nodes.dict.json",
]

SEARCH_INDEX_FILE = "search_index.json"

# Those that have been uploaded to repo after external (py/jupyter) pre-processing
EXTERNAL_ARTIFACT_FILES = [
    "motw_index.faiss",
    "motw_chunks.parquet",
    "motw_vectors.parquet",
    "state.json",  
]

# def run_py(script: Path, env: dict | None = None, name: str | None = None) -> None:
#     if not script.exists():
#         print(f"[skip] {name or script.name}, not found at {script}")
#         return
#     print(f"[run]  {name or script.name}")
#     proc = subprocess.run([sys.executable, str(script)], cwd=ROOT, env=env or os.environ.copy())
#     if proc.returncode != 0:
#         raise SystemExit(f"Step failed, {script} returned {proc.returncode}")
def run_py(script: Path, env: dict | None = None, name: str | None = None) -> None:
    if not script.exists():
        print(f"[skip] {name or script.name}, not found at {script}")
        return

    print(f"[run]  {name or script.name}")

    # prepends repo root to PYTHONPATH for child scripts that orchestrator runs 'import admin_scripts'
    env = env or os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    if existing:
        env["PYTHONPATH"] = f"{ROOT}{os.pathsep}{existing}"
    else:
        env["PYTHONPATH"] = str(ROOT)

    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        env=env,
    )
    if proc.returncode != 0:
        raise SystemExit(f"Step failed, {script} returned {proc.returncode}")

def size_of(p: Path) -> str:
    try:
        return f"{p.stat().st_size:,} bytes"
    except FileNotFoundError:
        return "missing"

def sha256_of(p: Path, block: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(block), b""):
            h.update(chunk)
    return h.hexdigest()

def copy_with_report(src: Path, dst: Path, verify_hash: bool) -> str:
    if not src.exists():
        return f"[miss] {src.name} not present in {src.parent}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    old_size = dst.stat().st_size if dst.exists() else None
    new_size = src.stat().st_size

    old_hash = new_hash = None
    if verify_hash and dst.exists():
        try:
            old_hash = sha256_of(dst)
        except Exception as e:
            return f"[warn] could not hash existing {dst.name}, {e}"
    if verify_hash:
        try:
            new_hash = sha256_of(src)
        except Exception as e:
            return f"[warn] could not hash source {src.name}, {e}"

    shutil.copy2(src, dst)

    if old_size is None:
        return f"[create] {dst.name}, size {new_size:,} bytes"
    if verify_hash and old_hash and new_hash:
        if old_hash == new_hash:
            return f"[unchanged] {dst.name} (hash equal)"
        return f"[overwritten] {dst.name} (old {old_size:,}, new {new_size:,})"
    status = "overwritten" if old_size != new_size else "replaced"
    return f"[{status}] {dst.name}, old {old_size:,}, new {new_size:,} bytes"

def ingest_external_files(verify_hash: bool = False) -> list[str]:
    msgs: list[str] = []
    if not EXT_INBOX.exists():
        msgs.append(f"[skip] external inbox not found, {EXT_INBOX}")
        return msgs

    # search_index.json to docs/data
    si_src = EXT_INBOX / SEARCH_INDEX_FILE
    si_dst = DOCS_DATA / SEARCH_INDEX_FILE
    msgs.append(copy_with_report(si_src, si_dst, verify_hash))

    # artifacts to docs/data/csc_artifacts
    for name in EXTERNAL_ARTIFACT_FILES:
        src = EXT_INBOX / name
        dst = ARTI_DIR / name
        msgs.append(copy_with_report(src, dst, verify_hash))

    return msgs

def main():
    ap = argparse.ArgumentParser(description="Rebuild graph assets, then ingest external search and vector artifacts.")
    ap.add_argument("--no-full", action="store_true", help="Skip full graph builder")
    ap.add_argument("--no-lite", action="store_true", help="Skip lite graph builder")
    ap.add_argument("--no-explorer", action="store_true", help="Skip explorer assets")
    ap.add_argument("--no-sources", action="store_true", help="Skip source list JSON and DICT steps")
    ap.add_argument("--no-sources-page", action="store_true", help="Skip rebuilding sources.md")
    ap.add_argument("--no-ingest-external", action="store_true", help="Skip ingesting data_externally_processed")
    ap.add_argument("--verify-hash", action="store_true", help="Hash before and after when ingesting, slower, precise diff")
    ap.add_argument("--type-class-style", choices=["passthrough", "short", "model"],
                    default=os.getenv("TYPE_CLASS_STYLE", "short"),
                    help="Normalise node type, short gives 'org', model gives 'organization'")
    args = ap.parse_args()

    DOCS_DATA.mkdir(parents=True, exist_ok=True)

    if not args.no_full:
        run_py(S_FULL, name="full graph builder")

    if not args.no_lite:
        run_py(S_LITE, name="lite graph builder")

    if not args.no_explorer:
        env = os.environ.copy()
        env["TYPE_CLASS_STYLE"] = args.type_class_style
        run_py(S_EXPL, env=env, name="explorer assets")

    if not args.no_sources:
        run_py(S_SRC_V1, name="source list, JSON v1")
        src_json = DOCS_DATA / "source_nodes.json"
        if src_json.exists():
            shutil.copy2(src_json, DOCS_DATA / "source_nodes.list.json")

        run_py(S_SRC_V2, name="source list, DICT v2")
        src_dict = DOCS_DATA / "source_nodes.json"
        if src_dict.exists():
            shutil.copy2(src_dict, DOCS_DATA / "source_nodes.dict.json")

    if not args.no_sources_page:
        run_py(S_PAGE, name="sources page")

    if not args.no_ingest_external:
        print(f"[ingest] checking {EXT_INBOX}")
        for m in ingest_external_files(verify_hash=args.verify_hash):
            print(" ", m)

    print("\nSummary of key outputs:")
    for rel in REPORT_FILES:
        p = DOCS_DATA / rel
        print(f"  - {rel:28} {size_of(p)}")

    if ARTI_DIR.exists():
        print("\nVector search artifacts under docs/data/csc_artifacts:")
        for f in sorted(ARTI_DIR.iterdir()):
            if f.is_file():
                print(f"  - {f.name:24} {size_of(f)}")
    else:
        print("\nDocs artifact folder missing, expected if not ingested external files yet")

    if EXT_INBOX.exists():
        print(f"\nExternal inbox present at {EXT_INBOX}")
    else:
        print(f"\nExternal inbox not found at {EXT_INBOX}")

if __name__ == "__main__":
    main()
