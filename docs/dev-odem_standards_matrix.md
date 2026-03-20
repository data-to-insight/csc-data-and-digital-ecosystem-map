# UK government, CSC and best-fit standards matrix

This README reformats the earlier standards review into four sections for easier reuse in a project repo.

## Scope

The aim is not to force the whole project into one standard. The aim is to use a best-fit standards stack for an ecosystem map covering organisations, people, suppliers, standards, guidance, datasets, software, relationships and provenance, with a searchable backend driven by JSON and Parquet.

## Structure

1. UK government and CSC relevant standards or guidance
2. Additional standards and vocabularies worth keeping handy
3. Best-fit stack for this ecosystem mapping project
4. Recommended adoption profile

## 1. UK government and CSC relevant standards or guidance

| Standard / guidance | Owner, status | Core purpose | Most applicable in your project | Suggested fit | Source URL |
|---|---|---|---|---|---|
| CBDS, Common Basic Data Set | DfE, live reference database | Defines common data items and code sets used in DfE and local authority software systems, and helps explain the structure of DfE data collections. | Use as a crosswalk and naming reference where your ecosystem map touches statutory-return style child, episode, plan, workforce or code-set fields. | High, for CSC aligned fields and definitions, not as your whole ecosystem model. | https://www.gov.uk/government/publications/common-basic-data-set-cbds-database |
| Children in Need census specification | DfE, current annual technical specification | Defines child-level supply, XML structure and validation rules for the CIN return. | Use as a domain reference model for CIN-related concepts, not as the backbone for non-CIN ecosystem objects. | High, where you map CIN entities or fields. | https://www.gov.uk/guidance/children-in-need-census |
| SSDA903, Children Looked After return technical specifications | DfE, current annual technical specification | Defines CLA return structure, data dictionary, code sets, XML and CSV submission formats. | Use as a domain reference model for looked-after child, placement, care leaver and related concepts. | High, where your map references CLA datasets or aligned fields. | https://www.gov.uk/government/publications/children-looked-after-return-2026-to-2027-technical-specifications |
| Children's Social Work Workforce census guide and collection | DfE, current census guidance | Defines workforce collection modules and submission guidance, and is tied to CBDS. | Use as a reference for workforce entities and field semantics. | Medium to high, if you are mapping workforce data or systems. | https://www.gov.uk/government/publications/childrens-social-work-workforce-guide |
| Children's social care data and digital strategy | DfE, strategic policy | Sets direction for data transformation, information sharing, case systems and adoption of technical and data standards. | Treat as an ecosystem reference node, also useful as design context for why interoperability matters. | High as context, low as a schema. | https://www.gov.uk/government/publications/childrens-social-care-data-and-digital-strategy/childrens-social-care-data-and-digital-strategy |
| Improving case management systems for children's social care services | DfE guidance | Helps local authorities assess systems that record, track, analyse and share CSC information across systems. | Treat as an ecosystem artefact, supplier or policy reference, not as your data model. | High as a mapped reference, low as a modelling standard. | https://www.gov.uk/government/publications/childrens-social-care-improving-case-management-systems/improving-case-management-systems-for-childrens-social-care-services |
| Data Standards Authority, Standards Catalogue | GDS / CDDO, current catalogue | Central catalogue of standards used or assessed across UK government. | Use as the official source of truth for which cross-government standards are endorsed, in review, or relevant. | High, as your standards inventory anchor. | https://www.gov.uk/government/publications/data-standards-authority-standards-catalogue/standards-catalogue |
| Open Standards Principles | UK government policy | Sets the policy basis for open standards in software interoperability, data and document formats, and encourages wider public sector adoption. | Use as your governing principle for selecting open, reusable standards in the repo and model. | High, as design policy. | https://www.gov.uk/government/publications/open-standards-principles/open-standards-principles |
| Metadata standards for sharing and publishing data | DSA collection of guidance | Bundles metadata-related standards and guidance for sharing and publishing data. | Use as a metadata governance reference for dataset records and catalogue entries. | High, for documentation and discoverability. | https://www.gov.uk/government/collections/metadata-standards-for-sharing-and-publishing-data |
| Linked identifier schemes, best practice guide | Geospatial Commission / GOV.UK guidance | Best practice for assigning identifiers so data can be joined reliably over time. | Use for stable IDs, slugs, canonical URIs, crosswalk identifiers and lifecycle identifiers. | High, for entity identity design. | https://www.gov.uk/government/publications/linked-identifier-schemes-best-practice-guide |
| Publish reference data for use across government | GOV.UK guidance | Guidance for publishing reusable reference data across government. | Use for code lists, lookup tables, controlled lists and enumerations in your repo. | High, especially for relation types, tags, object classes and status codes. | https://www.gov.uk/guidance/publish-reference-data-for-use-across-government |
| Record information about data sets you share with others | GOV.UK guidance | Guidance for recording metadata about shared datasets. | Use for dataset-level metadata fields such as owner, purpose, coverage, update cadence, provenance note and sensitivity note. | High, for dataset and asset cards. | https://www.gov.uk/guidance/record-information-about-data-sets-you-share-with-others |
| Government Data Quality Framework | UK government framework | Structured approach to understanding, documenting and improving data quality. | Use for quality flags, completeness notes, freshness notes and validation status on datasets and nodes. | Medium to high, especially for backend parquet or JSON assets. | https://www.gov.uk/government/publications/the-government-data-quality-framework |
| Data Sharing Governance Framework | UK government framework | Governance framework for better data sharing, with references to metadata, reference data and architecture. | Use as governance context where your map includes data flows, sharing relationships or stewardship. | Medium, mainly governance rather than graph schema. | https://www.gov.uk/government/publications/data-sharing-governance-framework/data-sharing-governance-framework |
| OpenReferralUK | Listed in DSA catalogue, endorsed | Service directory data structure for human services, extended for English use. | Very relevant if you want a service node or profile that is richer than a generic resource or organisation. | High, but only for service-directory parts of the model. | https://www.gov.uk/government/publications/data-standards-authority-standards-catalogue/standards-catalogue |
| UPRN | Listed in DSA catalogue, endorsed | Stable place identifier for land and property. | Relevant if you map sites, addresses, service locations, buildings or place-based joins. | Medium, only if location granularity matters. | https://www.gov.uk/government/publications/data-standards-authority-standards-catalogue/standards-catalogue |
| UK Gemini | Listed in DSA catalogue, in review | UK geographic metadata standard. | Relevant only if you publish geospatial datasets, boundary layers or location-based map resources. | Low to medium, unless geospatial metadata is first class. | https://www.gov.uk/government/publications/data-standards-authority-standards-catalogue/standards-catalogue |
| RFC 4180 CSV, via DSA catalogue | Cross-government recognised open standard | Standardises CSV structure, while validation and richer metadata remain separate. | Useful for exported tabular slices or crosswalks, but not as the main graph model. | Medium, for exchange exports only. | https://www.gov.uk/government/publications/data-standards-authority-standards-catalogue/standards-catalogue |

## 2. Additional standards and vocabularies worth keeping handy

| Standard | Owner, status | Core purpose | Most applicable in your project | Suggested fit | Source URL |
|---|---|---|---|---|---|
| DCAT 3 | W3C Recommendation, 22 Aug 2024 | RDF vocabulary for interoperable data catalogues, datasets and data services. | Best for your dataset catalogue layer, especially for parquet, JSON and document-backed assets. | Very high, for catalogue metadata. | https://www.w3.org/TR/vocab-dcat-3/ |
| PROV-O | W3C Recommendation | Ontology for provenance information, covering entities, activities and agents. | Best for source tracking, scrape lineage, transformations, generated artefacts, derived nodes and evidence chains. | Very high, for provenance and auditability. | https://www.w3.org/TR/prov-o/ |
| SKOS | W3C Recommendation | Lightweight model for taxonomies, thesauri, concept schemes and mappings. | Best for controlled vocabularies, tags, relationship types, thematic domains, statuses and crosswalks between terms. | Very high, for vocabulary control. | https://www.w3.org/TR/skos-reference/ |
| ORG | W3C Recommendation | Core ontology for organisations, units, memberships, roles, posts and organisational history. | Best for organisations, teams, programmes, posts, people-in-role, suppliers, partnerships and organisational restructures. | Very high, for organisation graph. | https://www.w3.org/TR/vocab-org/ |
| ADMS | EU / SEMIC specification, also published as W3C Working Group Note | Describes reusable assets such as specifications, data models, reference data and open source software. | Best for describing the standards, schemas, tools, repos, scripts and other assets that sit inside your ecosystem. | High, for asset registry and standards inventory. | https://interoperable-europe.ec.europa.eu/collection/semic-support-centre/adms |
| CPSV-AP | EU / SEMIC application profile | Reusable model for harmonising public service descriptions. | Best if you want a formal service description layer for public services, eligibility, outputs, competent authority and service channels. | Medium to high, only where service modelling is important. | https://interoperable-europe.ec.europa.eu/collection/semic-support-centre/solution/core-vocabularies/core-public-service-vocabulary-application-profile |
| BPMN | OMG standard | Standard graphical notation for business processes. | Useful only for supplementary process maps, for example how a referral, assessment or collection flow works. | Low as graph backbone, medium as supporting diagrams. | https://www.omg.org/bpmn/ |
| DMN | OMG standard | Standard notation for business decisions and rules. | Useful only if you explicitly model decision logic, such as thresholds, routing rules, classification decisions or business rules. | Low as graph backbone, medium as supporting decision artefact. | https://www.omg.org/dmn/ |

## 3. Best-fit stack for this ecosystem mapping project

| Project layer | Best-fit standard or approach | Why |
|---|---|---|
| Core entity graph | ORG + local project profile | ORG gives a strong base for organisations, units, roles, memberships, posts and collaborations. A local profile can then add project-specific node classes such as dataset, software, supplier, policy, guidance, scraper, pipeline, report and relationship subtypes. |
| Controlled vocabularies | SKOS | Use SKOS concept schemes for @type, tags, themes, relation types, evidence status, maturity level, sector, lifecycle stage and similar enumerations. |
| Provenance and derivation | PROV-O | Clean fit for source URL, derived-from, generated-by, transformed-by, imported-from, refreshed-on and similar lineage relationships. |
| Dataset and asset catalogue | DCAT 3 + ADMS | DCAT 3 fits datasets and distributions. ADMS fits standards, specs, software, repos, tools and reusable assets. They complement each other well. |
| Service descriptions | CPSV-AP or OpenReferralUK, selectively | Use CPSV-AP when you need a public-service description model. Use OpenReferralUK when you want practical English human-service directory semantics. |
| CSC field semantics | CBDS + statutory return specifications | These are the strongest official anchors for names, meanings, code sets and domain boundaries where CSC data is involved. |
| Identifiers | Linked identifier guidance + local URI or slug policy | Use stable, non-semantic identifiers internally, then add human-readable slugs separately. |
| Metadata minimum | Record information about data sets... + Government Data Quality Framework | Useful for catalogue cards, refresh metadata, quality notes and stewardship fields. |
| Location layer | UPRN, optionally | Only where specific sites, placements, offices or service locations matter. |
| Geospatial metadata | UK Gemini, optionally | Only if you have formal map layers, boundary assets or geospatial datasets to describe. |
| Process or decision overlays | BPMN, DMN, optional | Good for attached diagrams or linked artefacts, but not the main graph schema. |

## 4. Recommended adoption profile

| Category | Standard / guidance | Role in project | Notes |
|---|---|---|---|
| Adopt as core | ORG | Organisation and role structure | Primary base for organisations, units, memberships, roles, posts and collaborations. |
| Adopt as core | SKOS | Controlled vocabularies and classification | Use for concept schemes, tags, statuses, relation types and taxonomy mapping. |
| Adopt as core | PROV-O | Provenance and evidence chains | Use for source lineage, derivations, refresh events and generated artefacts. |
| Adopt as core | DCAT 3 | Dataset catalogue metadata | Use for dataset, distribution and catalogue level metadata around parquet, JSON and related assets. |
| Adopt as core | CBDS + DfE return specifications | CSC field crosswalk references | Use where your ecosystem map touches CSC datasets, code sets and official field semantics. |
| Adopt selectively | ADMS | Standards, tools, schemas, repos and reusable assets | Best for asset registry and standards inventory. |
| Adopt selectively | CPSV-AP | Formal public service descriptions | Use where service modelling is important. |
| Adopt selectively | OpenReferralUK | Practical service directory content | Use for English human-service directory and referral mapping. |
| Adopt selectively | UPRN | Location-aware objects | Use only where location precision and joins matter. |
| Adopt selectively | UK Gemini | Geospatial resources metadata | Use only for formal map layers or geospatial datasets. |
| Keep as supporting references | BPMN | Process diagrams | Useful as an attached process view, not as the graph backbone. |
| Keep as supporting references | DMN | Decision logic diagrams | Useful where business decision logic needs to be expressed separately. |
| Keep as supporting references | Children's social care data and digital strategy | Strategic ecosystem reference | Useful as a policy and change-context node in the map, not as a schema. |
| Keep as supporting references | Improving case management systems for children's social care services | Guidance reference node | Useful as a connected guidance artefact in the ecosystem map, not as the graph schema. |

## Notes

- Treat DfE statutory-return specifications and CBDS as CSC domain anchors and crosswalk references, not as the entire ecosystem schema.
- Treat ORG, SKOS, PROV-O and DCAT 3 as the most useful core standards for a GitHub, YAML, JSON and graph-oriented ecosystem mapping project.
- Treat ADMS, CPSV-AP, OpenReferralUK, UPRN and UK Gemini as selective layers used only where they add clear value.
- Treat BPMN, DMN and broader DfE guidance artefacts as supporting overlays or reference nodes rather than the graph backbone.
