# R2 — International Legal Information Systems & Standards

## Executive Summary

This research examines how countries and international organizations represent, serve, and manage legal information digitally. Key findings:

1. **Akoma Ntoso (LegalDocML)** is the dominant international standard for legislative XML, adopted by the EU, UK (as export format), Africa, and individual nations. It is the clear choice for any new legislative system.

2. **FRBR-based data models** (Work/Expression/Manifestation/Item) are used by EUR-Lex (CDM ontology) and increasingly by national systems. This separates the logical document from its language versions, format variants, and physical files.

3. **Point-in-time access** is now considered essential. The UK, Italy, Ontario, Estonia, and Czech Republic all provide historical versions of legislation. Implementation ranges from manual editorial processes (UK: 43-person team) to algorithmic consolidation (Italy's Normattiva).

4. **ELI (European Legislation Identifier)** provides a standardized URI scheme for legislation across the EU. Bulgaria, as an EU member, should implement ELI.

5. **Open-source platforms exist** and are production-ready: Indigo (Laws.Africa) for publishing, LEOS (EU Commission) for drafting. Both use Akoma Ntoso.

6. **Scale reference points**: EUR-Lex holds 2.7M work entries; Italy's Normattiva covers ~75,000 acts from 1861; the UK has legislation from 1267 onward with ~3,000 statutory instruments per year. Bulgaria's corpus will be significantly smaller than any of these.

---

## 1. National Systems

### 1.1 EUR-Lex / CELLAR (European Union)

#### Architecture & Data Model

EUR-Lex is the EU's portal for legal documents, backed by **CELLAR** — the Publications Office's content repository. CELLAR uses:

- **OpenLink Virtuoso** triple store for metadata (RDF/SPARQL)
- **Common Data Model (CDM)** — an OWL ontology aligned with FRBR:
  - **Work**: The intellectual creation (e.g., Regulation 2024/1689). Identified by CELEX number and ELI URI.
  - **Expression**: A language-specific realization (e.g., the English version). Linked via `cdm:work_has_expression`.
  - **Manifestation**: A format variant (XHTML, PDF, Formex XML). Linked via `cdm:expression_has_manifestation`.
  - **Item**: The physical file.
- **EuroVoc thesaurus** for subject classification: 7,000+ concepts in 21 domains, 127 sub-domains, available in 24+ languages.

#### API Access

**SPARQL Endpoint**: `https://publications.europa.eu/webapi/rdf/sparql`
- SPARQL 1.1 via HTTP GET/POST
- Content negotiation: JSON, XML, CSV
- Rate limits: 60s query timeout, <5 concurrent connections per IP, exponential backoff on 429/503
- Paginate results >10,000 rows with OFFSET/LIMIT

**REST API**: `GET https://publications.europa.eu/resource/cellar/{cellar-id}`
- Content negotiation for format selection
- ELI URIs resolve to documents: `http://data.europa.eu/eli/reg/2024/1689/oj`

**Bulk access**: Pillar IV Atom feed for update notifications (poll every 15-30 min).

#### Consolidation Approach

EUR-Lex provides consolidated texts of EU legislation. Documents pre-2014 are stored in **Formex XML**; newer documents use XHTML with Akoma Ntoso `eId` attributes for article-level granularity. The **AKN4EU** subschema (v3.0) is the EU's instantiation of Akoma Ntoso.

#### Volume

Over **2.7 million work entries** spanning treaties, regulations, directives, decisions, and case law across 24 official languages.

#### Key Takeaways for Our Project

- FRBR-aligned data model is proven at massive scale
- SPARQL endpoint enables powerful metadata queries
- ELI URIs provide persistent, semantic identifiers — Bulgaria should implement as an EU member
- CDM ontology is publicly available and reusable
- Rate limiting approach is well-documented and reasonable

---

### 1.2 legislation.gov.uk (United Kingdom)

#### Architecture & Data Model

Widely considered the **gold standard** for legislative data management.

**Technology stack**:
- **MarkLogic** native XML database for document storage
- **GraphDB** and **Virtuoso** for RDF stores
- **Orbeon** and **Tomcat** for application layer
- **XQuery**, **SPARQL**, and **XSLT** for processing pipelines
- **Crown Legislation Markup Language (CLML)** — proprietary XML schema owned by The National Archives

**CLML schema** (open-sourced on GitHub: `github.com/legislation/clml-schema`):
- `legislation.xsd` — Primary and Secondary UK Legislation
- `en.xsd` — Explanatory Notes and Memoranda
- `impactAssessment.xsd` — UK Impact Assessments
- `fragment.xsd` — subsets during editing

**Coverage**: All primary legislation in force since **1267**, all secondary legislation since **1823**.

#### API Access

RESTful API based on the legislation URI scheme. Multiple output formats:
- Default XHTML (`/data.htm`)
- CLML XML (most semantically complete)
- Akoma Ntoso XML (derived from CLML, simpler)
- HTML5 serialization of AKN

The CLML schema is open-sourced on GitHub. All data is freely available for reuse.

#### Consolidation & Time Machine

**Editorial process**: A dedicated team of **~43 people** (21 TNA employees, 8 from contractor TSO, 14 additional) manually applies amendments to produce revised/consolidated texts.

**Point-in-time access**:
- Timeline shows dates when changes came into force
- Base date: **01/02/1991** (England/Wales/Scotland) or **01/01/2006** (Northern Ireland)
- No versions available before the base date
- Unapplied effects are tracked but only shown on latest/prospective versions

**Known limitation**: There is an **editorial backlog** — not all amendments are applied in real-time. Changes are applied by the editorial team over time.

#### Volume

- ~4,200 Acts from 1950-2019
- ~3,000 Statutory Instruments per year (average 2010-2019)
- Primary legislation from 1267 onward

#### Key Takeaways for Our Project

- CLML is proprietary but the schema is open-sourced — shows the value of domain-specific XML
- AKN export proves Akoma Ntoso as a viable interchange format even when internal storage differs
- Manual editorial consolidation is resource-intensive (43 people) and creates backlogs
- Point-in-time needs a "base date" — historical completeness has practical limits
- Open data policy with multiple format outputs is best practice

---

### 1.3 Normattiva (Italy)

#### Architecture & Data Model

Activated **March 2010**, managed by the Istituto Poligrafico e Zecca dello Stato (IPZS). Built on the earlier **Norme in Rete** metadata systems.

#### Consolidation: The Multivigenza System

Normattiva's defining feature is its **multivigenza** (multi-validity) system, offering three views of any act:

1. **Original version** — as published in the Gazzetta Ufficiale
2. **Current version** — in force on the date of consultation
3. **Historical version** — in force on any user-specified past date

The system uses **algorithmic verification** against official Gazzetta Ufficiale sources, rather than purely manual editorial consolidation.

#### Coverage

~**75,000 normative acts** from **1861** to present. Since October 2023, expanded to include secondary implementing measures (ministerial decrees, circulars).

#### Key Takeaways for Our Project

- Algorithmic consolidation is more scalable than manual editorial (compare UK's 43-person team)
- Three-view model (original/current/historical) is the minimum for a modern system
- 75,000 acts is a useful scale reference — Bulgaria's corpus should be comparable or smaller

---

### 1.4 Riigi Teataja (Estonia)

#### Architecture & Data Model

Estonia's official gazette, **fully digital since June 1, 2010** (last paper copy: May 31, 2010). Published by the Ministry of Justice.

**Historical timeline**:
- First published 1918
- Electronic format available since 1996
- Dual paper/electronic from 2002
- Digital-only from 2010 (Riigi Teataja Act)

The system uses **ELI-compatible URIs** (e.g., `riigiteataja.ee/en/eli/523052018003/consolide`), integrating with the EU's European Legislation Identifier standard.

Part of Estonia's broader **X-Road** digital infrastructure — a decentralized data exchange system connecting public and private entities.

#### Key Takeaways for Our Project

- A small EU country can go fully digital — Estonia proves the model
- ELI adoption is practical even for small nations
- Integration with X-Road shows how legislation fits into broader e-governance
- Consolidated texts are maintained digitally with official legal force

---

### 1.5 e-Sbírka & e-Legislativa (Czech Republic)

#### Architecture & Data Model

Two complementary systems launched recently:

**e-Sbírka** (Electronic Collection of Laws):
- **Full operation since January 1, 2024** — replaced the printed Collection of Laws
- Two components: (1) portal with binding electronic texts, (2) database of information about legal acts
- Integrates with **EUR-Lex** and **N-Lex**
- Funded by EU Integrated Regional Operational Program (IROP)
- Published by the Ministry of Interior

**e-Legislativa** (Electronic Legislation):
- Platform for creation, deliberation, and enactment of legal regulations
- Operational from **January 15, 2025** for government regulations
- Provides transparency into ongoing legislative processes

#### Key Takeaways for Our Project

- Most recent example of a country transitioning from paper to digital-only legislation
- Dual system approach: publication platform + drafting platform
- EU funding was used (IROP) — similar funding may be available for Bulgaria
- EUR-Lex/N-Lex integration is built-in from the start

---

### 1.6 Gesetze im Internet (Germany)

#### Architecture & Data Model

Portal providing free access to virtually all current federal law. Joint operation of the Federal Ministry of Justice and the Federal Office of Justice.

**Current limitations**: Limited metadata, restricted search, technical access below modern standards.

**NeuRIS modernization project** (ongoing):
- Being developed to comply with the **German Data Use Act** (implementing EU Open Data Directive)
- New architecture: PostgreSQL (Amazon RDS), with "Download" and "Ingest" background tasks
- API documentation to be published with "request for comment" process
- Open, transparent, agile development process

**GitHub presence**: `github.com/bundestag/gesetze` — federal laws as Git repository; `github.com/tech4germany/rechtsinfo_api` — API prototype.

**Notable**: An MCP server for German legislation exists: `github.com/Ansvar-Systems/German-law-mcp`.

#### Key Takeaways for Our Project

- Even Germany acknowledges their current system is outdated
- "Legislation as Git" approach (bundestag/gesetze) is an interesting experiment
- NeuRIS shows the move toward modern APIs and open data
- The existence of an MCP server shows demand for programmatic access

---

### 1.7 Legal Information Institute / LII (United States — Cornell)

#### Architecture & Data Model

Established **1992** at Cornell Law School. Pioneer of free online legal information.

**Data sources**:
- US Code (from bulk XML provided by GPO)
- Supreme Court opinions (automated pipeline)
- Code of Federal Regulations (eCFR — from GPO bulk XML)
- State regulations for all 50 states

**Architecture**: Automated processing pipelines that ingest bulk XML from government sources, transform and hyperlink content, and publish.

**Key innovation**: The **eCFR** (Electronic Code of Federal Regulations) — a high-value enhanced version of the CFR created through a GPO-Cornell partnership (2010 pilot).

#### Key Takeaways for Our Project

- Government providing bulk XML data enables third-party innovation
- Automated processing pipelines for ingestion and cross-referencing
- Non-profit model proves sustainable for 30+ years
- "Wex" legal encyclopedia adds value beyond raw legislation

---

### 1.8 e-Laws Ontario (Canada)

#### Point-in-Time Access

Ontario's e-Laws provides **official digital copies** of legislation with legal force (Part IV of the Legislation Act, 2006).

**Point-in-time versions** available from **2003** (federal) and **2004** (Ontario). A new version is created every time an act/regulation is amended.

**Features**:
- Legislative history at statute/regulation and section level
- Commencement dates to determine relevant period-in-time versions
- Printouts of e-Laws copies are also official copies

#### Key Takeaways for Our Project

- Digital copies can have official legal force — requires legislative backing
- Version-on-every-amendment model is clean and trackable
- Section-level history is valuable for legal research

---

### 1.9 ISAP (Poland)

**Internetowy System Aktów Prawnych** — Internet System of Legal Acts. Maintained by the IT Centre of the Chancellery of the Sejm.

- Coverage: Journal of Laws since **1918**, Polish Monitor since **1930**
- Free public access at `isap.sejm.gov.pl`
- Does NOT include local government law or internal law
- Bibliographic descriptions + full texts

---

### 1.10 Singapore Statutes Online (SSO)

Provided by the Attorney-General's Chambers. Free public access to updated Singapore statutes with full legislative history per Act.

**LawNet** (subscription, Singapore Academy of Law) provides broader resources: case law, Singapore Law Reports, Legal Workbench.

Dual model: free basic access (SSO) + premium research tools (LawNet).

---

## 2. Standards & Formats

### 2.1 Akoma Ntoso (OASIS LegalDocML)

**Full name**: Architecture for Knowledge-Oriented Management of African Normative Texts using Open Standards and Ontologies.

**Status**: OASIS Standard v1.0 (August 2018), through the LegalDocML Technical Committee.

**Purpose**: International XML standard for representing legislative, executive, and judiciary documents in a structured, machine-readable format. Enables:
- Point-in-time consolidation
- Cross-border interchange
- Semantic analysis and deductive reasoning
- Smart legislative services

**Document types supported**: Acts, bills, amendments, debates, judgments, gazette documents.

**Key features**:
- Hierarchical document structure (part, chapter, section, article, paragraph)
- Semantic markup for references, definitions, temporal information
- FRBR-based identification (Work/Expression/Manifestation)
- Naming Convention standard for URIs (AKN NC v1.0)

**Countries/organizations using Akoma Ntoso**:
- **EU**: AKN4EU v3.0 subschema, used by LEOS and EUR-Lex
- **UK**: legislation.gov.uk exports in AKN (derived from CLML)
- **Italy**: Senate publishes all bills in AKN since July 2016
- **Germany**: LegalDocML.de application profile (v1.0, March 2020)
- **Finland**: Uses AKN as standard
- **Luxembourg**: Official Journal in AKN
- **South Africa**: Laws.Africa / Indigo platform
- **USA**: Office of the Law Revision Counsel; State of California
- **Brazil, Chile, Nicaragua**: Various implementations
- **Hong Kong**: XML standard for document management
- **United Nations**: HLCM adopted AKN for documentation (April 2017)

**Relevance for Bulgaria**: As an EU member, Bulgaria should adopt AKN4EU for interoperability with EUR-Lex and N-Lex. The Czech Republic's e-Sbírka already integrates with EUR-Lex using compatible standards.

---

### 2.2 ELI (European Legislation Identifier)

**Purpose**: Standardized URI scheme to make legislation accessible, exchangeable, and reusable across borders.

**Four Pillars**:

1. **URI Identification**: Every legal text gets a persistent, human-readable URI. Template: `/eli/{jurisdiction}/{agent}/{year}/{type}/{natural_id}/{point_in_time}/{version}/{language}` — all components optional, order flexible.

2. **Metadata & Ontology**: FRBR-based data model for describing legislation metadata. Published as OWL ontology. Enables linked data.

3. **Machine-Readable Exchange**: Content annotation using **RDFa** and **JSON-LD** to semanticize existing web pages.

4. **Discovery Protocol**: ELI sitemap and ELI Atom feed for automated discovery of legislative resources.

**Extensions**: **ELI-DL** (2021-2022) — for draft legislation, enabling tracking of legislative initiatives across the EU.

**Implementation by country**: Spain (BOE), France, Luxembourg, Ireland, Italy, Denmark, Finland, Austria, and others have implemented ELI. Estonia's Riigi Teataja uses ELI-compatible URIs.

**Relevance for Bulgaria**: As an EU member, Bulgaria is expected to implement ELI. This should be designed into any new system from the start.

---

### 2.3 ECLI (European Case Law Identifier)

**Purpose**: Uniform identifier for judicial decisions across the EU.

**Structure**: `ECLI:{country_code}:{court_code}:{year}:{unique_id}`
- Country code: ISO 3166-1 alpha-2 (or "EU" for EU courts)
- Court code: max 7 characters, assigned by national coordinator
- Year: 4 digits
- Unique ID: max 25 characters (letters, digits, dots)

**Established**: Council Conclusions of 22 December 2010 (2011/C 127/01).

**Metadata**: 9 mandatory + 8 optional fields, based on Dublin Core.

**Infrastructure**: EU-wide ECLI search engine and resolver at `e-justice.europa.eu/ecli/`.

**Relevance for Bulgaria**: Primarily for case law, not legislation. But any comprehensive legal information system should support ECLI for court decisions.

---

### 2.4 EuroVoc Thesaurus

**Purpose**: Multilingual, multidisciplinary thesaurus for indexing EU documents.

**Scale**: 7,000+ concepts in 21 domains, 127 sub-domains. Available in 24 official EU languages plus Albanian, North Macedonian, and Serbian.

**Usage**: Every document in EUR-Lex receives EuroVoc descriptors. National parliaments use it for indexing EU-related legislation.

**Machine learning**: The European Parliament has published a classifier model on HuggingFace (`EuropeanParliament/eurovoc_eu`) for automatic EuroVoc classification.

**Relevance for Bulgaria**: Bulgarian is one of the supported languages. Using EuroVoc descriptors would enable interoperability with EUR-Lex classification.

---

### 2.5 LegalRuleML

**Purpose**: XML standard for modeling legal normative rules, enabling automated legal reasoning.

**Status**: OASIS Standard v1.0 (August 2021). Based on Consumer RuleML 1.02.

**Capabilities**:
- Defeasibility of rules and defeasible logic
- Deontic operators (obligations, permissions, prohibitions, rights)
- Semantic management of negation
- Temporal management of rules
- Classification of norms (constitutive, prescriptive)
- Jurisdiction of norms
- Isomorphism between rules and natural language

**Relevance for Bulgaria**: Not immediately needed for a legislation repository. More relevant for future "rules as code" initiatives. Worth noting for long-term roadmap.

---

## 3. Open-Source Platforms

### 3.1 Indigo (Laws.Africa)

**Repository**: `github.com/laws-africa/indigo` (LGPL 3.0 / GPL 3.0)
**Version**: 19.1.0 (December 2025)
**Stats**: 71 stars, 32 forks, 10,926 commits, 26 releases

**Technology stack**:
- Python / Django / PostgreSQL
- Django REST Framework for API
- Webpack, Vue.js for frontend
- Docker support (Dockerfile + docker-compose.yml)
- Crowdin for i18n

**Key components**:
- **Bluebell** — plain-text parser (Markdown-like) that generates valid Akoma Ntoso 3.0 XML
- **Cobalt** — lightweight Python library for AKN document handling
- `indigo_api` — REST API layer
- `indigo_app` — Web interface
- `indigo_content_api` — Read-only public content API
- `indigo_resolver` — Reference resolution
- `indigo_za` — South Africa-specific features (country modules)

**Features**:
- Full legislation lifecycle: publication, commencement, amendment, repeal
- Multiple document types in AKN 3.0
- REST API for both management and public content delivery
- Country-specific modules (extensible)

**Used by**: African Legal Information Institute (AfricanLII), Laws.Africa, multiple African countries.

**Relevance for Bulgaria**: Most mature open-source platform for legislation management with AKN support. Could potentially be adapted with a `indigo_bg` country module, though the editorial workflow may not match Bulgarian institutional processes.

---

### 3.2 LEOS (Legislation Editing Open Software)

**Repository**: `github.com/MinBZK/leos` (mirror); official source on Joinup.
**License**: EUPL 1.2+

**Purpose**: Legislative drafting tool with collaboration features.

**Technology**:
- Web-based editor
- Akoma Ntoso XML (AKN4EU subschema)
- CMIS (Apache Chemistry) for document storage
- Demo: H2 in-memory database; Production: Oracle
- REST Webservice clients for integration

**Features**:
- Collaborative co-editing
- Comments and suggestions
- Version control
- Import from Official Journal
- Review workflow
- Modular plugin architecture

**Users**: European Commission (internal), piloted by member states including Greece (Hellenic Parliament).

**Relevance for Bulgaria**: Useful for the legislative **drafting** side, not the publication/consolidation side. Could complement Indigo in a full-lifecycle solution.

---

### 3.3 OpenLegislation (NY Senate)

**Repository**: `github.com/nysenate/OpenLegislation`

Web service delivering legislative information from NY State Senate and Assembly in near-real time. Powers nysenate.gov and Bluebird-CRM.

**Relevance**: US-specific, but demonstrates real-time legislative data delivery patterns.

---

### 3.4 Other Notable Projects

- **Legalize** (`github.com/legalize-dev/legalize`): "Legislation as code" — every law as Markdown, every reform as a Git commit. Experimental but conceptually interesting.
- **bundestag/gesetze** (`github.com/bundestag/gesetze`): German federal laws as a Git repository.
- **open-source-legislation** (`github.com/spartypkp/open-source-legislation`): Global legislation in SQL knowledge-graph format for LLMs. **Discontinued August 2024** — infrastructure shut down, links broken.
- **The National Archives** (`github.com/legislation`): Lawmaker tool for UK/Scottish legislation drafting. Parts are open-sourced.

---

## 4. Patterns & Best Practices

### 4.1 Cross-Cutting Patterns

| Pattern | Systems Using It | Maturity |
|---------|-----------------|----------|
| FRBR-based data model (Work/Expression/Manifestation) | EUR-Lex, ELI, Akoma Ntoso | Gold standard |
| Persistent URI identifiers | ELI, ECLI, legislation.gov.uk | Essential |
| Point-in-time access | UK, Italy, Ontario, Estonia, Czech Republic | Expected feature |
| Akoma Ntoso XML | EU (AKN4EU), Indigo, LEOS, multiple nations | Dominant standard |
| RDFa/JSON-LD metadata embedding | ELI, EUR-Lex | Growing adoption |
| SPARQL endpoint for metadata | EUR-Lex/CELLAR | Advanced |
| REST API for content | legislation.gov.uk, Indigo, EUR-Lex | Standard practice |
| Bulk XML download | US (GPO), Germany | Basic access |
| Subject classification thesaurus | EuroVoc, UK SIFlics | Important for discovery |
| Digital-only official publication | Estonia (2010), Czech Republic (2024) | Trend |

### 4.2 Architecture Patterns

1. **Separation of storage format from delivery format**: legislation.gov.uk stores in CLML but serves CLML, AKN, XHTML, HTML5. EUR-Lex stores in Formex/XHTML but serves multiple formats. Lesson: internal storage format can differ from API outputs.

2. **Metadata store + content store separation**: EUR-Lex uses Virtuoso (RDF/SPARQL) for metadata and separate content storage. legislation.gov.uk uses MarkLogic + GraphDB/Virtuoso. Lesson: graph databases for relationships, document databases for content.

3. **Editorial vs. algorithmic consolidation**: UK uses manual editorial (high quality, slow, backlogs). Italy uses algorithmic verification. Lesson: for a small team, algorithmic consolidation with manual review is the pragmatic choice.

4. **Country modules / extensibility**: Indigo uses country-specific modules (`indigo_za`). LEOS uses plugins. Lesson: core framework should be jurisdiction-agnostic with pluggable national specifics.

---

## 5. Volume & Scale Data

| System | Jurisdiction | Volume | Time Span |
|--------|-------------|--------|-----------|
| EUR-Lex / CELLAR | EU (24 languages) | 2.7M work entries | Treaties onward |
| legislation.gov.uk | UK | Primary since 1267, Secondary since 1823 | ~750 years |
| Normattiva | Italy | ~75,000 normative acts | 1861-present |
| ISAP | Poland | Journal of Laws + Monitor | 1918-present |
| e-Sbírka | Czech Republic | Full Collection of Laws | Digital from 2024 |
| Riigi Teataja | Estonia | All official legislation | 1918-present (digital from 2010) |
| US Code | United States | ~30,000+ federal statutes | Since 1789 |
| UK Acts (modern) | UK | ~4,200 Acts | 1950-2019 |
| UK SIs | UK | ~3,000/year | Ongoing |

**UK legislation volume trends** (1950-2019):
- Number of Acts has generally declined over the last 40 years
- Number of Statutory Instruments has increased
- Average ~3,000 SIs per year (2010-2019)

**Legal publishing industry**: The market is dominated by the "Wexis" duopoly (Westlaw/Thomson Reuters and LexisNexis/RELX). Wolters Kluwer is the third major player. These companies invest heavily in consolidation, cross-referencing, and citation-checking technology (e.g., Westlaw's KeyCite, LexisNexis's Shepard's Citations). Their approaches are proprietary but indicate the commercial value of well-structured, consolidated legal data.

---

## Implications for Architecture

Based on this international survey, a Bulgarian legislation system should:

1. **Adopt Akoma Ntoso (AKN4EU)** as the canonical XML format. This ensures interoperability with EUR-Lex, N-Lex, LEOS, and the broader EU legislative ecosystem.

2. **Implement ELI** for persistent URI identification of all Bulgarian legislation. This is effectively required for EU members and enables linked data integration.

3. **Use FRBR-based data model** (Work/Expression/Manifestation/Item) for the internal data model. This is proven at scale (EUR-Lex: 2.7M entries) and aligns with ELI and AKN ontologies.

4. **Provide point-in-time access** from a defined base date. Every amendment should create a new version. Three views minimum: original, current, historical (following Italy's multivigenza model).

5. **Pursue algorithmic consolidation with editorial review** rather than purely manual editorial (UK model requires 43 people). Given Bulgaria's expected corpus size (~10,000-30,000 acts), algorithmic approaches are feasible.

6. **Evaluate Indigo** as a potential platform or reference architecture. It's the most mature open-source AKN platform (Django/PostgreSQL, v19.1.0, LGPL). A `indigo_bg` country module could provide Bulgarian-specific features.

7. **Expose both REST API and structured metadata** (RDFa/JSON-LD at minimum; SPARQL endpoint as aspirational). Multiple output formats: HTML, AKN XML, PDF.

8. **Classify content with EuroVoc** descriptors for EU interoperability. Bulgarian is already a supported EuroVoc language.

9. **Design for digital-first or digital-only** publication, following Estonia (2010) and Czech Republic (2024) precedents. This requires legislative backing (cf. Ontario's Legislation Act, 2006).

10. **Integrate with EUR-Lex and N-Lex** from day one, as the Czech e-Sbírka demonstrates.

---

## Bulgaria Gap Analysis (from T1 site-analyst findings)

**lex.bg implements NONE of the international standards described in this document.** Confirmed findings:

- **No ELI URIs** — uses proprietary numeric doc IDs (signed 32-bit integers, some negative)
- **No Akoma Ntoso** — entirely proprietary HTML with custom CSS classes (TitleDocument, Article, Part, Heading, Section)
- **No ECLI** for case law references
- **No EuroVoc** descriptors in metadata
- **No RDFa/JSON-LD** semantic markup
- **windows-1251 encoding** (not UTF-8)
- **Proprietary desktop app hooks** (`window.external.OpenRef()`, `window.external.OpenEdition()`)
- **Cloudflare CDN** in front

The CSS class names (TitleDocument, Article, Part, Heading, Section) are well-structured and map roughly to Akoma Ntoso hierarchical elements, which could facilitate conversion. However, the gap between lex.bg's current state and international standards is significant.

This means **any new Bulgarian system would need to bridge from a fully proprietary ecosystem** with no standards compliance. The Czech Republic's e-Sbírka (2024) is the closest comparable transition — from legacy to modern, EU-integrated standards.

## Open Questions

1. ~~Does Bulgaria currently implement ELI in any form?~~ **ANSWERED: No.** (confirmed by T1)
2. What is Bulgaria's current status in N-Lex? Is there a functioning national gateway?
3. Has Bulgaria adopted or expressed interest in Akoma Ntoso?
4. Are there any EU funding programs (like IROP for Czech Republic) available for Bulgaria's digital legislation modernization?
5. What legislative changes would be needed to give digital publications official legal force in Bulgaria?
6. ~~How does lex.bg's internal data model compare to FRBR?~~ **ANSWERED: No FRBR. Proprietary numeric IDs, no Work/Expression/Manifestation separation.** (confirmed by T1)

---

## Sources Log

| # | Source | URL | Date Accessed | What Was Found |
|---|--------|-----|--------------|----------------|
| 1 | EUR-Lex — Reuse details | https://eur-lex.europa.eu/content/help/data-reuse/reuse-contents-eurlex-details.html | 2026-04-19 | Data reuse options, API overview |
| 2 | Polzia — EUR-Lex CELLAR API Guide | https://polzia.com/blog/eur-lex-cellar-api-developers-guide | 2026-04-19 | SPARQL endpoint, CDM, ELI URIs, rate limits, volume (2.7M works) |
| 3 | Publications Office — CELLAR data | https://op.europa.eu/en/web/cellar/cellar-data | 2026-04-19 | CELLAR architecture, knowledge graph |
| 4 | EUR-Lex — ELI register technical info | https://eur-lex.europa.eu/eli-register/technical_information.html | 2026-04-19 | ELI implementation details |
| 5 | EUR-Lex — What is ELI | https://eur-lex.europa.eu/eli-register/what_is_eli.html | 2026-04-19 | Four pillars of ELI |
| 6 | Wikipedia — ELI | https://en.wikipedia.org/wiki/European_Legislation_Identifier | 2026-04-19 | ELI structure, ELI-DL extension |
| 7 | legislation.gov.uk — Technology choices factsheet | https://www.legislation.gov.uk/pdfs/projects/technology-choices-factsheet.pdf | 2026-04-19 | MarkLogic, CLML, technology stack |
| 8 | GitHub — CLML schema | https://github.com/legislation/clml-schema | 2026-04-19 | Open-sourced CLML schema files |
| 9 | legislation.gov.uk — Formats | https://www.legislation.gov.uk/developer/formats | 2026-04-19 | API output formats, AKN export |
| 10 | National Archives — Legislation data presentation | https://cdn.nationalarchives.gov.uk/documents/cas-82049-presentation-notes.pdf | 2026-04-19 | API introduction, editorial process |
| 11 | Contracts Finder — TNA legislation services | https://www.contractsfinder.service.gov.uk/Notice/Attachment/fc335f1a-27de-4d4e-8945-7d79c5c0962a | 2026-04-19 | Editorial team size (43 people) |
| 12 | House of Commons Library — CBP-7438 | https://commonslibrary.parliament.uk/research-briefings/cbp-7438/ | 2026-04-19 | UK legislation volume 1850-2019 |
| 13 | Wikipedia — Normattiva | https://en.wikipedia.org/wiki/Normattiva | 2026-04-19 | Multivigenza system, 75K acts |
| 14 | N-Lex — Italy info | https://n-lex.europa.eu/n-lex/info/info-it/index | 2026-04-19 | Normattiva architecture |
| 15 | Riigi Teataja | https://www.riigiteataja.ee/en/ | 2026-04-19 | Estonia digital legislation |
| 16 | N-Lex — Estonia info | https://n-lex.europa.eu/n-lex/info/info-ee/index | 2026-04-19 | eRT architecture |
| 17 | Czech Ministry of Interior — e-Sbírka | https://mv.gov.cz/clanek/e-sbirka-a-e-legislativa.aspx | 2026-04-19 | e-Sbírka/e-Legislativa launch |
| 18 | e-Sbírka portal | https://www.e-sbirka.cz/co-je-esbirka | 2026-04-19 | System description |
| 19 | DigitalService Germany — NeuRIS | https://digitalservice.bund.de/en/projects/new-legal-information-system | 2026-04-19 | German modernization project |
| 20 | GitHub — bundestag/gesetze | https://github.com/bundestag/gesetze | 2026-04-19 | Laws as Git repo |
| 21 | GitHub — rechtsinfo_api | https://github.com/tech4germany/rechtsinfo_api | 2026-04-19 | API prototype |
| 22 | Wikipedia — LII | https://en.wikipedia.org/wiki/Legal_Information_Institute | 2026-04-19 | Cornell LII history |
| 23 | Code4Lib — LII eCFR | https://journal.code4lib.org/articles/13241 | 2026-04-19 | eCFR architecture |
| 24 | Ontario e-Laws | https://www.ontario.ca/laws/about-e-laws | 2026-04-19 | Point-in-time access, official status |
| 25 | N-Lex — Poland info | https://n-lex.europa.eu/n-lex/info/info-pl/index | 2026-04-19 | ISAP coverage |
| 26 | Wikipedia — ISAP | https://en.wikipedia.org/wiki/Internetowy_System_Akt%C3%B3w_Prawnych | 2026-04-19 | ISAP history, coverage since 1918 |
| 27 | Singapore AGC — SSO | https://www.agc.gov.sg/our-roles/drafter-of-laws/singapore-statutes-online/ | 2026-04-19 | SSO features |
| 28 | OASIS — LegalDocML TC | https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=legaldocml | 2026-04-19 | AKN standard status |
| 29 | Wikipedia — Akoma Ntoso | https://en.wikipedia.org/wiki/Akoma_Ntoso | 2026-04-19 | Countries using AKN |
| 30 | AKN4EU — Publications Office | https://op.europa.eu/en/web/eu-vocabularies/akn4eu | 2026-04-19 | EU AKN subschema |
| 31 | Wikipedia — ECLI | https://en.wikipedia.org/wiki/European_Case_Law_Identifier | 2026-04-19 | ECLI structure, governance |
| 32 | OASIS — LegalRuleML | https://www.oasis-open.org/2021/09/08/legalruleml-core-specification-v1-0-oasis-standard-published/ | 2026-04-19 | LegalRuleML v1.0 standard |
| 33 | Wikipedia — EuroVoc | https://en.wikipedia.org/wiki/EuroVoc | 2026-04-19 | 7000+ concepts, 24 languages |
| 34 | GitHub — laws-africa/indigo | https://github.com/laws-africa/indigo | 2026-04-19 | Indigo v19.1.0, architecture, Bluebell |
| 35 | Indigo documentation | https://indigo.readthedocs.io/en/latest/ | 2026-04-19 | Platform documentation |
| 36 | Joinup — LEOS | https://interoperable-europe.ec.europa.eu/collection/justice-law-and-security/solution/leos-open-source-software-editing-legislation | 2026-04-19 | LEOS features, architecture |
| 37 | GitHub — MinBZK/leos | https://github.com/MinBZK/leos | 2026-04-19 | LEOS source code |
| 38 | GitHub — nysenate/OpenLegislation | https://github.com/nysenate/OpenLegislation/ | 2026-04-19 | NY Senate legislative data service |
| 39 | GitHub — legalize-dev/legalize | https://github.com/legalize-dev/legalize | 2026-04-19 | Legislation as code concept |
| 40 | Wikipedia — Wexis | https://en.wikipedia.org/wiki/Wexis | 2026-04-19 | Legal publishing duopoly |
