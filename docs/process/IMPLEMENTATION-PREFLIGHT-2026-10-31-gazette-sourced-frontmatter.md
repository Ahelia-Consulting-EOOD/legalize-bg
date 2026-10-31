# Preflight: the frontmatter of an act taken from the State Gazette

Who this is for: the owner. On 31 October 2026 the owner decided that the frontmatter of an act taken from the State Gazette goes through a signed preflight before the Закон за обществения транспорт is written from the Gazette (decision D-076, point 2). This document asks for that signature.

## The decision asked for

Please sign this preflight, so that the transport law can be written from the Gazette item that promulgated it. The change is small: one field takes a new value, the [source field](#glossary), and one block of the frontmatter takes new content, the [provenance base](#glossary). Every other field keeps the value it has today, the act's key included. Nothing is removed or renamed, no field changes its type, and the only act written in this session is the transport law.

## What changes, field by field

The act's file today carries the frontmatter that was built when the act was read from lex.bg on 22 October 2026. Once the act is written from Gazette [material](#glossary) 242220, the file will carry the values below. Every field not named here stays exactly as committed.

| Field | Today | From the Gazette | Why |
|---|---|---|---|
| the source field | `lex.bg` | `dv.parliament.bg` | The schema reference already names this value for an act taken from the Gazette. The field stays a literal from a closed set of two values. |
| the act's key (`identificador`) | `2137259781` | unchanged | The key identifies the act, not its source. The corpus file, the index and every consumer find the act by this key. |
| the publication date and the date of the last change | 1 April 2026 | 1 April 2026, taken from the material's header | The Gazette issue date is the publication date, and the act has never been amended, so both dates are the same. |
| the issue number and year | 32 and 2026 | the same, taken from the material's header | The same values, now read from the Gazette itself. |
| the amendment history | one row, issue 32 of 2026, dated 1 April 2026 | the same one row | An act read whole from the item that promulgated it has one event in its history. Any extra field that the row carries today is kept. |
| the status (`estado`) | in force | unchanged | A promulgation item never repeals an act. |
| the title, the country, the rank, the date in force, the category, the ELI address, and any other field | as committed | unchanged | The Gazette item gives no reason to change them. |
| the provenance base | names the lex.bg page: its source, its state as a snapshot, the page's hash and fetch time | names the Gazette item: the Gazette as the source, the state as promulgated, the material number 242220, issue 32 of 2026 and its date, the material's hash and fetch time | The provenance base says where the text was read from, so that the reading can be checked again against that same page or material. |

The provenance block has three parts. The provenance base is the one that changes. The second part, the run record, names the labelling run the body was built from, with the hashes of the labels and the blocks; the third, the omissions, lists what the reading left out of the page's text and why. Both keep their form. The whole block is an optional extension field of the frontmatter under decision D-071, so it needs no preflight of its own; the owner asked for this preflight because of the source field and the new content of the base.

The commit that writes the act ends with the same four lines that every reading commit ends with. These lines, called trailers, record the source identifier, the source date, the identifier of the act and the identifier of the labelling run. The keys of the four lines are unchanged. Only the source identifier's first part names the Gazette instead of lex.bg, a value the write gate has accepted since it was built.

## The checklist of the template

- Protected surface: 2, the YAML frontmatter schema.
- Authoritative source: the Legalize specification for the eight mandatory fields; the project's schema reference for the Bulgarian extension fields and the provenance block.
- Hard constraint confirmed: yes. No mandatory field is removed, renamed or changed in type or meaning. The source field keeps its type, a literal, and takes the second value that the schema reference already documents for it.
- Violation risk: a consumer of the corpus that assumed every act's source field says `lex.bg`. The MCP server and the SQLite indexer read the field as a string and never compare it with a value; this was checked on 31 October 2026, as the last section explains. What remains is the risk of a document that states the value as universal, and the schema reference already does not.
- Allowed scope confirmed: yes. The provenance base is part of an optional extension field under decision D-071. The source field's new value lies inside the closed set the schema documents, which the template does not count as a schema change; the owner asked for this preflight anyway (decision D-076, point 2).
- Waiver required: no.
- Migration: none. One act changes, through one write of the gate; the other 3,623 acts are untouched.
- Owner confirmation: the owner, 31 October 2026, in the S0+S1 session of the starting state ("Signed, write it").
- Implementation may proceed: yes (31 October 2026).

## How this was checked

The frontmatter is built by the function `build_frontmatter_dv` in `reading/write.py`. Its test, in `tests/reading/test_write.py`, writes a small Gazette material through the gate into a test repository and reads back every field named above. The gate is the one function that writes a corpus file: it runs the correctness checks of the corpus (no leftover markup fragments, no page chrome in the text) against the waiver file, and refuses the write when a check fails. Before the gate is called, the write path itself refuses the act in four cases: the material in the cache does not hash as the run recorded it; the material splits into other blocks than the run's; the body differs from the staged body; or the checks find an exception or lost text. The claim that no consumer compares the source field with a value was checked by searching the folders `mcp_server/` and `index/` for such a comparison of the field `fuente`; there is none. The closed set of the source field is documented in `docs/data/schema-reference.md`, in the table of mandatory fields.

## Glossary

- Frontmatter: the YAML block at the top of every corpus file, with the act's fields.
- Source field: the mandatory field `fuente`, which names where the act's text was taken from.
- Material: one published item of a Gazette issue. Material 242220 is the item that promulgated the transport law in issue 32 of 1 April 2026.
- Provenance block, provenance base: the frontmatter block that records where the text came from and how it was read. Its base names the page or material the text was read from, with its hash and fetch time; its run record names the labelling run; its omissions list what the reading left out.
- Trailer: a line at the end of a commit message with a key and a value, such as the source date.
- The gate, the write path: the gate is the single function that writes a corpus file, `corpus_gate.write_act`, with its checks; the write path is the code that prepares an act and calls the gate.
- ELI: the European Legislation Identifier, the standard address of an act, carried in the field `eli`.
- MCP server: the project's server for the Model Context Protocol, through which Claude Code reads the corpus.
- YAML: the text format of the frontmatter.
- D-071, D-076: decisions of the project's decision log. D-071 lets the provenance block enter the frontmatter as an optional extension field. D-076 approves the plan of 31 October 2026 together with this preflight.

## References

- The implementation plan of 31 October 2026, `docs/plans/2026-10-31-starting-state-implementation-plan.md`, section 7, decision 2.
- The decision log, `docs/sync/DECISIONS.md`, decisions D-071 and D-076.
- The preflight template, `docs/process/IMPLEMENTATION-PREFLIGHT.md`, Protected Surface 2.
- The schema reference, `docs/data/schema-reference.md`.
- The Legalize specification, `legalize-dev/legalize/SPEC.md` in the Legalize repository.
- State Gazette issue 32 of 1 April 2026, material 242220, at dv.parliament.bg.
