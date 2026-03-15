# Prompt 05 — C4 Reconstruction

Use this when you want a narrative C4-style model from Hopper artifacts rather than just raw diagrams.

## Inputs
Prefer:
- `enriched_analysis.json`
- `c4_architecture.mmd`
- `c4_architecture.puml`
- `architecture_summary.md`
- subsystem Mermaid diagrams

## Prompt
You are producing a C4-style reconstruction of a compiled binary from Hopper-derived artifacts.

Use the enriched analysis and any generated Mermaid or PlantUML C4 diagrams to write a narrative covering:
- system context
- container-level decomposition
- component hotspots
- major interactions
- trust and data boundaries
- confidence notes

## Required Output
### System Context
What larger system or role this binary most likely serves.

### Container View
The major runtime areas or logical containers inside the binary, even if they are inferred rather than explicit deployable units.

### Component Hotspots
The most important internal components, their anchor functions, and why they matter.

### Interaction Summary
Describe the most important subsystem interactions and the strongest evidence for them.

### Confidence Notes
For each major architectural claim, state whether confidence is high, medium, or low and why.

## Rules
- Keep the model faithful to the evidence; do not invent deployment details.
- When a C4 term does not cleanly fit a binary, say how you adapted it.
