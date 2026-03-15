from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from _hopper_utils import load_json, parse_address, parse_color


try:
    from hopper import Document  # type: ignore[import-not-found]

    HAS_HOPPER = True
except ModuleNotFoundError:
    Document = None
    HAS_HOPPER = False


VERSION = "1.5.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply labels, comments, tags, colors, and bookmarks to the current Hopper document.",
    )
    parser.add_argument(
        "annotations_json",
        nargs="?",
        help="Path to an annotations JSON payload. If omitted inside Hopper, a file picker is shown.",
    )
    return parser.parse_args()


def resolve_input_path(document: Any, path_arg: str | None) -> Path:
    if path_arg:
        return Path(path_arg)

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


def main() -> int:
    if not HAS_HOPPER:
        print("Hopper Python API is unavailable. Run this script inside Hopper.")
        return 1

    document = Document.getCurrentDocument()
    if document is None:
        print("No active Hopper document.")
        return 1

    args = parse_args()
    try:
        input_path = resolve_input_path(document, args.annotations_json)
        payload = load_json(input_path)
        summary = apply_annotations(document, payload)
    except (OSError, json.JSONDecodeError, RuntimeError, ValueError, KeyError) as error:
        print(f"Failed to apply annotations: {error}")
        return 1

    print("Annotations applied from:", input_path)
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
