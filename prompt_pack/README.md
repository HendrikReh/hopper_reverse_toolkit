# LLM-Ready Prompt Pack
Version: 1.5.0

This folder contains reusable prompt templates for architecture reconstruction, security triage, flow mapping, and Hopper annotation generation from Hopper-derived artifacts.

## Recommended inputs
- `enriched_analysis.json`
- `architecture_summary.md`
- `*.hopper_export.json`
- `*.callgraph.json`
- `*.analysis.json`
- Mermaid diagrams
- GraphML
- optional C4 Mermaid / PlantUML diagrams

## Prompt guide
- `01_architecture_reconstruction.md`: first-pass architecture recovery and trust-boundary mapping
- `02_security_hotspots.md`: security-oriented hotspot triage
- `03_request_flow_mapping.md`: likely ingress-to-effect flow reconstruction
- `04_app_vs_framework.md`: isolate application logic from framework noise
- `05_c4_reconstruction.md`: produce a narrative C4-style model from the generated diagrams
- `06_annotation_candidates.md`: generate JSON annotations for `hopper_apply_annotations.py`

## Usage notes
- These prompts are designed to be copied into an LLM alongside Hopper export artifacts.
- The prompts assume the analyst wants evidence, uncertainty, and follow-up guidance, not just a summary.
- `06_annotation_candidates.md` is intentionally conservative and should be used when the output will be written back into Hopper.
