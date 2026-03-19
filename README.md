[![Deploy](https://img.shields.io/github/actions/workflow/status/data-to-insight/csc-map-of-the-world/deploy.yml?branch=main&style=flat-square)](https://github.com/data-to-insight/csc-map-of-the-world/actions/workflows/deploy.yml) [![Docs](https://img.shields.io/badge/docs-live-brightgreen?style=flat-square)](https://data-to-insight.github.io/csc-map-of-the-world/) [![License: MIT](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](https://choosealicense.com/licenses/mit/) [![Data refreshed](https://img.shields.io/github/last-commit/data-to-insight/csc-map-of-the-world?path=docs/data/graph_data.json&label=data%20refreshed&style=flat-square)](https://github.com/data-to-insight/csc-map-of-the-world/commits/main/docs/data/graph_data.json)



# CSC Open Data Ecosystem Map (CSC ODEM)

A structured, open-source ecosystem map for the **Children’s Social Care (CSC)** sector and searchable knowledge layer. 

This project brings together [Documentation], [Relationships], [Services], [Sector_Tools], [Rules], [Plans], [Events] using a flexible YAML-based data model and aiming for alignment with the [Smart City Concept Model (SCCM)](http://www.smartcityconceptmodel.com/) towards sector data interoperability.

It aims to support full-text search, (filtered)graph-based relations visualisation, and YAML schema validation across structured `.yml` records. Supporting documents (PDF, Markdown, HTML, Python, JS). Development is scaffolded/designed to be extensible, transparent, and Git-native.

**Current Dev Phase:** *Discovery-Alpha*  
CSC Network Map Tool & Knowledge Search available at: [data-to-insight.github.io/csc-map-of-the-world](https://data-to-insight.github.io/csc-map-of-the-world/)
---

## Project Purpose

This proof of concept(PoC) project explores how a structured, searchable map of Children’s Social Care (CSC) data, tools, and activity could support work across the sector. While exact use-cases are still emerging, our goal is to create a shared resource that brings together:

- published reports  
- pre-defined data objects  
- web data (e.g. from the DfE, local authorities, third parties)  
- sector-developed tools and frameworks  
- connected people (organisational/sector tools linked where consent given or public record)  

All of this would be made accessible through a visual or navigable interface, allowing users to explore connections between people, projects, standards, and services.

We think this could help:

- **Make relationships clearer** — between local and national CSC initiatives, policies, systems, and data sources  
- **Show who’s doing what** — helping users track new tools, updates to frameworks, or structural changes in services  
- **Bring siloed or under-the-radar work into view** — so efforts can align, build on each other, or avoid duplication  
- **Support local teams** — by contributing to a more joined-up picture of activity across the sector  

We see this as **a collaborative mapping tool**, developed potentially with input from local authority teams, analysts, service leads, academic partners, and national bodies.

---

## Features

- Full-text search across `.md`, `.pdf`, `.html`, `.py`, `.js`, `.yml`, and `.yaml` documents
- Graph-based relationship rendering using Cytoscape.js
- Normalised text extraction via Python based tools, e.g. `nltk`
- Search index + schema validation scripts
- Open standards alignment across YAML content
- Local document upload (`/docs/`) for manual additions
- GitHub integration for syncing external relevant repos/project documentation
- Modular structure that supports standalone or embedded use

---

## Project Layout

*Note: Non-UK spelling dictated by some tools.|modelling standards* 

```
/workspaces/csc-map-of-the-world-mkdocs/

├── admin_scripts/                      # Python build glue, turns YAML plus external sources into JSON artifacts for site (graph, search, crosswalk)
│   …                                   # Individual scripts handle graph_data, lite graph, source_nodes, external corpus indexing
├── data_externally_processed/          # Precomputed search corpus from PDFs etc, feeds semantic search and LLM style tools
│   ├── motw_chunks.parquet             # Text chunks table, one row per chunk, used to reconstruct context windows
│   ├── motw_index.faiss                # Vector index file, enables fast nearest neighbour search over motw_vectors
│   ├── motw_vectors.parquet            # Embeddings table, one row per chunk, mirrors motw_chunks row ids
│   └── search_index.json               # Lightweight JSON search index, exported for static site or API style search
├── data_repos/                         # Upstream Git repos pulled in, additional raw search corpora data 
│   ├── SEND-tool/                      # 
│   ├── annex-a-sen-validator-be/       # 
│   ├── nvest/                          # 
│   └── …                               # 
├── data_web/                           # External sources, supports reproducible scraping
│   ├── *.txt                           # URL manifests, define which pages get scraped for services, guidance, frameworks
│   └── …                               # Acts as configuration not content, keeps web scrape inputs versioned
├── data_yml/                           # Core SCCM metadata, single source-of-truth for graph nodes and details
│   ├── organizations/                  # ORGANIZATION entities
│   ├── relationships/                  # RELATIONSHIP entities, edge definitions, link two SCCM objects in graph_data
│   ├── services/                       # SERVICE entities
│   ├── rules/                          # RULE or GUIDANCE entities
│   ├── events/                         # EVENT entities
│   ├── resources/                      # RESOURCE entities
│   └── …                               # Other SCCM concept folders, all converge into graph_data and search indexes
├── docs/                               # MKDocs front-end (user facing)
│   ├── css/
│   │   └── styles.css                  # Custom theme tweaks, graph panel layout, font sizes, chips, filters
│   ├── data/                           # Build outputs consumed by front end JS, never hand edited in normal flow
│   │   ├── adjacency.json              # Node adjacency map, used for neighbour lookups or quick context mode hints
│   │   ├── crosswalk.json              # Id slug to page path mapping, joins YAML graph ids to MkDocs pages and URLs
│   │   ├── csc_artifacts/              # Packaged semantic search artifacts for the public site
│   │   │   ├── motw_chunks.parquet     # Deployed copy of chunks, used by notebook tooling or future on device search
│   │   │   ├── motw_index.faiss        # Deployed ANN index, supports offline or local vector queries
│   │   │   ├── motw_vectors.parquet    # Deployed embeddings, aligns with chunks, future friendly for new tools
│   │   │   └── state.json              # Metadata about the above artifacts, shapes, versions, build state
│   │   ├── degree.json                 # Node degree per id, used to size or dim nodes, supports optimisation and QA
│   │   ├── graph_data.json             # Full node and edge payload for standard graph view, richest version
│   │   ├── graph_data.lite.json        # Reduced version of graph_data, trimmed fields or nodes for faster load
│   │   ├── graph_search_index.json     # Search index focused on graph nodes, backing data for graph search ui
│   │   ├── lite_index.json             # Tiny index for lite graph, quick lookup of ids, slugs, basic labels
│   │   ├── node_details.json           # Per node detail blob, used by side panel instead of hitting YAML at runtime
│   │   ├── related_nodes.json          # Precomputed related suggestions, powers “show related” or context recommendations
│   │   ├── search_index.json           # Site wide search index, complements MkDocs default, used by search_tool.js
│   │   ├── source_nodes.dict.json      # Mapping source file or source id to node list as dict form, handy for tooling
│   │   ├── source_nodes.json           # Canonical source to nodes mapping, used by optimisation and QA views
│   │   └── source_nodes.list.json      # List oriented variant of source_nodes, easier to scan in dev and scripts

│   ├── index.md                        # Main landing page
│   ├── explore.md                      # 
│   ├── data_source_optimisation.md     # D2I/Dev backend source data running design notes
│   ├── dev_log.md                      # D2I/Dev diary
│   ├── graph_filtering_guidance.md     # Explains graph filters, tags, types, gives context for explorer.js behaviour

│   ├── form/
│   │   └── index.html                  # Live entity submission form, enables export YAML aligned to data_yml structures
│   ├── imgs/
│   │   └── MotW-Infographic.png        # High level explainer for sharing
│   ├── js/                             # Browser logic layer that consumes docs/data JSON
│   │   ├── explorer.js                 # Main explore experience, binds filters and search ui to graph JSON endpoints
│   │   ├── related_nodes.json          # Local static related nodes data or legacy copy, quick lookup in JS context
│   │   ├── render_graph_lite.js        # Cytoscape initialiser for lite graph, consumes graph_data.lite and lite_index
│   │   ├── render_graph_standard.js    # Full graph renderer, uses graph_data, node_details, degree, crosswalk
│   │   └── search_tool.js              # Custom search ui logic, hits graph_search_index and search_index JSON files

├── mkdocs.yml                          # MkDocs site config          
├── setup.sh                            # Bootstrap script, installs requirements, prep local

```

---

## Getting Started (Dev + CLI)

### Env Setup

```bash
./setup.sh  # one-time setup (pip install, nltk, etc.)
```

### Run local

```bash
mkdocs serve
# or if port conflict:
mkdocs serve --dev-addr=0.0.0.0:8001
# or 
python -m mkdocs serve

```


### Validate YAML records

```bash
python admin_scripts/validate_yml_objects.py
```
Ensure the core YML files are valid before running subsequent update processes. 

### Rebuild Search Index + Graph

```bash
python admin_scripts/build_main_search_index.py
```
Re-create/update the search index file from available data. 

```bash
python admin_scripts/build_cytoscape_json.py
```
Re-create/update the graph/network diagram index file from available data. 

```bash
python /workspaces/csc-map-of-the-world/admin_scripts/admin-re-build-sources-page.py
```
Refresh the sources page with any refreshed files or sources. Note that this overwrites the sources.md page. 


### Clean up

```bash
rm -rf site/
```
Clean re-build of mkdocs site folder. Rarely needed but in case. 

---

## Tech Stack

###  Python Stack
| Purpose             | Tools                                                                  |
| ------------------- | ---------------------------------------------------------------------- |
| YAML parsing        | `PyYAML`, `ruamel.yaml`                                                |
| PDF parsing         | `pdfplumber`, `PyMuPDF`                                                |
| HTML scraping       | `requests`, `BeautifulSoup4`                                           |
| NLP & text cleaning | `nltk` (stopwords, lemmatisation), `spacy`, `transformers`             |
| Keyword filtering   | `scikit-learn` (`CountVectorizer` for frequency-based filtering)       |
| Parquet support     | `fastparquet` (used with `pandas.to_parquet`)                          |
| Data handling       | `pandas`, `json`, `os`, `re`, `datetime`, `hashlib`                    |
| File handling       | `pathlib`, `glob`, `shutil`, `unicodedata`                             |
| Indexing (planned)  | `lunr`, `duckdb`, custom JSON-based indexing                           |
| Graph generation    | `networkx`, `pyvis`, `cytoscape.js` (via JSON export)                  |
| Markdown generation | `markdown`, `mkdocs`, `mkdocs-material`, `pandoc` (for `.docx` export) |
| Visualisation UI    | `streamlit`, `stlite`, `Cytoscape.js`                                  |


### Frontend / Docs / Search
| Purpose        | Tools                                                               |
| -------------- | ------------------------------------------------------------------- |
| Documentation  | `MkDocs`, `Material for MkDocs`, `mkdocs.yml`, `mkdocs-private.yml` |
| Hosting        | GitHub Pages (`gh-pages`, `GitHub Actions`)                         |
| Graph frontend | `Cytoscape.js` (embedded via JS inside MkDocs site)                 |
| Static search  | `list.js`, planned integration of `lunr.js`                         |


---

## D2I Dev Notes

- YAML objects (attempt to)follow SCCM concepts: `OBJECT`, `AGENT`, `SERVICE`, `EVENT`, `COLLECTION`, `OBSERVATION`, `RELATIONSHIP`, etc.
- Each YAML file should include a `name`, `description`, and optional `@type`, `tags`, `related_to`, `source_url`, etc.
- `search_index.json` and `graph_data.json` are regenerated via scripts and used by the frontend
- Folder structure matters: new categories of YAML content should be placed in their own folder inside `/data_yml/`
- Scraped or imported documentation (e.g. Ofsted inspections, SEND guidance) lives in `/docs/` or `/data_published/`

---

## D2I Dev/future work

Aside the ongoing dev/fixes... 

**To do notes**
- already integrated the repo clone into index compile, need the same for web scrape 
- data_published needs sub structure to aid management - or an index/tracking file for ease of over sight. 
- data_published needsa dedup?
- tidy up admin script process flow, need one refresh all script

- SCCM-compliant exports
- Live data ingress to maintain updates, via direct LA/DfE urls or alternative
- Enhanced relationship modelling (multi-level RELATIONSHIP, EVENT chains)
- Editable front-end (e.g. via YAML form editor) or enabling direct YAML contributions
- Scaled search index using DuckDB-based backend or further optimised search index method(s)
- Expanded integration across D2I GitHub repos via cross-referencing tags

- Consider how best to model *temporal relationships* (e.g. `start_date`, `end_date`, `published`)
- Decide on storing personal names (e.g. contributors, collaborators) in `AGENT` vs anonymised role-based entries
- Test load/search performance as data grows (browser-side memory vs backend streaming)
- Can this stack/structure and git file allowance sufficiently scale up..... 

---

## Smart City Concept Model (SCCM) 

Possible mapping examples within this tool, these and others currently in internal review. 

| SCCM Concept (Category)                                                                 | Suggested example(s) (in progress)                                                                                     | 
|-----------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| [Community](http://www.smartcityconceptmodel.com/index.php?Action=ShowConcept&Id=161)   | South East fostering cluster                                                                                            |
| [Documentation](http://www.smartcityconceptmodel.com/index.php?Action=ShowConcept&Id=183) | [CSC Independent Review](https://assets.publishing.service.gov.uk/media/640a17f28fa8f5560820da4b/Independent_review_of_children_s_social_care_-_Final_report.pdf) |
| [Events](http://www.smartcityconceptmodel.com/index.php?Action=ShowConcept&Id=164)        | *Children’s Social Care Review*, *ILACS Inspections*, *Public Inquiries*                                                |
| [Organization](http://www.smartcityconceptmodel.com/index.php?Action=ShowConcept&Id=160) | [Data to Insight](https://www.datatoinsight.org/), [LIIA](https://www.liia.london/)                                     |
| [Persons](http://www.smartcityconceptmodel.com/index.php?Action=ShowConcept&Id=159)      | Organisational/sector tools linked where consent given or public record                                                 |
| [Plans](http://www.smartcityconceptmodel.com/index.php?Action=ShowConcept&Id=177)        | *Kinship Care Strategy*, *Children’s Social Care National Framework*                                                    |
| [Relationships](http://www.smartcityconceptmodel.com/index.php?Action=ShowModel&Id=10)   | LA-1 ↔ Supports ↔ SSD Tests, DfE ↔ Pilots ↔ API Data Flows                                                               |
| [Rules](http://www.smartcityconceptmodel.com/index.php?Action=ShowConcept&Id=175)        | Statutory Guidance, *Keeping Children Safe in Education 2025*                                                           |
| [Sector Tools](http://www.smartcityconceptmodel.com/index.php?Action=ShowConcept&Id=166) | [PATCH](https://www.datatoinsight.org/patch), ChAT                                                                      |
| [Services](http://www.smartcityconceptmodel.com/index.php?Action=ShowConcept&Id=169)     |                                                                                                                         |




© Data to Insight — sector-driven, open knowledge 

