"""The single sanctioned writer of a corpus `.md` file.

Part II Task 6 of `docs/plans/2026-08-11-corpus-correctness-convergence.md`.

Today's integrity checks are wired into `refresh.py` and `bootstrap.py`, which
is the lex.bg write path only. A Gazette patcher writing corpus files would be
a third writer, and nothing would force it through those checks: the guarantee
would lapse silently at exactly the moment the source changed. So the gate is
built as a property of *writing a corpus file*, before the second writer exists.

Three things make it a gate rather than a convention:

- **Every ingestion adapter calls it** — lex.bg refresh, Gazette consolidation,
  manual gap-fill, municipal — and `find_corpus_writers` fails the build if any
  module other than this one writes to a corpus path (defence in depth, Part
  IV.3 layer 1; the corpus-wide CI runner is layer 2).
- **There is no force flag.** A bypass would make the guarantee advisory. A
  refusal is fixed by repairing the act or by amending the waiver file, never
  by asking the gate to look away.
- **Waivers are honoured here exactly as the CI runner honours them**, through
  the same `corpus_integrity.waivers.reconcile`, on equality of the count: a
  waived act may be rewritten with the number of violations its census pinned
  and with no other number. More is an excess, fewer is count drift, none is a
  stale waiver, and all three are refusals — so a repair sweep lands the
  repaired act and its waiver update in one operation and never separately.
"""

from __future__ import annotations

import ast
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

from corpus_integrity.__main__ import CHECKS  # registered by append, see below
from corpus_integrity.loader import CATEGORY_DIRS, act_from_text
from corpus_integrity.protocol import Act, Violation
from corpus_integrity.waivers import load_waivers, reconcile

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent

# The waiver file the gate reads in production. Injectable for tests only; a
# run that silently used a different exception set than CI would defeat the
# point of running the same reconciliation.
DEFAULT_WAIVERS = REPO_ROOT / "docs" / "data" / "waivers.yaml"

# Where an act may come from. The value travels into the commit trailer, so an
# unknown kind is a usage error and not a free-text label.
SOURCE_KINDS: frozenset[str] = frozenset({"lexbg", "dv", "manual", "municipal"})

# Frontmatter key order, mirroring `fetcher/bg/assembler.assemble_file`. Keys
# outside these lists are kept and written after them: the assembler drops
# them, and a gate that silently dropped a frontmatter block would be causing
# the data loss it exists to prevent.
_MANDATORY: tuple[str, ...] = (
    "titulo", "identificador", "pais", "rango",
    "fecha_publicacion", "ultima_actualizacion", "estado", "fuente",
)
_EXTENSIONS: tuple[str, ...] = ("dv_issue", "dv_year", "effective_date", "category", "eli")
_TRAILING: tuple[str, ...] = ("amendment_history",)


@dataclass(frozen=True)
class SourceRef:
    """The ingestion path an act arrived by, for the commit trailer."""

    kind: str   # "lexbg" | "dv" | "manual" | "municipal"
    ident: str

    def __post_init__(self) -> None:
        if self.kind not in SOURCE_KINDS:
            raise ValueError(
                f"unknown source kind {self.kind!r}; one of {sorted(SOURCE_KINDS)}"
            )
        if not str(self.ident).strip():
            raise ValueError(f"source {self.kind!r} carries no identifier")


class CorpusIntegrityError(Exception):
    """A write refused because the act does not meet the correctness floor.

    Carries every violation with its locator, so the refusal is walkable: a
    message that says only „3 violations“ sends a reviewer back to the corpus
    to find out which.
    """

    def __init__(self, path: Path, violations: list[Violation]):
        self.path, self.violations = Path(path), list(violations)
        detail = "; ".join(
            f"{v.check}@{v.locator}: {v.detail}" for v in self.violations
        )
        super().__init__(f"{path}: {detail}")


# --- rendering --------------------------------------------------------------


def render_act(frontmatter: dict, body: str) -> str:
    """Serialise one act, byte-identically to `assemble_file` for its keys.

    The assembler emits a fixed whitelist and drops everything else. That is
    safe while the whitelist is the whole schema, and it stops being safe the
    moment a `provenance` block exists, so the gate writes the whitelist in the
    assembler's order and then every remaining key in insertion order.

    One leading newline is dropped, because the format already separates the
    frontmatter from the body with a blank line while every reader hands that
    blank line back as part of the body. Without the drop, the ordinary
    read-modify-write of an act — split it, change one field, write it — adds a
    blank line at the top of every act it touches, and a corpus-wide pass
    lands 3 600 spurious diffs. No parser output begins with a newline, so
    this never changes what an ingestion adapter writes.
    """
    if not isinstance(frontmatter, dict):
        raise ValueError(f"frontmatter is not a mapping: {type(frontmatter)!r}")
    if not isinstance(body, str):
        raise ValueError(f"body is not text: {type(body)!r}")
    if body.startswith("\n"):
        body = body[1:]

    ordered: dict = {}
    for key in (*_MANDATORY, *_EXTENSIONS, *_TRAILING):
        if key in frontmatter:
            ordered[key] = frontmatter[key]
    for key, value in frontmatter.items():
        if key not in ordered:
            ordered[key] = value

    yaml_str = yaml.dump(
        ordered, default_flow_style=False, allow_unicode=True, sort_keys=False
    )
    return f"---\n{yaml_str}---\n\n{body}"


# --- the checks, with the waiver reconciliation the runner uses -------------


_waiver_cache: dict[tuple[str, int, int], dict[str, dict[str, int | None]]] = {}


def load_waiver_set(path: Path | str | None = None) -> dict[str, dict[str, int | None]]:
    """Load the waiver file once per process (per path and per revision).

    A sweep calls the gate once per act, so re-parsing the file 3 600 times is
    pure waste; keying the cache on the file's identity as well as its path
    keeps a test that rewrites its own waiver file honest.

    The identity is `(mtime_ns, size)`. On a filesystem with coarse mtime
    granularity, a rewrite that changes no byte count within one tick would
    read a stale waiver set; the fix if that ever bites is to key on a hash,
    not to drop the cache.
    """
    resolved = Path(path or DEFAULT_WAIVERS).resolve()
    stat = resolved.stat()  # FileNotFoundError here is the right failure
    key = (str(resolved), stat.st_mtime_ns, stat.st_size)
    if key not in _waiver_cache:
        _waiver_cache[key] = load_waivers(resolved)
    return _waiver_cache[key]


def run_write_checks(
    act: Act, *, waivers: dict[str, dict[str, int | None]] | None = None
) -> list[Violation]:
    """Every registered check over one act, reconciled against its waiver.

    Returns the rows that refuse the write; an empty list is a pass. The
    reconciliation is `corpus_integrity.waivers.reconcile`, the same function
    the corpus-wide runner calls, so the gate and CI can never disagree about
    what a waiver covers.
    """
    waivers = load_waiver_set() if waivers is None else waivers
    refusals: list[Violation] = []
    # CHECKS is held by reference, so a later class registered with
    # `CHECKS.append(...)` is gated from the moment it is registered. Rebinding
    # the name in the runner would leave the gate on the old list, so a new
    # detector is appended and never assigned.
    for check in CHECKS:
        waived = waivers.get(check.name, {})
        expected = {act.slug: waived[act.slug]} if act.slug in waived else {}
        unwaived, stale, drift = reconcile(check.name, check.run([act]), expected)
        refusals.extend(unwaived)
        for slug in stale:
            refusals.append(Violation(
                check=check.name, slug=slug, locator=f"waiver:{check.name}",
                detail=(
                    f"stale waiver: waived for {expected[slug]} violation(s) and "
                    "now clean; the repair lands with the waiver removal, not "
                    "before it"
                ),
            ))
        for d in drift:
            refusals.append(Violation(
                check=check.name, slug=d.slug, locator=f"waiver:{check.name}",
                detail=(
                    f"waived for expected {d.expected} violation(s), found "
                    f"{d.actual}; update the waiver count in the same change"
                ),
            ))
    return refusals


# --- the gate ---------------------------------------------------------------


def write_act(
    path: Path | str,
    frontmatter: dict,
    body: str,
    *,
    source: SourceRef,
    category: str | None = None,
    waivers_path: Path | str | None = None,
) -> None:
    """The ONLY sanctioned writer of a corpus `.md` file.

    Every ingestion adapter calls this: lex.bg refresh, Gazette consolidation,
    manual gap-fill, municipal. There is deliberately no force flag — a bypass
    would make the guarantee advisory rather than structural.

    Raises `CorpusIntegrityError` naming every violation with its locator, and
    `ValueError` for a malformed call: an unknown source kind, a path outside
    the corpus categories, or a waiver file the strict schema refuses.
    """
    write_act_text(
        path, render_act(frontmatter, body),
        source=source, category=category, waivers_path=waivers_path,
    )


def write_act_text(
    path: Path | str,
    text: str,
    *,
    source: SourceRef,
    category: str | None = None,
    waivers_path: Path | str | None = None,
) -> None:
    """The same gate over an already-serialised act.

    An `estado` flip is a one-line edit to bytes that are already committed;
    round-tripping such a file through YAML would rewrite whatever the dumper
    formats differently today, churning acts the change never intended to
    touch. So a byte-level edit keeps its bytes and still passes every check.
    """
    path = Path(path)
    if not isinstance(source, SourceRef):
        raise ValueError(f"source must be a SourceRef, got {type(source)!r}")
    category = category or path.parent.name
    if category not in CATEGORY_DIRS:
        raise ValueError(
            f"{path}: category {category!r} is not a corpus category "
            f"{list(CATEGORY_DIRS)}; a write outside them lands where the index "
            "never scans"
        )

    act = act_from_text(path, text, category=category)
    violations = run_write_checks(act, waivers=load_waiver_set(waivers_path))
    if violations:
        raise CorpusIntegrityError(path, violations)

    _atomic_write(path, text)
    log.debug("wrote %s (%s-%s)", path, source.kind, source.ident)


def _atomic_write(path: Path, text: str) -> None:
    """Write through a temp file in the same directory, then `os.replace`.

    Same directory, so the replace is a rename within one filesystem and is
    atomic: a run interrupted mid-write leaves the previous act intact rather
    than half of the new one.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


# --- the structural guarantee: no second writer ------------------------------

# Directory names that identify a path as addressing the corpus.
_CORPUS_SEGMENTS: frozenset[str] = frozenset(CATEGORY_DIRS)

# Symbols that map a category onto a corpus directory. A writer addressing the
# corpus through the mapping carries no directory literal at all.
_CORPUS_SYMBOLS: frozenset[str] = frozenset(
    {"CATEGORY_DIRS", "CORPUS_DIRS", "CATEGORY_DIR", "_CORPUS_SEGMENTS"}
)

# Symbols that turn frontmatter and a body into corpus file content. A module
# that assembles an act and writes to a path the scan cannot resolve is a
# corpus writer until it proves otherwise.
_ASSEMBLY_SYMBOLS: frozenset[str] = frozenset(
    {"assemble_file", "write_act", "write_act_text", "render_act"}
)

_EXCLUDED_PARTS: frozenset[str] = frozenset(
    {".venv", "venv", ".git", "worktrees", "node_modules", "tests", "__pycache__"}
)

_WRITE_MODE_CHARS = frozenset("wax+")
# `shutil.move` sits here, not in _MOVE_FUNCS: it has no innocent idiom to protect
# (the repo has no production call to it), so it keeps BOTH rules, including the
# unresolved-destination fallback (re-review of PR #36).
_COPY_FUNCS = frozenset({"copy", "copy2", "copyfile", "copytree", "move"})

# Moves. A file that arrives by rename is as written as one that arrives by
# `write_text`, and staging outside the corpus then renaming in is both the
# gate's own idiom and the shape the Gazette rebuild is specified to use. They
# are judged on positive evidence only: a rename's destination is routinely a
# plain local, and the unresolved-path fallback would flag every atomic
# checkpoint write in a module that also touches the corpus.
_MOVE_FUNCS = frozenset({"replace", "rename"})


def find_corpus_writers(
    exclude: set[str] | None = None, *, root: Path | str | None = None
) -> list[str]:
    """Every module outside the gate that writes to a corpus path.

    Static, because the guarantee must hold for code that is never executed in
    CI. Each offender is reported as `relative/path.py:LINE: reason`, so the
    failure names the line to route rather than the file to argue about.

    A site puts a file somewhere: `write_text`, `write_bytes`, `open` in a
    write mode either bare or as `Path.open`, a `shutil` copy, and the moves —
    `os.replace`, `os.rename`, `shutil.move`, `Path.replace`, `Path.rename` —
    because a file that arrives by rename is as written as one that arrives by
    `write_text`, and staging outside the corpus then renaming in is both this
    module's own idiom and the shape the Gazette rebuild is specified to use.

    A site is an offender when either holds:

    1. its target path resolves — through local assignments, transitively — to
       a corpus category directory, or to a symbol that maps categories onto
       one. This catches both `Path("laws") / f"{slug}.md"` and the real
       writers' `output_dir / corpus_dir / f"{slug}.md"`;
    2. its target resolves to no path evidence at all *and* the module both
       names a corpus directory and assembles act content. This catches
       `entry.path.write_text(assemble_file(meta, body))`, where the path comes
       out of a record the scan cannot follow. The move shapes are exempt from
       this second rule and judged on rule 1 alone: a rename's destination is
       routinely a plain local, so applying it would flag every atomic
       checkpoint write in a module that also touches the corpus.

    Not scanned: `.venv`, `.git`, `__pycache__`, `node_modules`, any
    `worktrees` directory, and `tests/`, where a test writes its own temp
    corpus by design. A file that cannot be parsed is reported rather than
    skipped, because a scan that silently drops a file reports a clean tree
    over an unread one.

    Two residuals, stated rather than hidden. A module that names no category
    directory, assembles nothing, and writes to a path built entirely at
    runtime is not caught. Neither is a write performed by a subprocess — a
    shelled-out `tee`, `cp` or `git checkout` — since the scan reads Python
    and not the commands Python runs. Layer 2, the corpus-wide CI runner, is
    what catches the output of both.
    """
    exclude = set(exclude or ()) | {"corpus_gate.py"}
    root = Path(root or REPO_ROOT).resolve()
    offenders: list[str] = []

    for py in sorted(root.rglob("*.py")):
        rel = py.relative_to(root)
        if _EXCLUDED_PARTS & set(rel.parts) or rel.name in exclude or str(rel) in exclude:
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(rel))
        except (SyntaxError, UnicodeDecodeError) as exc:
            offenders.append(f"{rel}:1: unparsable, so unaudited ({exc.__class__.__name__})")
            continue
        offenders.extend(f"{rel}:{line}: {why}" for line, why in _scan_module(tree))

    return sorted(offenders)


def _scan_module(tree: ast.Module) -> list[tuple[int, str]]:
    assignments = _assignments(tree)
    module_names = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    } | {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    module_strings = {
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    corpus_aware = bool(_CORPUS_SYMBOLS & module_names) or any(
        _names_a_corpus_dir(s) for s in module_strings
    )
    assembles = bool(_ASSEMBLY_SYMBOLS & module_names)

    found: list[tuple[int, str]] = []
    for line, kind, target, positive_only in _write_sites(tree):
        strings, names = _evidence(target, assignments)
        if any(_names_a_corpus_dir(s) for s in strings) or (_CORPUS_SYMBOLS & names):
            found.append((line, f"{kind} into a corpus path"))
        elif not positive_only and not strings and corpus_aware and assembles:
            found.append((line, f"{kind} to an unresolved path in a module that "
                                "names a corpus directory and assembles acts"))
    return found


def _names_a_corpus_dir(text: str) -> bool:
    """True when a string literal addresses a corpus category directory."""
    parts = [p for p in text.replace("\\", "/").split("/") if p]
    return bool(_CORPUS_SEGMENTS & set(parts))


def _assignments(tree: ast.Module) -> dict[str, list[ast.expr]]:
    """`{name: [every expression ever assigned to it]}`, all scopes flattened.

    Flattened deliberately: the scan over-approximates rather than reasoning
    about scope, because a missed writer is a lapsed guarantee while a false
    positive is a routed writer.
    """
    out: dict[str, list[ast.expr]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            targets, value = [node.target], node.value
        else:
            continue
        if value is None:
            continue
        for target in targets:
            for name in _bound_names(target):
                out.setdefault(name, []).append(value)
    return out


def _bound_names(target: ast.expr) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        return [n for element in target.elts for n in _bound_names(element)]
    return []


def _evidence(
    expr: ast.expr | None, assignments: dict[str, list[ast.expr]], depth: int = 0
) -> tuple[set[str], set[str]]:
    """String constants and identifiers reachable from a path expression."""
    strings: set[str] = set()
    names: set[str] = set()
    if expr is None or depth > 6:
        return strings, names
    for node in ast.walk(expr):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.add(node.value)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Name):
            names.add(node.id)
            for assigned in assignments.get(node.id, []):
                if assigned is expr:
                    continue
                sub_strings, sub_names = _evidence(
                    assigned, {k: v for k, v in assignments.items() if k != node.id},
                    depth + 1,
                )
                strings |= sub_strings
                names |= sub_names
    return strings, names


def _write_sites(
    tree: ast.Module,
) -> Iterable[tuple[int, str, ast.expr | None, bool]]:
    """Every call that puts a file somewhere, and the expression naming where.

    The fourth element is `positive_only`: true for the move shapes, which are
    judged on resolved corpus evidence alone and never on an unresolved path.
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute):
            module = func.value.id if isinstance(func.value, ast.Name) else None
            if func.attr in ("write_text", "write_bytes"):
                yield node.lineno, f"{func.attr}()", func.value, False
            elif func.attr == "open" and _is_write_mode(node, first_arg_is_mode=True):
                yield node.lineno, "Path.open(w)", func.value, False
            elif func.attr in _COPY_FUNCS and module == "shutil":
                target = node.args[1] if len(node.args) > 1 else None
                yield node.lineno, f"shutil.{func.attr}()", target, False
            elif func.attr in _MOVE_FUNCS and module in ("os", "shutil"):
                # os.replace(src, dst), os.rename(src, dst)
                target = node.args[1] if len(node.args) > 1 else None
                yield node.lineno, f"{module}.{func.attr}()", target, True
            elif func.attr in ("replace", "rename") and _is_path_move(node):
                # p.replace(dst) / p.rename(dst). One positional argument and no
                # keywords is what separates these from str.replace, which
                # always takes two.
                yield node.lineno, f"Path.{func.attr}()", node.args[0], True
        elif isinstance(func, ast.Name) and func.id == "open":
            if _is_write_mode(node, first_arg_is_mode=False):
                yield node.lineno, "open(w)", node.args[0] if node.args else None, False


def _is_path_move(call: ast.Call) -> bool:
    """True for `p.replace(dst)` / `p.rename(dst)`, false for `s.replace(a, b)`."""
    return len(call.args) == 1 and not call.keywords


def _is_write_mode(call: ast.Call, *, first_arg_is_mode: bool) -> bool:
    """True unless the call provably opens for reading only.

    An unreadable mode expression counts as a write: `open(p, "a" if r else "w")`
    is a writer, and so is anything the scan cannot evaluate.
    """
    index = 0 if first_arg_is_mode else 1
    mode: ast.expr | None = None
    for keyword in call.keywords:
        if keyword.arg == "mode":
            mode = keyword.value
    if mode is None and len(call.args) > index:
        mode = call.args[index]
    if mode is None:
        return False  # no mode given: read
    if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
        return bool(_WRITE_MODE_CHARS & set(mode.value))
    return True
