#!/usr/bin/env python3
# ./admin_scripts/admin-validate_yml_objects.py

# run this periodically, or post new additions. IT will scan the yml folder(s) looking for out of place typos/content/filenames 
# against the expected yml schema and flag the errors it finds, e.g. filenames with spaces, missing elements within the ymls

import yaml
import re
from pathlib import Path

def is_snake_case(value):
    return bool(re.fullmatch(r"[a-z0-9_]+", value))

def validate_yaml(file_path):
    errors = []
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            content = yaml.safe_load(f)
        except Exception as e:
            return [f"{file_path}: YAML error - {e}"]

    required_fields = ['@type', 'name', 'description']
    for field in required_fields:
        if field not in content:
            errors.append(f"{file_path}: Missing required field '{field}'")

    if 'tags' in content:
        for tag in content['tags']:
            if not isinstance(tag, str) or not tag.islower() or ' ' in tag:
                errors.append(f"{file_path}: Invalid tag '{tag}' (should be lowercase and no spaces)")

    snake_fields = ['lead_organisation', 'employer', 'source', 'target']
    for field in snake_fields:
        val = content.get(field)
        if val and not is_snake_case(val):
            errors.append(f"{file_path}: Field '{field}' not snake_case -> '{val}'")

    return errors

def validate_relationship_links(relationship_dir, all_node_ids):
    errors = []
    for file in relationship_dir.glob("*.yaml"):
        if file.name.startswith("0_template"):
            continue
        with open(file, 'r', encoding='utf-8') as f:
            try:
                content = yaml.safe_load(f)
            except Exception as e:
                errors.append(f"{file}: YAML error - {e}")
                continue

        source = content.get("source")
        target = content.get("target")

        if source and source not in all_node_ids:
            errors.append(f"{file}: source '{source}' not found among node IDs")
        if target and target not in all_node_ids:
            errors.append(f"{file}: target '{target}' not found among node IDs")
    return errors

def rename_files_with_spaces(directory):
    renamed_files = []
    for ext in ("*.yml", "*.yaml"):
        for path in directory.rglob(ext):
            new_stem = path.stem.replace(" ", "_").lower()
            new_name = f"{new_stem}{path.suffix.lower()}"
            new_path = path.with_name(new_name)
            if path.name != new_name:
                path.rename(new_path)
                renamed_files.append((path, new_path))
    return renamed_files


if __name__ == "__main__":
    root = Path("./data_yml")
    rel_dir = root / "relationships"

    # rename .yml and .yaml files with spaces
    renames = rename_files_with_spaces(root)
    if renames:
        print("Renamed files:")
        for old, new in renames:
            print(f"  {old} -> {new}")
    else:
        print("No filenames with spaces found.")

    # validate contents
    all_yamls = list(root.rglob("*.yaml"))
    relationship_yamls = list(rel_dir.glob("*.yaml"))
    node_yamls = [p for p in all_yamls if p not in relationship_yamls]

    node_ids = set(p.stem for p in node_yamls if not p.name.lower().startswith("template"))
    all_errors = []

    for yml in all_yamls:
        all_errors.extend(validate_yaml(yml))

    all_errors.extend(validate_relationship_links(rel_dir, node_ids))

    if all_errors:
        print("\nValidation issue(s) found:")
        for err in all_errors:
            print(err)
        print("\n")
    else:
        print("\nAll YAML files passed validation and relationship integrity checks")
