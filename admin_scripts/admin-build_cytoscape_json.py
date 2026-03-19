#!/usr/bin/env python3
# ./admin_scripts/admin-build_cytoscape_json.py

# The full builder

# Purpose: build complete graph payload for analysis, debugging richer UI stuff
# Data shape: verbose nodes and edges, plus a crosswalk, anything site or tools might need. prefers id then file stem, and it resolves relationship endpoints through the crosswalk.
# Typical outputs: docs/data/graph_data.json [full], docs/data/crosswalk.json [lookup], other side files wired in main builder
# Use: local dev, QA checks, search indexing, data audits, exporting for notebooks, anything where needed all fields and max detail.
    
# example output
# Graph JSON written: /workspaces/csc-map-of-the-world/docs/data/graph_data.json (minified, 149646 bytes)
# Crosswalk written:  /workspaces/csc-map-of-the-world/docs/data/crosswalk.json (minified, 41078 bytes)

import os
import re
import json
import yaml
from datetime import date, datetime
from pathlib import Path
from admin_scripts.admin_build_cytoscape_utils import (
    load_yaml,
    type_class,
    extract_type_fields,
    pick_summary,
    as_list,
    slug_from_path,
    singularize,
    coalesce,
    search_blob,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data_yml"
REL_DIR  = DATA_DIR / "relationships"

# Single output location (site assets)
OUT_DIR        = ROOT / "docs" / "data"
GRAPH_PATH     = OUT_DIR / "graph_data.json"
CROSSWALK_PATH = OUT_DIR / "crosswalk.json"

# slug -> { id, label, type, slug, source_path, page_url }
CROSSWALK = {}

# ---------------- helpers ----------------

def _json_default(o):
    """help datetime.date or datetime.datetime in graph structure to serialise
      in case any non-str dates in yml org etc files"""
    if isinstance(o, (date, datetime)):
        # "2025-12-02" style, JSON friendly
        return o.isoformat()
    # Fallback so dont crash on other odd types
    return str(o)


# ---------------- helpers ----------------
def write_json(path: Path, payload, *, minify: bool = True):
    """Write JSON either minified (default) or pretty- ensure parent dir exist"""
    opts = {
        "ensure_ascii": False,
        "default": _json_default,
    }
    if minify:
        opts.update(separators=(",", ":"))
    else:
        opts.update(indent=2)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, **opts)


def kebab(s: str) -> str:
    if s is None:
        return ""
    s = re.sub(r"[^a-zA-Z0-9/_-]+", " ", str(s)).strip().lower()
    s = s.replace(" ", "-")
    return re.sub(r"-{2,}", "-", s)

def slug_from_path(path: Path, base: Path) -> str:
    """Derive stable slug from file path relative to data_yml/ (no extension)"""
    rel = path.relative_to(base).with_suffix("")
    segs = [kebab(p) for p in rel.parts]
    return "/".join(segs)

def as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v if x is not None]
    return [str(v)]

def pick_summary(data: dict, limit: int | None = 260) -> str:
    """
    Choose short summary for details/info panel

    Prefer 'summary' fall back == 'description' -->  'notes'
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

def singularize(s: str) -> str:
    if not s:
        return s
    return s[:-1] if s.endswith("s") else s
# -----------------------------------------


def get_entities():
    elements = []
    seen_nodes = set()

    # if global crosswalk dict elsewhere dont clear it here
    for category in DATA_DIR.iterdir():
        if not category.is_dir() or category.name == "relationships":
            continue

        for file in category.glob("*.yaml"):
            name_l = file.name.lower()
            if name_l.startswith("template") or file.name.startswith("0_template"):
                continue

            data = load_yaml(file)
            if not data:
                continue

            # prefer explicit id, else file stem
            node_id = data.get("id") or file.stem
            if not node_id or node_id in seen_nodes:
                continue

            # label, type, class
            label = coalesce(data.get("name"), node_id)
            if not label:
                print(f"Skipping node with invalid or missing label: {node_id}")
                continue

            raw_type = (data.get("@type") or singularize(category.name)).strip()
            ntype = raw_type.upper()                  # e.g. ORGANIZATION, EVENT, PLAN
            cls   = type_class(raw_type, category.name)  # e.g. org, event, plan

            # basic metadata
            tags     = as_list(data.get("tags"))
            summary  = pick_summary(data)
            slug     = data.get("slug") or slug_from_path(file, DATA_DIR)
            sblob    = search_blob(label, tags, summary, slug=slug, raw_type=raw_type)
            source_path    = str(file.relative_to(ROOT)).replace("\\", "/")
            page_url       = f"{slug}/"   # front-end will prefix SITE_BASE
            website        = data.get("website")
            notes          = data.get("notes")
            version        = data.get("version")
            date_published = data.get("date_published")
            super_concept  = data.get("super_concept")
            sub_concept    = data.get("sub_concept")

            # generic type-specific block for info panel
            fields = extract_type_fields(data, ntype)  # e.g. event_fields, plan_fields, etc.

            # convenience pull-throughs for legacy UI bits
            organisation_type = (fields.get("organisation_type")
                                 or fields.get("organization_type"))
            region   = fields.get("region")
            projects = as_list(fields.get("projects"))
            persons  = fields.get("persons") or []
            norm_persons = []
            if isinstance(persons, list):
                for p in persons:
                    if isinstance(p, dict):
                        # normalise keys to strings
                        norm_persons.append({
                            "name": str(p.get("name", "")),
                            "role": str(p.get("role", "")) if p.get("role") is not None else "",
                            "from": str(p.get("from", "")) if p.get("from") is not None else "",
                        })
                    else:
                        # allow simple string person entries
                        norm_persons.append({"name": str(p), "role": "", "from": ""})

            el = {
                "group": "nodes",
                "data": {
                    "id":            node_id,
                    "label":         label,
                    "type":          ntype,          # keep model type with Z spelling for ORGANIZATION
                    "group":         "nodes",
                    "slug":          slug,
                    "source_path":   source_path,
                    "page_url":      page_url,
                    "tags":          tags,
                    "summary":       summary,
                    "search_blob":   sblob,
                    "website":       website,
                    "notes":         notes,
                    "version":       str(version) if version is not None else None,
                    "date_published": str(date_published) if date_published is not None else None,
                    "super_concept":  super_concept,
                    "sub_concept":    sub_concept,

                    # expose type-specific fields in one place for side info panel
                    "fields":        fields,

                    # convenience legacy keys, especially for orgs
                    "organisation_type": organisation_type,
                    "region":            region,
                    "projects":          projects,
                    "persons":           norm_persons,
                },
                "classes": cls  # compact style class eg. org, event, plan
            }

            elements.append(el)
            seen_nodes.add(node_id)

            # keep existing crosswalk payload if rely on it elsewhere (tbc)
            CROSSWALK[slug] = {
                "id":          node_id,
                "label":       label,
                "type":        ntype,
                "slug":        slug,
                "source_path": source_path,
                "page_url":    page_url,
            }

    return elements, seen_nodes



def get_relationships(seen_nodes):
    edges = []
    for file in REL_DIR.glob("*.yaml"):
        if file.name.startswith("0_template"):
            continue
        with open(file, encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                print(f"YAML error in {file}: {e}")
                continue

        def resolve_id(x):


            if not x:


                return x


            if x in seen_nodes:


                return x


            # try slug lookup from CROSSWALK keys which are slugs


            cw = CROSSWALK.get(x)


            if cw and cw.get("id"):


                return cw["id"]


            return x


        


        source = resolve_id(data.get("source"))


        target = resolve_id(data.get("target"))

        if not source or not target:
            print(f"Incomplete edge in {file}: missing source or target")
            continue
        if source not in seen_nodes or target not in seen_nodes:
            print(f"Skipping edge with missing node(s): {source} -> {target} in {file.name}")
            continue

        relationship_type = data.get("relationship_type", "relatesTo")
        edges.append({
            "group": "edges",
            "data": {
                "source": source,
                "target": target,
                "label": relationship_type,
                "relationship_type": relationship_type,
                "group": "edges"
            }
        })
    return edges


if __name__ == "__main__":

    MINIFY = True # for now, as CLI not in use
    # Output format toggle (env only): GRAPH_MINIFY=0 -> pretty; else minified (default)
    # MINIFY = os.getenv("GRAPH_MINIFY", "1") != "0"

    print("Building Cytoscape JSON from YAMLs...")
    nodes, seen_nodes = get_entities()
    edges = get_relationships(seen_nodes)

    if not nodes:
        raise ValueError("No nodes were generated. Check input YAMLs")
    if not edges:
        print("No edges generated. Potential isolated nodes visible")

    graph = {"elements": nodes + edges}

    # Single outputs (no intermediate copies)
    write_json(GRAPH_PATH, graph, minify=MINIFY)
    print(f"Graph JSON written: {GRAPH_PATH} ({'minified' if MINIFY else 'pretty'}, {GRAPH_PATH.stat().st_size} bytes)")

    write_json(CROSSWALK_PATH, CROSSWALK, minify=MINIFY)
    print(f"Crosswalk written:  {CROSSWALK_PATH} ({'minified' if MINIFY else 'pretty'}, {CROSSWALK_PATH.stat().st_size} bytes)")
