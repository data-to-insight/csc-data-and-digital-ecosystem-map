#!/usr/bin/env python3
# ./admin_scripts/admin-build_cytoscape_utils.py


"""
Shared helpers for Cytoscape JSON builders used by both full and lite scripts 
"""

import json
import yaml
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path as _Path  # avoid clashing with Path type hints
import re

# ---------- YAML ----------

def load_yaml(path: Path) -> dict:
    """Safe load YAML file, return {} on empty, print friendly message on error and skip"""
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        print(f"YAML error in {path}: {e}")
        return {}

# Map node @type to type specific field block key in YAML
# Keep ORGANIZATION annoyingly spelled with Z to match the data model
TYPE_TO_BLOCK = {
    "ORGANIZATION": "organization_fields",
    "EVENT":        "event_fields",
    "PLAN":         "plan_fields",
    "RULE":         "rule_fields",
    "SERVICE":      "service_fields",
    "DATASET":      "dataset_fields",
    "PERSON":       "person_fields",
    "RESOURCE":     "resource_fields",
}

def extract_type_fields(data: dict, ntype: str) -> dict:
    """
    Return type specific fields dictionary from node YAML
    Eg for ntype='EVENT' this returns data['event_fields'] if present
    Falls back to {} never raises if block missing or not dict
    """
    key = TYPE_TO_BLOCK.get((ntype or "").upper())
    if not key:
        return {}
    block = data.get(key)
    if isinstance(block, dict):
        return block
    # if author used scalar or list by mistake preserve as "_value"
    if block is None:
        return {}
    return {"_value": block}

# ---------- JSON writing ----------

def _to_json_safe(obj):
    """Recursively convert objects that json cannot encode by default, eg dates or Paths"""
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
        return {str(k): _to_json_safe(v) for k, v in obj.items()}
    return obj

def write_json(path: Path, payload, *, minify: bool = True, safe_convert: bool = True) -> None:
    """Write JSON to path minified by default, with opt safe conversion for complex types"""
    path.parent.mkdir(parents=True, exist_ok=True)
    obj = _to_json_safe(payload) if safe_convert else payload
    opts = {"ensure_ascii": False}
    if minify:
        opts.update(separators=(",", ":"))
    else:
        opts.update(indent=2)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, **opts)

# ---------- Text helpers ----------

def kebab(s: str) -> str:
    if s is None:
        return ""
    s = re.sub(r"[^a-zA-Z0-9/_-]+", " ", str(s)).strip().lower()
    s = s.replace(" ", "-")
    return re.sub(r"-{2,}", "-", s)

def coalesce(*vals) -> str:
    for v in vals:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""

def singularize(s: str) -> str:
    if not s:
        return s
    return s[:-1] if s.endswith("s") else s

def as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v if x is not None]
    return [str(v)]

def pick_summary(d: dict) -> str:
    for k in ("summary", "description"):
        if d.get(k):
            return str(d[k])
    return ""

# ---------- Slugs and ids ----------

def slug_from_path(path: Path, base: Path) -> str:
    """Derive stable slug from file path relative to base, without extension"""
    rel = path.relative_to(base).with_suffix("")
    segs = [kebab(p) for p in rel.parts]
    return "/".join(segs)

def slug_from_file(file: Path) -> str:
    """Default simple slug from file name stem"""
    return file.stem

def canonical_node_id(data: dict, file: Path) -> str:
    """Prefer explicit id in YAML, else the file stem"""
    return data.get("id") or file.stem

def update_crosswalk(cw: dict, *, slug: str = None, name: str = None, filestem: str = None, node_id: str = None):
    """Populate crosswalk with common alternates that may appear in RELs- mapping to canonical node id"""
    if not node_id:
        return
    if slug:
        cw[slug] = node_id
    if name:
        cw[name] = node_id
        cw[name.lower()] = node_id
    if filestem:
        cw[filestem] = node_id

def resolve_id(x, seen_nodes: set, crosswalk: dict):
    """Resolve REL endpoint to canonical node id using seen set and crosswalk, return x if unresolved"""
    if not x:
        return x
    if x in seen_nodes:
        return x
    hit = crosswalk.get(x)
    if hit:
        return hit
    hit = crosswalk.get(str(x).lower())
    if hit:
        return hit
    return x

# ---------- Node presentation helpers ----------

def type_class(raw_type: str, category: str) -> str:
    """
    Map @type or folder category to concise class string used for styling
    We normalise both 'organization' and 'organisation' to 'org' here
    This only for CSS or palette lookup, YAML @type can stay 'ORGANIZATION' (with Z)
    """
    t = (raw_type or category or "other").strip().lower()
    # normalise UK versus US spelling for organisation, emit 'org' as style class
    # Some uncertainty here about how best to use the SCCM model as such as this an annoyance/unclear currently 
    if t in {"organization", "organisation"}:
        return "org"
    mapping = {
        "service": "service",
        "event": "event",
        "plan": "plan",
        "rule": "rule",
        "collection": "collection",
        "person": "person",
        "relationship": "relationship",
        "dataset": "dataset",
        "tool": "tool",
        "other": "default",
        "default": "default",
    }
    return mapping.get(t, "default")

def search_blob(label: str, tags, desc: str, *, slug: str = "", raw_type: str = "", limit: int = 500) -> str:
    """Compact search text blob for client side filtering trimmed to limit"""
    tag_str = " ".join(tags or [])
    parts = [label or "", tag_str, (desc or ""), slug or "", (raw_type or "")]
    base = " ".join(" ".join(p.split()) for p in parts if p is not None).strip().lower()
    return base[:limit]

def position_from_yaml(data: dict):
    """Optional fixed position from YAML returns {x, y} or None"""
    pos = data.get("position") or {}
    try:
        x = float(pos.get("x")); y = float(pos.get("y"))
        return {"x": x, "y": y}
    except Exception:
        return None
