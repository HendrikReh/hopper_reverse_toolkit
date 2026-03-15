# enrich_hopper_exports.py

**Version**: 1.5.0
**Runs in**: Command line (outside Hopper)

## Purpose

Merges the metadata export (`*.hopper_export.json`) and callgraph export (`*.callgraph.json`) into a single enriched JSON file. Computes subsystem labels, in/out degrees, caller/callee previews, and an interestingness score for each function. Also produces a human-readable Markdown summary.

## Output

- `enriched_analysis.json` (default) -- enriched function records and call edges
- `architecture_summary.md` (default) -- subsystem distribution and top-ranked functions

## What it produces

| Field | Description |
|---|---|
| `address` | Function address |
| `name_mangled` | Original symbol name |
| `name_demangled` | Demangled name (via `rustfilt` if available) |
| `subsystem` | Heuristic subsystem label based on known crate/library tokens |
| `in_degree` / `out_degree` | Number of callers / callees |
| `callers` / `callees` | Up to 25 neighbor addresses |
| `interesting_score` | Weighted score combining degree, subsystem, and name tokens |

Additional fields from the source exports (entry_point, signature, basic_blocks, tags, etc.) are preserved when available.

### Interestingness scoring

- In-degree contributes up to 24 points (capped at 20 callers, x1.2)
- Out-degree contributes up to 20 points (capped at 20 callees, x1.0)
- `application-or-unknown` subsystem: +4 points
- Security-relevant subsystems (tls, crypto, database, http-routing, middleware): +3 points
- Name tokens (auth, token, login, verify, router, handler, service, query, request, response): +1.5 each

### Subsystem classification

Recognized tokens: `tokio` (async-runtime), `axum` (http-routing), `hyper` (http-core), `serde` (serialization), `tracing` (observability), `rustls` (tls), `ring` (crypto), `sqlx` (database), `reqwest` (http-client), `tower` (middleware), `std::` (std). Unmatched names map to `application-or-unknown`.

## Usage

```bash
python enrich_hopper_exports.py <metadata.json> <callgraph.json> \
    --out-json enriched_analysis.json \
    --out-md architecture_summary.md
```

### Arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `metadata_json` | yes | -- | Path to `*.hopper_export.json` |
| `callgraph_json` | yes | -- | Path to `*.callgraph.json` |
| `--out-json` | no | `enriched_analysis.json` | Output enriched JSON path |
| `--out-md` | no | `architecture_summary.md` | Output Markdown summary path |

## Dependencies

- `_hopper_utils.py` (bundled)
- `rustfilt` (optional, for Rust symbol demangling)
