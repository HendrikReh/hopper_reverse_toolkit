# Prompt 02 — Security Hotspots

Use this when the goal is to triage likely security-relevant code paths from Hopper exports.

## Inputs
Prefer:
- `enriched_analysis.json`
- `architecture_summary.md`
- `*.hopper_export.json`
- `*.callgraph.json`
- `*.analysis.json`
- Mermaid or C4 diagrams if available

## Prompt
You are reviewing a compiled binary from Hopper-derived artifacts to identify probable security hotspots and abuse-relevant code paths.

Focus on:
- authentication and authorization
- token handling
- crypto and TLS
- request parsing and deserialization
- filesystem or archive handling
- persistence boundaries
- outbound network calls
- logging and observability choke points
- configuration or feature-flag gates

Use function names, signatures, locals, strings, subsystem labels, call-site metadata, CFG shape, and caller/callee structure as evidence.

## Required Output
### Priority Findings
Rank the most important hotspots by likely risk and analyst payoff.

For each hotspot include:
- severity estimate: high, medium, or low
- address and function name
- likely responsibility
- supporting evidence
- uncertainty or alternative explanations
- recommended Hopper follow-up

### Boundary Review
Identify likely boundaries for:
- inbound input
- privilege checks
- secret handling
- crypto operations
- storage
- outbound traffic

### False-Positive Filters
Call out cases that are probably framework noise rather than application-specific risk.

### Suggested Tags
Suggest a short tag list the analyst could apply in Hopper, such as:
- `auth`
- `crypto`
- `tls`
- `parser`
- `storage`
- `network`
- `hotspot`

## Rules
- Prefer evidence-backed suspicion over dramatic claims.
- Call out confidence explicitly.
- Distinguish direct evidence from name-based heuristics.
