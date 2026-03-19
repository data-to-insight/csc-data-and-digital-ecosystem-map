#!/usr/bin/env python3
# ./

import os
from pathlib import Path
from datetime import datetime
import pdfplumber


BASE_DIR = Path("/workspaces/csc-map-of-the-world")

FOLDERS = {
    # This to be added to as further data_ folders added
    "SCCM-aligned YAML Metadata": BASE_DIR / "data_yml",
    "Published Reports and Frameworks": BASE_DIR / "data_published",
    "Cloned Repo Docs": BASE_DIR / "data_repos",
    "Public Web Data": BASE_DIR / "data_web",
}
OUTPUT_MD = BASE_DIR / "docs/sources.md" # overwrites existing
INCLUDE_EXT = {".yml", ".yaml", ".pdf", ".txt", ".md"}

def get_word_count(file_path, ext):
    try:
        if ext == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                return sum(len(p.extract_text().split()) for p in pdf.pages if p.extract_text())
        elif ext == ".docx":
            # note - have switched off import of docx lib/ python-docx
            doc = Document(file_path)
            return sum(len(p.text.split()) for p in doc.paragraphs)
        elif ext in {".txt", ".md"}:
            return len(Path(file_path).read_text(encoding="utf-8", errors="ignore").split())
    except Exception:
        return "-"
    return "-"

def get_last_refreshed(file_path):
    # Using file modified time as a proxy for "refreshed"
    # Will only show last re-build time, but still relevant
    ts = os.path.getmtime(file_path)
    return datetime.fromtimestamp(ts).strftime("%d/%m/%Y")

def collect_sources(folder_path):
    data = {}
    for subdir, _, files in os.walk(folder_path):
        rel = Path(subdir).relative_to(folder_path)

        # Skip /data_yml/relationships entirely
        if folder_path.name == "data_yml" and rel.parts and rel.parts[0] == "relationships":
            continue

        group = rel.parts[0] if rel.parts else folder_path.name
        if group not in data:
            data[group] = []

        for file in files:
            if file.startswith("0_"):
                continue
            ext = Path(file).suffix.lower()
            if ext not in INCLUDE_EXT:
                continue
            full_path = Path(subdir) / file
            label = Path(file).stem
            word_count = "-" if ext in {".yml", ".yaml"} else get_word_count(full_path, ext)
            refreshed = get_last_refreshed(full_path)
            data[group].append((label, ext, word_count, refreshed))

    return data

def generate_markdown():
    lines = [
        "# Data Sources",
        "",
        "To add transparency to the search in particular, below is the current scope of the input data/sources enabling the network graph|visualisations; these sources also contribute to the expanded 'full search' resource). Note: Some of the visualisation labelling is feed dynamically off the sources themselves and may therefore be inconsistent. ",
        ""
    ]

    for section_name, folder in FOLDERS.items():
        grouped_sources = collect_sources(folder)
        total_entries = sum(len(entries) for entries in grouped_sources.values())
        if total_entries == 0:
            continue

        lines.append(f"## {section_name} *(~{total_entries} source{'s' if total_entries != 1 else ''})*")

        # Special case: Flatten Cloned Repo tables into one table
        # Otherwise we get a table of 1/2 entries per repo 
        if section_name == "Cloned Repo Docs":
            flat_entries = []
            for subfolder, entries in sorted(grouped_sources.items()):
                for label, ext, word_count, refreshed in entries:
                    combined_label = f"{subfolder}_{label}"
                    flat_entries.append((combined_label, ext, word_count, refreshed))

            if flat_entries:
                lines.append("| Source | File Type | Word Count | Last Refreshed |")
                lines.append("|--------|-----------|------------|----------------|")
                for combined_label, ext, word_count, refreshed in sorted(flat_entries):
                    lines.append(f"| {combined_label} | {ext} | {word_count} | {refreshed} |")
                lines.append("")

        else:
            for subfolder, entries in sorted(grouped_sources.items()):
                if not entries:
                    continue
                lines.append(f"### {subfolder}")
                lines.append("| Source | File Type | Word Count | Last Refreshed |")
                lines.append("|--------|-----------|------------|----------------|")
                for label, ext, word_count, refreshed in sorted(entries):
                    lines.append(f"| {label} | {ext} | {word_count} | {refreshed} |")
                lines.append("")

    return "\n".join(lines)


def main():
    md_output = generate_markdown()
    OUTPUT_MD.write_text(md_output, encoding="utf-8")
    print(f"sources.md (re)created at: {OUTPUT_MD}")

if __name__ == "__main__":
    main()
