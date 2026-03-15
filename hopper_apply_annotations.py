# hopper_apply_annotations.py — run inside Hopper's script engine
# Applies labels, comments, tags, colors, and bookmarks from a JSON file to the current document.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


Document: Any  # provided by Hopper's script engine at runtime

VERSION = "1.5.2"


# ---------------------------------------------------------------------------
# Utility helpers (inlined — no external module dependencies)
# ---------------------------------------------------------------------------

def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_address(value: object) -> int:
    if isinstance(value, int):
        return value
    text = str(value).strip().lower()
    if text.startswith("0x"):
        return int(text, 16)
    return int(text, 10)


def parse_color(value: object) -> int:
    if isinstance(value, int):
        return value
    text = str(value).strip().lower()
    if text.startswith("#"):
        text = text[1:]
    if text.startswith("0x"):
        text = text[2:]
    return int(text, 16)


# ---------------------------------------------------------------------------
# Annotation logic
# ---------------------------------------------------------------------------

def resolve_input_path(document: Any) -> Path:
    try:
        executable_path = Path(document.getExecutableFilePath())
        start_dir = str(executable_path.parent)
    except Exception:
        start_dir = str(Path.home())

    selected = Document.askFile("Select annotations JSON", start_dir, False)
    if not selected:
        raise RuntimeError("No annotations JSON selected.")
    return Path(selected)


def apply_annotations(document: Any, payload: dict[str, Any]) -> dict[str, int]:
    summary = {
        "labels": 0,
        "comments": 0,
        "inline_comments": 0,
        "tags": 0,
        "colors": 0,
        "bookmarks": 0,
    }

    for record in payload.get("labels", []):
        document.setNameAtAddress(parse_address(record["address"]), str(record["name"]))
        summary["labels"] += 1

    for record in payload.get("comments", []):
        document.setCommentAtAddress(parse_address(record["address"]), str(record["comment"]))
        summary["comments"] += 1

    for record in payload.get("inline_comments", []):
        document.setInlineCommentAtAddress(
            parse_address(record["address"]),
            str(record["comment"]),
        )
        summary["inline_comments"] += 1

    for record in payload.get("tags", []):
        address = parse_address(record["address"])
        tag = document.buildTag(str(record["tag"]))
        document.addTagAtAddress(tag, address)
        summary["tags"] += 1

    for record in payload.get("colors", []):
        document.setColorAtAddress(
            parse_color(record["color"]),
            parse_address(record["address"]),
        )
        summary["colors"] += 1

    for record in payload.get("bookmarks", []):
        document.setBookmarkAtAddress(
            parse_address(record["address"]),
            record.get("name"),
        )
        summary["bookmarks"] += 1

    if any(summary.values()):
        document.refreshView()
    return summary


# ---------------------------------------------------------------------------
# Script entry — runs immediately inside Hopper
# ---------------------------------------------------------------------------

doc = Document.getCurrentDocument()
if doc is None:
    raise RuntimeError("No active Hopper document.")

input_path = resolve_input_path(doc)
payload = load_json(input_path)
summary = apply_annotations(doc, payload)

doc.log(f"[hopper_apply_annotations] Applied from: {input_path}")
for key, value in summary.items():
    doc.log(f"[hopper_apply_annotations]   {key}: {value}")
