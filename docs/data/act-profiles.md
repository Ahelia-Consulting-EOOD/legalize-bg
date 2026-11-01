# The act profiles register (`act-profiles.csv`)

One row per corpus act, built by `reading/profiles.py build` and checked by `reading/profiles.py check` (step S3 of the plan of 31 October 2026, decision D-077). The register is written by the script alone; nothing edits it by hand.

| Column | Values | Source |
|---|---|---|
| `slug` | the act's file name without `.md` | the corpus |
| `category` | `laws`, `codes`, `ordinances`, `regulations`, `implementing` | the corpus folder |
| `kind` | `закон`, `кодекс`, `наредба`, `правилник`, `правилник по прилагане` | the frontmatter's `rango` |
| `era` | `html` (published 2003 or later), `pdf` (1989 to 2002), `pre1989`, `unknown` (no publication date; 121 acts) | the frontmatter's `fecha_publicacion`, by year |
| `candidate_grade` | `A`, `B`, `B-pending`, `C`, `none` | the coverage map of 5 September 2026 (`acts-summary.csv`); no gate has graded any act (D-059) |
| `page_holds_act` | `yes`; `no` (the seven lex.bg pages that are site chrome with no act); `no_page` (the act's page is a stub in the raw store) | the splitter's spine test on the raw page |
| `annex_headings` | count | short blocks opening „Приложение № …“ or „Приложение към …“ |
| `table_rows` | count | `tr` elements of the act's own markup |
| `images` | count | `img` elements of the act's own markup that are not lex.bg's per-article icons or a tracking pixel |
| `unnumbered_paragraphs` | count | body blocks that open like no provision, heading, separator, chrome or table cell |
| `superscript_numbers` | count | `sup` elements of the act's own markup, plus blocks carrying a unicode superscript digit or a leaked `SUP>` remnant (D-072 ruling 13) |
| `repeated_headings` | count | a heading number line printed twice in a row, with or without its title (D-072 ruling 1) |
| `known_defects_s2` | empty, or a `;`-list of codes from S2's defect register | **pending**: empty in every row until step S2 reports its register `lexbg-defect-kinds.yaml` |
| `source` | `lexbg:<doc id>`, `dv:<material id>`, `strategy.bg:<url>` | the frontmatter's `fuente` and provenance base |

The counts are taken over the act's own blocks only: the subtrees the splitter drops (lex.bg's history block, its advertising and reference boxes), the page's tail (the related-EU-acts list and the news footer) and the chrome lines are left out, as the reading checks leave them out. A row with `page_holds_act` other than `yes` carries zero counts.

The in-force question for the acts begun before the Gazette's archive is answered beside this register in `pre-archive-acts-in-force.yaml`, with its evidence and the limits of its method.
