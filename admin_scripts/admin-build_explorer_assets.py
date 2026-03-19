#!/usr/bin/env python3
# python ./admin_scripts/admin-build_cytoscape_json_lite.py
# python ./admin_scripts/admin-build_explorer_assets.py

# Build an undirected adjacency list adjacency.json, keyed by node id, for instant neighbour lookups without touching Cytoscape, for simple algorithms degree counts and BFS in plain JS
# Build key addressable lite map lite_index.json, object keyed by id - faster than scanning array when populating side panels or cross reference positions
# Build minimal search array graph_search_index.json, tiny records {id, l, t, s} to enable filters with plain JS, no heavyweight search lib
# full and lite builders create graph_data.json, crosswalk.json, graph_data.lite.json, and node_details.json

# writes:
# docs/data/lite_index.json , id keyed node lookup
# docs/data/graph_search_index.json , minimal search list
# docs/data/adjacency.json , undirected, de duplicated, sorted
# docs/data/degree.json , { id: degree } sorted by id

from pathlib import Path
import json, os

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"
SRC  = DATA / "graph_data.lite.json"

OUT_SEARCH = DATA / "graph_search_index.json"   # [{id,l,t,s}, ...]
OUT_ADJ    = DATA / "adjacency.json"      # {id: [neighborId, ...], ...}
OUT_LITE   = DATA / "lite_index.json"     # {id: {id,l,t,s,x,y,sb?}}
OUT_DEGREE = DATA / "degree.json"         # {id: degree}

TYPE_CLASS_STYLE = os.getenv("TYPE_CLASS_STYLE", "passthrough")  # passthrough, short, model

def normalise_t(t: str) -> str:
    if TYPE_CLASS_STYLE == "passthrough":
        return t or "other"
    # this only to handle possible inconsistent spellings given we're on confusing US-SCCM definition
    if t in {"organization", "organisation"}: # expecting z but just in case
        return "org" if TYPE_CLASS_STYLE == "short" else "organization"
    return t or "other"

def main():
    if not SRC.exists():
        raise SystemExit(f"Missing {SRC}, build your graph_data.lite.json first.")

    raw = json.loads(SRC.read_text(encoding="utf-8"))
    nodes = raw.get("nodes", [])
    edges = raw.get("edges", [])

    lite_index = {}
    search_index = []
    adj_sets = {}

    # deterministic order
    for n in sorted(nodes, key=lambda x: x.get("id", "")):
        nid = n["id"]
        tval = normalise_t(n.get("t"))
        obj = {
            "id": nid,
            "l": n.get("l") or nid,
            "t": tval,
            "s": n.get("s") or "",
            "x": n.get("x"),
            "y": n.get("y"),
        }
        if n.get("sb"):
            obj["sb"] = n["sb"]
        lite_index[nid] = obj

        search_index.append({"id": nid, "l": obj["l"], "t": tval, "s": obj["s"]})
        adj_sets[nid] = set()

    # undirected adjacency
    for e in edges:
        if not isinstance(e, list) or len(e) < 2:
            continue
        s, t = e[0], e[1]
        if s in adj_sets and t in adj_sets:
            adj_sets[s].add(t)
            adj_sets[t].add(s)

    # sort for stable diffs
    adj = {k: sorted(v) for k, v in sorted(adj_sets.items(), key=lambda kv: kv[0])}
    degree = {k: len(v) for k, v in adj.items()}

    DATA.mkdir(parents=True, exist_ok=True)
    OUT_LITE.write_text(json.dumps(lite_index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    OUT_SEARCH.write_text(json.dumps(search_index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    OUT_ADJ.write_text(json.dumps(adj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    OUT_DEGREE.write_text(json.dumps(degree, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"Wrote {OUT_LITE} ({OUT_LITE.stat().st_size} bytes)")
    print(f"Wrote {OUT_SEARCH} ({OUT_SEARCH.stat().st_size} bytes)")
    print(f"Wrote {OUT_ADJ} ({OUT_ADJ.stat().st_size} bytes)")
    print(f"Wrote {OUT_DEGREE} ({OUT_DEGREE.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
