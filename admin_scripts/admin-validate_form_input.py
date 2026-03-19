#!/usr/bin/env python3
# ./

import os
import yaml
from pathlib import Path
import shutil

# source and target folders
incoming_dir = Path("incoming_submissions")
target_base = Path("data_yml")

# Create map of @type to subfolder
type_to_folder = {
    "ORGANIZATION": "organizations",
    "SERVICE": "services",
    "TOOL": "tools",
    "PROJECT": "projects",
    "PERSON": "persons",
    "PLAN": "plans",
    "RESOURCE": "resources",
    "COLLECTION": "collections",
    "RELATIONSHIP": "relationships",
    "EVENT": "events"
}

def is_valid_yaml(yaml_path):
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        if not isinstance(content, dict):
            print(f"Invalid format in {yaml_path.name}: not a dictionary at root.")
            return False, None
        if "@type" not in content:
            print(f"Missing '@type' in {yaml_path.name}")
            return False, None
        return True, content
    except yaml.YAMLError as e:
        print(f"YAML error in {yaml_path.name}: {e}")
        return False, None

def move_file(yaml_path, content):
    obj_type = content["@type"].upper()
    folder = type_to_folder.get(obj_type)
    if not folder:
        print(f"Unsupported type '{obj_type}' in {yaml_path.name}")
        return

    dest_dir = target_base / folder
    dest_dir.mkdir(parents=True, exist_ok=True)

    # name to snake_case for filename
    name_slug = content.get("name", "unnamed").lower().replace(" ", "_")
    new_filename = f"{name_slug}.yaml"
    dest_path = dest_dir / new_filename

    shutil.move(str(yaml_path), str(dest_path))
    print(f"Moved {yaml_path.name} → {dest_path}")

def process_all():
    if not incoming_dir.exists():
        print("No incoming_submissions folder found.")
        return

    for file in incoming_dir.glob("*.yaml"):
        valid, content = is_valid_yaml(file)
        if valid:
            move_file(file, content)

if __name__ == "__main__":
    process_all()
