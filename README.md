# Hopper Reverse Toolkit

[![GitHub release](https://img.shields.io/github/v/release/HendrikReh/hopper_reverse_toolkit)](https://github.com/HendrikReh/hopper_reverse_toolkit/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![Hopper](https://img.shields.io/badge/Hopper-v6-orange)](https://www.hopperapp.com/)

**Version**: 1.5.1
**Last updated**: 2026-03-15
**Maintained by**: <hendrik.reh@blacksmith-consulting.ai>

This toolkit turns [Hopper](https://www.hopperapp.com/) analysis into reusable artifacts for architecture recovery, security triage, prompt-driven reverse engineering, and annotation write-back.

## Table of contents

- [About Hopper](#about-hopper)
- [Included files and versions](#included-files-and-versions)
- [Quick start](#quick-start)
- [Artifact guide](#artifact-guide)
- [Recommended workflow](#recommended-workflow)
- [Prompt pack](#prompt-pack)
- [Applying annotations inside Hopper](#applying-annotations-inside-hopper)
- [Documentation](#documentation)
- [Notes](#notes)

## About Hopper

[Hopper](https://www.hopperapp.com/) is a native macOS disassembler and reverse engineering tool for analyzing executable code. It supports Mach-O, ARM, and Windows binaries and provides:

- Assembly disassembly and decompilation to C-like pseudo-code
- Interactive control flow graphs with PDF export
- Objective-C selector extraction and Swift name demangling
- LLDB and GDB debugger integration
- Python scripting API for automation
- An extensible SDK for custom loaders and CPU backends
- AI-assisted analysis via an MCP server

Hopper requires macOS 12.4 or later. This toolkit targets the Hopper v6 Python scripting API.

For Hopper scripting details beyond the toolkit workflow, see [`docs/hopper_6_2_1_python_api.md`](docs/hopper_6_2_1_python_api.md).

## Included files and versions

| File | Version | Purpose |
|---|---:|---|
| `hopper_export_metadata.py` | 1.5.1 | Export segments, sections, strings, procedures, locals, tags, and CFG metadata from Hopper |
| `hopper_export_callgraph.py` | 1.5.1 | Export a procedure call graph with call-site and call-type metadata |
| `hopper_export_rust_analysis.py` | 1.5.1 | Export Rust-oriented function data with demangling, signatures, and call metadata |
| `hopper_apply_annotations.py` | 1.5.1 | Apply labels, comments, tags, colors, and bookmarks back into the current Hopper document |
| `enrich_hopper_exports.py` | 1.5.1 | Merge Hopper exports into enriched JSON while preserving richer call metadata |
| `docs/hopper_6_2_1_python_api.md` | n/a | Practical plus reference guide for Hopper 6.2.1 Python scripting |
| `export_graphml.py` | 1.4.0 | Convert `*.callgraph.json` into GraphML |
| `generate_mermaid.py` | 1.4.0 | Generate subsystem, hotspot, and callflow Mermaid diagrams |
| `json_to_mermaid_architecture.py` | 1.4.0 | Synthesize a higher-level Mermaid architecture diagram |
| `generate_c4_architecture.py` | 1.4.0 | Generate C4-style Mermaid and PlantUML diagrams from enriched JSON |
| `prompt_pack/` | 1.5.1 | Reusable prompts for architecture reconstruction, security triage, flow mapping, and annotation generation |
| `CHANGELOG.md` | n/a | Bundle history |
| `README.md` | n/a | This document |

## Quick start

### 1. Export inside Hopper
Run these from `Scripts → Run Script`:
1. `hopper_export_metadata.py`
2. `hopper_export_callgraph.py`
3. `hopper_export_rust_analysis.py` (optional)

Typical outputs written next to the executable:
- `<binary>.hopper_export.json`
- `<binary>.callgraph.json`
- `<binary>.analysis.json`

The export scripts wait for Hopper background analysis to finish before collecting data, so you do not need to manually pause for the analysis queue to drain.

### 2. Enrich and render outside Hopper
```bash
python enrich_hopper_exports.py /path/to/binary.hopper_export.json /path/to/binary.callgraph.json --out-json enriched_analysis.json --out-md architecture_summary.md
python generate_mermaid.py enriched_analysis.json --subsystems subsystems.mmd --hotspots hotspots.mmd --callflow callflow.mmd
python json_to_mermaid_architecture.py enriched_analysis.json --out architecture_synthesized.mmd
python generate_c4_architecture.py enriched_analysis.json --mermaid-out c4_architecture.mmd --plantuml-out c4_architecture.puml
python export_graphml.py /path/to/binary.callgraph.json /path/to/binary.graphml
```

### 3. Analyze with the prompt pack
Use the templates in `prompt_pack/` with the generated JSON, summary, Mermaid, GraphML, and optional Rust analysis artifacts.

### 4. Write annotations back into Hopper
Run `hopper_apply_annotations.py` inside Hopper with a JSON payload generated manually or via `prompt_pack/06_annotation_candidates.md`.

If no file path is passed, the script opens a Hopper file picker.

## Artifact guide

| Artifact | Produced by | Contents | Typical downstream use |
|---|---|---|---|
| `*.hopper_export.json` | `hopper_export_metadata.py` | Document info, segments, sections, strings, symbols, procedures, locals, tags, and CFG basics | Primary structural export for enrichment and prompt-driven analysis |
| `*.callgraph.json` | `hopper_export_callgraph.py` | Procedures plus procedure-to-procedure edges with call-site and call-type metadata | GraphML export, enrichment, flow mapping, hotspot triage |
| `*.analysis.json` | `hopper_export_rust_analysis.py` | Rust-oriented function metadata, demangled names, signatures, tag counts, and call metadata | Rust-heavy binaries, crate inference, framework-vs-app separation |
| `enriched_analysis.json` | `enrich_hopper_exports.py` | Merged function records with subsystem labels, degrees, caller/callee previews, and preserved call metadata | Mermaid generation, prompt pack, architecture synthesis |
| `architecture_summary.md` | `enrich_hopper_exports.py` | Human-readable subsystem distribution and ranked functions | Analyst brief, prompt context, quick triage |
| `*.mmd` / `*.puml` | Mermaid/C4 generators | Visual architecture and call-flow diagrams | Review, docs, prompt context |
| `*.graphml` | `export_graphml.py` | Call graph in GraphML | External graph tooling |

## Recommended workflow

### Inside Hopper
- Start with `hopper_export_metadata.py` and `hopper_export_callgraph.py`.
- Use `hopper_export_rust_analysis.py` when symbol quality or crate inference matters.
- Use `hopper_apply_annotations.py` only after reviewing the annotation payload; it writes directly to the open document.

### Outside Hopper
- Treat `enriched_analysis.json` as the main handoff artifact.
- Generate Mermaid or C4 views after enrichment, not before.
- Use GraphML when you want external graph tooling rather than prompt-driven analysis.

## Prompt pack

`prompt_pack/` is designed for copy-paste use with an LLM and the Hopper artifacts produced by this bundle.

Recommended prompt selection:
- `01_architecture_reconstruction.md`: first-pass system architecture and trust boundaries
- `02_security_hotspots.md`: likely auth, crypto, parser, storage, and network hotspots
- `03_request_flow_mapping.md`: ingress-to-effect or request-to-response flow reconstruction
- `04_app_vs_framework.md`: isolate likely application-owned logic from framework noise
- `05_c4_reconstruction.md`: narrative C4-style architecture write-up
- `06_annotation_candidates.md`: conservative JSON annotation generation for `hopper_apply_annotations.py`

## Applying annotations inside Hopper

`hopper_apply_annotations.py` accepts a JSON payload with any of these top-level keys:
- `labels`
- `comments`
- `inline_comments`
- `tags`
- `colors`
- `bookmarks`

Example payload:
```json
{
  "labels": [{"address": "0x1000", "name": "entry_main"}],
  "comments": [{"address": "0x1000", "comment": "Recovered entry point"}],
  "inline_comments": [{"address": "0x1004", "comment": "Calls helper"}],
  "tags": [{"address": "0x1000", "tag": "review"}],
  "colors": [{"address": "0x1000", "color": "#FF112233"}],
  "bookmarks": [{"address": "0x1000", "name": "main entry"}]
}
```

Use conservative payloads. A wrong label or comment in Hopper is more damaging than no annotation.

## Documentation

The `docs/` directory contains detailed documentation for every script and module in the toolkit.

### Script references

| Document | Covers |
|---|---|
| [`hopper_export_metadata.md`](docs/hopper_export_metadata.md) | Structural metadata export -- segments, procedures, pseudocode, basic blocks |
| [`hopper_export_callgraph.md`](docs/hopper_export_callgraph.md) | Call graph export with call-site and call-type metadata |
| [`hopper_export_rust_analysis.md`](docs/hopper_export_rust_analysis.md) | Rust-specific export with demangling and crate inference |
| [`hopper_apply_annotations.md`](docs/hopper_apply_annotations.md) | Annotation write-back -- labels, comments, tags, colors, bookmarks |
| [`enrich_hopper_exports.md`](docs/enrich_hopper_exports.md) | Merge and enrichment with interestingness scoring and subsystem classification |
| [`export_graphml.md`](docs/export_graphml.md) | Callgraph JSON to GraphML conversion |
| [`generate_mermaid.md`](docs/generate_mermaid.md) | Subsystem, hotspot, and callflow Mermaid diagrams |
| [`json_to_mermaid_architecture.md`](docs/json_to_mermaid_architecture.md) | High-level synthesized architecture Mermaid diagram |
| [`generate_c4_architecture.md`](docs/generate_c4_architecture.md) | C4-style Mermaid and PlantUML diagrams |
| [`_hopper_utils.md`](docs/_hopper_utils.md) | Shared utility library -- all helper functions, subsystem tokens, call type codes |

### Hopper scripting reference

| Document | Covers |
|---|---|
| [`hopper_6_2_1_python_api.md`](docs/hopper_6_2_1_python_api.md) | Practical and reference guide for the Hopper 6.2.1 Python scripting API |

## Notes

- Hopper's Python API differs across versions; this bundle targets the documented public segment, procedure, basic-block, and call-reference APIs.
- `rustfilt` is optional but recommended for Rust binaries.
- Diagram outputs are heuristic starting points, not ground truth.
- The richer exports preserve call-site metadata, local variables, strings, tags, and basic-block relationships for downstream automation.
