"""Fetch-only: the Ministry of Justice portal's page of an act into the raw store (step S1 of the plan of 31 October 2026).

    python scripts/raw_fetch_moj.py ID [ID ...] [--out data/raw/moj] [--force]

The portal publishes consolidated texts at ``https://justice.government.bg/home/normdoc/{id}``, where ``id`` is the
act's lex.bg document id for the acts it holds (``docs/research/2026-06-22-I4-official-consolidation.md``). It holds
a curated subset, not the whole corpus: for an act it does not hold it answers a 500 page of 182 bytes. The script
fetches one page at a time with one request per second, keeps the body as ``<out>/<id>.html`` (an absent act's
answer as ``<id>.absent.html``, kept as the evidence of the absence) and appends one line per fetch to
``<out>/manifest.jsonl``: the id, the URL, the time, the HTTP status, the bytes, the SHA-256 and the outcome
(``ok``, ``absent`` or ``error``). A page already answered, ``ok`` or ``absent``, is not fetched again unless ``--force``; an error is asked again.
The portal is a witness (decision D-061): nothing here reads the text, and nothing here writes a corpus file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "moj"
URL = "https://justice.government.bg/home/normdoc/{id}"
RATE_LIMIT_SECONDS = 1.0
TIMEOUT = 30
UA = "legalize-bg witness fetch (one request per second)"


def manifest_rows(out: Path) -> list[dict]:
    p = out / "manifest.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def last_ok(out: Path, doc_id: str) -> dict | None:
    """The last answered fetch of the page: ``ok`` or ``absent`` (the portal's settled answer), never an error."""
    rows = [r for r in manifest_rows(out) if str(r.get("doc_id")) == str(doc_id) and r.get("outcome") in ("ok", "absent")]
    return rows[-1] if rows else None


def last_row(out: Path, doc_id: str) -> dict | None:
    rows = [r for r in manifest_rows(out) if str(r.get("doc_id")) == str(doc_id)]
    return rows[-1] if rows else None


def fetch_one(doc_id: str, out: Path, *, session=None, sleep=time.sleep, force: bool = False) -> dict:
    """Fetch one page and record it; returns the manifest row written (or the existing ok row)."""
    out.mkdir(parents=True, exist_ok=True)
    if not force:
        row = last_ok(out, doc_id)
        if row is not None and (out / row.get("file", f"{doc_id}.html")).exists():
            return {**row, "cached": True}
    session = session or requests.Session()
    url = URL.format(id=doc_id)
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    via = "requests"
    try:
        resp = session.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
        status, body = resp.status_code, resp.content
    except requests.exceptions.SSLError:
        # the portal's certificate chain does not verify against the Python bundle (31 October 2026) while the system's
        # trust store accepts it: the same request goes through curl, which uses that store; nothing else changes
        status, body = _curl(url)
        via = "curl"
    except requests.RequestException as exc:
        row = {"doc_id": str(doc_id), "url": url, "fetched_at": fetched_at, "status": None, "bytes": 0, "sha256": None,
               "outcome": "error", "detail": f"{type(exc).__name__}: {exc}"}
        _append(out, row)
        sleep(RATE_LIMIT_SECONDS)
        return row
    if status is None:
        row = {"doc_id": str(doc_id), "url": url, "fetched_at": fetched_at, "status": None, "bytes": 0, "sha256": None,
               "outcome": "error", "detail": "curl could not fetch the page either", "via": via}
        _append(out, row)
        sleep(RATE_LIMIT_SECONDS)
        return row
    if status == 200 and len(body) > 1000:
        outcome = "ok"
    elif status in (404, 500):
        outcome = "absent"   # the portal's answer for an act it does not hold (500, 182 bytes, measured 31 October 2026)
    else:
        outcome = "error"
    name = f"{doc_id}.html" if outcome == "ok" else f"{doc_id}.{outcome}.html"
    (out / name).write_bytes(body)
    row = {"doc_id": str(doc_id), "url": url, "fetched_at": fetched_at, "status": status, "bytes": len(body),
           "sha256": hashlib.sha256(body).hexdigest(), "outcome": outcome, "file": name, "via": via}
    _append(out, row)
    sleep(RATE_LIMIT_SECONDS)
    return row


def _curl(url: str) -> tuple[int | None, bytes]:
    """The page through the system's curl and trust store: (HTTP status, body), or (None, b"") when curl fails."""
    try:
        proc = subprocess.run(["curl", "-sS", "-m", str(TIMEOUT), "-A", UA, "-w", "\n%{http_code}", url], capture_output=True, timeout=TIMEOUT + 5)
    except (OSError, subprocess.TimeoutExpired):
        return None, b""
    if proc.returncode != 0 or b"\n" not in proc.stdout:
        return None, b""
    body, _, code = proc.stdout.rpartition(b"\n")
    return (int(code) if code.isdigit() else None), body


def _append(out: Path, row: dict) -> None:
    with (out / "manifest.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ids", nargs="+", help="the portal's document ids (the lex.bg ids for the acts it holds)")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--force", action="store_true", help="fetch again a page already fetched with outcome ok")
    args = ap.parse_args(argv)
    out = Path(args.out)
    for doc_id in args.ids:
        row = fetch_one(doc_id, out, force=args.force)
        print(f"{row['doc_id']}: {row['outcome']}" + (" (cached)" if row.get("cached") else "") + f" status {row.get('status')} bytes {row.get('bytes')} sha256 {str(row.get('sha256'))[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
