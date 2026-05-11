# Design: Phase 7 — Bulgarian Legislation Browser

**Date:** 2026-05-11
**Status:** Draft — pending approval
**Author:** Brainstorming session (legalize-bg main repo)
**Repos:** `Ahelia-Consulting-EOOD/legalize-bg` (REST API), `Ahelia-Consulting-EOOD/legalize-bg-web` (Next.js frontend, new)
**Depends on:** Phase 2 (temporal index), Phase 3+ (DV monitor) for full feature set; REST API can begin after Phase 1b.3

---

## Problem Statement

Bulgarian legislation is locked behind commercial portals (lex.bg, Ciela, APIS) with no free, open, machine-readable access. legalize-bg already provides a backend (3,573 acts as Markdown+YAML in git, MCP server, SQLite index) but has zero user-facing interface. The legislation is accessible only through Claude Code MCP tools.

Phase 7 builds an open-source web application that makes Bulgarian legislation freely browsable, searchable, and diffable by anyone — lawyers, researchers, journalists, and the general public.

---

## Decisions from Brainstorming

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | All audiences (lawyers, researchers, public) | Layered UX: core reading for everyone, advanced features (time machine, diff) for power users |
| 2 | Public website, open-source frontend | Credibility, community contribution, civic value |
| 3 | Separate REST API + shared query layer | REST API is core backend (same repo as MCP); both are surfaces over `index/fts.py` and `mcp_server/queries.py` |
| 4 | Next.js 15 + TypeScript + Tailwind | SSR for SEO (3,573 indexable law pages), React for interactive features (search, diff, timeline) |
| 5 | Frontend in separate repo | Keep frontend concerns outside the legislation corpus/backend repo |
| 6 | Full launch with time machine | Gated on Phase 2 temporal index; design now, build after backend phases complete |

---

## System Architecture

### Two Repos

**`legalize-bg`** (existing) — gains `api/` package:
```
legalize-bg/
├── api/                    # NEW — FastAPI REST API
│   ├── __init__.py
│   ├── app.py              # FastAPI application
│   ├── routes/
│   │   ├── laws.py         # /api/v1/laws, /api/v1/laws/{slug}
│   │   ├── articles.py     # /api/v1/laws/{slug}/articles/{n}
│   │   ├── history.py      # /api/v1/laws/{slug}/history
│   │   ├── diff.py         # /api/v1/laws/{slug}/diff
│   │   ├── search.py       # /api/v1/search
│   │   └── stats.py        # /api/v1/stats
│   └── schemas.py          # Pydantic response models
├── mcp_server/             # existing MCP server
├── index/                  # existing — shared query layer
├── fetcher/                # existing
└── ...
```

**`legalize-bg-web`** (new) — Next.js frontend:
```
legalize-bg-web/
├── src/
│   ├── app/
│   │   ├── page.tsx                    # Landing + search
│   │   ├── laws/
│   │   │   ├── page.tsx                # Category browser
│   │   │   ├── [category]/
│   │   │   │   └── page.tsx            # Law list
│   │   │   └── [slug]/
│   │   │       ├── page.tsx            # Law reader
│   │   │       ├── [art]/page.tsx      # Article deep-link
│   │   │       ├── history/page.tsx    # Amendment timeline
│   │   │       └── diff/page.tsx       # Version diff viewer
│   │   ├── search/page.tsx             # Search results
│   │   └── about/page.tsx              # Project info
│   ├── components/
│   │   ├── SearchDialog.tsx            # Cmd+K global search
│   │   ├── LawReader.tsx               # Markdown renderer with TOC
│   │   ├── TableOfContents.tsx         # Sticky collapsible TOC
│   │   ├── ArticleAnchor.tsx           # Article-level deep-linking
│   │   ├── TimelineView.tsx            # Amendment timeline
│   │   ├── DatePicker.tsx              # Point-in-time selector
│   │   ├── DiffViewer.tsx              # Side-by-side / unified diff
│   │   ├── CategoryGrid.tsx            # Category cards with counts
│   │   └── MetadataCard.tsx            # Law header (DV ref, dates, status)
│   ├── lib/
│   │   ├── api.ts                      # REST API client
│   │   └── types.ts                    # TypeScript types from API schemas
│   └── styles/
├── public/
└── ...
```

### Data Flow

```
Browser → Next.js (SSR/CSR) → REST API (FastAPI) → Shared Query Layer → SQLite + Git
                                                          ↑
                                        MCP Server (Claude Code) ──┘
```

The REST API and MCP server are **peers** — both import from `index/fts.py`, `mcp_server/queries.py`, and `index/catalog.py`. The REST API adds HTTP concerns (CORS, pagination, caching headers); the MCP server adds stdio/JSON-RPC concerns.

---

## Pages and UX Features

### Core Pages (7)

| Page | Route | SSR | Key Features |
|------|-------|-----|-------------|
| Landing | `/` | Yes | Search bar (Cmd+K), corpus stats, recent amendments |
| Category Browser | `/laws` | Yes | Grid of 5 categories with counts, filter by status |
| Law List | `/laws/[category]` | Yes | Sortable table (title, DV ref, dates, amendment count), pagination |
| Law Reader | `/laws/[slug]` | Yes | Full Markdown rendered, sticky TOC, article anchors, metadata card, date picker |
| Article Deep-Link | `/laws/[slug]/[art]` | Yes | Single article with context, share-friendly URL, per-article history |
| Amendment Timeline | `/laws/[slug]/history` | Yes | Vertical timeline, DV references, click-to-diff, date slider |
| Diff Viewer | `/laws/[slug]/diff` | CSR | Side-by-side or unified diff, article navigation within diff |

Additional: `/search?q=`, `/about`

### Cross-Cutting UX

- **Cmd+K search** — global search dialog (shadcn Command component), Bulgarian stemming via API
- **Responsive** — mobile-first law reading, collapsible TOC on mobile
- **Dark mode** — system-preference + toggle
- **Bulgarian UI** — all chrome in Bulgarian; English toggle deferred (FR candidate)
- **OpenGraph** — law title + article preview for social sharing
- **SEO** — SSR for all law pages, `sitemap.xml` generated from API `/stats` endpoint, structured data (Schema.org Legislation type)

### Key Interactions

**Point-in-time selector** (legislation.gov.uk pattern):
- Date picker on law reader page
- Selecting a date reloads the law text at that historical version
- URL updates to `/laws/zop?date=2020-06-15`
- Visual indicator: "Viewing version from 15.06.2020 г." banner

**Diff viewer** (lexdiff pattern):
- Select two dates from the timeline
- Side-by-side view with green/red highlighting
- Article-level jump links in the diff
- Toggle unified/split view

---

## REST API Endpoints

| Endpoint | Method | Description | Query Layer Source |
|----------|--------|-------------|-------------------|
| `/api/v1/laws` | GET | List laws, filter by category/status, paginate | `catalog.py` |
| `/api/v1/laws/{slug}` | GET | Full law text as Markdown, optional `?date=` | `queries.get_law_text` |
| `/api/v1/laws/{slug}/articles/{art}` | GET | Single article, optional `?date=` | `queries.get_article_text` |
| `/api/v1/laws/{slug}/history` | GET | Amendment timeline from `law_versions` | `catalog.py` (Phase 2) |
| `/api/v1/laws/{slug}/diff` | GET | Diff between `?from=` and `?to=` dates | `git diff` via subprocess |
| `/api/v1/search` | GET | FTS search, `?q=&category=&limit=&include_body=` | `fts.search_fts` |
| `/api/v1/stats` | GET | Corpus stats (counts, categories, last update) | `catalog.py` |

Response format: JSON with typed schemas matching `mcp_server/schemas.py` where possible.

---

## Tech Stack

### Backend (REST API, in legalize-bg repo)

- **FastAPI** — async, OpenAPI docs auto-generated, Pydantic validation
- **Uvicorn** — ASGI server
- **Shared imports** — `index/fts.py`, `mcp_server/queries.py`, `index/catalog.py`
- **No new database** — same SQLite catalog.db as MCP server

### Frontend (legalize-bg-web repo)

- **Next.js 15** (App Router) — SSR + ISR for law pages
- **TypeScript** — strict mode
- **Tailwind CSS 4** + **shadcn/ui** — design system
- **Framer Motion** — timeline animations, page transitions
- **react-diff-viewer-continued** or custom — diff display
- **cmdk** — Cmd+K search dialog

### Deployment (future)

- Frontend: Vercel or Cloudflare Pages (static + edge SSR)
- Backend: VPS or container with Uvicorn behind Caddy/nginx
- Domain: TBD (e.g., zakoni.bg, legislation.bg, or subdomain)

---

## UX References

| Feature | Reference | Adaptation |
|---------|-----------|------------|
| Point-in-time slider | legislation.gov.uk | Date picker instead of slider (works better for Bulgarian date format) |
| Amendment diff | lexdiff.com | Side-by-side + unified toggle, article-level navigation |
| Semantic TOC | LegalViz.EU | Collapsible, sticky, follows scroll position |
| Cmd+K search | LegalViz.EU / modern SaaS | shadcn Command component with Bulgarian stemming |
| Thematic browse | lexdiff.com | Deferred — potential FR for "browse by life topic" |

---

## Phase 7 Dependencies

| Dependency | Status | Impact |
|------------|--------|--------|
| Phase 1b (MCP server + query layer) | **Complete** | REST API builds on this |
| Phase 2 (temporal index) | **Next** | Required for history/diff endpoints |
| Phase 3 (DV monitor) | Planned | Required for "recent amendments" feed on landing page |
| Phase 4 (consolidation engine) | Planned | Required for ongoing freshness |
| Phase 5 (Legalize contribution) | Planned | No dependency |

The REST API can begin development as soon as Phase 2 ships. The frontend can begin in parallel (using mocked API responses for temporal endpoints).

---

## Phasing Within Phase 7

### 7.1 REST API (in legalize-bg repo)

- FastAPI app with all 7 endpoints
- OpenAPI spec auto-generated
- Shares query layer with MCP server
- Tests against the same fixtures
- CORS configuration for the frontend domain

### 7.2 Core Frontend (in legalize-bg-web repo)

- Landing, category browser, law list, law reader
- Cmd+K search
- SSR + SEO (sitemap, structured data, OpenGraph)
- Dark mode, responsive

### 7.3 Time Machine (in legalize-bg-web repo)

- Amendment timeline page
- Point-in-time date picker on law reader
- Diff viewer
- Per-article version history

### 7.4 Polish and Launch

- Performance optimization (ISR, edge caching)
- Accessibility audit
- Open-source launch (MIT license, README, contributing guide)
- Domain setup and deployment

---

## Documentation Plan

### For legalize-bg repo (REST API addition)

The API is a new surface in an existing repo. Required updates:

| Document | Action |
|----------|--------|
| `docs/prd/legalize-bg-prd.md` | Add Capability 8: REST API for web frontend |
| `docs/architecture/container-view.md` | Add REST API container |
| `docs/architecture/context.md` | Add browser as external actor |
| `docs/api/` | Add REST API OpenAPI spec (auto-generated by FastAPI) |
| `.ahelia/protected-surfaces.yaml` | Add REST API endpoint signatures as protected surface |
| `docs/frs/INDEX.md` | Add FR-019+ for Phase 7 features |

### For legalize-bg-web repo (new frontend repo)

Per Ahelia software documentation standard §7 ("app/UI repo" column) and §11:

**Required from day one (standard baseline for app/UI repos):**

| Document | Standard ref | Content |
|----------|-------------|---------|
| `README.md` | §5.1 | Repo identity, setup instructions, relationship to legalize-bg |
| `.ahelia/repo-profile.yaml` | §5.11 | repo_type: app_ui_repo, paired_repos: [legalize-bg] |
| `docs/process/delivery-contract.md` | §5.3 | Frontend process rules, review model, Definition of Done |
| `docs/prd/legalize-bg-web-prd.md` | §5.2 | Frontend-specific PRD (UX requirements, page specs, accessibility) |
| `docs/plans/` | §5.2 | Implementation plans |
| `docs/frs/INDEX.md` | §5.2 | Frontend-specific future requirements |
| `docs/architecture/` | §5.4 | Next.js app architecture, component hierarchy, data flow |
| **`docs/ui/ui-principles.md`** | §5.6 | Design principles, typography, color, spacing |
| **`docs/ui/information-architecture.md`** | §5.6 | Page hierarchy, navigation model, URL structure |
| **`docs/ui/screen-inventory.md`** | §5.6 | All 7+ pages with purpose and key interactions |
| **`docs/ui/user-flows.md`** | §5.6 | Core user journeys: search→read, browse→article, timeline→diff |
| `docs/testing/test-strategy.md` | §5.8 | Component tests, E2E (Playwright), visual regression |
| `docs/sync/ACTIVE.md` | §5.10 | Current work state |
| `docs/sync/DECISIONS.md` | §5.10 | Frontend-specific decisions |
| `.claude/CLAUDE.md` | §5.11 | Agent bootstrap for frontend sessions |

**Recommended additions:**

| Document | Standard ref |
|----------|-------------|
| `docs/ui/screen-specs/` | §5.6 |
| `docs/ui/design-system.md` | §5.6 |
| `docs/ui/accessibility-rules.md` | §5.6 |
| `docs/ui/copy-guidelines.md` | §5.6 |

### Product Management Artifacts

The following can be generated using available PM skills:

| Artifact | Skill | Purpose |
|----------|-------|---------|
| Frontend PRD | `write-spec` | Full product requirements with personas, user stories, success metrics |
| Phase 7 roadmap | `roadmap-update` | Now/Next/Later roadmap for 7.1-7.4 |
| Stakeholder update | `stakeholder-update` | Launch comms for different audiences |
| Competitive brief | `competitive-brief` | Positioning vs lex.bg, APIS, Ciela |

---

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Phase 2 delays block time machine | Medium | REST API + core frontend can ship without temporal endpoints; add them when ready |
| lex.bg content changes break parser | Medium | Already mitigated by DV monitor (Phase 3); frontend shows "last updated" date |
| SEO competition with lex.bg | Low | Different value prop: open, free, with diffs and timeline; not a lex.bg replacement |
| Bulgarian text rendering edge cases | Medium | Extensive fixture testing with real corpus; Markdown renderer tested against all 5 categories |
| Performance with 3,573 SSR pages | Medium | ISR (Incremental Static Regeneration) for law pages; edge caching |
| Open-source contributions break UX | Low | Contributing guide, PR review process, design system as guardrail |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Corpus coverage | 100% of 3,573 acts browsable | Sitemap entry count |
| Page load (law reader) | < 2s on 3G | Lighthouse, Web Vitals |
| Search response | < 300ms p95 | API metrics |
| SEO indexing | > 90% of law pages indexed within 30 days | Google Search Console |
| Time machine usage | > 10% of law page views use date picker | Analytics |
| Diff viewer usage | > 5% of history page views trigger a diff | Analytics |
| Open-source engagement | > 50 GitHub stars in first 3 months | GitHub |
