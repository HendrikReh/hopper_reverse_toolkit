# generate_mermaid.py

**Version**: 1.4.0
**Runs in**: Command line (outside Hopper)

## Purpose

Generates three Mermaid diagrams from the enriched Hopper analysis JSON: a subsystem distribution chart, a hotspot diagram of the most interesting functions, and a callflow diagram of the highest-degree functions.

## Output

Three `.mmd` files (defaults shown):

| File | Diagram type | Description |
|---|---|---|
| `subsystems.mmd` | `flowchart TD` | Top 12 subsystems by function count, branching from a central "Binary" node |
| `hotspots.mmd` | `flowchart TD` | Top 15 functions ranked by interestingness score |
| `callflow.mmd` | `flowchart LR` | Top 10 functions by total degree with inter-edges among them |

## Usage

```bash
python generate_mermaid.py <enriched_analysis.json> \
    --subsystems subsystems.mmd \
    --hotspots hotspots.mmd \
    --callflow callflow.mmd
```

### Arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `enriched_json` | yes | -- | Path to `enriched_analysis.json` |
| `--subsystems` | no | `subsystems.mmd` | Subsystem diagram output path |
| `--hotspots` | no | `hotspots.mmd` | Hotspot diagram output path |
| `--callflow` | no | `callflow.mmd` | Callflow diagram output path |

## Dependencies

- `_hopper_utils.py` (bundled)
