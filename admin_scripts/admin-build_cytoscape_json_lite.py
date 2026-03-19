#!/usr/bin/env python3
# ./admin_scripts/admin-build_cytoscape_json_lite.py

# The lite builder

# Purpose: produce small payload for fast page loads on GitHub Pages, mobile, and lower bandwidth end-user
# Data shape: tiny node objects with short keys [id, l, t, s, sb], edges as [src, tgt, rel], and one separate rich file for side panels. 
# prefers id then file stem and resolves relationship endpoints via crosswalk same as full builder.

# Outputs:
# docs/data/graph_data.lite.json [just what Cytoscape needs to render]
# docs/data/node_details.json [lazy loaded for the side panel]
# Use: production site build, simpler cache logic on the front end.

import os, json, yaml
from pathlib import Path
from admin_build_cytoscape_utils import extract_type_fields


ROOT     = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data_yml"
REL_DIR  = DATA_DIR / "relationships"

OUT_DIR  = ROOT / "docs" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LITE_PATH    = OUT_DIR / "graph_data.lite.json"
DETAILS_PATH = OUT_DIR / "node_details.json"


from datetime import date, datetime
from decimal import Decimal
from pathlib import Path as _Path  # alias to avoid clashing with given Path

def pick_summary(data: dict, limit: int | None = 260) -> str:
    """
    Choose short summary for the details/info panel

    Prefer 'summary', fall back == 'description' -->  'notes'
    Normalise whitespace opt truncate if limit not None
    """
    for key in ("summary", "description", "notes"):
        val = data.get(key)
        if val:
            text = " ".join(str(val).split())
            if limit is not None:
                return text[:limit]
            return text
    return ""


def _to_json_safe(obj):
    # Recursively convert objs not supported by JSON
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, _Path):
        return str(obj)
    if isinstance(obj, set):
        return sorted(_to_json_safe(v) for v in obj)
    if isinstance(obj, tuple):
        return [_to_json_safe(v) for v in obj]
    if isinstance(obj, list):
        return [_to_json_safe(v) for v in obj]
    if isinstance(obj, dict):
        return { str(k): _to_json_safe(v) for k, v in obj.items() }
    return obj

# compact join safe types
def _coalesce(*vals):
    for v in vals:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""

def _slug_from(file: Path):
    return file.stem  # keep it simple and stable

def _type_class(t: str, category: str):
    t = (t or category or "other").lower()
    if t == "organization": 
        return "org"
    return t

def _search_blob(label, tags, desc, limit=240):
    base = " ".join([label or "", " ".join(tags or []), (desc or "")]).strip()
    base = " ".join(base.split())  # collapse whitespace
    return base[:limit]

def _position_from_yaml(data: dict):
    # OP: support precomputed positions if present in YAML, e.g.:
    # position: { x: 120, y: 480 }
    pos = data.get("position") or {}
    try:
        x = float(pos.get("x")); y = float(pos.get("y"))
        return {"x": x, "y": y}
    except Exception:
        return None

def collect_nodes_and_details():
    lite_nodes = []
    details = {}
    seen = set()
    crosswalk = {}  # map of alternate identifiers to canonical node id

    for category in DATA_DIR.iterdir():
        if not category.is_dir() or category.name == "relationships":
            continue

        for file in category.glob("*.yaml"):
            if file.name.lower().startswith("template") or file.name.startswith("0_template"):
                continue

            # Load YAML first
            try:
                with open(file, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                print(f"YAML error in {file}: {e}")
                continue

            # Prefer explicit id in YAML, else file stem
            node_id = (data.get("id") or file.stem)
            if node_id in seen:
                continue

            label   = _coalesce(data.get("name"), node_id)
            ntype   = data.get("@type", category.name)
            cls     = _type_class(ntype, category.name)
            slug    = data.get("slug") or _slug_from(file)
            tags    = data.get("tags") or []
            desc    = data.get("description") or data.get("summary") or ""
            pos     = _position_from_yaml(data)  # optional

            # LITE node (small)
            n = {"id": node_id, "l": label, "t": cls, "s": slug, "sb": _search_blob(label, tags, desc)}
            if pos: 
                n["x"] = pos["x"]; n["y"] = pos["y"]
            lite_nodes.append(n)

            # DETAILS node (for side panel, richer)
            ntype  = (data.get("@type") or category.name).upper()
            fields = extract_type_fields(data, ntype)
            details[node_id] = {
                "label": label,
                "slug": slug,
                "type": ntype,
                "summary": pick_summary(data),
                "tags": data.get("tags") or [],
                "website": data.get("website"),
                "notes": data.get("notes"),
                "fields": fields,
                "organisation_type": fields.get("organisation_type"),
                "organization_type": fields.get("organization_type"),
                "region": fields.get("region"),
            }

            # Populate crosswalk with helpful keys that might appear in relationships
            if slug:
                crosswalk[slug] = node_id
            name_val = data.get("name")
            if isinstance(name_val, str) and name_val:
                crosswalk[name_val] = node_id
                crosswalk[name_val.lower()] = node_id

            # Also allow file stem as a key, which may equal slug anyway
            crosswalk[file.stem] = node_id

            seen.add(node_id)

    return lite_nodes, details, seen, crosswalk

def _resolve_id(x, seen_nodes, crosswalk):
    if not x:
        return x
    if x in seen_nodes:
        return x
    # try crosswalk
    hit = crosswalk.get(x)
    if hit:
        return hit
    # try case-insensitive match for names or slugs
    hit = crosswalk.get(str(x).lower())
    if hit:
        return hit
    return x

def collect_edges(seen_nodes, crosswalk):
    edges = []
    skipped = 0
    MAX_LOG = 20  # <=20 examples
    for file in REL_DIR.glob("*.yaml"):
        if file.name.startswith("0_template"):
            continue
        try:
            with open(file, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"YAML error in {file}: {e}")
            continue

        src = _resolve_id(data.get("source"), seen_nodes, crosswalk)
        tgt = _resolve_id(data.get("target"), seen_nodes, crosswalk)

        if not src or not tgt:
            if skipped < MAX_LOG:
                print(f"Incomplete edge in {file}: missing source or target")
            skipped += 1
            continue
        if src not in seen_nodes or tgt not in seen_nodes:
            if skipped < MAX_LOG:
                print(f"Skipping edge with missing node(s): {src}->{tgt} in {file.name}")
            skipped += 1
            continue
        rel = data.get("relationship_type", "relatesTo")
        edges.append([src, tgt, rel])
    if skipped:
        print(f"(Skipped {skipped} edges that referenced unknown nodes)")
    return edges


def write_json(path: Path, obj):
    safe = _to_json_safe(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(safe, f, separators=(",", ":"), ensure_ascii=False)
    print(f"Wrote {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    print("Building lite graph and details")
    nodes, details, seen, crosswalk = collect_nodes_and_details()
    edges = collect_edges(seen, crosswalk)

    print(f"Nodes: {len(nodes)}  |  Edges: {len(edges)}  |  Unique IDs: {len(seen)}")

    # LITE payload (tiny)
    write_json(LITE_PATH, {"nodes": nodes, "edges": edges})

    # DETAILS payload (rich)
    write_json(DETAILS_PATH, details)
