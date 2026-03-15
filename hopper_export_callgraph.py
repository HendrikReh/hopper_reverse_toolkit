
from __future__ import annotations

from pathlib import Path
from typing import Any

from _hopper_utils import (
    call_type_name,
    default_output_path,
    ensure_document_ready,
    iter_document_procedures,
    tag_names,
    to_hex,
    write_json,
)


try:
    from hopper import Document  # type: ignore[import-not-found]

    HAS_HOPPER = True
except ModuleNotFoundError:
    Document = None
    HAS_HOPPER = False


VERSION = "1.5.0"


def collect_callgraph(document: Any) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str, str | None, int]] = set()
    procedures = iter_document_procedures(document)

    for procedure in procedures:
        entry_point = to_hex(procedure.getEntryPoint())
        nodes.append(
            {
                "id": entry_point,
                "name": procedure.getName(),
                "start": to_hex(procedure.getStartingAddress()),
                "end": to_hex(procedure.getEndingAddress()),
                "entry_point": entry_point,
                "signature": str(procedure.signatureString() or ""),
                "basic_block_count": int(procedure.getBasicBlockCount()),
                "tags": tag_names(procedure),
            },
        )

    for procedure in procedures:
        source = to_hex(procedure.getEntryPoint())
        if not source:
            continue
        try:
            callees = procedure.getAllCallees()
        except Exception:
            continue

        for call_reference in callees:
            target = to_hex(call_reference.toAddress())
            if not target:
                continue
            call_site = to_hex(call_reference.fromAddress())
            type_value = int(call_reference.type())
            edge_key = (source, target, call_site, type_value)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "call_site": call_site,
                    "call_type": type_value,
                    "call_type_name": call_type_name(type_value),
                },
            )

    return {
        "tool": "hopper_export_callgraph.py",
        "version": VERSION,
        "nodes": nodes,
        "edges": edges,
    }


def export_callgraph(document: Any | None = None) -> Path:
    if not HAS_HOPPER and document is None:
        raise RuntimeError("Hopper Python API is unavailable. Run this script inside Hopper.")

    active_document = document or Document.getCurrentDocument()
    if active_document is None:
        raise RuntimeError("No active Hopper document.")

    ensure_document_ready(active_document)
    try:
        executable_path = active_document.getExecutableFilePath()
    except Exception:
        executable_path = None

    result = collect_callgraph(active_document)
    output_path = default_output_path(
        executable_path,
        ".callgraph.json",
        "hopper_callgraph.json",
    )
    write_json(output_path, result)
    return output_path


def main() -> int:
    try:
        output_path = export_callgraph()
    except RuntimeError as error:
        print(error)
        return 1

    print("Callgraph exported:", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
