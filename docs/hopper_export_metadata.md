# hopper_export_metadata.py

**Version**: 1.5.0
**Runs in**: Hopper (Scripts > Run Script)

## Purpose

Exports comprehensive structural metadata from the active Hopper document into a single JSON file. This is typically the first script you run and produces the primary structural export used by downstream tools.

## Output

`<binary>.hopper_export.json` (written next to the analyzed binary)

## What it exports

| Section | Contents |
|---|---|
| `document` | Document name, database path, executable path, entry point, 64-bit flag |
| `segments` | Segment name, start address, length, file offset, procedure/string counts, and nested sections (name, start, length, flags) |
| `symbols` | Named addresses per segment with segment association |
| `procedures` | Name, entry point, start/end addresses, signature, heap size, local variables (name + displacement), tags, basic blocks (start, end, successors, tags), and decompiled pseudocode when available |
| `entry_points` | Document entry point address |

## Behavior

- Waits for Hopper background analysis to complete before collecting data.
- Attempts pseudocode decompilation for each procedure; silently skips on failure.
- Collects warnings for segment or procedure parsing failures without aborting.

## Usage

Run inside Hopper via **Scripts > Run Script**. No arguments needed.

```python
from hopper_export_metadata import export_hopper_metadata

output_path, result = export_hopper_metadata()
```

Or run as a standalone script inside Hopper:

```
Scripts > Run Script > hopper_export_metadata.py
```

## Output schema (abbreviated)

```json
{
  "tool": "hopper_export_metadata.py",
  "version": "1.5.0",
  "document": {
    "name": "...",
    "database_path": "...",
    "file_path": "...",
    "entry_point": "0x...",
    "is_64_bit": true
  },
  "segments": [ ... ],
  "symbols": [ ... ],
  "procedures": [ ... ],
  "entry_points": [ "0x..." ],
  "warnings": [ "..." ]
}
```

## Dependencies

- `_hopper_utils.py` (bundled)
- Hopper Python API (`hopper` module)
