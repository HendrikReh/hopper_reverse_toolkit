# hopper_export_rust_analysis.py

**Version**: 1.5.0
**Runs in**: Hopper (Scripts > Run Script)

## Purpose

Exports Rust-oriented function metadata from the active Hopper document. Demangles Rust symbols, infers crate origins, and captures call relationships. Use this when analyzing Rust binaries where crate attribution and demangled names matter.

## Output

`<binary>.analysis.json` (written next to the analyzed binary)

## What it exports

| Section | Contents |
|---|---|
| `functions` | Address, mangled name, demangled name, inferred crate, size, entry point, signature, basic block count, local variable count, tags |
| `calls` | Source, target, call-site address, call type (numeric + name) |

### Crate inference

The script recognizes these crate tokens: `tokio`, `axum`, `hyper`, `serde`, `tracing`, `rustls`, `ring`, and `std`. Unrecognized symbols are labeled `unknown`.

## Behavior

- Waits for Hopper background analysis to complete before collecting data.
- Uses `rustfilt` for demangling when available; falls back to the mangled name if `rustfilt` is not installed.
- Deduplicates call edges by (source, target, call_site, call_type).

## Usage

Run inside Hopper via **Scripts > Run Script**. No arguments needed.

```python
from hopper_export_rust_analysis import export_analysis

output_path = export_analysis()
```

## Output schema (abbreviated)

```json
{
  "tool": "hopper_export_rust_analysis.py",
  "version": "1.5.0",
  "functions": [
    {
      "address": "0x...",
      "name_mangled": "_ZN...",
      "name_demangled": "crate::module::function",
      "crate": "tokio",
      "size": 256,
      "entry_point": "0x...",
      "signature": "...",
      "basic_block_count": 8,
      "local_variable_count": 3,
      "tags": []
    }
  ],
  "calls": [ ... ]
}
```

## Dependencies

- `_hopper_utils.py` (bundled)
- Hopper Python API (`hopper` module)
- `rustfilt` (optional, recommended)
