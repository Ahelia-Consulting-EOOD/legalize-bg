"""FR-032 segmenter tests. The load-bearing contract is the coverage
invariant: concatenating all segment spans reproduces the body exactly
(design 2026-07-21 Decision 2 — the answer to the 57%-provisions-coverage
trap and the D-047 lesson)."""

import pytest

from index.segments import SEG_MAX_BYTES, Segment, segment, segment_texts


def _concat(body: str, segs: list[Segment]) -> str:
    return "".join(body[s.start:s.end] for s in segs)


def _identity_normalize(text: str) -> str:
    return text


# ── segment(): shapes ──────────────────────────────────────────────────

def test_empty_body_yields_no_segments():
    assert segment("") == []


def test_no_anchors_yields_single_other_segment():
    body = "Постановление без членове.\n\nВтори абзац без котви.\n"
    segs = segment(body)
    assert [s.kind for s in segs] == ["other"]
    assert _concat(body, segs) == body


def test_preamble_then_articles():
    body = ("Обнародван ДВ бр. 1.\n\n"
            "**Чл. 1.** Първи член.\n\n"
            "**Чл. 2.** Втори член.\n")
    segs = segment(body)
    assert [(s.kind, s.label) for s in segs] == [
        ("preamble", ""), ("article", "чл. 1"), ("article", "чл. 2")]
    assert _concat(body, segs) == body


def test_act_starting_with_anchor_has_no_preamble():
    body = "**Чл. 1.** Първи член.\n\n**Чл. 2.** Втори.\n"
    segs = segment(body)
    assert [s.kind for s in segs] == ["article", "article"]
    assert _concat(body, segs) == body


def test_unbolded_article_anchor_is_recognized():
    body = "Чл. 5. Обикновен анкер.\n\nЧл. 5а. Кирилски суфикс.\n"
    segs = segment(body)
    assert [(s.kind, s.label) for s in segs] == [
        ("article", "чл. 5"), ("article", "чл. 5а")]


def test_paragraph_section_anchor():
    body = ("**Чл. 1.** Член.\n\n"
            "## ПРЕХОДНИ И ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ\n\n"
            "**§ 1.** Първи параграф.\n\n"
            "§ 2. Втори параграф.\n")
    segs = segment(body)
    kinds_labels = [(s.kind, s.label) for s in segs]
    assert ("para", "§ 1") in kinds_labels
    assert ("para", "§ 2") in kinds_labels
    assert _concat(body, segs) == body


def test_annex_anchor():
    body = ("**Чл. 1.** Член.\n\n"
            "**Приложение № 2 към чл. 1**\n\nСъдържание на приложението.\n")
    segs = segment(body)
    assert segs[-1].kind == "annex"
    assert segs[-1].label == "приложение 2"
    assert _concat(body, segs) == body


def test_heading_glues_to_following_segment():
    body = ("**Чл. 1.** Член first.\n\n"
            "## Глава втора\n\n"
            "**Чл. 2.** Член second.\n")
    segs = segment(body)
    assert [s.kind for s in segs] == ["article", "article"]
    second = body[segs[1].start:segs[1].end]
    assert "Глава втора" in second
    assert _concat(body, segs) == body


def test_alinea_continuation_stays_with_its_article():
    body = ("**Чл. 3.** (1) Първа алинея.\n\n"
            "(2) Втора алинея като отделен абзац.\n\n"
            "**Чл. 4.** Следващ член.\n")
    segs = segment(body)
    assert [s.label for s in segs] == ["чл. 3", "чл. 4"]
    first = body[segs[0].start:segs[0].end]
    assert "Втора алинея" in first


def test_inline_quoted_anchor_does_not_split_paragraph():
    body = ("**Чл. 7.** Текст който цитира Чл. 5. по средата на абзаца.\n\n"
            "**Чл. 8.** Следващ.\n")
    segs = segment(body)
    assert [s.label for s in segs] == ["чл. 7", "чл. 8"]


def test_coverage_invariant_on_mixed_act():
    body = ("Преамбюл.\n\n"
            "# Заглавие\n\n"
            "**Чл. 1.** (1) Едно. (2) Две.\n\n"
            "(3) Три.\n\n"
            "## ДОПЪЛНИТЕЛНИ РАЗПОРЕДБИ\n\n"
            "**§ 1.** Дефиниции.\n\n"
            "**Приложение № 1**\n\nТаблица.\n\n"
            "Заключителен ред без котва.")
    segs = segment(body)
    assert _concat(body, segs) == body
    assert segs[0].kind == "preamble"


# ── segment_texts(): chunking ──────────────────────────────────────────

def test_segment_texts_normalizes_each_segment():
    body = "**Чл. 1.** ПЪРВИ   член.\n"
    rows = segment_texts(body, str.lower)
    assert len(rows) == 1
    seg, text = rows[0]
    assert text == body.lower()


def test_oversized_segment_chunked_at_paragraph_boundaries():
    para = "Дълъг абзац от приложение. " * 40  # ~1 KB
    body = "**Приложение № 1**\n\n" + "\n\n".join([para] * 12)
    rows = segment_texts(body, _identity_normalize, max_bytes=4_000)
    assert len(rows) > 1
    assert all(s.kind == "annex" and s.label == "приложение 1"
               for s, _ in rows)
    assert all(len(t.encode("utf-8")) <= 4_000 for _, t in rows)
    assert "".join(body[s.start:s.end] for s, _ in rows) == body


def test_paragraphless_oversized_segment_hard_splits():
    # one giant paragraph with no \n\n boundaries — the spike found 9 such
    # rows in the live corpus; the hard byte-boundary fallback must apply
    body = "**Приложение № 1** " + "х" * 20_000
    rows = segment_texts(body, _identity_normalize, max_bytes=4_000)
    assert len(rows) > 1
    assert all(len(t.encode("utf-8")) <= 4_000 for _, t in rows)
    assert "".join(body[s.start:s.end] for s, _ in rows) == body


def test_chunk_spans_are_contiguous_and_labeled():
    body = "**Чл. 1.** " + "текст " * 2_000
    rows = segment_texts(body, _identity_normalize, max_bytes=3_000)
    for (a, _), (b, _) in zip(rows, rows[1:]):
        assert a.end == b.start
    assert {s.label for s, _ in rows} == {"чл. 1"}


def test_default_seg_max_bytes_is_400k():
    assert SEG_MAX_BYTES == 400_000


# ── real-corpus acceptance (skips when the corpus is absent) ───────────

import pathlib  # noqa: E402

_REPO = pathlib.Path(__file__).resolve().parent.parent.parent

# The spike's pathological set: the 3 formerly cap-truncated acts (annex-
# dominated, >1.9 MB normalized) + a zero-provision act (no Чл. anchors).
_PATHOLOGICAL = [
    "codes/kodeks-za-sotsialno-osiguryavane-zagl-izm-dv-br-67-ot-2003-g.md",
    "codes/kodeks-za-zastrahovaneto.md",
    "ordinances/naredba-za-kachestvoto-na-sotsialnite-uslugi.md",
    "laws/zakon-za-izplashtane-na-zadalzheniyata-ugovoreni-v-zlato.md",
]


def _read_body(rel: str) -> str:
    path = _REPO / rel
    if not path.exists():
        pytest.skip(f"corpus act missing: {rel}")
    raw = path.read_text(encoding="utf-8")
    return raw[4:].split("\n---\n", 1)[1]


@pytest.mark.parametrize("rel", _PATHOLOGICAL)
def test_real_act_coverage_invariant_and_chunk_bound(rel):
    from index.fts import bg_normalize

    body = _read_body(rel)
    segs = segment(body)
    assert _concat(body, segs) == body
    rows = segment_texts(body, bg_normalize)
    assert "".join(body[s.start:s.end] for s, _ in rows) == body
    assert all(len(t.encode("utf-8")) <= SEG_MAX_BYTES for _, t in rows)
