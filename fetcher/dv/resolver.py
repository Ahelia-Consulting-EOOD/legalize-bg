"""Turning the act named in a Gazette title into a corpus act.

§5.3 of `docs/plans/2026-09-05-dv-graded-source-design.md`. Every
attribution of the coverage map, every chain-omission row and therefore
every candidate grade rests on this module, so its first rule is that it
never guesses: two candidates, or none, is `None` with `title_ambiguous`
and a queue entry, not a best effort. A wrong attribution writes a false
chain into a research artifact that later becomes the derivation input
for a provenance grade; an unresolved event is merely `unlocated` and
`pending`, which is honest and blocks nothing but a grade.

Three keys, tried in order.

**The normalised title.** A ЗИД names its target with a definite article
(„Закон за изменение и допълнение на Закона за обществените поръчки“).
`normalise_title` casefolds, drops the editorial title-amendment note,
strips the amending prefix and the „, приета с ...“ adoption tail, and
`title_variants` offers the article back in its nominative forms. The
Cyrillic casefold is Python's `str.casefold`, the same FR-019 fold
`mcp_server/queries.py` applies row by row because SQLite's `LOWER()`
is ASCII-only; there is no shared helper in the tree to import, so this
module calls `str.casefold` directly.

**The number.** 1,976 corpus наредби are titled „НАРЕДБА № N ОТ <дата>
Г. ЗА ...“ and an amending instruction cites „Наредба № N от YYYY г.“
with no issuing ministry in either, so the key is (act type, number,
year) gated by the Gazette section the material sits in. Numbers carry
letters, dashes and slashes („№ Н-10“, „№ РД-02-20-1“, „№ 8121з-1006“,
„№ І-3“, „№ РД-07/2“) and the corpus writes the same series with Latin
and with Cyrillic look-alikes, so the number is folded before it is
compared.

The key alone does not identify: 363 keys of (act type, number, year)
name two or more corpus acts and 1,038 acts sit in such a group, because
ministries number independently. So a stated year is never crossed, a
stated date must agree, and an exact key needs every coordinate the
citation states. A citation whose key and stated full date name one act
is then decided by the key alone, and refused only when the two SUBJECT
clauses, the part after the number and the date, share not one content
word (`subject_unrelated`). Anything less is settled on the subject
clause, under the 0.90 floor and the digit guard and nothing else when
exactly one candidate survives the date narrowing, where a content-word
difference is the flag `content_mismatch` rather than a refusal, and
under the fuzzy step's four bounds when more than one does, where it is
a refusal. Every refusal that got as far as comparing the subject
clauses reports its real score, so `unresolved.csv` shows the reader the
same near miss the resolver saw; a stated date that contradicts is
refused before any comparison and has none. `numbered_key_tie` is
reported when, and only when, the key named more than one act.

**A bounded fuzzy match**, for a title the Gazette and lex.bg word
differently. Four bounds, and a win needs all four:

- a floor of 0.90 on `difflib.SequenceMatcher.ratio`,
- a margin of 0.05 over the runner-up,
- identical digit sequences, and
- identical CONTENT words, which are the tokens of three letters or more
  that are not act-type nouns, ЗИД verbs or long prepositions.

**Measured by leave-one-out over all 3,624 corpus titles**, holding each
out and asking what the rest of the corpus offers in its place, which is
what a Gazette material naming an act the corpus does not hold looks
like. Wrong attributions, before and after:

| Step | Wrong |
|---|---|
| the digit guard and the 0.90 floor alone | 508 (33 fuzzy, 475 numbered) |
| a stated year never crossed | 267 |
| a stated date may contradict, and slashes stay in the number | 88 |
| an exact key needs every stated coordinate | 6 |
| content words must be equal | **0** |

The earlier evidence for the floor was measured over the 424 laws and
codes alone, where the digit guard does the work because the confusable
families are annual („за 2025 г.“ against „за 2026 г.“, 0.98). Laws and
codes are 12 % of the corpus. The other 3,200 acts are наредби and
правилници built from a fixed frame plus one distinguishing noun, and
that is where the minimal pairs live: „ДЪРЖАВНИТЕ ГОРСКИ СТОПАНСТВА“
against „ДЪРЖАВНИТЕ ЛОВНИ СТОПАНСТВА“ at 0.9489, „СЪДОВЕТЕ ПОД НАЛЯГАНЕ“
against „СЪОРЪЖЕНИЯТА ПОД НАЛЯГАНЕ“ at 0.9451, „ИГРАЧКИТЕ“ against
„МАШИНИТЕ“ at 0.9388. None of them differs in a digit.

The content guard costs nothing measurable. A reworded title, one
function word dropped, still resolves in 2,977 of 3,608 cases, and when
the guard was first written the looser readings of it, a superset or a
one-token difference, resolved exactly as many while leaving four wrong
attributions. What the guard does cost is stated plainly: a one-letter
typo inside a content word is a token substitution and is refused, so
such an event stays `unlocated` and `pending`, which blocks a grade and
writes nothing false.

Ambiguity that survives all three keys is broken by the inline
promulgation citation „(ДВ, бр. N от YYYY г.)“, cross-checked against the
candidate's `dv_issue`/`dv_year` and its chain. Nothing else breaks it.

**Every entry point cleans its input first.** The Gazette's own titles
carry the soft hyphen its typesetter left inside a word broken across a
line: 960 of them inside 777 of the 32,117 material titles of the
2026-09-05 enumeration, „Репуб­лика“, „Постанов­ление“. The character is
invisible in every viewer and it sits inside the act-type noun, which is
the first thing `act_type_of`, `numbered_key`, `strip_amending_prefix`
and `instruction_kind` read, so a hyphenated title used to take a
different path through all of them and `normalise_title` turned the
character into a SPACE, which split the word and missed the exact key
too. `clean_title` removes it and its five zero-width relatives, and
resolving 683 such titles that the coverage map had left unattributed
attributes 54 of them, 36 by the exact key and 18 by the numbered one.
"""

import copy
import difflib
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from fetcher.dv.sections import COUNCIL, MINISTRY, PARLIAMENT, section_kind

log = logging.getLogger(__name__)

#: Floor on the fuzzy ratio, and the margin the winner must hold over the
#: runner-up. Justified by the leave-one-out measurement in the module
#: docstring; both are needed, and neither is enough without the digit
#: guard of `_digits`.
FUZZY_THRESHOLD = 0.90
FUZZY_MARGIN = 0.05

#: Candidates below this cannot win and cannot be the runner-up the
#: margin is measured against, so `difflib`'s two upper bounds throw them
#: out before the real comparison. The body scan resolves on the order of
#: forty-two thousand titles against 2,645 наредби, and the full ratio on
#: every pair is hours of arithmetic for an answer the bounds already
#: give.
FUZZY_PREFILTER = FUZZY_THRESHOLD - FUZZY_MARGIN

#: The categories of the corpus tree, which are also the only act types
#: it holds. A Gazette title naming a постановление, указ, тарифа,
#: решение or договор has no corpus counterpart, and saying so is more
#: useful than „not found“.
CORPUS_ACT_TYPES = frozenset({"закон", "кодекс", "наредба", "правилник"})
CORPUS_CATEGORIES = ("laws", "codes", "ordinances", "regulations", "implementing")

#: The act types each Gazette section may issue. The gate applies to the
#: numbered key, where the number alone is ambiguous across the whole
#: corpus: „Наредба № 2 от 2001 г.“ is a ministerial act and cannot be a
#: material of Народно събрание, which issues закони and кодекси.
SECTION_ACT_TYPES = {
    PARLIAMENT: frozenset({"закон", "кодекс"}),
    COUNCIL: frozenset({"постановление", "наредба", "правилник"}),
    MINISTRY: frozenset({"наредба", "инструкция"}),
}

#: The definite forms of the act-type noun, which is how a ЗИД names its
#: target: „Закона за ...“, „Кодекса на ...“, „Наредбата за ...“.
_DEFINITE_NOUNS = {
    "закона": "закон",
    "кодекса": "кодекс",
    "наредбата": "наредба",
    "правилника": "правилник",
    "постановлението": "постановление",
    "указа": "указ",
    "тарифата": "тарифа",
    "инструкцията": "инструкция",
}

#: Act types as a title opens with them, definite or not. `rango` in the
#: frontmatter uses the same words, except „правилник по прилагане“,
#: which is a правилник whose title begins with „ПРАВИЛНИК ЗА ПРИЛАГАНЕ“.
_ACT_TYPE_WORDS = {
    "закон": "закон",
    "закона": "закон",
    "кодекс": "кодекс",
    "кодекса": "кодекс",
    "наредба": "наредба",
    "наредбата": "наредба",
    "правилник": "правилник",
    "правилника": "правилник",
    "правила": "правила",
    "правилата": "правила",
    "постановление": "постановление",
    "постановлението": "постановление",
    "указ": "указ",
    "указа": "указ",
    "тарифа": "тарифа",
    "тарифата": "тарифа",
    "инструкция": "инструкция",
    "инструкцията": "инструкция",
    "решение": "решение",
    "решението": "решение",
    "договор": "договор",
    "договора": "договор",
}

#: How far into a name the act-type word may sit. It is the first word
#: („Закона за X“, „Наредба № 3“) unless one or two adjectives precede it
#: („Устройствения правилник“, „Данъчно-осигурителния процесуален
#: кодекс“), which is as deep as the corpus goes.
_ACT_TYPE_LOOKAHEAD = 4

#: The operative verb of an amending, repealing or adopting title. What
#: follows „на“ is the act the instruction is about, which is the act the
#: event belongs to; what precedes it is the amending act's own name.
#:
#: The verb has to sit at the FIRST „за“ of the title, which is where a
#: Bulgarian act's subject clause opens. Scanning further finds a „за
#: отмяна на“ inside the subject of a title that repeals nothing:
#: „НАРЕДБА № Н-1 ... ЗА УСЛОВИЯТА И РЕДА ЗА ПОДАВАНЕ НА ДАННИ ..., И ЗА
#: ОТМЯНА НА ДИРЕКТИВА 2001/20/ЕО“ is a promulgation whose subject
#: recounts what the EU directive it implements repealed. Read the other
#: way it becomes a repeal, throws the наредба's own name away as the
#: matching key, and files an `estado` dispute against an act nobody
#: touched. `(?:(?!\bза\b).)*` is what keeps the search inside the head.
_PREFIX_RE = re.compile(
    r"(?:(?!\bза\b).)*\bза\s+(изменение\s+и\s+допълнение|изменение|допълнение|"
    r"отмяна|отменяне|приемане|одобряване|утвърждаване)\s+на\s+",
    re.IGNORECASE | re.DOTALL,
)
_CORRIGENDUM_RE = re.compile(r"^\s*поправк[аи]\s+(?:в|на)\s+", re.IGNORECASE)

#: What the operative verb of a title says the material does. Repeal is
#: separated from the rest because it is the one instruction the title
#: pass can turn into an `estado` finding: a Gazette repeal of an act the
#: corpus still calls „vigente“ (§5.2, D-064 item 5).
_INSTRUCTION_BY_VERB = {
    "изменение и допълнение": "amending",
    "изменение": "amending",
    "допълнение": "amending",
    "отмяна": "repeal",
    "отменяне": "repeal",
    "приемане": "adopting",
    "одобряване": "adopting",
    "утвърждаване": "adopting",
}

#: „..., приета с Постановление № 97 ... от 2013 г.“ and its variants.
#: The tail says which instrument adopted the target, not what the target
#: is called.
#:
#: An adoption is always in the instrumental: adopted WITH a decree. „,
#: издадени ОТ Международната федерация на счетоводителите“ names an
#: author, „, приети СЪГЛАСНО чл. 15“ a legal basis, „, приета В Ню Йорк“
#: a place, and „, ОБНОВЯВАНЕ, ПОДДЪРЖАНЕ“ is a list item, not an
#: abbreviation. Matching those cut most of eight corpus titles away,
#: two of them losing every digit, which voids the digit guard for them.
#: So the participle must be followed by „с“ or „със“, and „обн“ must be
#: an actual abbreviation.
_ADOPTION_TAIL_RE = re.compile(
    r",\s*(?:(?:приет|издаден|утвърден|одобрен)\w*\s+(?:със|с)\s|обн\.).*$",
    re.IGNORECASE | re.DOTALL,
)

#: The editorial note lex.bg appends when it renamed a title, and a
#: trailing promulgation citation. Neither is part of the act's name. A
#: parenthetical that is neither is left alone, because „ЗАКОН ЗА
#: ИЗПЪЛНЕНИЕ НА РЕГЛАМЕНТ (ЕС) 2019/125“ needs its own.
_TITLE_NOTE_RE = re.compile(r"\s*\(\s*ЗАГЛ[^()]*\)", re.IGNORECASE)
_TRAILING_CITATION_RE = re.compile(r"\s*\(\s*ДВ\s*,[^()]*\)\s*$", re.IGNORECASE)

_DV_CITATION_RE = re.compile(
    r"ДВ\s*,\s*бр\.?\s*(\d+)\s*от\s*(?:\d{1,2}\.\d{1,2}\.)?(\d{4})", re.IGNORECASE
)

#: An act number as the Gazette writes it: digits, Cyrillic or Latin
#: letters, dashes, and a slash when the slash is part of the number
#: („№ РД-07/2“ and „№ РД-07/8“ are two наредби). A slash before a
#: four-digit year separates the number from the year („№ 3/2001“), so it
#: is not taken.
_NUMBER_RE = re.compile(r"№\s*((?:[\wІі-]|/(?!\d{4}\b))+)", re.UNICODE)
_YEAR_RE = re.compile(r"\b(1[89]\d{2}|20\d{2})\b")
_DIGITS_RE = re.compile(r"\d+")

#: Latin letters the Gazette and the corpus use interchangeably with
#: their Cyrillic look-alikes inside an act number. Folding them is the
#: difference between finding „Наредба № Н-10“ and recording a Gazette
#: gap that is not there.
_HOMOGLYPHS = str.maketrans(
    {
        "A": "А", "B": "В", "C": "С", "E": "Е", "H": "Н", "I": "І",
        "K": "К", "M": "М", "O": "О", "P": "Р", "T": "Т", "X": "Х", "Y": "У",
    }
)
_DASHES = str.maketrans({"‐": "-", "‑": "-", "‒": "-",
                         "–": "-", "—": "-", "−": "-"})

#: Characters that occupy a position in the string and none on the page:
#: the soft hyphen the Gazette's typesetter left inside a word broken
#: across lines, the zero-width space and the two zero-width joiners, the
#: word joiner and the byte-order mark. They are written here as escapes
#: rather than as themselves, because a literal one in this file would be
#: invisible to every reader of it.
#:
#: The enumeration of 2026-09-05 counted 960 soft hyphens inside 777 of
#: the 32,117 material titles: „Репуб­лика“, „Постанов­ление“.
#: One inside the act-type noun is the worst place it can sit, since the
#: noun is what `act_type_of`, `numbered_key` and `strip_amending_prefix`
#: read first, and `normalise_title` turns the character into a SPACE,
#: which splits the word and misses the exact key too.
_INVISIBLE_RE = re.compile("[\\u00ad\\u200b\\u200c\\u200d\\u2060\\ufeff]")


def clean_title(text: str | None) -> str:
    """A title with the invisible characters taken out.

    Every entry point of this module calls it on its own input, so that a
    hyphenated title and a clean one are one string by the time anything
    is parsed, whichever door the caller came through.
    """
    if not text:
        return ""
    return _INVISIBLE_RE.sub("", str(text))


@dataclass(frozen=True)
class NumberedKey:
    """The identity of a numbered act: „Наредба № 8121з-1006 от 2015 г.“."""

    act_type: str
    number: str
    year: int | None


@dataclass(frozen=True)
class CorpusAct:
    """One act of the corpus, as the resolver needs to see it."""

    law_id: str
    title: str
    act_type: str
    category: str
    dv_issue: str | None
    dv_year: int | None
    fecha_publicacion: str | None
    #: „vigente“ or „derogado“ as lex.bg's history block left it. A
    #: witness, not an authority: a Gazette repeal that contradicts it is
    #: an `estado` dispute rather than a correction (D-064 item 5).
    estado: str | None
    #: Every (year, number) the act's `amendment_history` names, which is
    #: lex.bg's chain and therefore a witness, not an authority.
    chain: frozenset[tuple[int, int]]
    #: The same rows in order, each as ((year, number) or None, date or
    #: None). The order is the chain's order and the first row is the
    #: promulgation, which the coverage map needs to tell a base from an
    #: event; a row whose „dv“ is absent or unparseable keeps its date,
    #: which is still enough to place it before or after 1989.
    amendment_history: tuple[tuple[tuple[int, int] | None, str | None], ...]

    @classmethod
    def from_frontmatter(cls, *, law_id: str, category: str, frontmatter: dict):
        rango = (frontmatter.get("rango") or "").strip()
        # „правилник по прилагане“ is a правилник whose title opens with
        # „ПРАВИЛНИК ЗА ПРИЛАГАНЕ“, so the matching act type is правилник.
        act_type = "правилник" if rango.startswith("правилник") else rango
        chain = set()
        history: list[tuple[tuple[int, int] | None, str | None]] = []
        for row in frontmatter.get("amendment_history") or []:
            if not isinstance(row, dict):
                continue
            pair = parse_dv_reference(row.get("dv"))
            history.append((pair, _as_text(row.get("date"))))
            if pair is not None:
                chain.add(pair)
        return cls(
            amendment_history=tuple(history),
            law_id=law_id,
            title=(frontmatter.get("titulo") or "").strip(),
            act_type=act_type,
            category=category,
            dv_issue=_as_text(frontmatter.get("dv_issue")),
            dv_year=_as_int(frontmatter.get("dv_year")),
            fecha_publicacion=_as_text(frontmatter.get("fecha_publicacion")),
            estado=_as_text(frontmatter.get("estado")),
            chain=frozenset(chain),
        )

    @property
    def promulgation(self) -> tuple[int, int] | None:
        """The (year, number) of the act's own promulgation, if it cites one."""
        number = _as_int(self.dv_issue)
        if self.dv_year is None or number is None:
            return None
        return (self.dv_year, number)


@dataclass(frozen=True)
class Resolution:
    """What the resolver made of one title.

    `law_id` is the corpus act or None; `candidates` is what was
    considered, kept even when nothing was chosen so `unresolved.csv` can
    show the reader the same field the resolver saw; `score` is the
    winning similarity (1.0 for an exact or numbered key); `flags` is the
    uncertainty vocabulary of §4.1.
    """

    law_id: str | None
    candidates: tuple[str, ...]
    score: float
    flags: tuple[str, ...]
    method: str


def _as_text(value) -> str | None:
    if value is None:
        return None
    return str(value).strip() or None


def _as_int(value) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def parse_dv_reference(text) -> tuple[int, int] | None:
    """The (year, number) of an `amendment_history` row's „N/YYYY“."""
    if not text:
        return None
    match = re.fullmatch(r"\s*(\d+)\s*/\s*(\d{4})\s*", str(text))
    if match is None:
        return None
    return (int(match.group(2)), int(match.group(1)))


def parse_dv_citation(text: str | None) -> tuple[int, int] | None:
    """The (number, year) of an inline „(ДВ, бр. N от YYYY г.)“ citation."""
    if not text:
        return None
    match = _DV_CITATION_RE.search(text)
    if match is None:
        return None
    return (int(match.group(1)), int(match.group(2)))


def strip_amending_prefix(text: str) -> str:
    """What a ЗИД, a поправка or an adopting decree is about.

    „Закон за изменение и допълнение на Закона за X“ is an event in the
    chain of X, not an act of its own, so the name that matters is what
    follows the operative verb. „Постановление № 238 ... за изменение на
    Наредбата за Y, приета с Постановление № 97 ... от 2013 г.“ carries
    the decree's own number before the verb and the adopting decree after
    the target, and both must go: the first would attribute the event to
    whichever наредба happens to carry number 238.
    """
    stripped = _CORRIGENDUM_RE.sub("", clean_title(text))
    match = _PREFIX_RE.match(stripped)
    if match is not None and names_an_act(stripped[match.end():]):
        stripped = stripped[match.end():]
    return _ADOPTION_TAIL_RE.sub("", stripped).strip()


def names_an_act(text: str | None) -> bool:
    """Whether this text opens with the name of a normative act.

    The gate on the prefix strip, and the difference between an
    instruction about another act and an act's own subject. „НАРЕДБА № 1
    ОТ 2016 Г. ЗА ОДОБРЯВАНЕ НА МЕТОДИКА ЗА ...“ approves a methodology,
    which is what the наредба is FOR, not an instruction pointing at
    another act; stripping there threw the наредба's own name away and
    its number with it, and 95 numbered corpus acts were in that
    position, unreachable by any citation „Наредба № N от YYYY г.“. The
    same shape covers „ЗА ПРИЕМАНЕ НА ДЕКЛАРАЦИЯ ПО ЧЛ. 287 ...“ and „ЗА
    ОТМЯНА НА НОРМАТИВНИ АКТОВЕ“, which repeals acts it does not name.
    """
    if not text:
        return False
    words = re.sub(r"[^\w\s-]", " ", str(text).casefold()).split()
    return any(word in _ACT_TYPE_WORDS for word in words[:_ACT_TYPE_LOOKAHEAD])


def instruction_kind(title: str | None) -> str:
    """What a Gazette title says the material does to the act it names.

    „repeal“, „amending“, „adopting“, „corrigendum“, or „promulgation“
    for a title that names no other act and is therefore about itself.

    The distinction the coverage map needs is repeal against the rest: a
    material that repeals an act the corpus still records as `vigente` is
    an `estado` dispute the title pass can find on its own, while an
    amendment says nothing about whether the act is in force.
    """
    if not title:
        return "promulgation"
    title = clean_title(title)
    if _CORRIGENDUM_RE.match(title):
        return "corrigendum"
    cleaned = _TITLE_NOTE_RE.sub("", title)
    match = _PREFIX_RE.match(cleaned)
    if match is None or not names_an_act(cleaned[match.end():]):
        return "promulgation"
    verb = re.sub(r"\s+", " ", match.group(1)).casefold()
    return _INSTRUCTION_BY_VERB.get(verb, "amending")


def normalise_title(text: str | None) -> str:
    """The matching key of an act title.

    Casefolded (FR-019: Python's fold, because SQLite's `LOWER()` does
    not touch Cyrillic), without the editorial title-amendment note,
    without the amending prefix and the adoption tail, without
    punctuation, and with whitespace collapsed. Hyphens survive, because
    a hyphen inside a name carries meaning („Данъчно-осигурителен
    процесуален кодекс“) and every letter-and-dash act number is built
    out of them.
    """
    if not text:
        return ""
    stripped = _TITLE_NOTE_RE.sub("", clean_title(text))
    stripped = _TRAILING_CITATION_RE.sub("", stripped)
    stripped = strip_amending_prefix(stripped)
    folded = stripped.casefold()
    folded = folded.translate(_DASHES)
    folded = re.sub(r"[^\w\s№-]", " ", folded, flags=re.UNICODE)
    folded = re.sub(r"\s+", " ", folded).strip()
    # The definite act-type noun back to the nominative. This one is a
    # lookup and cannot be wrong, so it belongs in the key itself; the
    # adjectival forms, whose inverse is not a function, are offered as
    # readings by `title_variants` instead.
    head, _, tail = folded.partition(" ")
    if head in _DEFINITE_NOUNS:
        folded = _DEFINITE_NOUNS[head] + (f" {tail}" if tail else "")
    return folded


def title_variants(normalised: str) -> frozenset[str]:
    """The nominative readings of a title whose first word is declined.

    A citation names its target in the definite form and the corpus holds
    the nominative. Two shapes occur. The act-type noun takes the
    postpositive article („Закона“, „Наредбата“), which is a lookup and
    which `normalise_title` has already undone. An adjective takes the
    masculine short article and elides the fleeting
    vowel („наказателен“ becomes „наказателния“, „търговски“ becomes
    „търговския“, „семеен“ becomes „семейния“, „устройствен“ becomes
    „устройствения“), and the inverse is not a function: „...ния“ comes
    from „...ен“ with the elision and „...ения“ from „...ен“ without it.
    So every reading is offered and the corpus index decides, which is
    safe because the whole title must match, not the word.
    """
    if not normalised:
        return frozenset()
    head, _, tail = normalised.partition(" ")
    tail = f" {tail}" if tail else ""
    heads = {head}
    if head in _DEFINITE_NOUNS:
        heads.add(_DEFINITE_NOUNS[head])
    if head.endswith("ския"):
        heads.add(head[:-4] + "ски")
    if head.endswith("йния"):
        heads.add(head[:-4] + "ен")
    elif head.endswith("ния"):
        heads.add(head[:-3] + "ен")
    if head.endswith("ия"):
        heads.add(head[:-2])
    return frozenset(f"{item}{tail}" for item in heads)


def act_type_of(title: str | None) -> str | None:
    """The act type a title opens with, or None if it opens with nothing known."""
    normalised = normalise_title(clean_title(title))
    if not normalised:
        return None
    head = normalised.split(" ", 1)[0]
    return _ACT_TYPE_WORDS.get(head)


def _fold_number(raw: str) -> str:
    """One spelling for a number the corpus writes several ways."""
    folded = raw.strip().translate(_DASHES).upper().translate(_HOMOGLYPHS)
    return folded.strip("-.,;:")


def numbered_key(title: str | None) -> NumberedKey | None:
    """The (act type, number, year) a numbered title or citation names.

    Read from the TARGET of the title, so a ПМС that amends a наредба
    yields the наредба's number or nothing, never the decree's.

    The year is the one the title itself states („ОТ 22 АПРИЛ 2026 Г.“,
    „от 2026 г.“, „от 22.04.2026 г.“), taken from between the number and
    the subject clause that „за“ opens. 365 of the corpus's numbered
    наредби state no year at all, and for those the year is None and the
    number carries the identity alone.
    """
    if not title:
        return None
    target = strip_amending_prefix(_TITLE_NOTE_RE.sub("", clean_title(title)))
    act_type = act_type_of(target)
    if act_type is None:
        return None
    match = _NUMBER_RE.search(target)
    if match is None:
        return None
    rest = target[match.end():]
    subject = re.split(r"\s(?:за|относно|на)\s", rest, maxsplit=1, flags=re.IGNORECASE)[0]
    year_match = _YEAR_RE.search(subject)
    return NumberedKey(
        act_type=act_type,
        number=_fold_number(match.group(1)),
        year=int(year_match.group(1)) if year_match else None,
    )


#: Words that carry no identity: the act-type nouns, the operative verbs
#: of a ЗИД, and the prepositions and conjunctions of three letters or
#: more. Shorter function words („за“, „на“, „и“, „с“, „в“, „от“, „по“)
#: fall out of `_content` on length alone.
_STOP_WORDS = frozenset(_ACT_TYPE_WORDS) | frozenset(
    {
        "изменение", "изменението", "допълнение", "допълнението", "отмяна",
        "отменяне", "отменяване", "приемане", "одобряване", "утвърждаване",
        "поправка", "изм", "доп",
        "или", "със", "към", "над", "под", "при", "без", "чрез", "след",
        "преди", "между", "около", "срещу", "върху", "относно", "съгласно",
        "спрямо", "поради", "освен", "като", "чл", "бр",
    }
)


def _content(text: str) -> frozenset[str]:
    """The words of a title that say WHICH act it is.

    Tokens of three letters or more that are not act-type nouns, ЗИД
    verbs or long prepositions. What is left is the subject matter, and
    two titles whose subject matter differs are two acts.
    """
    words = []
    for word in text.split():
        letters = sum(1 for char in word if char.isalpha())
        if letters >= 3 and word not in _STOP_WORDS:
            words.append(word)
    return frozenset(words)


def _content_compatible(query: frozenset[str], candidate: frozenset[str]) -> bool:
    """Whether two titles may be compared at all.

    The guard the fuzzy step was missing. `difflib` measures characters,
    and 88 % of this corpus is наредби and правилници built from a fixed
    frame plus one distinguishing noun, so a single word apart scores 0.91
    to 0.95 and shares every digit: „ДЪРЖАВНИТЕ ГОРСКИ СТОПАНСТВА“ against
    „ДЪРЖАВНИТЕ ЛОВНИ СТОПАНСТВА“, „СЪДОВЕТЕ ПОД НАЛЯГАНЕ“ against
    „СЪОРЪЖЕНИЯТА ПОД НАЛЯГАНЕ“, „ИГРАЧКИТЕ“ against „МАШИНИТЕ“. Neither
    the 0.90 floor nor the digit guard sees any of them.

    The rule is equality, and the looser readings were measured rather
    than assumed. Allowing the query's content words to be a SUPERSET of
    the candidate's, or the two sets to differ by one token, was tried
    over the whole corpus by leave-one-out: it left four wrong
    attributions and resolved exactly as many reworded titles, 2,984 of
    3,608, as equality did. An extra content word names a different body
    („Правилник за устройството и дейността на АКАДЕМИЯТА на
    Министерството на вътрешните работи“ is not the правилник of the
    ministry) or a different instrument („Правилник ЗА ПОМИРЕНИЕ на
    Арбитражния съд“ is not its правилник), so the looser branches bought
    nothing and cost four.
    """
    return query == candidate


#: A day of the month inside the date segment of a numbered title. Its
#: presence is what tells „от 30 август 2016 г.“, a full date, from
#: „от 2016 г.“, which is a citation stating only the year.
_DAY_RE = re.compile(r"\b\d{1,2}\b")


def numbered_date(title: str | None) -> str | None:
    """The full date a numbered title states, or None if it states a year.

    „НАРЕДБА № 1 ОТ 30 АВГУСТ 2016 Г. ЗА ...“ gives „от 30 август 2016 г“.
    Together with the act type and the number that is five coordinates,
    which is as identifying as a numbered act gets, so it settles a tie on
    (act type, number, year) before anything is compared. A citation that
    states only the year cannot use it and falls through to the subject.
    """
    normalised = normalise_title(title)
    if not normalised:
        return None
    match = _NUMBER_RE.search(normalised)
    if match is None:
        return None
    rest = normalised[match.end():]
    head = re.split(r"\s(?:за|относно)\s", rest, maxsplit=1)[0].strip()
    if not head or not _DAY_RE.search(head):
        return None
    return head


def numbered_subject(title: str | None) -> str:
    """What a numbered title says after its number and its date.

    „НАРЕДБА № 6 ОТ 11 ФЕВРУАРИ 2021 Г. ЗА РЕДА ... В ОБЛАСТТА НА
    ВЕТЕРИНАРНАТА МЕДИЦИНА“ gives „реда ... в областта на ветеринарната
    медицина“. 363 keys of (act type, number, year) name two or more
    corpus acts and 1,038 acts sit in such a group, so the subject is
    what tells them apart; comparing the whole title instead compares the
    date the citation does not repeat.

    A title with no number gives its whole normalised self, so the
    function is total and the caller needs no special case.
    """
    normalised = normalise_title(title)
    if not normalised:
        return ""
    match = _NUMBER_RE.search(normalised)
    if match is None:
        return normalised
    rest = normalised[match.end():]
    parts = re.split(r"\s(?:за|относно)\s", rest, maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else rest.strip()


def _shares_nothing(one: str, other: str) -> bool:
    """Whether two subject clauses have no content word in common.

    Only a sanity check, and only where an exact key already decided: two
    texts this far apart are not one act under any renaming. It says
    nothing when either side has no content words at all, which a very
    short subject can leave.
    """
    left, right = _content(one), _content(other)
    return bool(left) and bool(right) and not (left & right)


def _digits(text: str) -> tuple[str, ...]:
    """Every number in a title, in order.

    A legal title's numbers identify it: a budget law „за 2025 г.“ and one
    „за 2026 г.“ differ by one character in sixty and score 0.98 against
    each other. The fuzzy step may not cross them.
    """
    return tuple(_DIGITS_RE.findall(text))


def load_corpus_acts(root, categories=CORPUS_CATEGORIES) -> list[CorpusAct]:
    """Read every act's frontmatter under `root`. Read-only, always.

    Only the YAML header is parsed; the body of a 500 KB кодекс is never
    read, which is what keeps a full pass over 3,624 acts at a few
    seconds.
    """
    root = Path(root)
    acts: list[CorpusAct] = []
    for category in categories:
        directory = root / category
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            frontmatter = read_frontmatter(path)
            if frontmatter is None:
                log.warning("%s has no YAML frontmatter; skipped", path)
                continue
            acts.append(
                CorpusAct.from_frontmatter(
                    law_id=path.stem, category=category, frontmatter=frontmatter
                )
            )
    return acts


def read_frontmatter(path) -> dict | None:
    """The YAML header of one corpus file, or None if it has none."""
    with Path(path).open("r", encoding="utf-8") as handle:
        if handle.readline().rstrip("\n") != "---":
            return None
        head: list[str] = []
        for line in handle:
            if line.rstrip("\n") == "---":
                break
            head.append(line)
        else:
            return None
    loaded = yaml.safe_load("".join(head))
    return loaded if isinstance(loaded, dict) else None


class Resolver:
    """Corpus acts in, `resolve` out. Built once, queried per material."""

    def __init__(self, corpus_acts):
        self._acts = tuple(corpus_acts)
        self._excluded: frozenset[str] = frozenset()
        self._by_id = {act.law_id: act for act in self._acts}
        self._by_title: dict[str, list[CorpusAct]] = {}
        self._by_number: dict[tuple[str, str], list[CorpusAct]] = {}
        self._normalised: dict[str, str] = {}
        #: The subject clause of a numbered title, which is what a tie on
        #: (act type, number, year) is broken on.
        self._subjects: dict[str, str] = {}
        #: The act's own (type, number, year) and stated date, so a
        #: citation can be checked against them without re-parsing.
        self._keys: dict[str, NumberedKey | None] = {}
        self._dates: dict[str, str | None] = {}
        for act in self._acts:
            key = normalise_title(act.title)
            self._normalised[act.law_id] = key
            self._subjects[act.law_id] = numbered_subject(act.title)
            if key:
                self._by_title.setdefault(key, []).append(act)
            self._dates[act.law_id] = numbered_date(act.title)
            numbered = numbered_key(act.title)
            self._keys[act.law_id] = numbered
            if numbered is not None:
                self._by_number.setdefault(
                    (numbered.act_type, numbered.number), []
                ).append((act, numbered))

    def holding_out(self, law_id: str) -> "Resolver":
        """A view of this resolver that has never seen one act.

        The leave-one-out measurement the fuzzy bounds are justified by
        asks, for each of 3,624 corpus titles, what the REST of the corpus
        offers in its place, which is what a Gazette material naming an
        act the corpus does not hold looks like. Rebuilding the index
        3,624 times is ten minutes; sharing it and hiding one act is
        seconds, which is the difference between a measurement that can be
        a test and one that can only be a note.
        """
        clone = copy.copy(self)
        clone._excluded = frozenset({law_id})
        return clone

    def resolve(self, title, *, section=None, dv_citation=None) -> Resolution:
        """The corpus act a Gazette title names, or None with the reason.

        `section` is the Gazette section the material sits in, which gates
        the numbered key. `dv_citation` is the inline promulgation
        citation, as a string or an already-parsed (number, year); when it
        is not given the title itself is searched for one.

        The title is cleaned of invisible characters before anything else
        happens, because the three keys below and the citation parser
        each read the raw text and a soft hyphen inside the act-type noun
        sends them down different paths.
        """
        title = clean_title(title)
        if dv_citation is not None and not isinstance(dv_citation, tuple):
            dv_citation = clean_title(dv_citation)
        normalised = normalise_title(title)
        if not normalised:
            return Resolution(None, (), 0.0, ("empty_title", "title_ambiguous"), "none")

        citation = (
            dv_citation
            if isinstance(dv_citation, tuple)
            else parse_dv_citation(dv_citation) or parse_dv_citation(title)
        )
        target_type = act_type_of(title)

        exact = self._exact(normalised)
        if exact:
            return self._decide(exact, 1.0, "exact", citation, target_type)

        numbered, considered, score, flags = self._numbered(title, section)
        if considered:
            return self._decide(
                numbered, score, "numbered", citation, target_type,
                extra=flags, reported=considered,
            )

        chosen, considered, score = self._fuzzy(normalised, section, target_type)
        return self._decide(
            chosen, score, "fuzzy", citation, target_type, reported=considered
        )

    # --- the three keys ---------------------------------------------------

    def _exact(self, normalised: str) -> list[CorpusAct]:
        found: list[CorpusAct] = []
        seen: set[str] = set()
        # Sorted, because `title_variants` is a frozenset and its
        # iteration order is per-process: `Resolution.candidates` has to
        # read the same in every run for the CSVs to be reproducible.
        for variant in sorted(title_variants(normalised)):
            for act in self._by_title.get(variant, ()):
                if act.law_id in self._excluded:
                    continue
                if act.law_id not in seen:
                    seen.add(act.law_id)
                    found.append(act)
        return found

    def _numbered(self, title, section):
        """The acts a numbered citation names, what was considered, the score.

        A stated year is identifying and is never crossed. The 365
        numbered наредби whose titles state no year stay candidates for
        any year, since silence cannot contradict; an act that states a
        DIFFERENT year is a different act, and widening to „any act with
        this number“ attributed 475 held-out titles to a sibling of
        another year, each reported as an exact key at 1.000.

        A key shared by several acts is settled first on the full date,
        which adds a day and a month to the type, the number and the year.
        That must survive a renamed title, because 282 corpus titles carry
        „(ЗАГЛ. ИЗМ. ...)“ and a 2016 material can differ from lex.bg's
        current text of the same наредба by a content word („спортна
        подготовка“ became „специализирана подготовка“ in 2019). But a
        date is not identifying on its own, since ministries number
        independently and two наредби № 6 can both be dated 11 February
        2021, so the subject must still clear the floor.

        Where the dates agree or the citation states none, the subject
        decides: under the floor and the digit guard always, and under
        the content guard by how many candidates SURVIVE the date
        narrowing below, not by how many the key named. Exactly one
        survivor takes the single-candidate branch, where a content-word
        difference is the flag `content_mismatch`; more than one goes to
        `_rank`, where the content guard is a veto and the row is
        refused. The two are independent, so a key that named several
        acts and was narrowed by a stated full date to one is attributed
        with `numbered_key_tie` for the tie and `content_mismatch` for
        the difference.
        """
        key = numbered_key(title)
        if key is None:
            return [], [], 0.0, ()
        allowed = SECTION_ACT_TYPES.get(section_kind(section)) if section else None
        if allowed is not None and key.act_type not in allowed:
            return [], [], 0.0, ()
        rows = [
            pair
            for pair in self._by_number.get((key.act_type, key.number), [])
            if pair[0].law_id not in self._excluded
        ]
        if key.year is None:
            matched = [act for act, _ in rows]
        else:
            matched = [act for act, other in rows if other.year in (key.year, None)]
        if not matched:
            return [], [], 0.0, ()
        unique_by_key = len(matched) == 1

        # A stated full date can CONTRADICT, not only settle. „№ Н-9 от 7
        # ноември 2018“ and „№ Н-9 от 4 април 2018“ are two наредби, and
        # with the first absent the key names exactly the second: 230
        # held-out titles used to resolve that way at a reported 1.000.
        # An act whose own title states no date is not contradicted by
        # one, since silence cannot contradict.
        stated = numbered_date(title)
        if stated is not None:
            same_date = [act for act in matched if numbered_date(act.title) == stated]
            if same_date:
                matched = same_date
            else:
                undated = [
                    act for act in matched if numbered_date(act.title) is None
                ]
                if not undated:
                    return [], matched, 0.0, ("numbered_date_mismatch",)
                matched = undated

        subject = numbered_subject(title)
        if len(matched) == 1:
            other = matched[0]
            other_subject = self._subjects[other.law_id]
            if unique_by_key and stated is not None and self._agrees(
                key, stated, other
            ):
                # A full date, every coordinate matched, and the key named
                # this act alone: an exact key, not a comparison. A year
                # without a day is not enough, since 363 keys of (type,
                # number, year) name two or more corpus acts, and two
                # citations „Наредба № 28 от 2004 г.“ reached the wrong
                # наредба that way.
                #
                # Four coordinates is a strong key and the subject is not
                # compared against it, with one exception: the corpus
                # holds five pairs of acts sharing (type, number, year,
                # date), and two subjects with not one content word in
                # common are not one act under any renaming.
                if _shares_nothing(subject, other_subject):
                    return (
                        [],
                        matched,
                        self._similarity(subject, other),
                        ("subject_unrelated",),
                    )
                return matched, matched, 1.0, ()

            # Otherwise the subject has to carry it. Either the key named
            # several acts and something narrowed it, or the candidate is
            # silent about a year or a date the citation states, which is
            # how 84 held-out titles reached the one наредба № 49 whose
            # title carries no date at all.
            flags = () if unique_by_key else ("numbered_key_tie",)

            # The digit guard is absolute here as everywhere: „подмярка
            # 19.4“ and „подмярка 19.5“ are two наредби, and „чл. 327“ is
            # not „чл. 328“. A renaming does not change a title's digits,
            # so the exemption below does not reach them.
            if _digits(other_subject) != _digits(subject):
                return (
                    [],
                    matched,
                    self._similarity(subject, other),
                    flags + ("numbered_digit_mismatch",),
                )

            score = self._similarity(subject, other)
            if score < FUZZY_THRESHOLD:
                return [], matched, score, flags

            # The content check is a FLAG here rather than a refusal, and
            # this is the one place the two differ. The branch exists to
            # catch a renamed title, and 282 corpus titles carry „(ЗАГЛ.
            # ИЗМ. ...)“: a 2016 material and lex.bg's current text of one
            # наредба differ by a content word („спортна подготовка“ became
            # „специализирана подготовка“ in 2019) and are one act. The
            # number and the year pin it, so refusing would lose the act
            # the branch is for. What the flag buys is that the row does
            # not look clean: it is attributed, and it carries
            # `content_mismatch` in the `resolver_flags` column of
            # `coverage-map.csv`, which a reader can filter by. It is NOT
            # a route. `scripts/dv_coverage_map.py` writes
            # `unresolved.csv` only for rows with no law id, so a flagged
            # row never reaches it; whether the reasoning pass reviews
            # these rows is that script's concern and is not built here.
            if not _content_compatible(_content(subject), _content(other_subject)):
                flags = flags + ("content_mismatch",)
            return matched, matched, score, flags

        chosen, considered, score = self._rank(subject, matched, subject=True)
        return chosen, considered, score, ("numbered_key_tie",)

    def _agrees(self, key: NumberedKey, stated: str | None, act: CorpusAct) -> bool:
        """Whether an act matches every coordinate the citation states.

        A citation that states a year or a date carries information; an
        act whose own title is silent about it does not match it, it
        merely fails to contradict. The difference decides whether this is
        an exact key or a comparison.
        """
        other = self._keys.get(act.law_id)
        if key.year is not None and (other is None or other.year != key.year):
            return False
        if stated is not None and self._dates.get(act.law_id) != stated:
            return False
        return True

    def _similarity(self, subject: str, act: CorpusAct) -> float:
        """How alike two subject clauses are. Reported, never decisive here."""
        return difflib.SequenceMatcher(
            None, self._subjects[act.law_id], subject
        ).ratio()

    def _fuzzy(self, normalised: str, section, target_type):
        pool = self._pool(section, target_type)
        return self._rank(normalised, pool)

    def _pool(self, section, target_type) -> list[CorpusAct]:
        acts = [act for act in self._acts if act.law_id not in self._excluded]
        if target_type is not None:
            return [act for act in acts if act.act_type == target_type]
        allowed = SECTION_ACT_TYPES.get(section_kind(section)) if section else None
        if allowed is None:
            return acts
        return [act for act in acts if act.act_type in allowed]

    def _rank(self, normalised: str, pool, *, subject: bool = False):
        """Who wins, who was considered, and the best score.

        Returns `(chosen, candidates, score)`. `chosen` is a one-element
        list or empty; `candidates` is everything that cleared the floor,
        reported whether or not it won, so `unresolved.csv` shows the
        reader the same near miss the resolver saw.

        Three bounds decide, and a win needs all three. The floor and the
        margin over the runner-up are about how alike two strings are.
        The content guard is about whether they are the same act at all:
        `difflib` measures characters, and 88 % of this corpus is наредби
        and правилници built from a fixed frame plus one distinguishing
        noun, so a single word apart scores 0.91 to 0.95 and shares every
        digit. It vetoes rather than prunes, so the near miss still
        reaches the report.

        `subject` only changes WHICH text is compared: the subject clause
        when the number and the date are already pinned, the whole title
        otherwise.
        """
        side = self._subjects if subject else self._normalised
        wanted = _digits(normalised)
        wanted_content = _content(normalised)
        matcher = difflib.SequenceMatcher(None)
        # `set_seq2` builds the index that `set_seq1` then reuses, so the
        # query goes in once and the candidates stream past it.
        matcher.set_seq2(normalised)
        scored: list[tuple[float, CorpusAct]] = []
        for act in pool:
            other = side[act.law_id]
            if not other or _digits(other) != wanted:
                continue
            matcher.set_seq1(other)
            if (
                matcher.real_quick_ratio() < FUZZY_PREFILTER
                or matcher.quick_ratio() < FUZZY_PREFILTER
            ):
                continue
            scored.append((matcher.ratio(), act))
        if not scored:
            return [], [], 0.0
        scored.sort(key=lambda pair: (-pair[0], pair[1].law_id))
        best = scored[0][0]
        runner_up = scored[1][0] if len(scored) > 1 else 0.0
        above = [act for ratio, act in scored if ratio >= FUZZY_THRESHOLD]
        if len(above) != 1:
            return [], above, best
        if best - runner_up < FUZZY_MARGIN:
            # Too close to call, even though only one cleared the floor.
            return [], [act for _, act in scored[:2]], best
        if not _content_compatible(wanted_content, _content(side[above[0].law_id])):
            return [], above, best
        return above, above, best

    # --- deciding ---------------------------------------------------------

    def _decide(self, candidates, score, method, citation, target_type,
                extra=(), reported=None) -> Resolution:
        ids = tuple(
            act.law_id for act in (candidates if reported is None else reported)
        )
        if len(candidates) == 1:
            return Resolution(candidates[0].law_id, ids, score, tuple(extra), method)

        if len(candidates) > 1 and citation is not None:
            narrowed = [act for act in candidates if _matches_citation(act, citation)]
            if len(narrowed) == 1:
                return Resolution(
                    narrowed[0].law_id,
                    ids,
                    score,
                    tuple(extra) + ("disambiguated_by_citation",),
                    method,
                )

        flags = list(extra) + ["title_ambiguous"]
        if candidates:
            flags.append("ambiguous_candidates")
        else:
            flags.append("no_candidate")
            if target_type is not None and target_type not in CORPUS_ACT_TYPES:
                flags.append("act_type_not_in_corpus")
        return Resolution(None, ids, score, tuple(flags), method)


def _matches_citation(act: CorpusAct, citation: tuple[int, int]) -> bool:
    """Whether an act was promulgated or amended by the cited issue.

    The citation is (number, year) as the Gazette writes it; the corpus
    keeps (year, number). The promulgation is the strong signal and the
    chain the weaker one, and both are lex.bg's assertion, so this
    narrows an ambiguity and never creates a match on its own.
    """
    number, year = citation
    return act.promulgation == (year, number) or (year, number) in act.chain
