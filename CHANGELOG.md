
# Changelog

## Unreleased
- Added `HOPPER_6_2_1_PYTHON_API.md`, a hybrid practical guide and class reference for Hopper 6.2.1 Python scripting.

## v1.5.0
- Reworked Hopper exporters to use documented segment, procedure, and call-reference APIs.
- Wait for Hopper background analysis before exporting to avoid partial metadata.
- Expanded metadata exports with sections, strings, locals, signatures, and basic-block details.
- Expanded call exports with call-site and call-type metadata.
- Added `hopper_apply_annotations.py` to write labels, comments, tags, colors, and bookmarks back into Hopper.
- Rewrote `prompt_pack/` templates into structured analyst prompts and added annotation-payload generation guidance.

## v1.4.0
- Added `generate_c4_architecture.py` for automatic C4-style architecture diagrams from binaries.
- Added Mermaid and PlantUML C4 outputs.
- Added prompt pack entry for C4 reconstruction.
- Updated README and bundle versioning.

## v1.3.0
- Added `json_to_mermaid_architecture.py` for higher-level Mermaid architecture synthesis.

## v1.2.0
- Added `generate_mermaid.py` and `prompt_pack/`.

## v1.1.0
- Added `export_graphml.py` and `enrich_hopper_exports.py`.

## v1.0.0
- Initial toolkit bundle.
