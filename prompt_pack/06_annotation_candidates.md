# Prompt 06 — Hopper Annotation Candidates

Use this when you want the model to produce machine-readable annotations that can be applied with `hopper_apply_annotations.py`.

## Inputs
Prefer:
- `enriched_analysis.json`
- `*.hopper_export.json`
- `*.callgraph.json`
- `*.analysis.json`
- analyst notes or prior write-ups

## Prompt
You are preparing a conservative annotation payload for Hopper based on reverse-engineering artifacts.

Return only valid JSON, with no Markdown fence and no explanatory prose.

The JSON schema must be:
```json
{
  "labels": [{"address": "0x...", "name": "..."}],
  "comments": [{"address": "0x...", "comment": "..."}],
  "inline_comments": [{"address": "0x...", "comment": "..."}],
  "tags": [{"address": "0x...", "tag": "..."}],
  "colors": [{"address": "0x...", "color": "#AARRGGBB"}],
  "bookmarks": [{"address": "0x...", "name": "..."}]
}
```

Only emit annotations that are high-confidence and useful for a human analyst.

## Annotation Policy
- Labels: use for strongly supported function or dispatcher names.
- Comments: use for concise high-value summaries.
- Inline comments: use for a specific call site, branch, or noteworthy instruction address.
- Tags: prefer short reusable tags such as `entrypoint`, `handler`, `auth`, `crypto`, `parser`, `storage`, `network`, `framework`, `app`, or `hotspot`.
- Colors: use sparingly and consistently.
- Bookmarks: reserve for addresses worth immediate manual review.

## Rules
- Do not fabricate names when the evidence is weak.
- Keep comments short and factual.
- Prefer no annotation over a misleading one.
- If a category has no strong candidates, return an empty list for that category.
