"""The material parser: a Gazette material's blocks read as header, instructions, quoted text and tail
(step F1 of the plan of 31 October 2026, part 1: the splitter extended as the materials need).

``split_dv`` cuts a material into blocks. This module decides nothing about the meaning of an instruction;
it reads the material's *skeleton*, which has a strict form (the owner's rule of 21 October 2026: the
structured skeleton of an act keeps mechanical checks), and records it as data:

- the **header**: the promulgation decree a law opens with (УКАЗ № … to the minister's countersignature),
  the issuing body a ministry's act opens with, the title lines, and the cited history line
  „(обн., ДВ, бр. 10 от 2018 г.; изм., …)“ that names the amended act's promulgation issue;
- the **instructions**: every ``§ N.`` of an amending material opens a node, ``N.`` an item under it,
  ``а)`` a letter, ``аа)`` a sub-letter; a block that opens with a quotation mark, or stands inside a
  quotation an earlier block left open, is **quoted text** (the new wording) and hangs under the last
  instruction; a centred heading inside the body („Преходни и заключителни разпоредби“) names the section
  the following §§ belong to; a § that opens „В Закона за … (обн., …)“ names another act, the **cross-act
  target** the attribution step resolves;
- the **tail**: the adoption formula, the signatures and the material's number.

Every block lands in exactly one role; ``check`` lists what the grammar could not place and what breaks
the sequence (a § out of order, an item not following, a quotation left open at the end). A material with
findings is still attributed by its title; the instruction step refuses it until the finding is read.

Nothing here calls a model or writes a corpus file.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

from .splitter import Block, SplitAct

KINDS = ("law", "code", "decree", "ordinance", "regulation", "instruction", "tariff", "corrigendum", "decision", "ukaz", "other")
ROLES = ("header", "instruction", "quoted", "continuation", "heading", "tail", "embedded", "act", "unplaced")
SECTIONS = ("body", "additional", "transitional", "final", "transitional_final")

_KIND_WORDS = (
    (re.compile(r"^(ЗАКОН|Закон)\b"), "law"), (re.compile(r"^(КОДЕКС|Кодекс)\b|КОДЕКС$"), "code"),
    (re.compile(r"^(ПОСТАНОВЛЕНИЕ|Постановление)\b"), "decree"), (re.compile(r"^(НАРЕДБА|Наредба)\b"), "ordinance"),
    (re.compile(r"^((УСТРОЙСТВЕН\s+)?ПРАВИЛНИК|(Устройствен\s+)?Правилник)\b"), "regulation"),
    (re.compile(r"^(ИНСТРУКЦИЯ|Инструкция)\b"), "instruction"), (re.compile(r"^(ТАРИФА|Тарифа)\b"), "tariff"),
    (re.compile(r"^(ПОПРАВКА|Поправка)\b"), "corrigendum"), (re.compile(r"^(РЕШЕНИЕ|Решение)\b"), "decision"),
    (re.compile(r"^(УКАЗ|Указ)\b"), "ukaz"),
)
DECREE_START = re.compile(r"^УКАЗ №")
DECREE_END = re.compile(r"^Министър на правосъдието")
SIGN = re.compile(r"^(?:§\s*(\d+[а-я]?)\s*\.|(Параграф\s+единствен)\.)")
ITEM = re.compile(r"^(\d+[а-я]?)\.\s")
LETTER = re.compile(r"^([а-я])\)\s")
SUBLETTER = re.compile(r"^(([а-я])\2)\)\s")
ARTICLE = re.compile(r"^(?:Чл\.\s*\d|Член\s+единствен)")
ARTICLE_HEAD = re.compile(r"^Чл\.\s*(\d+[а-я]?)\.")
STRUCTURAL = re.compile(r"^(Част|Дял|Глава|Раздел|Подраздел)\s", re.I)
HISTORY_LINE = re.compile(r"^\(\s*([oо]бн|ДВ|изм|попр)", re.I)   # a Latin o for the Cyrillic one occurs in the Gazette's own text
HISTORY_IN_LINE = re.compile(r"\(\s*([oо]бн\.|ДВ\s*,)", re.I)        # older materials append the history to the title line itself
PROVISIONS = re.compile(r"^(допълнителн|преходн|заключителн)\S*(\s+и\s+\S+)?\s+разпоредб", re.I)   # „Допълнителна информация“ in an annex is no heading
ADOPTION = re.compile(r"^(Законът|Кодексът|Законите)\s+(е|са)\s+приет")
SIGNATURE = re.compile(r"^(Председател|Заместник-председател|Зам\.-председател|За председател|Министър|За министър|Министър-председател|"
                       r"Главен секретар|Изпълнителен директор|Директор|Управител|Секретар|Конституционни съдии|Президент|Подпечатан с държавния печат|"
                       r"Съдия-докладчик|Зам\. министър-председател|Заместник министър-председател|Генерален директор|Главен директор|Началник|Ръководител|Говорител|"
                       r"Главен прокурор|Главен инспектор|Главен архитект|Областен управител|Кмет|Ректор|Председателстващ|Членове)\b")
NUMBER_LINE = re.compile(r"^\d{1,6}$")
QUOTE_OPEN = "„“\"«"
QUOTE_CLOSE = "“”\"»"
QUOTES = "„“”\"«»"
INLINE_QUOTE = re.compile(r"[„“\"«]([^„“”\"«»]*)[“”\"»]")
# the act another act's provision amends: „В Закона за данъците … (обн., ДВ, бр. 95 от 2006 г.; изм., …) се правят …“, or „Законът за … се отменя“
CROSS_ACT = re.compile(r"^(?:В|Във)\s+(?P<title>[А-ЯA-Z][^()]{3,220}?)\s*"
                       r"\((?P<cite>(?:[oо]бн|ДВ)[^()]*(?:\([^()]*\)[^()]*)*)\)", re.S)
CROSS_ACT_REPEAL = re.compile(r"^(?P<title>[А-ЯA-Z][^()]{3,220}?)\s*"
                              r"\((?P<cite>(?:[oо]бн|ДВ)[^()]*(?:\([^()]*\)[^()]*)*)\)\s*се\s+отменя", re.S)
CITED_ISSUE = re.compile(r"бр\.\s*((?:\d+(?:\s*,\s*|\s+и\s+)?)+)\s*от\s*(\d{4})")
BULGARIAN_LETTERS = "абвгдежзиклмнопрстуфхцчшщюя"
TOKEN_CHARS = 3.2   # characters per token for Bulgarian in this model's tokeniser, measured on the structure-map runs (D-070's design study)


@dataclass
class Node:
    id: str
    level: int
    block: int
    text: str
    section: str = "body"
    children: list["Node"] = field(default_factory=list)
    quoted: list[int] = field(default_factory=list)
    continuation: list[int] = field(default_factory=list)
    inline_quotes: list[str] = field(default_factory=list)
    target: dict | None = None   # the act another § names: {"title", "cite", "promulgation": [n, y] | None, "issues": [[n, y], ...], "repeal": bool}

    def to_dict(self) -> dict:
        d = asdict(self)
        d["children"] = [c.to_dict() for c in self.children]
        return d


@dataclass
class Material:
    kind: str
    amending: bool
    own_title: str
    target_title: str | None          # the act the title says it amends, as cited, or None
    cited_history: dict | None        # {"promulgation": [n, y] | None, "issues": [[n, y], ...], "text": ...} from the title's history line
    body_org: str | None
    header: list[int]
    nodes: list[Node]
    headings: list[int]
    tail: list[int]
    roles: dict[int, str]
    findings: list[dict]
    blocks: int
    embedded: dict | None = None        # {"start": block, "title": text}: the act a decree adopts, printed after the decree's signatures
    instruction_kind: str = "unknown"   # the resolver's reading of the title: promulgation | amending | repeal | adopting | corrigendum
    whole_act: bool = False             # a promulgation: the blocks before its own final provisions carry the role "act"

    def to_dict(self) -> dict:
        d = {k: v for k, v in asdict(self).items() if k != "nodes"}
        d["nodes"] = [n.to_dict() for n in self.nodes]
        d["roles"] = {str(k): v for k, v in self.roles.items()}
        return d

    def instructions(self) -> list[Node]:
        """Every node in document order, depth first."""
        out: list[Node] = []

        def walk(ns: list[Node]) -> None:
            for n in ns:
                out.append(n)
                walk(n.children)
        walk(self.nodes)
        return out

    def targets(self) -> list[Node]:
        return [n for n in self.instructions() if n.target]

    def section_of(self, node: Node) -> str:
        return node.section


def parse_cited_history(text: str) -> dict:
    """The issues a history line cites: the first is the promulgation („обн., ДВ, бр. 10 от 2018 г.; изм., бр. 27 и 92 от 2018 г.“)."""
    issues: list[list[int]] = []
    for nums, year in CITED_ISSUE.findall(text):
        for n in re.findall(r"\d+", nums):
            issues.append([int(n), int(year)])
    return {"promulgation": issues[0] if issues else None, "issues": issues, "text": text.strip()}


def _without_history(text: str) -> str:
    """A title line without the history the Gazette appends to it in parentheses („… (обн., ДВ, бр. 103 от 2004 г.; изм., …)“)."""
    m = HISTORY_IN_LINE.search(text)
    return text[:m.start()].rstrip(" ,") if m else text


def _kind_of(text: str) -> str | None:
    for rx, kind in _KIND_WORDS:
        if rx.search(text.strip()):
            return kind
    return None


def _opens_body(text: str) -> bool:
    return bool(SIGN.match(text) or ARTICLE.match(text) or STRUCTURAL.match(text))


def _quote_delta(text: str) -> int:
    return sum(text.count(c) for c in QUOTES) % 2


def _target(text: str) -> dict | None:
    m = CROSS_ACT.match(text)
    repeal = False
    if not m:
        m = CROSS_ACT_REPEAL.match(text)
        repeal = bool(m)
    if not m:
        return None
    cite = parse_cited_history(m.group("cite"))
    return {"title": re.sub(r"\s+", " ", m.group("title")).strip(" ,"), "cite": cite["text"], "promulgation": cite["promulgation"],
            "issues": cite["issues"], "repeal": repeal}


def _head_stripped(text: str) -> str:
    """The instruction's text without its own § or item head, so a cross-act citation is read from its first word."""
    for rx in (SIGN, ITEM, SUBLETTER, LETTER, ARTICLE_HEAD):
        m = rx.match(text)
        if m:
            return text[m.end():].lstrip()
    return text


def _closes(text: str) -> bool:
    """A block that ends a quotation: an unmatched closing mark at its end (its marks are odd and its last one, before
    trailing punctuation, closes); a block of one mark alone, as the Gazette prints after a quoted table, closes too."""
    t = text.rstrip().rstrip(".;,:)")
    return bool(t) and t[-1] in QUOTE_CLOSE and _quote_delta(text) == 1


def _resumes(text: str, m_sign, stack: list, expected_sign: int, section: str) -> bool:
    """Whether a block inside a quoted run carries the amending act's next number: § expected_sign, or the next item of the open §,
    or the next letter of the open item, or a provisions heading of the amending act, or a signature."""
    if m_sign and m_sign.group(1):
        m = re.match(r"\d+", m_sign.group(1))
        return bool(m) and int(m.group()) == expected_sign and not re.search(r"[а-я]$", m_sign.group(1))
    mi = ITEM.match(text)
    if mi and stack:
        nums = [c.id.rsplit(".", 1)[-1] for c in stack[0].children]
        last = re.match(r"\d+", nums[-1]).group() if nums else "0"
        return mi.group(1).isdigit() and int(mi.group(1)) == int(last) + 1 and int(mi.group(1)) > 1
    ml = LETTER.match(text)
    if ml and len(stack) >= 2:
        letters = [c.id.rsplit(".", 1)[-1] for c in stack[1].children]
        return bool(letters) and len(letters[-1]) == 1 and BULGARIAN_LETTERS.find(ml.group(1)) == BULGARIAN_LETTERS.find(letters[-1]) + 1
    return bool(SIGNATURE.match(text)) or (bool(PROVISIONS.match(text)) and section == "body")


def _ends_with_closer(text: str) -> bool:
    t = text.rstrip().rstrip(".;,:)")
    return bool(t) and t[-1] in QUOTE_CLOSE


def _opens(text: str) -> bool:
    """A block that opens a quotation and does not close it: it starts with an opening mark and its marks are odd."""
    return text[:1] in QUOTE_OPEN and _quote_delta(text) == 1


def parse(act: SplitAct) -> Material:
    """Read a split Gazette material's skeleton; ``act.blocks`` are the splitter's blocks of one material."""
    blocks = act.blocks
    n = len(blocks)
    roles: dict[int, str] = {}
    findings: list[dict] = []
    header: list[int] = []
    i = 0
    # the promulgation decree of a law
    if n and DECREE_START.match(blocks[0].text):
        end = next((k for k, b in enumerate(blocks) if DECREE_END.match(b.text)), None)
        if end is None:
            findings.append({"block": 0, "kind": "decree_without_end", "detail": "УКАЗ № … without the minister's countersignature"})
            end = 0
        header.extend(range(0, end + 1))
        i = end + 1
    # the title lines, up to the first body opener; the issuing body line of a ministry's act is among them
    body_org = None
    title_lines: list[int] = []
    kind = None
    cited_history = None
    while i < n and not _opens_body(blocks[i].text) and blocks[i].text[:1] not in QUOTE_OPEN and len(title_lines) <= 12:
        t = blocks[i].text
        if kind is None:
            k = _kind_of(t)
            if k is None and not title_lines and t == t.upper() and not HISTORY_LINE.match(t):
                body_org = t
            elif k is not None:
                kind = k
        mh = HISTORY_IN_LINE.search(t)
        if mh and cited_history is None:
            cited_history = parse_cited_history(t[mh.start():])
        title_lines.append(i)
        header.append(i)
        i += 1
    if kind is None:
        kind = "other"
    own_title = " ".join(_without_history(blocks[k].text) for k in title_lines if not HISTORY_LINE.match(blocks[k].text) and blocks[k].text != body_org).strip()
    # the tail, from the end: the number, the signatures, the adoption formula
    tail: list[int] = []
    j = n - 1
    while j >= i and NUMBER_LINE.match(blocks[j].text):
        tail.append(j); j -= 1
    while j >= i and blocks[j].text.strip() not in QUOTES and (SIGNATURE.match(blocks[j].text) or blocks[j].hint == "DvRight"
                      or (j - 1 >= i and blocks[j - 1].text.rstrip().endswith(":") and SIGNATURE.match(blocks[j - 1].text) and len(blocks[j].text) < 60)):
        tail.append(j); j -= 1
    if j >= i and ADOPTION.match(blocks[j].text):
        tail.append(j); j -= 1
    tail.sort()
    body_end = j + 1
    for k in header:
        roles[k] = "header"
    for k in tail:
        roles[k] = "tail"
    from fetcher.dv.resolver import instruction_kind, strip_amending_prefix
    ik = instruction_kind(own_title)
    target_title = strip_amending_prefix(own_title) or None if ik in ("amending", "repeal", "corrigendum") else None
    # a whole act (a promulgation): its text is not instructions; only the §§ of its own final provisions are read, for the
    # acts they amend („§ 17. В Закона за наследството (обн., …)“), and the labeller route reads the act itself
    whole_act = kind not in ("decree", "decision", "ukaz", "corrigendum") and ik == "promulgation" and i < body_end and (ARTICLE.match(blocks[i].text) or STRUCTURAL.match(blocks[i].text))
    act_end = i
    if whole_act:
        last_prov = max((k for k in range(i, body_end) if PROVISIONS.match(blocks[k].text) and len(blocks[k].text) < 80), default=None)
        act_end = last_prov if last_prov is not None else body_end
        for k in range(i, act_end):
            roles[k] = "act"
        i = act_end
    # the body
    nodes: list[Node] = []
    headings: list[int] = []
    embedded: dict | None = None
    stack: list[Node] = []   # the open nodes by level
    section = "body"
    quote_open = False
    depth = 0
    last: Node | None = None
    expected_sign = 1
    signed = False   # a signature line inside the body: the decree is over, an embedded act may follow
    k = i
    while k < body_end:
        b = blocks[k]
        t = b.text
        if embedded is not None:
            roles[k] = "embedded"
            k += 1
            continue
        m_sign = SIGN.match(t)
        if quote_open and _resumes(t, m_sign, stack, expected_sign, section):
            # the Gazette closes a nested quotation with one mark, so the marks' parity lies; the amending act's own sequence does
            # not: a § or an item carrying the number the sequence expects next resumes the instructions, whatever the marks said
            findings.append({"block": k, "kind": "quote_closed_by_sequence", "detail": f"the run before {t[:40]!r} is closed by the sequence, not by a mark"})
            quote_open = False
            depth = 0
        if quote_open:
            roles[k] = "quoted"
            last.quoted.append(k)
            if t.strip() in QUOTES:
                depth -= 1
            elif _opens(t):
                depth += 1
            elif _closes(t):
                depth -= 1
            quote_open = depth > 0
            k += 1
            continue
        if t[:1] in QUOTE_OPEN:
            if last is None:
                roles[k] = "unplaced"
                findings.append({"block": k, "kind": "quoted_before_instruction", "detail": t[:60]})
            else:
                roles[k] = "quoted"
                last.quoted.append(k)
                quote_open = _opens(t)
                depth = 1 if quote_open else 0
            k += 1
            continue
        if signed or (nodes and SIGNATURE.match(t) and (b.hint == "DvRight" or ":" in t)):
            if SIGNATURE.match(t) or b.hint == "DvRight":
                roles[k] = "tail"; tail.append(k); signed = True
                k += 1
                continue
            # the first block after the decree's signatures opens the act the decree adopts
            embedded = {"start": k, "title": t}
            roles[k] = "embedded"
            k += 1
            continue
        if m_sign:
            num = m_sign.group(1) or "единствен"
            node = Node(id=f"§{num}", level=0, block=k, text=t, section=section)
            if num != "единствен":
                key = int(re.match(r"\d+", num).group())
                if whole_act and not nodes:
                    expected_sign = key   # an act's own provisions continue its numbering; the sequence is checked from the first § read
                if key != expected_sign and not (key == expected_sign - 1 and re.search(r"[а-я]$", num)):
                    findings.append({"block": k, "kind": "sign_sequence", "detail": f"§ {num} where § {expected_sign} was expected"})
                expected_sign = key + 1
            nodes.append(node)
            stack = [node]
        elif ARTICLE.match(t) and kind == "decree" and not stack:
            m = ARTICLE_HEAD.match(t)
            node = Node(id=f"Чл.{m.group(1) if m else 'единствен'}", level=0, block=k, text=t, section=section)   # „Чл. 1. Приема Наредба за …“
            nodes.append(node)
            stack = [node]
        elif SUBLETTER.match(t) and len(stack) >= 3:
            m = SUBLETTER.match(t)
            node = Node(id=f"{stack[2].id}.{m.group(1)}", level=3, block=k, text=t, section=section)
            stack[2].children.append(node)
            stack = stack[:3] + [node]
        elif LETTER.match(t) and len(stack) >= 2 and not SUBLETTER.match(t):
            m = LETTER.match(t)
            node = Node(id=f"{stack[1].id}.{m.group(1)}", level=2, block=k, text=t, section=section)
            stack[1].children.append(node)
            stack = stack[:2] + [node]
        elif ITEM.match(t) and stack:
            m = ITEM.match(t)
            node = Node(id=f"{stack[0].id}.{m.group(1)}", level=1, block=k, text=t, section=section)
            stack[0].children.append(node)
            stack = stack[:1] + [node]
        elif (LETTER.match(t) or SUBLETTER.match(t) or ITEM.match(t)) and not stack:
            roles[k] = "act" if whole_act else "unplaced"
            if not whole_act:
                findings.append({"block": k, "kind": "item_without_sign", "detail": t[:60]})
            k += 1
            continue
        elif PROVISIONS.match(t) or (not stack and not ARTICLE.match(t) and (b.hint == "DvCenter" or (t == t.upper() and len(t) < 80))):
            roles[k] = "heading"
            headings.append(k)
            kinds = frozenset(x.lower() for x in re.findall(r"(допълнителн|преходн|заключителн)", t, re.I))
            if kinds:
                section = ("additional" if kinds == {"допълнителн"} else "transitional" if kinds == {"преходн"} else "final" if kinds == {"заключителн"} else "transitional_final")
            k += 1
            continue
        elif ARTICLE.match(t) or STRUCTURAL.match(t) or (whole_act and not stack):
            if whole_act:
                roles[k] = "act"   # an annex or a line of the act after its provisions heading
            else:
                # a provision printed without quotation marks inside an amending body: the Gazette's old form, or a lost quotation
                roles[k] = "unplaced"
                findings.append({"block": k, "kind": "unquoted_provision", "detail": t[:60]})
            k += 1
            continue
        elif last is not None and stack:
            roles[k] = "continuation"
            last.continuation.append(k)
            quote_open = bool(_quote_delta(t)) and not _closes(t)
            depth = 1 if quote_open else 0
            k += 1
            continue
        else:
            roles[k] = "act" if whole_act else "unplaced"
            if not whole_act:
                findings.append({"block": k, "kind": "unplaced", "detail": t[:60]})
            k += 1
            continue
        roles[k] = "instruction"
        node.inline_quotes = [q for q in INLINE_QUOTE.findall(t)]
        node.target = _target(_head_stripped(t))
        quote_open = bool(_quote_delta(t)) and not _closes(t)
        depth = 1 if quote_open else 0
        last = node
        k += 1
    tail.sort()
    if quote_open:
        findings.append({"block": body_end - 1, "kind": "quote_open_at_end", "detail": "a quotation is left open at the end of the body"})
    for k in range(n):
        roles.setdefault(k, "unplaced")
    # what the material says it does
    unquoted = any(f["kind"] == "unquoted_provision" for f in findings)
    amending = kind not in ("decision", "ukaz", "other") and not whole_act and (bool(target_title) or (bool(nodes) and embedded is None and not unquoted and ik != "adopting"))
    return Material(kind=kind, amending=amending, own_title=own_title, target_title=target_title, cited_history=cited_history, body_org=body_org,
                    header=header, nodes=nodes, headings=headings, tail=tail, roles=roles, findings=findings, blocks=n, embedded=embedded,
                    instruction_kind=ik, whole_act=whole_act)


def check(m: Material) -> list[str]:
    """The skeleton's mechanical checks: every block in one role, no unplaced block, the sequences hold, quotations closed."""
    out = [f"block {f['block']}: {f['kind']}: {f['detail']}" for f in m.findings]
    if sorted(m.roles) != list(range(m.blocks)):
        out.append("the roles do not cover every block exactly once")
    unplaced = [k for k, r in m.roles.items() if r == "unplaced"]
    if unplaced and not any(f["kind"] in ("unplaced", "quoted_before_instruction", "item_without_sign") for f in m.findings):
        out.append(f"{len(unplaced)} unplaced block(s) without a finding")
    for v in m.roles.values():
        if v not in ROLES:
            out.append(f"unknown role {v}")
    return out


def instruction_text_tokens(m: Material) -> int:
    """An estimate of the tokens the instruction step reads from this material: every instruction, quoted and continuation block."""
    chars = 0
    for node in m.instructions():
        chars += len(node.text)
    return int(chars / TOKEN_CHARS)


def quoted_tokens(m: Material, blocks: list[Block]) -> int:
    chars = sum(len(blocks[k].text) for node in m.instructions() for k in node.quoted + node.continuation)
    return int(chars / TOKEN_CHARS)
