# FR-011 — Degenerate-Act Triage + WAIVERS

**Date:** 2026-06-21 (batch 2.x-a) · **Decision:** D-034 · **FR:** FR-011 · **Gate:** G2 (frontmatter validation) pre-gate for Phase 5.

## Summary

The bootstrap flagged ~128 "degenerate" acts (empty `titulo` + null `fecha_publicacion`). Re-counted against the **live 3,599-act corpus** (post the 2026-06 re-scrape, D-030): the counts are **unchanged** — the re-scrape did not alter them, which is expected (the metadata parser is frozen at the April bootstrap, so a re-photograph reproduces the same fields).

| Metric | Count |
|---|---|
| Acts with empty/missing `titulo` | **7** |
| Acts with null/missing `fecha_publicacion` | **121** |
| Both (empty titulo ⊂ null pub) | 7 |
| **Union (degenerate)** | **121** |

**Disposition: WAIVE all 121.** Every null `fecha_publicacion` is **faithful to the source** (lex.bg, the oracle per D-003) — it is not a parse failure to be backfilled. Fabricating a publication date to make G2 green would corrupt the data to satisfy the gate, the exact inversion of the gate's purpose. This registry records *why* each null is correct.

## Method

1. Re-parsed YAML frontmatter across all 3,599 act `.md` files (`laws/ codes/ ordinances/ regulations/ implementing/`).
2. Classified by slug + title + `rango`/`category` into: municipal-council acts, judicial ethics codes, §7.3 numeric phantoms, and residual titled acts.
3. For every residual, checked all corpus date signals (`dv_issue`, `dv_year`, `effective_date`, `ultima_actualizacion`) — **all null**, confirming lex.bg itself carries no ДВ date for them (the corpus is a faithful photograph; absence in the corpus = absence at source, re-confirmed by the frozen parser running twice: April bootstrap + June re-scrape).

## Categories & dispositions

| Category | Count | Why null is correct | Disposition |
|---|---|---|---|
| **Municipal council acts** (`наредба/правилник на ... общински съвет` — Sofia / Veliko Tarnovo) | 104 | The lex.bg source carries no parseable ДВ date for these specific entries, so `fecha_publicacion` is null — the faithful source value. **NB (owner, 2026-06-21):** this is *not* "municipal acts are never in ДВ" — some municipal acts **are** promulgated in Държавен вестник. Authoritative municipal dates (and full municipal coverage) belong to the dedicated municipal-corpus build-out (**FR-022**, prioritized ASAP — supersedes the D-006 Phase-6 timing). | **Waived for now** — null faithful to lex.bg; municipal dates to be sourced properly by FR-022. |
| **Judicial ethics codes** | 2 | Adopted by judicial/professional bodies (СВ/ВСС), not promulgated in ДВ with a parseable date at lex.bg. | **Waived** — null expected. |
| **§7.3 numeric phantoms** (empty `titulo`, numeric slug) | 7 | lex.bg shows no title; already handled at query time by the `<doc_id=N>` substitute (search/get_law remain functional). Includes `-549676032` (pre-existing §7.3 fixture). | **Waived** — known phantoms; reachable by identificador. |
| **Residual titled acts** (professional-body bylaws, arbitration-court rules, internal charters) | 8 | No date signal anywhere in the corpus → lex.bg carries no ДВ date. These are bodies-internal/court acts (КИИП, БТПП arbitration, Сметна палата rulebook, Съюз на архитектите, etc.), not ДВ-promulgated. One (`2137255124`, Union of Architects bylaw) is already owner-marked `derogado` as a scope exclusion (handoff `2026-06-21-missing-acts-evaluation.md`). | **Waived (provisional)** — null faithful to source; see "Optional future verification" below. |

## G2 impact

With this registry, **every** degenerate act is explained. G2 frontmatter validation should treat these 121 as **known waivers**, not failures: the 8 mandatory SPEC fields are present except `fecha_publicacion`, which is legitimately null for non-ДВ-promulgated acts. No corpus edits, no schema change, no invented data.

## Optional future verification (NOT gating 2.x-a)

The 8 residuals are the only acts where a national-level ДВ promulgation is *conceivable* (e.g. the Сметна палата rulebook `2136124032`, the national-classification-of-professions rulebook `2135711771`). If a future national-coverage policy requires it, a focused source pass could re-check each at lex.bg: **if** lex.bg shows a ДВ date the frozen metadata parser missed, that would be a *parser-coverage* finding (file as a new FR — fix the parser, then re-derive), **not** a license to hand-enter dates. Until then, null is the faithful value. Lex.bg is oracle-only post-bootstrap (D-002/D-003) and rate-limited, so this is deliberately deferred, not done speculatively.

---

## WAIVERS registry

### §7.3 numeric phantoms (7) — empty titulo

| law_id (slug) | doc_id |
|---|---|
| `2137254803` | 2137254803 |
| `2137254802` | 2137254802 |
| `-549676032` | -549676032 |
| `2135625007` | 2135625007 |
| `2136890603` | 2136890603 |
| `2137254804` | 2137254804 |
| `2137254795` | 2137254795 |

### Judicial ethics codes (2)

| law_id (slug) | doc_id |
|---|---|
| `etichen-kodeks-na-sadebnite-sluzhiteli` | 2135951391 |
| `kodeks-za-etichno-povedenie-na-balgarskite-magistrati` | 2135951392 |

### Residual titled acts (8) — provisional waive

| law_id (slug) | doc_id | note |
|---|---|---|
| `naredba-2-za-proektantskata-pravosposobnost-na-inzhenerite-registrirani-v-kiip` | 2135512067 | КИИП engineers — professional-body act |
| `naredba-za-otchitane-i-opazvane-na-dvizhimite-pametnitsi-na-kulturata` | 2135573429 | cultural-monuments ordinance |
| `pravilnik-za-ustroystvoto-i-organizatsiyata-na-deynostta-na-smetnata-palata` | 2136124032 | Сметна палата rulebook (national body — verify candidate) |
| `pravilnik-na-arbitrazhniya-sad-pri-balgarskata-targovsko-promishlena-palata` | -536870185 | БТПП arbitration court rules |
| `pravilnik-za-arbitrazh-ad-hok-podpomagan-ot-arbitrazhniya-sad-pri-balgarska-targ` | 1027604536 | БТПП ad-hoc arbitration rules |
| `ustroystven-pravilnik-na-regionalen-tsentar-za-savremenni-izkustva-toplotsentral` | 2137230151 | regional arts centre charter |
| `pravilnik-za-prilagane-na-natsionalnata-klasifikatsiya-na-profesiite-i-dlazhnost` | 2135711771 | national classification of professions (verify candidate) |
| `pravilnik-za-sotsialno-podpomagane-na-chlenovete-na-sayuza-na-arhitektite-v-balg` | 2137255124 | Union of Architects bylaw — already `derogado` (scope exclusion, owner) |

### Municipal council acts (104) — Sofia (Столичен) + Veliko Tarnovo councils

| law_id (slug) | doc_id |
|---|---|
| `naredba-na-stolichen-obshtinski-savet-po-prinuditelnoto-otchuzhdavane-na-imoti-c` | -1073741283 |
| `naredba-na-stolichen-obshtinski-savet-za-grobishtnite-parkove-i-pogrebalno-obred` | 2137174804 |
| `naredba-na-stolichen-obshtinski-savet-za-izgrazhdane-na-obshtodostapna-sreda-v-g` | -1073741270 |
| `naredba-na-stolichen-obshtinski-savet-za-izgrazhdane-poddarzhane-i-opazvane-na-z` | 2135584316 |
| `naredba-na-stolichen-obshtinski-savet-za-izvarshvane-na-obshtestven-prevoz-na-pa` | -1073741276 |
| `naredba-na-stolichen-obshtinski-savet-za-obshtinskata-sobstvenost` | 2135781509 |
| `naredba-na-stolichen-obshtinski-savet-za-obshtinskite-lechebni-zavedeniya` | 2135786744 |
| `naredba-na-stolichen-obshtinski-savet-za-opredelyane-i-administrirane-na-mestni-` | 2135584751 |
| `naredba-na-stolichen-obshtinski-savet-za-opredelyane-na-razmera-na-mestnite-dana` | 2135585788 |
| `naredba-na-stolichen-obshtinski-savet-za-organizatsiya-na-dvizhenieto-na-teritor` | 2135584936 |
| `naredba-na-stolichen-obshtinski-savet-za-pazarite-na-teritoriyata-na-stolichna-o` | -1073741267 |
| `naredba-na-stolichen-obshtinski-savet-za-pravata-i-zadalzheniyata-na-mestnite-or` | -1073741274 |
| `naredba-na-stolichen-obshtinski-savet-za-predostavyane-na-sotsialnite-uslugi-asi` | 2135584312 |
| `naredba-na-stolichen-obshtinski-savet-za-premestvaemite-obekti-za-reklamnite-inf` | 2136398645 |
| `naredba-na-stolichen-obshtinski-savet-za-pridobivane-pritezhavane-i-otglezhdane-` | 2135585787 |
| `naredba-na-stolichen-obshtinski-savet-za-pridobivane-pritezhavane-i-otglezhdane--2` | 2135782093 |
| `naredba-na-stolichen-obshtinski-savet-za-prinuditelnoto-izpalnenie-na-zapovedi-p` | 2136235773 |
| `naredba-na-stolichen-obshtinski-savet-za-privatizatsiya-na-grupa-predpriyatiya-c` | -1073741285 |
| `naredba-na-stolichen-obshtinski-savet-za-privlichane-i-nasarchavane-na-investits` | 2136895717 |
| `naredba-na-stolichen-obshtinski-savet-za-prouchvane-analiz-i-simulatsiya-na-tran` | 2137235283 |
| `naredba-na-stolichen-obshtinski-savet-za-reda-i-nachina-za-provezhdane-na-obshte` | 2137177850 |
| `naredba-na-stolichen-obshtinski-savet-za-reda-i-usloviyata-za-izvarshvane-na-tar` | 2135502797 |
| `naredba-na-stolichen-obshtinski-savet-za-reda-i-usloviyata-za-upravlenie-i-razpo` | 2135530445 |
| `naredba-na-stolichen-obshtinski-savet-za-reda-za-poluchavane-i-upravlenie-na-dar` | 2136746925 |
| `naredba-na-stolichen-obshtinski-savet-za-reda-za-preobrazuvane-i-privatizatsiya-` | -1073741272 |
| `naredba-na-stolichen-obshtinski-savet-za-sastavyane-izpalnenie-otchitane-i-kontr` | 2135785167 |
| `naredba-na-stolichen-obshtinski-savet-za-simvolikata-i-otlichiyata-na-stolichna-` | 2135585790 |
| `naredba-na-stolichen-obshtinski-savet-za-upravlenie-na-obshtinskite-patishta` | 2135788487 |
| `naredba-na-stolichen-obshtinski-savet-za-upravlenie-na-otpadatsite-i-poddarzhane` | 2136566830 |
| `naredba-na-stolichen-obshtinski-savet-za-usloviyata-i-reda-za-provezhdane-na-obs` | 2135585789 |
| `naredba-na-stolichen-obshtinski-savet-za-usloviyata-i-reda-za-provezhdane-na-tar` | 2135585398 |
| `naredba-na-stolichen-obshtinski-savet-za-usloviyata-i-reda-za-sastavyane-na-byud` | 2137176777 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-finansovo-podpomagane-na-sportn` | 2137203702 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-formirane-i-upravlenie-na-priho` | 2137180647 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-izgrazhdane-i-adaptirane-na-dos` | 2137180220 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-izgrazhdane-poddarzhane-i-opazv` | 2137205887 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-nasarchavane-na-investitsiite-s` | 2137180250 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-opazvane-na-okolnata-sreda-na-t` | 2137180456 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-opredelyane-na-mestna-taksa-koy` | 2137180435 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-opredelyane-predostavyane-podda` | 2137204689 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-opredelyaneto-i-administriranet` | 2137180429 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-opredelyaneto-i-administriranet-2` | 2137180172 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-organizatsiya-na-deynostta-na-d` | 2137180430 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-organizatsiyata-na-rabota-v-pri` | 2137207467 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-priem-na-detsa-v-yasleni-grupi-` | 2137229870 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-priemane-na-uchenitsi-v-parvi-k` | 2137203759 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-provezhdane-na-obshtestveno-obs` | 2137180475 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-reda-na-pridobivane-upravlenie-` | 2137192874 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-reda-za-spirane-prestoy-i-parki` | 2137180540 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-simvolite-i-nagradite-na-obshti` | 2137180576 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-targovskata-deynost-i-premestva` | 2137180584 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-upravlenie-na-obshtinskata-patn` | 2137193609 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-upravlenie-stopanisvane-i-polzv` | 2137182934 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-upravlenie-stopanisvane-i-polzv-2` | 2137180674 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-upravlenieto-stopanisvaneto-i-p` | 2137180670 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-usloviyata-i-reda-pri-predostav` | 2137180667 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-usloviyata-i-reda-za-izpolzvane` | 2137203660 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-usloviyata-i-reda-za-sastavyane` | 2137180669 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-usloviyata-i-reda-za-uprazhnyav` | 2137205868 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-vazlagane-izvarshvaneto-na-deyn` | 2137192877 |
| `naredba-na-velikotarnovskiya-obshtinski-savet-za-vodene-na-registar-na-obshtinsk` | 2137180402 |
| `pravilnik-na-stolichen-obshtinski-savet-za-avtomatiziranite-informatsionni-siste` | 2135614833 |
| `pravilnik-na-stolichen-obshtinski-savet-za-deynostta-na-kastratsionni-tsentrove-` | -536870176 |
| `pravilnik-na-stolichen-obshtinski-savet-za-deynostta-na-stolichna-obshtinska-age` | 2136149617 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiya-i-rabota-na-spetsializi` | 2135790662 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-i-deynostta-na-konsul` | 2135608451 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-i-deynostta-na-obshte` | 2137193723 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-i-deynostta-na-obshte-2` | 2135614832 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-i-deynostta-na-obshti` | 2135594230 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-i-deynostta-na-rayone` | -536870199 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-i-deynostta-na-saveta` | 2137234643 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-i-deynostta-na-stolic` | 2135594231 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-i-deynostta-na-stolic-2` | 2135499266 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-na-deynostta-na-obsht` | 2135834933 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-na-deynostta-na-obsht-2` | 2135805118 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-na-deynostta-na-obsht-3` | 2136010680 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-na-deynostta-na-obsht-4` | 2135828372 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-na-deynostta-na-obsht-5` | 2135584323 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-na-deynostta-na-obsht-6` | 2137191687 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-na-deynostta-na-obsht-7` | 2135584324 |
| `pravilnik-na-stolichen-obshtinski-savet-za-organizatsiyata-na-deynostta-na-obsht-8` | 2135805119 |
| `pravilnik-na-stolichen-obshtinski-savet-za-osashtestvyavane-na-deynostta-na-obsh` | 2137205621 |
| `pravilnik-na-stolichen-obshtinski-savet-za-otlichiyata-na-stolichniya-obshtinski` | -536870197 |
| `pravilnik-na-stolichen-obshtinski-savet-za-ustroystvoto-i-deynostta-na-obshtinsk` | 2135864526 |
| `pravilnik-na-stolichen-obshtinski-savet-za-ustroystvoto-i-deynostta-na-obshtinsk-2` | 2136451648 |
| `pravilnik-na-stolichen-obshtinski-savet-za-ustroystvoto-i-deynostta-na-regionale` | 2137200752 |
| `pravilnik-na-stolichen-obshtinski-savet-za-ustroystvoto-i-deynostta-na-saveta-po` | 2135565701 |
| `pravilnik-na-stolichen-obshtinski-savet-za-ustroystvoto-i-deynostta-na-sofiyska-` | 2137197215 |
| `pravilnik-na-stolichen-obshtinski-savet-za-ustroystvoto-i-deynostta-na-stolichen` | 2135614835 |
| `pravilnik-na-stolichen-obshtinski-savet-za-ustroystvoto-i-deynostta-na-tsentar-z` | 2136945512 |
| `pravilnik-na-stolichen-obshtinski-savet-za-ustroystvoto-i-deynostta-na-tsentar-z-2` | 2136945011 |
| `pravilnik-na-stolichen-obshtinski-savet-za-ustroystvoto-i-deynostta-na-tsentar-z-3` | 2137179255 |
| `pravilnik-na-stolichen-obshtinski-savet-za-ustroystvoto-organizatsiyata-i-deynos` | 2136591615 |
| `pravilnik-na-stolichen-obshtinski-savet-za-ustroystvoto-organizatsiyata-i-deynos-3` | 2136594890 |
| `pravilnik-na-stolichen-obshtinski-savet-za-ustroystvoto-organizatsiyata-i-deynos-4` | 2136594889 |
| `pravilnik-na-stolichen-obshtinski-savet-za-ustroystvoto-organizatsiyata-i-deynos-5` | 2136591426 |
| `pravilnik-na-stolichen-obshtinski-savet-za-zalavyane-i-transportirane-na-bezstop` | -536870175 |
| `pravilnik-na-velikotarnovskiya-obshtinski-savet-za-deynostta-na-obshtinskata-age` | 2137180690 |
| `pravilnik-na-velikotarnovskiya-obshtinski-savet-za-finansovo-podpomagane-na-izsl` | 2137181033 |
| `pravilnik-na-velikotarnovskiya-obshtinski-savet-za-organizatsiyata-i-deynostta-n-2` | 2137248939 |
| `pravilnik-na-velikotarnovskiya-obshtinski-savet-za-organizatsiyata-i-upravleniet` | 2137212225 |
| `pravilnik-na-velikotarnovskiya-obshtinski-savet-za-organizatsiyata-reda-i-rabota` | 2137215485 |
| `pravilnik-na-velikotarnovskiya-obshtinski-savet-za-ustroystvoto-i-deynostta-na-r` | 2137214876 |
| `pravilnik-na-velikotarnovskiya-obshtinski-savet-za-ustroystvoto-i-deynostta-na-t` | 2137180692 |

> **Regeneration:** this registry is derived from the corpus frontmatter (`titulo`/`fecha_publicacion` null) classified by slug/title pattern. Re-run the FR-011 classification over the corpus to refresh after any re-scrape; the counts should stay stable while the metadata parser is frozen.
