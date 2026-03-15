# Prompt 04 — Application Logic vs Framework Noise

Use this when the binary is symbol-heavy and you need to isolate the code that is most likely owned by the application.

## Inputs
Prefer:
- `enriched_analysis.json`
- `*.analysis.json`
- `*.hopper_export.json`
- `architecture_summary.md`

## Prompt
You are separating probable application logic from framework or dependency noise in Hopper-derived binary analysis artifacts.

Classify functions and subsystems into:
- likely application-owned
- likely framework or runtime
- uncertain mixed zones

Use evidence from:
- demangled names
- subsystem labels
- string references
- signatures and locals
- call centrality
- trust-boundary proximity
- whether a function looks like a dispatcher, wrapper, adapter, or concrete business rule

## Required Output
### Application Candidates
List the strongest candidate application functions and why they are likely application-owned.

### Framework Candidates
List the clearest framework-heavy functions and why they are probably noise for manual reversing.

### Anchor Functions
Recommend the best manual starting points in Hopper for understanding the binary quickly.

For each anchor include:
- address
- function name
- what it likely reveals
- what to inspect next if the hypothesis is correct

### Misclassification Risks
Explain where you might be wrong, especially for adapter layers or project-local wrappers around popular libraries.

## Rules
- Avoid simplistic “crate name equals framework” reasoning.
- Treat thin wrapper functions carefully; they can be application-owned even when they call framework code.
