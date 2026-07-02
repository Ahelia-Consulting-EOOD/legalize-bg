"""`legalize-bg-api` / `python -m api` — run the REST API with uvicorn."""

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="legalize-bg-api",
        description="legalize-bg REST API (FR-028) — FastAPI over the "
                    "shared query layer; per-request ro connections.")
    ap.add_argument("--db", type=Path, default=Path("catalog.db"))
    ap.add_argument("--corpus", type=Path, default=Path("."))
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8228)
    ap.add_argument("--cors-origin", action="append", default=[],
                    help="allowed origin (repeatable); e.g. "
                         "http://localhost:3000 for the Next.js dev server")
    args = ap.parse_args(argv)
    if not args.db.exists():
        print(f"catalog not found: {args.db} — run `python -m index.build` "
              "first", file=sys.stderr)
        return 2
    import uvicorn
    from api.app import create_app
    app = create_app(db_path=str(args.db), corpus_root=args.corpus,
                     cors_origins=args.cors_origin or None)
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
