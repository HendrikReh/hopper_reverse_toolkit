# json_to_mermaid_architecture.py

**Version**: 1.4.0
**Runs in**: Command line (outside Hopper)

## Purpose

Synthesizes a high-level Mermaid architecture diagram from the enriched Hopper JSON. Groups functions by subsystem, shows representative functions inside each group, and draws weighted edges between subsystems based on cross-subsystem call counts.

## Output

A single `.mmd` file (default: `architecture_synthesized.mmd`) containing a `flowchart TD` diagram with:

- A top-level node per subsystem (up to `--max-groups`, default 8) showing function count
- Subgraph detail panels with up to 3 representative functions per subsystem (ranked by interestingness score)
- Weighted edges between subsystems labeled with call counts (up to `--max-edges`, default 16)

## Usage

```bash
python json_to_mermaid_architecture.py <enriched_analysis.json> \
    --out architecture_synthesized.mmd \
    --max-groups 8 \
    --max-edges 16
```

### Arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `enriched_json` | yes | -- | Path to `enriched_analysis.json` |
| `--out` | no | `architecture_synthesized.mmd` | Output Mermaid file path |
| `--max-groups` | no | `8` | Maximum number of subsystem groups to include |
| `--max-edges` | no | `16` | Maximum number of inter-subsystem edges |

### Programmatic

```python
from json_to_mermaid_architecture import synthesize

rendered = synthesize("enriched_analysis.json", "architecture.mmd", max_groups=8, max_edges=16)
```

## Dependencies

- `_hopper_utils.py` (bundled)
