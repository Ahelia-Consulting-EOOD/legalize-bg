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
letters and dashes („№ Н-10“, „№ РД-02-20-1“, „№ 8121з-1006“, „№ І-3“)
and the corpus writes the same series with Latin and with Cyrillic
look-alikes, so the number is folded before it is compared.

**A bounded fuzzy match**, for a title lex.bg and the Gazette word
differently. Three bounds, and the third is the one that matters:

- a floor of 0.90 on `difflib.SequenceMatcher.ratio`,
- a margin of 0.05 over the runner-up, and
- identical digit sequences in both titles.

Measured on the 424 laws and codes of the corpus, holding each title out
and asking what the rest of the corpus offers in its place: at 0.85 with
no guard, 32 of 424 held-out titles are attributed to some other act; at
0.85 with the margin, 20; with the digit guard added, 8 at 0.85, 1 at
0.88 and **0 at 0.90**. The digit guard does the work, because the
confusable families are annual („за 2025 г.“ against „за 2026 г.“, 0.98)
and numbers in a legal title identify the act rather than describe it.
The 0.90 floor costs nothing: with the de-articling of `title_variants`
the adjectival codes („Семейния кодекс“, „Административнопроцесуалния
кодекс“) match exactly rather than fuzzily.

Ambiguity that survives all three keys is broken by the inline
promulgation citation „(ДВ, бр. N от YYYY г.)“, cross-checked against the
candidate's `dv_issue`/`dv_year` and its chain. Nothing else breaks it.
"""

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
#: The tail says who adopted the target, not what the target is called.
_ADOPTION_TAIL_RE = re.compile(
    r",\s*(?:приет|приета|прието|приети|издаден|издадена|издадено|издадени|"
    r"утвърден|утвърдена|обн)\w*\b.*$",
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

_NUMBER_RE = re.compile(r"№\s*([\wІі-]+)", re.UNICODE)
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
    stripped = _CORRIGENDUM_RE.sub("", text)
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
    if _CORRIGENDUM_RE.match(str(title)):
        return "corrigendum"
    cleaned = _TITLE_NOTE_RE.sub("", str(title))
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
    stripped = _TITLE_NOTE_RE.sub("", str(text))
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
    normalised = normalise_title(title)
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
    target = strip_amending_prefix(_TITLE_NOTE_RE.sub("", str(title)))
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
        self._by_id = {act.law_id: act for act in self._acts}
        self._by_title: dict[str, list[CorpusAct]] = {}
        self._by_number: dict[tuple[str, str], list[CorpusAct]] = {}
        self._normalised: dict[str, str] = {}
        for act in self._acts:
            key = normalise_title(act.title)
            self._normalised[act.law_id] = key
            if key:
                self._by_title.setdefault(key, []).append(act)
            numbered = numbered_key(act.title)
            if numbered is not None:
                self._by_number.setdefault(
                    (numbered.act_type, numbered.number), []
                ).append((act, numbered))

    def resolve(self, title, *, section=None, dv_citation=None) -> Resolution:
        """The corpus act a Gazette title names, or None with the reason.

        `section` is the Gazette section the material sits in, which gates
        the numbered key. `dv_citation` is the inline promulgation
        citation, as a string or an already-parsed (number, year); when it
        is not given the title itself is searched for one.
        """
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

        numbered = self._numbered(title, section)
        if numbered:
            return self._decide(numbered, 1.0, "numbered", citation, target_type)

        fuzzy, score = self._fuzzy(normalised, section, target_type)
        return self._decide(fuzzy, score, "fuzzy", citation, target_type)

    # --- the three keys ---------------------------------------------------

    def _exact(self, normalised: str) -> list[CorpusAct]:
        found: list[CorpusAct] = []
        seen: set[str] = set()
        for variant in title_variants(normalised):
            for act in self._by_title.get(variant, ()):
                if act.law_id not in seen:
                    seen.add(act.law_id)
                    found.append(act)
        return found

    def _numbered(self, title, section) -> list[CorpusAct]:
        key = numbered_key(title)
        if key is None:
            return []
        allowed = SECTION_ACT_TYPES.get(section_kind(section)) if section else None
        if allowed is not None and key.act_type not in allowed:
            return []
        rows = self._by_number.get((key.act_type, key.number), [])
        matched = [act for act, other in rows if other.year == key.year]
        if not matched:
            # 365 numbered наредби state no year in their title, so a
            # citation that states one still has to reach them; a year
            # that matched something exactly is never widened this way.
            matched = [act for act, _ in rows]
        if len(matched) <= 1:
            return matched
        # A number and a year name several acts often enough that the
        # design makes the title tail part of the key: „Наредба № 1 от
        # 2016 г.“ is six corpus acts. The digit guard is off here: the
        # number and the year are already pinned, and what is left to
        # compare is a date the citation does not repeat.
        best, score = self._rank(normalise_title(title), matched, guard=False)
        return best if score >= FUZZY_THRESHOLD else matched

    def _fuzzy(self, normalised: str, section, target_type) -> tuple[list[CorpusAct], float]:
        pool = self._pool(section, target_type)
        return self._rank(normalised, pool)

    def _pool(self, section, target_type) -> list[CorpusAct]:
        if target_type is not None:
            return [act for act in self._acts if act.act_type == target_type]
        allowed = SECTION_ACT_TYPES.get(section_kind(section)) if section else None
        if allowed is None:
            return list(self._acts)
        return [act for act in self._acts if act.act_type in allowed]

    def _rank(self, normalised: str, pool, *, guard: bool = True) -> tuple[list[CorpusAct], float]:
        """The acts of `pool` above the floor, and the best score.

        Returns every act at or above the floor, so two near-equal
        candidates reach `_decide` as an ambiguity rather than as a
        winner. The margin rule catches the other shape: one candidate
        above the floor with a runner-up just below it.
        """
        wanted = _digits(normalised)
        matcher = difflib.SequenceMatcher(None)
        # `set_seq2` builds the index that `set_seq1` then reuses, so the
        # query goes in once and the candidates stream past it.
        matcher.set_seq2(normalised)
        scored: list[tuple[float, CorpusAct]] = []
        for act in pool:
            other = self._normalised[act.law_id]
            if not other or (guard and _digits(other) != wanted):
                continue
            matcher.set_seq1(other)
            if (
                matcher.real_quick_ratio() < FUZZY_PREFILTER
                or matcher.quick_ratio() < FUZZY_PREFILTER
            ):
                continue
            scored.append((matcher.ratio(), act))
        if not scored:
            return [], 0.0
        scored.sort(key=lambda pair: (-pair[0], pair[1].law_id))
        best = scored[0][0]
        runner_up = scored[1][0] if len(scored) > 1 else 0.0
        if best < FUZZY_THRESHOLD:
            return [], best
        above = [act for ratio, act in scored if ratio >= FUZZY_THRESHOLD]
        if len(above) == 1 and best - runner_up < FUZZY_MARGIN:
            # Too close to call, even though only one cleared the floor.
            return [act for _, act in scored[:2]], best
        return above, best

    # --- deciding ---------------------------------------------------------

    def _decide(self, candidates, score, method, citation, target_type) -> Resolution:
        ids = tuple(act.law_id for act in candidates)
        if len(candidates) == 1:
            return Resolution(candidates[0].law_id, ids, score, (), method)

        if len(candidates) > 1 and citation is not None:
            narrowed = [act for act in candidates if _matches_citation(act, citation)]
            if len(narrowed) == 1:
                return Resolution(
                    narrowed[0].law_id,
                    ids,
                    score,
                    ("disambiguated_by_citation",),
                    method,
                )

        flags = ["title_ambiguous"]
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
