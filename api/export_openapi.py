"""Export/verify the REST OpenAPI contract (FR-028) — the REST analogue
of mcp_server.export_tools. The spec is generated from a THROWAWAY app
instance (db need not exist; no request is served)."""

import argparse
import json
import sys
from pathlib import Path

from api.app import create_app


def generate_spec() -> dict:
    app = create_app(db_path="catalog.db", corpus_root=Path("."))
    return app.openapi()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--output", type=Path)
    g.add_argument("--check", type=Path)
    args = ap.parse_args(argv)
    spec_dict = generate_spec()
    spec = json.dumps(spec_dict, ensure_ascii=False, indent=2,
                      sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(spec, encoding="utf-8")
        print(f"wrote {args.output}")
        return 0
    committed = args.check.read_text(encoding="utf-8")
    if committed != spec:
        print("openapi-rest.json is STALE — regenerate with --output",
              file=sys.stderr)
        return 1
    print(f"OK: {args.check} matches live app (version="
          f"{spec_dict['info']['version']}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
