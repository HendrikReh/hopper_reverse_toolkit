# hopper_export_callgraph.py

**Version**: 1.5.0
**Runs in**: Hopper (Scripts > Run Script)

## Purpose

Exports a procedure-level call graph from the active Hopper document, capturing caller/callee relationships with call-site addresses and call-type metadata.

## Output

`<binary>.callgraph.json` (written next to the analyzed binary)

## What it exports

| Section | Contents |
|---|---|
| `nodes` | One entry per procedure: id, name, start/end addresses, entry point, signature, basic block count, tags |
| `edges` | One entry per unique call: source, target, call-site address, call type (numeric + name) |

Call types: `none` (0), `unknown` (1), `direct` (2), `objc` (3).

## Behavior

- Waits for Hopper background analysis to complete before collecting data.
- Deduplicates edges by (source, target, call_site, call_type).
- Iterates all segments and their procedures to build the graph.

## Usage

Run inside Hopper via **Scripts > Run Script**. No arguments needed.

```python
from hopper_export_callgraph import export_callgraph

output_path = export_callgraph()
```

## Output schema (abbreviated)

```json
{
  "tool": "hopper_export_callgraph.py",
  "version": "1.5.0",
  "nodes": [
    {
      "id": "0x...",
      "name": "...",
      "start": "0x...",
      "end": "0x...",
      "entry_point": "0x...",
      "signature": "...",
      "basic_block_count": 12,
      "tags": []
    }
  ],
  "edges": [
    {
      "source": "0x...",
      "target": "0x...",
      "call_site": "0x...",
      "call_type": 2,
      "call_type_name": "direct"
    }
  ]
}
```

## Dependencies

- `_hopper_utils.py` (bundled)
- Hopper Python API (`hopper` module)
