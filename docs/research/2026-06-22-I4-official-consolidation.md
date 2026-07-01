# I4 — Official Bulgarian Consolidation Sources

**Investigation:** I4. **Date:** 2026-06-22. **Author:** research agent (Claude Opus 4.8, 1M).
**Source log:** `docs/research/2026-06-22-I4-official-consolidation-sources.md` (claims trace to `extract#N`).

**Premise under test:** Bulgaria has NO official consolidated-law API/source (unlike
Spain's BOE, France's Légifrance, the EU's EUR-Lex). If true, the legalize-bg
pipeline CANNOT fetch official consolidated text and MUST self-consolidate
deterministically from the Държавен вестник (ДВ) amendment stream.

**Headline result — the premise needs ONE correction, but the roadmap conclusion holds.**
There is **no official consolidated-law database or API of national scope** — but
there IS a *government-domain* portal (the Ministry of Justice e-justice portal,
`justice.government.bg/home/normdoc/`) that publishes full consolidated texts for
a **curated subset** of acts. Critically, that consolidation is **performed by a
private vendor (Ciela Norma)**, not by the state, and there is **no API, no full-corpus
coverage, and no machine-readable bulk access**. So Bulgaria still cannot follow the
ecosystem's "fetch the official consolidated text via an official API" path. The
self-consolidate conclusion stands; the nuance is that an official *validation
surface* (free, government-domain consolidated text for major acts) exists and is
worth using as an oracle alongside lex.bg.

---

## Q1 — Official consolidation: does it exist?

**Finding: No official, state-authored, consolidated, full-corpus legal database
exists — but there is one government-domain consolidated surface (MoJ/Ciela) of
curated scope.** Each candidate portal was checked directly.

**Държавен вестник (ДВ, `dv.parliament.bg`) — the official gazette — is NOT
consolidated.** It is the constitutionally official promulgation channel (ЗНА чл. 37:
laws, Council-of-Ministers decrees and ministerial acts are promulgated in ДВ), but
the EU's own N-Lex country page states it plainly: *"State gazette consists mainly of
editions and corrections of the official documents, and not of the full texts of
actual laws in Bulgaria"* and *"any search in its database provides mainly information
about changes in legislative papers, and not the whole list of acting laws"*
(extract#1). The Bulgarian Wikipedia entry on legal-information systems gives the
mechanism: on amendment of an already-promulgated act, *"в Държавен вестник се
публикуват само отделните части, които се променят"* (only the changed parts are
published) — i.e. ДВ is an amendment stream, exactly as the handoff §1 assumed
(extract#7).

**National Assembly (`parliament.bg`) — bills/enacted acts, not consolidated.** Its
`/bg/laws` and `/bg/bills` sections carry законопроекти and acts as passed/voted; the
only "consolidated" documents found are EU treaties (TEU/TFEU), not consolidated
national statutes (search #7, negative).

**Council of Ministers / government legal portal — none.** No CoM consolidated-law
database surfaced. The `strategy.bg` "Портал за обществени консултации" (referenced
inside ЗНА itself) is a draft-acts/consultation portal, not a consolidated-law store.

**IISDA (`iisda.government.bg`, the Council-of-Ministers Administrative Register) —
metadata, not consolidated text.** It is a genuine official system, but its regulatory
pages provide a description plus a PDF reference, not an amended-into-base consolidated
database (search #5; WebFetch of `regulatory/244`).

**`data.egov.bg` (open-data portal) — no consolidated-legislation dataset.** It is the
EU-Directive-2019/1024 open-data portal; no consolidated-law dataset was found
(search #6, negative).

**Ministry of Justice e-justice portal (`justice.government.bg/home/normdoc/{id}`) —
this is the real find.** Rendering it directly (extract#6) shows full **consolidated,
amended-into-base** text: the Law on Normative Acts header reads *"Обн. ДВ. бр.27 от 3
Април 1973г., изм. ДВ. бр.65 … изм. и доп. ДВ. бр.30 от 27 Март 2026г."* and the body
carries every article with inline amendment markers — *"Чл. 1. (Изм. - ДВ, бр. 46 от
2007 г.) …"*, repeals *"Чл. 5. (Отм. - ДВ, бр. 46 от 2007 г.)"*, insertions *"Чл. 1а.
(Нов - …)"*, renumberings *"(Предишна ал. 2 …)"* — current to 2026, with per-element
"Редакции на елемента" (point-in-time revisions) and cross-reference affordances.
**Three caveats that keep it from satisfying the premise's "official consolidation":**
(1) **Scope is curated, not the full corpus** — the Public Procurement Act (ЗОП), one
of Bulgaria's most-amended laws, did *not* surface as a MoJ `normdoc` URL; its
consolidated text lives on lex.bg / `legislation.apis.bg` / ministry PDFs instead
(search #11). The acts that do appear are MoJ-adjacent (ЗНА, Constitution, citizenship,
judicial power, civil procedure, labour code, trade register). (2) **The portal is the
MoJ institutional site**, not a legislation database — its top nav is ministry services;
there is no "all Bulgarian legislation" browse/search (search #12, homepage render).
(3) **The consolidation is done by a private vendor** — see Q3 (extract#4). So it is an
*official-domain re-publication of a privately-consolidated subset*, not a sovereign
consolidation engine.

---

## Q2 — EU level: N-Lex / EUR-Lex coverage of Bulgaria

**Finding: N-Lex and EUR-Lex do NOT provide consolidated Bulgarian national law. They
point back to the (non-consolidated) ДВ gazette.**

**N-Lex** is the EU's "common gateway to National Law" — a single entry point that
*links to* each member state's own national-law database; it does not itself host or
consolidate national legislation (extract#5). For Bulgaria specifically, the official
N-Lex country page links **one** primary database: the State Gazette
(`dv.parliament.bg`), described as the "Bulgarian government official journal." The same
page is the source of the definitive negative statement that the ДВ database is
editions/corrections, not full law texts (extract#1). N-Lex therefore *confirms* the
absence of an official consolidated Bulgarian source rather than supplying one — it has
nothing better to point at than the gazette.

**EUR-Lex** consolidates **only EU acts**, not national law: *"Consolidated versions of
EU legal acts combine … the initial act with all its subsequent amendments …"* and the
consolidated-texts section *"covers legal acts published in the Official Journal of the
European Union."* For national material EUR-Lex carries only references to (and, where a
member state agrees to provide them, texts of) **national transposition measures** of EU
directives — not consolidated domestic statutes — and explicitly defers to N-Lex as the
national-law gateway (extract#5). EUR-Lex also notes consolidated texts have "no legal
effect … intended for use as documentation only" — the same non-authoritative status
any consolidation (ours included) carries.

**Implication:** the EU layer offers no shortcut. Unlike France (Légifrance feeds
EUR-Lex/N-Lex with consolidated national law) or Spain (BOE), the Bulgarian node of the
EU legal-information network resolves to a gazette. This independently corroborates Q1.

---

## Q3 — The private consolidators

**Finding: Consolidated Bulgarian law is, in practice, produced and sold by PRIVATE
commercial compilers. The state's only consolidated surface (MoJ portal) is itself
vendor-supplied.**

The Bulgarian Wikipedia article on правно-информационни системи enumerates the market —
**Сиела (Ciela), Лакорда (Lakorda), Дакси (Daksi), Експертис (Expertis), АПИС (APIS),
Doxtream** — all **private "комерсиални продукти"** requiring payment (*"за ползването
им се налага да се заплати парична сума"*), and states the defining difference from the
gazette: where ДВ publishes only the changed parts, the commercial systems *"нанасят
промените върху целия текст"* (apply the changes onto the whole text) — i.e. *they* are
who actually consolidates Bulgarian law (extract#7).

Characterization of the principals relevant to this project:

- **lex.bg** — the project's current bootstrap source and validation oracle (D-002/D-003).
  Free-to-browse consolidated current texts; asserts a ЗАПСП чл. 93б database right +
  reference-only-use ToS (*"Копиране на базите … представлява правонарушение"*) per D-038.
- **APIS (`apis.bg`; `legislation.apis.bg`; municipal `obshtini.bg`)** — the oldest
  Bulgarian legal-IS vendor; consolidated national + municipal law (the FR-022 municipal
  bootstrap source, D-037). Same чл. 93б posture.
- **Ciela / Сиела Норма (`ciela.net`)** — legal-IS vendor "updated after each ДВ issue";
  notably, **Ciela Norma built and maintains the Ministry of Justice e-justice portal**
  under an EU-funded contract (contract 03.10.2017; ~485,523 BGN), with *"Автоматично ще
  бъдат актуализирани с последни редакции и всички текстове на нормативни актове"* —
  i.e. the consolidated normative-act texts shown on `justice.government.bg` are
  auto-updated through Ciela's pipeline (extract#4). This is the key structural fact:
  even the government's consolidated surface is **private consolidation re-published
  under a `.government.bg` domain**, not a sovereign state consolidation.
- **Lakorda, Daksi, Expertis, Doxtream** — additional commercial systems, same model.

This is consistent with D-039's standing legal posture: the legislative *texts* are
public-domain (ЗАПСП чл. 4); what these vendors hold is the compilation/consolidation
investment (чл. 93б) — which the project does not re-use, building its own structure
from the free texts.

---

## Definitive conclusion

**Does an official consolidated Bulgarian-law source exist? — Effectively NO, for the
purpose that matters to this project.**

- There is **no official, state-authored, full-corpus, machine-readable / API-accessible
  consolidated database** of Bulgarian legislation. Bulgaria has no BOE, no Légifrance,
  no official Cellar-equivalent. The constitutional official source (ДВ) is a
  **gazette/amendment stream**, explicitly not consolidated (extract#1, #3, #7), and the
  EU layer (N-Lex/EUR-Lex) points back to that gazette and consolidates only EU acts
  (extract#5).
- The **one correction to the premise**: a *government-domain* consolidated surface
  exists — the **Ministry of Justice e-justice portal** (`justice.government.bg/home/
  normdoc/{id}`) — serving genuine amended-into-base, point-in-time-capable consolidated
  text, current to 2026, for free (extract#6). But it is (a) **curated, not full-corpus**
  (e.g. ЗОП absent — search #11), (b) **HTML-only, no API / no bulk / no enumeration
  surfaced**, and (c) **consolidated by the private vendor Ciela, not the state**
  (extract#4). It is therefore an official-domain *re-publication of private
  consolidation*, not an official consolidation engine the pipeline could "fetch from"
  the way `legalize-es`/`-fr`/`-eu` fetch from BOE/Légifrance/EUR-Lex APIs.

**Implication for the roadmap (one line):** the "must self-consolidate deterministically
from ДВ" conclusion (handoff §1, Concern 2, Phases 3-4) is **validated** — no official
API/consolidated-corpus exists to fetch — and the MoJ/Ciela `justice.government.bg`
portal should be adopted as a **second, government-domain validation oracle** alongside
lex.bg (strengthening D-003 / D-b), since it offers free, official-domain consolidated
text for the major acts to byte-check our self-consolidated output against.

**Self-review (protocol step 4):** each named official portal was checked directly —
National Assembly `parliament.bg` (search #7, negative), Council of Ministers /
`strategy.bg` (none), Ministry of Justice `justice.government.bg` (rendered, extract#6 —
the one positive, with scope/provenance caveats), IISDA `iisda.government.bg`
(WebFetch + search #5, metadata-only), `data.egov.bg` (search #6, negative), and the EU
N-Lex/EUR-Lex layer (extract#1, #5). The negative conclusion rests on the EU's own
N-Lex Bulgaria page (most authoritative neutral source), the Library of Congress /
European Forum of Official Gazettes summary, and the Bulgarian-Wikipedia
private-vs-gazette mechanism description — not a vague "couldn't find one." The single
positive (MoJ/Ciela) was pursued to its limits (scope test via ЗОП, provenance via the
Ciela contract) so the conclusion is precise rather than overstated.
