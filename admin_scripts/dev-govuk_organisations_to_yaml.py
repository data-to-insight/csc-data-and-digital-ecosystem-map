#!/usr/bin/env python3
# ./admin-scripts/dev-govuk_organisations_to_yaml.py

"""

Fetch GOV.UK orgs API data and write a yaml file per organisation slug

Support:
- basic schema for organisation yml
- motw schema for richer MapOfTheWorld-style organisation yaml
- opt separate relationship yaml files derived from documented GOV.UK org links
- opt crosswalk csv export
- configurable word separator for generated identifiers and filenames:
    dash       -> government-digital-service
    underscore -> government_digital_service
- configurable name style:
    human      -> keeps readable names, for example "Government Digital Service"
    identifier -> makes name use the same generated identifier style as slug

E.g.
--------
# All orgs, MOTW schema, underscore identifiers, relationship files, crosswalk CSV
python govuk_organisations_to_yaml.py \
  --all \
  --schema motw \
  --word-separator underscore \
  --name-style identifier \
  --output-dir data_yml/organizations \
  --emit-relationship-files \
  --relationship-dir data_yml/relationships \
  --emit-crosswalk-csv \
  --crosswalk-path data_yml/relationships_crosswalk.csv
"""

# # orgs output
# @type: ORGANIZATION
# name: government_digital_service
# slug: government_digital_service
# label: Government Digital Service

# # relationships output
# @type: RELATIONSHIP
# name: government_digital_service_supersedes_geospatial_commission
# slug: government_digital_service_supersedes_geospatial_commission
# label: Government Digital Service supersedes_organisation geospatial_commission
# source: government_digital_service
# target: geospatial_commission
# relationship_type: supersedes_organisation

# # cross walk output
# relationship_slug,relationship_file,source,target,relationship_type,source_type,target_type,source_label,target_label,source_org_api_url,target_org_api_url,target_org_web_url
# government_digital_service_supersedes_geospatial_commission,government_digital_service_supersedes_geospatial_commission.yml,government_digital_service,geospatial_commission,supersedes_organisation,ORGANIZATION,ORGANIZATION,government_digital_service,geospatial_commission,https://www.gov.uk/api/organisations/government-digital-service,https://www.gov.uk/api/organisations/geospatial-commission,https://www.gov.uk/government/organisations/geospatial-commission


# python ./admin_scripts/govuk_organisations_to_yaml.py \
#   --all \
#   --schema motw \
#   --word-separator underscore \
#   --name-style identifier \
#   --output-dir data_yml/organizations \
#   --emit-relationship-files \
#   --relationship-dir data_yml/relationships \
#   --emit-crosswalk-csv \
#   --crosswalk-path data_yml/relationships_crosswalk.csv


from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urlparse

import requests
import yaml
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://www.gov.uk"
ORGS_LIST_URL = f"{BASE_URL}/api/organisations"

RELATIONSHIP_SPECS = {
    "parent_organisations": {
        "relationship_type": "has_parent_organisation",
        "filename_token": "parent",
        "description_template": "{source_label} has parent organisation {target_label}.",
    },
    "child_organisations": {
        "relationship_type": "has_child_organisation",
        "filename_token": "child",
        "description_template": "{source_label} has child organisation {target_label}.",
    },
    "superseded_organisations": {
        "relationship_type": "supersedes_organisation",
        "filename_token": "supersedes",
        "description_template": "{source_label} supersedes organisation {target_label}.",
    },
    "superseding_organisations": {
        "relationship_type": "superseded_by_organisation",
        "filename_token": "superseded_by",
        "description_template": "{source_label} is superseded by organisation {target_label}.",
    },
}


# ----------------------------
# CLI
# ----------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch GOV.UK organisations and write yaml files"
    )

    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--slug", help="Single organisation slug, for example government-digital-service")
    scope.add_argument("--all", action="store_true", help="Fetch all organisations")

    parser.add_argument(
        "--schema",
        choices=["basic", "motw"],
        default="basic",
        help="Organisation output schema, default: basic",
    )

    parser.add_argument(
        "--output-dir",
        default="organisations_yaml",
        help="Directory for organisation yaml files, default: organisations_yaml",
    )

    parser.add_argument(
        "--emit-relationship-files",
        action="store_true",
        help="Also emit separate yaml files for organisation-to-organisation relationships",
    )

    parser.add_argument(
        "--relationship-dir",
        default=None,
        help="Directory for relationship yaml files, default: <output-dir>/relationships",
    )

    parser.add_argument(
        "--emit-crosswalk-csv",
        action="store_true",
        help="Also emit a CSV crosswalk of source,target,relationship_type and related metadata",
    )

    parser.add_argument(
        "--crosswalk-path",
        default=None,
        help="Path for crosswalk CSV, default: <output-dir>/relationships_crosswalk.csv",
    )

    parser.add_argument(
        "--word-separator",
        choices=["dash", "underscore"],
        default="dash",
        help="Separator used in generated slugs, identifiers and filenames, default: dash",
    )

    parser.add_argument(
        "--name-style",
        choices=["human", "identifier"],
        default="human",
        help="Whether generated name fields stay human-readable or use machine identifiers, default: human",
    )

    return parser.parse_args()


# ----------------------------
# HTTP / API
# ----------------------------

def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "govuk-organisations-yaml/1.3 (+https://www.gov.uk/)",
            "Accept": "application/json",
        }
    )

    retries = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_json(session: requests.Session, url: str, timeout: int = 30) -> Any:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_all_organisations(session: requests.Session) -> List[Dict[str, Any]]:
    payload = get_json(session, ORGS_LIST_URL)

    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return payload["results"]

    if isinstance(payload, list):
        return payload

    raise ValueError("Unexpected response shape from organisations list endpoint")


def fetch_organisation_by_slug(session: requests.Session, slug: str) -> Dict[str, Any]:
    payload = get_json(session, f"{ORGS_LIST_URL}/{slug}")

    if not isinstance(payload, dict):
        raise ValueError(f"Unexpected response shape for slug '{slug}'")

    return payload


# ----------------------------
# Helpers
# ----------------------------

def separator_char(word_separator: str) -> str:
    return "-" if word_separator == "dash" else "_"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def last_path_segment(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    path = urlparse(url).path.strip("/")
    if not path:
        return None
    return path.split("/")[-1]


def safe_identifier(value: str, word_separator: str) -> str:
    sep = separator_char(word_separator)
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", sep, value)
    value = re.sub(r"[-_]+", sep, value)
    value = re.sub(rf"{re.escape(sep)}{{2,}}", sep, value).strip(sep)
    return value or "unknown"


def to_identifier_from_title(title: Optional[str], word_separator: str, fallback: str = "unknown") -> str:
    if not title:
        return fallback
    return safe_identifier(title, word_separator)


def file_stem(value: str, word_separator: str) -> str:
    return safe_identifier(value, word_separator)


def remove_none_and_empty(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned = {
            k: remove_none_and_empty(v)
            for k, v in value.items()
            if v is not None
        }
        return {k: v for k, v in cleaned.items() if v not in ({}, [], "", None)}

    if isinstance(value, list):
        cleaned = [remove_none_and_empty(v) for v in value if v is not None]
        return [v for v in cleaned if v not in ({}, [], "", None)]

    return value


def relation_summary(items: List[Dict[str, Any]], word_separator: str) -> List[Dict[str, Optional[str]]]:
    out: List[Dict[str, Optional[str]]] = []
    for item in items or []:
        raw_slug = last_path_segment(item.get("id"))
        out.append(
            {
                "slug": safe_identifier(raw_slug or "unknown", word_separator),
                "api_url": item.get("id"),
                "web_url": item.get("web_url"),
            }
        )
    return out


def relation_slugs(items: List[Dict[str, Any]], word_separator: str) -> List[str]:
    out: List[str] = []
    for item in items or []:
        raw_slug = last_path_segment(item.get("id"))
        if raw_slug:
            out.append(safe_identifier(raw_slug, word_separator))
    return out


def org_raw_slug(org: Dict[str, Any]) -> str:
    details = org.get("details", {}) or {}
    return details.get("slug") or last_path_segment(org.get("id")) or "unknown-organisation"


def org_slug(org: Dict[str, Any], word_separator: str) -> str:
    return safe_identifier(org_raw_slug(org), word_separator)


def org_label(org: Dict[str, Any]) -> str:
    return org.get("title") or org_raw_slug(org)


def org_name_value(org: Dict[str, Any], word_separator: str, name_style: str) -> str:
    if name_style == "identifier":
        return org_slug(org, word_separator)
    return org_label(org)


def write_yaml_file(data: Dict[str, Any], output_dir: Path, filename: Optional[str] = None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        stem = str(data.get("slug") or data.get("name") or "unknown")
        filename = f"{stem}.yml"

    path = output_dir / filename
    cleaned = remove_none_and_empty(data)

    yaml_text = yaml.safe_dump(
        cleaned,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=1000,
    )

    path.write_text(yaml_text, encoding="utf-8")
    return path


# ----------------------------
# Organisation transforms
# ----------------------------

def basic_schema(org: Dict[str, Any], word_separator: str, name_style: str) -> Dict[str, Any]:
    details = org.get("details", {}) or {}
    slug = org_slug(org, word_separator)
    label = org_label(org)
    name = org_name_value(org, word_separator, name_style)

    data = {
        "name": name,
        "slug": slug,
        "label": label,
        "format": org.get("format"),
        "web_url": org.get("web_url"),
        "api_url": org.get("id"),
        "updated_at": org.get("updated_at"),
        "analytics_identifier": org.get("analytics_identifier"),
        "details": {
            "abbreviation": details.get("abbreviation"),
            "logo_formatted_name": details.get("logo_formatted_name"),
            "organisation_brand_colour_class_name": details.get("organisation_brand_colour_class_name"),
            "organisation_logo_type_class_name": details.get("organisation_logo_type_class_name"),
            "govuk_status": details.get("govuk_status"),
            "govuk_closed_status": details.get("govuk_closed_status"),
            "closed_at": details.get("closed_at"),
            "content_id": details.get("content_id"),
            "raw_govuk_slug": org_raw_slug(org),
        },
        "parent_organisations": relation_summary(org.get("parent_organisations", []), word_separator),
        "child_organisations": relation_summary(org.get("child_organisations", []), word_separator),
        "superseded_organisations": relation_summary(org.get("superseded_organisations", []), word_separator),
        "superseding_organisations": relation_summary(org.get("superseding_organisations", []), word_separator),
    }
    return data


def motw_schema(org: Dict[str, Any], word_separator: str, name_style: str) -> Dict[str, Any]:
    details = org.get("details", {}) or {}
    slug = org_slug(org, word_separator)
    label = org_label(org)
    name = org_name_value(org, word_separator, name_style)
    abbreviation = details.get("abbreviation")
    govuk_status = details.get("govuk_status")

    tags = [
        "govuk",
        "uk-government",
        "organization",
    ]

    if govuk_status:
        tags.append(f"govuk-status:{govuk_status}")

    if org.get("format"):
        tags.append(f"govuk-format:{safe_identifier(str(org['format']), word_separator)}")

    aliases: List[str] = []
    if abbreviation and abbreviation != label:
        aliases.append(abbreviation)

    return {
        "@type": "ORGANIZATION",
        "name": name,
        "slug": slug,
        "label": label,
        "aliases": aliases,
        "website": org.get("web_url"),
        "source": org.get("id"),
        "tags": tags,
        "external_ids": {
            "govuk_content_id": details.get("content_id"),
            "govuk_analytics_identifier": org.get("analytics_identifier"),
            "govuk_slug": org_raw_slug(org),
        },
        "govuk": {
            "title": org.get("title"),
            "format": org.get("format"),
            "updated_at": org.get("updated_at"),
            "abbreviation": abbreviation,
            "logo_formatted_name": details.get("logo_formatted_name"),
            "organisation_brand_colour_class_name": details.get("organisation_brand_colour_class_name"),
            "organisation_logo_type_class_name": details.get("organisation_logo_type_class_name"),
            "govuk_status": govuk_status,
            "govuk_closed_status": details.get("govuk_closed_status"),
            "closed_at": details.get("closed_at"),
        },
        "relationships": {
            "parent_organisations": relation_slugs(org.get("parent_organisations", []), word_separator),
            "child_organisations": relation_slugs(org.get("child_organisations", []), word_separator),
            "superseded_organisations": relation_slugs(org.get("superseded_organisations", []), word_separator),
            "superseding_organisations": relation_slugs(org.get("superseding_organisations", []), word_separator),
        },
        "provenance": {
            "source_system": "GOV.UK Organisations API",
            "api_url": org.get("id"),
            "retrieved_at": utc_now_iso(),
        },
    }


def convert_org(org: Dict[str, Any], schema: str, word_separator: str, name_style: str) -> Dict[str, Any]:
    if schema == "basic":
        return basic_schema(org, word_separator, name_style)
    if schema == "motw":
        return motw_schema(org, word_separator, name_style)
    raise ValueError(f"Unsupported schema: {schema}")


# ----------------------------
# Relationship emission
# ----------------------------

def build_relationship_record(
    source_org: Dict[str, Any],
    target_ref: Dict[str, Any],
    relationship_field: str,
    word_separator: str,
    name_style: str,
) -> Optional[Dict[str, Any]]:
    spec = RELATIONSHIP_SPECS[relationship_field]

    source_slug = org_slug(source_org, word_separator)
    source_label = org_label(source_org)

    target_raw_slug = last_path_segment(target_ref.get("id"))
    if not target_raw_slug:
        return None

    target_slug = safe_identifier(target_raw_slug, word_separator)
    target_label = target_slug if name_style == "identifier" else target_raw_slug.replace("-", " ").replace("_", " ")

    relationship_type = spec["relationship_type"]
    filename_token = safe_identifier(spec["filename_token"], word_separator)

    rel_slug = separator_char(word_separator).join([source_slug, filename_token, target_slug])
    rel_name = rel_slug if name_style == "identifier" else f"{source_label} {relationship_type} {target_slug}"

    return {
        "@type": "RELATIONSHIP",
        "name": rel_name,
        "slug": rel_slug,
        "label": f"{source_label} {relationship_type} {target_slug}",
        "description": spec["description_template"].format(
            source_label=source_label,
            target_label=target_label,
        ),
        "source": source_slug,
        "target": target_slug,
        "relationship_type": relationship_type,
        "source_type": "ORGANIZATION",
        "target_type": "ORGANIZATION",
        "tags": [
            "govuk",
            "uk-government",
            "relationship",
            f"relationship:{relationship_type}",
        ],
        "provenance": {
            "source_system": "GOV.UK Organisations API",
            "source_org_api_url": source_org.get("id"),
            "target_org_api_url": target_ref.get("id"),
            "target_org_web_url": target_ref.get("web_url"),
            "retrieved_at": utc_now_iso(),
        },
    }


def iter_relationship_records(
    org: Dict[str, Any],
    word_separator: str,
    name_style: str,
) -> Iterable[Dict[str, Any]]:
    for field_name in RELATIONSHIP_SPECS.keys():
        items = org.get(field_name, []) or []
        for item in items:
            rel = build_relationship_record(org, item, field_name, word_separator, name_style)
            if rel is not None:
                yield rel


def relationship_filename(rel: Dict[str, Any]) -> str:
    return f"{rel['slug']}.yml"


# ----------------------------
# Crosswalk CSV
# ----------------------------

def write_crosswalk_csv(
    rows: List[Dict[str, Any]],
    csv_path: Path,
) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "relationship_slug",
        "relationship_file",
        "source",
        "target",
        "relationship_type",
        "source_type",
        "target_type",
        "source_label",
        "target_label",
        "source_org_api_url",
        "target_org_api_url",
        "target_org_web_url",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def crosswalk_row_from_relationship(rel: Dict[str, Any]) -> Dict[str, Any]:
    label = rel.get("label", "")
    source_label = ""
    target_label = ""

    if rel.get("description"):
        source_label = rel["description"]

    # Better to keep direct values where possible
    return {
        "relationship_slug": rel.get("slug"),
        "relationship_file": f"{rel.get('slug')}.yml",
        "source": rel.get("source"),
        "target": rel.get("target"),
        "relationship_type": rel.get("relationship_type"),
        "source_type": rel.get("source_type"),
        "target_type": rel.get("target_type"),
        "source_label": rel.get("source"),
        "target_label": rel.get("target"),
        "source_org_api_url": rel.get("provenance", {}).get("source_org_api_url"),
        "target_org_api_url": rel.get("provenance", {}).get("target_org_api_url"),
        "target_org_web_url": rel.get("provenance", {}).get("target_org_web_url"),
    }


# ----------------------------
# Main
# ----------------------------

def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    relationship_dir = Path(args.relationship_dir) if args.relationship_dir else output_dir / "relationships"
    crosswalk_path = Path(args.crosswalk_path) if args.crosswalk_path else output_dir / "relationships_crosswalk.csv"

    session = build_session()

    try:
        if args.slug:
            orgs = [fetch_organisation_by_slug(session, args.slug)]
        else:
            orgs = fetch_all_organisations(session)

        org_count = 0
        rel_count = 0
        seen_relationship_slugs: Set[str] = set()
        crosswalk_rows: List[Dict[str, Any]] = []

        for org in orgs:
            converted = convert_org(
                org=org,
                schema=args.schema,
                word_separator=args.word_separator,
                name_style=args.name_style,
            )
            org_filename = f"{file_stem(converted['slug'], args.word_separator)}.yml"
            write_yaml_file(converted, output_dir, filename=org_filename)
            org_count += 1

            if args.emit_relationship_files or args.emit_crosswalk_csv:
                for rel in iter_relationship_records(
                    org=org,
                    word_separator=args.word_separator,
                    name_style=args.name_style,
                ):
                    rel_slug = str(rel["slug"])
                    if rel_slug in seen_relationship_slugs:
                        continue

                    seen_relationship_slugs.add(rel_slug)

                    if args.emit_relationship_files:
                        write_yaml_file(rel, relationship_dir, filename=relationship_filename(rel))
                        rel_count += 1

                    if args.emit_crosswalk_csv:
                        crosswalk_rows.append(crosswalk_row_from_relationship(rel))

        if args.emit_crosswalk_csv:
            write_crosswalk_csv(crosswalk_rows, crosswalk_path)

        messages = [f"Wrote {org_count} organisation yaml files to: {output_dir}"]

        if args.emit_relationship_files:
            messages.append(f"Wrote {rel_count} relationship yaml files to: {relationship_dir}")

        if args.emit_crosswalk_csv:
            messages.append(f"Wrote {len(crosswalk_rows)} crosswalk rows to: {crosswalk_path}")

        print("\n".join(messages))
        return 0

    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        print(f"HTTP error: {status}", file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(f"Request error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())