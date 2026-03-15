# _hopper_utils.py

**Version**: 1.5.0
**Type**: Internal shared library

## Purpose

Shared utility functions used by all scripts in the toolkit. Not intended to be run directly.

## Functions

| Function | Description |
|---|---|
| `load_json(path)` | Load and parse a JSON file |
| `write_json(path, payload)` | Write a Python object as indented JSON |
| `write_text(path, content)` | Write a string to a file (UTF-8) |
| `demangle_rust_symbol(name)` | Demangle a Rust symbol via `rustfilt` (cached, falls back to original name) |
| `guess_subsystem(name)` | Map a function name to a subsystem label based on known crate/library tokens |
| `sanitize_id(value)` | Convert a value to an alphanumeric-only identifier (for Mermaid/GraphML) |
| `sanitize_label(value)` | Escape double quotes in a label string |
| `short_label(value, limit=36)` | Truncate a label to a maximum length with `...` |
| `default_output_path(executable_path, suffix, fallback_name)` | Derive an output path next to the binary, or fall back to `~/fallback_name` |
| `to_hex(value)` | Convert an integer-like value to a `0x...` hex string |
| `parse_address(value)` | Parse a hex or decimal address string to `int` |
| `parse_color(value)` | Parse a `#AARRGGBB` or `0x...` color string to `int` |
| `call_type_name(value)` | Map a numeric call type to a human-readable name |
| `ensure_document_ready(document)` | Wait for Hopper background analysis to complete |
| `iter_document_procedures(document)` | Collect all procedures across all segments in a Hopper document |
| `tag_names(owner)` | Extract tag name strings from a Hopper object's tag list |

## Subsystem tokens

| Token | Subsystem label |
|---|---|
| `tokio` | async-runtime |
| `axum` | http-routing |
| `hyper` | http-core |
| `serde` | serialization |
| `tracing` | observability |
| `rustls` | tls |
| `ring` | crypto |
| `sqlx` | database |
| `reqwest` | http-client |
| `tower` | middleware |
| `std::` | std |

Unmatched names return `application-or-unknown`.

## Call type codes

| Code | Name |
|---|---|
| 0 | none |
| 1 | unknown |
| 2 | direct |
| 3 | objc |
