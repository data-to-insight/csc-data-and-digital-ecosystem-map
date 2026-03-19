#!/usr/bin/env python3
# ./

import os
import json
from pathlib import Path

# This script needs to be run regularly if nodes/new objects have added to the map
# Running the script updates the list of 'Source'(s) that is used to populate that field 
# in the submit form for RELATIONSHIP.Source (this added to enforce that no relation is added for none-existent objects)


BASE_DIR = Path("/workspaces/csc-map-of-the-world")
OUTPUT_FILE = BASE_DIR / "docs/data/source_nodes.json"

# Custom folder scanning config
FOLDER_RULES = {
    # # Some here are short-term ignored as backend structure not yet supported for some input types 
    # # In the same way, some input formats/naming is not yet optimised or release ready (e.g. unuseably long file naming)
    # "data_published": ["*.pdf"],
    "data_repos": "folders",  # Use folder names only
    # "data_web": ["*.txt"],
    "data_yml": ["events/*.yaml", "plans/*.yaml", "services/*.yaml", "organizations/*.yaml", "collections/*.yaml", "resources/*.yaml", "persons/*.yaml"]
}

# hold unique names
node_names = set()

for folder_name, rules in FOLDER_RULES.items():
    folder_path = BASE_DIR / folder_name
    if not folder_path.exists():
        continue

    # Skip data_output entirely
    if folder_name == "data_output":
        continue

    # Special case: scan folders instead of files
    if rules == "folders":
        for subfolder in folder_path.iterdir():
            if subfolder.is_dir():
                node_names.add(subfolder.name.strip())
        continue

    # General case: apply file pattern rules
    for pattern in rules:
        for file in folder_path.glob(pattern):
            if file.name.startswith("0_"):
                continue  # Skip disabled files
            stem = file.stem.strip()
            if stem:
                node_names.add(stem)

# Output JSON
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(sorted(node_names), f, indent=2)

print(f"Extracted {len(node_names)} source nodes to {OUTPUT_FILE}")
