"""Which issuing body a Gazette section names, and which sections we read.

The официален раздел of Държавен вестник groups every material under the
body that issued it: „Народно събрание“, „Министерски съвет“, one or
several ministries, and then the courts, the Централна избирателна
комисия, the sector regulators and the other state bodies.

Two consumers need the same reading of that string. The bulk body fetch
uses it to decide which of the roughly forty-two thousand HTML-era
materials to read at all, and the act-name resolver uses it to gate the
act type a numbered citation may resolve to: a „Наредба № 3“ published
under Народно събрание is not the ministerial наредба of the same number
(§5.3 of `docs/plans/2026-09-05-dv-graded-source-design.md`).

Matching is on the casefolded string, because the listing prints the
section in mixed case and the material page prints its section path in
capitals.

„министерств“ is the stem that covers „Министерство“ and „Министерства“
without touching „Министерски съвет“, which is a different body with a
different act type („Постановление“, and the наредби and правилници it
adopts by decree).
"""

PARLIAMENT = "parliament"
COUNCIL = "council"
MINISTRY = "ministry"
OTHER = "other"

#: The sections the body scan reads by default: the bodies that issue the
#: acts of this corpus. Everything else in the official section issues
#: decisions, rules and instruments that are not corpus acts, and reading
#: their bodies would buy thousands of requests for nothing.
DEFAULT_KINDS = (PARLIAMENT, COUNCIL, MINISTRY)

_PARLIAMENT_MARK = "народно събрание"
_COUNCIL_MARK = "министерски съвет"
_MINISTRY_MARK = "министерств"


def section_kind(section: str | None) -> str:
    """The issuing body a section string names.

    A material may be issued jointly, in which case the section lists
    several ministries separated by commas; naming any ministry makes it
    a ministerial material.
    """
    text = (section or "").casefold()
    if _PARLIAMENT_MARK in text:
        return PARLIAMENT
    if _COUNCIL_MARK in text:
        return COUNCIL
    if _MINISTRY_MARK in text:
        return MINISTRY
    return OTHER


def selected(section: str | None, extra: tuple[str, ...] = ()) -> bool:
    """Whether the body scan reads this section.

    `extra` widens the default set and never narrows it: each entry is a
    section name matched casefolded as a substring, and the single entry
    „all“ takes every section. Narrowing is not offered, because a body
    scan that skipped a default section would leave `chain_scan_complete`
    claiming a coverage it does not have.
    """
    if any(item.strip().casefold() == "all" for item in extra):
        return True
    if section_kind(section) in DEFAULT_KINDS:
        return True
    text = (section or "").casefold()
    return any(item.strip().casefold() in text for item in extra if item.strip())
