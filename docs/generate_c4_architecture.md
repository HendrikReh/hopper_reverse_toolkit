# generate_c4_architecture.py

**Version**: 1.4.0
**Runs in**: Command line (outside Hopper)

## Purpose

Generates C4-style architecture diagrams in both Mermaid and PlantUML formats from the enriched Hopper JSON. Provides a higher-level "analyst facing a binary" view with subsystem containers and representative functions.

## Output

Two files (defaults shown):

| File | Format | Description |
|---|---|---|
| `c4_architecture.mmd` | Mermaid `flowchart TB` | C4-style diagram with analyst, binary, system, subsystem containers, and weighted cross-subsystem edges |
| `c4_architecture.puml` | PlantUML | Same structure using PlantUML `@startuml` syntax with packages and components |

Both diagrams show:
- Up to `--max-groups` (default 8) subsystems ranked by function count
- Up to 3 representative functions per subsystem (ranked by interestingness score)
- Up to `--max-edges` (default 14) weighted edges between subsystems

## Usage

```bash
python generate_c4_architecture.py <enriched_analysis.json> \
    --mermaid-out c4_architecture.mmd \
    --plantuml-out c4_architecture.puml \
    --max-groups 8 \
    --max-edges 14
```

### Arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `enriched_json` | yes | -- | Path to `enriched_analysis.json` |
| `--mermaid-out` | no | `c4_architecture.mmd` | Mermaid output path |
| `--plantuml-out` | no | `c4_architecture.puml` | PlantUML output path |
| `--max-groups` | no | `8` | Maximum subsystem groups |
| `--max-edges` | no | `14` | Maximum inter-subsystem edges |

## Dependencies

- `_hopper_utils.py` (bundled)
