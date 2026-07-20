"""Cloudflare export pipeline (spec: cf-data-plane-spec.md v1).

Reads catalog.db + the corpus checkout (both READ-ONLY) and emits:
  d1-schema.sql + d1-data-NNNN.sql   — D1 database (laws, law_versions,
                                       amendments, schema_version, and a
                                       rebuilt laws_fts; provisions excluded)
  r2/acts/{law_id}.json              — per-act payload (meta + body +
                                       baked articles map)
  r2/versions/{law_id}/{date}.json   — one per law_versions row
  r2/meta/stats.json                 — precomputed /stats payload
  manifest.json                      — counts + sha256 per artifact class

Deterministic: same inputs → same outputs (stable ordering; the only
timestamp is `exported_at`). Never modifies catalog.db or the corpus.
"""
