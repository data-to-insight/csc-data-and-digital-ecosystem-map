# MapOfTheWorld development log v4.2  

Short notes so others can see journey, also as reminder for me :) - might use this for some later reflective write-up work. 


## 2026-03-20

Post review and agreement from AH with regards pivoting approach on the project's unpinning standards adherence, am definitely moving to a revised approach in terms of the underpinning yml base structure/attributes. atm this impacts the graph visualisation, all supporting data structures feeding those and the codebase that generates this. Info panel generation also. But because i'd not yet transitioned the other data ingress routes into the yml structure, we dont have to contend with this. But initial work is now to scope out how much time/effort needed to make this pivot, likewise whether to create our own bespoke standard to ease overheads - create a best fit instead of adherence. Intend to still provide the mechanisms to record adherence to SCCM - but it's clear that for our needs on this [SCCM](http://www.smartcityconceptmodel.com/) is not a good fit(alone).

refs:
https://www.gov.uk/government/publications/open-standards-principles/open-standards-principles
https://www.gov.uk/government/publications/data-sharing-governance-framework/data-sharing-governance-framework
https://www.w3.org/TR/skos-reference/
https://www.w3.org/TR/vocab-dcat-3/#Property:data_service_endpoint_url

Possible:
https://coda.io/@savvi/welcome/the-whole-concept-model-277

## 2026-03-19

Culmination of complete review and rethink in regards the SCCM standard/model application and how it might be preventing both progress and form a blocker for developing out, particularly in the currently limited 'relationships' definitions that are not a good fit for our onward aims. 

Some minor re-work of content, but also major renaming in line with shift in standards use:
*CSC Data and Digital Ecosystem Map (CSC DDEM)
A structured, open-source ecosystem map for the Children’s Social Care(CSC) sector combining visualised ecosystem map with searchable meta/knowledge layer with data ingress from both published source documentation and sector knowledge. The combined ecosystem resource aims to provide sector colleagues with a resource for collaboration, shared knowledge around otherwise siloed relevant data project work*


## 2026-03-17

Built a quick poc to pull directly rfom https://docs.publishing.service.gov.uk/manual/organisations-api.html straight into our motw yml format. Works, incl the reltionships but not an obvious way to filter on relevant orgs within that data. Also alot less than expected with just 21 coming through (git repo is at : https://github.com/alphagov/govuk-developer-docs). 
Also possible use-case for https://github.com/x-govuk/govuk-services-list

## 2026-03-11

- Added missing url links into some of JB new org ymls. MAde me wonder about having key roles(DCS) in there not just 'people' - but also how we might reasonably/cheaply obtain this into the meta data. 
This week was also one where i came accross similar work e.g. 
- https://ukgov-network-graph.lovable.app/
- https://graphcommons.com/graphs/d6b35ab0-90fb-4cef-a00a-3ce711f9f4c4
and a potential game changer within : https://docs.publishing.service.gov.uk/manual/organisations-api.html

Realised that we still have the issue of node size not reflecting the importance/link levels. But also... cant recall how/where i set this. 

## 2026-03-04

- back at it. Added some recent new objects/relations from JB

---

## 2026-01-20

- Having to remind myself how the backend .pynb process actually works! Need some better notes/documentation somewhere on a simple level and this despite the dev diary and other notes made already. Possible re-think?  Thank my lucky stars for my simplified admin-ORCHASTRATOR-rebuild_all_assets.py
- Some further objects and relations from JB updloaded. Some minoir yml corrections needed in order to run orchastrator (e.g. space afrer : colons)
- Still see some panel inconsistencies and the slug is still appearing as a secondary heading under the title... i thought i'd dropped this in the last pull? 
- first wider team collab session AH, JB, A, RH - set up recurring sesisons to move this forward.

---

## 2026-01-14

- Rethinking what data points 'should' be included in the yml files. Need to establish baselines here - forum collab/collectively?  
- Some further work adding primarily new org objects, with some connected relations (JB)  
- Fixed non-disappearing/persistent info panel on full-network page  
- centralised the info panel formatting... trying to remove some of the inconsistencies seen between the 3 instances of this  

---

## 2025-12-02  

- Back on project after long gap, many log entries missing  
- Fixed explorer search not firing  
- Stopped explorer showing full results list after selection, now list hides once node picked  
- Explorer info panel now pulls full data from `node_details.json`, not just minimal fields  
- Fixed duplicated edges when pressing add 1 hop repeatedly, now track bidirectional edge index  
- Added 2 hops option and made explorer buttons more visible with extra CSS  
- Alison refreshed intro text and infographic for landing page  
- Added content to `data_source_optimisation.md`  
- Realised back end flow now fuzzy in head, note to write short idiot guide for self, including external notebook, `search_index.json`, `state.json`, `csc_artifacts`, `docs/data`, parquet and faiss refresh  
- Timed `network_fullscreen.md` graph load, roughly 50 seconds off peak, plan small warning on page  
- Updated `setup.sh` and `devcontainer.json` so Python and `mkdocs serve` work in Codespaces without manual venv setup  

---

## 2025-11-28  

- Converted public intro copy for MapOfTheWorld into markdown  
- Added image include for infographic on main project page  
- Committed staged docs changes from feature branch into `main`  

---

## 2025-11 overview  

- Reviewed JSON size and limits, keep only minified JSON in `docs/data` for deploy  
- Keep pretty JSON locally for debugging and diffs  
- Standardised base URL safe fetch pattern using `new URL(relPath, document.baseURI)`  
- Documented split JSON contract and local rebuild steps for contributors  

---

## 2025-10 overview  

- Reached v4.2, search and graph load feel stable, payload trimmed  
- Removed client side GitHub API calls for feedback, now ship `docs/data/feedback-items.json`  
- Locked label policy. Edge labels hidden until zoom threshold, above roughly 5k nodes labels at load too risky  
- Added preload hook so demo pages can embed `window.MOTW.graphStd`, default still fetch from `docs/data` for caching  
- Tweaked scraper filenames, stripped stopwords from stems, optional `-u<hash>` for collision control, no double underscores, avoid noisy topic prefixes  

---

## 2025-09 overview  

- Adopted split JSON pattern  
  - `docs/data/graph_data.json` minimal nodes and edges for Cytoscape  
  - `docs/data/crosswalk.json` ids, slugs, page URLs  
  - `docs/data/degree.json` for seeded staged load and ordering  
  - `docs/data/related_nodes.json` optional suggestions  
  - `docs/data/search_index.json` compact index for site search  
- Kept node fields tight, mainly `slug`, `tags`, `summary`, `search_blob`  
- Added Choices.js type filter and context mode checkbox to keep neighbours visible while filtering  
- Moved heavy processing out of GitHub Actions, now build JSON locally in Python then commit, Pages only serves static files  

---

## 2025-08 overview  

- Switched fully to SCCM aligned YAML as source of truth  
  - Types include ORGANIZATION, SERVICE, EVENT, PLAN, RULE, RESOURCE, PERSON, RELATIONSHIP  
- Wrote Python builders to emit small artefacts only  
  - `docs/data/graph_data.json` for render  
  - `docs/data/crosswalk.json` for lookups  
  - Pretty versus minified toggle via `GRAPH_MINIFY`  
- Replaced hover card with side panel version 2, lighter DOM work, clearer field bag  
- Improved search, free text plus `tag:` and `type:` operators, debounced input, URL state persisted  
- Edges start in haystack style for speed, switch to bezier when zoomed in  
- Edge labels off by default, show only after useful zoom, labels at load killed frame rate  
- Isolated degree 0 nodes placed in compact grid along bottom, keeps layout stable  
- Staged loader, show high degree organisations first, then stream more nodes and edges in batches, status chip shows progress  

---

## 2025-08-06  

- Revisited SAVVI model and checked fit against SCCM  
- Decided to stay with SCCM for MapOfTheWorld  
- Scoped dynamic filter for RELATIONSHIP Source field by source type, planned helper script change  

---

## 2025-08-05  

### Input form logic with YAML export  

- Finalised static HTML form for new MapOfTheWorld entries  
- Form supports `@type` values from SCCM model, including ORGANIZATION, SERVICE, EVENT, PLAN, COLLECTION, PERSON, RESOURCE, RELATIONSHIP  
- Each type has its own field section, shown or hidden when type changes  
- RELATIONSHIP block includes source type dropdown so `relationship_type` options filter correctly  
- Added grey placeholder examples for multi value fields, for example collaborators, related entities, interests, delivery partners  
- Placeholders stripped from YAML output if unchanged  
- On `@type` change, YAML output box cleared so entries do not bleed across  

### Implementation notes  

- Form uses plain HTML, CSS and vanilla JavaScript plus `js-yaml` for YAML serialisation  
- Served directly from repo, fully static, no build step, matches GitHub Pages model  
- YAML output fits Git based workflow, contributors can download file or later raise pull request  

### Problems encountered  

- Type specific sections initially not appearing, only ORGANIZATION and RELATIONSHIP worked, fixed by applying `toggleTypeSections()` on load and on change  
- Generate YAML button originally acted like form submit and cleared content, fixed by preventing default submit behaviour  
- Some type specific fields missing from YAML, reintroduced full per type mapping when building object  
- Placeholder values leaked into YAML, fixed with `cleanList()` and `cleanTextList()` utilities to strip placeholder text  

---

## 2025-08-01  

### Mailto links, devlog structure, public dev log  

- Revised mailto link for suggest improvement or fix, easier for direct feedback  
- Defined structure for this dev log, hybrid of dev log and changelog  
- Skipped tags and automation for now, markdown fast enough to edit by hand  

---

## 2025-07 overview  

- Set aim, searchable visual map of people, projects, rules, services, hosted as static site  
- Early build used single large JSON with everything, worked up to roughly two thousand nodes then stalled, memory churn and long time to first paint  
- Chose SCCM aligned YAML for core data, decided against Parquet on Pages, keep Parquet and faiss local only  
- Submission form matured, type specific fields and RELATIONSHIP block with dynamic options  

---

## 2025-07-31  

### Cytoscape class filters and stlite graph fixes  

- Found bug where class based filters did not apply on page load  
- Root cause, class assignment lagged layout render, simple `setTimeout` after layout fixed it  
- Fixed mismatch in hard coded colours and class names in legend, ORGANIZATION nodes no longer show grey due to casing drift  

---

## 2025-07-30  

### Static legend and sources listing  

- Dynamic legend proved fragile when class names drifted from type names  
- Rebuilt legend as static block with known entity types such as ORGANIZATION, SERVICE, PERSON with fixed colours  
- Filter defaults now apply on load and legend starts collapsed  
- Designed Python script to scan `data_yml` and other folders and build `docs/sources.md`, table per source type, ready for later refinement  

---

## 2025-07-29  

### YAML errors and edge failures in Cytoscape build  

- Hit YAML error during `admin-build_cytoscape_json.py`, single malformed file broke whole build  
- Noticed edges skipped because of missing nodes, traced to ID naming mismatches  
- Rebuilt broken relationship YAML from working template, fixed missing edges  
- Reinforced need for stricter YAML validation around relationships  

---

## 2025-07-22 to 2025-07-26  

### External data inclusion and web scraping  

- Decided to include external web content, for example PDFs, guidance, reports  
- Designed approach to store scraped artefacts under `data_web/` with YAML metadata for indexing  
- Early blockers, inconsistent text extraction from some GOV.UK PDFs and odd header parsing in `.txt` and `.pdf` sources  

---

## 2025-07-19  

### Pivot from stlite to MkDocs with custom JS  

- Tried several iterations of interactive graphs in stlite, repeated issues with modules and layout timing  
- Cytoscape.js often failed to load or broke quietly because of Pyodide and import limits  
- stlite felt too fragile for graph exploration with filters, tooltips, legend controls  
- Decided to move to MkDocs as primary frontend and embed custom HTML plus JavaScript components instead  
- Static MkDocs base gave better search integration, reusable components and cleaner GitHub Pages hosting  

---

## 2025-07-18  

### Migration to stlite for browser hosting  

- Earlier step shifted from standard Streamlit to stlite so app could run in browser on GitHub Pages  
- Removed unsupported modules such as `pyvis`, `Path(__file__)` usage and Parquet I/O  
- Rebuilt visualisation to use JSON plus embedded Cytoscape.js in HTML  

---

## 2025-07-17  

### Parquet removal and browser based frontend  

- Adapted original Streamlit app to run fully in browser  
- Dropped Parquet loading because of browser limitations  
- Replaced with pre generated JSON at `data/index_data.json`, loaded over HTTP  
- Moved from Python based visual tools to Cytoscape.js for performance and portability  

---

## 2025-07-16  

### SCCM node type update for YAML  

- Standardised entity types to quoted form such as `@type: 'PERSON'` to avoid YAML parsing quirks  
- Change rippled through validators and graph builder  
- Highlighted need for stronger YAML schema checks later  

---

## 2025-07-14  

### Fixing schema to graph disconnects  

- Found broken links and dangling edges from mismatched service and organisation IDs  
- Rewrote edge building logic to verify both subject and object exist before creating edge  
- Added clearer error messages when relationships skipped  

---

## 2025-07-09  

### Visual and navigational structure  

- Reorganised `/docs/` folder to avoid old MkDocs sprawl  
- Added grouped navigation for tools, scrapes and thematic areas such as Early Help, SEND, Benchmarking  
- Refined script that auto generates `mkdocs.yml` navigation from folder structure  

---

## 2025-07-03  

### CSV and contact data integration  

- Added merge step for contact lists from different sources, for example Wix exports and curated CSVs  
- Normalised email domains and lowercased fields  
- Started mapping people entities for wider ecosystem graph  

---

## What I tried that did not work  

- Single giant JSON with full metadata, slow parse, slow paint, brittle caching  
- Edge labels enabled at load, browser struggled once graph neared five thousand nodes  
- Hover cards on mouse move, too many DOM changes and jitter on large graphs  
- Live GitHub API calls from client, rate limits and unauth flows, unreliable on Pages  
- Embedding full text for search inside graph JSON, payload size exploded, hurt first paint  
- Parquet on Pages, not supported, kept only as local build artefact  
- Loading all nodes and edges at once, long white screen and no progress signals  
- Bezier edges at initial zoom, layout cost too high when zoomed out  

---

## What works now  

- Split JSON, only bytes needed for current task  
- Staged loading seeded by degree, fast first paint then gradual reveal  
- Labels off until zoom, bezier edges after zoom, smoother interaction  
- Side panel version 2, type agnostic field bag, fewer re renders  
- Search with operators and URL state, easier sharing of views  
- Context mode keeps neighbours during filtering, supports sense making  
- Local Python pipeline writes minified deploy assets plus optional pretty debug files  
- Static JSON for feedback and lists, no client GitHub API  

--- 

## Files and purpose  

- `data_externally_processed/` - Precomputed search corpus from PDFs etc, feeds semantic search  
- `data_externally_processed/motw_chunks.parquet` - Text chunks table, one row per chunk, used to reconstruct context windows  
- `data_externally_processed/motw_index.faiss` - Vector index, fast nearest neighbour search over `motw_vectors`  
- `data_externally_processed/motw_vectors.parquet` - Embeddings table, one row per chunk, mirrors `motw_chunks` row ids  
- `data_externally_processed/search_index.json` - Lightweight search index export, usable by static site or potentialy API tools  

- `data_repos/` - Upstream Git repos pulled in, extra raw corpora for search and mapping  
- `data_web/` - External source configs, reproducible scraping   
- `data_yml/` - Core SCCM metadata, single source of truth for graph nodes and details  
- `docs/data/` - Build outputs for front end JavaScript, not hand edited in normal flow 

- `docs/data/adjacency.json` - Node adjacency map, used for neighbour lookups and context mode hints  
- `docs/data/crosswalk.json` - Id and slug to page path mapping, joins YAML ids to MkDocs pages and URLs  
- `docs/data/csc_artifacts/` - Packaged semantic search artefacts for public site or LA notebooks  
- `docs/data/csc_artifacts/motw_chunks.parquet` - Deployed chunk table, used by external notebooks or future on device search  
- `docs/data/csc_artifacts/motw_index.faiss` - Deployed ANN index, supports offline or local vector queries  
- `docs/data/csc_artifacts/motw_vectors.parquet` - Deployed embeddings, aligned with chunks, future friendly for new tools  
- `docs/data/csc_artifacts/state.json` - Metadata for chunks, vectors and index, shapes, versions, build state  

- `docs/data/degree.json` - Node degree per id, used for sizing or dimming nodes, supports optimisation and QA  
- `docs/data/graph_data.json` - Full node and edge payload for standard graph view, richest graph version  
- `docs/data/graph_data.lite.json` - Reduced graph payload, trimmed fields or nodes for faster load and lighter demos  
- `docs/data/graph_search_index.json` - Search index focused on graph nodes, drives graph explorer search UI  
- `docs/data/lite_index.json` - Tiny index for lite graph, quick lookup of ids, slugs and basic labels  
- `docs/data/node_details.json` - Per node detail blob, side panel reads from here instead of YAML at runtime  
- `docs/data/related_nodes.json` - Precomputed related suggestions, powers show related and context recommendations  
- `docs/data/search_index.json` - Site wide search index, complements MkDocs default, used by custom search tooling  
- `docs/data/source_nodes.dict.json` - Source to nodes mapping in dictionary shape, handy for scripts and analysis  
- `docs/data/source_nodes.json` - Canonical mapping of sources to node lists, used by optimisation and QA views  
- `docs/data/source_nodes.list.json` - List shaped variant of source to nodes mapping, easier to scan during dev  

- `docs/data/feedback-items.json` - Static feedback items for site, replaces live GitHub API calls  

- `docs/data/graph_data.json` - Renderable graph core, shared across main network views  
- `scripts/*.py` - Local build scripts, drive YAML validation, graph build and index generation  


---

## Build pipeline, local  

1. Read YAML sources for all types and validate fields  
2. Generate graph structures, compute degree, neighbours and crosswalk  
3. Build search index, tokenise, normalise, trim to compact form  
4. Write minified JSON to `docs/data`, optionally write pretty copies for review  
5. Run local smoke test, start MkDocs preview, check first paint and zoom behaviour  
6. Commit JSON artefacts, scripts and docs, push to GitHub, Pages serves static site  

---

## Performance notes  

- Aim for first content visible fast, show small seed subgraph before full graph  
- Keep JSON small, strip unused fields, prefer integer ids and short keys  
- Use cache friendly paths under `docs/data`  
- Avoid heavy synchronous work on client, defer expensive transforms until user zooms in  
- Prefer haystack edges at low zoom, switch to bezier when detail matters  
- Never show thousands of labels at once  

---

## Lessons learned  

- Design for static hosting from start, no hidden servers  
- Split concerns, separate files for render, search and lookups  
- Build locally where tools are rich, publish only what browsers need  
- Test with large graphs early, set label thresholds using data  
- Keep UX simple, side panel better than hover flood, context mode helps exploration  

---

## Next  

- Optional worker to pre compute layouts for very large subgraphs  
- Light theming pass for accessibility, including high contrast toggle  
- More examples in docs, plus short how to videos  
