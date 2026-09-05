"""The single corpus write gate (Part II Task 6 of the convergence plan).

Three guarantees are under test here, and they are the reason the gate exists
rather than a convention in a document:

1. **A defective act is never written.** The checks the CI runner applies
   corpus-wide are applied to the one act at ingestion, before any byte lands.
2. **A waiver is honoured at the gate exactly as the runner honours it**, on
   equality of the count, so an act that is waived for 22 remnants may be
   rewritten with 22 and never with 21 or 23.
3. **No second writer exists.** A static scan over the source tree fails if any
   module other than the gate writes a corpus file, which is what keeps the
   guarantee true when the Gazette patcher arrives.
"""

import inspect
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from corpus_gate import (
    CorpusIntegrityError,
    SourceRef,
    find_corpus_writers,
    render_act,
    write_act,
    write_act_text,
)

REPO = Path(__file__).resolve().parents[1]

_SIGNED = "  ruling: r\n  owner_signed: 2026-09-05\n  expires: when repaired\n"

_FM = {"titulo": "Закон за тест", "identificador": "1", "pais": "bg"}


def _waivers(tmp_path: Path, text: str = "{}\n") -> Path:
    path = tmp_path / "waivers.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def _laws(tmp_path: Path) -> Path:
    d = tmp_path / "laws"
    d.mkdir(parents=True, exist_ok=True)
    return d


# --- the plan's three tests -------------------------------------------------


def test_gate_refuses_an_act_with_a_markup_remnant(tmp_path):
    with pytest.raises(CorpusIntegrityError) as exc:
        write_act(
            tmp_path / "laws" / "bad.md",
            {"titulo": "X"},
            "**Чл. 1.**/span>. Текст.",
            source=SourceRef("lexbg", "123"),
            waivers_path=_waivers(tmp_path),
        )
    assert "tag_remnants" in str(exc.value)
    assert not (tmp_path / "laws" / "bad.md").exists()  # nothing written


def test_gate_writes_a_clean_act(tmp_path):
    _laws(tmp_path)
    write_act(
        tmp_path / "laws" / "ok.md",
        {"titulo": "X"},
        "**Чл. 1.** Текст.",
        source=SourceRef("lexbg", "123"),
        waivers_path=_waivers(tmp_path),
    )
    assert (tmp_path / "laws" / "ok.md").exists()


def test_only_the_gate_writes_corpus_files():
    """Structural guarantee: no second writer may exist, now or later."""
    offenders = find_corpus_writers(exclude={"corpus_gate.py"})
    assert offenders == [], f"corpus write outside the gate: {offenders}"


# --- the refusal names every violation with its locator ---------------------


def test_the_refusal_names_every_violation_with_its_locator(tmp_path):
    with pytest.raises(CorpusIntegrityError) as exc:
        write_act(
            tmp_path / "laws" / "bad.md",
            {"titulo": "X"},
            "**Чл. 1.**/span>\nЧисто.\n**Чл. 2.**SUP>",
            source=SourceRef("lexbg", "123"),
            waivers_path=_waivers(tmp_path),
        )
    assert len(exc.value.violations) == 2
    text = str(exc.value)
    # The rendered body starts one line below the frontmatter delimiter, so the
    # locators must be the ones the CI runner would print for the same file.
    assert "line 2" in text and "line 4" in text
    assert "/span>" in text and "SUP>" in text


def test_the_gate_has_no_force_flag():
    """A bypass would make the guarantee advisory rather than structural."""
    names = set(inspect.signature(write_act).parameters)
    assert not names & {"force", "skip_checks", "bypass", "no_verify", "ignore"}


# --- waivers apply at the gate, on equality of the count --------------------


def test_a_waived_act_is_written_when_its_count_matches_exactly(tmp_path):
    _laws(tmp_path)
    write_act(
        tmp_path / "laws" / "waived.md",
        _FM,
        "**Чл. 1.**/span>\n**Чл. 2.**/span>",
        source=SourceRef("lexbg", "1"),
        waivers_path=_waivers(
            tmp_path, "tag_remnants:\n" + _SIGNED + "  acts:\n    waived: 2\n"
        ),
    )
    assert (tmp_path / "laws" / "waived.md").exists()


def test_one_more_violation_than_the_waiver_pins_is_refused(tmp_path):
    """A waived act is not a blind spot for new defects of the same class."""
    with pytest.raises(CorpusIntegrityError) as exc:
        write_act(
            tmp_path / "laws" / "waived.md",
            _FM,
            "**Чл. 1.**/span>\n**Чл. 2.**/span>\n**Чл. 3.**/span>",
            source=SourceRef("lexbg", "1"),
            waivers_path=_waivers(
                tmp_path, "tag_remnants:\n" + _SIGNED + "  acts:\n    waived: 2\n"
            ),
        )
    assert len(exc.value.violations) == 1  # the excess only


def test_a_repaired_waived_act_is_refused_until_its_waiver_goes(tmp_path):
    """Equality both ways: the repair must land with the waiver update."""
    with pytest.raises(CorpusIntegrityError) as exc:
        write_act(
            tmp_path / "laws" / "waived.md",
            _FM,
            "**Чл. 1.** Чисто.",
            source=SourceRef("lexbg", "1"),
            waivers_path=_waivers(
                tmp_path, "tag_remnants:\n" + _SIGNED + "  acts:\n    waived: 2\n"
            ),
        )
    assert "stale" in str(exc.value).lower()
    assert not (tmp_path / "laws" / "waived.md").exists()


def test_a_partially_repaired_waived_act_is_refused_as_count_drift(tmp_path):
    with pytest.raises(CorpusIntegrityError) as exc:
        write_act(
            tmp_path / "laws" / "waived.md",
            _FM,
            "**Чл. 1.**/span>",
            source=SourceRef("lexbg", "1"),
            waivers_path=_waivers(
                tmp_path, "tag_remnants:\n" + _SIGNED + "  acts:\n    waived: 4\n"
            ),
        )
    assert "expected 4" in str(exc.value)


def test_a_waiver_for_another_act_does_not_cover_this_one(tmp_path):
    with pytest.raises(CorpusIntegrityError):
        write_act(
            tmp_path / "laws" / "other.md",
            _FM,
            "**Чл. 1.**/span>",
            source=SourceRef("lexbg", "1"),
            waivers_path=_waivers(
                tmp_path, "tag_remnants:\n" + _SIGNED + "  acts:\n    waived: 1\n"
            ),
        )


def test_a_waiver_for_another_check_does_not_cover_this_one(tmp_path):
    with pytest.raises(CorpusIntegrityError) as exc:
        write_act(
            tmp_path / "laws" / "waived.md",
            _FM,
            "**Чл. 1.**/span>",
            source=SourceRef("lexbg", "1"),
            waivers_path=_waivers(
                tmp_path, "chrome:\n" + _SIGNED + "  acts:\n    waived: 1\n"
            ),
        )
    assert "tag_remnants" in str(exc.value)


def test_the_legacy_list_form_of_a_waiver_is_a_schema_error_at_the_gate(tmp_path):
    """Count-blind waiving cannot be reinstated silently (requirement 6)."""
    _laws(tmp_path)
    with pytest.raises(ValueError, match="mapping"):
        write_act(
            tmp_path / "laws" / "ok.md",
            _FM,
            "**Чл. 1.** Чисто.",
            source=SourceRef("lexbg", "1"),
            waivers_path=_waivers(
                tmp_path, "tag_remnants:\n" + _SIGNED + "  acts: [waived]\n"
            ),
        )


# --- atomicity --------------------------------------------------------------


def test_a_refused_write_leaves_the_original_file_byte_identical(tmp_path):
    target = _laws(tmp_path) / "act.md"
    original = render_act(_FM, "**Чл. 1.** Оригинален текст.\n")
    target.write_text(original, encoding="utf-8")
    before = target.read_bytes()

    with pytest.raises(CorpusIntegrityError):
        write_act(
            target,
            _FM,
            "**Чл. 1.**/span> Ново.",
            source=SourceRef("lexbg", "1"),
            waivers_path=_waivers(tmp_path),
        )

    assert target.read_bytes() == before
    assert sorted(p.name for p in target.parent.iterdir()) == ["act.md"]


def test_a_successful_write_leaves_no_temporary_file(tmp_path):
    target = _laws(tmp_path) / "act.md"
    write_act(
        target, _FM, "**Чл. 1.** Текст.\n",
        source=SourceRef("lexbg", "1"), waivers_path=_waivers(tmp_path),
    )
    assert sorted(p.name for p in target.parent.iterdir()) == ["act.md"]
    assert target.read_text(encoding="utf-8").startswith("---\ntitulo: Закон за тест\n")


def test_the_gate_creates_the_category_directory_only_after_the_checks_pass(tmp_path):
    with pytest.raises(CorpusIntegrityError):
        write_act(
            tmp_path / "laws" / "bad.md", _FM, "**Чл. 1.**/span>",
            source=SourceRef("lexbg", "1"), waivers_path=_waivers(tmp_path),
        )
    assert not (tmp_path / "laws").exists()


# --- rendering: the gate is the assembler's superset, never its subset ------


def test_render_act_is_byte_identical_to_the_assembler(tmp_path):
    """Routing a writer through the gate must not rewrite what it emits."""
    from fetcher.bg.assembler import assemble_file

    meta = {
        "titulo": "Закон за тест",
        "identificador": "2135623256",
        "pais": "bg",
        "rango": "закон",
        "fecha_publicacion": "1991-07-13",
        "ultima_actualizacion": "2003-09-26",
        "estado": "vigente",
        "fuente": "lex.bg",
        "dv_issue": "56",
        "dv_year": 1991,
        "effective_date": "1991-07-13",
        "category": "laws",
        "eli": None,
        "amendment_history": [{"dv": "85/2003", "date": "2003-09-26"}],
    }
    body = "**Чл. 1.** Текст.\n"
    assert render_act(meta, body) == assemble_file(meta, body)


def test_render_act_round_trips_a_committed_act_without_churn(tmp_path):
    """Split it, change nothing, write it back: the bytes must be identical.

    Every reader hands the blank line after the frontmatter back as part of
    the body, so a renderer that adds its own would accrete one blank line per
    pass — 3 600 spurious diffs on the first corpus-wide backfill.
    """
    from corpus_integrity.loader import act_from_text

    original = render_act(_FM, "# Заглавие\n\n**Чл. 1.** Текст.\n")
    act = act_from_text(tmp_path / "laws" / "x.md", original, category="laws")
    assert act.body.startswith("\n")  # the split really does carry it
    assert render_act(act.frontmatter, act.body) == original


def test_render_act_keeps_a_key_the_assembler_would_drop(tmp_path):
    """The Gazette work adds a `provenance` block; dropping it silently would
    be a data loss the gate itself caused."""
    from fetcher.bg.assembler import assemble_file

    meta = dict(_FM, provenance={"grade": "B-pending"})
    assert "provenance" not in assemble_file(meta, "x")
    rendered = render_act(meta, "x")
    assert "provenance:" in rendered and "B-pending" in rendered


# --- the raw-text sibling ---------------------------------------------------


def test_write_act_text_gates_a_byte_level_edit(tmp_path):
    """`estado` flips are surgical edits to committed bytes; re-rendering the
    frontmatter would churn every file it touches, so the raw sibling exists —
    and it runs the same checks."""
    target = _laws(tmp_path) / "act.md"
    good = render_act(_FM, "**Чл. 1.** Текст.\n")
    write_act_text(target, good, source=SourceRef("lexbg", "1"),
                   waivers_path=_waivers(tmp_path))
    assert target.read_text(encoding="utf-8") == good

    with pytest.raises(CorpusIntegrityError):
        write_act_text(target, good.replace("Текст.", "Текст./span>"),
                       source=SourceRef("lexbg", "1"),
                       waivers_path=_waivers(tmp_path))
    assert target.read_text(encoding="utf-8") == good


# --- the source reference ---------------------------------------------------


def test_an_unknown_ingestion_kind_is_refused(tmp_path):
    _laws(tmp_path)
    with pytest.raises(ValueError, match="source"):
        write_act(
            tmp_path / "laws" / "ok.md", _FM, "**Чл. 1.** Текст.",
            source=SourceRef("scraped-by-hand", "1"),
            waivers_path=_waivers(tmp_path),
        )


def test_a_path_outside_a_corpus_category_is_refused(tmp_path):
    (tmp_path / "ords").mkdir()
    with pytest.raises(ValueError, match="category"):
        write_act(
            tmp_path / "ords" / "ok.md", _FM, "**Чл. 1.** Текст.",
            source=SourceRef("lexbg", "1"), waivers_path=_waivers(tmp_path),
        )


def test_a_staging_write_may_name_its_category_explicitly(tmp_path):
    """The Gazette rebuild stages a candidate outside the corpus tree; it is
    still gated, and it still declares which category it is checked as."""
    stage = tmp_path / "stage"
    stage.mkdir()
    write_act(
        stage / "act.md", _FM, "**Чл. 1.** Текст.", category="laws",
        source=SourceRef("dv", "242220"), waivers_path=_waivers(tmp_path),
    )
    assert (stage / "act.md").exists()


# --- the static scan --------------------------------------------------------


def _module(root: Path, name: str, src: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(src), encoding="utf-8")
    return path


def test_the_scan_catches_a_module_writing_into_laws(tmp_path):
    _module(tmp_path, "patcher.py", """
        from pathlib import Path

        def patch(slug, text):
            (Path(".") / "laws" / f"{slug}.md").write_text(text, encoding="utf-8")
    """)
    offenders = find_corpus_writers(root=tmp_path)
    assert [o.split(":")[0] for o in offenders] == ["patcher.py"]
    assert "write_text" in offenders[0]


def test_the_scan_catches_open_in_write_mode_and_shutil_copy(tmp_path):
    _module(tmp_path, "a.py", """
        def go(p):
            with open("ordinances/x.md", "w", encoding="utf-8") as fh:
                fh.write(p)
    """)
    _module(tmp_path, "b.py", """
        import shutil

        def go(src):
            shutil.copy(src, "codes/x.md")
    """)
    _module(tmp_path, "c.py", """
        from pathlib import Path

        def go(text):
            Path("implementing/x.md").open("w").write(text)
    """)
    _module(tmp_path, "d.py", """
        from pathlib import Path

        def go(data):
            Path("regulations/x.md").write_bytes(data)
    """)
    assert sorted({o.split(":")[0] for o in find_corpus_writers(root=tmp_path)}) == [
        "a.py", "b.py", "c.py", "d.py",
    ]


def test_the_scan_resolves_a_path_built_through_local_variables(tmp_path):
    """`filepath = output_dir / corpus_dir / f"{slug}.md"` is how the real
    writers address the corpus; a literal-only scan would miss every one."""
    _module(tmp_path, "runner.py", """
        from pathlib import Path

        CATEGORY_DIRS = {"ords": "ordinances"}

        def run(output_dir, entry, slug, text):
            corpus_dir = CATEGORY_DIRS.get(entry["category"], entry["category"])
            filepath = output_dir / corpus_dir / f"{slug}.md"
            filepath.write_text(text, encoding="utf-8")
    """)
    assert [o.split(":")[0] for o in find_corpus_writers(root=tmp_path)] == ["runner.py"]


def test_the_scan_catches_an_opaque_write_in_a_module_that_assembles_acts(tmp_path):
    """`ce.path.write_text(candidate)` carries no literal at all; the module
    names a category directory and assembles act text, so it is a writer."""
    _module(tmp_path, "sweep.py", """
        from fetcher.bg.assembler import assemble_file

        CATEGORY_DIRS = {"laws": "laws"}

        def run(entry, meta, body):
            entry.path.write_text(assemble_file(meta, body), encoding="utf-8")
    """)
    assert [o.split(":")[0] for o in find_corpus_writers(root=tmp_path)] == ["sweep.py"]


def test_the_scan_clears_a_report_write_next_to_the_corpus(tmp_path):
    """A module that reads the corpus and writes a report is not a writer."""
    _module(tmp_path, "report.py", """
        import json
        from pathlib import Path

        CATEGORY_DIRS = {"laws": "laws"}

        def run(root, findings):
            (root / "gate-report.json").write_text(json.dumps(findings))
            tmp = Path("state.json").with_suffix(".json.tmp")
            tmp.write_text("{}")
    """)
    assert find_corpus_writers(root=tmp_path) == []


def test_the_scan_ignores_reads_and_tests_and_the_gate_itself(tmp_path):
    _module(tmp_path, "reader.py", """
        from pathlib import Path

        def run():
            return Path("laws/x.md").read_text(encoding="utf-8"), open("laws/x.md").read()
    """)
    _module(tmp_path, "tests/test_thing.py", """
        from pathlib import Path

        def test_it(tmp_path):
            (tmp_path / "laws" / "x.md").write_text("---\\n---\\n")
    """)
    _module(tmp_path, "corpus_gate.py", """
        from pathlib import Path

        def _atomic_write(path, text):
            Path("laws/x.md").write_text(text)
    """)
    _module(tmp_path, ".venv/lib/thing.py", """
        from pathlib import Path
        Path("laws/x.md").write_text("x")
    """)
    assert find_corpus_writers(root=tmp_path, exclude={"corpus_gate.py"}) == []


def test_the_scan_reports_a_file_it_cannot_parse_rather_than_skipping_it(tmp_path):
    """A scan that silently skipped an unreadable file would report a clean
    tree over an unread one, which is the failure mode the runner refuses too."""
    _module(tmp_path, "broken.py", "def f(:\n")
    offenders = find_corpus_writers(root=tmp_path)
    assert [o.split(":")[0] for o in offenders] == ["broken.py"]
    assert "unparsable" in offenders[0]


# --- the runner and the gate honour the same waiver file --------------------


def test_the_committed_waiver_file_loads_under_the_strict_schema():
    """`docs/data/waivers.yaml` is the file the gate loads in production."""
    from corpus_integrity.waivers import load_waivers

    waivers = load_waivers(REPO / "docs" / "data" / "waivers.yaml")
    assert waivers["tag_remnants"]["kodeks-na-truda"] == 1
    assert all(isinstance(v, int) for v in waivers["tag_remnants"].values())
    assert waivers["frontmatter_dates"] == {}


def test_the_runner_json_carries_the_violation_rows(tmp_path):
    """The row a reviewer must walk to, not only how many there are."""
    import json

    d = tmp_path / "laws"
    d.mkdir()
    # Written exactly as the gate renders an act, so the locator the runner
    # prints is the locator the gate would have printed for the same act.
    (d / "bad.md").write_text(render_act({"titulo": "X"}, "**Чл. 1.**/span>\n"),
                              encoding="utf-8")
    _waivers(tmp_path)
    r = subprocess.run(
        [sys.executable, "-m", "corpus_integrity", "--root", str(tmp_path),
         "--waivers", str(tmp_path / "waivers.yaml"), "--json"],
        capture_output=True, text=True, cwd=REPO,
    )
    assert r.returncode == 1
    rows = json.loads(r.stdout)["checks"]["tag_remnants"]["violations"]
    assert rows == [
        {"check": "tag_remnants", "slug": "bad", "locator": "line 2",
         "detail": "markup remnant '/span>'"}
    ]
