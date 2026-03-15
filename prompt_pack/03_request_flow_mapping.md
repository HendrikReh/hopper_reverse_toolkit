# Prompt 03 — Request Flow Mapping

Use this when you want to reconstruct how requests or commands likely move through the binary.

## Inputs
Use:
- `enriched_analysis.json`
- `*.callgraph.json`
- Mermaid callflow artifacts
- GraphML if available
- `architecture_summary.md`

## Prompt
You are mapping the most likely request-processing flow of a compiled binary from Hopper-derived artifacts.

Reconstruct the dominant end-to-end flow from likely ingress points to routing, validation, business logic, persistence, and outbound effects.

Pay special attention to:
- handler and router naming
- subsystem transitions
- high-degree functions
- call-site metadata
- security-relevant branches
- framework-to-application handoff points

## Required Output
### Candidate Entry Paths
List the most likely ingress functions or dispatcher roots with evidence.

### Step-by-Step Flow
Describe the most likely flow in ordered stages:
1. ingress
2. routing or dispatch
3. parsing or validation
4. core application logic
5. storage or outbound calls
6. response or termination path

For each stage include addresses and function names.

### Framework Handoff
Identify where framework code likely transitions into application-specific logic.

### Confidence Breaks
Point out where the flow becomes speculative and what Hopper checks would reduce uncertainty.

## Rules
- Use addresses and edge evidence where possible.
- If multiple flows are plausible, present the top two rather than collapsing them into one story.
- Do not overfit the flow from subsystem names alone.
