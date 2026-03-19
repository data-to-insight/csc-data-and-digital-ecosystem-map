#!/usr/bin/env python3
# ./


import os
import json
from pathlib import Path

# This script needs to be run regularly if nodes/new objects have added to the map
# Running the script updates the list of 'Source'(s) that is used to populate that field 
# in the submit form for RELATIONSHIP.Source (this added to enforce that no relation is added for none-existent objects)


# 
BASE_DIR = Path("/workspaces/csc-map-of-the-world")
OUTPUT_FILE = BASE_DIR / "docs/data/source_nodes.json"

# Mapping subfolder ->> source type label
SOURCE_TYPE_MAP = {
    "events": "EVENT",
    "plans": "PLAN",
    "services": "SERVICE",
    "organizations": "ORGANIZATION",
    "collections": "COLLECTION",
    "resources": "RESOURCE",
    "persons": "PERSON"
}

# Folder scanning config
FOLDER_RULES = {
    # # Some here are short-term ignored as backend structure not yet supported for some input types 
    # # In the same way, some input formats/naming is not yet optimised or release ready (e.g. unuseably long file naming)
    # "data_published": ["*.pdf"],
    "data_repos": "folders",  # Use folder names only
    # "data_web": ["*.txt"],
    "data_yml": ["events/*.yaml", "plans/*.yaml", "services/*.yaml", "organizations/*.yaml", "collections/*.yaml", "resources/*.yaml", "persons/*.yaml"]
}

# Dictionary to hold {type: [list of source names]}
typed_nodes = {}

for folder_name, rules in FOLDER_RULES.items():
    folder_path = BASE_DIR / folder_name
    if not folder_path.exists():
        continue

    if folder_name == "data_output":
        continue

    # Special case: folder names as source names
    if rules == "folders":
        for subfolder in folder_path.iterdir():
            if subfolder.is_dir():
                typed_nodes.setdefault("SERVICE", []).append(subfolder.name.strip())
        continue

    # General case: use path pattern and infer type from subfolder
    for pattern in rules:
        for file in folder_path.glob(pattern):
            if file.name.startswith("0_"):
                continue

            stem = file.stem.strip()
            if not stem:
                continue

            # Infer type from subfolder
            subfolder = file.parent.name
            source_type = SOURCE_TYPE_MAP.get(subfolder)
            if not source_type:
                continue

            typed_nodes.setdefault(source_type, []).append(stem)

# Sort entries for readability
for k in typed_nodes:
    typed_nodes[k] = sorted(set(typed_nodes[k]))

# Output JSON
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(typed_nodes, f, indent=2)

print(f"Extracted sources grouped by type to {OUTPUT_FILE}")
