# Prompt 01 — Architecture Reconstruction

Use this when you want a disciplined first-pass architecture readout from Hopper artifacts.

## Inputs
Use as many of these as are available:
- `enriched_analysis.json`
- `architecture_summary.md`
- `*.hopper_export.json`
- `*.callgraph.json`
- `*.analysis.json`
- Mermaid or GraphML call-flow artifacts

## Prompt
You are assisting a reverse engineer working from Hopper-derived artifacts for a compiled binary.

Reconstruct the most likely runtime architecture of the binary. Distinguish application logic from framework or library plumbing, identify major subsystems, describe likely trust boundaries, and highlight the functions that deserve manual Hopper follow-up.

Use evidence from:
- subsystem labels
- demangled and mangled names
- signatures
- local variables
- basic-block structure
- caller and callee relationships
- call-site metadata
- strings, symbols, and exported notes

## Required Output
### Executive Summary
Provide a short narrative of what the binary appears to do.

### Subsystem Map
For each major subsystem, include:
- likely role
- anchor functions with addresses
- why the subsystem boundary is credible
- confidence level

### Application vs Framework Split
Separate likely application-specific code from framework or dependency-heavy code and explain the distinction.

### Trust Boundaries
Identify where untrusted input likely enters, where persistence or network boundaries exist, and where secrets or privileged decisions may occur.

### High-Value Functions
List the most important functions to inspect next, with:
- address
- name
- why they matter
- what to verify in Hopper

### Open Questions
List unresolved hypotheses and what evidence would confirm or falsify them.

## Rules
- Cite concrete addresses and function names when making claims.
- Separate evidence from inference.
- If the artifacts are ambiguous, say so explicitly.
- Do not claim source-level certainty from symbol names alone.
