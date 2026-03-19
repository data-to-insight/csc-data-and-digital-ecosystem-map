#!/usr/bin/env python3
# ./admin_scripts/dev-testing-scale_up_yml.py

# Remember: if re-running with revised node numbers, you must have already (re)run the admin_scripts/admin-ORCHASTRATOR-rebuild_all_assets.py
# as it is this process that updates all the search index and graph definiton files. 


"""
Generate test ORGANIZATION YAMLs, and RELATIONSHIP YAMLs for scaling up tests. 
This process is all towards being able to test the MotW front end and search with increasingly large numbers of 
source files and optimised search and graph indexes. Note: Estimated top end atm is 10k nodes. 

Defaults
- ORG outdir: data_yml/organizations
- REL outdir: data_yml/relationships
- ORG filename: {prefix}{index:04d}.yaml, for example test_0001.yaml
- REL filename: {rel_prefix}{pair_index:04d}.yaml, for example testrel_0001.yaml
- ORG name: TEST{index}, for example TEST1
- REL source and target identifiers: file stems by default, for example test_0001

Relationship modes
  pairs   adjacent pairs, 1 with 2, 3 with 4, same as before
  chain   1-2-3-...-n
  ring    chain plus n-1 with 1
  knn     each node connects to the next K by index, set with --knn-k
  star    distributed hubs, one hub every --star-span nodes, hub connects to others in its span
  random  random K neighbors per node, set with --random-k, or use --random-p to choose by probability
  mixed   chain plus random K neighbors per node

Usage examples
  python admin_scripts/dev-testing-scale_up_yml.py -n 200 --clean-first --make-relationships
  python admin_scripts/dev-testing-scale_up_yml.py -n 200 --make-relationships --rel-mode knn --knn-k 3
  python admin_scripts/dev-testing-scale_up_yml.py -n 500 --make-relationships --rel-mode star --star-span 12
  python admin_scripts/dev-testing-scale_up_yml.py -n 500 --make-relationships --rel-mode random --random-k 4 --seed 123
  python admin_scripts/dev-testing-scale_up_yml.py -n 500 --make-relationships --rel-mode mixed --random-k 2
  # keep labels padded, but store slugs in source and target
  python admin_scripts/dev-testing-scale_up_yml.py -n 50 --make-relationships --id-strategy slug --label-id-strategy filestem
"""

# #very sparse
# python admin_scripts/dev-testing-scale_up_yml.py \
#   -n 500 \
#   --clean-first \
#   --make-relationships \
#   --id-strategy filestem \
#   --rel-mode ring \
#   --rel-prefix testrel_ring_

# #sparse hub clusters, not global connected
# python admin_scripts/dev-testing-scale_up_yml.py \
#   -n 500 \
#   --clean-first \
#   --make-relationships \
#   --id-strategy filestem \
#   --rel-mode star \
#   --star-span 10 \
#   --rel-prefix testrel_star10_

# #moderate, light, connected
# python admin_scripts/dev-testing-scale_up_yml.py \
#   -n 500 \
#   --clean-first \
#   --make-relationships \
#   --id-strategy filestem \
#   --rel-mode knn \
#   --knn-k 2 \
#   --rel-prefix testrel_knn2_

## full rel files clean up with prefixes
# # remove earlier test sets
# rm -f data_yml/relationships/testrel_mixed_*.yaml
# rm -f data_yml/relationships/testrel_star_*.yaml
# rm -f data_yml/relationships/testrel_ring_*.yaml

# # wipe everything under relationships, then rebuild sparse ring
# python admin_scripts/dev-testing-scale_up_yml.py -n 500 \
#   --clean-first --clean-all-rels \
#   --make-relationships --id-strategy filestem \
#   --rel-mode ring --rel-prefix testrel_ring_

# # keep current orgs, but delete any previous mixed or star sets
# python admin_scripts/dev-testing-scale_up_yml.py -n 500 \
#   --clean-first --clean-rel-glob 'testrel_mixed_*' --clean-rel-glob 'testrel_star10_*' \
#   --make-relationships --id-strategy filestem \
#   --rel-mode knn --knn-k 2 --rel-prefix testrel_knn2_


## Test running at 21/10/25
#3 step builds 500 orgs once, 
# ayers two sparse relationship sets on top
# First run wipes both orgs and rels, the next run keep just created and add more edges
# All runs keep --id-strategy filestem, and each layer uses own --rel-prefix so files dont collide

# #sparse, connected backbone, ring
# python admin_scripts/dev-testing-scale_up_yml.py \
#   -n 500 \
#   --clean-first --clean-all-orgs --clean-all-rels \
#   --make-relationships \
#   --id-strategy filestem \
#   --rel-mode ring \
#   --rel-prefix testrel_ring_

# #add light hub clusters
# python admin_scripts/dev-testing-scale_up_yml.py \
#   -n 500 \
#   --overwrite \
#   --make-relationships \
#   --id-strategy filestem \
#   --rel-mode star \
#   --star-span 20 \
#   --rel-prefix testrel_star20_

# #add few random cross links, capped
# python admin_scripts/dev-testing-scale_up_yml.py \
#   -n 500 \
#   --overwrite \
#   --make-relationships \
#   --id-strategy filestem \
#   --rel-mode random \
#   --random-k 1 \
#   --seed 42 \
#   --max-edges 150 \
#   --rel-prefix testrel_rand1_

import argparse
from pathlib import Path
import sys
import glob
import re
import random
from typing import List, Tuple, Iterable, Set

# Prefer ruamel.yaml, fall back to PyYAML
try:
    from ruamel.yaml import YAML
    from ruamel.yaml.scalarstring import FoldedScalarString
    _USE_RUAMEL = True
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.explicit_start = False
    yaml.explicit_end = False
except Exception:
    _USE_RUAMEL = False
    import yaml  # type: ignore

ORG_OUTDIR_DEFAULT = "/workspaces/csc-map-of-the-world/data_yml/organizations"
REL_OUTDIR_DEFAULT = "/workspaces/csc-map-of-the-world/data_yml/relationships"

def slugify(s: str) -> str:
    """Simple slug to mirror 'data_to_insight' style ids, lowercase plus underscores."""
    s = s.strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")

def build_org_payload(idx: int):
    """Construct the dict for one ORGANIZATION test record."""
    name = f"TEST{idx}"
    desc = "-"
    notes = "-"

    org_block = {
        "@type": "ORGANIZATION",
        "super_concept": "AGENT",
        "sub_concept": "",
        "name": name,
        "slug": slugify(name),
        "description": desc,
        "organization_fields": {
            "organisation_type": "",
            "region": "England",
            "projects": [""],
            "persons": [
                {"name": "", "role": "", "from": "1900-01-01"}
            ],
        },
        "tags": ["scaling"],
        "version": "2025.07",
        "date_published": "2020-01-01",
        "website": "https://www.example.org.uk",
        "notes": notes,
    }

    if _USE_RUAMEL:
        org_block["description"] = FoldedScalarString(desc)
        org_block["notes"] = FoldedScalarString(notes)

    return org_block

def build_relationship_payload(source_id: str, target_id: str, rel_type: str = "collaboratesWith", label: str = ""):
    """Construct the dict for one RELATIONSHIP record."""
    if not label:
        label = f"{source_id} | {target_id} {rel_type}"
    return {
        "@type": "RELATIONSHIP",
        "name": label,
        "source": source_id,
        "target": target_id,
        "relationship_type": rel_type,
        "tags": ["scaling"],
    }

def write_yaml(obj, path: Path, overwrite: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    if _USE_RUAMEL:
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(obj, f)
    else:
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(obj, f, sort_keys=False, allow_unicode=True, default_flow_style=False)

def _leading_literal(glob_pattern: str) -> str:
    """Return leading literal before any wildcard, used to infer safe delete prefix"""
    for i, ch in enumerate(glob_pattern):
        if ch in "*?[":
            return glob_pattern[:i]
    return glob_pattern

def _safe_delete(paths, allowed_prefixes) -> int:
    """Delete only files name starts with allowed prefixes"""
    removed = 0
    for p in map(Path, paths):
        fname = p.name
        if any(fname.startswith(pref) for pref in allowed_prefixes):
            try:
                p.unlink()
                removed += 1
            except Exception as e:
                print(f"Warning: could not remove {p}: {e}", file=sys.stderr)
        else:
            print(f"Skip, protected by prefix guard: {fname}", file=sys.stderr)
    return removed


def clean_prefix(outdir: Path, prefix: str) -> int:
    """Delete files named prefix*.yaml only - leave existing legit files in there"""
    pattern = str(outdir / f"{prefix}*.yaml")
    return _safe_delete(glob.glob(pattern), {prefix})


def clean_glob(outdir: Path, pattern: str, allowed_prefixes) -> int:
    """
    Delete files matching outdir/pattern, but only if names start with allowed_prefixes
    Eg: clean_glob(dir, 'testrel_mixed_*', {'testrel_', 'testrel_mixed_'})
    """
    pat = pattern if pattern.endswith(".yaml") else f"{pattern}.yaml"
    return _safe_delete(glob.glob(str(outdir / pat)), set(allowed_prefixes))

# ---------- relationship index pair generators ----------

def _dedup_edges(pairs: Iterable[Tuple[int,int]], n: int) -> List[Tuple[int,int]]:
    """Ensure i != j, store one undirected edge per pair as (min, max), drop out of range."""
    seen: Set[Tuple[int,int]] = set()
    out: List[Tuple[int,int]] = []
    for i, j in pairs:
        if i == j: 
            continue
        if not (0 <= i < n and 0 <= j < n):
            continue
        a, b = (i, j) if i < j else (j, i)
        if (a, b) in seen:
            continue
        seen.add((a, b))
        out.append((a, b))
    return out

def gen_pairs(n: int) -> List[Tuple[int,int]]:
    return _dedup_edges(((i, i+1) for i in range(0, n-1, 2)), n)

def gen_chain(n: int) -> List[Tuple[int,int]]:
    return _dedup_edges(((i, i+1) for i in range(0, n-1)), n)

def gen_ring(n: int) -> List[Tuple[int,int]]:
    base = [(i, i+1) for i in range(0, n-1)]
    if n > 2:
        base.append((n-1, 0))
    return _dedup_edges(base, n)

def gen_knn(n: int, k: int) -> List[Tuple[int,int]]:
    pairs = []
    for i in range(n):
        for d in range(1, k+1):
            j = i + d
            if j < n:
                pairs.append((i, j))
    return _dedup_edges(pairs, n)

def gen_star_distributed(n: int, span: int) -> List[Tuple[int,int]]:
    """Partition by 'span', pick the first in each block as hub, connect hub to others in block."""
    if span < 2:
        span = 2
    pairs = []
    for start in range(0, n, span):
        end = min(start + span, n)
        if end - start < 2:
            continue
        hub = start
        for j in range(start+1, end):
            pairs.append((hub, j))
    return _dedup_edges(pairs, n)

def gen_random_fixed_k(n: int, k: int, seed: int) -> List[Tuple[int,int]]:
    rng = random.Random(seed)
    pairs = []
    for i in range(n):
        # choose up to k distinct others
        choices = list(range(n))
        choices.remove(i)
        rng.shuffle(choices)
        for j in choices[:max(0, k)]:
            pairs.append((i, j))
    return _dedup_edges(pairs, n)

def gen_random_p(n: int, p: float, seed: int) -> List[Tuple[int,int]]:
    """Probability based, O(n^2), for smaller n."""
    rng = random.Random(seed)
    pairs = []
    for i in range(n):
        for j in range(i+1, n):
            if rng.random() < p:
                pairs.append((i, j))
    return _dedup_edges(pairs, n)

def gen_mixed(n: int, random_k: int, seed: int) -> List[Tuple[int,int]]:
    """Chain plus light random sprinkle."""
    base = set(gen_chain(n))
    rnd = set(gen_random_fixed_k(n, random_k, seed))
    out = list(base.union(rnd))
    out.sort()
    return out




# ---------- main ----------

def main():
    p = argparse.ArgumentParser(description="Generate ORGANIZATION and RELATIONSHIP test YAML files")
    p.add_argument("--count", "-n", type=int, required=True, help="Number of ORG files to generate")
    p.add_argument("--start", "-s", type=int, default=1, help="Starting index for TEST names and file numbering, default 1")
    p.add_argument("--prefix", "-p", default="test_", help="ORG filename prefix, default 'test_'")
    p.add_argument("--outdir", "-o", default=ORG_OUTDIR_DEFAULT, help=f"ORG output directory, default {ORG_OUTDIR_DEFAULT}")
    p.add_argument("--overwrite", action="store_true", help="Allow overwriting existing ORG and REL files")
    p.add_argument("--clean-first", action="store_true", help="Delete existing files matching prefixes before generating")

    # Relationship options
    p.add_argument("--make-relationships", action="store_true", help="Also create RELATIONSHIP YAMLs")
    p.add_argument("--rel-outdir", default=REL_OUTDIR_DEFAULT, help=f"REL output directory, default {REL_OUTDIR_DEFAULT}")
    p.add_argument("--rel-prefix", default="testrel_", help="REL filename prefix, default 'testrel_'")
    p.add_argument("--rel-type", default="collaboratesWith", help="relationship_type value, default collaboratesWith")

    p.add_argument("--id-strategy", choices=["slug", "name", "filestem"], default="filestem",
                   help="Identifier to store in source and target, default filestem, for example test_0001")
    p.add_argument("--label-id-strategy", choices=["slug", "name", "filestem"], default="filestem",
                   help="Identifier to use in the human label, default filestem, for example test_0001")

    p.add_argument("--rel-mode", choices=["pairs", "chain", "ring", "knn", "star", "random", "mixed"], default="pairs",
                   help="Relationship topology, default pairs")
    p.add_argument("--knn-k", type=int, default=3, help="k for knn mode, default 3")
    p.add_argument("--star-span", type=int, default=10, help="span for distributed stars, default 10")
    p.add_argument("--random-k", type=int, default=2, help="random neighbors per node for random or mixed modes, default 2")
    p.add_argument("--random-p", type=float, default=None, help="edge probability for random mode, optional, use for small n")
    p.add_argument("--seed", type=int, default=42, help="random seed for repeatable outputs, default 42")
    p.add_argument("--max-edges", type=int, default=None, help="optional cap on the number of relationships written")

    # extended
    p.add_argument("--clean-rel-glob", default=None,
                help="Extra glob to clean in relationships dir, for example 'testrel_*' or '*'")
    p.add_argument("--clean-org-glob", default=None,
                help="Extra glob to clean in org dir, for example 'test_*' or '*'")
    p.add_argument("--clean-all-rels", action="store_true",
                help="Clean all .yaml in relationships dir, use with care")
    p.add_argument("--clean-all-orgs", action="store_true",
                help="Clean all .yaml in organizations dir, use with care")

    args = p.parse_args()

    org_outdir = Path(args.outdir)
    rel_outdir = Path(args.rel_outdir)

    if args.clean_first:
        # Always guard by prefix of files - failsafe to prevent accidental non-test file removal
        allowed_org_prefixes = {args.prefix, "test_"}
        allowed_rel_prefixes = {args.rel_prefix, "testrel_", "test_"}  # include test_ just in case

        removed_org = clean_prefix(org_outdir, args.prefix)
        removed_rel = clean_prefix(rel_outdir, args.rel_prefix)

        # optional extra cleaning, still guarded
        if args.clean_all_orgs:
            # only remove org YAMLs that start with allowed test prefixes
            removed_org += clean_glob(org_outdir, "*.yaml", allowed_org_prefixes)

        if args.clean_org_glob:
            # infer a safe prefix from the glob, then add it to the guard set
            inferred = _leading_literal(args.clean_org_glob)
            removed_org += clean_glob(org_outdir, args.clean_org_glob, allowed_org_prefixes | {inferred})

        if args.clean_all_rels:
            removed_rel += clean_glob(rel_outdir, "*.yaml", allowed_rel_prefixes)

        if args.clean_rel_glob:
            inferred = _leading_literal(args.clean_rel_glob)
            removed_rel += clean_glob(rel_outdir, args.clean_rel_glob, allowed_rel_prefixes | {inferred})

        print(f"Cleaned {removed_org} ORG file(s) and {removed_rel} REL file(s).")


    # --- Generate ORGs
    created_orgs = 0
    file_stems: List[str] = []
    ids_for_relationships: List[str] = []
    names: List[str] = []
    slugs: List[str] = []

    for i in range(args.start, args.start + args.count):
        payload = build_org_payload(i)
        fname = f"{args.prefix}{i:04d}.yaml"
        fpath = org_outdir / fname

        payload["id"] = fpath.stem  # for example test_0001

        # precompute name and slug so we can use them for labels later
        nm = payload["name"]            # TEST{idx}
        sg = payload.get("slug") or slugify(nm)

        # choose identifier for the stored edge endpoints
        if args.id_strategy == "slug":
            id_value = sg
        elif args.id_strategy == "name":
            id_value = nm
        else:
            id_value = fpath.stem

        try:
            write_yaml(payload, fpath, overwrite=args.overwrite)
            created_orgs += 1
            file_stems.append(fpath.stem)
            ids_for_relationships.append(id_value)
            names.append(nm)
            slugs.append(sg)
        except FileExistsError as e:
            print(str(e), file=sys.stderr)
        except Exception as e:
            print(f"Error writing {fpath}: {e}", file=sys.stderr)

    print(f"ORGs: created {created_orgs} file(s) in {org_outdir}")

    # --- Generate RELATIONSHIPS
    created_rels = 0
    if args.make_relationships and created_orgs > 0:
        n = len(ids_for_relationships)

        # map for label id strategy
        label_map = {
            "filestem": file_stems,
            "slug": slugs,
            "name": names,
        }
        label_ids = label_map[args.label_id_strategy]

        # pick edge set by mode
        if args.rel_mode == "pairs":
            idx_pairs = gen_pairs(n)
        elif args.rel_mode == "chain":
            idx_pairs = gen_chain(n)
        elif args.rel_mode == "ring":
            idx_pairs = gen_ring(n)
        elif args.rel_mode == "knn":
            idx_pairs = gen_knn(n, max(1, args.knn_k))
        elif args.rel_mode == "star":
            idx_pairs = gen_star_distributed(n, max(2, args.star_span))
        elif args.rel_mode == "random":
            if args.random_p is not None:
                idx_pairs = gen_random_p(n, max(0.0, min(1.0, args.random_p)), args.seed)
            else:
                idx_pairs = gen_random_fixed_k(n, max(0, args.random_k), args.seed)
        elif args.rel_mode == "mixed":
            idx_pairs = gen_mixed(n, max(0, args.random_k), args.seed)
        else:
            idx_pairs = gen_pairs(n)

        # optional cap
        if args.max_edges is not None and len(idx_pairs) > args.max_edges:
            idx_pairs = idx_pairs[: args.max_edges]

        # write files
        for pair_idx, (a, b) in enumerate(idx_pairs, start=1):
            source_id = ids_for_relationships[a]
            target_id = ids_for_relationships[b]
            label_src = label_ids[a]
            label_tgt = label_ids[b]
            label = f"{label_src} | {label_tgt} {args.rel_type}"

            rel_payload = build_relationship_payload(source_id, target_id, rel_type=args.rel_type, label=label)
            rel_fname = f"{args.rel_prefix}{pair_idx:04d}.yaml"
            rel_fpath = rel_outdir / rel_fname
            try:
                write_yaml(rel_payload, rel_fpath, overwrite=args.overwrite)
                created_rels += 1
            except FileExistsError as e:
                print(str(e), file=sys.stderr)
            except Exception as e:
                print(f"Error writing {rel_fpath}: {e}", file=sys.stderr)

        print(f"RELATIONSHIPS: created {created_rels} file(s) in {rel_outdir}  , mode {args.rel_mode}, total nodes {n}")

        # odd leftover note only applies to 'pairs'
        if args.rel_mode == "pairs" and (n % 2 == 1):
            leftover = label_ids[-1]
            print(f"Note: odd count, leftover org with no pair: {leftover}")

if __name__ == "__main__":
    main()
